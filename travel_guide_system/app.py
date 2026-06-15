"""
旅游攻略搜索与分析系统 - Flask 后端 API
"""

import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from web_search import search_web_guides
from platform_reviews import search_platform_reviews
from ai_analyzer import stream_analysis
from cache_manager import get_cache, set_cache
from query_parser import parse_travel_query

app = Flask(__name__, static_folder="static")
CORS(app)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/search", methods=["POST"])
def search():
    """搜索接口 - 搜索网页攻略和各平台评论"""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"success": False, "message": "请输入搜索内容"}), 400

    # 解析出发地和目的地
    origin, destination = parse_query(query)
    if not destination:
        return jsonify({"success": False, "message": "无法识别目的地，请使用'从A到B'或'A-B'格式"}), 400

    print(f"[搜索请求] 出发地: {origin}, 目的地: {destination}")

    web_results = _get_web_results(origin, destination)
    reviews_results = _get_review_results(origin, destination)

    return jsonify({
        "success": True,
        "origin": origin,
        "destination": destination,
        "web_results": web_results,
        "reviews_results": reviews_results,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """分析接口 - AI 综合分析并生成攻略"""
    data = request.get_json(silent=True) or {}
    origin = data.get("origin", "")
    destination = data.get("destination", "")

    if not origin or not destination:
        return jsonify({"success": False, "message": "缺少出发地或目的地"}), 400

    print(f"[分析请求] 出发地: {origin}, 目的地: {destination}")

    # 获取搜索数据
    web_results = _get_web_results(origin, destination)
    reviews_results = _get_review_results(origin, destination)

    def generate():
        try:
            # 流式输出分析结果
            for chunk in stream_analysis(origin, destination, web_results, reviews_results):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def parse_query(query: str) -> tuple:
    """
    解析用户查询，提取出发地和目的地
    
    支持格式：
    - "从北京到上海的旅游攻略"
    - "北京-上海"
    - "北京到上海"
    - "上海旅游攻略"（出发地默认为"我的城市"）
    """
    return parse_travel_query(query)


def _is_search_cache(data: dict) -> bool:
    return (
        isinstance(data, dict)
        and data.get("schema_version") == 2
        and data.get("mode") in {"live", "partial", "fallback"}
    )


def _get_web_results(origin: str, destination: str) -> dict:
    cached_web = get_cache(origin, destination, "web")
    if _is_search_cache(cached_web):
        result = dict(cached_web)
        result["from_cache"] = True
        return result

    result = search_web_guides(origin, destination)
    if result.get("success"):
        set_cache(origin, destination, "web", result)
    return result


def _get_review_results(origin: str, destination: str) -> dict:
    cached_reviews = get_cache(origin, destination, "reviews")
    if _is_search_cache(cached_reviews):
        result = dict(cached_reviews)
        result["from_cache"] = True
        return result

    result = search_platform_reviews(destination)
    if result.get("success"):
        set_cache(origin, destination, "reviews", result)
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("  旅游攻略搜索与分析系统")
    print("=" * 60)
    print("  访问 http://localhost:5001 打开系统")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
