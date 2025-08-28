"""
WxPusher 消息提供者

实现WxPusher消息发送和订阅功能
"""

import requests
from typing import Any, Dict, Optional
from ..config import config
from .base import BuiltinProvider


class WxPusherProvider(BuiltinProvider):
    """WxPusher 微信推送提供者
    
    实现WxPusher消息发送和订阅功能
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
                try:
                    result = response.json()
                    
                    # 处理WxPusher API响应格式
                    if isinstance(result, dict):
                        # 检查状态码和success字段
                        code = result.get("code", 0)
                        success = result.get("success", False)
                        msg = result.get("msg", "未知状态")
                        
                        if code == 1000 and success:
                            # 发送成功，提取有用的信息
                            data_list = result.get("data", [])
                            if isinstance(data_list, list) and len(data_list) > 0:
                                # 取第一个发送记录的信息
                                first_record = data_list[0]
                                message_content_id = first_record.get("messageContentId")
                                send_record_id = first_record.get("sendRecordId")
                                uid = first_record.get("uid")
                                
                                return {
                                    "success": True,
                                    "messageId": message_content_id,  # 使用messageContentId替代废弃的messageId
                                    "sendRecordId": send_record_id,
                                    "uid": uid,
                                    "data": result
                                }
                            else:
                                return {
                                    "success": True,
                                    "messageId": None,
                                    "data": result
                                }
                        else:
                            # 发送失败或状态异常
                            return {
                                "success": False,
                                "msg": f"发送失败: {msg} (状态码: {code})",
                                "data": result
                            }
                    else:
                        # 响应格式异常
                        return {
                            "success": False,
                            "msg": f"响应格式异常: 期望字典格式，实际为 {type(result).__name__}",
                            "data": {"raw_response": result}
                        }
                        
                except Exception as parse_error:
                    return {
                        "success": False,
                        "msg": f"解析响应失败: {parse_error}",
                        "data": {"raw_response": response.text}
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
        # 使用HTML格式，链接可点击，用户码方便复制
        message = (
            f"🔐 百度网盘设备码授权<br><br>"
            f"🔢 用户码: <code style='background-color: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;'>{user_code}</code><br>"
            f"🔗 验证链接: <a href='{verification_url}' target='_blank'>{verification_url}</a><br>"
            f"⏰ 有效期: {expires_in} 秒<br><br>"
            f"📱 请点击上方链接或复制用户码完成授权。<br><br>"
            f"⚠️ 用户码 {expires_in} 秒后过期，请及时完成授权。"
        )
        
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
            message = (
                f"✅ 百度网盘授权成功！<br><br>"
                f"🔑 访问令牌: {masked_token}<br>"
                f"⏰ 授权时间: 刚刚完成<br><br>"
                f"🎉 现在可以使用百度网盘API进行文件操作了！"
            )
        else:
            message = (
                "✅ 百度网盘授权成功！<br><br>"
                "🎉 授权已完成，现在可以使用百度网盘API进行文件操作了！"
            )
        
        return self.send_message(
            user_id=user_id,
            content=message,
            summary="百度网盘授权成功",
            content_type=2
        )


    def create_subscription_qrcode(self, extra: str = "", valid_time: int = 1800) -> Dict[str, Any]:
        """创建订阅二维码
        
        Args:
            extra: 二维码携带的参数，最长64位
            valid_time: 二维码有效期，默认30分钟，最长30天，单位是秒
            
        Returns:
            创建结果
        """
        try:
            # 构建请求数据
            data = {
                "appToken": self.app_token,
                "extra": extra,
                "validTime": valid_time
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/api/fun/create/qrcode",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    if isinstance(result, dict):
                        code = result.get("code", 0)
                        success = result.get("success", False)
                        msg = result.get("msg", "未知状态")
                        
                        if code == 1000 and success:
                            qrcode_data = result.get("data", {})
                            return {
                                "success": True,
                                "qrcode_url": qrcode_data.get("url"),
                                "qrcode_code": qrcode_data.get("code"),
                                "expires_in": qrcode_data.get("expiresIn"),
                                "data": result
                            }
                        else:
                            return {
                                "success": False,
                                "msg": f"创建二维码失败: {msg} (状态码: {code})",
                                "data": result
                            }
                    else:
                        return {
                            "success": False,
                            "msg": f"响应格式异常: 期望字典格式，实际为 {type(result).__name__}",
                            "data": {"raw_response": result}
                        }
                        
                except Exception as parse_error:
                    return {
                        "success": False,
                        "msg": f"解析响应失败: {parse_error}",
                        "data": {"raw_response": response.text}
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
                "msg": f"创建二维码异常: {e}",
                "data": {}
            }
    
    def get_subscription_info(self) -> Dict[str, Any]:
        """获取订阅信息
        
        Returns:
            订阅信息
        """
        # 创建带默认参数的二维码用于用户订阅
        # 使用时间戳作为唯一标识，避免重复
        import time
        extra = f"timestamp={int(time.time())}"
        
        qrcode_result = self.create_subscription_qrcode(
            extra=extra, 
            valid_time=1800
        )
        
        if qrcode_result.get("success"):
            return {
                "success": True,
                "app_name": "百度网盘通知",
                "app_token": self.app_token,
                "subscribe_url": qrcode_result.get("qrcode_url"),
                "qr_code": qrcode_result.get("qrcode_url"),
                "qrcode_code": qrcode_result.get("qrcode_code"),
                "expires_in": qrcode_result.get("expires_in"),
                "data": {
                    "appName": "百度网盘通知",
                    "appToken": self.app_token,
                    "qrcode_info": qrcode_result
                }
            }
        else:
            return {
                "success": False,
                "msg": f"创建订阅二维码失败: {qrcode_result.get('msg')}",
                "app_name": "百度网盘通知",
                "app_token": self.app_token
            }
    
    def check_scan_status(self, qrcode_code: str) -> Dict[str, Any]:
        """查询扫码用户UID
        
        Args:
            qrcode_code: 二维码的code参数
            
        Returns:
            扫码状态
        """
        try:
            # 发送请求
            response = requests.get(
                f"{self.base_url}/api/fun/scan-qrcode-uid",
                params={"code": qrcode_code},
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    if isinstance(result, dict):
                        code = result.get("code", 0)
                        success = result.get("success", False)
                        msg = result.get("msg", "未知状态")
                        
                        if code == 1000 and success:
                            scan_data = result.get("data")
                            
                            # 根据WxPusher API文档，扫码成功后data字段直接是UID字符串
                            if isinstance(scan_data, str):
                                # 扫码成功，data是UID
                                return {
                                    "success": True,
                                    "scanned": True,
                                    "uid": scan_data,
                                    "scan_time": None,  # WxPusher API没有返回扫码时间
                                    "extra": None,      # WxPusher API没有返回额外参数
                                    "data": result
                                }
                            elif isinstance(scan_data, dict):
                                # 扫码成功，data是对象（兼容其他可能的格式）
                                return {
                                    "success": True,
                                    "scanned": scan_data.get("scanned", True),
                                    "uid": scan_data.get("uid"),
                                    "scan_time": scan_data.get("scanTime"),
                                    "extra": scan_data.get("extra"),
                                    "data": result
                                }
                            else:
                                # 未知的data格式
                                return {
                                    "success": True,
                                    "scanned": True,
                                    "uid": str(scan_data),
                                    "scan_time": None,
                                    "extra": None,
                                    "data": result
                                }
                        else:
                            return {
                                "success": False,
                                "msg": f"查询扫码状态失败: {msg} (状态码: {code})",
                                "data": result
                            }
                    elif isinstance(result, str):
                        # 处理字符串响应
                        return {
                            "success": False,
                            "msg": f"响应格式异常: 收到字符串响应: {result}",
                            "data": {"raw_response": result}
                        }
                    else:
                        return {
                            "success": False,
                            "msg": f"响应格式异常: 期望字典格式，实际为 {type(result).__name__}",
                            "data": {"raw_response": result}
                        }
                        
                except Exception as parse_error:
                    return {
                        "success": False,
                        "msg": f"解析响应失败: {parse_error}",
                        "data": {"raw_response": response.text}
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
                "msg": f"查询扫码状态异常: {e}",
                "data": {}
            }

    def poll_scan_status(self, qrcode_code: str, interval: int = 15, max_attempts: int = 120) -> Dict[str, Any]:
        """轮询扫码状态直到获得用户UID
        
        Args:
            qrcode_code: 二维码的code参数
            interval: 轮询间隔（秒），最小10秒
            max_attempts: 最大轮询次数，默认120次（30分钟）
            
        Returns:
            轮询结果
        """
        import time
        
        # 确保轮询间隔不小于10秒，避免封号
        if interval < 10:
            interval = 10
            print(f"⚠️  轮询间隔已调整为10秒（最小间隔要求）")
        
        print(f"🔄 开始轮询扫码状态...")
        print(f"   📱 二维码Code: {qrcode_code}")
        print(f"   ⏰ 轮询间隔: {interval} 秒")
        print(f"   🔢 最大次数: {max_attempts} 次")
        print(f"   ⏱️  预计时间: {max_attempts * interval // 60} 分钟")
        print()
        
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 第 {attempt}/{max_attempts} 次查询...")
            
            # 查询扫码状态
            result = self.check_scan_status(qrcode_code)
            
            if result.get("success"):
                if result.get("scanned") and result.get("uid"):
                    print(f"✅ 用户扫码成功！")
                    print(f"   👤 用户UID: {result.get('uid')}")
                    print(f"   ⏰ 扫码时间: {result.get('scan_time')}")
                    print(f"   🔑 额外参数: {result.get('extra')}")
                    print(f"   🎯 轮询完成，共查询 {attempt} 次")
                    
                    return {
                        "success": True,
                        "scanned": True,
                        "uid": result.get("uid"),
                        "scan_time": result.get("scan_time"),
                        "extra": result.get("extra"),
                        "attempts": attempt,
                        "total_time": attempt * interval,
                        "data": result
                    }
                else:
                    print(f"⏳ 用户尚未扫码，继续等待...")
            else:
                print(f"❌ 查询失败: {result.get('msg')}")
            
            # 如果不是最后一次查询，则等待
            if attempt < max_attempts:
                print(f"⏰ 等待 {interval} 秒后重试...")
                time.sleep(interval)
                print()
        
        # 达到最大轮询次数
        print(f"⏰ 轮询超时，共查询 {max_attempts} 次")
        print(f"💡 建议:")
        print(f"   • 检查二维码是否过期")
        print(f"   • 确认用户是否完成订阅")
        print(f"   • 可以手动使用 'bddriver messaging scan {qrcode_code}' 查询")
        
        return {
            "success": False,
            "msg": f"轮询超时，{max_attempts} 次查询后仍未获得用户UID",
            "attempts": max_attempts,
            "total_time": max_attempts * interval,
            "data": {}
        }


# 为了向后兼容，保留WxPusherClient别名
WxPusherClient = WxPusherProvider
