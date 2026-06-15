"""测试 API 流式输出"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
import json

url = "http://localhost:5000/api/chat"
data = {
    "message": "我下周想从上海去北京旅行3天，帮我查一下北京天气、火车票，再给朋友zhangsan@email.com发个旅行邀请邮件"
}

print(f"发送请求: {data['message']}")
print("=" * 60)

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data_str = line[6:]
            if data_str == "[DONE]":
                print("\n[DONE] 请求完成")
                continue
            try:
                parsed = json.loads(data_str)
                msg_type = parsed.get("type")

                if msg_type == "tool_call":
                    print(f"\n[工具调用] {parsed['tool_name']}")
                    print(f"  参数: {json.dumps(parsed['tool_args'], ensure_ascii=False, indent=2)}")

                elif msg_type == "tool_result":
                    print(f"\n[工具返回] {parsed['tool_name']}:")
                    content = parsed["content"]
                    if len(content) > 300:
                        content = content[:300] + "..."
                    print(f"  {content}")

                elif msg_type == "final":
                    print("\n" + "=" * 60)
                    print("[最终回复]")
                    print("=" * 60)
                    print(parsed["content"])

                elif msg_type == "error":
                    print(f"\n[错误] {parsed['content']}")

            except json.JSONDecodeError as e:
                print(f"解析错误: {e}")
