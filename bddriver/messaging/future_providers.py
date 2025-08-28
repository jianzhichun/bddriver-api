"""
未来可能的消息提供者示例

展示如何基于抽象接口实现新的推送渠道
"""

from typing import Dict, Any, Optional
from .base import MessageProvider, MessageResult, MessageStatus


class DingTalkProvider(MessageProvider):
    """钉钉机器人消息提供者示例"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化钉钉提供者
        
        Args:
            config: 配置字典，必须包含 webhook_url
        """
        super().__init__("dingtalk", config)
        self.webhook_url = config["webhook_url"]
        self.secret = config.get("secret")
    
    def _validate_config(self) -> None:
        """验证钉钉配置"""
        if not self.webhook_url:
            raise ValueError("钉钉配置缺少 webhook_url")
    
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
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取钉钉用户信息"""
        return {
            "provider": "dingtalk",
            "user_id": user_id,
            "type": "dingtalk_user"
        }
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> MessageResult:
        """发送钉钉消息"""
        # 这里实现钉钉机器人API调用
        # 目前返回模拟结果
        return MessageResult(
            success=True,
            status=MessageStatus.SUCCESS,
            metadata={"provider": "dingtalk", "user_id": user_id}
        )


class WeChatWorkProvider(MessageProvider):
    """企业微信消息提供者示例"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化企业微信提供者
        
        Args:
            config: 配置字典，必须包含 corp_id, agent_id, secret
        """
        super().__init__("wechat_work", config)
        self.corp_id = config["corp_id"]
        self.agent_id = config["agent_id"]
        self.secret = config["secret"]
    
    def _validate_config(self) -> None:
        """验证企业微信配置"""
        required_keys = ["corp_id", "agent_id", "secret"]
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"企业微信配置缺少 {key}")
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证企业微信用户ID格式"""
        # 企业微信用户ID通常是字符串格式
        return len(user_id) > 0 and not user_id.isspace()
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取企业微信用户信息"""
        return {
            "provider": "wechat_work",
            "user_id": user_id,
            "type": "wechat_work_user"
        }
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> MessageResult:
        """发送企业微信消息"""
        # 这里实现企业微信API调用
        # 目前返回模拟结果
        return MessageResult(
            success=True,
            status=MessageStatus.SUCCESS,
            metadata={"provider": "wechat_work", "user_id": user_id}
        )


class EmailProvider(MessageProvider):
    """邮件消息提供者示例"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化邮件提供者
        
        Args:
            config: 配置字典，必须包含 smtp_host, smtp_port, username, password
        """
        super().__init__("email", config)
        self.smtp_host = config["smtp_host"]
        self.smtp_port = config["smtp_port"]
        self.username = config["username"]
        self.password = config["password"]
    
    def _validate_config(self) -> None:
        """验证邮件配置"""
        required_keys = ["smtp_host", "smtp_port", "username", "password"]
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"邮件配置缺少 {key}")
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证邮箱格式"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, user_id) is not None
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取邮件用户信息"""
        return {
            "provider": "email",
            "user_id": user_id,
            "type": "email_address"
        }
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> MessageResult:
        """发送邮件"""
        # 这里实现SMTP邮件发送
        # 目前返回模拟结果
        return MessageResult(
            success=True,
            status=MessageStatus.SUCCESS,
            metadata={"provider": "email", "user_id": user_id}
        )
    
    def get_supported_features(self) -> list:
        """获取邮件支持的功能"""
        return ["basic_message", "html_message", "attachments", "cc_bcc"]
