"""
消息提供者抽象基类

定义所有消息提供者应该实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseMessageProvider(ABC):
    """消息提供者抽象基类"""
    
    @abstractmethod
    def __init__(self, **kwargs):
        """初始化消息提供者"""
        pass
    
    @abstractmethod
    def validate_user_id(self, user_id: str) -> bool:
        """验证用户ID格式
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否有效
        """
        pass
    
    @abstractmethod
    def send_message(
        self,
        user_id: str,
        content: str,
        summary: Optional[str] = None,
        content_type: int = 1,
        url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送消息
        
        Args:
            user_id: 用户ID
            content: 消息内容
            summary: 消息摘要
            content_type: 内容类型
            url: 原文链接
            **kwargs: 其他参数
            
        Returns:
            发送结果
        """
        pass
    
    def get_supported_features(self) -> List[str]:
        """获取支持的功能列表
        
        Returns:
            支持的功能列表
        """
        return ["basic_message"]
    
    def supports_subscription(self) -> bool:
        """是否支持订阅功能
        
        Returns:
            是否支持订阅
        """
        return False
    
    def get_subscription_info(self) -> Optional[Dict[str, Any]]:
        """获取订阅信息
        
        Returns:
            订阅信息，如果不支持则返回None
        """
        return None
    
    def create_subscription_qrcode(
        self, 
        extra: str = "", 
        valid_time: int = 1800
    ) -> Optional[Dict[str, Any]]:
        """创建订阅二维码
        
        Args:
            extra: 二维码携带的参数
            valid_time: 二维码有效期（秒）
            
        Returns:
            创建结果，如果不支持则返回None
        """
        return None
    
    def check_scan_status(self, qrcode_code: str) -> Optional[Dict[str, Any]]:
        """查询扫码状态
        
        Args:
            qrcode_code: 二维码的code参数
            
        Returns:
            扫码状态，如果不支持则返回None
        """
        return None
    
    def get_provider_name(self) -> str:
        """获取提供者名称
        
        Returns:
            提供者名称
        """
        return self.__class__.__name__.lower().replace('provider', '')
    
    def get_provider_type(self) -> str:
        """获取提供者类型
        
        Returns:
            提供者类型（内置/外部）
        """
        return "external"  # 默认外部提供者


class SubscriptionProvider(BaseMessageProvider):
    """支持订阅功能的消息提供者基类"""
    
    def supports_subscription(self) -> bool:
        """支持订阅功能"""
        return True
    
    @abstractmethod
    def get_subscription_info(self) -> Dict[str, Any]:
        """获取订阅信息"""
        pass
    
    @abstractmethod
    def create_subscription_qrcode(
        self, 
        extra: str = "", 
        valid_time: int = 1800
    ) -> Dict[str, Any]:
        """创建订阅二维码"""
        pass
    
    @abstractmethod
    def check_scan_status(self, qrcode_code: str) -> Dict[str, Any]:
        """查询扫码状态"""
        pass


class BuiltinProvider(SubscriptionProvider):
    """内置消息提供者基类"""
    
    def get_provider_type(self) -> str:
        """内置提供者"""
        return "builtin"
    
    def __init__(self):
        """内置提供者不需要配置参数"""
        super().__init__()

