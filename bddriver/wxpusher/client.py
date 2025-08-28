"""
WxPusher client for BaiduDriver SDK
Based on TIP 2: WxPusher Integration
Sends WeChat notifications via WxPusher service
"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from ..config import config
from ..utils.errors import WxPusherError, create_error_from_api_response
from ..utils.logger import get_wxpusher_logger, log_api_call


class WxPusherClient:
    """WxPusher 微信推送客户端"""

    def __init__(self):
        self.logger = get_wxpusher_logger()
        self.config = config.get_wxpusher_config()
        self.session = requests.Session()
        self._last_send_at: float = 0.0
        self.session.headers.update(
            {"User-Agent": self.config.user_agent, "Content-Type": "application/json"}
        )

    def _api_url(self, path: str) -> str:
        """Build WxPusher API url robustly preserving base path (e.g., /api).
        Ensures base ends with one slash and path has no leading slash.
        """
        base = (self.config.base_url or "").rstrip("/") + "/"
        rel = path.lstrip("/")
        return urljoin(base, rel)

    def send_message(
        self,
        user_id: Optional[str] = None,
        content: str = "",
        summary: str = None,
        content_type: int = 2,
        url: str = None,
        uids: Optional[list] = None,
    ) -> Dict[str, Any]:
        """发送消息到指定用户

        Args:
            user_id: 用户 UID
            content: 消息内容
            summary: 消息摘要（≤20字符）
            content_type: 内容类型 1:文本 2:HTML 3:Markdown
            url: 原文链接

        Returns:
            发送结果

        Raises:
            WxPusherError: 发送失败
        """
        api_url = self._api_url("send/message")

        # 构建请求数据
        truncated_summary = (summary or "百度网盘授权通知")[:20]
        # WxPusher 对内容长度较敏感，这里在发送前做保护性截断
        max_content_len = 40000
        safe_content = content if content is not None else ""
        if len(safe_content) > max_content_len:
            safe_content = safe_content[: max_content_len - 3] + "..."
        if url and len(url) > 400:
            url = url[:400]
        data = {
            "appToken": self.config.app_token,
            "content": safe_content,
            "summary": truncated_summary,
            "contentType": content_type,
        }
        if uids is not None:
            data["uids"] = uids
        elif user_id is not None:
            data["uids"] = [user_id]

        if url:
            data["url"] = url

        # 参数验证
        self._validate_message_params(data)

        # 参数已验证，准备发送

        # 发送请求
        return self._send_request(api_url, data, f"发送消息到用户 {user_id}")

    # 便捷函数：测试期望的 API
    def send_auth_request(
        self,
        user_id: str,
        auth_url: str,
        file_path: str,
        description: str,
        requester: str,
    ) -> Dict[str, Any]:
        from .templates import MessageTemplates

        msg = MessageTemplates.auth_request_template(
            user_id, auth_url, description, requester
        )
        return self.send_message(
            user_id=user_id,
            content=msg["content"],
            summary=msg["summary"],
            content_type=msg["content_type"],
            url=msg.get("url"),
        )

    def send_auth_success(
        self, user_id: str, file_path: str, expires_at: int
    ) -> Dict[str, Any]:
        from .templates import MessageTemplates

        msg = MessageTemplates.auth_success_template(user_id)
        return self.send_message(
            user_id=user_id,
            content=msg["content"],
            summary=msg["summary"],
            content_type=msg["content_type"],
        )

    def send_auth_failure(
        self, user_id: str, file_path: str, error: str
    ) -> Dict[str, Any]:
        from .templates import MessageTemplates

        msg = MessageTemplates.auth_failed_template(user_id, error)
        return self.send_message(
            user_id=user_id,
            content=msg["content"],
            summary=msg["summary"],
            content_type=msg["content_type"],
        )

    def send_message_to_topic(
        self,
        topic_id: str,
        content: str,
        summary: str = None,
        content_type: int = 2,
        url: str = None,
    ) -> Dict[str, Any]:
        """发送消息到主题（群发）

        Args:
            topic_id: 主题 ID
            content: 消息内容
            summary: 消息摘要（≤20字符）
            content_type: 内容类型 1:文本 2:HTML 3:Markdown
            url: 原文链接

        Returns:
            发送结果
        """
        api_url = self._api_url("send/message")

        truncated_summary = (summary or "百度网盘授权通知")[:20]
        max_content_len = 40000
        safe_content = content if content is not None else ""
        if len(safe_content) > max_content_len:
            safe_content = safe_content[: max_content_len - 3] + "..."
        if url and len(url) > 400:
            url = url[:400]
        data = {
            "appToken": self.config.app_token,
            "content": safe_content,
            "summary": truncated_summary,
            "contentType": content_type,
            "topicIds": [topic_id],
        }

        if url:
            data["url"] = url

        self._validate_message_params(data)

        # 参数已验证，准备发送

        return self._send_request(api_url, data, f"发送消息到主题 {topic_id}")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息

        Args:
            user_id: 用户 UID

        Returns:
            用户信息
        """
        api_url = self._api_url("user/wxuser")

        params = {"appToken": self.config.app_token, "uid": user_id}

        try:
            start_time = time.time()
            response = self.session.get(
                api_url, params=params, timeout=self.config.timeout
            )
            duration = time.time() - start_time

            log_api_call(
                self.logger,
                "WxPusher",
                "GET",
                api_url,
                response.status_code,
                duration,
                user_id=user_id,
            )

            response.raise_for_status()
            result = response.json()

            if not result.get("success", False):
                raise create_error_from_api_response("WxPusher", result)

            return result.get("data", {})

        except requests.RequestException as e:
            self.logger.error(f"获取用户信息请求失败: {e}")
            raise WxPusherError(f"获取用户信息失败: {e}", user_id=user_id)

    def _send_request(
        self, url: str, data: Dict[str, Any], operation: str
    ) -> Dict[str, Any]:
        """发送请求的通用方法"""
        retries = 0
        max_retries = self.config.max_retries

        while retries <= max_retries:
            try:
                # 轻量限流：QPS <= 2（请求间隔至少 ~0.5s）
                self._respect_rate_limit()
                start_time = time.time()
                response = self.session.post(
                    url, json=data, timeout=self.config.timeout
                )
                duration = time.time() - start_time

                log_api_call(
                    self.logger,
                    "WxPusher",
                    "POST",
                    url,
                    response.status_code,
                    duration,
                    operation=operation,
                    attempt=retries + 1,
                )

                response.raise_for_status()
                result = response.json()

                # 检查 API 返回状态
                if not result.get("success", False):
                    # 透出服务端错误信息（如：接口不存在 / 内容长度超限）
                    server_msg = result.get("msg") or "WxPusher 调用失败"
                    api_error = WxPusherError(server_msg)

                    # 某些错误码不需要重试
                    if self._should_not_retry(result):
                        raise api_error

                    if retries < max_retries:
                        retries += 1
                        wait_time = 2**retries
                        self.logger.warning(
                            f"{operation} 失败，{wait_time}s 后重试 ({retries}/{max_retries}): {api_error}"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise api_error

                self.logger.info(f"{operation} 成功")
                return result

            except requests.RequestException as e:
                if retries < max_retries:
                    retries += 1
                    wait_time = 2**retries
                    self.logger.warning(
                        f"{operation} 网络错误，{wait_time}s 后重试 ({retries}/{max_retries}): {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"{operation} 最终失败: {e}")
                    raise WxPusherError(f"{operation} 失败: {e}")

        # 不应该到达这里
        raise WxPusherError(f"{operation} 重试次数耗尽")

    def _respect_rate_limit(self) -> None:
        """遵守 WxPusher 发送速率限制（最大 QPS≈2）。"""
        now = time.time()
        elapsed = now - self._last_send_at
        min_interval = 0.5
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_send_at = time.time()

    def _validate_message_params(self, data: Dict[str, Any]) -> None:
        """验证消息参数"""
        # 验证内容长度
        content = data.get("content", "")
        if len(content) > 40000:
            raise WxPusherError("消息内容超过40000字符限制")

        # 验证摘要长度
        summary = data.get("summary", "")
        if summary and len(summary) > 20:
            raise WxPusherError("消息摘要超过20字符限制")

        # 验证 URL 长度
        url = data.get("url")
        if url and len(url) > 400:
            raise WxPusherError("URL 超过400字符限制")

        # 验证内容类型
        content_type = data.get("contentType", 2)
        if content_type not in [1, 2, 3]:
            raise WxPusherError(
                "无效的内容类型，必须是 1(文本)、2(HTML) 或 3(Markdown)"
            )

        # 验证接收者
        has_uids = data.get("uids") and len(data["uids"]) > 0
        has_topics = data.get("topicIds") and len(data["topicIds"]) > 0

        if not (has_uids or has_topics):
            raise WxPusherError("必须指定接收用户 UID 或主题 ID")
        if has_uids and len(data["uids"]) > 2000:
            raise WxPusherError("单条消息 UID 数量超过 2000 限制")
        if has_topics and len(data["topicIds"]) > 5:
            raise WxPusherError("单条消息 topicIds 数量超过 5 限制")

    def _should_not_retry(self, result: Dict[str, Any]) -> bool:
        """判断是否不应该重试"""
        error_code = result.get("code")

        # 这些错误码不需要重试
        no_retry_codes = {
            1001,  # appToken无效
            1003,  # uid参数错误
            1004,  # 内容长度超限
        }

        return error_code in no_retry_codes

    def cleanup(self) -> None:
        """清理资源

        清理所有相关的资源，如网络连接等
        """
        try:
            self.logger.info("开始清理WxPusher客户端资源")

            # 关闭网络会话
            if hasattr(self, "session") and self.session:
                self.session.close()
                self.logger.debug("网络会话已关闭")

            self.logger.info("WxPusher客户端资源清理完成")

        except Exception as e:
            self.logger.warning(f"清理WxPusher客户端资源时发生异常: {e}")
            # 清理过程中的异常不应该影响主流程

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
        except:
            pass
