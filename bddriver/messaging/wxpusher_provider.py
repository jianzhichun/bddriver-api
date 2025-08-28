"""
WxPusher 消息提供者

直接实现WxPusher消息发送，保持向后兼容性
"""

import requests
from typing import Any, Dict, Optional
from ..config import config


class WxPusherProvider:
    """WxPusher 微信推送提供者
    
    直接实现WxPusher消息发送，保持向后兼容性
    """
    
    def __init__(self):
        """初始化WxPusher提供者"""
        wxpusher_config = config.get_wxpusher_config()
        self.app_token = wxpusher_config.app_token
        self.base_url = wxpusher_config.base_url
        self.api_url = f"{self.base_url}/api/send/message"
    
    def validate_user_id(self, user_id: str) -> bool:
        """验证WxPusher用户ID格式
        
        WxPusher用户ID通常是UID_开头的字符串
        """
        return user_id.startswith("UID_") and len(user_id) > 4
    
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
        
        try:
            # 构建请求数据
            data = {
                "appToken": self.app_token,
                "content": content,
                "summary": summary or "百度网盘通知",
                "contentType": content_type,
                "uids": [target_user],
            }
            
            if url:
                data["url"] = url
            
            # 发送请求
            response = requests.post(
                self.api_url,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "success": True,
                        "messageId": result.get("data", {}).get("messageId"),
                        "data": result
                    }
                else:
                    return {
                        "success": False,
                        "msg": result.get("msg", "发送失败"),
                        "data": result
                    }
            else:
                return {
                    "success": False,
                    "msg": f"HTTP {response.status_code}: {response.text}",
                    "data": {"status_code": response.status_code}
                }
                
        except Exception as e:
            return {
                "success": False,
                "msg": f"发送消息异常: {e}",
                "data": {}
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


# 为了向后兼容，保留WxPusherClient别名
WxPusherClient = WxPusherProvider
