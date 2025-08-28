#!/usr/bin/env python3
"""
BaiduDriver 上下文管理器示例

演示如何使用上下文管理器来确保资源的正确管理和清理
"""

import os
import sys
import tempfile
import time

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver import BaiduDriver
from bddriver.utils.errors import BaiduDriverError


def example_1_basic_context_manager():
    """示例1: 基础上下文管理器使用"""
    print("示例1: 基础上下文管理器")
    print("-" * 40)

    # 使用 with 语句确保资源自动清理
    with BaiduDriver() as driver:
        print(f"   📱 SDK 版本: {driver.get_version()}")
        print("   🔧 配置信息已加载")

        # 获取配置信息
        config_info = driver.get_config_info()
        print(f"   ⚙️  配置模块数量: {len(config_info)}")

        # 在这个作用域内，driver 是活跃的
        print("   ✅ 客户端在 with 块内正常工作")

    # 当退出 with 块时，driver.cleanup() 会自动调用
    print("   🧹 退出 with 块，资源已自动清理")


def example_2_auth_session_context():
    """示例2: 授权会话上下文管理器"""
    print("\n示例2: 授权会话上下文管理器")
    print("-" * 40)

    driver = BaiduDriver()

    try:
        # 替换为实际的 WxPusher UID
        target_user_id = "UID_xxxxxxxxx"  # 请替换为实际的 WxPusher UID

        print("   🔐 开始授权会话...")

        # 使用授权会话上下文管理器
        with driver.auth_session(
            target_user_id=target_user_id,
            file_path="/ContextManager_Demo",
            description="演示上下文管理器的使用",
            requester="上下文管理器示例",
        ) as session:

            access_token = session["access_token"]
            request_id = session["request_id"]

            print(f"   ✅ 授权会话建立成功")
            print(f"   🆔 请求ID: {request_id}")

            # 在授权会话中执行文件操作
            print("   📋 列出根目录文件...")
            files = driver.list_files(access_token, "/", limit=5)

            if files:
                print(f"   📁 找到 {len(files)} 个项目:")
                for file in files:
                    icon = "📁" if file.get("is_dir") else "📄"
                    name = file.get("filename", "Unknown")
                    print(f"      {icon} {name}")
            else:
                print("   ℹ️  根目录为空")

            # 创建测试目录
            test_folder = "/ContextManager_Demo"
            try:
                driver.create_folder(access_token, test_folder)
                print(f"   ✅ 创建测试目录: {test_folder}")
            except Exception as e:
                print(f"   ⚠️  创建目录失败: {e}")

        # 会话结束时会自动记录日志
        print("   🔚 授权会话自动结束")

    except Exception as e:
        print(f"   ❌ 授权会话失败: {e}")

    finally:
        # 清理主客户端
        driver.cleanup()


def example_3_nested_context_managers():
    """示例3: 嵌套上下文管理器"""
    print("\n示例3: 嵌套上下文管理器")
    print("-" * 40)

    # 在这个例子中，我们使用多个上下文管理器
    with BaiduDriver() as driver:
        print("   🚀 外层：BaiduDriver 客户端已创建")

        try:
            # 替换为实际的 WxPusher UID
            target_user_id = "UID_xxxxxxxxx"  # 请替换为实际的 WxPusher UID

            # 嵌套的授权会话
            with driver.auth_session(
                target_user_id=target_user_id,
                file_path="/NestedContext_Demo",
                description="演示嵌套上下文管理器",
                timeout=120,
            ) as session:

                print("   🔐 内层：授权会话已建立")
                access_token = session["access_token"]

                # 在嵌套上下文中执行操作
                print("   📊 检查令牌状态...")
                is_expired = driver.is_token_expired(session)
                print(f"   🔍 令牌状态: {'过期' if is_expired else '有效'}")

                # 创建临时文件并上传
                temp_content = f"嵌套上下文管理器测试\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                temp_file = os.path.join(
                    tempfile.gettempdir(), "nested_context_test.txt"
                )

                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(temp_content)

                print("   📤 上传测试文件...")
                remote_path = "/NestedContext_Demo/test_file.txt"

                # 先创建目录
                try:
                    driver.create_folder(access_token, "/NestedContext_Demo")
                except Exception:
                    pass  # 忽略目录已存在的错误

                # 上传文件
                success = driver.upload_file(access_token, temp_file, remote_path)
                if success:
                    print("   ✅ 文件上传成功")

                    # 立即下载验证
                    download_path = os.path.join(
                        tempfile.gettempdir(), "downloaded_nested.txt"
                    )
                    success = driver.download_file(
                        access_token, remote_path, download_path
                    )

                    if success:
                        print("   ✅ 文件下载验证成功")

                        # 清理本地文件
                        for local_file in [temp_file, download_path]:
                            if os.path.exists(local_file):
                                os.unlink(local_file)

                        # 清理远程文件
                        driver.delete_file(access_token, "/NestedContext_Demo")
                        print("   🧹 远程测试文件已清理")

                print("   🔚 内层：准备退出授权会话")

            print("   ✅ 内层：授权会话已正常结束")

        except Exception as e:
            print(f"   ❌ 授权会话异常: {e}")

        print("   🔚 外层：准备退出 BaiduDriver 客户端")

    print("   ✅ 外层：BaiduDriver 客户端已清理")


def example_4_exception_handling():
    """示例4: 异常处理与资源清理"""
    print("\n示例4: 异常处理与资源清理")
    print("-" * 40)

    with BaiduDriver() as driver:
        print("   🚀 客户端已创建")

        try:
            # 故意使用无效的用户ID来触发异常
            print("   ⚠️  故意触发授权异常进行测试...")

            with driver.auth_session(
                target_user_id="INVALID_UID",  # 无效的UID
                file_path="/ExceptionTest",
                timeout=10,  # 短超时时间
            ) as session:
                # 这段代码不会执行，因为授权会失败
                print("   ❌ 这行不应该被执行")

        except Exception as e:
            print(f"   ✅ 异常被正确捕获: {type(e).__name__}")
            print(f"   ℹ️  异常信息: {str(e)[:50]}...")

        print("   🔍 验证客户端仍然可用...")
        version = driver.get_version()
        print(f"   ✅ 客户端正常，版本: {version}")

    print("   ✅ 即使发生异常，资源也被正确清理")


def example_5_manual_cleanup_comparison():
    """示例5: 手动清理与自动清理对比"""
    print("\n示例5: 手动清理与自动清理对比")
    print("-" * 40)

    print("   📋 手动清理方式:")
    try:
        driver = BaiduDriver()
        print("   ✅ 客户端创建成功")

        # 手动执行一些操作
        config = driver.get_config_info()
        print(f"   ⚙️  配置模块: {len(config)}")

        # 手动清理
        driver.cleanup()
        print("   🧹 手动清理完成")

    except Exception as e:
        print(f"   ❌ 手动方式出错: {e}")
        # 如果出错，可能忘记清理

    print("\n   📋 自动清理方式（推荐）:")
    try:
        with BaiduDriver() as driver:
            print("   ✅ 客户端创建成功")

            # 执行相同的操作
            config = driver.get_config_info()
            print(f"   ⚙️  配置模块: {len(config)}")

            # 可能发生异常的代码
            if False:  # 这里不会执行，只是示例
                raise Exception("模拟异常")

        print("   🧹 自动清理完成（即使发生异常也会清理）")

    except Exception as e:
        print(f"   ❌ 自动方式出错: {e}")
        print("   ✅ 但资源仍然被自动清理了")


def main():
    """主函数"""
    print("🔧 BaiduDriver 上下文管理器示例")
    print("=" * 60)

    print("💡 上下文管理器的优势:")
    print("   1. 自动资源管理 - 确保资源被正确清理")
    print("   2. 异常安全 - 即使发生异常也会执行清理")
    print("   3. 代码简洁 - 减少手动管理资源的代码")
    print("   4. 防止资源泄漏 - 避免忘记清理资源")
    print()

    try:
        # 运行各个示例
        example_1_basic_context_manager()
        example_2_auth_session_context()
        example_3_nested_context_managers()
        example_4_exception_handling()
        example_5_manual_cleanup_comparison()

        print(f"\n🎉 所有上下文管理器示例完成！")
        print("\n💡 最佳实践总结:")
        print("   ✅ 总是使用 with 语句来管理 BaiduDriver 实例")
        print("   ✅ 使用 auth_session() 来管理授权会话")
        print("   ✅ 嵌套使用上下文管理器来处理复杂场景")
        print("   ✅ 依赖上下文管理器来处理异常情况下的清理")
        print("   ✅ 避免手动调用 cleanup()，让上下文管理器自动处理")

    except Exception as e:
        print(f"\n💥 示例执行过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
