"""
Unit tests for configuration system
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver.config.builtin import BaiduConfig, BuiltinConfig, WxPusherConfig
from bddriver.utils.errors import ConfigurationError


class TestBaiduConfig(unittest.TestCase):
    """测试百度网盘配置"""

    def test_baidu_config_creation(self):
        """测试创建百度配置"""
        config = BaiduConfig()
        self.assertIsNotNone(config.app_id)
        self.assertIsNotNone(config.app_key)
        self.assertIsNotNone(config.secret_key)
        self.assertEqual(config.client_id, config.app_id)
        self.assertEqual(config.client_secret, config.app_key)

    def test_baidu_config_validation(self):
        """测试百度配置验证"""
        config = BaiduConfig()
        # 测试属性存在
        self.assertTrue(hasattr(config, "app_id"))
        self.assertTrue(hasattr(config, "app_key"))
        self.assertTrue(hasattr(config, "secret_key"))

        # 测试默认值不为空
        self.assertNotEqual(config.app_id, "")
        self.assertNotEqual(config.app_key, "")
        self.assertNotEqual(config.secret_key, "")


class TestWxPusherConfig(unittest.TestCase):
    """测试 WxPusher 配置"""

    def test_wxpusher_config_creation(self):
        """测试创建 WxPusher 配置"""
        config = WxPusherConfig()
        self.assertIsNotNone(config.app_token)
        self.assertEqual(config.base_url, "https://wxpusher.zjiecode.com/api")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)

    def test_wxpusher_config_validation(self):
        """测试 WxPusher 配置验证"""
        config = WxPusherConfig()
        # 测试属性存在
        self.assertTrue(hasattr(config, "app_token"))
        self.assertTrue(hasattr(config, "base_url"))

        # 测试默认值
        self.assertNotEqual(config.app_token, "")
        self.assertTrue(config.base_url.startswith("http"))


class TestBuiltinConfig(unittest.TestCase):
    """测试内置配置管理器"""

    def setUp(self):
        """设置测试环境"""
        self.config = BuiltinConfig()

    def test_get_general_config(self):
        """测试获取通用配置"""
        from bddriver.config.builtin import GeneralConfig

        general_config = self.config.get_general_config()
        self.assertIsInstance(general_config, GeneralConfig)
        self.assertEqual(general_config.request_timeout, 30)
        self.assertEqual(general_config.max_retries, 3)

    def test_get_baidu_config(self):
        """测试获取百度配置"""
        baidu_config = self.config.get_baidu_config()
        self.assertIsInstance(baidu_config, BaiduConfig)

    def test_get_wxpusher_config(self):
        """测试获取 WxPusher 配置"""
        wxpusher_config = self.config.get_wxpusher_config()
        self.assertIsInstance(wxpusher_config, WxPusherConfig)

    def test_get_all_config(self):
        """测试获取所有配置"""
        all_config = self.config.get_all_config()
        self.assertIsInstance(all_config, dict)
        expected_modules = ["general", "baidu", "wxpusher"]
        for module in expected_modules:
            self.assertIn(module, all_config)

    def test_validate_all(self):
        """测试验证所有配置"""
        # 应该不抛出异常
        result = self.config.validate_config()
        self.assertTrue(result)

    def test_environment_override(self):
        """测试环境变量覆盖（当前版本为内置配置，不支持环境变量覆盖）"""
        config = BuiltinConfig()
        baidu_config = config.get_baidu_config()

        # 当前版本使用内置配置，不支持环境变量覆盖
        # 这里测试默认值
        self.assertEqual(baidu_config.app_id, "119872432")
        self.assertIsNotNone(baidu_config.secret_key)


if __name__ == "__main__":
    unittest.main()
