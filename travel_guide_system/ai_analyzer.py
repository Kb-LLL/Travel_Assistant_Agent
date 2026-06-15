"""
AI analysis module for public travel search results.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import MIMO_API_KEY, MIMO_BASE_URL, MIMO_MODEL


def create_llm():
    """Create the configured MiMo LLM instance."""
    return ChatOpenAI(
        model=MIMO_MODEL,
        api_key=MIMO_API_KEY,
        base_url=MIMO_BASE_URL,
        temperature=0.7,
        streaming=True,
    )


def analyze_travel_guide(origin: str, destination: str, web_guides: dict, platform_reviews: dict) -> dict:
    """
    Generate a complete travel-guide analysis from normalized search data.
    """
    llm = create_llm()
    prompt = _build_analysis_prompt(origin, destination, web_guides, platform_reviews)

    try:
        response = llm.invoke([
            SystemMessage(content=_system_prompt()),
            HumanMessage(content=prompt),
        ])

        return {
            "success": True,
            "analysis": response.content,
            "origin": origin,
            "destination": destination,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "origin": origin,
            "destination": destination,
        }


def stream_analysis(origin: str, destination: str, web_guides: dict, platform_reviews: dict):
    """
    Stream a complete travel-guide analysis from normalized search data.
    """
    llm = create_llm()
    prompt = _build_analysis_prompt(origin, destination, web_guides, platform_reviews)

    try:
        for chunk in llm.stream([
            SystemMessage(content=_system_prompt()),
            HumanMessage(content=prompt),
        ]):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        yield f"\n\n[分析出错: {str(e)}]"


def _system_prompt() -> str:
    return (
        "你是一个谨慎、实用的旅游攻略分析师。你必须基于用户提供的公开搜索结果和摘要进行分析，"
        "不要编造评分、评论人数、门票价格或营业时间。信息不足时请明确写“未在公开摘要中确认”。"
    )


def _build_analysis_prompt(origin: str, destination: str, web_guides: dict, platform_reviews: dict) -> str:
    web_summary = _format_web_results(web_guides)
    platform_summary = _format_platform_results(platform_reviews)
    warning_text = _format_warnings(web_guides, platform_reviews)

    return f"""请基于以下公开搜索资料，为用户生成一份{origin}到{destination}的旅游攻略。

## 网页攻略搜索结果
{web_summary}

## 多平台公开搜索结果
{platform_summary}

## 搜索状态提示
{warning_text}

请输出以下结构：
1. **结论速览**：用 3-5 条概括是否值得去、适合人群、建议天数。
2. **交通建议**：从{origin}到{destination}的可行方式；如果搜索摘要没有确认具体票价或班次，请说明未确认。
3. **景点与体验**：列出高频出现或标题摘要中明确出现的景点/玩法，并标注来自哪些来源。
4. **美食与住宿线索**：只总结公开摘要中出现的信息，不要编造店名或价格。
5. **预算与时间安排**：给 3-5 天行程框架；价格未知时给“需二次确认”的提醒。
6. **避坑提醒**：结合公开摘要中的排队、旺季、交通、预订等线索，没有线索就写未确认。
7. **参考来源**：列出 5 个以内最有用的标题和链接。

写作要求：
- 用中文，结构清晰，适合直接给旅行者阅读。
- 明确区分“搜索结果显示”和“需要二次确认”。
- 不要使用不存在的评分、用户名、评论数量。"""


def _format_web_results(web_guides: dict) -> str:
    results = web_guides.get("results", [])[:8]
    if not results:
        return "未获得网页攻略结果。"

    lines = []
    for index, item in enumerate(results, 1):
        lines.append(
            f"{index}. {item.get('title', '未命名')} | {item.get('source', '公开网页')}\n"
            f"   摘要：{item.get('snippet', '') or '无摘要'}\n"
            f"   链接：{item.get('url', '')}"
        )
    return "\n".join(lines)


def _format_platform_results(platform_reviews: dict) -> str:
    platforms = platform_reviews.get("platforms", {})
    if not platforms:
        return "未获得多平台公开搜索结果。"

    sections = []
    for key, data in platforms.items():
        items = data.get("items") or data.get("reviews") or []
        lines = [
            f"【{data.get('platform', key)}】公开结果 {len(items)} 条，模式：{data.get('mode', 'unknown')}"
        ]
        for item in items[:3]:
            lines.append(
                f"- {item.get('title', '未命名')} | {item.get('source', '公开网页')}\n"
                f"  摘要：{item.get('snippet') or item.get('content') or '无摘要'}\n"
                f"  链接：{item.get('url', '')}"
            )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _format_warnings(web_guides: dict, platform_reviews: dict) -> str:
    warnings = []
    for data in (web_guides, platform_reviews):
        warning = data.get("warning")
        if warning:
            warnings.append(warning)
    return "\n".join(f"- {warning}" for warning in warnings) if warnings else "公开搜索正常返回。"
