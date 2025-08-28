"""
Built-in configuration for BaiduDriver SDK
All credentials and settings are embedded for zero-configuration usage.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BaiduConfig:
    """百度网盘配置"""

    app_id: str = "119878817"
    app_key: str = "hsbs6yhFco7KZRTIt1Vp83hM5xKpeLca"
    secret_key: str = "VCBG1NOYBCMAhGSgm18TtIyWI93GD96G"
    sign_key: str = "0$4q+3@j%9Ny85OdfcfOg77oDAoZyPgz"
    share_secret: str = ""
    share_third_id: str = "0"

    @property
    def client_id(self) -> str:
        """OAuth client_id (alias for app_id)"""
        return self.app_key

    @property
    def client_secret(self) -> str:
        """OAuth client_secret (alias for app_key)"""
        return self.secret_key


@dataclass
class WxPusherConfig:
    """WxPusher 配置"""

    app_token: str = "AT_xyiuJwTytQRirHTQdmS3otsCQhfUVfqd"
    base_url: str = "https://wxpusher.zjiecode.com/api"
    user_agent: str = "BaiduDriver/1.0"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class GeneralConfig:
    """通用配置"""

    request_timeout: int = 30
    max_retries: int = 3
    auth_timeout: int = 300  # 5分钟授权超时
    device_auth_timeout: int = 600  # 10分钟设备码授权超时


class BuiltinConfig:
    """SDK 内置配置管理器"""

    def __init__(self):
        self.baidu = BaiduConfig()
        self.wxpusher = WxPusherConfig()
        self.general = GeneralConfig()

    def get_baidu_config(self) -> BaiduConfig:
        """获取百度网盘配置"""
        return self.baidu

    def get_wxpusher_config(self) -> WxPusherConfig:
        """获取 WxPusher 配置"""
        return self.wxpusher

    def get_general_config(self) -> GeneralConfig:
        """获取通用配置"""
        return self.general

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "baidu": self.baidu.__dict__,
            "wxpusher": self.wxpusher.__dict__,
            "general": self.general.__dict__,
        }

    def validate_config(self) -> bool:
        """验证配置的完整性和有效性"""
        try:
            # 验证百度网盘配置
            assert self.baidu.app_id and self.baidu.app_key, "百度网盘配置不完整"
            assert self.baidu.secret_key, "百度网盘secret_key不能为空"

            # 验证 WxPusher 配置
            assert self.wxpusher.app_token, "WxPusher配置不完整"
            assert self.wxpusher.base_url.startswith(
                "http"
            ), "WxPusher base_url格式错误"

            return True
        except AssertionError as e:
            print(f"配置验证失败: {e}")
            return False


# 全局配置实例
config = BuiltinConfig()
