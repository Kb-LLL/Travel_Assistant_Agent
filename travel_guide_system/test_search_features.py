"""
Lightweight tests for the public-search travel features.

Run from repo root:
python travel_guide_system/test_search_features.py
"""

import os
import sys
import unittest
import importlib.util
from types import SimpleNamespace


sys.path.insert(0, os.path.dirname(__file__))


SAMPLE_WEB_RESULT = {
    "title": "杭州旅游攻略",
    "url": "https://example.com/hangzhou",
    "source": "example.com",
    "snippet": "西湖、灵隐寺、美食和住宿建议。",
    "publish_date": "",
    "views": None,
}


def fake_search_response(query, max_results=8):
    return SimpleNamespace(
        items=[dict(SAMPLE_WEB_RESULT)],
        query=query,
        mode="live",
        source_url="https://duckduckgo.com/?q=test",
        search_time=0.01,
        warning="",
        engine="test",
    )


class SearchFeatureTests(unittest.TestCase):
    def test_parse_travel_query(self):
        from query_parser import parse_travel_query

        self.assertEqual(parse_travel_query("从北京到上海旅游攻略"), ("北京", "上海"))
        self.assertEqual(parse_travel_query("广州-西安"), ("广州", "西安"))
        self.assertEqual(parse_travel_query("杭州攻略"), ("我的城市", "杭州"))

    def test_web_search_shape(self):
        import web_search

        original = web_search.public_web_search
        web_search.public_web_search = fake_search_response
        try:
            result = web_search.search_web_guides("北京", "杭州")
        finally:
            web_search.public_web_search = original

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["results"][0]["title"], "杭州旅游攻略")
        self.assertIn("url", result["results"][0])

    def test_platform_search_shape(self):
        import platform_reviews

        original = platform_reviews.public_web_search
        platform_reviews.public_web_search = fake_search_response
        try:
            result = platform_reviews.search_platform_reviews("杭州")
        finally:
            platform_reviews.public_web_search = original

        self.assertTrue(result["success"])
        self.assertIn("xiaohongshu", result["platforms"])
        item = result["platforms"]["xiaohongshu"]["items"][0]
        self.assertEqual(item["platform"], "小红书")
        self.assertEqual(result["platforms"]["xiaohongshu"]["reviews"], result["platforms"]["xiaohongshu"]["items"])
        self.assertNotIn("rating", item)
        self.assertNotIn("user", item)

    def test_flask_feature_endpoints(self):
        app_module = None
        old_path = list(sys.path)
        repo_root = os.path.dirname(os.path.dirname(__file__))
        agent_dir = os.path.join(repo_root, "travel_agent")
        agent_app_path = os.path.join(agent_dir, "app.py")

        try:
            sys.modules.pop("config", None)
            sys.path.insert(0, agent_dir)
            sys.path.insert(1, os.path.dirname(__file__))
            spec = importlib.util.spec_from_file_location("travel_agent_app_under_test", agent_app_path)
            app_module = importlib.util.module_from_spec(spec)
            sys.modules["travel_agent_app_under_test"] = app_module
            spec.loader.exec_module(app_module)
        except ModuleNotFoundError as exc:
            self.skipTest(f"Flask app dependencies are not installed: {exc}")
        finally:
            sys.path = old_path

        web_result = {
            "success": True,
            "query": "北京到杭州 旅游攻略",
            "origin": "北京",
            "destination": "杭州",
            "total_results": 1,
            "results": [dict(SAMPLE_WEB_RESULT)],
            "search_time": 0.01,
            "mode": "live",
            "engine": "test",
            "warning": "",
            "source_url": "https://duckduckgo.com/?q=test",
        }
        review_result = {
            "success": True,
            "destination": "杭州",
            "mode": "live",
            "platforms": {
                "xiaohongshu": {
                    "platform": "小红书",
                    "icon": "📕",
                    "items": [dict(SAMPLE_WEB_RESULT, platform="小红书", platform_key="xiaohongshu")],
                    "reviews": [dict(SAMPLE_WEB_RESULT, platform="小红书", platform_key="xiaohongshu")],
                    "mode": "live",
                }
            },
            "total_reviews": 1,
            "total_items": 1,
            "warning": "",
        }

        original_web = app_module._get_web_results
        original_reviews = app_module._get_review_results
        original_stream = app_module.stream_analysis
        app_module._get_web_results = lambda origin, destination: web_result
        app_module._get_review_results = lambda origin, destination: review_result
        app_module.stream_analysis = lambda origin, destination, web, reviews: iter(["测试分析"])
        try:
            app_module.app.config["TESTING"] = True
            client = app_module.app.test_client()

            web_response = client.post("/api/web-search", json={"query": "从北京到杭州"})
            self.assertEqual(web_response.status_code, 200)
            self.assertTrue(web_response.get_json()["success"])

            platform_response = client.post("/api/platform-search", json={"destination": "杭州"})
            self.assertEqual(platform_response.status_code, 200)
            self.assertIn("items", platform_response.get_json()["platforms"]["xiaohongshu"])

            analysis_response = client.post("/api/full-analysis", json={"origin": "北京", "destination": "杭州"})
            self.assertEqual(analysis_response.status_code, 200)
            self.assertIn("测试分析", analysis_response.get_data(as_text=True))
        finally:
            app_module._get_web_results = original_web
            app_module._get_review_results = original_reviews
            app_module.stream_analysis = original_stream


if __name__ == "__main__":
    unittest.main()
