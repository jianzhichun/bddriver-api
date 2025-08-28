"""
钉钉机器人消息提供者

实现钉钉机器人API的消息发送功能
"""

from typing import Dict, Any, Optional
from .base import BaseMessageProvider


class DingTalkProvider(BaseMessageProvider):
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
        content: str,
        summary: Optional[str] = None,
        content_type: int = 1,
        url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送钉钉消息"""
        # 这里实现钉钉机器人API调用
        # 目前返回模拟结果
        return {
            "success": True,
            "provider": "dingtalk",
            "user_id": user_id,
            "content": content,
            "summary": summary
        }
