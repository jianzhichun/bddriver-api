"""
消息推送提供者抽象基类

定义统一的消息推送接口，支持多种推送渠道
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class MessageStatus(Enum):
    """消息发送状态"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RATE_LIMITED = "rate_limited"


@dataclass
class MessageResult:
    """消息发送结果"""
    success: bool
    message_id: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageProvider(ABC):
    """消息推送提供者抽象基类
    
    所有消息推送渠道都需要实现这个接口
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化消息提供者
        
        Args:
            name: 提供者名称
            config: 配置参数
        """
        self.name = name
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置参数"""
        pass
    
    @abstractmethod
    def send_message(
        self, 
        user_id: str, 
        message: str, 
        title: Optional[str] = None,
        **kwargs
    ) -> MessageResult:
        """发送消息到指定用户
        
        Args:
            user_id: 用户标识符
            message: 消息内容
            title: 消息标题（可选）
            **kwargs: 其他参数
            
        Returns:
            MessageResult: 发送结果
        """
        pass
    
    @abstractmethod
    def validate_user_id(self, user_id: str) -> bool:
        """验证用户ID格式是否有效
        
        Args:
            user_id: 用户标识符
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息
        
        Args:
            user_id: 用户标识符
            
        Returns:
            Dict[str, Any]: 用户信息，如果获取失败返回None
        """
        pass
    
    def get_supported_features(self) -> List[str]:
        """获取支持的功能特性
        
        Returns:
            List[str]: 支持的功能列表
        """
        return ["basic_message"]
    
    def get_rate_limit_info(self) -> Optional[Dict[str, Any]]:
        """获取频率限制信息
        
        Returns:
            Dict[str, Any]: 频率限制信息，如果无限制返回None
        """
        return None
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"
