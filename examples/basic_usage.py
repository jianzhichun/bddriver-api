#!/usr/bin/env python3
"""
BaiduDriver 基础使用示例

演示如何使用 BaiduDriver SDK 进行基本的文件操作
"""

import os
import sys
import time

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver import BaiduDriver
from bddriver.utils.errors import AuthTimeoutError, BaiduDriverError


def main():
    """主函数"""
    print("🚀 BaiduDriver 基础使用示例")
    print("=" * 50)

    # 1. 创建 BaiduDriver 实例
    print("1. 创建 BaiduDriver 客户端...")
    driver = BaiduDriver()
    print(f"   ✅ SDK 版本: {driver.get_version()}")

    try:
        # 2. 发起授权请求
        print("\n2. 发起百度网盘访问授权...")
        print("   📝 请在微信中查看授权请求通知")

        # 替换为实际的 WxPusher UID
        target_user_id = "UID_xxxxxxxxx"  # 请替换为实际的 WxPusher UID

        auth_result = driver.request_access(
            target_user_id=target_user_id,
            file_path="/",  # 请求访问根目录
            description="演示 BaiduDriver SDK 的基本功能，包括文件列表和下载操作",
            requester="BaiduDriver 示例程序",
            timeout=300,  # 5分钟超时
        )

        print(f"   ✅ 授权成功！")
        print(f"   🔑 请求ID: {auth_result['request_id']}")

        # 获取访问令牌
        access_token = auth_result["access_token"]

        # 3. 列出根目录文件
        print("\n3. 列出百度网盘根目录...")
        files = driver.list_files(access_token, path="/", limit=10)

        if files:
            print(f"   📁 找到 {len(files)} 个项目:")
            for file in files[:5]:  # 只显示前5个
                icon = "📁" if file.get("is_dir") else "📄"
                size_info = ""
                if not file.get("is_dir") and file.get("size"):
                    size = file["size"]
                    if size < 1024:
                        size_info = f" ({size} B)"
                    elif size < 1024 * 1024:
                        size_info = f" ({size/1024:.1f} KB)"
                    else:
                        size_info = f" ({size/(1024*1024):.1f} MB)"

                print(f"      {icon} {file.get('filename', 'Unknown')}{size_info}")
        else:
            print("   ℹ️  根目录为空")

        # 4. 演示文件信息获取（如果有文件的话）
        if files:
            first_file = None
            for file in files:
                if not file.get("is_dir"):  # 找第一个文件
                    first_file = file
                    break

            if first_file:
                print(f"\n4. 获取文件详细信息...")
                file_path = first_file.get("path") or f"/{first_file.get('filename')}"
                try:
                    file_info = driver.get_file_info(access_token, file_path)
                    print(f"   📄 文件: {file_info.get('filename')}")
                    print(f"   📏 大小: {file_info.get('size', 0)} 字节")
                    print(f"   🕐 修改时间: {time.ctime(file_info.get('mtime', 0))}")
                    if file_info.get("md5"):
                        print(f"   🔐 MD5: {file_info['md5'][:16]}...")
                except Exception as e:
                    print(f"   ⚠️  获取文件信息失败: {e}")

        # 5. 演示创建文件夹
        print("\n5. 创建测试文件夹...")
        test_folder_path = "/BaiduDriver_Test_" + str(int(time.time()))
        try:
            success = driver.create_folder(access_token, test_folder_path)
            if success:
                print(f"   ✅ 成功创建文件夹: {test_folder_path}")

                # 清理：删除测试文件夹
                print("   🧹 清理测试文件夹...")
                driver.delete_file(access_token, test_folder_path)
                print("   ✅ 测试文件夹已删除")
            else:
                print("   ❌ 创建文件夹失败")
        except Exception as e:
            print(f"   ⚠️  文件夹操作失败: {e}")

        # 6. 显示令牌信息
        print(f"\n6. 授权信息:")
        if auth_result.get("expires_at"):
            expire_time = time.ctime(auth_result["expires_at"])
            print(f"   ⏰ 令牌过期时间: {expire_time}")

        # 检查令牌是否过期
        is_expired = driver.is_token_expired(auth_result)
        print(f"   🔍 令牌状态: {'已过期' if is_expired else '有效'}")

        print("\n🎉 示例程序执行完成！")
        print("\n💡 提示:")
        print("   - 可以将授权结果保存到文件中重复使用")
        print("   - 令牌过期后可以使用 refresh_token 刷新")
        print("   - 更多功能请参考其他示例文件")

    except AuthTimeoutError:
        print("\n⏰ 授权请求超时")
        print("   请确保在微信中及时响应授权请求")

    except BaiduDriverError as e:
        print(f"\n❌ BaiduDriver 错误: {e}")
        if hasattr(e, "error_code") and e.error_code:
            print(f"   错误代码: {e.error_code}")

    except Exception as e:
        print(f"\n💥 未知错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 清理资源
        driver.cleanup()
        print("\n🧹 资源清理完成")


if __name__ == "__main__":
    main()
