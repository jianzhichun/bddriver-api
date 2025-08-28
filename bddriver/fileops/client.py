"""
High-level file operations client for BaiduDriver SDK
Provides simplified file operation interfaces
"""

from typing import Any, Callable, Dict, List, Optional

from .manager import FileOperationsManager


class FileClient:
    """高级文件操作客户端

    提供简化的文件操作接口，封装常用操作模式
    """

    def __init__(self, access_token: str):
        """初始化文件客户端

        Args:
            access_token: 访问令牌
        """
        self.access_token = access_token
        self.manager = FileOperationsManager()

    def ls(self, path: str = "/") -> List[Dict[str, Any]]:
        """列出目录内容（简化接口）

        Args:
            path: 目录路径

        Returns:
            文件列表
        """
        return self.manager.list_files(self.access_token, path)

    def info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息（简化接口）"""
        return self.manager.get_file_info(self.access_token, file_path)

    def download(
        self, remote_path: str, local_path: str, progress_callback: Callable = None
    ) -> bool:
        """下载文件（简化接口）"""
        return self.manager.download_file(
            self.access_token, remote_path, local_path, progress_callback
        )

    def upload(
        self, local_path: str, remote_path: str, progress_callback: Callable = None
    ) -> bool:
        """上传文件（简化接口）"""
        return self.manager.upload_file(
            self.access_token, local_path, remote_path, progress_callback
        )

    def rm(self, file_path: str) -> bool:
        """删除文件（简化接口）"""
        return self.manager.delete_file(self.access_token, file_path)

    def cp(self, source: str, dest: str, new_name: str = None) -> bool:
        """复制文件（简化接口）"""
        return self.manager.copy_file(self.access_token, source, dest, new_name)

    def mv(self, source: str, dest: str, new_name: str = None) -> bool:
        """移动文件（简化接口）"""
        return self.manager.move_file(self.access_token, source, dest, new_name)

    def mkdir(self, folder_path: str) -> bool:
        """创建文件夹（简化接口）"""
        return self.manager.create_folder(self.access_token, folder_path)
