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
from bddriver.wxpusher.client import WxPusherClient
from bddriver.wxpusher.templates import MessageTemplates


class TestWxPusherClient(unittest.TestCase):
    """测试 WxPusher 客户端"""

    def setUp(self):
        """设置测试环境"""
        self.client = WxPusherClient()

    def test_initialization(self):
        """测试客户端初始化"""
        self.assertIsNotNone(self.client.config)
        self.assertIsNotNone(self.client.session)
        self.assertIsNotNone(self.client.logger)

    @patch("bddriver.wxpusher.client.requests.Session.post")
    def test_send_message_success(self, mock_post):
        """测试成功发送消息"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "code": 1000,
            "msg": "发送成功",
            "data": [{"messageId": "msg_12345", "status": "success"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.send_message(
            uids=["test_uid"], content="测试消息", summary="测试"
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("bddriver.wxpusher.client.requests.Session.post")
    def test_send_message_failure(self, mock_post):
        """测试发送消息失败"""
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "code": 1001,
            "msg": "发送失败",
            "data": None,
        }
        mock_post.return_value = mock_response

        with self.assertRaises(WxPusherError):
            self.client.send_message(
                uids=["test_uid"], content="测试消息", summary="测试"
            )

    @patch("bddriver.wxpusher.client.requests.Session.post")
    def test_send_message_with_retry(self, mock_post):
        """测试重试机制"""
        # 第一次失败，第二次成功
        mock_response_fail = MagicMock()
        mock_response_fail.json.return_value = {
            "success": False,
            "code": 1002,
            "msg": "临时错误",
        }

        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {
            "success": True,
            "code": 1000,
            "msg": "发送成功",
            "data": [{"messageId": "msg_12345", "status": "success"}],
        }
        mock_response_success.raise_for_status.return_value = None

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        result = self.client.send_message(
            uids=["test_uid"], content="测试消息", summary="测试"
        )

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)

    @patch("bddriver.wxpusher.client.requests.Session.post")
    def test_send_auth_request(self, mock_post):
        """测试发送授权请求"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "code": 1000,
            "msg": "发送成功",
            "data": [{"messageId": "msg_12345", "status": "success"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.send_auth_request(
            user_id="test_user",
            auth_url="https://auth.url",
            file_path="/test",
            description="测试授权",
            requester="测试者",
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

        # 验证调用参数
        call_args = mock_post.call_args
        self.assertIn("json", call_args.kwargs)
        json_data = call_args.kwargs["json"]
        self.assertIn("content", json_data)
        self.assertIn("授权请求", json_data["content"])

    @patch("bddriver.wxpusher.client.requests.Session.post")
    def test_send_auth_success(self, mock_post):
        """测试发送授权成功通知"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "code": 1000,
            "msg": "发送成功",
            "data": [{"messageId": "msg_12345", "status": "success"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.send_auth_success(
            user_id="test_user", file_path="/test", expires_at=1234567890
        )

        self.assertTrue(result)

    @patch("bddriver.wxpusher.client.requests.Session.post")
    def test_send_auth_failure(self, mock_post):
        """测试发送授权失败通知"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "code": 1000,
            "msg": "发送成功",
            "data": [{"messageId": "msg_12345", "status": "success"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.send_auth_failure(
            user_id="test_user", file_path="/test", error="超时错误"
        )

        self.assertTrue(result)


class TestMessageTemplates(unittest.TestCase):
    """测试消息模板"""

    def test_auth_request_template(self):
        """测试授权请求模板"""
        template = MessageTemplates.auth_request(
            auth_url="https://auth.url",
            file_path="/test",
            description="测试授权",
            requester="测试者",
        )

        self.assertIn("授权请求", template)
        self.assertIn("https://auth.url", template)
        self.assertIn("/test", template)
        self.assertIn("测试授权", template)
        self.assertIn("测试者", template)

    def test_auth_success_template(self):
        """测试授权成功模板"""
        template = MessageTemplates.auth_success(
            file_path="/test", expires_at=1234567890
        )

        self.assertIn("授权成功", template)
        self.assertIn("/test", template)
        self.assertIn("2009", template)  # 时间戳对应的年份

    def test_auth_failure_template(self):
        """测试授权失败模板"""
        template = MessageTemplates.auth_failure(file_path="/test", error="超时错误")

        self.assertIn("授权失败", template)
        self.assertIn("/test", template)
        self.assertIn("超时错误", template)

    def test_progress_update_template(self):
        """测试进度更新模板"""
        template = MessageTemplates.progress_update(
            operation="下载文件", progress=50, details="已完成 5/10 个文件"
        )

        self.assertIn("进度更新", template)
        self.assertIn("下载文件", template)
        self.assertIn("50%", template)
        self.assertIn("已完成 5/10 个文件", template)

    def test_operation_complete_template(self):
        """测试操作完成模板"""
        template = MessageTemplates.operation_complete(
            operation="文件同步", summary="成功同步 10 个文件"
        )

        self.assertIn("操作完成", template)
        self.assertIn("文件同步", template)
        self.assertIn("成功同步 10 个文件", template)

    def test_template_html_validation(self):
        """测试模板 HTML 有效性"""
        templates = [
            MessageTemplates.auth_request("https://test.url", "/test"),
            MessageTemplates.auth_success("/test", 1234567890),
            MessageTemplates.auth_failure("/test", "错误"),
            MessageTemplates.progress_update("操作", 50),
            MessageTemplates.operation_complete("操作", "完成"),
        ]

        for template in templates:
            # 验证基本 HTML 结构
            self.assertIn("<html", template)
            self.assertIn("</html>", template)
            self.assertIn("<head>", template)
            self.assertIn("</head>", template)
            self.assertIn("<body>", template)
            self.assertIn("</body>", template)

            # 验证响应式设计
            self.assertIn("viewport", template)
            self.assertIn("mobile", template)


if __name__ == "__main__":
    unittest.main()
