#!/usr/bin/env python3
"""
设备码授权示例

演示如何使用BaiduDriver SDK的设备码模式进行百度网盘授权。
设备码模式无需回调链接，适合任何环境部署。

使用方法:
    python device_auth.py

注意事项:
    1. 确保目标用户已关注WxPusher微信公众号
    2. 目标用户需要提供其WxPusher UID
    3. 用户码有效期通常为10分钟，请及时完成授权
"""

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bddriver import BaiduDriver
from bddriver.utils.errors import AuthTimeoutError, BaiduDriveError, WxPusherError


def main():
    """主函数：演示设备码授权流程"""
    print("🚀 BaiduDriver 设备码授权示例")
    print("=" * 50)

    # 创建BaiduDriver实例
    try:
        driver = BaiduDriver()
        print("✅ BaiduDriver 初始化成功")
    except Exception as e:
        print(f"❌ BaiduDriver 初始化失败: {e}")
        return

    # 获取目标用户UID
    target_user_id = input("\n请输入目标用户的WxPusher UID: ").strip()
    if not target_user_id:
        print("❌ 用户UID不能为空")
        return

    # 获取授权范围
    scope = input("请输入授权范围 (默认: basic,netdisk): ").strip()
    if not scope:
        scope = "basic,netdisk"

    # 获取超时时间
    timeout_input = input("请输入授权超时时间(秒，默认: 300): ").strip()
    try:
        timeout = int(timeout_input) if timeout_input else 300
    except ValueError:
        print("❌ 超时时间格式错误，使用默认值300秒")
        timeout = 300

    print(f"\n📋 授权信息:")
    print(f"   目标用户: {target_user_id}")
    print(f"   授权范围: {scope}")
    print(f"   超时时间: {timeout}秒")

    # 确认开始授权
    confirm = input("\n确认开始授权? (y/N): ").strip().lower()
    if confirm != "y":
        print("❌ 用户取消授权")
        return

    print(f"\n🔄 开始设备码授权流程...")
    print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 发起设备码授权请求
        start_time = time.time()

        result = driver.request_device_access(
            target_user_id=target_user_id, scope=scope, timeout=timeout
        )

        end_time = time.time()
        duration = end_time - start_time

        # 授权成功
        print(f"\n🎉 授权成功！")
        print(f"⏱️  总耗时: {duration:.1f}秒")
        print(f"🔑 Access Token: {result['access_token'][:20]}...")
        print(f"🔄 Refresh Token: {result['refresh_token'][:20]}...")
        print(f"⏰ 过期时间: {result['expires_in']}秒")
        print(f"📋 授权范围: {result['scope']}")
        print(f"🔧 授权方式: {result['auth_method']}")

        # 演示如何使用token
        print(f"\n🚀 现在可以使用access_token进行文件操作了！")

        # 这里可以添加文件操作示例
        # files = driver.list_files(result['access_token'], "/")
        # print(f"📁 根目录文件数量: {len(files)}")

    except AuthTimeoutError as e:
        print(f"\n⏰ 授权超时: {e}")
        print("💡 建议:")
        print("   1. 检查目标用户是否收到WxPusher消息")
        print("   2. 确认用户是否及时完成授权")
        print("   3. 增加超时时间重试")

    except WxPusherError as e:
        print(f"\n📱 WxPusher推送失败: {e}")
        print("💡 建议:")
        print("   1. 检查目标用户UID是否正确")
        print("   2. 确认用户是否已关注WxPusher微信公众号")
        print("   3. 检查网络连接")

    except BaiduDriveError as e:
        print(f"\n🔐 百度网盘授权失败: {e}")
        print("💡 建议:")
        print("   1. 检查百度网盘应用配置")
        print("   2. 确认授权范围是否正确")
        print("   3. 稍后重试")

    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        print("💡 建议:")
        print("   1. 检查错误日志")
        print("   2. 确认SDK版本")
        print("   3. 联系技术支持")


def demo_batch_auth():
    """演示批量设备码授权"""
    print("\n🔄 批量设备码授权演示")
    print("=" * 30)

    # 模拟多个用户授权
    users = [
        {"uid": "user1_uid", "scope": "basic,netdisk"},
        {"uid": "user2_uid", "scope": "basic,netdisk"},
        {"uid": "user3_uid", "scope": "basic,netdisk"},
    ]

    driver = BaiduDriver()
    results = []

    for i, user in enumerate(users, 1):
        print(f"\n📱 处理用户 {i}/{len(users)}: {user['uid']}")

        try:
            result = driver.request_device_access(
                target_user_id=user["uid"], scope=user["scope"], timeout=300
            )

            results.append(
                {
                    "user_id": user["uid"],
                    "status": "success",
                    "access_token": result["access_token"][:20] + "...",
                }
            )

            print(f"✅ 用户 {user['uid']} 授权成功")

        except Exception as e:
            results.append(
                {"user_id": user["uid"], "status": "failed", "error": str(e)}
            )

            print(f"❌ 用户 {user['uid']} 授权失败: {e}")

    # 显示批量授权结果
    print(f"\n📊 批量授权结果:")
    print(f"{'用户ID':<15} {'状态':<10} {'结果'}")
    print("-" * 40)

    for result in results:
        if result["status"] == "success":
            print(f"{result['user_id']:<15} {'成功':<10} {result['access_token']}")
        else:
            print(f"{result['user_id']:<15} {'失败':<10} {result['error']}")


def demo_custom_scope():
    """演示自定义授权范围"""
    print("\n🔧 自定义授权范围演示")
    print("=" * 30)

    driver = BaiduDriver()

    # 不同的授权范围示例
    scopes = [
        "basic,netdisk",  # 基础权限
        "basic,netdisk,netdisk_quota",  # 包含配额查询
        "basic,netdisk,netdisk_quota,netdisk_share",  # 包含分享功能
    ]

    target_user_id = input("请输入测试用户UID: ").strip()
    if not target_user_id:
        print("❌ 用户UID不能为空")
        return

    for scope in scopes:
        print(f"\n🔐 测试授权范围: {scope}")

        try:
            result = driver.request_device_access(
                target_user_id=target_user_id, scope=scope, timeout=300
            )

            print(f"✅ 授权成功，范围: {result['scope']}")
            print(f"🔑 Token: {result['access_token'][:20]}...")

        except Exception as e:
            print(f"❌ 授权失败: {e}")


if __name__ == "__main__":
    try:
        # 主授权流程
        main()

        # 询问是否运行其他演示
        print(f"\n" + "=" * 50)
        print("🎯 其他演示选项:")
        print("   1. 批量授权演示")
        print("   2. 自定义授权范围演示")
        print("   3. 退出")

        choice = input("\n请选择 (1-3): ").strip()

        if choice == "1":
            demo_batch_auth()
        elif choice == "2":
            demo_custom_scope()
        elif choice == "3":
            print("👋 再见！")
        else:
            print("❌ 无效选择")

    except KeyboardInterrupt:
        print(f"\n\n⏹️  用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback

        traceback.print_exc()
