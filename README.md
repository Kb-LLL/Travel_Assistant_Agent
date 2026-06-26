# Travel Agent - AI 旅行助手系统

基于 LangGraph + MiMo AI 的多 Agent 智能旅行规划系统，提供天气查询、火车票搜索、景点推荐、路线规划、酒店推荐、交通规划、预算计算、风险提醒和攻略生成等一站式旅行服务。
<!-- Failed to upload "6月26日 (1).mp4" -->
## 项目概述

本项目是一个基于大语言模型（LLM）的智能旅行助手，采用多 Agent 协作架构。用户可以通过 Web 界面选择所需的 Agent 功能模块，系统会并行调用多个 Agent 同时工作，实时流式输出每个 Agent 的分析结果。

### 核心特性

- **多 Agent 并行执行**：支持同时运行多个 Agent，每个 Agent 独立调用 AI 模型，互不阻塞
- **实时流式输出**：每个 Agent 拥有独立的输出框，逐字显示 AI 生成内容，带打字光标动画
- **工具调用可视化**：实时展示 Agent 的工具调用决策和返回结果
- **灵活的 Agent 选择**：支持单选或多选 Agent，可自由组合所需功能
- **模拟数据工具**：内置天气查询、火车票搜索、邮件草稿生成等模拟工具
- **邮件发送支持**：集成 SMTP 邮件发送功能，支持主流邮箱服务
- **MySQL 数据持久化**：可选的旅行记录存储功能

## 技术栈

| 技术 | 说明 |
|------|------|
| **Python 3.11+** | 后端开发语言 |
| **Flask** | Web 框架，提供 RESTful API |
| **LangGraph** | 多 Agent 编排框架，基于 ReAct 模式 |
| **LangChain OpenAI** | LLM 调用层，兼容 OpenAI API 格式 |
| **MiMo AI (mimo-v2.5-pro)** | 大语言模型后端（小米 MiMo API） |
| **HTML/CSS/JS** | 前端单页面应用，原生实现 |
| **SSE (Server-Sent Events)** | 流式数据传输协议 |
| **PyMySQL** | MySQL 数据库连接（可选） |
| **SMTP** | 邮件发送功能 |

## 项目结构

```
travel_agent/
├── app.py              # Flask 后端主程序，提供 Web API 接口
├── agent.py            # 单 Agent 核心逻辑（ReAct Agent 创建与运行）
├── multi_agent.py      # 多 Agent 协作方案（LangGraph StateGraph）
├── main.py             # 命令行交互入口
├── config.py           # API 密钥和模型配置
├── tools.py            # 模拟工具模块（天气、火车票、邮件草稿）
├── email_sender.py     # SMTP 邮件发送模块
├── mysql_tools.py      # MySQL 数据持久化工具（可选）
├── requirements.txt    # Python 依赖列表
├── static/
│   └── index.html      # 前端单页面应用
└── __pycache__/        # Python 字节码缓存
```

## 功能模块

### 8 大 Agent 功能

| Agent | 图标 | 说明 | 使用工具 |
|-------|------|------|----------|
| **需求分析** | 📋 | 理解旅行需求，提取出发地、目的地、天数、预算、偏好等关键信息 | 否 |
| **景点推荐** | 🏞️ | 根据目的地和偏好推荐热门/小众景点，含游玩时间和距离分析 | 是（天气/火车票） |
| **路线规划** | 🗺️ | 将景点安排成合理的每日行程，考虑交通时间和开放时间 | 是（天气/火车票） |
| **酒店推荐** | 🏨 | 根据预算、位置偏好推荐住宿区域和酒店类型 | 否 |
| **交通规划** | 🚄 | 规划出发地到目的地及景点间的交通方案，含时间和费用估算 | 是（天气/火车票） |
| **预算计算** | 💰 | 计算旅行总花费明细（交通、住宿、门票、餐饮等） | 是（天气/火车票） |
| **风险提醒** | ⚠️ | 检查天气风险、景区关闭、节假日拥堵等注意事项 | 是（天气/火车票） |
| **攻略生成** | 📖 | 生成完整的旅行攻略文档，包含行程、交通、美食、预算等 | 是（天气/火车票） |

### 内置工具

| 工具 | 说明 |
|------|------|
| `get_weather` | 查询指定城市的天气信息（温度、天气状况、湿度、风力） |
| `search_train_ticket` | 搜索两城市间的火车票信息（车次、时间、票价、余票） |
| `draft_email` | 根据收件人、主题和内容大纲生成邮件草稿 |
| `send_email` | 通过 SMTP 发送真实邮件（支持 QQ/163/Gmail/Outlook 等） |

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/your-username/travel_agent.git
cd travel_agent
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置 API 密钥**

编辑 `config.py` 文件，设置你的 MiMo API 密钥：

```python
# 小米 MiMo API 配置
MIMO_API_KEY = "your_api_key_here"
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5-pro"
```

> 你也可以使用其他兼容 OpenAI API 格式的服务商（如 DeepSeek、OpenAI 等），只需修改 `ACTIVE_API_KEY`、`ACTIVE_BASE_URL`、`ACTIVE_MODEL` 即可。

4. **启动服务**

```bash
python app.py
```

5. **访问界面**

打开浏览器访问 [http://localhost:5002](http://localhost:5002)

### 命令行模式

如果不使用 Web 界面，也可以直接通过命令行运行：

```bash
python main.py
```

## 使用方式

### Web 界面操作

1. **选择 Agent**：在左侧栏点击选择需要的 Agent 功能（支持多选）
2. **输入需求**：在底部输入框输入旅行需求，例如 `从广州到新疆`
3. **运行**：点击「运行选中」按钮
4. **查看结果**：每个 Agent 会并行工作，在独立的输出框中实时显示流式结果

### 快捷键

- **全选**：选中所有 8 个 Agent
- **清除**：取消所有选中
- **运行选中**：执行当前选中的 Agent

### API 接口

#### 运行 Agent

```
POST /api/agent-run
Content-Type: application/json

{
  "message": "从广州到新疆",
  "agents": ["demand", "scenic", "route", "hotel", "transport", "budget", "risk", "guide"]
}
```

响应为 SSE（Server-Sent Events）流式数据：

```
data: {"type": "agent_start", "agent_key": "demand", "agent_name": "需求分析"}
data: {"type": "chunk", "agent_key": "demand", "content": "根据您提供的信息..."}
data: {"type": "tool_call", "agent_key": "scenic", "tool_name": "get_weather", "tool_args": {...}}
data: {"type": "tool_result", "agent_key": "scenic", "tool_name": "get_weather", "content": "..."}
data: {"type": "agent_done", "agent_key": "demand", "agent_name": "需求分析"}
data: {"type": "final", "content": "所有选中的Agent已完成工作！"}
data: [DONE]
```

#### 综合分析

```
POST /api/full-analysis
Content-Type: application/json

{
  "query": "从广州到新疆",
  "origin": "广州",
  "destination": "新疆"
}
```

## 架构设计

### 多 Agent 并行架构

```
用户请求
  │
  ├── Thread 1: 需求分析 Agent ──→ AI Model ──→ 流式输出
  ├── Thread 2: 景点推荐 Agent ──→ AI Model + 工具 ─→ 流式输出
  ├── Thread 3: 路线规划 Agent ──→ AI Model + 工具 ──→ 流式输出
  ├── Thread 4: 酒店推荐 Agent ──→ AI Model ──→ 流式输出
  ├── Thread 5: 交通规划 Agent ─→ AI Model + 工具 ──→ 流式输出
  ├── Thread 6: 预算计算 Agent ──→ AI Model + 工具 ──→ 流式输出
  ├── Thread 7: 风险提醒 Agent ──→ AI Model + 工具 ──→ 流式输出
  └── Thread 8: 攻略生成 Agent ──→ AI Model + 工具 ─→ 流式输出
         │
         ▼
    Queue 队列（按到达顺序推送事件）
         │
         ▼
    SSE 流式响应 ─→ 前端独立输出框渲染
```

### 技术实现

- **后端**：使用 Python `threading` 为每个 Agent 创建独立线程，通过 `queue.Queue` 收集各线程的事件输出
- **流式传输**：使用 Flask `Response` + `text/event-stream` MIME 类型实现 SSE
- **前端**：原生 JavaScript `fetch` + `ReadableStream` 接收 SSE 数据，为每个 Agent 创建独立的 DOM 容器

## 依赖说明

```
langchain>=0.3.0          # LangChain 框架
langchain-openai>=0.2.0   # OpenAI 兼容 LLM 调用
langgraph>=0.2.0          # Agent 编排框架
openai>=1.0.0             # OpenAI SDK
pymysql>=1.1.0            # MySQL 数据库连接（可选）
flask>=3.0.0              # Web 框架
flask-cors>=4.0.0         # 跨域支持
requests>=2.31.0          # HTTP 请求
beautifulsoup4>=4.12.0    # HTML 解析
```

## 扩展开发

### 添加新 Agent

在 `app.py` 的 `agent_configs` 字典中添加新的 Agent 配置：

```python
"new_agent": {
    "name": "新Agent名称",
    "prompt": "系统提示词...",
    "use_tools": True  # 是否使用工具
}
```

### 添加新工具

在 `tools.py` 中使用 `@tool` 装饰器定义新工具：

```python
@tool
def my_new_tool(param: str) -> str:
    """工具描述"""
    return f"结果: {param}"
```

### 切换 LLM 提供商

修改 `config.py` 中的 `ACTIVE_API_KEY`、`ACTIVE_BASE_URL`、`ACTIVE_MODEL` 即可切换到其他兼容 OpenAI API 的服务商。

## 注意事项

- 本项目中的天气和火车票工具返回的是**模拟数据**，仅供演示使用
- 邮件发送功能需要配置真实的 SMTP 授权码
- MySQL 数据持久化为可选功能，默认不启用
- 建议使用 Chrome/Edge 等现代浏览器以获得最佳体验

## License

MIT License
