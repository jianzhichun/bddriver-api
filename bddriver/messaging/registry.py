"""
消息提供者注册表

管理多个消息提供者，支持自动检测和选择
"""

from typing import Dict, Optional, List, Type
from .base import MessageProvider


class MessageProviderRegistry:
    """消息提供者注册表
    
    管理多个消息提供者，支持自动检测用户ID格式并选择合适的提供者
    """
    
    def __init__(self):
        """初始化注册表"""
        self._providers: Dict[str, MessageProvider] = {}
        self._provider_types: Dict[str, Type[MessageProvider]] = {}
    
    def register_provider(self, name: str, provider: MessageProvider) -> None:
        """注册消息提供者
        
        Args:
            name: 提供者名称
            provider: 提供者实例
        """
        self._providers[name] = provider
    
    def register_provider_type(self, name: str, provider_class: Type[MessageProvider]) -> None:
        """注册消息提供者类型
        
        Args:
            name: 提供者类型名称
            provider_class: 提供者类
        """
        self._provider_types[name] = provider_class
    
    def create_provider(self, name: str, config: Dict) -> MessageProvider:
        """创建消息提供者实例
        
        Args:
            name: 提供者类型名称
            config: 配置参数
            
        Returns:
            MessageProvider: 提供者实例
            
        Raises:
            ValueError: 如果提供者类型未注册
        """
        if name not in self._provider_types:
            raise ValueError(f"未注册的消息提供者类型: {name}")
        
        provider_class = self._provider_types[name]
        return provider_class(config)
    
    def get_provider(self, name: str) -> Optional[MessageProvider]:
        """获取已注册的消息提供者
        
        Args:
            name: 提供者名称
            
        Returns:
            MessageProvider: 提供者实例，如果不存在返回None
        """
        return self._providers.get(name)
    
    def get_all_providers(self) -> List[MessageProvider]:
        """获取所有已注册的消息提供者
        
        Returns:
            List[MessageProvider]: 所有提供者列表
        """
        return list(self._providers.values())
    
    def detect_provider_by_user_id(self, user_id: str) -> Optional[MessageProvider]:
        """根据用户ID自动检测合适的消息提供者
        
        Args:
            user_id: 用户标识符
            
        Returns:
            MessageProvider: 合适的提供者，如果无法检测返回None
        """
        for provider in self._providers.values():
            if provider.validate_user_id(user_id):
                return provider
        return None
    
    def get_provider_names(self) -> List[str]:
        """获取所有已注册的提供者名称
        
        Returns:
            List[str]: 提供者名称列表
        """
        return list(self._providers.keys())
    
    def get_provider_types(self) -> List[str]:
        """获取所有已注册的提供者类型
        
        Returns:
            List[str]: 提供者类型名称列表
        """
        return list(self._provider_types.keys())
    
    def remove_provider(self, name: str) -> bool:
        """移除消息提供者
        
        Args:
            name: 提供者名称
            
        Returns:
            bool: 是否成功移除
        """
        if name in self._providers:
            del self._providers[name]
            return True
        return False
    
    def clear_providers(self) -> None:
        """清空所有已注册的提供者"""
        self._providers.clear()
    
    def __len__(self) -> int:
        return len(self._providers)
    
    def __contains__(self, name: str) -> bool:
        return name in self._providers
    
    def __iter__(self):
        return iter(self._providers.values())
