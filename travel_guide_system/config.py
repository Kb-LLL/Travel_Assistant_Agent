"""
旅游攻略搜索与分析系统 - 配置文件
"""

# ========== 小米 MiMo API 配置 ==========
MIMO_API_KEY = "your_api_key_here"
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5-pro"

# ========== 系统配置 ==========
CACHE_ENABLED = True
CACHE_EXPIRE_HOURS = 24  # 缓存过期时间（小时）
MAX_SEARCH_RESULTS = 10  # 每个平台最大搜索结果数
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）

# ========== 平台配置 ==========
PLATFORMS = {
    "xiaohongshu": {
        "name": "小红书",
        "icon": "📕",
        "enabled": True,
    },
    "douyin": {
        "name": "抖音",
        "icon": "🎵",
        "enabled": True,
    },
    "dianping": {
        "name": "大众点评",
        "icon": "⭐",
        "enabled": True,
    },
    "mafengwo": {
        "name": "马蜂窝",
        "icon": "🐝",
        "enabled": True,
    },
    "ctrip": {
        "name": "携程",
        "icon": "✈️",
        "enabled": True,
    },
}
