"""
多 Agent 协作方案（可选扩展）
==============================
使用 LangGraph 的 StateGraph 构建多 Agent 系统：
- 天气Agent: 负责查询天气
- 交通Agent: 负责查询火车票
- 邮件Agent: 负责撰写邮件
- 协调Agent: 负责整合信息并给出最终建议

运行方式：
    python multi_agent.py
"""

from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from config import ACTIVE_API_KEY, ACTIVE_BASE_URL, ACTIVE_MODEL
from tools import get_weather, search_train_ticket, draft_email


# ========== 状态定义 ==========
class AgentState(TypedDict):
    messages: Annotated[list, "对话消息列表"]
    weather_info: str
    ticket_info: str
    email_draft: str
    final_advice: str


# ========== 创建各子Agent ==========
def create_llm():
    return ChatOpenAI(
        model=ACTIVE_MODEL,
        api_key=ACTIVE_API_KEY,
        base_url=ACTIVE_BASE_URL,
        temperature=0.7,
        streaming=True,
    )


def weather_agent(state: AgentState) -> AgentState:
    """天气Agent - 负责查询天气"""
    print("\n[天气Agent] 正在查询天气信息...")
    llm = create_llm()
    agent = create_react_agent(
        model=llm,
        tools=[get_weather],
        prompt="你是天气查询专家。根据用户需求查询相关城市天气，并简要分析天气对旅行的影响。用中文回复。",
    )

    last_msg = state["messages"][-1].content
    result = agent.invoke({"messages": [HumanMessage(content=last_msg)]})
    weather_info = result["messages"][-1].content

    print(f"[天气Agent] 完成天气查询")
    return {**state, "weather_info": weather_info}


def ticket_agent(state: AgentState) -> AgentState:
    """交通Agent - 负责查询火车票"""
    print("\n[交通Agent] 正在查询火车票...")
    llm = create_llm()
    agent = create_react_agent(
        model=llm,
        tools=[search_train_ticket],
        prompt="你是交通出行专家。根据用户需求搜索合适的火车票，并推荐最佳方案。用中文回复。",
    )

    last_msg = state["messages"][-1].content
    result = agent.invoke({"messages": [HumanMessage(content=last_msg)]})
    ticket_info = result["messages"][-1].content

    print(f"[交通Agent] 完成火车票查询")
    return {**state, "ticket_info": ticket_info}


def email_agent(state: AgentState) -> AgentState:
    """邮件Agent - 负责撰写邮件"""
    print("\n[邮件Agent] 正在生成邮件草稿...")
    llm = create_llm()
    agent = create_react_agent(
        model=llm,
        tools=[draft_email],
        prompt="你是邮件撰写专家。根据用户需求和已查询的信息，生成合适的邮件草稿。用中文回复。",
    )

    context = (
        f"用户需求: {state['messages'][-1].content}\n"
        f"天气信息: {state.get('weather_info', '暂无')}\n"
        f"交通信息: {state.get('ticket_info', '暂无')}\n"
        "请根据以上信息生成一封旅行邀请邮件。"
    )
    result = agent.invoke({"messages": [HumanMessage(content=context)]})
    email_draft = result["messages"][-1].content

    print(f"[邮件Agent] 完成邮件草稿")
    return {**state, "email_draft": email_draft}


def coordinator_agent(state: AgentState) -> AgentState:
    """协调Agent - 整合所有信息给出最终建议"""
    print("\n[协调Agent] 正在整合信息并生成旅行建议...")

    llm = create_llm()
    prompt = f"""你是旅行规划协调专家。请根据以下信息，为用户生成一份完整的旅行建议。

天气信息：
{state.get('weather_info', '暂无')}

交通信息：
{state.get('ticket_info', '暂无')}

邮件草稿：
{state.get('email_draft', '暂无')}

请给出：
1. 旅行总结和建议
2. 注意事项
3. 推荐的下一步行动"""

    result = llm.invoke([HumanMessage(content=prompt)])
    final_advice = result.content

    print(f"[协调Agent] 完成旅行建议生成")
    return {**state, "final_advice": final_advice}


# ========== 构建多Agent图 ==========
def create_multi_agent_graph():
    """创建多Agent协作图"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("weather_agent", weather_agent)
    workflow.add_node("ticket_agent", ticket_agent)
    workflow.add_node("email_agent", email_agent)
    workflow.add_node("coordinator", coordinator_agent)

    # 设置入口
    workflow.set_entry_point("weather_agent")

    # 设置边（顺序执行各子Agent）
    workflow.add_edge("weather_agent", "ticket_agent")
    workflow.add_edge("ticket_agent", "email_agent")
    workflow.add_edge("email_agent", "coordinator")
    workflow.add_edge("coordinator", END)

    return workflow.compile()


def run_multi_agent(user_input: str):
    """运行多Agent系统"""
    graph = create_multi_agent_graph()

    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "weather_info": "",
        "ticket_info": "",
        "email_draft": "",
        "final_advice": "",
    }

    print("=" * 60)
    print(f"用户输入: {user_input}")
    print("=" * 60)

    result = graph.invoke(initial_state)

    # 打印各Agent的输出
    print("\n" + "=" * 60)
    print("【各Agent输出汇总】")
    print("=" * 60)

    print(f"\n--- 天气Agent ---")
    print(result.get("weather_info", "无"))

    print(f"\n--- 交通Agent ---")
    print(result.get("ticket_info", "无"))

    print(f"\n--- 邮件Agent ---")
    print(result.get("email_draft", "无"))

    print(f"\n{'=' * 60}")
    print("【最终旅行建议】")
    print("=" * 60)
    print(result.get("final_advice", "无"))
    print("=" * 60)


if __name__ == "__main__":
    user_input = (
        "我计划下周从上海去北京旅行3天，请帮我：\n"
        "1. 查询北京天气\n"
        "2. 搜索火车票\n"
        "3. 给朋友张三(zhangsan@email.com)发旅行邀请邮件"
    )
    run_multi_agent(user_input)
