"""
消息推送模块

支持多种消息推送渠道
"""

from .wxpusher.client import WxPusherClient
from .providers import DingTalkProvider, WeChatWorkProvider, EmailProvider

__all__ = [
    "WxPusherClient",
    "DingTalkProvider",
    "WeChatWorkProvider", 
    "EmailProvider"
]
