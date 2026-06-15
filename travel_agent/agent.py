"""
旅行助手 Agent - 使用 LangGraph 创建的 ReAct Agent
通过小米 MiMo API 作为 LLM 后端
使用 stream 模式打印中间过程
"""

import sys
import io
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import ACTIVE_API_KEY, ACTIVE_BASE_URL, ACTIVE_MODEL
from tools import get_weather, search_train_ticket, draft_email

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def safe_print(*args, **kwargs):
    """安全打印，处理编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("utf-8", errors="replace").decode("utf-8"), **kwargs)


def create_travel_agent():
    """创建旅行助手 Agent"""

    # 1. 初始化 LLM（连接小米 MiMo API）
    llm = ChatOpenAI(
        model=ACTIVE_MODEL,
        api_key=ACTIVE_API_KEY,
        base_url=ACTIVE_BASE_URL,
        temperature=0.7,
        streaming=True,  # 启用流式输出
    )

    # 2. 注册工具
    tools = [get_weather, search_train_ticket, draft_email]

    # 3. 创建 ReAct Agent（使用 create_agent）
    system_prompt = """你是一个专业的旅行助手Agent。你的职责是帮助用户规划旅行。

你可以使用以下工具：
- get_weather: 查询城市天气，帮助用户了解目的地天气情况
- search_train_ticket: 搜索火车票，帮助用户规划出行交通
- draft_email: 生成邮件草稿，帮助用户发送旅行邀请或行程确认邮件

工作流程：
1. 根据用户需求，先查询相关城市的天气
2. 搜索合适的火车票信息
3. 如果用户需要，生成旅行邀请或行程确认的邮件草稿
4. 综合所有信息，给出旅行建议

请用中文回复，并确保信息清晰、有条理。"""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent


def run_with_stream(agent, user_input: str):
    """使用 stream 模式运行 Agent，打印中间过程"""

    print("=" * 60)
    print(f"用户输入: {user_input}")
    print("=" * 60)

    # 使用 stream 获取中间过程
    for event in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        stream_mode="values",
    ):
        for key, value in event.items():
            if key == "messages":
                last_message = value[-1]
                msg_type = type(last_message).__name__

                # 打印不同类型的消息
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    # Agent 决定调用工具
                    for tc in last_message.tool_calls:
                        print(f"\n[Agent 决策] 调用工具: {tc['name']}")
                        print(f"  参数: {tc['args']}")

                elif msg_type == "ToolMessage":
                    # 工具返回结果
                    print(f"\n[工具返回] {last_message.name}:")
                    # 截断过长的输出
                    content = last_message.content
                    if len(content) > 500:
                        content = content[:500] + "\n  ... (输出已截断)"
                    print(f"  {content}")

                elif hasattr(last_message, "content") and last_message.content:
                    if msg_type == "AIMessage":
                        # AI 的最终回复
                        # 只在最后输出完整回复
                        pass

    # 获取最终回复
    final_output = event["messages"][-1].content

    print("\n" + "=" * 60)
    print("最终回复:")
    print("=" * 60)
    print(final_output)
    print("=" * 60)

    return final_output


def main():
    """主函数 - 演示 Agent 功能"""

    print("正在初始化旅行助手 Agent...")
    print(f"使用 LLM: {ACTIVE_MODEL} @ {ACTIVE_BASE_URL}")
    print()

    agent = create_travel_agent()

    # 示例1：规划北京旅行
    user_input_1 = (
        "我计划下周去北京旅行3天，请帮我：\n"
        "1. 查询北京的天气\n"
        "2. 搜索从上海到北京的火车票\n"
        "3. 给我的朋友张三(zhangsan@email.com)发一封旅行邀请邮件"
    )

    print("\n" + ">>> 示例1: 规划北京旅行 <<<")
    run_with_stream(agent, user_input_1)

    # 示例2：简单的天气查询
    print("\n\n")
    user_input_2 = "成都和杭州这两天天气怎么样？适合旅游吗？"

    print(">>> 示例2: 天气查询 <<<")
    run_with_stream(agent, user_input_2)

    # 交互模式
    print("\n\n>>> 交互模式 <<<")
    print("输入旅行需求，Agent 将为你提供帮助。输入 'quit' 退出。")

    while True:
        user_input = input("\n请输入你的旅行需求: ").strip()
        if user_input.lower() in ("quit", "exit", "q", "退出"):
            print("感谢使用旅行助手，再见！")
            break
        if user_input:
            run_with_stream(agent, user_input)


if __name__ == "__main__":
    main()
