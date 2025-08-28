"""
消息提供者管理器

支持动态注册、配置和切换不同的消息推送渠道
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, asdict

from .base import BaseMessageProvider, SubscriptionProvider, BuiltinProvider
from .wxpusher_provider import WxPusherProvider
from .dingtalk_provider import DingTalkProvider
from .wechat_work_provider import WeChatWorkProvider
from .email_provider import EmailProvider
from ..utils.logger import get_logger


@dataclass
class ProviderConfig:
    """消息提供者配置"""
    enabled: bool = False
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class MessageProviderManager:
    """消息提供者管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化消息提供者管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = get_logger("messaging")
        
        # 注册所有可用的消息提供者
        self._providers: Dict[str, Type[BaseMessageProvider]] = {
            "wxpusher": WxPusherProvider,
            "dingtalk": DingTalkProvider,
            "wechat_work": WeChatWorkProvider,
            "email": EmailProvider
        }
        
        # 提供者实例缓存
        self._provider_instances: Dict[str, Any] = {}
        
        # 配置管理
        self.config_file = config_file or self._get_default_config_file()
        self.config = self._load_config()
        
        self.logger.info(f"消息提供者管理器初始化完成，配置文件: {self.config_file}")
    
    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        # 优先使用项目根目录的配置文件
        project_config = ".bddriver-messaging.json"
        if os.path.exists(project_config):
            return project_config
        
        # 其次使用用户目录的配置文件
        user_config_dir = Path.home() / ".bddriver"
        user_config_dir.mkdir(exist_ok=True)
        return str(user_config_dir / "messaging.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "default_provider": "wxpusher",
            "providers": {
                "wxpusher": {
                    "enabled": True,  # WxPusher始终启用，作为内置提供者
                    "config": {},
                    "builtin": True   # 标记为内置提供者
                },
                "dingtalk": {
                    "enabled": False,
                    "config": {},
                    "builtin": False
                },
                "wechat_work": {
                    "enabled": False,
                    "config": {},
                    "builtin": False
                },
                "email": {
                    "enabled": False,
                    "config": {},
                    "builtin": False
                }
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，保持向后兼容
                    for provider_name, provider_config in loaded_config.get("providers", {}).items():
                        if provider_name in default_config["providers"]:
                            # 对于内置提供者，保持enabled=True
                            if provider_name == "wxpusher":
                                # WxPusher始终启用，但可以更新其他配置
                                provider_config["enabled"] = True
                                provider_config["builtin"] = True
                            default_config["providers"][provider_name].update(provider_config)
                    default_config["default_provider"] = loaded_config.get("default_provider", "wxpusher")
                    self.logger.info(f"配置文件加载成功: {self.config_file}")
            except Exception as e:
                self.logger.warning(f"配置文件加载失败，使用默认配置: {e}")
        else:
            self.logger.info("配置文件不存在，使用默认配置")
        
        return default_config
    
    def _save_config(self):
        """保存配置文件"""
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
    
    def get_available_providers(self) -> List[str]:
        """获取所有可用的消息提供者名称"""
        return list(self._providers.keys())
    
    def get_enabled_providers(self) -> List[str]:
        """获取已启用的消息提供者名称"""
        return [name for name, config in self.config["providers"].items() 
                if config.get("enabled", False)]
    
    def get_default_provider(self) -> str:
        """获取默认消息提供者名称"""
        default = self.config.get("default_provider", "wxpusher")
        # 确保默认提供者已启用
        if default in self.config["providers"] and self.config["providers"][default].get("enabled", False):
            return default
        
        # 如果默认提供者未启用，返回第一个启用的提供者
        enabled = self.get_enabled_providers()
        if enabled:
            return enabled[0]
        
        # 如果没有启用的提供者，返回wxpusher（向后兼容）
        return "wxpusher"
    
    def set_default_provider(self, provider_name: str) -> bool:
        """设置默认消息提供者
        
        Args:
            provider_name: 提供者名称
            
        Returns:
            是否设置成功
        """
        if provider_name not in self._providers:
            self.logger.error(f"未知的消息提供者: {provider_name}")
            return False
        
        if not self.config["providers"][provider_name].get("enabled", False):
            self.logger.error(f"消息提供者 {provider_name} 未启用")
            return False
        
        old_default = self.config.get("default_provider", "wxpusher")
        self.config["default_provider"] = provider_name
        self._save_config()
        
        self.logger.info(f"默认消息提供者已从 {old_default} 切换到 {provider_name}")
        return True
    
    def enable_provider(self, provider_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """启用消息提供者
        
        Args:
            provider_name: 提供者名称
            config: 提供者配置
            
        Returns:
            是否启用成功
        """
        if provider_name not in self._providers:
            self.logger.error(f"未知的消息提供者: {provider_name}")
            return False
        
        # 检查是否为内置提供者
        if provider_name == "wxpusher":
            self.logger.warning("WxPusher是内置提供者，始终启用，无需配置")
            return True
        
        if config is None:
            config = {}
        
        self.config["providers"][provider_name]["enabled"] = True
        self.config["providers"][provider_name]["config"] = config
        
        # 清除实例缓存
        if provider_name in self._provider_instances:
            del self._provider_instances[provider_name]
        
        self._save_config()
        self.logger.info(f"消息提供者 {provider_name} 已启用")
        return True
    
    def disable_provider(self, provider_name: str) -> bool:
        """禁用消息提供者
        
        Args:
            provider_name: 提供者名称
            
        Returns:
            是否禁用成功
        """
        if provider_name not in self._providers:
            self.logger.error(f"未知的消息提供者: {provider_name}")
            return False
        
        # 检查是否为内置提供者
        if provider_name == "wxpusher":
            self.logger.warning("WxPusher是内置提供者，不能被禁用")
            return False
        
        self.config["providers"][provider_name]["enabled"] = False
        
        # 清除实例缓存
        if provider_name in self._provider_instances:
            del self._provider_instances[provider_name]
        
        # 如果禁用的是默认提供者，需要重新选择默认提供者
        if self.config.get("default_provider") == provider_name:
            enabled = self.get_enabled_providers()
            if enabled:
                self.config["default_provider"] = enabled[0]
                self.logger.info(f"默认消息提供者已切换到: {enabled[0]}")
        
        self._save_config()
        self.logger.info(f"消息提供者 {provider_name} 已禁用")
        return True
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """获取消息提供者配置
        
        Args:
            provider_name: 提供者名称
            
        Returns:
            提供者配置，如果不存在则返回None
        """
        if provider_name not in self.config["providers"]:
            return None
        
        return self.config["providers"][provider_name].copy()
    
    def update_provider_config(self, provider_name: str, config: Dict[str, Any]) -> bool:
        """更新消息提供者配置
        
        Args:
            provider_name: 提供者名称
            config: 新的配置
            
        Returns:
            是否更新成功
        """
        if provider_name not in self._providers:
            self.logger.error(f"未知的消息提供者: {provider_name}")
            return False
        
        # 检查是否为内置提供者
        if provider_name == "wxpusher":
            self.logger.warning("WxPusher是内置提供者，配置更新将被忽略")
            return True
        
        self.config["providers"][provider_name]["config"].update(config)
        
        # 清除实例缓存
        if provider_name in self._provider_instances:
            del self._provider_instances[provider_name]
        
        self._save_config()
        self.logger.info(f"消息提供者 {provider_name} 配置已更新")
        return True
    
    def get_subscription_info(self, provider_name: str = "wxpusher") -> Dict[str, Any]:
        """获取消息提供者订阅信息
        
        Args:
            provider_name: 提供者名称，默认为wxpusher
            
        Returns:
            订阅信息
        """
        if provider_name not in self._providers:
            raise ValueError(f"未知的消息提供者: {provider_name}")
        
        # 检查提供者是否支持订阅功能
        provider_class = self._providers[provider_name]
        if not issubclass(provider_class, SubscriptionProvider):
            return {
                "success": False,
                "msg": f"消息提供者 {provider_name} 不支持订阅功能"
            }
        
        if provider_name == "wxpusher":
            # WxPusher作为内置提供者，直接创建实例
            provider_instance = provider_class()
            return provider_instance.get_subscription_info()
        else:
            # 其他提供者需要先启用
            if not self.config["providers"][provider_name].get("enabled", False):
                raise ValueError(f"消息提供者 {provider_name} 未启用")
            
            provider_instance = self.get_provider_instance(provider_name)
            return provider_instance.get_subscription_info()
    
    def create_subscription_qrcode(self, extra: str = "", valid_time: int = 1800, provider_name: str = "wxpusher") -> Dict[str, Any]:
        """创建订阅二维码
        
        Args:
            extra: 二维码携带的参数，最长64位
            valid_time: 二维码有效期，默认30分钟，最长30天，单位是秒
            provider_name: 提供者名称，默认为wxpusher
            
        Returns:
            创建结果
        """
        if provider_name not in self._providers:
            raise ValueError(f"未知的消息提供者: {provider_name}")
        
        # 检查提供者是否支持订阅功能
        provider_class = self._providers[provider_name]
        if not issubclass(provider_class, SubscriptionProvider):
            return {
                "success": False,
                "msg": f"消息提供者 {provider_name} 不支持订阅功能"
            }
        
        if provider_name == "wxpusher":
            # WxPusher作为内置提供者，直接创建实例
            provider_instance = provider_class()
            return provider_instance.create_subscription_qrcode(extra, valid_time)
        else:
            # 其他提供者需要先启用
            if not self.config["providers"][provider_name].get("enabled", False):
                raise ValueError(f"消息提供者 {provider_name} 未启用")
            
            provider_instance = self.get_provider_instance(provider_name)
            return provider_instance.create_subscription_qrcode(extra, valid_time)
    
    def check_scan_status(self, qrcode_code: str, provider_name: str = "wxpusher") -> Dict[str, Any]:
        """查询扫码用户UID
        
        Args:
            qrcode_code: 二维码的code参数
            provider_name: 提供者名称，默认为wxpusher
            
        Returns:
            扫码状态
        """
        if provider_name not in self._providers:
            raise ValueError(f"未知的消息提供者: {provider_name}")
        
        # 检查提供者是否支持订阅功能
        provider_class = self._providers[provider_name]
        if not issubclass(provider_class, SubscriptionProvider):
            return {
                "success": False,
                "msg": f"消息提供者 {provider_name} 不支持订阅功能"
            }
        
        if provider_name == "wxpusher":
            # WxPusher作为内置提供者，直接创建实例
            provider_instance = provider_class()
            return provider_instance.check_scan_status(qrcode_code)
        else:
            # 其他提供者需要先启用
            if not self.config["providers"][provider_name].get("enabled", False):
                raise ValueError(f"消息提供者 {provider_name} 未启用")
            
            provider_instance = self.get_provider_instance(provider_name)
            return provider_instance.check_scan_status(qrcode_code)

    def poll_scan_status(self, qrcode_code: str, provider_name: str = "wxpusher", interval: int = 15, max_attempts: int = 120) -> Dict[str, Any]:
        """轮询扫码状态直到获得用户UID
        
        Args:
            qrcode_code: 二维码的code参数
            provider_name: 提供者名称，默认为wxpusher
            interval: 轮询间隔（秒），最小10秒
            max_attempts: 最大轮询次数，默认120次（30分钟）
            
        Returns:
            轮询结果
        """
        if provider_name not in self._providers:
            raise ValueError(f"未知的消息提供者: {provider_name}")
        
        # 检查提供者是否支持订阅功能
        provider_class = self._providers[provider_name]
        if not issubclass(provider_class, SubscriptionProvider):
            return {
                "success": False,
                "msg": f"消息提供者 {provider_name} 不支持订阅功能"
            }
        
        if provider_name == "wxpusher":
            # WxPusher作为内置提供者，直接创建实例
            provider_instance = provider_class()
            # 检查是否有轮询方法
            if hasattr(provider_instance, 'poll_scan_status'):
                return provider_instance.poll_scan_status(qrcode_code, interval, max_attempts)
            else:
                return {"success": False, "msg": f"提供者 {provider_name} 不支持轮询功能"}
        else:
            # 其他提供者需要先启用
            if not self.config["providers"][provider_name].get("enabled", False):
                raise ValueError(f"消息提供者 {provider_name} 未启用")
            
            provider_instance = self.get_provider_instance(provider_name)
            # 检查是否有轮询方法
            if hasattr(provider_instance, 'poll_scan_status'):
                return provider_instance.poll_scan_status(qrcode_code, interval, max_attempts)
            else:
                return {"success": False, "msg": f"提供者 {provider_name} 不支持轮询功能"}
    
    def get_provider_instance(self, provider_name: Optional[str] = None) -> Any:
        """获取消息提供者实例
        
        Args:
            provider_name: 提供者名称，如果为None则使用默认提供者
            
        Returns:
            消息提供者实例
        """
        if provider_name is None:
            provider_name = self.get_default_provider()
        
        if provider_name not in self._providers:
            raise ValueError(f"未知的消息提供者: {provider_name}")
        
        if not self.config["providers"][provider_name].get("enabled", False):
            raise ValueError(f"消息提供者 {provider_name} 未启用")
        
        # 如果实例不存在，创建新实例
        if provider_name not in self._provider_instances:
            provider_class = self._providers[provider_name]
            provider_config = self.config["providers"][provider_name]["config"]
            
            try:
                # 特殊处理：内置提供者不需要配置
                if provider_name == "wxpusher":
                    # WxPusherProvider 作为内置提供者，不需要配置参数
                    instance = provider_class()
                else:
                    # 其他提供者需要配置参数
                    if not provider_config:
                        raise ValueError(f"消息提供者 {provider_name} 需要配置参数")
                    instance = provider_class(**provider_config)
                
                self._provider_instances[provider_name] = instance
                self.logger.debug(f"创建消息提供者实例: {provider_name}")
            except Exception as e:
                self.logger.error(f"创建消息提供者实例失败 {provider_name}: {e}")
                raise
        
        return self._provider_instances[provider_name]
    
    def test_provider(self, provider_name: str, test_config: Optional[Dict[str, Any]] = None) -> bool:
        """测试消息提供者
        
        Args:
            provider_name: 提供者名称
            test_config: 测试配置，如果为None则使用当前配置
            
        Returns:
            测试是否成功
        """
        if provider_name not in self._providers:
            self.logger.error(f"未知的消息提供者: {provider_name}")
            return False
        
        try:
            if test_config is None:
                test_config = self.config["providers"][provider_name]["config"]
            
            provider_class = self._providers[provider_name]
            test_instance = provider_class(**test_config)
            
            # 尝试发送测试消息
            test_result = test_instance.send_message(
                user_id="test_user",
                title="测试消息",
                content="这是一条测试消息，用于验证消息提供者配置是否正确。",
                summary="测试消息"
            )
            
            self.logger.info(f"消息提供者 {provider_name} 测试成功")
            return True
            
        except Exception as e:
            self.logger.error(f"消息提供者 {provider_name} 测试失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取消息提供者状态
        
        Returns:
            包含所有提供者状态的字典
        """
        status = {
            "default_provider": self.get_default_provider(),
            "config_file": self.config_file,
            "providers": {}
        }
        
        for name in self._providers:
            provider_status = {
                "enabled": self.config["providers"][name].get("enabled", False),
                "config": self.config["providers"][name].get("config", {}),
                "available": True
            }
            
            # 检查配置是否完整
            if name == "wxpusher":
                # WxPusher作为内置提供者，始终配置完整
                provider_status["config_complete"] = True
                provider_status["builtin"] = True
                provider_status["subscription_supported"] = True
            elif name == "dingtalk":
                provider_status["config_complete"] = bool(provider_status["config"].get("webhook_url"))
                provider_status["subscription_supported"] = False
            elif name == "wechat_work":
                provider_status["config_complete"] = all([
                    provider_status["config"].get("corp_id"),
                    provider_status["config"].get("agent_id"),
                    provider_status["config"].get("secret")
                ])
            elif name == "email":
                provider_status["config_complete"] = all([
                    provider_status["config"].get("smtp_host"),
                    provider_status["config"].get("username"),
                    provider_status["config"].get("password")
                ])
            
            status["providers"][name] = provider_status
        
        return status


# 全局消息提供者管理器实例
_messaging_manager = None


def get_messaging_manager() -> MessageProviderManager:
    """获取全局消息提供者管理器实例"""
    global _messaging_manager
    if _messaging_manager is None:
        _messaging_manager = MessageProviderManager()
    return _messaging_manager
