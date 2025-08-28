"""
Unit tests for utility modules
"""

import json
import logging
import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver.utils.errors import (
    AuthError,
    AuthTimeoutError,
    BaiduDriveError,
    BaiduDriverError,
    FileOperationError,
    NetworkError,
    WxPusherError,
    create_error_from_api_response,
)
from bddriver.utils.logger import (
    StructuredFormatter,
    get_logger,
    log_error,
    log_operation_end,
    log_operation_start,
)


class TestErrors(unittest.TestCase):
    """测试错误处理模块"""

    def test_base_error(self):
        """测试基础错误类"""
        error = BaiduDriverError("测试错误", error_code="TEST_ERROR")
        self.assertEqual(
            str(error), "[TEST_ERROR] 测试错误"
        )  # 实际实现包含错误代码前缀
        self.assertEqual(error.error_code, "TEST_ERROR")

    def test_error_hierarchy(self):
        """测试错误继承层次"""
        # 测试继承关系
        self.assertTrue(issubclass(NetworkError, BaiduDriverError))
        self.assertTrue(issubclass(AuthError, BaiduDriverError))
        self.assertTrue(issubclass(WxPusherError, BaiduDriverError))
        self.assertTrue(issubclass(BaiduDriveError, BaiduDriverError))
        self.assertTrue(issubclass(FileOperationError, BaiduDriverError))
        self.assertTrue(issubclass(AuthTimeoutError, AuthError))

    def test_create_error_from_api_response(self):
        """测试从 API 响应创建错误"""
        # 测试错误响应
        error_response = {"errno": -1, "errmsg": "invalid token"}
        error = create_error_from_api_response("测试操作", error_response)
        self.assertIsInstance(error, BaiduDriverError)
        self.assertIn(
            "系统错误", str(error)
        )  # 根据 ERROR_CODE_MAPPING，-1 对应 "系统错误"

        # 测试无错误码的情况
        no_code_response = {"errmsg": "some message"}
        error = create_error_from_api_response("测试操作", no_code_response)
        self.assertIsInstance(error, BaiduDriverError)
        self.assertIn("API 调用失败", str(error))

    def test_network_error(self):
        """测试网络错误"""
        error = NetworkError("连接失败", status_code=500)
        self.assertEqual(error.status_code, 500)

    def test_auth_timeout_error(self):
        """测试授权超时错误"""
        error = AuthTimeoutError("授权超时", timeout=300)
        self.assertEqual(error.timeout, 300)


class TestLogger(unittest.TestCase):
    """测试日志模块"""

    def setUp(self):
        """设置测试环境"""
        # 创建内存中的日志处理器
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.formatter = StructuredFormatter()
        self.handler.setFormatter(self.formatter)

        # 获取测试日志器
        self.logger = get_logger("test")
        self.logger.handlers.clear()
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def test_structured_formatter(self):
        """测试结构化格式器"""
        self.logger.info("测试消息", extra={"request_id": "test_123"})

        log_output = self.log_stream.getvalue()
        self.assertIn("测试消息", log_output)
        self.assertIn("test_123", log_output)

        # 验证是否为有效的 JSON
        lines = log_output.strip().split("\n")
        for line in lines:
            if line:
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    self.fail(f"日志输出不是有效的 JSON: {line}")

    def test_sensitive_data_sanitization(self):
        """测试敏感数据脱敏"""
        sensitive_data = {
            "access_token": "very_secret_token_12345",
            "password": "super_secret_password",
            "api_key": "secret_api_key_abcdef",
            "normal_field": "normal_value",
        }

        self.logger.info("包含敏感数据", extra=sensitive_data)

        log_output = self.log_stream.getvalue()

        # 验证敏感数据被脱敏
        self.assertNotIn("very_secret_token_12345", log_output)
        self.assertNotIn("super_secret_password", log_output)
        self.assertNotIn("secret_api_key_abcdef", log_output)

        # 验证正常字段未被脱敏
        self.assertIn("normal_value", log_output)

        # 验证脱敏标记存在
        self.assertIn("***", log_output)

    def test_log_operation_functions(self):
        """测试操作日志函数"""
        logger = get_logger("test_ops")

        # 测试操作开始日志
        log_operation_start(logger, "测试操作", {"param1": "value1"})

        # 测试操作结束日志
        log_operation_end(logger, "测试操作", {"result": "success"})

        # 测试错误日志
        test_error = BaiduDriverError("测试错误")
        log_error(logger, test_error, {"context": "test"})


if __name__ == "__main__":
    unittest.main()
