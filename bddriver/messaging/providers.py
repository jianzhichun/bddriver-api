"""
消息推送提供者实现

包含多种消息推送渠道的具体实现
"""

from typing import Dict, Any, Optional


class DingTalkProvider:
    """钉钉机器人消息提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化钉钉提供者
        
        Args:
            config: 配置字典，必须包含 webhook_url
        """
        self.webhook_url = config["webhook_url"]
        self.secret = config.get("secret")
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证钉钉用户ID格式
        
        钉钉用户ID可能是手机号或钉钉用户ID
        """
        # 手机号格式：11位数字
        if user_id.isdigit() and len(user_id) == 11:
            return True
        # 钉钉用户ID格式：通常以特定前缀开头
        if user_id.startswith("ding_") or user_id.startswith("uid_"):
            return True
        return False
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送钉钉消息"""
        # 这里实现钉钉机器人API调用
        # 目前返回模拟结果
        return {
            "success": True,
            "provider": "dingtalk",
            "user_id": user_id,
            "message": message
        }


class WeChatWorkProvider:
    """企业微信消息提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化企业微信提供者
        
        Args:
            config: 配置字典，必须包含 corp_id, agent_id, secret
        """
        self.corp_id = config["corp_id"]
        self.agent_id = config["agent_id"]
        self.secret = config["secret"]
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证企业微信用户ID格式"""
        # 企业微信用户ID通常是字符串格式
        return len(user_id) > 0 and not user_id.isspace()
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送企业微信消息"""
        # 这里实现企业微信API调用
        # 目前返回模拟结果
        return {
            "success": True,
            "provider": "wechat_work",
            "user_id": user_id,
            "message": message
        }


class EmailProvider:
    """邮件消息提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化邮件提供者
        
        Args:
            config: 配置字典，必须包含 smtp_host, smtp_port, username, password
        """
        self.smtp_host = config["smtp_host"]
        self.smtp_port = config["smtp_port"]
        self.username = config["username"]
        self.password = config["password"]
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证邮箱格式"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, user_id) is not None
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送邮件"""
        # 这里实现SMTP邮件发送
        # 目前返回模拟结果
        return {
            "success": True,
            "provider": "email",
            "user_id": user_id,
            "message": message
        }
    
    def get_supported_features(self) -> list:
        """获取邮件支持的功能"""
        return ["basic_message", "html_message", "attachments", "cc_bcc"]
