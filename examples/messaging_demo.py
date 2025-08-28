"""
消息提供者管理器演示

展示如何使用新的消息提供者管理器来动态切换和管理不同的消息推送渠道
"""

from bddriver.messaging import get_messaging_manager, MessageProviderManager


def demo_basic_usage():
    """演示基本用法"""
    print("🚀 消息提供者管理器基本用法演示")
    print("=" * 60)
    
    # 获取全局管理器实例
    manager = get_messaging_manager()
    
    # 查看当前状态
    status = manager.get_status()
    print(f"📋 配置文件: {status['config_file']}")
    print(f"🎯 默认提供者: {status['default_provider']}")
    print(f"✅ 已启用的提供者: {', '.join(manager.get_enabled_providers())}")
    print()


def demo_provider_management():
    """演示提供者管理"""
    print("🔧 提供者管理演示")
    print("=" * 60)
    
    manager = get_messaging_manager()
    
    # 列出所有可用提供者
    print("📱 所有可用的消息提供者:")
    for provider in manager.get_available_providers():
        print(f"  • {provider}")
    print()
    
    # 查看详细状态
    status = manager.get_status()
    for provider_name, provider_status in status['providers'].items():
        status_icon = "✅" if provider_status['enabled'] else "❌"
        config_icon = "✅" if provider_status.get('config_complete', False) else "⚠️"
        print(f"{status_icon} {provider_name.upper()}: {'启用' if provider_status['enabled'] else '禁用'} (配置: {'完整' if provider_status.get('config_complete', False) else '不完整'})")
    print()


def demo_configuration_examples():
    """演示配置示例"""
    print("⚙️ 配置示例")
    print("=" * 60)
    
    manager = get_messaging_manager()
    
    print("📱 WxPusher 配置示例:")
    print("  manager.enable_provider('wxpusher', {'app_token': 'AT_xxxxxxxxxxxxxxxxxxxxxxxx'})")
    print()
    
    print("🔔 钉钉配置示例:")
    print("  manager.enable_provider('dingtalk', {")
    print("      'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=xxx',")
    print("      'secret': 'SEC000000000000000000000'")
    print("  })")
    print()
    
    print("💼 企业微信配置示例:")
    print("  manager.enable_provider('wechat_work', {")
    print("      'corp_id': 'wwxxxxxxxxxxxxxxxxxx',")
    print("      'agent_id': '1000001',")
    print("      'secret': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'")
    print("  })")
    print()
    
    print("📧 邮件配置示例:")
    print("  manager.enable_provider('email', {")
    print("      'smtp_host': 'smtp.gmail.com',")
    print("      'smtp_port': 587,")
    print("      'username': 'your-email@gmail.com',")
    print("      'password': 'your-app-password'")
    print("  })")
    print()


def demo_dynamic_switching():
    """演示动态切换"""
    print("🔄 动态切换演示")
    print("=" * 60)
    
    manager = get_messaging_manager()
    
    current_provider = manager.get_default_provider()
    print(f"🎯 当前默认提供者: {current_provider}")
    
    # 尝试切换到其他提供者（如果已启用）
    enabled_providers = manager.get_enabled_providers()
    if len(enabled_providers) > 1:
        # 选择第一个不是当前默认的已启用提供者
        for provider in enabled_providers:
            if provider != current_provider:
                print(f"🔄 尝试切换到: {provider}")
                if manager.set_default_provider(provider):
                    print(f"✅ 成功切换到: {provider}")
                    break
                else:
                    print(f"❌ 切换失败: {provider}")
    else:
        print("ℹ️  只有一个已启用的提供者，无法演示切换")
    
    print()


def demo_advanced_features():
    """演示高级功能"""
    print("🚀 高级功能演示")
    print("=" * 60)
    
    manager = get_messaging_manager()
    
    # 演示配置更新
    print("📝 配置更新示例:")
    wxpusher_config = manager.get_provider_config("wxpusher")
    if wxpusher_config:
        print(f"  WxPusher 当前配置: {wxpusher_config}")
        print("  可以调用 manager.update_provider_config('wxpusher', new_config) 来更新")
    print()
    
    # 演示实例获取
    print("🔧 实例获取示例:")
    try:
        provider_instance = manager.get_provider_instance()
        print(f"  ✅ 成功获取默认提供者实例: {type(provider_instance).__name__}")
    except Exception as e:
        print(f"  ❌ 获取提供者实例失败: {e}")
    print()
    
    # 演示测试功能
    print("🧪 测试功能示例:")
    print("  可以调用 manager.test_provider('provider_name') 来测试提供者")
    print("  或者使用 CLI: bddriver messaging test <provider>")


def main():
    """主函数"""
    print("🎉 消息提供者管理器演示")
    print("=" * 80)
    print()
    
    try:
        # 基本用法演示
        demo_basic_usage()
        
        # 提供者管理演示
        demo_provider_management()
        
        # 配置示例演示
        demo_configuration_examples()
        
        # 动态切换演示
        demo_dynamic_switching()
        
        # 高级功能演示
        demo_advanced_features()
        
        print("=" * 80)
        print("🎯 使用建议:")
        print("1. 使用 'bddriver messaging list' 查看当前状态")
        print("2. 使用 'bddriver messaging config <provider>' 配置提供者")
        print("3. 使用 'bddriver messaging switch <provider>' 切换默认提供者")
        print("4. 使用 'bddriver messaging test <provider>' 测试配置")
        print("5. 配置文件会自动保存到 ~/.bddriver/messaging.json 或项目根目录")
        print()
        print("💡 更多信息请查看 README.md 和 CLI 帮助")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
