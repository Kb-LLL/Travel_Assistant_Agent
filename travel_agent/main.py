"""
旅行助手 Agent - 综合实验项目
================================
功能说明：
- 使用 LangGraph create_react_agent 创建 Agent
- 包含三个模拟工具：get_weather、search_train_ticket、draft_email
- 所有工具只返回模拟数据，不访问真实外部系统
- Agent 根据用户输入决定调用哪些工具
- 使用 stream 模式打印中间过程（工具调用、工具返回等）
- 最终输出旅行建议和邮件草稿

运行方式：
    python main.py

验收标准：
1. 能看到工具调用：运行后观察 "[Agent 决策] 调用工具: xxx" 输出
2. 能解释每个工具作用：
   - get_weather: 查询指定城市天气信息（模拟数据）
   - search_train_ticket: 搜索火车票信息（模拟数据）
   - draft_email: 根据收件人和主题生成邮件草稿（模拟数据）
3. 能提交运行截图：截取完整运行过程，包含工具调用和最终输出
"""

import sys
import io

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from agent import create_travel_agent, run_with_stream


def main():
    print("=" * 60)
    print("  旅行助手 Agent - 综合实验项目")
    print("=" * 60)
    print()
    print("工具说明：")
    print("  1. get_weather          - 查询城市天气（模拟数据）")
    print("  2. search_train_ticket  - 搜索火车票信息（模拟数据）")
    print("  3. draft_email          - 生成邮件草稿（模拟数据）")
    print()

    # 初始化 Agent
    print("正在初始化 Agent...")
    agent = create_travel_agent()
    print("Agent 初始化完成！")
    print()

    # 预设示例
    examples = [
        (
            "示例1: 完整旅行规划",
            "我计划下周去北京旅行3天，请帮我：\n"
            "1. 查询北京的天气\n"
            "2. 搜索从上海到北京的火车票\n"
            "3. 给我的朋友张三(zhangsan@email.com)发一封旅行邀请邮件",
        ),
        (
            "示例2: 多城市天气对比",
            "成都和杭州这两天天气怎么样？哪个更适合旅游？",
        ),
        (
            "示例3: 仅查火车票",
            "帮我查一下从广州到西安的火车票",
        ),
    ]

    # 运行预设示例
    print(">>> 运行预设示例 <<<\n")
    for title, query in examples:
        print(f"\n{'>' * 20} {title} {'<' * 20}")
        run_with_stream(agent, query)
        print()

    # 交互模式
    print("\n>>> 交互模式 <<<")
    print("输入旅行需求，Agent 将为你查询天气、车票并生成邮件。")
    print("输入 'quit' 退出程序。\n")

    while True:
        try:
            user_input = input("请输入你的旅行需求: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n感谢使用旅行助手，再见！")
            break

        if user_input.lower() in ("quit", "exit", "q", "退出"):
            print("感谢使用旅行助手，再见！")
            break

        if user_input:
            run_with_stream(agent, user_input)
            print()


if __name__ == "__main__":
    main()
