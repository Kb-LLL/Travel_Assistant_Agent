"""
Public web-search client used by the travel guide features.

The client only reads publicly visible search-result pages and normalizes
titles, snippets, and links. It does not scrape logged-in platform content.
"""

from __future__ import annotations

import html
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

try:
    import requests
except ModuleNotFoundError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    BeautifulSoup = None

try:
    from config import REQUEST_TIMEOUT
except Exception:
    REQUEST_TIMEOUT = 10


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)


@dataclass
class SearchResponse:
    items: list[dict]
    query: str
    mode: str
    source_url: str
    search_time: float
    warning: str = ""
    engine: str = ""


def public_web_search(query: str, max_results: int = 8) -> SearchResponse:
    """
    Search public web result pages and return normalized items.

    DuckDuckGo's HTML endpoint is tried first because it is simple and stable
    for public search pages. Bing is used as a backup. If both fail, a fallback
    item points the user to a normal search results page.
    """
    started = time.perf_counter()
    query = (query or "").strip()
    search_url = _duckduckgo_url(query)
    errors: list[str] = []

    for engine, fetcher in (
        ("duckduckgo", _search_duckduckgo),
        ("bing", _search_bing),
    ):
        try:
            items, source_url = fetcher(query, max_results)
            items = _dedupe_results(items)[:max_results]
            if items:
                return SearchResponse(
                    items=items,
                    query=query,
                    mode="live",
                    source_url=source_url,
                    search_time=round(time.perf_counter() - started, 2),
                    engine=engine,
                )
            errors.append(f"{engine}: no results")
        except Exception as exc:
            errors.append(f"{engine}: {exc}")

    warning = "公开搜索暂时不可用，已提供可点击的搜索入口。"
    fallback = {
        "title": f"打开搜索结果：{query}",
        "url": search_url,
        "source": "搜索入口",
        "snippet": warning,
        "publish_date": "",
        "views": None,
        "source_url": search_url,
        "is_fallback": True,
    }
    return SearchResponse(
        items=[fallback],
        query=query,
        mode="fallback",
        source_url=search_url,
        search_time=round(time.perf_counter() - started, 2),
        warning=warning,
        engine="fallback",
    )


def normalize_result(title: str, url: str, snippet: str, source_url: str = "") -> dict:
    url = _unwrap_url(url)
    return {
        "title": _clean_text(title) or "未命名结果",
        "url": url,
        "source": _source_name(url),
        "snippet": _clean_text(snippet),
        "publish_date": "",
        "views": None,
        "source_url": source_url,
    }


def _search_duckduckgo(query: str, max_results: int) -> tuple[list[dict], str]:
    _ensure_search_dependencies()
    source_url = "https://duckduckgo.com/html/"
    response = requests.get(
        source_url,
        params={"q": query, "kl": "cn-zh"},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[dict] = []

    for result in soup.select(".result"):
        link = result.select_one(".result__a")
        if not link:
            continue
        snippet = result.select_one(".result__snippet")
        item = normalize_result(
            title=link.get_text(" ", strip=True),
            url=link.get("href", ""),
            snippet=snippet.get_text(" ", strip=True) if snippet else "",
            source_url=response.url,
        )
        if item["url"]:
            items.append(item)
        if len(items) >= max_results:
            break

    return items, response.url


def _search_bing(query: str, max_results: int) -> tuple[list[dict], str]:
    _ensure_search_dependencies()
    source_url = "https://www.bing.com/search"
    response = requests.get(
        source_url,
        params={"q": query, "mkt": "zh-CN"},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[dict] = []

    for result in soup.select("li.b_algo"):
        link = result.select_one("h2 a")
        if not link:
            continue
        snippet = result.select_one("p")
        item = normalize_result(
            title=link.get_text(" ", strip=True),
            url=link.get("href", ""),
            snippet=snippet.get_text(" ", strip=True) if snippet else "",
            source_url=response.url,
        )
        if item["url"]:
            items.append(item)
        if len(items) >= max_results:
            break

    return items, response.url


def _dedupe_results(items: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in items:
        url_key = item.get("url", "").split("#", 1)[0].rstrip("/")
        title_key = item.get("title", "").lower()
        key = url_key or title_key
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _unwrap_url(url: str) -> str:
    url = html.unescape(url or "").strip()
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        wrapped = parse_qs(parsed.query).get("uddg", [""])[0]
        if wrapped:
            return unquote(wrapped)
    return url


def _source_name(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    return host or "公开网页"


def _clean_text(value: str) -> str:
    value = html.unescape(value or "")
    return " ".join(value.split())


def _duckduckgo_url(query: str) -> str:
    return f"https://duckduckgo.com/?q={quote_plus(query)}"


def _ensure_search_dependencies():
    if requests is None:
        raise RuntimeError("requests 未安装，无法执行公开网页搜索")
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 未安装，无法解析公开网页搜索结果")
