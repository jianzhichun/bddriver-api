"""
Configuration module for BaiduDriver SDK
"""

from .builtin import BaiduConfig, BuiltinConfig, WxPusherConfig
from .constants import *

# Create global configuration instance
config = BuiltinConfig()

__all__ = ["BuiltinConfig", "BaiduConfig", "WxPusherConfig", "config"]
