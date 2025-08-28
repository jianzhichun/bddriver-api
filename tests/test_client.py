"""
Unit tests for BaiduDriver main client
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver.client import BaiduDriver
from bddriver.utils.errors import AuthTimeoutError, BaiduDriverError, FileOperationError


class TestBaiduDriver(unittest.TestCase):
    """测试 BaiduDriver 主客户端"""

    def setUp(self):
        """设置测试环境"""
        self.driver = BaiduDriver()

    def test_initialization(self):
        """测试客户端初始化"""
        self.assertIsNotNone(self.driver.auth_manager)
        self.assertIsNotNone(self.driver.file_manager)
        self.assertIsNotNone(self.driver.general_config)
        self.assertIsInstance(self.driver._current_tokens, dict)

    @patch("bddriver.client.AuthManager")
    def test_request_access_success(self, mock_auth_manager):
        """测试成功的授权请求"""
        # 设置模拟授权管理器
        mock_auth_instance = MagicMock()
        mock_auth_instance.request_access.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_in": 3600,
            "expires_at": time.time() + 3600,
            "request_id": "test_request_id",
            "target_user_id": "test_user",
            "authorized_path": "/test",
        }
        mock_auth_manager.return_value = mock_auth_instance

        # 重新创建客户端以使用模拟
        driver = BaiduDriver()

        result = driver.request_access(
            target_user_id="test_user", file_path="/test", description="测试授权"
        )

        # 验证结果
        self.assertEqual(result["access_token"], "test_token")
        self.assertEqual(result["request_id"], "test_request_id")
        self.assertIn("test_request_id", driver._current_tokens)

    @patch("bddriver.client.AuthManager")
    def test_request_access_failure(self, mock_auth_manager):
        """测试授权请求失败"""
        mock_auth_instance = MagicMock()
        mock_auth_instance.request_access.side_effect = AuthTimeoutError("授权超时")
        mock_auth_manager.return_value = mock_auth_instance

        driver = BaiduDriver()

        with self.assertRaises(AuthTimeoutError):
            driver.request_access("test_user", "/test")

    def test_wait_for_auth(self):
        """测试等待授权"""
        # 设置模拟令牌
        test_token = {
            "access_token": "test_token",
            "request_id": "test_request_id",
            "request_time": time.time(),
        }
        self.driver._current_tokens["test_request_id"] = test_token

        result = self.driver.wait_for_auth("test_request_id")
        self.assertEqual(result["access_token"], "test_token")

    def test_wait_for_auth_no_request(self):
        """测试等待不存在的授权请求"""
        with self.assertRaises(BaiduDriverError):
            self.driver.wait_for_auth("nonexistent_id")

    @patch("bddriver.client.AuthManager")
    def test_refresh_access_token(self, mock_auth_manager):
        """测试刷新访问令牌"""
        mock_auth_instance = MagicMock()
        mock_auth_instance.refresh_token.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
        }
        mock_auth_manager.return_value = mock_auth_instance

        driver = BaiduDriver()

        result = driver.refresh_access_token("test_refresh_token")
        self.assertEqual(result["access_token"], "new_token")

    @patch("bddriver.client.FileOperationsManager")
    def test_list_files(self, mock_file_manager):
        """测试列出文件"""
        mock_file_instance = MagicMock()
        mock_file_instance.list_files.return_value = [
            {
                "filename": "test.txt",
                "path": "/test.txt",
                "size": 1024,
                "is_dir": False,
                "mtime": 1234567890,
            }
        ]
        mock_file_manager.return_value = mock_file_instance

        driver = BaiduDriver()

        files = driver.list_files("test_token", "/test")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["filename"], "test.txt")

    @patch("bddriver.client.FileOperationsManager")
    def test_download_file(self, mock_file_manager):
        """测试下载文件"""
        mock_file_instance = MagicMock()
        mock_file_instance.download_file.return_value = True
        mock_file_manager.return_value = mock_file_instance

        driver = BaiduDriver()

        success = driver.download_file(
            "test_token", "/remote/test.txt", "/local/test.txt"
        )
        self.assertTrue(success)

    @patch("bddriver.client.FileOperationsManager")
    def test_upload_file(self, mock_file_manager):
        """测试上传文件"""
        mock_file_instance = MagicMock()
        mock_file_instance.upload_file.return_value = True
        mock_file_manager.return_value = mock_file_instance

        driver = BaiduDriver()

        success = driver.upload_file(
            "test_token", "/local/test.txt", "/remote/test.txt"
        )
        self.assertTrue(success)

    def test_is_token_expired(self):
        """测试令牌过期检查"""
        # 未过期令牌
        valid_token = {"expires_at": time.time() + 3600}  # 1小时后过期
        self.assertFalse(self.driver.is_token_expired(valid_token))

        # 过期令牌
        expired_token = {"expires_at": time.time() - 3600}  # 1小时前过期
        self.assertTrue(self.driver.is_token_expired(expired_token))

        # 没有过期时间的令牌
        no_expiry_token = {}
        self.assertFalse(self.driver.is_token_expired(no_expiry_token))

    def test_get_version(self):
        """测试获取版本"""
        version = self.driver.get_version()
        self.assertIsInstance(version, str)
        self.assertRegex(version, r"\d+\.\d+\.\d+")

    def test_get_config_info(self):
        """测试获取配置信息"""
        config_info = self.driver.get_config_info()
        self.assertIsInstance(config_info, dict)
        # 验证敏感信息被脱敏
        for module, module_config in config_info.items():
            for key, value in module_config.items():
                if any(
                    sensitive in key.lower() for sensitive in ["token", "secret", "key"]
                ):
                    self.assertIn("*", str(value))

    def test_context_manager(self):
        """测试上下文管理器"""
        with self.driver as d:
            self.assertEqual(d, self.driver)

        # cleanup 应该被调用
        self.assertEqual(len(self.driver._current_tokens), 0)

    @patch("bddriver.client.AuthManager")
    def test_auth_session_context_manager(self, mock_auth_manager):
        """测试授权会话上下文管理器"""
        mock_auth_instance = MagicMock()
        mock_auth_instance.request_access.return_value = {
            "access_token": "test_token",
            "request_id": "test_request_id",
        }
        mock_auth_manager.return_value = mock_auth_instance

        driver = BaiduDriver()

        with driver.auth_session("test_user", "/test") as session:
            self.assertEqual(session["access_token"], "test_token")


if __name__ == "__main__":
    unittest.main()
