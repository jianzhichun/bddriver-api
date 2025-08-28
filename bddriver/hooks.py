"""
BaiduDriver 钩子系统

支持在关键操作前执行自定义逻辑，如支付验证、权限检查等
"""

from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from contextlib import contextmanager
import asyncio
import inspect


class HookEvent(Enum):
    """钩子事件类型"""
    
    # 授权相关
    BEFORE_AUTH_REQUEST = "before_auth_request"      # 授权请求前
    AFTER_AUTH_SUCCESS = "after_auth_success"        # 授权成功后
    AFTER_AUTH_FAILURE = "after_auth_failure"        # 授权失败后
    
    # 文件操作相关
    BEFORE_FILE_OPERATION = "before_file_operation"  # 文件操作前
    AFTER_FILE_OPERATION = "after_file_operation"    # 文件操作后
    
    # 消息推送相关
    BEFORE_MESSAGE_SEND = "before_message_send"      # 消息发送前
    AFTER_MESSAGE_SEND = "after_message_send"        # 消息发送后
    
    # 自定义事件
    CUSTOM = "custom"                                # 自定义事件


@dataclass
class HookContext:
    """钩子执行上下文"""
    
    event: HookEvent
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HookResult:
    """钩子执行结果"""
    
    def __init__(self, success: bool = True, data: Optional[Dict[str, Any]] = None, 
                 error: Optional[str] = None, should_continue: bool = True):
        self.success = success
        self.data = data or {}
        self.error = error
        self.should_continue = should_continue
    
    @classmethod
    def success(cls, data: Optional[Dict[str, Any]] = None) -> 'HookResult':
        """创建成功结果"""
        return cls(success=True, data=data, should_continue=True)
    
    @classmethod
    def failure(cls, error: str, should_continue: bool = False) -> 'HookResult':
        """创建失败结果"""
        return cls(success=False, error=error, should_continue=should_continue)
    
    @classmethod
    def stop(cls, error: str = None) -> 'HookResult':
        """创建停止执行的结果"""
        return cls(success=False, error=error, should_continue=False)


class HookManager:
    """钩子管理器"""
    
    def __init__(self):
        self._hooks: Dict[HookEvent, List[Callable]] = {
            event: [] for event in HookEvent
        }
        self._async_hooks: Dict[HookEvent, List[Callable]] = {
            event: [] for event in HookEvent
        }
        self._global_hooks: Dict[str, List[Callable]] = {}
        self._global_async_hooks: Dict[str, List[Callable]] = {}
    
    def register_hook(self, event: HookEvent, hook_func: Callable, 
                     priority: int = 0) -> None:
        """注册钩子函数
        
        Args:
            event: 钩子事件类型
            hook_func: 钩子函数，接收 HookContext 参数，返回 HookResult
            priority: 优先级，数字越小优先级越高
        """
        if not callable(hook_func):
            raise ValueError("钩子函数必须是可调用的")
        
        # 检查函数签名
        sig = inspect.signature(hook_func)
        if len(sig.parameters) != 1:
            raise ValueError("钩子函数必须只接收一个 HookContext 参数")
        
        # 判断是否为异步函数
        if asyncio.iscoroutinefunction(hook_func):
            self._async_hooks[event].append((priority, hook_func))
        else:
            self._hooks[event].append((priority, hook_func))
        
        # 按优先级排序
        self._hooks[event].sort(key=lambda x: x[0])
        self._async_hooks[event].sort(key=lambda x: x[0])
    
    def register_global_hook(self, event_name: str, hook_func: Callable, 
                           priority: int = 0) -> None:
        """注册全局钩子函数
        
        Args:
            event_name: 自定义事件名称
            hook_func: 钩子函数
            priority: 优先级
        """
        if event_name not in self._global_hooks:
            self._global_hooks[event_name] = []
            self._global_async_hooks[event_name] = []
        
        if asyncio.iscoroutinefunction(hook_func):
            self._global_async_hooks[event_name].append((priority, hook_func))
            self._global_async_hooks[event_name].sort(key=lambda x: x[0])
        else:
            self._global_hooks[event_name].append((priority, hook_func))
            self._global_hooks[event_name].sort(key=lambda x: x[0])
    
    def unregister_hook(self, event: HookEvent, hook_func: Callable) -> bool:
        """注销钩子函数
        
        Args:
            event: 钩子事件类型
            hook_func: 要注销的钩子函数
            
        Returns:
            是否成功注销
        """
        success = False
        
        # 从同步钩子中移除
        for i, (_, func) in enumerate(self._hooks[event]):
            if func == hook_func:
                self._hooks[event].pop(i)
                success = True
                break
        
        # 从异步钩子中移除
        for i, (_, func) in enumerate(self._async_hooks[event]):
            if func == hook_func:
                self._async_hooks[event].pop(i)
                success = True
                break
        
        return success
    
    def unregister_global_hook(self, event_name: str, hook_func: Callable) -> bool:
        """注销全局钩子函数"""
        success = False
        
        if event_name in self._global_hooks:
            for i, (_, func) in enumerate(self._global_hooks[event_name]):
                if func == hook_func:
                    self._global_hooks[event_name].pop(i)
                    success = True
                    break
        
        if event_name in self._global_async_hooks:
            for i, (_, func) in enumerate(self._global_async_hooks[event_name]):
                if func == hook_func:
                    self._global_async_hooks[event_name].pop(i)
                    success = True
                    break
        
        return success
    
    def execute_hooks(self, event: HookEvent, context: HookContext) -> HookResult:
        """执行同步钩子
        
        Args:
            event: 钩子事件类型
            context: 钩子上下文
            
        Returns:
            钩子执行结果
        """
        # 执行同步钩子
        for _, hook_func in self._hooks[event]:
            try:
                result = hook_func(context)
                if not isinstance(result, HookResult):
                    result = HookResult.success({"data": result})
                
                if not result.should_continue:
                    return result
                    
            except Exception as e:
                return HookResult.failure(f"钩子执行失败: {e}", should_continue=False)
        
        return HookResult.success()
    
    async def execute_async_hooks(self, event: HookEvent, context: HookContext) -> HookResult:
        """执行异步钩子
        
        Args:
            event: 钩子事件类型
            context: 钩子上下文
            
        Returns:
            钩子执行结果
        """
        # 执行异步钩子
        for _, hook_func in self._async_hooks[event]:
            try:
                result = await hook_func(context)
                if not isinstance(result, HookResult):
                    result = HookResult.success({"data": result})
                
                if not result.should_continue:
                    return result
                    
            except Exception as e:
                return HookResult.failure(f"异步钩子执行失败: {e}", should_continue=False)
        
        return HookResult.success()
    
    def execute_global_hooks(self, event_name: str, context: HookContext) -> HookResult:
        """执行全局钩子"""
        if event_name not in self._global_hooks:
            return HookResult.success()
        
        for _, hook_func in self._global_hooks[event_name]:
            try:
                result = hook_func(context)
                if not isinstance(result, HookResult):
                    result = HookResult.success({"data": result})
                
                if not result.should_continue:
                    return result
                    
            except Exception as e:
                return HookResult.failure(f"全局钩子执行失败: {e}", should_continue=False)
        
        return HookResult.success()
    
    async def execute_global_async_hooks(self, event_name: str, context: HookContext) -> HookResult:
        """执行全局异步钩子"""
        if event_name not in self._global_async_hooks:
            return HookResult.success()
        
        for _, hook_func in self._global_async_hooks[event_name]:
            try:
                result = await hook_func(context)
                if not isinstance(result, HookResult):
                    result = HookResult.success({"data": result})
                
                if not result.should_continue:
                    return result
                    
            except Exception as e:
                return HookResult.failure(f"全局异步钩子执行失败: {e}", should_continue=False)
        
        return HookResult.success()
    
    def clear_hooks(self, event: Optional[HookEvent] = None) -> None:
        """清空钩子
        
        Args:
            event: 指定事件类型，如果为None则清空所有
        """
        if event is None:
            self._hooks = {e: [] for e in HookEvent}
            self._async_hooks = {e: [] for e in HookEvent}
        else:
            self._hooks[event] = []
            self._async_hooks[event] = []
    
    def clear_global_hooks(self, event_name: Optional[str] = None) -> None:
        """清空全局钩子"""
        if event_name is None:
            self._global_hooks.clear()
            self._global_async_hooks.clear()
        else:
            self._global_hooks.pop(event_name, None)
            self._global_async_hooks.pop(event_name, None)
    
    def get_hook_count(self, event: HookEvent) -> int:
        """获取指定事件的钩子数量"""
        return len(self._hooks[event]) + len(self._async_hooks[event])
    
    def get_global_hook_count(self, event_name: str) -> int:
        """获取全局钩子数量"""
        return (len(self._global_hooks.get(event_name, [])) + 
                len(self._global_async_hooks.get(event_name, [])))


# 全局钩子管理器实例
hook_manager = HookManager()


# 装饰器：用于标记钩子函数
def hook(event: HookEvent, priority: int = 0):
    """钩子装饰器
    
    Args:
        event: 钩子事件类型
        priority: 优先级
        
    Example:
        @hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
        def payment_verification(context: HookContext) -> HookResult:
            # 支付验证逻辑
            if not verify_payment(context.data.get('user_id')):
                return HookResult.stop("支付验证失败")
            return HookResult.success()
    """
    def decorator(func):
        hook_manager.register_hook(event, func, priority)
        return func
    return decorator


def global_hook(event_name: str, priority: int = 0):
    """全局钩子装饰器"""
    def decorator(func):
        hook_manager.register_global_hook(event_name, func, priority)
        return func
    return decorator


# 便捷函数
def register_hook(event: HookEvent, hook_func: Callable, priority: int = 0) -> None:
    """注册钩子的便捷函数"""
    hook_manager.register_hook(event, hook_func, priority)


def register_global_hook(event_name: str, hook_func: Callable, priority: int = 0) -> None:
    """注册全局钩子的便捷函数"""
    hook_manager.register_global_hook(event_name, hook_func, priority)


def execute_hooks(event: HookEvent, context: HookContext) -> HookResult:
    """执行钩子的便捷函数"""
    return hook_manager.execute_hooks(event, context)


async def execute_async_hooks(event: HookEvent, context: HookContext) -> HookResult:
    """执行异步钩子的便捷函数"""
    return await hook_manager.execute_async_hooks(event, context)
