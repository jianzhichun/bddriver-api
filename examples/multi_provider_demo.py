"""
多消息提供者使用示例

展示如何使用新的消息抽象接口配置多个推送渠道
"""

from bddriver.messaging import MessageProviderRegistry, WxPusherProvider
from bddriver.messaging.future_providers import DingTalkProvider, WeChatWorkProvider, EmailProvider
from bddriver.auth import AuthManager


def setup_message_providers():
    """设置多个消息提供者"""
    registry = MessageProviderRegistry()
    
    # 1. 注册WxPusher提供者
    wxpusher_config = {
        "app_token": "AT_xxxxxxxxxxxxx",  # 从环境变量或配置文件获取
        "base_url": "https://wxpusher.zjiecode.com"
    }
    wxpusher_provider = WxPusherProvider(wxpusher_config)
    registry.register_provider("wxpusher", wxpusher_provider)
    
    # 2. 注册钉钉提供者（未来扩展）
    dingtalk_config = {
        "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx",
        "secret": "SEC000000000000000000000"  # 可选
    }
    dingtalk_provider = DingTalkProvider(dingtalk_config)
    registry.register_provider("dingtalk", dingtalk_provider)
    
    # 3. 注册企业微信提供者（未来扩展）
    wechat_work_config = {
        "corp_id": "wwxxxxxxxxxxxxxxxxxx",
        "agent_id": "1000001",
        "secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    wechat_work_provider = WeChatWorkProvider(wechat_work_config)
    registry.register_provider("wechat_work", wechat_work_provider)
    
    # 4. 注册邮件提供者（未来扩展）
    email_config = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your-email@gmail.com",
        "password": "your-app-password"
    }
    email_provider = EmailProvider(email_config)
    registry.register_provider("email", email_provider)
    
    return registry


def test_provider_detection():
    """测试提供者自动检测"""
    registry = setup_message_providers()
    
    # 测试不同类型的用户ID
    test_user_ids = [
        "UID_xxxxxxxxx",           # WxPusher
        "13800138000",             # 钉钉手机号
        "ding_xxxxxxxxx",          # 钉钉用户ID
        "wwxxxxxxxxxxxxxxxxxx",    # 企业微信用户ID
        "user@example.com",        # 邮箱
    ]
    
    print("🔍 测试消息提供者自动检测:")
    print("=" * 50)
    
    for user_id in test_user_ids:
        provider = registry.detect_provider_by_user_id(user_id)
        if provider:
            print(f"✅ {user_id} -> {provider.name} ({provider.__class__.__name__})")
        else:
            print(f"❌ {user_id} -> 无法识别")
    
    print("=" * 50)


def test_message_sending():
    """测试消息发送"""
    registry = setup_message_providers()
    
    # 测试发送消息到不同类型的用户
    test_cases = [
        ("UID_xxxxxxxxx", "WxPusher用户"),
        ("13800138000", "钉钉用户"),
        ("user@example.com", "邮件用户"),
    ]
    
    print("\n📤 测试消息发送:")
    print("=" * 50)
    
    for user_id, user_type in test_cases:
        provider = registry.detect_provider_by_user_id(user_id)
        if provider:
            print(f"📱 发送消息到 {user_type} ({user_id})...")
            
            # 发送测试消息
            result = provider.send_message(
                user_id=user_id,
                message="这是一条测试消息，用于验证消息提供者是否正常工作。",
                title="测试消息"
            )
            
            if result.success:
                print(f"✅ 发送成功: {result.message_id}")
            else:
                print(f"❌ 发送失败: {result.error_message}")
        else:
            print(f"⚠️  无法识别用户类型: {user_id}")
    
    print("=" * 50)


def test_auth_manager_integration():
    """测试与授权管理器的集成"""
    print("\n🔐 测试与授权管理器的集成:")
    print("=" * 50)
    
    try:
        # 创建授权管理器（会自动使用配置的消息提供者）
        auth_manager = AuthManager()
        print("✅ 授权管理器创建成功")
        
        # 这里可以测试实际的授权流程
        print("ℹ️  授权管理器已集成新的消息抽象接口")
        
    except Exception as e:
        print(f"❌ 授权管理器创建失败: {e}")
    
    print("=" * 50)


def main():
    """主函数"""
    print("🚀 多消息提供者演示")
    print("=" * 60)
    
    # 1. 测试提供者自动检测
    test_provider_detection()
    
    # 2. 测试消息发送
    test_message_sending()
    
    # 3. 测试授权管理器集成
    test_auth_manager_integration()
    
    print("\n🎉 演示完成！")
    print("\n💡 使用说明:")
    print("1. 配置环境变量或配置文件中的认证信息")
    print("2. 根据实际需要启用相应的消息提供者")
    print("3. 系统会自动根据用户ID格式选择合适的提供者")
    print("4. 未来可以轻松添加新的推送渠道")


if __name__ == "__main__":
    main()
