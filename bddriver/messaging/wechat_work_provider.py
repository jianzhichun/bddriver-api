"""
企业微信消息提供者

实现企业微信API的消息发送功能
"""

from typing import Dict, Any, Optional
from .base import BaseMessageProvider


class WeChatWorkProvider(BaseMessageProvider):
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
        content: str,
        summary: Optional[str] = None,
        content_type: int = 1,
        url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送企业微信消息"""
        # 这里实现企业微信API调用
        # 目前返回模拟结果
        return {
            "success": True,
            "provider": "wechat_work",
            "user_id": user_id,
            "content": content,
            "summary": summary
        }
