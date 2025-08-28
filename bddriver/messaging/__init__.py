"""
消息推送抽象模块

支持多种消息推送渠道的统一接口
"""

from .base import MessageProvider, MessageResult
from .wxpusher import WxPusherProvider
from .registry import MessageProviderRegistry

__all__ = [
    "MessageProvider",
    "MessageResult", 
    "WxPusherProvider",
    "MessageProviderRegistry"
]
