"""
Unit tests for WxPusher components
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver.utils.errors import WxPusherError
from bddriver.messaging.wxpusher.client import WxPusherClient


class TestWxPusherClient(unittest.TestCase):
    """测试 WxPusher 客户端"""

    def setUp(self):
        """设置测试环境"""
        self.client = WxPusherClient()

    def test_initialization(self):
        """测试客户端初始化"""
        self.assertIsNotNone(self.client.app_token)
        self.assertIsNotNone(self.client.base_url)
        self.assertIsNotNone(self.client.api_url)

    @patch("bddriver.messaging.wxpusher.client.requests.post")
    def test_send_message_success(self, mock_post):
        """测试成功发送消息"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "code": 1000,
            "msg": "发送成功",
            "data": {"messageId": "msg_12345", "status": "success"},
        }
        mock_post.return_value = mock_response

        result = self.client.send_message(
            user_id="test_uid", content="测试消息", summary="测试"
        )

        self.assertTrue(result["success"])
        mock_post.assert_called_once()

    @patch("bddriver.messaging.wxpusher.client.requests.post")
    def test_send_message_failure(self, mock_post):
        """测试发送消息失败"""
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "code": 1001,
            "msg": "发送失败",
            "data": None,
        }
        mock_post.return_value = mock_response

        result = self.client.send_message(
            user_id="test_uid", content="测试消息", summary="测试"
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["msg"], "发送失败")

    @patch("bddriver.messaging.wxpusher.client.requests.post")
    def test_send_message_http_error(self, mock_post):
        """测试HTTP错误"""
        # 模拟HTTP错误
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = self.client.send_message(
            user_id="test_uid", content="测试消息", summary="测试"
        )

        self.assertFalse(result["success"])
        self.assertIn("HTTP 500", result["msg"])

    @patch("bddriver.messaging.wxpusher.client.requests.post")
    def test_send_message_exception(self, mock_post):
        """测试发送消息异常"""
        # 模拟网络异常
        mock_post.side_effect = Exception("Network error")

        result = self.client.send_message(
            user_id="test_uid", content="测试消息", summary="测试"
        )

        self.assertFalse(result["success"])
        self.assertIn("发送消息异常", result["msg"])

    def test_send_device_auth_notification(self):
        """测试发送设备码授权通知"""
        with patch.object(self.client, 'send_message') as mock_send:
            mock_send.return_value = {"success": True}
            
            result = self.client.send_device_auth_notification(
                user_id="test_uid",
                user_code="123456",
                verification_url="https://example.com",
                expires_in=300
            )
            
            self.assertTrue(result["success"])
            mock_send.assert_called_once()

    def test_send_success_notification(self):
        """测试发送授权成功通知"""
        with patch.object(self.client, 'send_message') as mock_send:
            mock_send.return_value = {"success": True}
            
            result = self.client.send_success_notification(
                user_id="test_uid",
                access_token="test_token_12345"
            )
            
            self.assertTrue(result["success"])
            mock_send.assert_called_once()

    def test_send_success_notification_no_token(self):
        """测试发送授权成功通知（无token）"""
        with patch.object(self.client, 'send_message') as mock_send:
            mock_send.return_value = {"success": True}
            
            result = self.client.send_success_notification(
                user_id="test_uid"
            )
            
            self.assertTrue(result["success"])
            mock_send.assert_called_once()

    def test_validate_user_id(self):
        """测试用户ID验证"""
        # 测试有效用户ID
        result = self.client.send_message(
            user_id="valid_uid",
            content="test"
        )
        # 这里只是测试方法调用，实际验证在send_message中
        
        # 测试无效用户ID
        with self.assertRaises(ValueError):
            self.client.send_message(
                user_id=None,
                content="test"
            )


if __name__ == "__main__":
    unittest.main()
