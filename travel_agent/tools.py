"""
模拟工具模块 - 所有工具只返回模拟数据，不访问真实外部系统
包含三个工具：get_weather、search_train_ticket、draft_email
"""

import random
from datetime import datetime, timedelta
from langchain_core.tools import tool


@tool
def get_weather(city: str, date: str = "today") -> str:
    """查询指定城市的天气信息。

    Args:
        city: 要查询天气的城市名称，如"北京"、"上海"
        date: 查询日期，默认为"today"，也可以指定具体日期如"2026-06-05"
    """
    # 模拟天气数据
    weather_data = {
        "北京": {"temp": "28°C", "condition": "晴", "humidity": "35%", "wind": "北风3级"},
        "上海": {"temp": "30°C", "condition": "多云", "humidity": "65%", "wind": "东南风2级"},
        "广州": {"temp": "33°C", "condition": "雷阵雨", "humidity": "80%", "wind": "南风2级"},
        "成都": {"temp": "26°C", "condition": "阴", "humidity": "70%", "wind": "微风"},
        "杭州": {"temp": "29°C", "condition": "晴转多云", "humidity": "60%", "wind": "东风2级"},
        "西安": {"temp": "31°C", "condition": "晴", "humidity": "30%", "wind": "西风3级"},
        "三亚": {"temp": "34°C", "condition": "晴", "humidity": "75%", "wind": "西南风3级"},
        "昆明": {"temp": "22°C", "condition": "晴", "humidity": "50%", "wind": "微风"},
    }

    # 默认天气（城市不在预设列表中时）
    default_weather = {
        "temp": f"{random.randint(20, 35)}°C",
        "condition": random.choice(["晴", "多云", "阴", "小雨"]),
        "humidity": f"{random.randint(40, 80)}%",
        "wind": random.choice(["东风2级", "南风3级", "西风2级", "北风3级", "微风"]),
    }

    weather = weather_data.get(city, default_weather)
    target_date = date if date != "today" else datetime.now().strftime("%Y-%m-%d")

    return f"""
【天气查询结果】
城市：{city}
日期：{target_date}
温度：{weather['temp']}
天气：{weather['condition']}
湿度：{weather['humidity']}
风力：{weather['wind']}
【注意：以上为模拟数据，仅供参考】
""".strip()


@tool
def search_train_ticket(
    from_city: str, to_city: str, date: str = "today"
) -> str:
    """搜索火车票信息。

    Args:
        from_city: 出发城市，如"北京"
        to_city: 到达城市，如"上海"
        date: 出发日期，默认为"today"
    """
    target_date = date if date != "today" else datetime.now().strftime("%Y-%m-%d")

    # 模拟车次数据
    train_prefixes = ["G", "D", "K"]
    tickets = []
    for i in range(3):
        prefix = random.choice(train_prefixes)
        train_no = f"{prefix}{random.randint(100, 9999)}"
        depart_hour = random.randint(6, 20)
        depart_min = random.choice([0, 15, 30, 45])
        duration_hour = random.randint(2, 8)
        duration_min = random.choice([0, 15, 30, 45])
        price = random.randint(150, 800)
        seats_left = random.randint(0, 50)

        tickets.append(
            {
                "train_no": train_no,
                "depart": f"{depart_hour:02d}:{depart_min:02d}",
                "duration": f"{duration_hour}小时{duration_min}分钟",
                "price": f"¥{price}",
                "seats": seats_left,
            }
        )

    # 按出发时间排序
    tickets.sort(key=lambda x: x["depart"])

    result_lines = [
        "【火车票查询结果】",
        f"出发城市：{from_city}",
        f"到达城市：{to_city}",
        f"出发日期：{target_date}",
        "",
        "可选车次：",
    ]

    for idx, t in enumerate(tickets, 1):
        result_lines.append(
            f"  {idx}. {t['train_no']} | "
            f"出发: {t['depart']} | "
            f"历时: {t['duration']} | "
            f"票价: {t['price']} | "
            f"余票: {t['seats']}"
        )

    result_lines.append("\n【注意：以上为模拟数据，仅供参考】")

    return "\n".join(result_lines)


@tool
def draft_email(to: str, subject: str, body_outline: str) -> str:
    """根据收件人、主题和内容大纲，生成一封邮件草稿。

    Args:
        to: 收件人邮箱或姓名
        subject: 邮件主题
        body_outline: 邮件内容大纲或要点
    """
    # 根据主题生成邮件模板
    templates = {
        "旅行邀请": f"""亲爱的 {to}：

你好！希望这封邮件找到你一切安好。

我想邀请你一起进行一次愉快的旅行。根据{body_outline}，我已经做了详细的行程规划。

旅行亮点包括：
- 精心挑选的目的地，风景优美
- 合理的行程安排，劳逸结合
- 丰富的美食体验

如果你有兴趣，请回复这封邮件，我们可以进一步讨论具体的出行时间和细节。

期待你的回复！

祝好！""",

        "行程确认": f"""{to} 你好：

关于即将到来的旅行，特此确认以下行程安排：

{body_outline}

请确认以上信息是否正确。如有任何疑问或需要调整，请随时联系我。

祝旅途愉快！""",

        "默认": f"""{to} 你好：

主题：{subject}

{body_outline}

如有任何问题，请随时联系我。

祝好！""",
    }

    # 根据主题关键词选择模板
    body = templates["默认"]
    for key in templates:
        if key != "默认" and key in subject:
            body = templates[key]
            break

    return f"""
【邮件草稿】
收件人：{to}
主题：{subject}
-------------------
{body}
-------------------
【注意：以上为模拟生成的邮件草稿】
""".strip()
