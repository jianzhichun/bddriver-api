"""
消息推送模块

支持多种消息推送渠道，按功能分文件管理
"""

from .wxpusher_provider import WxPusherProvider, WxPusherClient
from .dingtalk_provider import DingTalkProvider
from .wechat_work_provider import WeChatWorkProvider
from .email_provider import EmailProvider
from .manager import MessageProviderManager, get_messaging_manager

__all__ = [
    "WxPusherProvider",
    "WxPusherClient",
    "DingTalkProvider",
    "WeChatWorkProvider", 
    "EmailProvider",
    "MessageProviderManager",
    "get_messaging_manager"
]


class MessageProviderFactory:
    """消息提供者工厂类"""
    
    _providers = {
        "wxpusher": WxPusherProvider,
        "dingtalk": DingTalkProvider,
        "wechat_work": WeChatWorkProvider,
        "email": EmailProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str):
        """获取指定的消息提供者
        
        Args:
            provider_name: 提供者名称 (wxpusher, dingtalk, wechat_work, email)
            
        Returns:
            消息提供者实例
            
        Raises:
            ValueError: 不支持的提供者名称
        """
        if provider_name not in cls._providers:
            supported = ", ".join(cls._providers.keys())
            raise ValueError(f"不支持的消息提供者: {provider_name}。支持的提供者: {supported}")
        
        return cls._providers[provider_name]()
    
    @classmethod
    def list_providers(cls):
        """列出所有支持的提供者"""
        return list(cls._providers.keys())
    
    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        """检查提供者是否支持"""
        return provider_name in cls._providers


def get_message_provider(provider_name: str = None):
    """获取消息提供者的便捷函数
    
    Args:
        provider_name: 提供者名称，如果为None则使用配置中的默认值
        
    Returns:
        消息提供者实例
    """
    if provider_name is None:
        # 从配置获取默认提供者
        from ..config import config
        provider_name = config.get_general_config().message_provider
    
    return MessageProviderFactory.get_provider(provider_name)
