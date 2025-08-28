"""
BaiduDriver - 零配置百度网盘授权驱动

零配置开箱即用的百度网盘授权 SDK，通过 WxPusher 实现授权流程。
让用户 A 能够安全地访问用户 B 的百度网盘文件。

Usage:
    from bddriver import BaiduDriver

    # 创建客户端实例
    driver = BaiduDriver()

    # 发起授权请求
    auth_result = driver.request_device_access("user_b_uid", "/files")

    # 使用文件
    files = driver.list_files(auth_result['access_token'])

Features:
    - 零配置开箱即用: 所有配置内置，无需任何设置
    - 完整授权流程: 设备码授权 + WxPusher + OAuth
    - 专业错误处理: 完整异常体系 + 友好错误信息
    - 结构化日志: JSON 格式 + 敏感数据脱敏
    - 上下文管理: 支持 with 语句自动资源管理
"""

__version__ = "1.0.0"
__author__ = "BaiduDriver Team"
__license__ = "MIT"
__description__ = "零配置百度网盘授权驱动 - 开箱即用的百度网盘 SDK"

# Main client interface
from .client import BaiduDriver

# Configuration
from .config import BuiltinConfig

# File operations
from .fileops import FileClient, FileOperationsManager

# Exception classes
from .utils.errors import (
    AuthError,
    AuthTimeoutError,
    BaiduDriveError,
    BaiduDriverError,
    ConfigurationError,
    FileOperationError,
    InvalidTokenError,
    NetworkError,
    TokenError,
    WxPusherError,
)

# Utilities
from .utils.logger import get_logger

# Version info
version_info = tuple(map(int, __version__.split(".")))

__all__ = [
    # Main interface
    "BaiduDriver",
    # Exception classes
    "BaiduDriverError",
    "NetworkError",
    "AuthError",
    "AuthTimeoutError",
    "WxPusherError",
    "BaiduDriveError",
    "FileOperationError",
    "ConfigurationError",
    "TokenError",
    "InvalidTokenError",
    # Components
    "BuiltinConfig",
    "FileOperationsManager",
    "FileClient",
    "get_logger",
    # Metadata
    "__version__",
    "version_info",
]
