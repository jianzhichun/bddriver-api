#!/usr/bin/env python3
"""
BaiduDriver CLI 演示脚本

展示如何使用命令行界面进行各种操作
"""

import os
import subprocess
import sys
import tempfile
import time

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)


def run_cli_command(cmd, description="", expect_error=False):
    """运行 CLI 命令并显示结果"""
    print(f"\n📟 {description}")
    print(f"   命令: {cmd}")
    print("   " + "-" * 40)

    try:
        # 使用 python -m bddriver.cli 来运行 CLI
        full_cmd = f"python -m bddriver.cli {cmd}"

        result = subprocess.run(
            full_cmd.split(),
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30,
        )

        if result.stdout:
            for line in result.stdout.split("\n"):
                if line.strip():
                    print(f"   {line}")

        if result.stderr and not expect_error:
            for line in result.stderr.split("\n"):
                if line.strip():
                    print(f"   ⚠️  {line}")

        if result.returncode != 0 and not expect_error:
            print(f"   ❌ 命令执行失败，返回码: {result.returncode}")
        elif result.returncode == 0:
            print(f"   ✅ 命令执行成功")

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print("   ⏰ 命令执行超时")
        return False, "", ""
    except Exception as e:
        print(f"   💥 执行异常: {e}")
        return False, "", ""


def create_demo_file():
    """创建演示文件"""
    content = f"""BaiduDriver CLI 演示文件
创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
这是用于演示 CLI 功能的测试文件。

文件内容：
- 支持中文字符
- 支持多行文本
- 文件大小约 {len('这是一些占位内容 ' * 20)} 字节

{'演示内容 ' * 20}
"""

    temp_file = os.path.join(tempfile.gettempdir(), "bddriver_cli_demo.txt")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)

    return temp_file


def main():
    """主函数"""
    print("🖥️  BaiduDriver CLI 演示")
    print("=" * 60)

    print("💡 本演示将展示 CLI 工具的各种功能")
    print("   注意：某些命令需要有效的授权令牌才能工作")
    print()

    # 1. 显示版本和帮助信息
    run_cli_command("--version", "显示版本信息")
    run_cli_command("--help", "显示帮助信息")

    # 2. 显示配置信息
    run_cli_command("info", "显示配置和版本信息")

    # 3. 演示授权命令（需要用户输入）
    print(f"\n📝 授权命令演示")
    print("   " + "-" * 40)
    print("   授权命令需要真实的 WxPusher UID，这里仅显示用法")
    print("   示例命令:")
    print("     python -m bddriver.cli auth UID_xxxxxxxxx")
    print("     python -m bddriver.cli auth UID_xxxxxxxxx --path /MyFiles")
    print("     python -m bddriver.cli auth UID_xxxxxxxxx --description '访问我的文档'")
    print("     python -m bddriver.cli auth UID_xxxxxxxxx --save-token token.json")

    # 4. 演示文件列表命令（需要令牌）
    print(f"\n📋 文件列表命令演示")
    print("   " + "-" * 40)
    print("   文件列表命令需要有效的访问令牌，这里仅显示用法")
    print("   示例命令:")
    print("     python -m bddriver.cli ls")
    print("     python -m bddriver.cli ls /MyDocuments")
    print("     python -m bddriver.cli ls --token YOUR_TOKEN")
    print("     python -m bddriver.cli ls --token-file token.json")
    print("     python -m bddriver.cli ls --detailed")
    print("     python -m bddriver.cli ls --limit 50 --order size")

    # 5. 演示下载命令（需要令牌）
    print(f"\n📥 文件下载命令演示")
    print("   " + "-" * 40)
    print("   下载命令需要有效的访问令牌，这里仅显示用法")
    print("   示例命令:")
    print("     python -m bddriver.cli download /remote/file.txt ./local/file.txt")
    print("     python -m bddriver.cli download /remote/file.txt ./local/ --progress")
    print(
        "     python -m bddriver.cli download /remote/file.txt ./local/ --token YOUR_TOKEN"
    )

    # 6. 演示上传命令（需要令牌和文件）
    demo_file = create_demo_file()

    print(f"\n📤 文件上传命令演示")
    print("   " + "-" * 40)
    print(f"   已创建演示文件: {demo_file}")
    print("   上传命令需要有效的访问令牌，这里仅显示用法")
    print("   示例命令:")
    print(f"     python -m bddriver.cli upload {demo_file} /remote/demo.txt")
    print(f"     python -m bddriver.cli upload {demo_file} /remote/ --progress")
    print(f"     python -m bddriver.cli upload {demo_file} /remote/ --token YOUR_TOKEN")

    # 7. 演示错误处理
    print(f"\n❌ 错误处理演示")
    print("   " + "-" * 40)

    # 无效的命令
    run_cli_command("invalid_command", "运行无效命令", expect_error=True)

    # 缺少必需参数的命令
    run_cli_command("auth", "缺少用户ID的授权命令", expect_error=True)

    # 8. 高级用法示例
    print(f"\n🚀 高级用法示例")
    print("   " + "-" * 40)

    print("   批量操作示例:")
    print("     # 批量下载")
    print("     for file in file1.txt file2.txt file3.txt; do")
    print('       python -m bddriver.cli download "/MyFiles/$file" "./downloads/$file"')
    print("     done")
    print()

    print("   脚本集成示例:")
    print("     #!/bin/bash")
    print("     # 自动备份脚本")
    print("     TOKEN=$(cat token.json | jq -r '.access_token')")
    print("     python -m bddriver.cli upload backup.tar.gz /Backups/ --token $TOKEN")
    print("     if [ $? -eq 0 ]; then")
    print("       echo '备份上传成功'")
    print("     else")
    print("       echo '备份上传失败'")
    print("     fi")
    print()

    print("   配置文件管理:")
    print("     # 使用环境变量")
    print("     export BDDRIVER_LOG_LEVEL=DEBUG")
    print("     python -m bddriver.cli info")
    print()

    print("   进度监控:")
    print("     python -m bddriver.cli upload large_file.zip /Upload/ --progress")
    print("     python -m bddriver.cli download /large_file.zip ./ --progress")

    # 9. 最佳实践建议
    print(f"\n💡 CLI 使用最佳实践")
    print("   " + "-" * 60)

    practices = [
        "🔐 令牌安全 - 将访问令牌保存到文件中，避免在命令行中明文使用",
        "📁 路径规范 - 使用绝对路径避免路径混淆",
        "📊 进度显示 - 对于大文件传输，使用 --progress 选项监控进度",
        "🔍 详细输出 - 使用 --detailed 选项获取文件的完整信息",
        "⚠️  错误处理 - 检查命令的返回码，在脚本中进行适当的错误处理",
        "🔄 批量操作 - 结合 shell 脚本进行批量文件操作",
        "📝 日志调试 - 使用环境变量 BDDRIVER_LOG_LEVEL 控制日志输出级别",
        "⏱️  超时设置 - 对于网络不稳定的环境，适当增加超时时间",
        "🧹 定期清理 - 定期清理过期的令牌文件",
    ]

    for i, practice in enumerate(practices, 1):
        print(f"   {i:2d}. {practice}")

    # 清理演示文件
    if os.path.exists(demo_file):
        os.unlink(demo_file)
        print(f"\n🧹 演示文件已清理: {demo_file}")

    print(f"\n🎉 CLI 演示完成！")
    print("\n📚 更多信息:")
    print("   - 使用 python -m bddriver.cli --help 查看完整帮助")
    print("   - 使用 python -m bddriver.cli COMMAND --help 查看子命令帮助")
    print("   - 查看项目文档了解更多高级用法")


if __name__ == "__main__":
    main()
