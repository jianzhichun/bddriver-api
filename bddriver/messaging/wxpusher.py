"""
WxPusher消息提供者实现

基于抽象基类的WxPusher推送实现
"""

import requests
from typing import Dict, Any, Optional
from .base import MessageProvider, MessageResult, MessageStatus


class WxPusherProvider(MessageProvider):
    """WxPusher消息提供者实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化WxPusher提供者
        
        Args:
            config: 配置字典，必须包含 app_token
        """
        super().__init__("wxpusher", config)
        self.app_token = config["app_token"]
        self.base_url = config.get("base_url", "https://wxpusher.zjiecode.com")
        self.api_url = f"{self.base_url}/api/send/message"
    
    def _validate_config(self) -> None:
        """验证WxPusher配置"""
        if not self.app_token:
            raise ValueError("WxPusher配置缺少 app_token")
        
        if not self.base_url:
            raise ValueError("WxPusher配置缺少 base_url")
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证WxPusher用户ID格式
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否为有效的WxPusher UID
        """
        return user_id.startswith("UID_") and len(user_id) > 4
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取WxPusher用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户信息
        """
        try:
            # 这里可以调用WxPusher API获取用户信息
            # 目前返回基本信息
            return {
                "provider": "wxpusher",
                "user_id": user_id,
                "type": "wxpusher_uid"
            }
        except Exception:
            return None
    
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> MessageResult:
        """发送WxPusher消息
        
        Args:
            user_id: WxPusher UID
            message: 消息内容
            title: 消息标题
            **kwargs: 其他参数
            
        Returns:
            MessageResult: 发送结果
        """
        try:
            # 构建请求数据
            data = {
                "appToken": self.app_token,
                "content": message,
                "summary": title or "百度网盘授权请求",
                "contentType": kwargs.get("content_type", 1),  # 1: 文本, 2: HTML
                "uids": [user_id],
                "url": kwargs.get("url", ""),
            }
            
            # 发送请求
            response = requests.post(
                self.api_url,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return MessageResult(
                        success=True,
                        message_id=result.get("data", {}).get("messageId"),
                        status=MessageStatus.SUCCESS,
                        metadata=result
                    )
                else:
                    return MessageResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        error_message=result.get("msg", "发送失败"),
                        metadata=result
                    )
            else:
                return MessageResult(
                    success=False,
                    status=MessageStatus.FAILED,
                    error_message=f"HTTP {response.status_code}: {response.text}",
                    metadata={"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            return MessageResult(
                success=False,
                status=MessageStatus.FAILED,
                error_message="请求超时"
            )
        except requests.exceptions.RequestException as e:
            return MessageResult(
                success=False,
                status=MessageStatus.FAILED,
                error_message=f"网络请求失败: {e}"
            )
        except Exception as e:
            return MessageResult(
                success=False,
                status=MessageStatus.FAILED,
                error_message=f"发送消息异常: {e}"
            )
    
    def get_supported_features(self) -> list:
        """获取WxPusher支持的功能"""
        return ["basic_message", "html_message", "url_redirect"]
    
    def get_rate_limit_info(self) -> Optional[Dict[str, Any]]:
        """获取WxPusher频率限制信息"""
        return {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "description": "每分钟60次，每小时1000次"
        }
