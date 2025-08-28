#!/usr/bin/env python3
"""订阅功能演示脚本

展示如何使用WxPusher进行用户订阅和消息推送
"""

from bddriver.messaging import get_messaging_manager
import time

def demo_subscription_flow():
    """演示完整的订阅流程"""
    print("🎉 WxPusher订阅功能演示")
    print("=" * 60)
    
    # 获取消息管理器
    manager = get_messaging_manager()
    provider = manager.get_provider_instance('wxpusher')
    
    print(f"✅ 获取到WxPusher提供者: {type(provider).__name__}")
    print()
    
    # 1. 获取订阅信息
    print("📱 步骤1: 获取订阅信息")
    print("-" * 30)
    
    subscribe_info = manager.get_subscription_info('wxpusher')
    if subscribe_info.get("success"):
        print("✅ 订阅信息获取成功")
        print(f"🔗 订阅地址: {subscribe_info.get('subscribe_url')}")
        print(f"📱 订阅二维码: {subscribe_info.get('qr_code')}")
        print(f"📋 应用名称: {subscribe_info.get('app_name')}")
    else:
        print(f"❌ 订阅信息获取失败: {subscribe_info.get('msg')}")
        return
    
    print()
    
    # 2. 创建带参数的订阅二维码
    print("📱 步骤2: 创建带参数的订阅二维码")
    print("-" * 30)
    
    # 模拟用户ID
    user_id = "forum_user_123"
    extra_param = f"user_id={user_id}&source=forum"
    
    qrcode_result = manager.create_subscription_qrcode(
        extra=extra_param,
        valid_time=1800,  # 30分钟
        provider_name='wxpusher'
    )
    
    if qrcode_result.get("success"):
        print("✅ 二维码创建成功")
        print(f"🔑 额外参数: {extra_param}")
        print(f"📱 二维码URL: {qrcode_result.get('qrcode_url')}")
        print(f"🔑 二维码Code: {qrcode_result.get('qrcode_code')}")
        print(f"⏰ 有效期: {qrcode_result.get('expires_in', 'N/A')} 秒")
        
        qrcode_code = qrcode_result.get('qrcode_code')
    else:
        print(f"❌ 二维码创建失败: {qrcode_result.get('msg')}")
        return
    
    print()
    
    # 3. 模拟用户扫码过程
    print("📱 步骤3: 模拟用户扫码过程")
    print("-" * 30)
    
    print("💡 现在用户需要:")
    print("   1. 扫描上方二维码")
    print("   2. 关注WxPusher公众号")
    print("   3. 完成订阅")
    print()
    
    print("⏳ 等待用户扫码...")
    print("💡 在实际使用中，你可以:")
    print("   - 定期调用 check_scan_status 查询扫码状态")
    print("   - 设置回调地址接收扫码通知")
    print("   - 使用轮询方式检查用户是否完成订阅")
    print()
    
    # 4. 查询扫码状态（模拟）
    print("📱 步骤4: 查询扫码状态")
    print("-" * 30)
    
    if qrcode_code:
        print(f"🔍 查询二维码 {qrcode_code} 的扫码状态...")
        
        # 在实际使用中，这里应该定期轮询
        scan_result = manager.check_scan_status(qrcode_code, 'wxpusher')
        
        if scan_result.get("success"):
            if scan_result.get("scanned"):
                print("✅ 用户已扫码完成订阅！")
                print(f"👤 用户UID: {scan_result.get('uid')}")
                print(f"⏰ 扫码时间: {scan_result.get('scan_time')}")
                print(f"🔑 额外参数: {scan_result.get('extra')}")
                
                # 5. 发送测试消息
                print()
                print("📱 步骤5: 发送测试消息")
                print("-" * 30)
                
                user_uid = scan_result.get('uid')
                if user_uid:
                    message_result = provider.send_message(
                        user_id=user_uid,
                        content="🎉 恭喜！您已成功订阅百度网盘通知服务。",
                        summary="订阅成功通知",
                        content_type=2
                    )
                    
                    if message_result.get("success"):
                        print("✅ 测试消息发送成功！")
                        print(f"📱 消息ID: {message_result.get('messageId')}")
                    else:
                        print(f"❌ 测试消息发送失败: {message_result.get('msg')}")
                else:
                    print("⚠️ 无法获取用户UID，跳过消息发送")
            else:
                print("⏳ 用户尚未扫码，请继续等待...")
        else:
            print(f"❌ 查询扫码状态失败: {scan_result.get('msg')}")
    
    print()
    print("🎯 订阅流程演示完成！")
    print()
    print("💡 实际使用建议:")
    print("   1. 在网页或应用中嵌入订阅二维码")
    print("   2. 定期轮询扫码状态（间隔≥10秒）")
    print("   3. 获取用户UID后保存到数据库")
    print("   4. 使用UID发送百度网盘相关通知")
    print("   5. 支持回调方式接收扫码通知")

if __name__ == "__main__":
    demo_subscription_flow()
