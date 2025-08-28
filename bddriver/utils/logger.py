"""
Logging system for BaiduDriver SDK
Based on TIP 7: Error Handling and Logging System
Simple, zero-configuration logging with structured output
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器，输出 JSON 格式日志"""

    def format(self, record: logging.LogRecord) -> str:
        # 基础日志信息
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # 合并 extra 字段（除了标准字段）
        standard_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
        }
        for key, value in record.__dict__.items():
            if key not in standard_fields and key not in log_entry:
                log_entry[key] = value

        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加以 extra_data 包裹的自定义字段（兼容库内日志辅助函数）
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # 敏感信息脱敏
        self._sanitize_sensitive_data(log_entry)

        return json.dumps(log_entry, ensure_ascii=False, separators=(",", ":"))

    def _sanitize_sensitive_data(self, log_entry: Dict[str, Any]) -> None:
        """敏感信息脱敏处理"""
        sensitive_keys = [
            "token",
            "access_token",
            "refresh_token",
            "app_token",
            "client_secret",
            "secret_key",
            "auth_token",
            "password",
            "app_key",
            "sign_key",
            "api_key",
        ]

        def _mask_value(value: str) -> str:
            if len(value) <= 6:
                return "*" * len(value)
            return value[:3] + "*" * (len(value) - 6) + value[-3:]

        def _sanitize_dict(d: Dict[str, Any]) -> None:
            for key, value in d.items():
                if key.lower() in sensitive_keys and isinstance(value, str):
                    d[key] = _mask_value(value)
                elif isinstance(value, dict):
                    _sanitize_dict(value)
                elif isinstance(value, str) and any(
                    sk in key.lower() for sk in sensitive_keys
                ):
                    d[key] = _mask_value(value)

        _sanitize_dict(log_entry)


class BaiduDriverLogger:
    """BaiduDriver SDK 日志管理器"""

    def __init__(self):
        self.logger = logging.getLogger("bddriver")
        self._setup_logger()

    def _setup_logger(self) -> None:
        """设置日志器配置"""
        if self.logger.handlers:
            return  # 避免重复配置

        # 设置日志级别 - 默认只显示WARNING及以上，减少噪音
        log_level = os.getenv("BDDRIVER_LOG_LEVEL", "WARNING").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.WARNING))

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_console_formatter())
        self.logger.addHandler(console_handler)

        # 文件处理器 (可选)
        if os.getenv("BDDRIVER_LOG_FILE"):
            file_handler = self._create_file_handler()
            if file_handler:
                file_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(file_handler)

        # 防止日志传播到根日志器
        self.logger.propagate = False

    def _get_console_formatter(self) -> logging.Formatter:
        """获取控制台格式化器"""
        if os.getenv("BDDRIVER_LOG_FORMAT") == "json":
            return StructuredFormatter()
        else:
            # 简洁的控制台格式
            return logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

    def _create_file_handler(self) -> Optional[logging.FileHandler]:
        """创建文件处理器"""
        try:
            log_file = os.getenv("BDDRIVER_LOG_FILE")
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            handler = logging.FileHandler(log_file, encoding="utf-8")
            return handler
        except Exception as e:
            self.logger.error(f"创建日志文件处理器失败: {e}")
            return None

    def get_logger(self, name: str = None) -> logging.Logger:
        """获取指定名称的日志器"""
        if name:
            return logging.getLogger(f"bddriver.{name}")
        return self.logger


# 全局日志管理器实例
_logger_manager = BaiduDriverLogger()


def get_logger(name: str = None) -> logging.Logger:
    """获取日志器的便捷函数"""
    return _logger_manager.get_logger(name)


def log_api_call(
    logger: logging.Logger,
    api_name: str,
    method: str,
    url: str,
    status_code: int = None,
    duration: float = None,
    **kwargs,
) -> None:
    """记录 API 调用日志"""
    extra_data = {
        "api_name": api_name,
        "method": method,
        "url": url,
        "type": "api_call",
    }

    if status_code is not None:
        extra_data["status_code"] = status_code
    if duration is not None:
        extra_data["duration_ms"] = round(duration * 1000, 2)

    extra_data.update(kwargs)

    # 根据状态码确定日志级别
    try:
        status_int = int(status_code) if status_code is not None else None
    except Exception:
        status_int = None
    if status_int is not None and status_int >= 400:
        level = logging.ERROR if status_code >= 500 else logging.WARNING
    else:
        level = logging.INFO

    logger.log(level, f"{api_name} API调用", extra={"extra_data": extra_data})


def log_operation_start(
    logger: logging.Logger,
    operation: str,
    details: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """记录操作开始日志"""
    extra_data = {
        "operation": operation,
        "type": "operation_start",
        "status": "started",
    }
    if isinstance(details, dict):
        extra_data.update(details)
    extra_data.update(kwargs)

    logger.info(f"开始执行: {operation}", extra={"extra_data": extra_data})


def log_operation_end(
    logger: logging.Logger,
    operation: str,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    duration: float = None,
    **kwargs,
) -> None:
    """记录操作结束日志"""
    extra_data = {
        "operation": operation,
        "type": "operation_end",
        "status": "completed" if success else "failed",
    }

    if duration is not None:
        extra_data["duration_ms"] = round(duration * 1000, 2)

    if isinstance(details, dict):
        extra_data.update(details)
    extra_data.update(kwargs)

    level = logging.INFO if success else logging.ERROR
    status_msg = "完成" if success else "失败"

    logger.log(
        level, f"操作{status_msg}: {operation}", extra={"extra_data": extra_data}
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    details: Optional[Dict[str, Any]] = None,
    operation: str = None,
    **kwargs,
) -> None:
    """记录错误日志"""
    from .errors import BaiduDriverError

    extra_data = {"error_type": error.__class__.__name__, "type": "error"}

    if operation:
        extra_data["operation"] = operation

    # 如果是自定义异常，添加详细信息
    if isinstance(error, BaiduDriverError):
        extra_data.update(error.to_dict())

    if isinstance(details, dict):
        extra_data.update(details)
    extra_data.update(kwargs)

    logger.error(
        f"发生错误: {str(error)}", exc_info=True, extra={"extra_data": extra_data}
    )


# 预配置的日志器
def get_auth_logger() -> logging.Logger:
    """获取授权模块日志器"""
    return get_logger("auth")


def get_wxpusher_logger() -> logging.Logger:
    """获取 WxPusher 模块日志器"""
    return get_logger("wxpusher")


def get_fileops_logger() -> logging.Logger:
    """获取文件操作模块日志器"""
    return get_logger("fileops")
