"""
Multi-platform public search module for travel references.

This module searches publicly visible result pages for each platform. It does
not scrape logged-in comments or fabricate ratings/user reviews.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from config import MAX_SEARCH_RESULTS, PLATFORMS
except Exception:
    MAX_SEARCH_RESULTS = 10
    PLATFORMS = {}

from search_client import public_web_search


PLATFORM_SEARCH_CONFIG = {
    "xiaohongshu": {
        "name": "小红书",
        "icon": "📕",
        "domain": "xiaohongshu.com",
        "query_words": "旅游攻略 笔记 避坑",
    },
    "douyin": {
        "name": "抖音",
        "icon": "🎵",
        "domain": "douyin.com",
        "query_words": "旅游 攻略 vlog 打卡",
    },
    "dianping": {
        "name": "大众点评",
        "icon": "⭐",
        "domain": "dianping.com",
        "query_words": "景点 美食 酒店 评价",
    },
    "mafengwo": {
        "name": "马蜂窝",
        "icon": "🐝",
        "domain": "mafengwo.cn",
        "query_words": "自由行 游记 攻略",
    },
    "ctrip": {
        "name": "携程",
        "icon": "✈️",
        "domain": "ctrip.com",
        "query_words": "旅游攻略 景点 门票 酒店",
    },
}


def search_platform_reviews(destination: str, platform: str = "all") -> dict:
    """
    Search public platform references for a destination.

    Args:
        destination: destination name
        platform: platform key, or "all"

    Returns:
        dict: normalized public search data for each platform
    """
    destination = (destination or "").strip()
    enabled_platforms = _platform_keys()

    if platform == "all":
        platforms_data = _search_all_platforms(destination, enabled_platforms)
        return {
            "success": True,
            "schema_version": 2,
            "destination": destination,
            "mode": _overall_mode(platforms_data.values()),
            "platforms": platforms_data,
            "total_reviews": sum(len(p.get("items", [])) for p in platforms_data.values()),
            "total_items": sum(len(p.get("items", [])) for p in platforms_data.values()),
            "warning": _merge_warnings(platforms_data.values()),
        }

    if platform not in PLATFORM_SEARCH_CONFIG:
        return {
            "success": False,
            "destination": destination,
            "platform": platform,
            "message": "未找到该平台",
        }

    data = _search_one_platform(destination, platform)
    return {
        "success": True,
        "schema_version": 2,
        "destination": destination,
        "platform": platform,
        "data": data,
    }


def analyze_reviews_sentiment(reviews: list) -> dict:
    """
    Provide a lightweight summary for compatibility.

    Public search results do not include reliable ratings, so this function
    only reports item counts unless rating fields are explicitly present.
    """
    ratings = [r.get("rating") for r in reviews if isinstance(r.get("rating"), (int, float))]
    total = len(reviews)
    if not ratings:
        return {
            "positive_ratio": 0,
            "avg_rating": None,
            "total_reviews": total,
            "sentiment": "公开搜索结果，暂无可靠评分",
        }

    positive_count = sum(1 for rating in ratings if rating >= 4.0)
    return {
        "positive_ratio": round(positive_count / len(ratings) * 100, 1),
        "avg_rating": round(sum(ratings) / len(ratings), 1),
        "total_reviews": total,
        "sentiment": "好评居多" if positive_count / len(ratings) > 0.7 else "评价一般",
    }


def _search_one_platform(destination: str, key: str) -> dict:
    config = PLATFORM_SEARCH_CONFIG[key]
    platform_meta = PLATFORMS.get(key, {})
    platform_name = platform_meta.get("name") or config["name"]
    icon = platform_meta.get("icon") or config["icon"]
    per_platform_limit = max(2, min(4, MAX_SEARCH_RESULTS))
    query = f"{destination} {config['query_words']} site:{config['domain']}"
    response = public_web_search(query, max_results=per_platform_limit)
    items = [_as_platform_item(item, key, platform_name) for item in response.items]

    return {
        "platform": platform_name,
        "schema_version": 2,
        "platform_key": key,
        "icon": icon,
        "domain": config["domain"],
        "query": query,
        "items": items,
        "reviews": items,
        "avg_rating": None,
        "total_reviews": len(items),
        "total_items": len(items),
        "mode": response.mode,
        "engine": response.engine,
        "source_url": response.source_url,
        "warning": response.warning,
    }


def _search_all_platforms(destination: str, keys: list[str]) -> dict:
    platforms_data: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=min(5, len(keys) or 1)) as executor:
        future_map = {
            executor.submit(_search_one_platform, destination, key): key
            for key in keys
        }
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                platforms_data[key] = future.result()
            except Exception as exc:
                platforms_data[key] = _platform_error(destination, key, str(exc))

    return {key: platforms_data[key] for key in keys if key in platforms_data}


def _platform_error(destination: str, key: str, message: str) -> dict:
    config = PLATFORM_SEARCH_CONFIG[key]
    platform_meta = PLATFORMS.get(key, {})
    platform_name = platform_meta.get("name") or config["name"]
    icon = platform_meta.get("icon") or config["icon"]
    query = f"{destination} {config['query_words']} site:{config['domain']}"
    return {
        "platform": platform_name,
        "schema_version": 2,
        "platform_key": key,
        "icon": icon,
        "domain": config["domain"],
        "query": query,
        "items": [],
        "reviews": [],
        "avg_rating": None,
        "total_reviews": 0,
        "total_items": 0,
        "mode": "fallback",
        "engine": "fallback",
        "source_url": "",
        "warning": f"{platform_name}公开搜索失败：{message}",
    }


def _as_platform_item(item: dict, platform_key: str, platform_name: str) -> dict:
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "source": item.get("source", ""),
        "snippet": item.get("snippet", ""),
        "content": item.get("snippet", ""),
        "publish_date": item.get("publish_date", ""),
        "views": item.get("views"),
        "source_url": item.get("source_url", ""),
        "is_fallback": item.get("is_fallback", False),
        "platform": platform_name,
        "platform_key": platform_key,
        "tags": ["公开搜索", platform_name],
        "item_type": "public_search_result",
    }


def _platform_keys() -> list[str]:
    configured = [
        key for key in PLATFORM_SEARCH_CONFIG
        if PLATFORMS.get(key, {"enabled": True}).get("enabled", True)
    ]
    return configured or list(PLATFORM_SEARCH_CONFIG.keys())


def _overall_mode(platforms: list[dict] | dict_values) -> str:
    modes = {p.get("mode") for p in platforms}
    if modes == {"live"}:
        return "live"
    if "live" in modes:
        return "partial"
    return "fallback"


def _merge_warnings(platforms: list[dict] | dict_values) -> str:
    warnings = [p.get("warning", "") for p in platforms if p.get("warning")]
    if not warnings:
        return ""
    return "；".join(warnings[:2])
