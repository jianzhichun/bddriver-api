"""
File operations manager for BaiduDriver SDK
Based on TIP 4: File Operations Wrapper
High-level interface for Baidu NetDisk file operations
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import requests

# Import Baidu NetDisk SDK from internal package
try:
    # Try to import from internal package
    import os
    import sys

    # Get the path to the internal package
    current_dir = os.path.dirname(__file__)
    vendor_path = os.path.join(current_dir, "..", "_vendor", "baidu-netdisk-sdk")

    if os.path.exists(vendor_path):
        sys.path.insert(0, vendor_path)
        import openapi_client  # Import the actual module
        from openapi_client.api import (
            fileinfo_api,
            filemanager_api,
            fileupload_api,
            multimediafile_api,
        )
        from openapi_client.exceptions import ApiException
    else:
        openapi_client = None
except ImportError:
    # Fallback: try to import from system packages
    try:
        import openapi_client
        from openapi_client.api import (
            fileinfo_api,
            filemanager_api,
            fileupload_api,
            multimediafile_api,
        )
        from openapi_client.exceptions import ApiException

        openapi_client = True
    except ImportError:
        openapi_client = None

# Create a dummy ApiException for type hints when SDK is not available
if openapi_client is None:

    class ApiException(Exception):
        pass


from ..config import config
from ..utils.errors import (
    BaiduDriveError,
    FileOperationError,
    create_error_from_api_response,
)
from ..utils.logger import (
    get_fileops_logger,
    log_api_call,
    log_operation_end,
    log_operation_start,
)


class FileOperationsManager:
    """文件操作管理器"""

    def __init__(self):
        self.logger = get_fileops_logger()
        self.general_config = config.get_general_config()

        if not openapi_client:
            raise BaiduDriveError(
                "百度网盘 SDK 未找到，请检查 lib/baidu-netdisk-sdk 目录"
            )

    def list_files(
        self,
        access_token: str,
        path: str = "/",
        limit: int = 100,
        order: str = "time",
        desc: bool = True,
        web: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取文件列表

        Args:
            access_token: 访问令牌
            path: 目录路径
            limit: 返回数量限制 (最大1000)
            order: 排序方式 (time, size, name)
            desc: 是否降序
            web: 是否返回缩略图等Web信息

        Returns:
            文件列表

        Raises:
            FileOperationError: 操作失败
        """
        operation_name = f"列出文件 {path}"
        log_operation_start(self.logger, operation_name, path=path, limit=limit)

        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = fileinfo_api.FileinfoApi(api_client)

                start_time = time.time()

                response = api_instance.xpanfilelist(
                    access_token=access_token,
                    dir=path,
                    order=order,
                    desc=1 if desc else 0,
                    limit=limit,
                    web="1" if web else "0",
                    folder="0",  # 0=文件和文件夹, 1=只有文件夹
                    start="0",  # 从第一个开始
                    showempty=1,  # 显示空文件夹
                )

                duration = time.time() - start_time

                log_api_call(
                    self.logger,
                    "BaiduDrive",
                    "GET",
                    "xpanfilelist",
                    200,
                    duration,
                    path=path,
                    count=len(response.list) if hasattr(response, "list") else 0,
                )

                # 简单的调试信息
                self.logger.debug(f"API响应类型: {type(response)}")

                # 转换响应格式 - 简化版本
                files = []

                # 百度网盘API返回的是字典，包含list字段
                if isinstance(response, dict) and "list" in response:
                    file_list = response["list"]
                    # 调试：打印前几个文件的详细信息
                    if file_list and len(file_list) > 0:
                        self.logger.info(f"第一个文件的原始数据: {file_list[0]}")

                    for item in file_list:
                        if isinstance(item, dict):
                            # 从path字段提取文件名
                            if "path" in item:
                                path = item["path"]
                                filename = (
                                    os.path.basename(path) if path != "/" else "根目录"
                                )
                                # 创建包含文件名的临时项目
                                temp_item = item.copy()
                                temp_item["server_filename"] = filename
                                item = temp_item

                            file_info = self._convert_file_info(item)
                            files.append(file_info)

                log_operation_end(
                    self.logger,
                    operation_name,
                    success=True,
                    duration=duration,
                    file_count=len(files),
                )

                return files

        except ApiException as e:
            self._handle_api_exception(e, operation_name, path=path)
        except Exception as e:
            error = FileOperationError(
                f"列出文件失败: {e}", file_path=path, operation="list"
            )
            self.logger.error(f"{operation_name} 异常: {e}")
            raise error

    def get_file_info(self, access_token: str, file_path: str) -> Dict[str, Any]:
        """获取文件信息 - 简化版本"""
        # 通过列表接口获取单个文件信息
        parent_dir = str(Path(file_path).parent) if file_path != "/" else "/"
        files = self.list_files(access_token, parent_dir)

        file_name = Path(file_path).name
        for file_info in files:
            if file_info["filename"] == file_name:
                return file_info

        raise FileOperationError(
            f"文件不存在: {file_path}", file_path=file_path, operation="info"
        )

    def download_file(
        self,
        access_token: str,
        remote_path: str,
        local_path: str,
        progress_callback: Callable[[float, int, int], None] = None,
    ) -> bool:
        """下载文件 - 基于官方API实现"""
        operation_name = f"下载文件 {remote_path}"
        log_operation_start(
            self.logger, operation_name, remote_path=remote_path, local_path=local_path
        )

        try:
            # 第一步：获取文件信息，包括 fs_id 和文件大小
            file_info = self.get_file_info(access_token, remote_path)
            if not file_info:
                raise FileOperationError(
                    f"文件不存在: {remote_path}",
                    file_path=remote_path,
                    operation="download",
                )

            fs_id = file_info.get("fs_id")
            file_size = file_info.get("size", 0)

            if not fs_id:
                raise FileOperationError(
                    f"无法获取文件ID: {remote_path}",
                    file_path=remote_path,
                    operation="download",
                )

            self.logger.info(
                f"准备下载文件: {remote_path} (fs_id: {fs_id}, 大小: {file_size})"
            )

            # 第二步：获取下载链接
            download_url = self._get_download_url(access_token, str(fs_id))
            self.logger.info(f"获取到下载链接: {download_url[:100]}...")

            # 第三步：下载文件
            success = self._download_file_from_url(
                download_url, local_path, file_size, progress_callback, access_token
            )

            if success:
                log_operation_end(
                    self.logger,
                    operation_name,
                    remote_path=remote_path,
                    local_path=local_path,
                )
                return True
            else:
                raise FileOperationError(
                    f"下载失败: {remote_path}",
                    file_path=remote_path,
                    operation="download",
                )

        except ApiException as e:
            raise self._handle_api_exception(e, operation_name)
        except Exception as e:
            self.logger.error(f"{operation_name} 异常: {str(e)}")
            raise FileOperationError(
                f"{operation_name}失败: {str(e)}",
                file_path=remote_path,
                operation="download",
            )

    def upload_file(
        self,
        access_token: str,
        local_path: str,
        remote_path: str,
        progress_callback: Callable[[float, int, int], None] = None,
    ) -> bool:
        """上传文件 - 基于官方文档实现"""
        operation_name = f"上传文件 {local_path}"
        log_operation_start(
            self.logger, operation_name, local_path=local_path, remote_path=remote_path
        )

        try:
            # 检查本地文件
            if not os.path.exists(local_path):
                raise FileOperationError(
                    f"本地文件不存在: {local_path}",
                    file_path=local_path,
                    operation="upload",
                )

            file_size = os.path.getsize(local_path)

            # 小文件使用简单上传，大文件使用分片上传
            if file_size <= 4 * 1024 * 1024:  # 4MB以下
                success = self._simple_upload(
                    access_token, local_path, remote_path, progress_callback
                )
            else:
                success = self._chunk_upload(
                    access_token, local_path, remote_path, progress_callback
                )

            if success:
                log_operation_end(
                    self.logger,
                    operation_name,
                    success=True,
                    file_size=file_size,
                    remote_path=remote_path,
                )

            return success

        except Exception as e:
            self.logger.error(f"{operation_name} 失败: {e}")
            if isinstance(e, FileOperationError):
                raise
            else:
                raise FileOperationError(
                    f"上传文件异常: {e}", file_path=local_path, operation="upload"
                )

    def delete_file(self, access_token: str, file_path: str) -> bool:
        """删除文件

        Args:
            access_token: 访问令牌
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        operation_name = f"删除文件 {file_path}"
        log_operation_start(self.logger, operation_name, file_path=file_path)

        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = filemanager_api.FilemanagerApi(api_client)

                # 构建删除请求 - 使用正确的API方法
                filelist = f'["{file_path}"]'

                response = api_instance.filemanagerdelete(
                    access_token=access_token, _async=0, filelist=filelist  # 同步删除
                )

                # 检查删除结果
                success = self._check_operation_result(response, "delete")

                if success:
                    log_operation_end(self.logger, operation_name, success=True)

                return success

        except ApiException as e:
            self._handle_api_exception(e, operation_name, file_path=file_path)
        except Exception as e:
            error = FileOperationError(
                f"删除文件异常: {e}", file_path=file_path, operation="delete"
            )
            self.logger.error(f"{operation_name} 异常: {e}")
            raise error

    def copy_file(
        self, access_token: str, source_path: str, dest_path: str, new_name: str = None
    ) -> bool:
        """复制文件

        Args:
            access_token: 访问令牌
            source_path: 源文件路径
            dest_path: 目标目录路径
            new_name: 新文件名 (可选)

        Returns:
            是否复制成功
        """
        operation_name = f"复制文件 {source_path} -> {dest_path}"
        log_operation_start(
            self.logger, operation_name, source_path=source_path, dest_path=dest_path
        )

        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = filemanager_api.FilemanagerApi(api_client)

                # 构建复制请求
                filelist = f'[{{"path": "{source_path}", "dest": "{dest_path}", "newname": "{new_name or Path(source_path).name}"}}]'

                response = api_instance.filemanagercopy(
                    access_token=access_token, _async=0, filelist=filelist  # 同步操作
                )

                success = self._check_operation_result(response, "copy")

                if success:
                    log_operation_end(self.logger, operation_name, success=True)

                return success

        except ApiException as e:
            self._handle_api_exception(e, operation_name, source_path=source_path)
        except Exception as e:
            error = FileOperationError(
                f"复制文件异常: {e}", file_path=source_path, operation="copy"
            )
            self.logger.error(f"{operation_name} 异常: {e}")
            raise error

    def move_file(
        self, access_token: str, source_path: str, dest_path: str, new_name: str = None
    ) -> bool:
        """移动文件

        Args:
            access_token: 访问令牌
            source_path: 源文件路径
            dest_path: 目标目录路径
            new_name: 新文件名 (可选)

        Returns:
            是否移动成功
        """
        operation_name = f"移动文件 {source_path} -> {dest_path}"
        log_operation_start(
            self.logger, operation_name, source_path=source_path, dest_path=dest_path
        )

        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = filemanager_api.FilemanagerApi(api_client)

                filelist = f'[{{"path": "{source_path}", "dest": "{dest_path}", "newname": "{new_name or Path(source_path).name}"}}]'

                response = api_instance.filemanagermove(
                    access_token=access_token, _async=0, filelist=filelist  # 同步操作
                )

                success = self._check_operation_result(response, "move")

                if success:
                    log_operation_end(self.logger, operation_name, success=True)

                return success

        except ApiException as e:
            self._handle_api_exception(e, operation_name, source_path=source_path)
        except Exception as e:
            error = FileOperationError(
                f"移动文件异常: {e}", file_path=source_path, operation="move"
            )
            self.logger.error(f"{operation_name} 异常: {e}")
            raise error

    def create_folder(self, access_token: str, folder_path: str) -> bool:
        """创建文件夹

        Args:
            access_token: 访问令牌
            folder_path: 文件夹路径

        Returns:
            是否创建成功
        """
        operation_name = f"创建文件夹 {folder_path}"
        log_operation_start(self.logger, operation_name, folder_path=folder_path)

        try:
            # 百度网盘支持在文件路径中包含目录结构
            # 当我们上传文件到不存在的路径时，百度网盘会自动创建必要的目录
            # 所以我们通过上传一个隐藏的标记文件来"创建"文件夹

            import os
            import tempfile

            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".tmp"
            ) as tmp_file:
                tmp_file.write("# 此文件用于创建目录结构，可以安全删除")
                tmp_path = tmp_file.name

            try:
                # 上传到目标文件夹路径，文件名使用隐藏的标记
                marker_path = f"{folder_path}/.folder_marker"
                success = self.upload_file(access_token, tmp_path, marker_path)

                if not success:
                    raise FileOperationError(
                        "目录标记文件上传失败",
                        file_path=marker_path,
                        operation="create_folder",
                    )

                log_operation_end(self.logger, operation_name, success=True)
                return True

            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except ApiException as e:
            self._handle_api_exception(e, operation_name, folder_path=folder_path)
        except Exception as e:
            error = FileOperationError(
                f"创建文件夹异常: {e}", file_path=folder_path, operation="create"
            )
            self.logger.error(f"{operation_name} 异常: {e}")
            raise error

    def _convert_file_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """转换文件信息格式 - 简化版本"""
        # 百度网盘API返回的是字典，直接处理
        return {
            "filename": item.get("server_filename", item.get("filename", "")),
            "path": item.get("path", ""),
            "size": item.get("size", 0),
            "is_dir": item.get("isdir", 0) == 1,
            "fs_id": item.get("fs_id", 0),
            "mtime": item.get("server_mtime", 0),
            "ctime": item.get("server_ctime", 0),
            "category": item.get("category", 0),
            "md5": item.get("md5", ""),
            "thumbs": item.get("thumbs", {}),
        }

    def _handle_api_exception(
        self, exception: ApiException, operation: str, **context
    ) -> None:
        """处理 API 异常 - 简化版本"""
        # 直接创建错误，不进行复杂的解析
        error = FileOperationError(
            f"{operation} 失败: {exception}", operation=operation, **context
        )
        self.logger.error(f"{operation} API 调用失败: {error}")
        raise error

    def _check_operation_result(self, response: Any, operation: str) -> bool:
        """检查操作结果 - 简化版本"""
        # 简单检查errno字段
        return getattr(response, "errno", 0) == 0

    def _get_download_url(self, access_token: str, fs_id: str) -> str:
        """获取文件下载链接 - 基于官方API实现"""
        operation_name = f"获取下载链接 {fs_id}"
        log_operation_start(self.logger, operation_name, fs_id=fs_id)

        try:
            with openapi_client.ApiClient() as api_client:
                api_client.configuration.access_token = access_token
                api_instance = multimediafile_api.MultimediafileApi(api_client)

                # 调用 filemetas API 获取下载链接
                response = api_instance.xpanmultimediafilemetas(
                    access_token=access_token,
                    fsids=f"[{fs_id}]",  # fsids 需要是 JSON 数组格式
                    dlink="1",  # 请求下载链接
                )

                # 解析响应，获取下载链接
                if hasattr(response, "to_dict"):
                    response_data = response.to_dict()
                elif hasattr(response, "__dict__"):
                    response_data = {
                        k: v
                        for k, v in response.__dict__.items()
                        if not k.startswith("_") and v is not None
                    }
                elif isinstance(response, dict):
                    response_data = response
                else:
                    response_data = {}

                # 查找文件信息
                files_info = response_data.get("list", [])
                if not files_info:
                    raise FileOperationError(
                        f"未找到文件信息: {fs_id}",
                        file_path=fs_id,
                        operation="get_download_url",
                    )

                file_info = files_info[0]
                dlink = file_info.get("dlink")

                if not dlink:
                    raise FileOperationError(
                        f"未获取到下载链接: {fs_id}",
                        file_path=fs_id,
                        operation="get_download_url",
                    )

                log_operation_end(self.logger, operation_name, fs_id=fs_id)
                return dlink

        except ApiException as e:
            raise self._handle_api_exception(e, operation_name)
        except Exception as e:
            self.logger.error(f"{operation_name} 异常: {str(e)}")
            raise FileOperationError(
                f"{operation_name}失败: {str(e)}",
                file_path=fs_id,
                operation="get_download_url",
            )

    def _download_file_from_url(
        self,
        url: str,
        local_path: str,
        file_size: int,
        progress_callback: Callable = None,
        access_token: str = None,
    ) -> bool:
        """从 URL 下载文件 - 基于 requests 实现，支持大文件和进度回调"""
        operation_name = f"下载文件到 {local_path}"
        log_operation_start(
            self.logger,
            operation_name,
            url=url,
            local_path=local_path,
            file_size=file_size,
        )

        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 设置请求头（必须包含 User-Agent）
            headers = {
                "User-Agent": "pan.baidu.com",
                "Referer": "https://pan.baidu.com",
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            # 如果有 access_token，添加到请求参数中
            params = {}
            if access_token:
                params["access_token"] = access_token

            # 发起流式下载请求
            with requests.get(
                url, headers=headers, params=params, stream=True, timeout=30
            ) as response:
                response.raise_for_status()

                # 获取实际文件大小（优先使用传入的file_size，其次使用响应头的content-length）
                actual_size = file_size or int(
                    response.headers.get("content-length", 0)
                )

                downloaded = 0
                chunk_size = 8192  # 8KB chunks

                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # 过滤掉保活的新块
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 调用进度回调
                            if progress_callback and actual_size > 0:
                                # 确保进度不超过100%
                                progress = min((downloaded / actual_size) * 100, 100.0)
                                progress_callback(progress, downloaded, actual_size)

            # 验证下载的文件大小
            actual_downloaded = os.path.getsize(local_path)
            if actual_size > 0 and actual_downloaded != actual_size:
                self.logger.warning(
                    f"下载文件大小不匹配: 期望 {actual_size}, 实际 {actual_downloaded}"
                )

            log_operation_end(
                self.logger,
                operation_name,
                local_path=local_path,
                downloaded_size=actual_downloaded,
            )
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"{operation_name} 网络请求异常: {str(e)}")
            # 清理可能的不完整文件
            if os.path.exists(local_path):
                os.remove(local_path)
            raise FileOperationError(
                f"下载失败，网络请求异常: {str(e)}",
                file_path=local_path,
                operation="download",
            )
        except Exception as e:
            self.logger.error(f"{operation_name} 异常: {str(e)}")
            # 清理可能的不完整文件
            if os.path.exists(local_path):
                os.remove(local_path)
            raise FileOperationError(
                f"下载失败: {str(e)}", file_path=local_path, operation="download"
            )

    def _simple_upload(
        self,
        access_token: str,
        local_path: str,
        remote_path: str,
        progress_callback: Callable = None,
    ) -> bool:
        """简单上传 - 基于官方文档实现"""
        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = fileupload_api.FileuploadApi(api_client)

                # 获取文件大小
                file_size = os.path.getsize(local_path)

                # 计算文件MD5（简化版本，实际应该分块计算）
                import hashlib

                with open(local_path, "rb") as f:
                    file_content = f.read()
                    file_md5 = hashlib.md5(file_content).hexdigest()

                # 预创建文件
                response = api_instance.xpanfileprecreate(
                    access_token=access_token,
                    path=remote_path,
                    isdir=0,  # 文件
                    size=file_size,
                    autoinit=1,
                    block_list=f'["{file_md5}"]',
                )

                if not self._check_operation_result(response, "precreate"):
                    raise FileOperationError(
                        "预创建文件失败", file_path=remote_path, operation="upload"
                    )

                # 获取uploadid
                uploadid = response.get("uploadid")
                if not uploadid:
                    raise FileOperationError(
                        "预创建失败：未获取到uploadid",
                        file_path=remote_path,
                        operation="upload",
                    )

                # 上传文件内容
                with open(local_path, "rb") as f:
                    upload_response = api_instance.pcssuperfile2(
                        access_token=access_token,
                        partseq="0",
                        path=remote_path,
                        uploadid=uploadid,
                        type="tmpfile",
                        file=f,
                    )

                if not self._check_operation_result(upload_response, "upload"):
                    raise FileOperationError(
                        "文件上传失败", file_path=remote_path, operation="upload"
                    )

                # 创建文件（合并分片）
                create_response = api_instance.xpanfilecreate(
                    access_token=access_token,
                    path=remote_path,
                    isdir=0,
                    size=file_size,
                    uploadid=uploadid,
                    block_list=f'["{file_md5}"]',
                )

                if not self._check_operation_result(create_response, "create"):
                    raise FileOperationError(
                        "文件创建失败", file_path=remote_path, operation="upload"
                    )

                return True

        except Exception as e:
            self.logger.error(f"简单上传失败: {e}")
            raise

    def _chunk_upload(
        self,
        access_token: str,
        local_path: str,
        remote_path: str,
        progress_callback: Callable = None,
    ) -> bool:
        """分片上传 - 基于官方文档实现"""
        try:
            with openapi_client.ApiClient() as api_client:
                api_instance = fileupload_api.FileuploadApi(api_client)

                # 获取文件大小
                file_size = os.path.getsize(local_path)

                # 分片大小：4MB
                chunk_size = 4 * 1024 * 1024
                total_chunks = (file_size + chunk_size - 1) // chunk_size

                # 计算每个分片的MD5
                block_list = []
                with open(local_path, "rb") as f:
                    for i in range(total_chunks):
                        chunk_data = f.read(chunk_size)
                        chunk_md5 = hashlib.md5(chunk_data).hexdigest()
                        block_list.append(chunk_md5)

                # 预创建文件
                block_list_json = (
                    "[" + ",".join([f'"{md5}"' for md5 in block_list]) + "]"
                )
                response = api_instance.xpanfileprecreate(
                    access_token=access_token,
                    path=remote_path,
                    isdir=0,  # 文件
                    size=file_size,
                    autoinit=1,
                    block_list=block_list_json,
                )

                if not self._check_operation_result(response, "precreate"):
                    raise FileOperationError(
                        "预创建文件失败", file_path=remote_path, operation="upload"
                    )

                # 获取uploadid
                uploadid = response.get("uploadid")
                if not uploadid:
                    raise FileOperationError(
                        "预创建失败：未获取到uploadid",
                        file_path=remote_path,
                        operation="upload",
                    )

                # 分片上传
                with open(local_path, "rb") as f:
                    for i in range(total_chunks):
                        chunk_data = f.read(chunk_size)

                        # 上传分片
                        upload_response = api_instance.pcssuperfile2(
                            access_token=access_token,
                            partseq=str(i),
                            path=remote_path,
                            uploadid=uploadid,
                            type="tmpfile",
                            file=chunk_data,
                        )

                        if not self._check_operation_result(
                            upload_response, f"upload_chunk_{i}"
                        ):
                            raise FileOperationError(
                                f"分片{i}上传失败",
                                file_path=remote_path,
                                operation="upload",
                            )

                        # 进度回调
                        if progress_callback:
                            progress = ((i + 1) / total_chunks) * 100
                            progress_callback(progress, i + 1, total_chunks)

                # 创建文件（合并分片）
                create_response = api_instance.xpanfilecreate(
                    access_token=access_token,
                    path=remote_path,
                    isdir=0,
                    size=file_size,
                    uploadid=uploadid,
                    block_list=block_list_json,
                )

                if not self._check_operation_result(create_response, "create"):
                    raise FileOperationError(
                        "文件创建失败", file_path=remote_path, operation="upload"
                    )

                return True

        except Exception as e:
            self.logger.error(f"分片上传失败: {e}")
            raise
