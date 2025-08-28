"""
Test configuration and fixtures for BaiduDriver tests
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return project_root


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_baidu_driver():
    """模拟 BaiduDriver 实例"""
    mock_driver = MagicMock()
    mock_driver.request_device_access.return_value = {
        "access_token": "test_access_token_1234567890",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
        "scope": "basic,netdisk",
        "token_type": "Bearer"
    }
    mock_driver.list_files.return_value = [
        {"filename": "test.txt", "is_dir": False, "size": 1024}
    ]
    mock_driver.download_file.return_value = True
    mock_driver.upload_file.return_value = True
    return mock_driver


@pytest.fixture
def mock_wxpusher_client():
    """模拟 WxPusher 客户端"""
    mock_client = MagicMock()
    mock_client.send_auth_request.return_value = True
    mock_client.send_message.return_value = True
    return mock_client


@pytest.fixture
def sample_file_info():
    """示例文件信息"""
    return {
        "filename": "test.txt",
        "is_dir": False,
        "size": 1024,
        "mtime": 1234567890,
        "md5": "abcdef123456789",
        "path": "/test.txt"
    }


@pytest.fixture
def sample_folder_info():
    """示例文件夹信息"""
    return {
        "filename": "test_folder",
        "is_dir": True,
        "mtime": 1234567890,
        "path": "/test_folder"
    }


@pytest.fixture
def mock_args():
    """模拟命令行参数"""
    args = MagicMock()
    args.user_id = "test_user"
    args.path = "/test"
    args.description = "测试授权"
    args.requester = "测试者"
    args.timeout = 300
    args.save_token = None
    args.token = None
    args.token_file = None
    return args


@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境"""
    # 设置测试环境变量
    os.environ.setdefault('BDDRIVER_LOG_LEVEL', 'WARNING')
    os.environ.setdefault('BDDRIVER_LOG_FORMAT', 'simple')
    
    # 清理后恢复
    yield
    
    # 清理测试环境
    for key in ['BDDRIVER_LOG_LEVEL', 'BDDRIVER_LOG_FORMAT']:
        if key in os.environ:
            del os.environ[key]
