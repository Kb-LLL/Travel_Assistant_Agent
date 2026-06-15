"""
Shared query parsing helpers for travel search features.
"""

import re


TRAVEL_SUFFIXES = (
    "的旅游攻略",
    "旅游攻略",
    "旅行攻略",
    "自由行攻略",
    "攻略",
    "怎么玩",
    "怎么去",
)


def clean_query(text: str) -> str:
    """Normalize common travel-search filler words without guessing intent."""
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ，,。.!！?？")
    for suffix in TRAVEL_SUFFIXES:
        text = text.replace(suffix, "")
    return text.strip(" ，,。.!！?？")


def parse_travel_query(query: str, default_origin: str = "我的城市") -> tuple[str, str]:
    """
    Extract origin and destination from common Chinese travel queries.

    Supported examples:
    - 从北京到上海
    - 北京到上海
    - 北京-上海
    - 北京 -> 上海
    - 上海旅游攻略
    """
    normalized = clean_query(query)
    if not normalized:
        return "", ""

    separator_patterns = [
        r"^\s*从?\s*(?P<origin>.+?)\s*(?:到|去|至|前往)\s*(?P<destination>.+?)\s*$",
        r"^\s*(?P<origin>.+?)\s*(?:->|=>|—|–|-|－|~|～)\s*(?P<destination>.+?)\s*$",
    ]

    for pattern in separator_patterns:
        match = re.match(pattern, normalized)
        if not match:
            continue
        origin = clean_query(match.group("origin").replace("从", "", 1))
        destination = clean_query(match.group("destination"))
        if origin and destination:
            return origin, destination

    return default_origin, normalized


def extract_destination(text: str) -> str:
    """Return the destination portion when a full route was entered."""
    _, destination = parse_travel_query(text)
    return destination
