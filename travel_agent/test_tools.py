"""
工具测试脚本 - 验证三个模拟工具正常工作
运行方式：python test_tools.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from tools import get_weather, search_train_ticket, draft_email


def test_all_tools():
    print("=" * 60)
    print("  工具测试 - 验证模拟工具")
    print("=" * 60)

    # 测试 get_weather
    print("\n[测试1] get_weather - 查询北京天气")
    print("-" * 40)
    result = get_weather.invoke({"city": "北京", "date": "2026-06-10"})
    print(result)

    # 测试 search_train_ticket
    print("\n[测试2] search_train_ticket - 上海到北京")
    print("-" * 40)
    result = search_train_ticket.invoke(
        {"from_city": "上海", "to_city": "北京", "date": "2026-06-10"}
    )
    print(result)

    # 测试 draft_email
    print("\n[测试3] draft_email - 旅行邀请邮件")
    print("-" * 40)
    result = draft_email.invoke(
        {
            "to": "张三",
            "subject": "北京旅行邀请",
            "body_outline": "下周一起去北京玩3天，看故宫爬长城",
        }
    )
    print(result)

    print("\n" + "=" * 60)
    print("  所有工具测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_all_tools()
