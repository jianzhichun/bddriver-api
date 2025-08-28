"""
Unit tests for CLI interface
"""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver.cli import (
    cmd_device_auth,
    cmd_download,
    cmd_info,
    cmd_list,
    cmd_upload,
    format_file_list,
    format_file_size,
    load_token_from_args,
)
from bddriver.utils.errors import BaiduDriverError


class TestCLIUtils(unittest.TestCase):
    """测试 CLI 工具函数"""

    def test_format_file_size(self):
        """测试文件大小格式化"""
        self.assertEqual(format_file_size(0), "0 B")
        self.assertEqual(format_file_size(1024), "1.0 KB")
        self.assertEqual(format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(format_file_size(500), "500 B")
        self.assertEqual(format_file_size(1536), "1.5 KB")

    @patch("sys.stdout", new_callable=StringIO)
    def test_format_file_list_empty(self, mock_stdout):
        """测试空文件列表格式化"""
        format_file_list([])
        output = mock_stdout.getvalue()
        self.assertIn("目录为空", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_format_file_list_mixed(self, mock_stdout):
        """测试混合文件列表格式化"""
        files = [
            {"filename": "folder1", "is_dir": True, "mtime": 1234567890},
            {
                "filename": "file1.txt",
                "is_dir": False,
                "size": 1024,
                "mtime": 1234567890,
                "md5": "abcdef123456789",
            },
        ]

        format_file_list(files, detailed=True)
        output = mock_stdout.getvalue()

        self.assertIn("📁 folder1/", output)
        self.assertIn("📄 file1.txt", output)
        self.assertIn("1.0 KB", output)
        self.assertIn("MD5: abcdef12", output)
        self.assertIn("总计: 1 个文件夹, 1 个文件", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_format_file_list_simple(self, mock_stdout):
        """测试简单文件列表格式化"""
        files = [{"filename": "test.txt", "is_dir": False, "size": 2048}]

        format_file_list(files, detailed=False)
        output = mock_stdout.getvalue()

        self.assertIn("📄 test.txt (2.0 KB)", output)
        self.assertNotIn("MD5:", output)  # 简单模式不显示 MD5


class TestCLICommands(unittest.TestCase):
    """测试 CLI 命令"""

    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cmd_auth_success(self, mock_stdout, mock_driver_class):
        """测试成功的授权命令"""
        # 设置模拟
        mock_driver = MagicMock()
        mock_driver.request_device_access.return_value = {
            "access_token": "test_access_token_1234567890",
            "refresh_token": "test_refresh_token",
            "expires_at": 1234567890,
        }
        mock_driver_class.return_value = mock_driver

        # 创建模拟参数
        args = MagicMock()
        args.user_id = "test_user_id"
        args.path = "/test"
        args.description = "测试授权"
        args.requester = "测试者"
        args.timeout = 300
        args.save_token = None

        result = cmd_device_auth(args)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn("access_token", result)

        output = mock_stdout.getvalue()
        self.assertIn("授权成功", output)
        self.assertIn("test_access_", output)  # 脱敏后的 token

    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cmd_auth_with_save_token(self, mock_stdout, mock_driver_class):
        """测试保存 token 的授权命令"""
        mock_driver = MagicMock()
        mock_driver.request_device_access.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 1234567890,
        }
        mock_driver_class.return_value = mock_driver

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            token_file = f.name

        try:
            args = MagicMock()
            args.user_id = "test_user"
            args.path = "/"
            args.description = None
            args.requester = None
            args.timeout = 300
            args.save_token = token_file

            result = cmd_device_auth(args)

            # 验证 token 文件
            self.assertTrue(os.path.exists(token_file))
            with open(token_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            self.assertEqual(saved_data["access_token"], "test_access_token")
            self.assertEqual(saved_data["user_id"], "test_user")

            output = mock_stdout.getvalue()
            self.assertIn("Token 已保存到", output)

        finally:
            if os.path.exists(token_file):
                os.unlink(token_file)

    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stderr", new_callable=StringIO)
    def test_cmd_auth_failure(self, mock_stderr, mock_driver_class):
        """测试授权失败"""
        mock_driver = MagicMock()
        mock_driver.request_device_access.side_effect = BaiduDriverError("授权失败")
        mock_driver_class.return_value = mock_driver

        args = MagicMock()
        args.user_id = "test_user"
        args.path = "/"
        args.description = None
        args.requester = None
        args.timeout = 300
        args.save_token = None

        result = cmd_device_auth(args)

        self.assertIsNone(result)
        error_output = mock_stderr.getvalue()
        self.assertIn("授权失败", error_output)

    @patch("bddriver.cli.load_token_from_args")
    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cmd_list_success(self, mock_stdout, mock_driver_class, mock_load_token):
        """测试成功的列表命令"""
        # 设置模拟
        mock_load_token.return_value = "test_token"

        mock_driver = MagicMock()
        mock_driver.list_files.return_value = [
            {"filename": "test.txt", "is_dir": False, "size": 1024, "mtime": 1234567890}
        ]
        mock_driver_class.return_value = mock_driver

        args = MagicMock()
        args.path = "/test"
        args.limit = 100
        args.order = "time"
        args.sort = "desc"
        args.detailed = False

        cmd_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("获取文件列表成功", output)
        self.assertIn("📄 test.txt", output)

    @patch("bddriver.cli.load_token_from_args")
    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cmd_download_success(
        self, mock_stdout, mock_driver_class, mock_load_token
    ):
        """测试成功的下载命令"""
        mock_load_token.return_value = "test_token"

        mock_driver = MagicMock()
        mock_driver.download_file.return_value = True
        mock_driver_class.return_value = mock_driver

        args = MagicMock()
        args.remote_path = "/remote/test.txt"
        args.local_path = "/local/test.txt"
        args.progress = False

        cmd_download(args)

        output = mock_stdout.getvalue()
        self.assertIn("下载完成", output)

    @patch("bddriver.cli.load_token_from_args")
    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stdout", new_callable=StringIO)
    @patch("os.path.exists")
    def test_cmd_upload_success(
        self, mock_exists, mock_stdout, mock_driver_class, mock_load_token
    ):
        """测试成功的上传命令"""
        mock_load_token.return_value = "test_token"
        mock_exists.return_value = True

        mock_driver = MagicMock()
        mock_driver.upload_file.return_value = True
        mock_driver_class.return_value = mock_driver

        args = MagicMock()
        args.local_path = "/local/test.txt"
        args.remote_path = "/remote/test.txt"
        args.progress = False

        cmd_upload(args)

        output = mock_stdout.getvalue()
        self.assertIn("上传完成", output)

    @patch("bddriver.cli.BaiduDriver")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cmd_info(self, mock_stdout, mock_driver_class):
        """测试信息命令"""
        mock_driver = MagicMock()
        mock_driver.get_config_info.return_value = {
            "general": {"timeout": 300, "debug": False},
            "baidu": {"app_id": "test_app_id", "secret_key": "***secret***"},
        }
        mock_driver_class.return_value = mock_driver

        args = MagicMock()

        cmd_info(args)

        output = mock_stdout.getvalue()
        self.assertIn("BaiduDriver CLI", output)
        self.assertIn("配置信息", output)
        self.assertIn("general", output)
        self.assertIn("baidu", output)


class TestTokenLoading(unittest.TestCase):
    """测试 token 加载"""

    def test_load_token_from_args_direct(self):
        """测试从参数直接加载 token"""
        args = MagicMock()
        args.token = "direct_token"

        token = load_token_from_args(args)
        self.assertEqual(token, "direct_token")

    def test_load_token_from_file(self):
        """测试从文件加载 token"""
        token_data = {"access_token": "file_token", "refresh_token": "refresh_token"}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(token_data, f)
            token_file = f.name

        try:
            args = MagicMock()
            args.token = None
            args.token_file = token_file

            token = load_token_from_args(args)
            self.assertEqual(token, "file_token")

        finally:
            os.unlink(token_file)

    def test_load_token_from_default_file(self):
        """测试从默认文件加载 token"""
        token_data = {"access_token": "default_token"}

        default_file = "bddriver_token.json"

        # 确保默认文件不存在
        if os.path.exists(default_file):
            os.unlink(default_file)

        try:
            with open(default_file, "w", encoding="utf-8") as f:
                json.dump(token_data, f)

            args = MagicMock()
            args.token = None
            args.token_file = None

            token = load_token_from_args(args)
            self.assertEqual(token, "default_token")

        finally:
            if os.path.exists(default_file):
                os.unlink(default_file)

    @patch("sys.stderr", new_callable=StringIO)
    def test_load_token_not_found(self, mock_stderr):
        """测试找不到 token"""
        args = MagicMock()
        args.token = None
        args.token_file = None

        # 确保默认文件不存在
        default_file = "bddriver_token.json"
        if os.path.exists(default_file):
            os.unlink(default_file)

        token = load_token_from_args(args)
        self.assertIsNone(token)

        error_output = mock_stderr.getvalue()
        self.assertIn("未找到访问令牌", error_output)


if __name__ == "__main__":
    unittest.main()
