"""
Web-search module for travel guide information.
"""

try:
    from config import MAX_SEARCH_RESULTS
except Exception:
    MAX_SEARCH_RESULTS = 10

from search_client import public_web_search


def search_web_guides(origin: str, destination: str) -> dict:
    """
    Search public web pages for travel guide information.

    The return shape keeps compatibility with the original mock implementation.
    """
    origin = (origin or "我的城市").strip()
    destination = (destination or "").strip()
    query = f"{origin}到{destination} 旅游攻略 景点 美食 交通 住宿"
    response = public_web_search(query, max_results=MAX_SEARCH_RESULTS)

    return {
        "success": True,
        "schema_version": 2,
        "query": query,
        "origin": origin,
        "destination": destination,
        "total_results": len(response.items),
        "results": response.items,
        "search_time": response.search_time,
        "mode": response.mode,
        "engine": response.engine,
        "warning": response.warning,
        "source_url": response.source_url,
    }


def extract_key_info(guides: list) -> dict:
    """
    Extract high-level metadata from normalized search results.
    """
    sources = sorted({g.get("source", "") for g in guides if g.get("source")})
    return {
        "total_guides": len(guides),
        "sources": sources,
        "latest_date": max((g.get("publish_date", "") for g in guides), default=""),
        "keywords": ["旅游攻略", "景点推荐", "美食", "交通", "住宿"],
    }
