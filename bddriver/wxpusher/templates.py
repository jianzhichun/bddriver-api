"""
Message templates for WxPusher notifications
Specialized for device code authorization flow
Provides HTML templates for device code authorization messages
"""

from datetime import datetime
from typing import Any, Dict


class MessageTemplates:
    """WxPusher 消息模板管理器 - 专门用于设备码授权"""

    @staticmethod
    def device_auth_template(
        user_code: str,
        verification_url: str,
        expires_in: int,
        file_path: str = "/",
        description: str = None,
    ) -> Dict[str, Any]:
        """设备码授权消息模板

        Args:
            user_code: 用户码
            verification_url: 验证URL
            expires_in: 过期时间（秒）
            file_path: 请求访问的文件路径
            description: 授权描述

        Returns:
            消息数据
        """
        # 计算剩余时间
        minutes = expires_in // 60
        seconds = expires_in % 60

        if not description:
            description = "需要访问您的百度网盘文件"

        # 构建HTML内容
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f8f9fa;">
            <div style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
                <!-- 标题 -->
                <div style="text-align: center; margin-bottom: 24px;">
                    <h2 style="color: #1a73e8; margin: 0; font-size: 24px;">🔐 百度网盘授权请求</h2>
                    <p style="color: #5f6368; margin: 8px 0 0 0; font-size: 14px;">请完成以下授权步骤</p>
                </div>
                
                <!-- 授权信息 -->
                <div style="background: #f1f3f4; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <h3 style="color: #202124; margin: 0 0 12px 0; font-size: 16px;">📋 授权详情</h3>
                    <p style="color: #5f6368; margin: 0 0 8px 0; font-size: 14px;">
                        <strong>请求访问:</strong> {file_path}
                    </p>
                    <p style="color: #5f6368; margin: 0 0 8px 0; font-size: 14px;">
                        <strong>说明:</strong> {description}
                    </p>
                    <p style="color: #5f6368; margin: 0; font-size: 14px;">
                        <strong>有效期:</strong> {minutes}分{seconds}秒
                    </p>
                </div>
                
                <!-- 操作步骤 -->
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #202124; margin: 0 0 12px 0; font-size: 16px;">🚀 授权步骤</h3>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 12px;">
                        <span style="background: #1a73e8; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px; margin-right: 12px;">1</span>
                        <span style="color: #5f6368; font-size: 14px;">点击下方按钮进入百度网盘授权页面</span>
                    </div>
                    
                    <div style="display: flex; align-items: center; margin-bottom: 12px;">
                        <span style="background: #1a73e8; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px; margin-right: 12px;">2</span>
                        <span style="color: #5f6368; font-size: 14px;">输入用户码: </span>
                        <div style="display: flex; align-items: center; margin-left: 8px;">
                            <code style="color: #202124; font-family: monospace; background: #e8f0fe; padding: 6px 10px; border-radius: 4px; border: 1px solid #dadce0; margin-right: 8px; font-size: 14px; letter-spacing: 1px;">{user_code}</code>
                            <button onclick="copyToClipboard('{user_code}')" style="background: #34a853; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-size: 12px; cursor: pointer; transition: background 0.2s; display: flex; align-items: center;">
                                📋 复制
                            </button>
                        </div>
                    </div>
                    
                    <div style="display: flex; align-items: center;">
                        <span style="background: #1a73e8; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px; margin-right: 12px;">3</span>
                        <span style="color: #5f6368; font-size: 14px;">确认授权即可完成</span>
                    </div>
                </div>
                
                <!-- 操作按钮 -->
                <div style="text-align: center;">
                    <a href="{verification_url}" style="display: inline-block; background: #1a73e8; color: white; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 500; font-size: 16px; transition: background 0.2s;">
                        🔗 进入授权页面
                    </a>
                    <p style="color: #5f6368; margin: 8px 0 0 0; font-size: 12px;">点击后将自动跳转到百度网盘授权页面</p>
                </div>
                
                <!-- 注意事项 -->
                <div style="margin-top: 20px; padding: 16px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin: 0 0 8px 0; font-size: 14px;">⚠️ 注意事项</h4>
                    <ul style="color: #856404; margin: 0; padding-left: 20px; font-size: 13px;">
                        <li>用户码有效期仅 {minutes} 分钟，请及时完成授权</li>
                        <li>授权完成后，我将能够访问您指定的文件</li>
                        <li>如需取消授权，请忽略此消息</li>
                    </ul>
                </div>
                
                <!-- 底部信息 -->
                <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e8eaed;">
                    <p style="color: #9aa0a6; margin: 0; font-size: 12px;">
                        此消息由 BaiduDriver SDK 自动发送<br>
                        如有疑问，请联系系统管理员
                    </p>
                </div>
            </div>
        </div>
        
        <!-- JavaScript 功能 -->
        <script>
        function copyToClipboard(text) {{
            // 创建临时输入框
            const tempInput = document.createElement('input');
            tempInput.value = text;
            document.body.appendChild(tempInput);
            
            // 选择并复制文本
            tempInput.select();
            tempInput.setSelectionRange(0, 99999); // 兼容移动设备
            
            try {{
                document.execCommand('copy');
                // 显示复制成功提示
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '✅ 已复制';
                button.style.background = '#10b981';
                
                // 2秒后恢复原样
                setTimeout(() => {{
                    button.innerHTML = originalText;
                    button.style.background = '#34a853';
                }}, 2000);
            }} catch (err) {{
                console.error('复制失败:', err);
                // 显示复制失败提示
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '❌ 复制失败';
                button.style.background = '#dc2626';
                
                // 2秒后恢复原样
                setTimeout(() => {{
                    button.innerHTML = originalText;
                    button.style.background = '#34a853';
                }}, 2000);
            }}
            
            // 清理临时元素
            document.body.removeChild(tempInput);
        }}
        </script>
        """

        return {
            "content": html_content,
            "summary": f"百度网盘授权请求 - 用户码: {user_code}",
            "content_type": 2,  # HTML格式
            "url": verification_url,
        }

    @staticmethod
    def auth_success_template(
        user_id: str, file_path: str = "/", expires_at: int = None
    ) -> Dict[str, Any]:
        """授权成功消息模板

        Args:
            user_id: 目标用户ID
            file_path: 授权访问的文件路径
            expires_at: 过期时间戳

        Returns:
            消息模板数据
        """

        # 格式化过期时间
        if expires_at:
            try:
                expire_time = datetime.fromtimestamp(expires_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                expire_info = f"过期时间: {expire_time}"
            except:
                expire_info = "有效期: 1小时"
        else:
            expire_info = "有效期: 1小时"

        content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; background: #f8fafc; padding: 20px; border-radius: 12px;">
            <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 16px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="color: #10b981; font-size: 48px; margin-bottom: 16px;">✅</div>
                    <h2 style="color: #1f2937; margin: 0 0 8px 0; font-size: 20px;">授权成功</h2>
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">BaiduDriver 授权通知</p>
                </div>
                
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <p style="margin: 0 0 8px 0; color: #166534; font-size: 14px;">
                        <strong>授权状态:</strong> 成功
                    </p>
                    <p style="margin: 0 0 8px 0; color: #166534; font-size: 14px;">
                        <strong>访问路径:</strong> {file_path}
                    </p>
                    <p style="margin: 0; color: #059669; font-size: 12px;">
                        <strong>{expire_info}</strong>
                    </p>
                </div>
                
                <div style="text-align: center;">
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">
                        现在可以访问您的百度网盘文件了
                    </p>
                </div>
            </div>
        </div>
        """

        return {"content": content, "summary": "百度网盘授权成功", "content_type": 2}

    @staticmethod
    def auth_failed_template(
        user_id: str, error_msg: str, requester: str = None
    ) -> Dict[str, Any]:
        """授权失败消息模板

        Args:
            user_id: 目标用户ID
            error_msg: 错误信息
            requester: 请求者标识

        Returns:
            消息模板数据
        """

        if not requester:
            requester = "BaiduDriver用户"

        content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; background: #f8fafc; padding: 20px; border-radius: 12px;">
            <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 16px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="color: #dc2626; font-size: 48px; margin-bottom: 16px;">❌</div>
                    <h2 style="color: #1f2937; margin: 0 0 8px 0; font-size: 20px;">授权失败</h2>
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">BaiduDriver 授权通知</p>
                </div>
                
                <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <p style="margin: 0 0 8px 0; color: #991b1b; font-size: 14px;">
                        <strong>请求者:</strong> {requester}
                    </p>
                    <p style="margin: 0 0 8px 0; color: #991b1b; font-size: 14px;">
                        <strong>错误信息:</strong> {error_msg}
                    </p>
                    <p style="margin: 0; color: #dc2626; font-size: 12px;">
                        <strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
                
                <div style="text-align: center;">
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">
                        如需重新授权，请等待新的授权请求
                    </p>
                </div>
            </div>
        </div>
        """

        return {"content": content, "summary": "百度网盘授权失败", "content_type": 2}

    @staticmethod
    def error_notification_template(
        error_type: str, error_msg: str, details: str = None
    ) -> Dict[str, Any]:
        """错误通知模板

        Args:
            error_type: 错误类型
            error_msg: 错误消息
            details: 详细信息

        Returns:
            消息模板数据
        """

        content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; background: #f8fafc; padding: 20px; border-radius: 12px;">
            <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 16px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="color: #f59e0b; font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h2 style="color: #1f2937; margin: 0 0 8px 0; font-size: 20px;">系统通知</h2>
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">BaiduDriver 系统通知</p>
                </div>
                
                <div style="background: #fffbeb; border: 1px solid #fde68a; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <p style="margin: 0 0 8px 0; color: #92400e; font-size: 14px;">
                        <strong>错误类型:</strong> {error_type}
                    </p>
                    <p style="margin: 0 0 8px 0; color: #92400e; font-size: 14px;">
                        <strong>错误消息:</strong> {error_msg}
                    </p>
                    {f'<p style="margin: 0 0 8px 0; color: #92400e; font-size: 14px;"><strong>详细信息:</strong> {details}</p>' if details else ''}
                    <p style="margin: 0; color: #d97706; font-size: 12px;">
                        <strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
                
                <div style="text-align: center;">
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">
                        请检查系统状态或联系管理员
                    </p>
                </div>
            </div>
        </div>
        """

        return {
            "content": content,
            "summary": f"系统通知: {error_type}",
            "content_type": 2,
        }

    @staticmethod
    def file_operation_progress_template(
        operation: str, progress: float, details: str = None
    ) -> Dict[str, Any]:
        """文件操作进度模板

        Args:
            operation: 操作类型
            progress: 进度 (0.0 - 1.0)
            details: 详细信息

        Returns:
            消息模板数据
        """

        # 计算百分比
        percentage = int(progress * 100)

        # 进度条
        progress_bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)

        content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; background: #f8fafc; padding: 20px; border-radius: 12px;">
            <div style="background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 16px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #1f2937; margin: 0 0 8px 0; font-size: 20px;">📁 文件操作进度</h2>
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">BaiduDriver 操作通知</p>
                </div>
                
                <div style="background: #f3f4f6; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <p style="margin: 0 0 8px 0; color: #374151; font-size: 14px;">
                        <strong>操作类型:</strong> {operation}
                    </p>
                    <p style="margin: 0 0 12px 0; color: #374151; font-size: 14px;">
                        <strong>进度:</strong> {percentage}%
                    </p>
                    
                    <!-- 进度条 -->
                    <div style="background: #e5e7eb; border-radius: 10px; height: 20px; overflow: hidden; margin-bottom: 8px;">
                        <div style="background: #3b82f6; height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
                    </div>
                    
                    <p style="margin: 0; color: #6b7280; font-size: 12px;">
                        {progress_bar} {percentage}%
                    </p>
                    
                    {f'<p style="margin: 8px 0 0 0; color: #6b7280; font-size: 13px;"><strong>详情:</strong> {details}</p>' if details else ''}
                </div>
                
                <div style="text-align: center;">
                    <p style="color: #6b7280; margin: 0; font-size: 14px;">
                        操作完成后将收到通知
                    </p>
                </div>
            </div>
        </div>
        """

        return {
            "content": content,
            "summary": f"{operation} 进度: {percentage}%",
            "content_type": 2,
        }
