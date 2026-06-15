"""
邮件发送模块 - 使用 SMTP 发送真实邮件
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


# ========== SMTP 配置 ==========
# 常用邮箱 SMTP 配置
SMTP_CONFIGS = {
    "qq.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "163.com": {"server": "smtp.163.com", "port": 465, "ssl": True},
    "126.com": {"server": "smtp.126.com", "port": 465, "ssl": True},
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "ssl": False},
    "outlook.com": {"server": "smtp.office365.com", "port": 587, "ssl": False},
    "hotmail.com": {"server": "smtp.office365.com", "port": 587, "ssl": False},
}


def get_smtp_config(email: str) -> dict:
    """根据邮箱地址自动获取 SMTP 配置"""
    domain = email.split("@")[-1].lower()
    if domain in SMTP_CONFIGS:
        return SMTP_CONFIGS[domain]
    # 默认使用通用配置
    return {"server": f"smtp.{domain}", "port": 465, "ssl": True}


def send_email(
    sender_email: str,
    sender_password: str,
    receiver_email: str,
    subject: str,
    body: str,
) -> dict:
    """
    发送邮件
    
    Args:
        sender_email: 发件人邮箱
        sender_password: 发件人邮箱密码/授权码
        receiver_email: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        # 获取 SMTP 配置
        config = get_smtp_config(sender_email)
        
        # 创建邮件
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = Header(subject, "utf-8")
        
        # 添加正文
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # 连接 SMTP 服务器并发送
        if config["ssl"]:
            server = smtplib.SMTP_SSL(config["server"], config["port"])
        else:
            server = smtplib.SMTP(config["server"], config["port"])
            server.starttls()
        
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        return {
            "success": True,
            "message": f"邮件已成功发送到 {receiver_email}"
        }
    
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "邮箱认证失败，请检查邮箱地址和授权码是否正确"
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "message": f"邮件发送失败: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"发送出错: {str(e)}"
        }


def get_smtp_help(email: str) -> str:
    """获取 SMTP 授权码设置帮助信息"""
    domain = email.split("@")[-1].lower()
    
    help_texts = {
        "qq.com": """QQ邮箱授权码获取方法：
1. 登录 QQ邮箱网页版
2. 进入 设置 -> 账户
3. 找到 POP3/SMTP 服务，点击开启
4. 按提示发送短信验证
5. 获取16位授权码（不是QQ密码）""",
        
        "163.com": """163邮箱授权码获取方法：
1. 登录 163邮箱网页版
2. 进入 设置 -> POP3/SMTP/IMAP
3. 开启 SMTP 服务
4. 按提示发送短信验证
5. 获取授权码（不是邮箱密码）""",
        
        "126.com": """126邮箱授权码获取方法：
1. 登录 126邮箱网页版
2. 进入 设置 -> POP3/SMTP/IMAP
3. 开启 SMTP 服务
4. 获取授权码""",
        
        "gmail.com": """Gmail应用专用密码获取方法：
1. 登录 Google 账号
2. 进入 安全性 -> 两步验证（需先开启）
3. 搜索"应用专用密码"
4. 生成一个16位应用专用密码""",
        
        "outlook.com": """Outlook邮箱：
1. 直接使用邮箱密码登录
2. 如开启两步验证，需使用应用密码""",
    }
    
    return help_texts.get(domain, f"请查看 {domain} 邮箱的 SMTP 设置说明，获取授权码/应用密码")
