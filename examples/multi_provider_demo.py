"""
多消息提供者使用示例

展示如何配置和使用不同的推送渠道
"""

from bddriver.messaging import WxPusherClient
from bddriver.messaging.providers import DingTalkProvider, WeChatWorkProvider, EmailProvider
from bddriver.auth import AuthManager


def setup_message_providers():
    """设置多个消息提供者"""
    providers = {}
    
    # 1. WxPusher提供者（默认）
    wxpusher_client = WxPusherClient()
    providers["wxpusher"] = wxpusher_client
    
    # 2. 钉钉提供者（未来扩展）
    dingtalk_config = {
        "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx",
        "secret": "SEC000000000000000000000"  # 可选
    }
    dingtalk_provider = DingTalkProvider(dingtalk_config)
    providers["dingtalk"] = dingtalk_provider
    
    # 3. 企业微信提供者（未来扩展）
    wechat_work_config = {
        "corp_id": "wwxxxxxxxxxxxxxxxxxx",
        "agent_id": "1000001",
        "secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    wechat_work_provider = WeChatWorkProvider(wechat_work_config)
    providers["wechat_work"] = wechat_work_provider
    
    # 4. 邮件提供者（未来扩展）
    email_config = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your-email@gmail.com",
        "password": "your-app-password"
    }
    email_provider = EmailProvider(email_config)
    providers["email"] = email_provider
    
    return providers


def test_provider_detection():
    """测试提供者自动检测"""
    providers = setup_message_providers()
    
    # 测试不同类型的用户ID
    test_user_ids = [
        "UID_xxxxxxxxx",           # WxPusher
        "13800138000",             # 钉钉手机号
        "ding_xxxxxxxxx",          # 钉钉用户ID
        "wwxxxxxxxxxxxxxxxxxx",    # 企业微信用户ID
        "user@example.com",        # 邮箱
    ]
    
    print("🔍 测试消息提供者:")
    print("=" * 50)
    
    for user_id in test_user_ids:
        if user_id.startswith("UID_"):
            print(f"✅ {user_id} -> WxPusher")
        elif user_id.isdigit() and len(user_id) == 11:
            print(f"✅ {user_id} -> 钉钉（手机号）")
        elif user_id.startswith("ding_"):
            print(f"✅ {user_id} -> 钉钉（用户ID）")
        elif user_id.startswith("ww"):
            print(f"✅ {user_id} -> 企业微信")
        elif "@" in user_id:
            print(f"✅ {user_id} -> 邮件")
        else:
            print(f"❌ {user_id} -> 无法识别")
    
    print("=" * 50)


def test_message_sending():
    """测试消息发送"""
    providers = setup_message_providers()
    
    print("\n📤 测试消息发送:")
    print("=" * 50)
    
    # 测试WxPusher消息发送
    wxpusher = providers["wxpusher"]
    print("📱 测试WxPusher消息发送...")
    
    # 这里只是演示，实际使用时需要有效的配置
    print("ℹ️  WxPusher客户端已初始化")
    print("ℹ️  需要有效配置才能发送实际消息")
    
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
        print("ℹ️  授权管理器已集成WxPusher消息推送")
        
    except Exception as e:
        print(f"❌ 授权管理器创建失败: {e}")
    
    print("=" * 50)


def main():
    """主函数"""
    print("🚀 多消息提供者演示")
    print("=" * 60)
    
    # 1. 测试提供者
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
