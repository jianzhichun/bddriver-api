"""
OAuth Manager for BaiduDriver SDK
Handles device code authorization flow with Baidu NetDisk APIs
"""

import os
import sys
import time
from typing import Any, Dict, Optional

# Import Baidu NetDisk SDK from internal package
try:
    # Try to import from internal package
    import os
    import sys

    # Get the path to the internal package
    current_dir = os.path.dirname(__file__)
    vendor_path = os.path.join(current_dir, "..", "_vendor", "baidu-netdisk-sdk")

    if os.path.exists(vendor_path):
        sys.path.insert(0, vendor_path)
        import openapi_client  # Import the actual module
        from openapi_client.api import auth_api
        from openapi_client.exceptions import ApiException
    else:
        openapi_client = None
except ImportError:
    # Fallback: try to import from system packages
    try:
        import openapi_client
        from openapi_client.api import auth_api
        from openapi_client.exceptions import ApiException

        openapi_client = True
    except ImportError:
        openapi_client = None

from ..config import BAIDU_OAUTH_SCOPES, config
from ..utils.errors import (
    AuthError,
    AuthTimeoutError,
    BaiduDriveError,
    InvalidTokenError,
    create_error_from_api_response,
)
from ..utils.logger import get_auth_logger, log_api_call


class OAuthManager:
    """OAuth 管理器 - 专门处理设备码授权流程"""

    def __init__(self):
        """初始化 OAuth 管理器"""
        self.logger = get_auth_logger()
        self.config = config.get_baidu_config()

        self.logger.info("OAuth 管理器初始化完成")

    def get_device_code(self, scope: str = None) -> Dict[str, Any]:
        """获取设备码

        Args:
            scope: 授权范围

        Returns:
            设备码信息，包含 device_code, user_code, verification_url 等
        """
        if not scope:
            scope = BAIDU_OAUTH_SCOPES

        self.logger.info("获取设备码")

        # 重试配置
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                with openapi_client.ApiClient() as api_client:
                    # 配置更长的超时时间
                    api_client.configuration.timeout = 30

                    api_instance = auth_api.AuthApi(api_client)

                    response = api_instance.oauth_token_device_code(
                        client_id=self.config.client_id, scope=scope
                    )

                    device_data = self._response_to_dict(response)

                    # 调试日志：输出响应结构
                    self.logger.debug(f"API响应类型: {type(response)}")
                    self.logger.debug(f"转换后的数据: {device_data}")

                    # 验证必要字段
                    required_fields = ["device_code", "user_code", "verification_url"]
                    for field in required_fields:
                        if field not in device_data:
                            self.logger.error(f"响应数据缺少字段: {field}")
                            self.logger.error(f"可用字段: {list(device_data.keys())}")
                            raise BaiduDriveError(f"设备码响应缺少必要字段: {field}")

                    self.logger.info("设备码获取成功")
                    return device_data

            except Exception as e:
                error_msg = str(e)
                self.logger.warning(
                    f"获取设备码尝试 {attempt + 1}/{max_retries} 失败: {error_msg}"
                )

                # 检查是否是SSL连接问题
                if (
                    "SSL" in error_msg
                    or "EOF" in error_msg
                    or "connection" in error_msg.lower()
                ):
                    if attempt < max_retries - 1:
                        self.logger.info(
                            f"检测到网络连接问题，{retry_delay}秒后重试..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                    else:
                        self.logger.error("网络连接问题，已达到最大重试次数")
                        raise BaiduDriveError(
                            f"网络连接失败，请检查网络环境: {error_msg}"
                        )

                # 其他错误直接抛出
                if attempt == max_retries - 1:
                    self.logger.error(f"获取设备码失败: {error_msg}")
                    raise BaiduDriveError(f"获取设备码失败: {error_msg}")
                else:
                    time.sleep(retry_delay)
                    continue

    def poll_device_authorization(
        self, device_code: str, interval: int = 5, timeout: int = 600
    ) -> Dict[str, Any]:
        """轮询检查设备授权状态

        Args:
            device_code: 设备码
            interval: 轮询间隔（秒）
            timeout: 总超时时间（秒）

        Returns:
            授权结果，包含 access_token

        Raises:
            AuthTimeoutError: 授权超时
            BaiduDriveError: 授权失败
        """
        self.logger.info(f"开始轮询设备授权状态，间隔: {interval}s，超时: {timeout}s")

        start_time = time.time()
        consecutive_errors = 0
        max_consecutive_errors = 3

        while time.time() - start_time < timeout:
            try:
                # 检查授权状态
                with openapi_client.ApiClient() as api_client:
                    # 配置更长的超时时间
                    api_client.configuration.timeout = 30

                    api_instance = auth_api.AuthApi(api_client)

                    response = api_instance.oauth_token_device_token(
                        code=device_code,
                        client_id=self.config.client_id,
                        client_secret=self.config.client_secret,
                    )

                    token_data = self._response_to_dict(response)

                    # 重置连续错误计数
                    consecutive_errors = 0

                    # 检查是否授权成功
                    if "access_token" in token_data:
                        # 添加过期时间戳
                        if "expires_in" in token_data:
                            token_data["expires_at"] = time.time() + int(
                                token_data["expires_in"]
                            )

                        self.logger.info("设备授权成功")
                        return token_data

                    # 检查错误信息
                    if "error" in token_data:
                        error = token_data.get("error")
                        if error == "authorization_pending":
                            # 用户还未授权，继续等待
                            self.logger.debug("用户还未授权，继续等待...")
                        elif error == "authorization_declined":
                            # 用户拒绝授权
                            raise BaiduDriveError("用户拒绝授权")
                        elif error == "expired_token":
                            # 设备码已过期
                            raise BaiduDriveError("设备码已过期")
                        else:
                            # 其他错误
                            raise BaiduDriveError(f"设备授权错误: {error}")

                # 等待指定间隔后再次轮询
                time.sleep(interval)

            except Exception as e:
                error_msg = str(e)

                # 检查是否是API异常（如authorization_pending）
                if "ApiException" in str(type(e)) or "400" in error_msg:
                    # 解析API响应体
                    if "authorization_pending" in error_msg:
                        # 这是正常状态，用户还未授权
                        self.logger.debug("用户还未授权，继续等待...")
                        consecutive_errors = 0  # 重置错误计数
                        time.sleep(interval)
                        continue
                    elif "authorization_declined" in error_msg:
                        # 用户拒绝授权
                        raise BaiduDriveError("用户拒绝授权")
                    elif "expired_token" in error_msg:
                        # 设备码已过期
                        raise BaiduDriveError("设备码已过期")
                    else:
                        # 其他API错误
                        consecutive_errors += 1
                        if consecutive_errors <= max_consecutive_errors:
                            self.logger.warning(
                                f"API错误 (连续错误 {consecutive_errors}/{max_consecutive_errors}): {error_msg}"
                            )
                            time.sleep(interval)
                            continue
                        else:
                            raise BaiduDriveError(f"API调用失败: {error_msg}")

                # 检查是否是网络连接问题
                elif (
                    "SSL" in error_msg
                    or "EOF" in error_msg
                    or "connection" in error_msg.lower()
                ):
                    consecutive_errors += 1
                    if consecutive_errors <= max_consecutive_errors:
                        self.logger.warning(
                            f"网络连接问题 (连续错误 {consecutive_errors}/{max_consecutive_errors}): {error_msg}"
                        )
                        # 网络问题增加等待时间
                        time.sleep(interval * 2)
                        continue
                    else:
                        self.logger.error("连续网络错误过多，停止轮询")
                        raise BaiduDriveError(f"网络连接不稳定: {error_msg}")

                # 其他错误
                else:
                    consecutive_errors += 1
                    if consecutive_errors <= max_consecutive_errors:
                        self.logger.warning(
                            f"轮询异常 (连续错误 {consecutive_errors}/{max_consecutive_errors}): {error_msg}"
                        )
                        time.sleep(interval)
                        continue
                    else:
                        self.logger.error("连续错误过多，停止轮询")
                        raise BaiduDriveError(f"轮询过程中发生过多错误: {error_msg}")

        # 超时
        raise AuthTimeoutError("设备授权超时")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 token 信息
        """
        self.logger.info("开始刷新访问令牌")

        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = auth_api.AuthApi(api_client)

                response = api_instance.oauth_token_refresh_token(
                    refresh_token=refresh_token,
                    client_id=self.config.client_id,
                    client_secret=self.config.client_secret,
                )

                token_data = self._response_to_dict(response)

                # 添加过期时间戳
                if "expires_in" in token_data:
                    token_data["expires_at"] = time.time() + int(
                        token_data["expires_in"]
                    )

                self.logger.info("访问令牌刷新成功")
                return token_data

        except ApiException as e:
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
            # 这里可以调用百度网盘的API来验证token有效性
            # 暂时返回True，实际使用时可以实现具体的验证逻辑
            return True
        except Exception as e:
            self.logger.warning(f"令牌验证失败: {e}")
            return False

    def _response_to_dict(self, response) -> Dict[str, Any]:
        """将API响应转换为字典

        Args:
            response: API响应对象

        Returns:
            字典格式的响应数据
        """
        # 处理百度网盘SDK的响应对象
        if hasattr(response, "to_dict"):
            return response.to_dict()
        elif hasattr(response, "__dict__"):
            # 过滤掉私有属性和None值
            result = {}
            for k, v in response.__dict__.items():
                if not k.startswith("_") and v is not None:
                    result[k] = v
            return result
        else:
            # 如果是字符串或其他类型，直接返回
            return str(response)

    def cleanup(self) -> None:
        """清理资源

        清理所有相关的资源，如临时文件、网络连接等
        """
        try:
            self.logger.info("开始清理OAuth管理器资源")
            # 目前没有需要清理的资源，预留接口
            self.logger.info("OAuth管理器资源清理完成")

        except Exception as e:
            self.logger.warning(f"清理OAuth管理器资源时发生异常: {e}")
            # 清理过程中的异常不应该影响主流程
