"""
Main BaiduDriver client interface
Based on TIP 0: Overall Architecture Design
Zero-configuration Baidu NetDisk authorization SDK
"""

import time
import asyncio
from threading import Thread
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Union

from .auth import AuthManager
from .config import config
from .fileops import FileOperationsManager
from .hooks import (
    HookEvent, HookContext, HookResult, hook_manager,
    execute_hooks, execute_async_hooks
)
from .utils.errors import (
    AuthTimeoutError,
    BaiduDriveError,
    BaiduDriverError,
    FileOperationError,
    WxPusherError,
)
from .utils.logger import get_logger, log_error, log_operation_end, log_operation_start


def _run_async_blocking(coro):
    """Run an async coroutine to completion from a sync context safely.

    - Uses asyncio.run when no loop is running.
    - When already inside a running loop (e.g., Jupyter/async app), runs the
      coroutine in a dedicated event loop on a background thread and blocks
      until it finishes.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in this thread
        return asyncio.run(coro)

    result_holder = {"result": None, "error": None}

    def _thread_runner():
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(coro)
            result_holder["result"] = result
        except Exception as exc:  # noqa: BLE001
            result_holder["error"] = exc
        finally:
            try:
                new_loop.close()
            except Exception:  # noqa: BLE001
                pass

    t = Thread(target=_thread_runner, daemon=True)
    t.start()
    t.join()

    if result_holder["error"] is not None:
        raise result_holder["error"]
    return result_holder["result"]


class BaiduDriver:
    """BaiduDriver 主客户端

    零配置开箱即用的百度网盘授权 SDK
    让用户 A 能够安全地访问用户 B 的百度网盘文件

    Usage:
        from bddriver import BaiduDriver

        # 创建客户端实例
        driver = BaiduDriver()

        # 发起授权请求
        result = driver.request_device_access("user_b_uid", "/files")

        # 使用文件
        files = driver.list_files(result['access_token'])
    """

    def __init__(self):
        """初始化 BaiduDriver 客户端"""
        self.logger = get_logger("client")

        # 初始化组件
        self.auth_manager = AuthManager()
        self.file_manager = FileOperationsManager()

        # 配置
        self.general_config = config.get_general_config()

        # 状态管理
        self._current_tokens: Dict[str, Dict[str, Any]] = {}

        # 钩子管理器
        self.hook_manager = hook_manager

        self.logger.info("BaiduDriver 客户端初始化完成")

    def request_device_access(
        self, target_user_id: str, scope: str = None, timeout: int = None,
        hook_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用设备码模式获取访问授权

        Args:
            target_user_id: 目标用户的 WxPusher UID
            scope: 授权范围，默认为 'basic,netdisk'
            timeout: 授权超时时间（秒）
            hook_data: 传递给钩子的额外数据

        Returns:
            授权结果，包含 access_token

        Example:
            >>> driver = BaiduDriver()
            >>> result = driver.request_device_access("user_b_uid")
            >>> print(f"授权成功: {result['access_token']}")

        Note:
            设备码模式无需回调链接，适合任何环境部署
        """
        # 执行授权前钩子
        hook_context = HookContext(
            event=HookEvent.BEFORE_AUTH_REQUEST,
            data={
                "target_user_id": target_user_id,
                "scope": scope,
                "timeout": timeout,
                **(hook_data or {})
            }
        )
        
        hook_result = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, hook_context)
        if not hook_result.success:
            raise BaiduDriverError(f"授权前钩子执行失败: {hook_result.error}")
        if not hook_result.should_continue:
            raise BaiduDriverError(f"授权被钩子阻止: {hook_result.error}")
        
        # 执行异步授权前钩子（阻塞等待完成，兼容已有事件循环）
        async_result = _run_async_blocking(
            execute_async_hooks(HookEvent.BEFORE_AUTH_REQUEST, hook_context)
        )
        if not async_result.success:
            raise BaiduDriverError(f"授权前异步钩子执行失败: {async_result.error}")
        if not async_result.should_continue:
            raise BaiduDriverError(f"授权被异步钩子阻止: {async_result.error}")
        
        try:
            # 执行授权
            auth_result = self.auth_manager.request_device_access(target_user_id, scope, timeout)
            
            # 执行授权成功钩子
            success_context = HookContext(
                event=HookEvent.AFTER_AUTH_SUCCESS,
                data={
                    "target_user_id": target_user_id,
                    "scope": scope,
                    "timeout": timeout,
                    "auth_result": auth_result,
                    **(hook_data or {})
                }
            )
            execute_hooks(HookEvent.AFTER_AUTH_SUCCESS, success_context)
            
            return auth_result
            
        except Exception as e:
            # 执行授权失败钩子
            failure_context = HookContext(
                event=HookEvent.AFTER_AUTH_FAILURE,
                data={
                    "target_user_id": target_user_id,
                    "scope": scope,
                    "timeout": timeout,
                    "error": str(e),
                    **(hook_data or {})
                }
            )
            execute_hooks(HookEvent.AFTER_AUTH_FAILURE, failure_context)
            raise

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 token 信息
        """
        return self.auth_manager.refresh_token(refresh_token)

    def is_token_expired(self, access_token: str) -> bool:
        """检查访问令牌是否过期

        Args:
            access_token: 访问令牌

        Returns:
            是否过期
        """
        return not self.auth_manager.validate_token(access_token)

    # File Operations - 文件操作接口

    def list_files(
        self,
        access_token: str,
        path: str = "/",
        limit: int = 100,
        order: str = "time",
        desc: bool = True,
        hook_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """列出文件和文件夹

        Args:
            access_token: 访问令牌
            path: 目录路径，默认根目录
            limit: 返回数量限制，默认 100，最大 1000
            order: 排序方式，可选 time/size/name
            desc: 是否降序排列
            hook_data: 传递给钩子的额外数据

        Returns:
            文件列表，每个文件包含：
            - filename: 文件名
            - path: 文件路径
            - size: 文件大小（字节）
            - is_dir: 是否为目录
            - mtime: 修改时间
            - md5: 文件 MD5 (如果可用)

        Example:
            files = driver.list_files(access_token, "/我的文档")
            for file in files:
                print(f"{file['filename']} - {file['size']} bytes")
        """
        self.logger.info(f"列出文件: {path}")

        # 执行文件操作前钩子
        hook_context = HookContext(
            event=HookEvent.BEFORE_FILE_OPERATION,
            data={
                "operation": "list_files",
                "access_token": access_token,
                "path": path,
                "limit": limit,
                "order": order,
                "desc": desc,
                **(hook_data or {})
            }
        )
        
        hook_result = execute_hooks(HookEvent.BEFORE_FILE_OPERATION, hook_context)
        if not hook_result.success:
            raise BaiduDriverError(f"文件操作前钩子执行失败: {hook_result.error}")
        if not hook_result.should_continue:
            raise BaiduDriverError(f"文件操作被钩子阻止: {hook_result.error}")
        
        # 执行异步文件操作前钩子（阻塞等待完成，兼容已有事件循环）
        async_result = _run_async_blocking(
            execute_async_hooks(HookEvent.BEFORE_FILE_OPERATION, hook_context)
        )
        if not async_result.success:
            raise BaiduDriverError(f"文件操作前异步钩子执行失败: {async_result.error}")
        if not async_result.should_continue:
            raise BaiduDriverError(f"文件操作被异步钩子阻止: {async_result.error}")

        try:
            # 执行文件操作
            result = self.file_manager.list_files(
                access_token=access_token,
                path=path,
                limit=limit,
                order=order,
                desc=desc,
            )
            
            # 执行文件操作后钩子
            after_context = HookContext(
                event=HookEvent.AFTER_FILE_OPERATION,
                data={
                    "operation": "list_files",
                    "access_token": access_token,
                    "path": path,
                    "limit": limit,
                    "order": order,
                    "desc": desc,
                    "result": result,
                    **(hook_data or {})
                }
            )
            execute_hooks(HookEvent.AFTER_FILE_OPERATION, after_context)
            
            return result
            
        except Exception as e:
            # 执行文件操作失败钩子
            failure_context = HookContext(
                event=HookEvent.AFTER_FILE_OPERATION,
                data={
                    "operation": "list_files",
                    "access_token": access_token,
                    "path": path,
                    "limit": limit,
                    "order": order,
                    "desc": desc,
                    "error": str(e),
                    **(hook_data or {})
                }
            )
            execute_hooks(HookEvent.AFTER_FILE_OPERATION, failure_context)
            self.logger.error(f"列出文件失败: {e}")
            raise

    def get_file_info(self, access_token: str, file_path: str) -> Dict[str, Any]:
        """获取文件详细信息

        Args:
            access_token: 访问令牌
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        return self.file_manager.get_file_info(access_token, file_path)

    def download_file(
        self,
        access_token: str,
        remote_path: str,
        local_path: str,
        progress_callback: Callable[[float, int, int], None] = None,
    ) -> bool:
        """下载文件

        Args:
            access_token: 访问令牌
            remote_path: 远程文件路径
            local_path: 本地保存路径
            progress_callback: 进度回调函数 (进度百分比, 当前大小, 总大小)

        Returns:
            是否下载成功

        Example:
            def on_progress(progress, current, total):
                print(f"下载进度: {progress:.1f}% ({current}/{total})")

            success = driver.download_file(
                access_token, "/大文件.zip", "./downloads/file.zip", on_progress
            )
        """
        return self.file_manager.download_file(
            access_token, remote_path, local_path, progress_callback
        )

    def upload_file(
        self,
        access_token: str,
        local_path: str,
        remote_path: str,
        progress_callback: Callable[[float, int, int], None] = None,
    ) -> bool:
        """上传文件

        Args:
            access_token: 访问令牌
            local_path: 本地文件路径
            remote_path: 远程保存路径
            progress_callback: 进度回调函数

        Returns:
            是否上传成功
        """
        return self.file_manager.upload_file(
            access_token, local_path, remote_path, progress_callback
        )

    def delete_file(self, access_token: str, file_path: str) -> bool:
        """删除文件或文件夹

        Args:
            access_token: 访问令牌
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        return self.file_manager.delete_file(access_token, file_path)

    def copy_file(
        self, access_token: str, source_path: str, dest_path: str, new_name: str = None
    ) -> bool:
        """复制文件

        Args:
            access_token: 访问令牌
            source_path: 源文件路径
            dest_path: 目标目录路径
            new_name: 新文件名（可选）

        Returns:
            是否复制成功
        """
        return self.file_manager.copy_file(
            access_token, source_path, dest_path, new_name
        )

    def move_file(
        self, access_token: str, source_path: str, dest_path: str, new_name: str = None
    ) -> bool:
        """移动文件

        Args:
            access_token: 访问令牌
            source_path: 源文件路径
            dest_path: 目标目录路径
            new_name: 新文件名（可选）

        Returns:
            是否移动成功
        """
        return self.file_manager.move_file(
            access_token, source_path, dest_path, new_name
        )

    def create_folder(self, access_token: str, folder_path: str) -> bool:
        """创建文件夹

        Args:
            access_token: 访问令牌
            folder_path: 文件夹路径

        Returns:
            是否创建成功
        """
        return self.file_manager.create_folder(access_token, folder_path)

    # Context Manager Support - 上下文管理器支持

    @contextmanager
    def auth_session(self, target_user_id: str, file_path: str = "/", **kwargs):
        """授权会话上下文管理器

        自动管理授权生命周期，确保资源正确清理

        Args:
            target_user_id: 目标用户 ID
            file_path: 文件路径
            **kwargs: 其他授权参数

        Usage:
            with driver.auth_session("user123", "/photos") as session:
                access_token = session['access_token']
                files = driver.list_files(access_token)
                # 会话结束时自动清理
        """
        auth_result = None
        try:
            self.logger.info(f"开始授权会话: {target_user_id}")
            auth_result = self.request_access(target_user_id, file_path, **kwargs)
            yield auth_result
        finally:
            if auth_result:
                self.logger.info(f"授权会话结束: {auth_result.get('request_id')}")

    # Utility Methods - 工具方法

    def get_auth_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """获取授权请求状态

        Args:
            request_id: 请求 ID

        Returns:
            请求状态信息
        """
        return self.auth_manager.get_request_status(request_id)

    def cancel_auth_request(self, request_id: str) -> bool:
        """取消授权请求

        Args:
            request_id: 请求 ID

        Returns:
            是否成功取消
        """
        return self.auth_manager.cancel_request(request_id)

    def get_version(self) -> str:
        """获取 SDK 版本"""
        from . import __version__

        return __version__

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息（脱敏后）"""
        try:
            all_config = config.get_all_config()

            # 脱敏处理
            sanitized_config = {}
            for module, module_config in all_config.items():
                sanitized_module = {}
                for key, value in module_config.items():
                    if any(
                        sensitive in key.lower()
                        for sensitive in ["token", "secret", "key"]
                    ):
                        if isinstance(value, str) and len(value) > 6:
                            sanitized_module[key] = (
                                value[:3] + "*" * (len(value) - 6) + value[-3:]
                            )
                        else:
                            sanitized_value = str(value)
                            sanitized_module[key] = "*" * max(1, len(sanitized_value))
                    else:
                        sanitized_module[key] = value
                sanitized_config[module] = sanitized_module

            return sanitized_config
        except Exception as e:
            self.logger.error(f"获取配置信息失败: {e}")
            return {}

    def cleanup(self) -> None:
        """清理资源"""
        try:
            self.auth_manager.cleanup()
            self._current_tokens.clear()
            self.logger.info("BaiduDriver 资源清理完成")
        except Exception as e:
            self.logger.warning(f"资源清理异常: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()

    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except:
            pass
