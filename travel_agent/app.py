"""
Flask 后端 API - 为前端提供 Agent 接口
"""

import sys
import io
import json
import queue
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import ACTIVE_API_KEY, ACTIVE_BASE_URL, ACTIVE_MODEL
from tools import get_weather, search_train_ticket, draft_email
from email_sender import send_email, get_smtp_help

# 导入旅游攻略系统模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'travel_guide_system'))
from web_search import search_web_guides
from platform_reviews import search_platform_reviews
from ai_analyzer import stream_analysis
from cache_manager import get_cache, set_cache
from query_parser import parse_travel_query

app = Flask(__name__, static_folder="static")
CORS(app)

# ========== Agent 初始化 ==========
llm = ChatOpenAI(
    model=ACTIVE_MODEL,
    api_key=ACTIVE_API_KEY,
    base_url=ACTIVE_BASE_URL,
    temperature=0.7,
    streaming=True,
)

tools = [get_weather, search_train_ticket, draft_email]

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

agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)


# ========== 路由 ==========
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """流式聊天接口 - 使用 SSE 返回中间过程和最终结果"""
    data = request.json
    user_input = data.get("message", "")

    if not user_input:
        return jsonify({"error": "消息不能为空"}), 400

    def generate():
        try:
            for event in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                stream_mode="values",
            ):
                for key, value in event.items():
                    if key == "messages":
                        last_message = value[-1]
                        msg_type = type(last_message).__name__

                        # Agent 决定调用工具
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tc in last_message.tool_calls:
                                data = json.dumps(
                                    {
                                        "type": "tool_call",
                                        "tool_name": tc["name"],
                                        "tool_args": tc["args"],
                                    },
                                    ensure_ascii=False,
                                )
                                yield f"data: {data}\n\n"

                        # 工具返回结果
                        elif msg_type == "ToolMessage":
                            data = json.dumps(
                                {
                                    "type": "tool_result",
                                    "tool_name": last_message.name,
                                    "content": last_message.content,
                                },
                                ensure_ascii=False,
                            )
                            yield f"data: {data}\n\n"

            # 最终回复
            final_output = event["messages"][-1].content
            data = json.dumps(
                {"type": "final", "content": final_output}, ensure_ascii=False
            )
            yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            data = json.dumps(
                {"type": "error", "content": str(e)}, ensure_ascii=False
            )
            yield f"data: {data}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/tools", methods=["GET"])
def list_tools():
    """列出所有可用工具"""
    tool_list = [
        {
            "name": "get_weather",
            "description": "查询指定城市的天气信息（模拟数据）",
            "parameters": ["city: 城市名称", "date: 日期（可选）"],
        },
        {
            "name": "search_train_ticket",
            "description": "搜索火车票信息（模拟数据）",
            "parameters": ["from_city: 出发城市", "to_city: 到达城市", "date: 日期（可选）"],
        },
        {
            "name": "draft_email",
            "description": "生成邮件草稿（可真正发送邮件）",
            "parameters": ["to: 收件人", "subject: 主题", "body_outline: 内容大纲"],
        },
    ]
    return jsonify(tool_list)


@app.route("/api/send-email", methods=["POST"])
def send_email_api():
    """发送邮件 API"""
    data = request.json
    
    sender_email = data.get("sender_email", "")
    sender_password = data.get("sender_password", "")
    receiver_email = data.get("receiver_email", "")
    subject = data.get("subject", "")
    body = data.get("body", "")
    
    if not all([sender_email, sender_password, receiver_email, subject, body]):
        return jsonify({"success": False, "message": "所有字段都是必填的"}), 400
    
    result = send_email(
        sender_email=sender_email,
        sender_password=sender_password,
        receiver_email=receiver_email,
        subject=subject,
        body=body,
    )
    
    return jsonify(result)


@app.route("/api/smtp-help", methods=["POST"])
def smtp_help():
    """获取 SMTP 授权码帮助信息"""
    data = request.json
    email = data.get("email", "")
    
    if not email:
        return jsonify({"help": "请输入邮箱地址"}), 400
    
    help_text = get_smtp_help(email)
    return jsonify({"help": help_text})


@app.route("/api/chat-and-send", methods=["POST"])
def chat_and_send():
    """处理带邮箱信息的请求 - AI生成内容并自动发送"""
    data = request.json
    
    user_message = data.get("message", "")
    sender_email = data.get("sender_email", "")
    sender_password = data.get("sender_password", "")
    receiver_email = data.get("receiver_email", "")
    receiver_name = data.get("receiver_name", "")
    
    print(f"[邮件请求] 发件人: {sender_email}, 收件人: {receiver_email}")
    
    if not all([user_message, sender_email, sender_password, receiver_email]):
        return jsonify({"success": False, "message": "缺少必要信息"}), 400
    
    def generate():
        try:
            # 构建给 Agent 的请求，包含邮箱信息
            agent_message = f"""{user_message}

【邮件发送信息】
发件人邮箱：{sender_email}
收件人邮箱：{receiver_email}
收件人称呼：{receiver_name if receiver_name else '朋友'}

请帮我：
1. 查询相关的天气和火车票信息
2. 生成一封专业的旅行邀请邮件
3. 邮件内容要包含查询到的天气和交通信息
4. 请直接输出邮件的完整内容（包括主题和正文），我会用这些内容发送邮件"""

            email_subject = ""
            email_body = ""
            
            for event in agent.stream(
                {"messages": [{"role": "user", "content": agent_message}]},
                stream_mode="values",
            ):
                for key, value in event.items():
                    if key == "messages":
                        last_message = value[-1]
                        msg_type = type(last_message).__name__

                        # Agent 决定调用工具
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tc in last_message.tool_calls:
                                tool_data = json.dumps(
                                    {
                                        "type": "tool_call",
                                        "tool_name": tc["name"],
                                        "tool_args": tc["args"],
                                    },
                                    ensure_ascii=False,
                                )
                                yield f"data: {tool_data}\n\n"

                        # 工具返回结果
                        elif msg_type == "ToolMessage":
                            tool_data = json.dumps(
                                {
                                    "type": "tool_result",
                                    "tool_name": last_message.name,
                                    "content": last_message.content,
                                },
                                ensure_ascii=False,
                            )
                            yield f"data: {tool_data}\n\n"

            # 获取最终回复
            final_output = event["messages"][-1].content
            
            # 从 Agent 回复中提取邮件内容
            # 尝试提取主题和正文
            lines = final_output.split('\n')
            for i, line in enumerate(lines):
                if '主题' in line or 'Subject' in line:
                    email_subject = line.split('：')[-1].split(':')[-1].strip()
                    # 获取正文（主题之后的内容）
                    email_body = '\n'.join(lines[i+1:]).strip()
                    break
            
            # 如果没有提取到主题，使用默认主题
            if not email_subject:
                email_subject = f"旅行邀请 - 来自{sender_email.split('@')[0]}"
            
            # 如果没有提取到正文，使用整个回复
            if not email_body:
                email_body = final_output
            
            # 发送邮件
            print(f"[准备发送邮件] 主题: {email_subject}")
            print(f"[邮件内容长度] {len(email_body)} 字符")
            send_result = send_email(
                sender_email=sender_email,
                sender_password=sender_password,
                receiver_email=receiver_email,
                subject=email_subject,
                body=email_body,
            )
            print(f"[发送结果] {send_result}")
            
            # 发送最终结果
            result_data = json.dumps(
                {
                    "type": "final",
                    "content": final_output,
                    "email_sent": send_result["success"],
                    "email_message": send_result["message"],
                    "email_subject": email_subject,
                },
                ensure_ascii=False,
            )
            yield f"data: {result_data}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_data = json.dumps(
                {"type": "error", "content": str(e)}, ensure_ascii=False
            )
            yield f"data: {error_data}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def parse_query(query: str) -> tuple:
    """解析用户查询，提取出发地和目的地"""
    return parse_travel_query(query)


def _request_data() -> dict:
    return request.get_json(silent=True) or {}


def _is_search_cache(data: dict) -> bool:
    return (
        isinstance(data, dict)
        and data.get("schema_version") == 2
        and data.get("mode") in {"live", "partial", "fallback"}
    )


def _get_web_results(origin: str, destination: str) -> dict:
    cached = get_cache(origin, destination, "web")
    if _is_search_cache(cached):
        result = dict(cached)
        result["from_cache"] = True
        return result

    result = search_web_guides(origin, destination)
    if result.get("success"):
        set_cache(origin, destination, "web", result)
    return result


def _get_review_results(origin: str, destination: str) -> dict:
    cached = get_cache(origin, destination, "reviews")
    if _is_search_cache(cached):
        result = dict(cached)
        result["from_cache"] = True
        return result

    result = search_platform_reviews(destination)
    if result.get("success"):
        set_cache(origin, destination, "reviews", result)
    return result


@app.route("/api/web-search", methods=["POST"])
def web_search_api():
    """网页搜索接口"""
    data = _request_data()
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"success": False, "message": "请输入搜索内容"}), 400
    
    origin, destination = parse_query(query)
    if not destination:
        return jsonify({"success": False, "message": "无法识别目的地"}), 400
    
    try:
        result = _get_web_results(origin, destination)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/platform-search", methods=["POST"])
def platform_search_api():
    """多平台评论搜索接口"""
    data = _request_data()
    query = (data.get("destination") or data.get("query") or "").strip()
    
    if not query:
        return jsonify({"success": False, "message": "请输入目的地"}), 400

    origin, destination = parse_query(query)
    if not destination:
        return jsonify({"success": False, "message": "无法识别目的地"}), 400
    
    try:
        result = _get_review_results(origin, destination)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/agent-run", methods=["POST"])
def agent_run_api():
    """多Agent运行接口 - 并行执行，每个Agent独立流式输出"""
    data = _request_data()
    message = (data.get("message") or "").strip()
    agents = data.get("agents", [])

    if not message:
        return jsonify({"success": False, "message": "请输入旅行需求"}), 400

    if not agents:
        return jsonify({"success": False, "message": "请至少选择一个Agent"}), 400

    agent_configs = {
        "demand": {
            "name": "需求分析",
            "prompt": """你是需求分析Agent。你的任务是理解用户的旅行需求，提取关键信息。
请分析用户的输入，提取以下信息：
- 出发地
- 目的地
- 出行天数
- 预算
- 人数
- 偏好（美食、自然、亲子、情侣、文化、拍照等）
- 限制条件（不想太累、不坐夜车、不吃辣等）

请以清晰的格式输出分析结果。""",
            "use_tools": False
        },
        "scenic": {
            "name": "景点推荐",
            "prompt": """你是景点推荐Agent。你的任务是根据用户的目的地和偏好，推荐合适的景点。
请推荐：
- 热门景点
- 小众景点
- 适合用户偏好的景点
- 估算每个景点的游玩时间
- 景点之间的距离关系

请给出详细的景点推荐，包含名称、推荐理由、建议游玩时间。""",
            "use_tools": True
        },
        "route": {
            "name": "路线规划",
            "prompt": """你是路线规划Agent。你的任务是把景点安排成合理的行程。
请考虑：
- 哪些景点离得近，可以安排在一起
- 每天不要太累
- 上午/下午/晚上怎么安排
- 景点开放时间
- 交通时间

请输出每日详细行程安排。""",
            "use_tools": True
        },
        "hotel": {
            "name": "酒店推荐",
            "prompt": """你是酒店推荐Agent。你的任务是为用户推荐住宿方案。
请考虑：
- 用户预算
- 距离景点远近
- 商圈位置
- 交通便利性
- 用户偏好（便宜、舒适、高端、靠地铁等）

请推荐合适的住宿区域和酒店类型。""",
            "use_tools": False
        },
        "transport": {
            "name": "交通规划",
            "prompt": """你是交通规划Agent。你的任务是规划出行交通。
请规划：
- 出发地到目的地的交通方式
- 景点之间的交通
- 地铁/公交/打车建议
- 估算时间和费用

请给出详细的交通方案。请先查询天气和火车票信息。""",
            "use_tools": True
        },
        "budget": {
            "name": "预算计算",
            "prompt": """你是预算计算Agent。你的任务是计算旅行总花费。
请计算：
- 往返交通费用
- 住宿费用
- 景点门票
- 餐饮费用
- 市内交通费用
- 备用金

请给出详细的预算明细表。""",
            "use_tools": True
        },
        "risk": {
            "name": "风险提醒",
            "prompt": """你是风险提醒Agent。你的任务是查看天气和出行风险。
请检查：
- 天气情况（是否下雨、高温等）
- 是否需要带伞/防晒
- 景区临时关闭提醒
- 节假日拥堵提醒
- 其他注意事项

请给出风险提醒和建议。请先查询目的地天气。""",
            "use_tools": True
        },
        "guide": {
            "name": "攻略生成",
            "prompt": """你是攻略生成Agent。你的任务是生成完整的旅行攻略。
请生成包含以下内容的攻略：
- 每日行程安排
- 交通建议
- 美食推荐
- 住宿建议
- 预算表
- 注意事项

请生成一份完整、可复制的旅行攻略文档。请先查询天气和交通信息。""",
            "use_tools": True
        }
    }

    def run_single_agent(agent_type, config, user_prompt, q):
        """单个Agent运行线程 - 推送到队列"""
        try:
            # 发送agent开始信号
            q.put(("agent_start", {
                "agent_key": agent_type,
                "agent_name": config["name"]
            }))

            if config["use_tools"]:
                agent_llm = ChatOpenAI(
                    model=ACTIVE_MODEL,
                    api_key=ACTIVE_API_KEY,
                    base_url=ACTIVE_BASE_URL,
                    temperature=0.7,
                    streaming=True,
                )

                agent_tools = [get_weather, search_train_ticket]
                temp_agent = create_react_agent(
                    model=agent_llm,
                    tools=agent_tools,
                    prompt=config["prompt"],
                )

                for event in temp_agent.stream(
                    {"messages": [{"role": "user", "content": user_prompt}]},
                    stream_mode="messages",
                ):
                    # stream_mode="messages" 返回 (message, metadata) 元组
                    msg_obj = event[0]
                    msg_class = type(msg_obj).__name__

                    # 调试日志
                    print(f"[{agent_type}] stream event: class={msg_class}, content_len={len(getattr(msg_obj, 'content', '') or '')}, has_tool_calls={bool(hasattr(msg_obj, 'tool_calls') and msg_obj.tool_calls)}")

                    # 工具调用决策（有tool_calls时content通常为空）
                    if msg_class == "AIMessageChunk" and hasattr(msg_obj, "tool_calls") and msg_obj.tool_calls:
                        for tc in msg_obj.tool_calls:
                            if tc.get("name"):
                                q.put(("tool_call", {
                                    "agent_key": agent_type,
                                    "tool_name": tc["name"],
                                    "tool_args": tc.get("args", {}),
                                }))

                    # 工具返回结果
                    elif msg_class == "ToolMessage":
                        q.put(("tool_result", {
                            "agent_key": agent_type,
                            "tool_name": msg_obj.name,
                            "content": msg_obj.content,
                        }))

                    # AI回复流式输出（有content且没有tool_calls）
                    elif msg_class == "AIMessageChunk" and hasattr(msg_obj, "content") and msg_obj.content:
                        q.put(("chunk", {
                            "agent_key": agent_type,
                            "content": msg_obj.content
                        }))

            else:
                agent_llm = ChatOpenAI(
                    model=ACTIVE_MODEL,
                    api_key=ACTIVE_API_KEY,
                    base_url=ACTIVE_BASE_URL,
                    temperature=0.7,
                    streaming=True,
                )

                messages = [
                    {"role": "system", "content": config["prompt"]},
                    {"role": "user", "content": user_prompt}
                ]

                for chunk in agent_llm.stream(messages):
                    if chunk.content:
                        q.put(("chunk", {
                            "agent_key": agent_type,
                            "content": chunk.content
                        }))

            q.put(("agent_done", {"agent_key": agent_type, "agent_name": config["name"]}))

        except Exception as e:
            q.put(("agent_error", {"agent_key": agent_type, "agent_name": config["name"], "error": str(e)}))

    def generate():
        try:
            origin, destination = parse_query(message)
            user_prompt = f"用户需求：{message}\n出发地：{origin or '未指定'}\n目的地：{destination or '未指定'}"

            q = queue.Queue()
            threads = []
            active_agents = []

            for agent_type in agents:
                config = agent_configs.get(agent_type)
                if not config:
                    continue
                active_agents.append(agent_type)
                t = threading.Thread(
                    target=run_single_agent,
                    args=(agent_type, config, user_prompt, q),
                    daemon=True
                )
                t.start()
                threads.append(t)

            done_agents = set()
            while len(done_agents) < len(active_agents):
                try:
                    event_type, data_obj = q.get(timeout=180)
                    payload = {"type": event_type, **data_obj}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

                    if event_type in ("agent_done", "agent_error"):
                        done_agents.add(data_obj["agent_key"])
                except queue.Empty:
                    break

            for t in threads:
                t.join(timeout=5)

            yield f"data: {json.dumps({'type': 'final', 'content': '所有选中的Agent已完成工作！'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/full-analysis", methods=["POST"])
def full_analysis_api():
    """AI综合分析接口 - 流式输出"""
    data = _request_data()
    query = (data.get("query") or "").strip()
    origin = (data.get("origin") or "").strip()
    destination = (data.get("destination") or "").strip()

    if query and not destination:
        origin, destination = parse_query(query)
    elif not origin:
        origin = "我的城市"
    
    if not destination:
        return jsonify({"success": False, "message": "请输入目的地"}), 400
    
    # 获取搜索数据
    web_results = _get_web_results(origin, destination)
    reviews_results = _get_review_results(origin, destination)
    
    def generate():
        try:
            for chunk in stream_analysis(origin, destination, web_results, reviews_results):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    print("启动旅行助手 Agent Web 服务...")
    print("访问 http://localhost:5002 打开前端页面")
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
