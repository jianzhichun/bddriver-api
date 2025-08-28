"""
Authorization Manager for BaiduDriver SDK
Handles device code authorization flow with WxPusher integration
"""

import time
from typing import Any, Dict, Optional

from ..config import config
from ..utils.errors import AuthTimeoutError, BaiduDriveError, WxPusherError
from ..utils.logger import (
    get_auth_logger,
    log_error,
    log_operation_end,
    log_operation_start,
)
from ..wxpusher.client import WxPusherClient

from .oauth import OAuthManager


class AuthManager:
    """授权管理器 - 专门处理设备码授权流程"""

    def __init__(self):
        """初始化授权管理器"""
        self.logger = get_auth_logger()
        self.general_config = config.get_general_config()

        # 初始化组件
        self.oauth_manager = OAuthManager()
        self.wxpusher_client = WxPusherClient()

        self.logger.info("授权管理器初始化完成")

    def request_device_access(
        self, target_user_id: str, scope: str = None, timeout: int = None
    ) -> Dict[str, Any]:
        """使用设备码模式请求访问授权

        Args:
            target_user_id: 目标用户的 WxPusher UID
            scope: 授权范围
            timeout: 授权超时时间（秒）

        Returns:
            授权结果，包含 access_token

        Raises:
            AuthTimeoutError: 授权超时
            WxPusherError: 消息发送失败
            BaiduDriveError: 百度 API 异常
        """
        if timeout is None:
            timeout = self.general_config.auth_timeout

        operation_name = "设备码授权请求"
        log_operation_start(
            self.logger, operation_name, target_user_id=target_user_id, timeout=timeout
        )

        start_time = time.time()

        try:
            # 1. 获取设备码
            self.logger.info("获取设备码")
            device_data = self.oauth_manager.get_device_code(scope)

            # 2. 显示用户授权信息
            user_code = device_data["user_code"]
            verification_url = device_data["verification_url"]
            expires_in = device_data.get("expires_in", 600)  # 默认10分钟

            print(f"\n{'='*60}")
            print(f"🔐 百度网盘设备码授权")
            print(f"{'='*60}")
            print(f"📱 请在浏览器中访问: {verification_url}")
            print(f"🔢 输入用户码: {user_code}")
            print(f"⏰ 用户码有效期: {expires_in} 秒")
            print(f"💡 授权完成后，我将自动获取访问权限")
            print(f"{'='*60}\n")

            # 3. 推送设备码信息给目标用户
            self._send_device_auth_notification(
                target_user_id, user_code, verification_url, expires_in
            )

            # 4. 轮询等待授权完成
            self.logger.info("开始等待用户授权...")
            token_data = self.oauth_manager.poll_device_authorization(
                device_code=device_data["device_code"],
                interval=device_data.get("interval", 5),
                timeout=min(timeout, expires_in),
            )

            # 5. 发送成功通知
            self._send_success_notification(target_user_id, None)

            # 6. 构建结果
            result = {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "expires_at": token_data.get("expires_at"),
                "scope": token_data.get("scope", scope or "basic,netdisk"),
                "token_type": token_data.get("token_type", "Bearer"),
                "auth_method": "device_code",
                "target_user_id": target_user_id,
            }

            duration = time.time() - start_time
            log_operation_end(
                self.logger,
                operation_name,
                success=True,
                duration=duration,
                access_token="已获取",
            )

            return result

        except Exception as e:
            log_error(self.logger, e, operation_name)
            raise

    def _send_device_auth_notification(
        self,
        target_user_id: str,
        user_code: str,
        verification_url: str,
        expires_in: int,
    ) -> None:
        """发送设备码授权通知"""
        try:
            result = self.wxpusher_client.send_device_auth_notification(
                user_id=target_user_id,
                user_code=user_code,
                verification_url=verification_url,
                expires_in=expires_in,
            )

            if result.get("success"):
                self.logger.info(f"设备码授权通知发送成功: {target_user_id}")
            else:
                self.logger.warning(f"设备码授权通知发送失败: {result.get('msg', '未知错误')}")

        except Exception as e:
            self.logger.error(f"发送设备码授权通知失败: {e}")
            raise WxPusherError(f"发送设备码授权通知失败: {e}", user_id=target_user_id)

    def _send_success_notification(
        self, target_user_id: str, file_path: str = None
    ) -> None:
        """发送授权成功通知"""
        try:
            result = self.wxpusher_client.send_success_notification(
                user_id=target_user_id
            )

            if result.get("success"):
                self.logger.info(f"授权成功通知发送成功: {target_user_id}")
            else:
                self.logger.warning(f"授权成功通知发送失败: {result.get('msg', '未知错误')}")

        except Exception as e:
            self.logger.warning(f"发送授权成功通知失败: {e}")
            # 不抛出异常，因为这不是关键操作

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 token 信息
        """
        self.logger.info("开始刷新访问令牌")

        try:
            token_data = self.oauth_manager.refresh_token(refresh_token)

            self.logger.info("访问令牌刷新成功")
            return {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "expires_at": token_data.get("expires_at"),
                "scope": token_data.get("scope", "basic,netdisk"),
                "token_type": token_data.get("token_type", "Bearer"),
            }

        except Exception as e:
            self.logger.error(f"刷新访问令牌失败: {e}")
            raise BaiduDriveError(f"刷新令牌失败: {e}")

    def validate_token(self, access_token: str) -> bool:
        """验证 access_token 是否有效

        Args:
            access_token: 访问令牌

        Returns:
            是否有效
        """
        try:
            return self.oauth_manager.validate_token(access_token)
        except Exception as e:
            self.logger.warning(f"令牌验证失败: {e}")
            return False

    def cleanup(self) -> None:
        """清理资源

        清理所有相关的资源，如临时文件、网络连接等
        """
        try:
            self.logger.info("开始清理授权管理器资源")

            # 清理OAuth管理器
            if hasattr(self.oauth_manager, "cleanup"):
                self.oauth_manager.cleanup()

            # 清理WxPusher客户端
            if hasattr(self.wxpusher_client, "cleanup"):
                self.wxpusher_client.cleanup()

            self.logger.info("授权管理器资源清理完成")

        except Exception as e:
            self.logger.warning(f"清理授权管理器资源时发生异常: {e}")
            # 清理过程中的异常不应该影响主流程
