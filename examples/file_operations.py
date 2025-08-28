#!/usr/bin/env python3
"""
BaiduDriver 文件操作示例

演示如何使用 BaiduDriver SDK 进行文件的上传、下载、复制、移动等操作
"""

import json
import os
import sys
import tempfile
import time

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from bddriver import BaiduDriver
from bddriver.utils.errors import BaiduDriverError, FileOperationError


def create_test_file(content="Hello, BaiduDriver!", filename="test.txt"):
    """创建测试文件"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def progress_callback(progress, current, total):
    """进度回调函数"""
    percent = progress * 100
    current_mb = current / (1024 * 1024)
    total_mb = total / (1024 * 1024)

    bar_length = 30
    filled_length = int(bar_length * progress)
    bar = "█" * filled_length + "▒" * (bar_length - filled_length)

    print(
        f"\r   📊 [{bar}] {percent:5.1f}% ({current_mb:.2f}/{total_mb:.2f} MB)", end=""
    )


def load_saved_token():
    """加载保存的令牌"""
    token_file = "bddriver_token.json"
    if os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                token_data = json.load(f)
                return token_data.get("access_token")
        except Exception:
            pass
    return None


def save_token(auth_result):
    """保存令牌到文件"""
    token_data = {
        "access_token": auth_result["access_token"],
        "refresh_token": auth_result.get("refresh_token"),
        "expires_at": auth_result.get("expires_at"),
        "saved_time": time.time(),
    }

    with open("bddriver_token.json", "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    print("📁 BaiduDriver 文件操作示例")
    print("=" * 60)

    # 创建 BaiduDriver 实例
    driver = BaiduDriver()

    try:
        # 尝试加载保存的令牌
        access_token = load_saved_token()

        if not access_token:
            print("🔑 未找到保存的令牌，开始授权流程...")

            # 替换为实际的 WxPusher UID
            target_user_id = "UID_xxxxxxxxx"  # 请替换为实际的 WxPusher UID

            auth_result = driver.request_access(
                target_user_id=target_user_id,
                file_path="/BaiduDriver_Demo",
                description="演示文件操作功能：上传、下载、复制、移动文件",
                requester="文件操作示例程序",
                timeout=300,
            )

            access_token = auth_result["access_token"]
            save_token(auth_result)
            print("✅ 授权成功，令牌已保存")
        else:
            print("🔑 使用保存的令牌")

        # 创建演示目录
        demo_folder = "/BaiduDriver_Demo"
        print(f"\n📁 创建演示目录: {demo_folder}")

        try:
            driver.create_folder(access_token, demo_folder)
            print("✅ 演示目录创建成功")
        except FileOperationError as e:
            if "already exists" in str(e).lower() or "目录已存在" in str(e):
                print("ℹ️  演示目录已存在，继续使用")
            else:
                raise

        # 1. 文件上传操作
        print(f"\n1. 📤 文件上传操作")
        print("-" * 30)

        # 创建测试文件
        test_content = f"""BaiduDriver SDK 测试文件
创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
文件大小测试内容: {'A' * 100}
中文内容测试: 这是一个测试文件
"""

        local_file = create_test_file(test_content, "bddriver_test.txt")
        remote_path = f"{demo_folder}/bddriver_test.txt"

        print(f"   本地文件: {local_file}")
        print(f"   远程路径: {remote_path}")
        print("   开始上传...")

        success = driver.upload_file(
            access_token, local_file, remote_path, progress_callback=progress_callback
        )

        print()  # 换行
        if success:
            print("   ✅ 文件上传成功")
        else:
            print("   ❌ 文件上传失败")
            return

        # 2. 文件列表操作
        print(f"\n2. 📋 查看演示目录")
        print("-" * 30)

        files = driver.list_files(access_token, demo_folder)

        if files:
            print(f"   找到 {len(files)} 个项目:")
            for file in files:
                icon = "📁" if file.get("is_dir") else "📄"
                name = file.get("filename", "Unknown")
                size = file.get("size", 0)

                if not file.get("is_dir"):
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    print(f"      {icon} {name} ({size_str})")
                else:
                    print(f"      {icon} {name}/")

        # 3. 文件下载操作
        print(f"\n3. 📥 文件下载操作")
        print("-" * 30)

        download_path = os.path.join(tempfile.gettempdir(), "downloaded_test.txt")
        print(f"   下载到: {download_path}")
        print("   开始下载...")

        success = driver.download_file(
            access_token,
            remote_path,
            download_path,
            progress_callback=progress_callback,
        )

        print()  # 换行
        if success:
            print("   ✅ 文件下载成功")

            # 验证下载的文件
            with open(download_path, "r", encoding="utf-8") as f:
                downloaded_content = f.read()

            if "BaiduDriver SDK 测试文件" in downloaded_content:
                print("   ✅ 文件内容验证成功")
            else:
                print("   ⚠️  文件内容验证失败")
        else:
            print("   ❌ 文件下载失败")

        # 4. 文件复制操作
        print(f"\n4. 📋 文件复制操作")
        print("-" * 30)

        copy_path = f"{demo_folder}/bddriver_test_copy.txt"
        print(f"   复制到: {copy_path}")

        success = driver.copy_file(
            access_token, remote_path, demo_folder, "bddriver_test_copy.txt"
        )

        if success:
            print("   ✅ 文件复制成功")
        else:
            print("   ❌ 文件复制失败")

        # 5. 文件移动操作
        print(f"\n5. 🚚 文件移动操作")
        print("-" * 30)

        # 创建子目录
        sub_folder = f"{demo_folder}/subfolder"
        try:
            driver.create_folder(access_token, sub_folder)
            print(f"   ✅ 创建子目录: {sub_folder}")
        except FileOperationError as e:
            if "already exists" in str(e).lower():
                print(f"   ℹ️  子目录已存在: {sub_folder}")
            else:
                print(f"   ⚠️  创建子目录失败: {e}")

        # 移动复制的文件到子目录
        move_dest = f"{demo_folder}/subfolder/moved_file.txt"
        success = driver.move_file(
            access_token, copy_path, sub_folder, "moved_file.txt"
        )

        if success:
            print("   ✅ 文件移动成功")
        else:
            print("   ❌ 文件移动失败")

        # 6. 查看最终目录结构
        print(f"\n6. 🌳 最终目录结构")
        print("-" * 30)

        def show_directory(path, prefix=""):
            """递归显示目录结构"""
            try:
                files = driver.list_files(access_token, path)
                for file in files:
                    icon = "📁" if file.get("is_dir") else "📄"
                    name = file.get("filename", "Unknown")
                    print(f"{prefix}{icon} {name}")

                    if file.get("is_dir"):
                        file_path = file.get("path") or f"{path}/{name}"
                        show_directory(file_path, prefix + "  ")
            except Exception as e:
                print(f"{prefix}❌ 无法读取目录: {e}")

        show_directory(demo_folder)

        # 7. 清理演示文件
        print(f"\n7. 🧹 清理演示文件")
        print("-" * 30)

        cleanup_choice = input("是否清理演示文件？(y/N): ").lower().strip()

        if cleanup_choice == "y":
            try:
                # 删除整个演示目录
                success = driver.delete_file(access_token, demo_folder)
                if success:
                    print("   ✅ 演示目录清理完成")
                else:
                    print("   ⚠️  目录清理可能不完整")
            except Exception as e:
                print(f"   ⚠️  清理过程中出现错误: {e}")
        else:
            print("   ℹ️  保留演示文件，可稍后手动清理")

        # 清理本地临时文件
        for temp_file in [local_file, download_path]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

        print("\n🎉 文件操作示例完成！")
        print("\n💡 操作总结:")
        print("   ✅ 文件上传 - 将本地文件上传到百度网盘")
        print("   ✅ 文件下载 - 从百度网盘下载文件到本地")
        print("   ✅ 文件复制 - 在网盘中复制文件")
        print("   ✅ 文件移动 - 在网盘中移动文件")
        print("   ✅ 目录创建 - 创建新的文件夹")
        print("   ✅ 目录列表 - 查看目录内容")

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
        print("\n🧹 SDK 资源清理完成")


if __name__ == "__main__":
    main()
