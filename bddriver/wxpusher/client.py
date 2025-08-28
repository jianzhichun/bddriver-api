"""
WxPusher client for BaiduDriver SDK

基于新的消息抽象接口实现，保持向后兼容性
"""

from typing import Any, Dict, Optional
from ..messaging.wxpusher import WxPusherProvider
from ..config import config


class WxPusherClient:
    """WxPusher 微信推送客户端
    
    基于新的消息抽象接口实现，保持向后兼容性
    """
    
    def __init__(self):
        """初始化WxPusher客户端"""
        wxpusher_config = config.get_wxpusher_config()
        self.provider = WxPusherProvider(wxpusher_config.__dict__)
    
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
            summary: 消息摘要
            content_type: 内容类型 1:文本 2:HTML 3:Markdown
            url: 原文链接
            uids: 用户ID列表
            
        Returns:
            发送结果
        """
        # 确定目标用户
        target_user = user_id or (uids[0] if uids else None)
        if not target_user:
            raise ValueError("必须指定 user_id 或 uids")
        
        # 发送消息
        result = self.provider.send_message(
            user_id=target_user,
            message=content,
            title=summary,
            url=url,
            content_type=content_type
        )
        
        # 转换为旧格式的返回结果
        if result.success:
            return {
                "success": True,
                "messageId": result.message_id,
                "data": result.metadata or {}
            }
        else:
            return {
                "success": False,
                "msg": result.error_message or "发送失败",
                "data": result.metadata or {}
            }
    
    def send_device_auth_notification(
        self,
        user_id: str,
        user_code: str,
        verification_url: str,
        expires_in: int,
    ) -> Dict[str, Any]:
        """发送设备码授权通知"""
        message = f"""
🔐 百度网盘设备码授权

🔢 用户码: {user_code}
🔗 验证链接: {verification_url}
⏰ 有效期: {expires_in} 秒

📱 请在浏览器中访问验证链接，输入用户码完成授权。

⚠️ 用户码 {expires_in} 秒后过期，请及时完成授权。
        """.strip()
        
        return self.send_message(
            user_id=user_id,
            content=message,
            summary="百度网盘设备码授权",
            content_type=2,
            url=verification_url
        )
    
    def send_success_notification(
        self,
        user_id: str,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发送授权成功通知"""
        if access_token:
            masked_token = access_token[:12] + "..." if len(access_token) > 12 else access_token
            message = f"""
✅ 百度网盘授权成功！

🔑 访问令牌: {masked_token}
⏰ 授权时间: 刚刚完成

🎉 现在可以使用百度网盘API进行文件操作了！
            """.strip()
        else:
            message = """
✅ 百度网盘授权成功！

🎉 授权已完成，现在可以使用百度网盘API进行文件操作了！
            """.strip()
        
        return self.send_message(
            user_id=user_id,
            content=message,
            summary="百度网盘授权成功",
            content_type=2
        )
