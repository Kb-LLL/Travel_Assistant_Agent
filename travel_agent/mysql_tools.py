"""
MySQL 集成示例（可选扩展）
===========================
将旅行查询记录保存到本地 MySQL 数据库

使用前：
1. 确保本地 MySQL 已安装并运行
2. 修改下方 MYSQL_CONFIG 配置
3. 安装依赖：pip install pymysql

运行方式：
    python mysql_tools.py
"""

import json
from datetime import datetime
from langchain_core.tools import tool

# ========== MySQL 配置 ==========
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",  # 请修改为你的 MySQL 密码
    "database": "travel_agent",
    "charset": "utf8mb4",
}


def init_database():
    """初始化数据库和表"""
    try:
        import pymysql

        # 先连接 MySQL（不指定数据库）创建数据库
        conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            charset=MYSQL_CONFIG["charset"],
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        conn.close()

        # 连接到目标数据库，创建表
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS travel_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_query TEXT NOT NULL,
                weather_result TEXT,
                ticket_result TEXT,
                email_draft TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        conn.commit()
        conn.close()
        print("[MySQL] 数据库初始化成功")
        return True

    except ImportError:
        print("[MySQL] 请安装 pymysql: pip install pymysql")
        return False
    except Exception as e:
        print(f"[MySQL] 初始化失败: {e}")
        return False


@tool
def save_travel_log(
    user_query: str,
    weather_result: str = "",
    ticket_result: str = "",
    email_draft: str = "",
) -> str:
    """将旅行查询记录保存到 MySQL 数据库。

    Args:
        user_query: 用户的原始查询
        weather_result: 天气查询结果
        ticket_result: 火车票查询结果
        email_draft: 邮件草稿
    """
    try:
        import pymysql

        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        sql = """
            INSERT INTO travel_logs
            (user_query, weather_result, ticket_result, email_draft)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (user_query, weather_result, ticket_result, email_draft))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()

        return f"旅行记录已保存到 MySQL，记录ID: {log_id}"

    except Exception as e:
        return f"保存失败: {e}"


@tool
def query_travel_history(limit: int = 5) -> str:
    """查询最近的旅行记录。

    Args:
        limit: 返回记录数量，默认5条
    """
    try:
        import pymysql

        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT id, user_query, weather_result, ticket_result,
                   email_draft, created_at
            FROM travel_logs
            ORDER BY created_at DESC
            LIMIT %s
        """
        cursor.execute(sql, (limit,))
        records = cursor.fetchall()
        conn.close()

        if not records:
            return "暂无旅行记录"

        result_lines = [f"【最近 {len(records)} 条旅行记录】\n"]
        for r in records:
            result_lines.append(
                f"ID: {r['id']} | 时间: {r['created_at']}\n"
                f"  查询: {r['user_query'][:100]}...\n"
            )

        return "\n".join(result_lines)

    except Exception as e:
        return f"查询失败: {e}"


# ========== 测试 ==========
if __name__ == "__main__":
    print("MySQL 集成测试")
    print("=" * 40)

    # 1. 初始化数据库
    if init_database():
        # 2. 测试保存
        result = save_travel_log.invoke(
            {
                "user_query": "测试：从上海到北京旅行",
                "weather_result": "北京 28°C 晴",
                "ticket_result": "G1 08:00出发",
                "email_draft": "亲爱的张三...",
            }
        )
        print(f"保存结果: {result}")

        # 3. 测试查询
        history = query_travel_history.invoke({"limit": 3})
        print(f"查询结果:\n{history}")
