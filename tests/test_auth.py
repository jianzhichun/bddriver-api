"""
Unit tests for authentication components
"""

import os
import sys
import threading
import time
import unittest
from http.server import HTTPServer
from unittest.mock import MagicMock, Mock, patch

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)


from bddriver.auth.manager import AuthManager
from bddriver.auth.oauth import OAuthManager
from bddriver.config import config
from bddriver.utils.errors import AuthError, AuthTimeoutError, BaiduDriveError


class TestOAuthManager(unittest.TestCase):
    """测试 OAuth 管理器"""

    def setUp(self):
        """设置测试环境"""
        self.oauth_manager = OAuthManager()

    def test_oauth_manager_initialization(self):
        """测试 OAuth 管理器初始化"""
        self.assertIsNotNone(self.oauth_manager.config)
        self.assertIsNotNone(self.oauth_manager.logger)

    def test_get_auth_url(self):
        """测试获取授权URL"""
        redirect_uri = "http://localhost:8080/callback"
        auth_url = self.oauth_manager.get_auth_url(redirect_uri)

        self.assertIn("https://openapi.baidu.com/oauth/2.0/authorize", auth_url)
        self.assertIn("client_id=", auth_url)
        self.assertIn("redirect_uri=", auth_url)
        self.assertIn("scope=", auth_url)

    @patch("bddriver.auth.oauth.requests.post")
    def test_exchange_code_for_token_success(self, mock_post):
        """测试成功交换授权码"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.oauth_manager.exchange_code_for_token(
            "test_code", "http://localhost:8080/callback"
        )

        self.assertEqual(result["access_token"], "test_access_token")
        self.assertEqual(result["refresh_token"], "test_refresh_token")
        self.assertEqual(result["expires_in"], 3600)

    @patch("bddriver.auth.oauth.requests.post")
    def test_exchange_code_for_token_failure(self, mock_post):
        """测试交换授权码失败"""
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code",
        }
        mock_post.return_value = mock_response

        with self.assertRaises(BaiduDriveError):
            self.oauth_manager.exchange_code_for_token(
                "invalid_code", "http://localhost:8080/callback"
            )

    @patch("bddriver.auth.oauth.requests.post")
    def test_refresh_token_success(self, mock_post):
        """测试成功刷新令牌"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.oauth_manager.refresh_token("test_refresh_token")

        self.assertEqual(result["access_token"], "new_access_token")
        self.assertEqual(result["refresh_token"], "new_refresh_token")


class TestAuthManager(unittest.TestCase):
    """测试授权管理器"""

    def setUp(self):
        """设置测试环境"""
        self.auth_manager = AuthManager()

    @patch("bddriver.auth.manager.WxPusherClient")
    @patch("bddriver.auth.manager.OAuthManager")
    def test_request_access_success(self, mock_oauth, mock_wxpusher):
        """测试成功的授权请求"""
        # 设置模拟对象
        mock_wxpusher_instance = MagicMock()
        mock_wxpusher_instance.send_auth_request.return_value = True
        mock_wxpusher.return_value = mock_wxpusher_instance

        mock_oauth_instance = MagicMock()
        mock_oauth_instance.get_auth_url.return_value = "https://auth.url"
        mock_oauth_instance.exchange_code_for_token.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_in": 3600,
        }
        mock_oauth.return_value = mock_oauth_instance

        # 执行测试
        result = self.auth_manager.request_access(
            target_user_id="test_user",
            file_path="/test",
            description="测试授权",
            timeout=30,
        )

        # 验证结果
        self.assertIn("access_token", result)
        self.assertIn("request_id", result)
        self.assertEqual(result["access_token"], "test_token")

    def test_get_request_status(self):
        """测试获取请求状态"""
        # 设置模拟状态
        request_id = "test_request_id"
        self.auth_manager._active_requests[request_id] = {
            "status": "completed",
            "target_user_id": "test_user",
        }

        status = self.auth_manager.get_request_status(request_id)
        self.assertEqual(status["status"], "completed")

    def test_cancel_request(self):
        """测试取消请求"""
        request_id = "test_request_id"
        self.auth_manager._active_requests[request_id] = {
            "status": "pending",
            "target_user_id": "test_user",
        }

        result = self.auth_manager.cancel_request(request_id)
        self.assertTrue(result)
        self.assertEqual(
            self.auth_manager._active_requests[request_id]["status"], "cancelled"
        )


if __name__ == "__main__":
    unittest.main()
