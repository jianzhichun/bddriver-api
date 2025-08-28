"""
Custom exception classes for BaiduDriver SDK
Based on TIP 7: Error Handling and Logging System
"""

from typing import Any, Dict, Optional


class BaiduDriverError(Exception):
    """百度网盘驱动基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class NetworkError(BaiduDriverError):
    """网络相关异常"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.url = url

        if status_code:
            self.details["status_code"] = status_code
        if url:
            self.details["url"] = url


class AuthError(BaiduDriverError):
    """授权相关异常"""

    def __init__(self, message: str, auth_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.auth_type = auth_type

        if auth_type:
            self.details["auth_type"] = auth_type


class AuthTimeoutError(AuthError):
    """授权超时异常"""

    def __init__(
        self,
        message: str = "授权请求超时",
        request_id: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, error_code="AUTH_TIMEOUT", **kwargs)
        self.request_id = request_id
        self.timeout = timeout

        if request_id:
            self.details["request_id"] = request_id
        if timeout:
            self.details["timeout"] = timeout


class WxPusherError(BaiduDriverError):
    """WxPusher 推送异常"""

    def __init__(
        self,
        message: str,
        api_error_code: Optional[int] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.api_error_code = api_error_code
        self.user_id = user_id

        if api_error_code:
            self.details["api_error_code"] = api_error_code
        if user_id:
            self.details["user_id"] = user_id


class BaiduDriveError(BaiduDriverError):
    """百度网盘 API 异常"""

    def __init__(
        self,
        message: str,
        api_error_code: Optional[int] = None,
        api_error_msg: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.api_error_code = api_error_code
        self.api_error_msg = api_error_msg

        if api_error_code:
            self.details["api_error_code"] = api_error_code
        if api_error_msg:
            self.details["api_error_msg"] = api_error_msg


class FileOperationError(BaiduDriveError):
    """文件操作异常"""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation

        if file_path:
            self.details["file_path"] = file_path
        if operation:
            self.details["operation"] = operation


class ConfigurationError(BaiduDriverError):
    """配置异常"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key

        if config_key:
            self.details["config_key"] = config_key


class TokenError(AuthError):
    """Token 相关异常"""

    def __init__(self, message: str, token_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.token_type = token_type

        if token_type:
            self.details["token_type"] = token_type


class InvalidTokenError(TokenError):
    """无效 Token 异常"""

    def __init__(self, message: str = "Token 无效或已过期", **kwargs):
        super().__init__(message, error_code="INVALID_TOKEN", **kwargs)


# 错误码映射
ERROR_CODE_MAPPING = {
    # 百度网盘 API 错误码
    -1: "系统错误",
    2: "参数错误",
    3: "用户未登录或者登录失败",
    4: "用户未授权",
    6: "不允许接入用户数据",
    42000: "access_token未授权",
    42001: "access_token过期",
    # WxPusher 错误码
    1000: "参数错误",
    1001: "appToken无效",
    1002: "内容不能为空",
    1003: "uid参数错误",
    1004: "内容长度超限",
}


def get_error_message(error_code: int) -> str:
    """根据错误码获取友好的错误信息"""
    return ERROR_CODE_MAPPING.get(error_code, f"未知错误 (错误码: {error_code})")


def create_error_from_api_response(
    api_name: str, response_data: Dict[str, Any]
) -> BaiduDriverError:
    """根据 API 响应创建相应的异常"""
    error_code = response_data.get("errno") or response_data.get("code")
    error_msg = response_data.get("errmsg") or response_data.get("msg")

    if not error_code:
        return BaiduDriverError(f"{api_name} API 调用失败")

    friendly_message = get_error_message(error_code)

    if api_name.lower() == "wxpusher":
        # 优先透出服务端 msg，避免误导开发与测试
        combined = error_msg or friendly_message
        err = WxPusherError(
            message=f"WxPusher 推送失败: {combined}",
            api_error_code=error_code,
            error_code="WXPUSHER_API_ERROR",
        )
        if error_msg:
            err.details["server_msg"] = error_msg
        return err
    else:
        combined = error_msg or friendly_message
        return BaiduDriveError(
            message=f"百度网盘 API 调用失败: {combined}",
            api_error_code=error_code,
            api_error_msg=error_msg,
            error_code="BAIDU_API_ERROR",
        )
