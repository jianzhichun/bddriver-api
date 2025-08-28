"""
Command Line Interface for BaiduDriver SDK
Provides convenient CLI commands for file operations and message provider management
🚀 开发模式：实时生效，无需重新安装！
"""

import argparse
import json
import os
import sys
from typing import List, Optional

from . import BaiduDriver, __version__
from .utils.errors import BaiduDriverError
from .utils.logger import get_logger


def setup_logger(verbose: bool = False):
    """设置 CLI 日志"""
    from .utils.logger import reconfigure_logging
    
    # 根据verbose参数重新配置日志级别
    if verbose:
        reconfigure_logging("DEBUG")
    else:
        reconfigure_logging("WARNING")

    return get_logger("cli")


def print_success(message: str):
    """打印成功信息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印错误信息"""
    print(f"❌ {message}", file=sys.stderr)


def print_info(message: str):
    """打印信息"""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """打印警告"""
    print(f"⚠️  {message}")


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = size_bytes / p
    if i == 0:
        return f"{int(s)} {size_names[i]}"
    return f"{s:.1f} {size_names[i]}"


def format_file_list(files: List[dict], detailed: bool = False) -> None:
    """格式化并打印文件列表"""
    if not files:
        print_info("目录为空")
        return

    # 分别处理文件夹和文件
    folders = [f for f in files if f.get("is_dir", False)]
    files_list = [f for f in files if not f.get("is_dir", False)]

    # 打印文件夹
    for folder in folders:
        name = folder.get("filename", "unknown")
        if detailed:
            mtime = folder.get("mtime", 0)
            import datetime

            time_str = (
                datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                if mtime
                else "unknown"
            )
            print(f"📁 {name}/ ({time_str})")
        else:
            print(f"📁 {name}/")

    # 打印文件
    for file in files_list:
        name = file.get("filename", "unknown")
        size = file.get("size", 0)
        size_str = format_file_size(size)

        if detailed:
            mtime = file.get("mtime", 0)
            import datetime

            time_str = (
                datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                if mtime
                else "unknown"
            )
            md5 = file.get("md5", "")[:8] + "..." if file.get("md5") else "N/A"
            print(f"📄 {name} ({size_str}, {time_str}, MD5: {md5})")
        else:
            print(f"📄 {name} ({size_str})")

    print(f"\n📊 总计: {len(folders)} 个文件夹, {len(files_list)} 个文件")


def cmd_device_auth(args) -> Optional[dict]:
    """设备码授权命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        print_info(f"发起设备码授权请求...")
        print_info(f"目标用户: {args.user_id}")
        print_info(f"授权范围: {args.scope}")
        print_info(f"超时时间: {args.timeout}秒")

        driver = BaiduDriver()

        # 发起设备码授权
        auth_result = driver.request_device_access(
            target_user_id=args.user_id, scope=args.scope, timeout=args.timeout
        )

        print_success("设备码授权成功！")

        # 构建 token 数据
        token_data = {
            "access_token": auth_result["access_token"],
            "refresh_token": auth_result.get("refresh_token"),
            "expires_at": auth_result.get("expires_at"),
            "user_id": args.user_id,
            "scope": auth_result.get("scope"),
            "auth_method": auth_result.get("auth_method"),
        }

        # 保存 token 到文件
        save_path = args.save_token or "bddriver_token.json"
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2, ensure_ascii=False)

            if args.save_token:
                print_success(f"Token 已保存到: {save_path}")
            else:
                print_success(f"Token 已自动保存到: {save_path}")
        except Exception as e:
            print_warning(f"Token 保存失败: {e}")
            print_info("您仍可以使用 --token 参数进行后续操作")

        # 显示 token 信息 (脱敏)
        token = auth_result["access_token"]
        masked_token = token[:12] + "..." if len(token) > 12 else token
        print_info(f"访问令牌: {masked_token}")

        if auth_result.get("expires_at"):
            import datetime

            expire_time = datetime.datetime.fromtimestamp(auth_result["expires_at"])
            print_info(f"过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print_info(f"授权方式: {auth_result.get('auth_method', 'device_code')}")
        print_info(f"授权范围: {auth_result.get('scope', 'basic,netdisk')}")

        # 提供后续使用指导
        print("\n🚀 现在您可以使用以下命令操作文件:")
        print(f"  # 查看文件列表")
        print(f"  bddriver ls / --token-file {save_path}")
        print(f"  # 下载文件")
        print(
            f"  bddriver download /remote/file.txt ./local.txt --token-file {save_path}"
        )
        print(f"  # 上传文件")
        print(
            f"  bddriver upload ./local.txt /remote/file.txt --token-file {save_path}"
        )
        print(f"  # 或直接使用 token")
        print(f"  bddriver ls / --token {masked_token}")

        return auth_result

    except BaiduDriverError as e:
        print_error(f"设备码授权失败: {e}")
        return None
    except KeyboardInterrupt:
        print_warning("用户取消操作")
        return None
    except Exception as e:
        logger.error(f"设备码授权异常: {e}")
        print_error(f"设备码授权异常: {e}")
        return None


def cmd_list(args) -> None:
    """列表命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        # 获取 token
        access_token = load_token_from_args(args)
        if not access_token:
            return

        driver = BaiduDriver()

        print_info(f"正在获取文件列表: {args.path}")

        files = driver.list_files(
            access_token=access_token,
            path=args.path,
            limit=args.limit,
            order=args.order,
            desc=(args.sort == "desc"),
        )

        print_success(f"获取文件列表成功 ({len(files)} 项)")
        format_file_list(files, detailed=args.detailed)

    except BaiduDriverError as e:
        print_error(f"获取文件列表失败: {e}")
    except Exception as e:
        logger.error(f"列表命令异常: {e}")
        print_error(f"列表命令异常: {e}")


def cmd_download(args) -> None:
    """下载命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        access_token = load_token_from_args(args)
        if not access_token:
            return

        driver = BaiduDriver()

        # 进度回调
        def progress_callback(progress, current, total):
            if args.progress:
                print(
                    f"\r📥 下载进度: {progress:.1f}% ({format_file_size(current)}/{format_file_size(total)})",
                    end="",
                )

        print_info(f"开始下载: {args.remote_path} -> {args.local_path}")

        success = driver.download_file(
            access_token=access_token,
            remote_path=args.remote_path,
            local_path=args.local_path,
            progress_callback=progress_callback if args.progress else None,
        )

        if args.progress:
            print()  # 换行

        if success:
            print_success(f"下载完成: {args.local_path}")
        else:
            print_error("下载失败")

    except BaiduDriverError as e:
        print_error(f"下载失败: {e}")
    except Exception as e:
        logger.error(f"下载命令异常: {e}")
        print_error(f"下载命令异常: {e}")


def cmd_upload(args) -> None:
    """上传命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        access_token = load_token_from_args(args)
        if not access_token:
            return

        # 检查本地文件
        if not os.path.exists(args.local_path):
            print_error(f"本地文件不存在: {args.local_path}")
            return

        driver = BaiduDriver()

        def progress_callback(progress, current, total):
            if args.progress:
                percent = progress * 100
                print(
                    f"\r📤 上传进度: {percent:.1f}% ({format_file_size(current)}/{format_file_size(total)})",
                    end="",
                )

        print_info(f"开始上传: {args.local_path} -> {args.remote_path}")

        success = driver.upload_file(
            access_token=access_token,
            local_path=args.local_path,
            remote_path=args.remote_path,
            progress_callback=progress_callback if args.progress else None,
        )

        if args.progress:
            print()

        if success:
            print_success(f"上传完成: {args.remote_path}")
        else:
            print_error("上传失败")

    except BaiduDriverError as e:
        print_error(f"上传失败: {e}")
    except Exception as e:
        logger.error(f"上传命令异常: {e}")
        print_error(f"上传命令异常: {e}")


def cmd_mkdir(args) -> None:
    """创建文件夹命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        access_token = load_token_from_args(args)
        if not access_token:
            return

        driver = BaiduDriver()

        print_info(f"开始创建文件夹: {args.path}")

        success = driver.create_folder(access_token=access_token, folder_path=args.path)

        if success:
            print_success(f"文件夹创建成功: {args.path}")
        else:
            print_error("文件夹创建失败")

    except BaiduDriverError as e:
        print_error(f"创建文件夹失败: {e}")
    except Exception as e:
        logger.error(f"创建文件夹命令异常: {e}")
        print_error(f"创建文件夹命令异常: {e}")


def cmd_copy(args) -> None:
    """复制命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        access_token = load_token_from_args(args)
        if not access_token:
            return

        driver = BaiduDriver()

        print_info(f"开始复制: {args.source} -> {args.dest}")

        success = driver.copy_file(
            access_token=access_token,
            source_path=args.source,
            dest_path=args.dest,
            new_name=args.name,
        )

        if success:
            print_success(f"复制成功: {args.source} -> {args.dest}")
        else:
            print_error("复制失败")

    except BaiduDriverError as e:
        print_error(f"复制失败: {e}")
    except Exception as e:
        logger.error(f"复制命令异常: {e}")
        print_error(f"复制命令异常: {e}")


def cmd_move(args) -> None:
    """移动命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        access_token = load_token_from_args(args)
        if not access_token:
            return

        driver = BaiduDriver()

        print_info(f"开始移动: {args.source} -> {args.dest}")

        success = driver.move_file(
            access_token=access_token,
            source_path=args.source,
            dest_path=args.dest,
            new_name=args.name,
        )

        if success:
            print_success(f"移动成功: {args.source} -> {args.dest}")
        else:
            print_error("移动失败")

    except BaiduDriverError as e:
        print_error(f"移动失败: {e}")
    except Exception as e:
        logger.error(f"移动命令异常: {e}")
        print_error(f"移动命令异常: {e}")


def cmd_delete(args) -> None:
    """删除命令"""
    logger = setup_logger(verbose=args.verbose)

    try:
        access_token = load_token_from_args(args)
        if not access_token:
            return

        driver = BaiduDriver()

        # 确认删除（除非使用 --force 参数）
        if not args.force:
            print_warning(f"即将删除: {args.path}")
            confirm = input("确认删除？(y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print_info("删除已取消")
                return

        print_info(f"开始删除: {args.path}")

        success = driver.delete_file(access_token=access_token, file_path=args.path)

        if success:
            print_success(f"删除成功: {args.path}")
        else:
            print_error("删除失败")

    except BaiduDriverError as e:
        print_error(f"删除失败: {e}")
    except Exception as e:
        logger.error(f"删除命令异常: {e}")
        print_error(f"删除命令异常: {e}")


def cmd_info(args) -> None:
    """信息命令"""
    logger = setup_logger(verbose=args.verbose)
    
    print_info(f"BaiduDriver CLI v{__version__}")
    print_info(f"零配置百度网盘授权驱动")
    print()

    # 显示配置信息
    try:
        driver = BaiduDriver()
        config_info = driver.get_config_info()

        print("📋 配置信息:")
        for module, module_config in config_info.items():
            print(f"  {module}:")
            for key, value in module_config.items():
                print(f"    {key}: {value}")

    except Exception as e:
        print_warning(f"无法获取配置信息: {e}")


def cmd_messaging_list(args) -> None:
    """列出所有可用的消息提供者"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        status = manager.get_status()
        
        print_info("📱 消息提供者状态")
        print("=" * 60)
        print(f"📋 配置文件: {status['config_file']}")
        print(f"🎯 默认提供者: {status['default_provider']}")
        print()
        
        for provider_name, provider_status in status['providers'].items():
            status_icon = "✅" if provider_status['enabled'] else "❌"
            config_icon = "✅" if provider_status.get('config_complete', False) else "⚠️"
            
            # 检查是否为内置提供者
            is_builtin = provider_status.get('builtin', False)
            provider_label = f"{provider_name.upper()}{' (内置)' if is_builtin else ''}"
            
            print(f"{status_icon} {provider_label}")
            print(f"   状态: {'启用' if provider_status['enabled'] else '禁用'}")
            
            if is_builtin:
                print(f"   类型: 内置提供者 (无需配置)")
            else:
                print(f"   配置: {'完整' if provider_status.get('config_complete', False) else '不完整'}")
            
            if provider_status['enabled'] and provider_status['config'] and not is_builtin:
                print(f"   配置详情:")
                for key, value in provider_status['config'].items():
                    if key.lower() in ['password', 'secret', 'token']:
                        masked_value = str(value)[:8] + "..." if len(str(value)) > 8 else "***"
                        print(f"     {key}: {masked_value}")
                    else:
                        print(f"     {key}: {value}")
            print()
        
        print("💡 使用 'bddriver messaging config <provider>' 来配置提供者")
        print("💡 使用 'bddriver messaging switch <provider>' 来切换默认提供者")
        print("💡 使用 'bddriver messaging test <provider>' 来测试提供者")
        print("💡 使用 'bddriver messaging subscribe <provider>' 来获取订阅信息")
        print("💡 使用 'bddriver messaging qrcode <provider>' 来创建订阅二维码")
        
    except Exception as e:
        logger.error(f"获取消息提供者状态失败: {e}")
        print_error(f"获取消息提供者状态失败: {e}")


def cmd_messaging_config(args) -> None:
    """配置指定的消息提供者"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        provider_name = args.provider.lower()
        
        if provider_name not in manager.get_available_providers():
            print_error(f"不支持的消息提供者: {args.provider}")
            print_info(f"支持的提供者: {', '.join(manager.get_available_providers())}")
            return
        
        print_info(f"🔧 配置消息提供者: {provider_name.upper()}")
        print("=" * 60)
        
        # 根据提供者类型提示配置项
        if provider_name == "wxpusher":
            print("📱 WxPusher 配置:")
            print("   需要配置 app_token")
            print("   示例: --app-token AT_xxxxxxxxxxxxxxxxxxxxxxxx")
            
            app_token = args.app_token or input("请输入 app_token: ").strip()
            if app_token:
                config = {"app_token": app_token}
                if manager.enable_provider(provider_name, config):
                    print_success(f"WxPusher 配置成功")
                else:
                    print_error("WxPusher 配置失败")
            else:
                print_warning("未提供 app_token，配置取消")
                
        elif provider_name == "dingtalk":
            print("🔔 钉钉配置:")
            print("   需要配置 webhook_url")
            print("   示例: --webhook-url https://oapi.dingtalk.com/robot/send?access_token=xxx")
            
            webhook_url = args.webhook_url or input("请输入 webhook_url: ").strip()
            if webhook_url:
                config = {"webhook_url": webhook_url}
                if args.secret:
                    config["secret"] = args.secret
                if manager.enable_provider(provider_name, config):
                    print_success(f"钉钉配置成功")
                else:
                    print_error("钉钉配置失败")
            else:
                print_warning("未提供 webhook_url，配置取消")
                
        elif provider_name == "wechat_work":
            print("💼 企业微信配置:")
            print("   需要配置 corp_id, agent_id, secret")
            
            corp_id = args.corp_id or input("请输入 corp_id: ").strip()
            agent_id = args.agent_id or input("请输入 agent_id: ").strip()
            secret = args.secret or input("请输入 secret: ").strip()
            
            if corp_id and agent_id and secret:
                config = {
                    "corp_id": corp_id,
                    "agent_id": agent_id,
                    "secret": secret
                }
                if manager.enable_provider(provider_name, config):
                    print_success(f"企业微信配置成功")
                else:
                    print_error("企业微信配置失败")
            else:
                print_warning("配置信息不完整，配置取消")
                
        elif provider_name == "email":
            print("📧 邮件配置:")
            print("   需要配置 smtp_host, username, password")
            
            smtp_host = args.smtp_host or input("请输入 SMTP 服务器地址: ").strip()
            smtp_port = args.smtp_port or input("请输入 SMTP 端口 (默认587): ").strip() or "587"
            username = args.username or input("请输入邮箱地址: ").strip()
            password = args.password or input("请输入邮箱密码/应用密码: ").strip()
            
            if smtp_host and username and password:
                config = {
                    "smtp_host": smtp_host,
                    "smtp_port": int(smtp_port),
                    "username": username,
                    "password": password
                }
                if manager.enable_provider(provider_name, config):
                    print_success(f"邮件配置成功")
                else:
                    print_error("邮件配置失败")
            else:
                print_warning("配置信息不完整，配置取消")
        
        print()
        print("💡 使用 'bddriver messaging test {provider_name}' 来测试配置")
        
    except Exception as e:
        logger.error(f"配置消息提供者失败: {e}")
        print_error(f"配置消息提供者失败: {e}")


def cmd_messaging_switch(args) -> None:
    """切换默认消息提供者"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        provider_name = args.provider.lower()
        
        if provider_name not in manager.get_available_providers():
            print_error(f"不支持的消息提供者: {args.provider}")
            print_info(f"支持的提供者: {', '.join(manager.get_available_providers())}")
            return
        
        current_provider = manager.get_default_provider()
        
        if provider_name == current_provider:
            print_info(f"当前默认提供者已经是 {provider_name.upper()}")
            return
        
        if not manager.config["providers"][provider_name].get("enabled", False):
            print_error(f"消息提供者 {provider_name.upper()} 未启用")
            print_info(f"请先使用 'bddriver messaging config {provider_name}' 进行配置")
            return
        
        if manager.set_default_provider(provider_name):
            print_success(f"默认消息提供者已从 {current_provider.upper()} 切换到 {provider_name.upper()}")
        else:
            print_error(f"切换默认消息提供者失败")
        
    except Exception as e:
        logger.error(f"切换消息提供者失败: {e}")
        print_error(f"切换消息提供者失败: {e}")


def cmd_messaging_test(args) -> None:
    """测试消息提供者"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        provider_name = args.provider.lower()
        
        if provider_name not in manager.get_available_providers():
            print_error(f"不支持的消息提供者: {args.provider}")
            print_info(f"支持的提供者: {', '.join(manager.get_available_providers())}")
            return
        
        if not manager.config["providers"][provider_name].get("enabled", False):
            print_error(f"消息提供者 {provider_name.upper()} 未启用")
            print_info(f"请先使用 'bddriver messaging config {provider_name}' 进行配置")
            return
        
        print_info(f"🧪 测试消息提供者: {provider_name.upper()}")
        print("=" * 60)
        
        # 检查配置是否完整
        provider_status = manager.get_status()["providers"][provider_name]
        if not provider_status.get("config_complete", False):
            print_warning(f"消息提供者 {provider_name.upper()} 配置不完整")
            print_info("请检查配置信息")
            return
        
        print("📤 正在发送测试消息...")
        
        if manager.test_provider(provider_name):
            print_success(f"消息提供者 {provider_name.upper()} 测试成功！")
            print("✅ 配置正确，可以正常使用")
        else:
            print_error(f"消息提供者 {provider_name.upper()} 测试失败")
            print("❌ 请检查配置信息或网络连接")
        
    except Exception as e:
        logger.error(f"测试消息提供者失败: {e}")
        print_error(f"测试消息提供者失败: {e}")


def cmd_messaging_subscribe(args) -> None:
    """获取消息提供者订阅信息"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        provider_name = args.provider.lower()
        
        if provider_name not in manager.get_available_providers():
            print_error(f"不支持的消息提供者: {args.provider}")
            print_info(f"支持的提供者: {', '.join(manager.get_available_providers())}")
            return
        
        print_info(f"📱 获取订阅信息: {provider_name.upper()}")
        print("=" * 60)
        
        # 获取订阅信息
        subscribe_info = manager.get_subscription_info(provider_name)
        
        if subscribe_info.get("success"):
            print_success("✅ 订阅信息获取成功")
            print()
            
            if provider_name == "wxpusher":
                print("🔗 订阅地址:")
                print(f"   {subscribe_info.get('subscribe_url', 'N/A')}")
                print()
                print("📱 订阅二维码:")
                print(f"   {subscribe_info.get('qr_code', 'N/A')}")
                print()
                print("🔑 二维码Code:")
                print(f"   {subscribe_info.get('qrcode_code', 'N/A')}")
                print()
                print("⏰ 有效期:")
                print(f"   {subscribe_info.get('expires_in', 'N/A')} 秒")
                print()
                print("📋 应用名称:")
                print(f"   {subscribe_info.get('app_name', 'N/A')}")
                print()
                
                qrcode_code = subscribe_info.get('qrcode_code')
                
                # 自动轮询扫码状态
                if qrcode_code:
                    print("🔄 自动轮询扫码状态...")
                    print("💡 用户扫码后会自动获取UID")
                    print("💡 按 Ctrl+C 可以随时退出轮询")
                    print()
                    
                    try:
                        poll_result = manager.poll_scan_status(qrcode_code, provider_name, 10, 999999)
                        
                        if poll_result.get("success") and poll_result.get("scanned"):
                            print()
                            print_success("🎉 轮询成功！用户已扫码完成订阅！")
                            print("📋 扫码信息:")
                            print(f"   UID: {poll_result.get('uid', 'N/A')}")
                            print(f"   扫码时间: {poll_result.get('scan_time', 'N/A')}")
                            if poll_result.get('extra'):
                                print(f"   额外参数: {poll_result.get('extra', 'N/A')}")
                            print(f"   轮询次数: {poll_result.get('attempts', 'N/A')}")
                            print(f"   总耗时: {poll_result.get('total_time', 'N/A')} 秒")
                            print()
                            print("💡 现在可以使用此UID发送消息了！")
                        else:
                            print(f"❌ 轮询失败: {poll_result.get('msg', '未知错误')}")
                    except KeyboardInterrupt:
                        print()
                        print_warning("⚠️ 轮询被用户中断")
                        print("💡 可以使用 'bddriver messaging poll <code>' 手动轮询")
            else:
                print("📋 订阅信息:")
                for key, value in subscribe_info.items():
                    if key != "success" and key != "data":
                        print(f"   {key}: {value}")
        else:
            print_error(f"❌ 获取订阅信息失败: {subscribe_info.get('msg', '未知错误')}")
            
    except Exception as e:
        logger.error(f"获取订阅信息失败: {e}")
        print_error(f"获取订阅信息失败: {e}")


def cmd_messaging_poll(args) -> None:
    """轮询扫码状态直到获得用户UID"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        provider_name = args.provider.lower()
        
        if provider_name not in manager.get_available_providers():
            print_error(f"不支持的消息提供者: {args.provider}")
            print_info(f"支持的提供者: {', '.join(manager.get_available_providers())}")
            return
        
        print_info(f"🔄 轮询扫码状态: {provider_name.upper()}")
        print("=" * 60)
        print(f"🔑 二维码Code: {args.code}")
        print(f"⏰ 轮询间隔: {args.interval} 秒")
        print(f"🔢 最大次数: {args.max_attempts} 次")
        print()
        
        poll_result = manager.poll_scan_status(args.code, provider_name, args.interval, args.max_attempts)
        
        if poll_result.get("success") and poll_result.get("scanned"):
            print()
            print_success("🎉 轮询成功！用户已扫码完成订阅！")
            print("📋 扫码信息:")
            print(f"   UID: {poll_result.get('uid', 'N/A')}")
            print(f"   扫码时间: {poll_result.get('scan_time', 'N/A')}")
            if poll_result.get('extra'):
                print(f"   额外参数: {poll_result.get('extra', 'N/A')}")
            print(f"   轮询次数: {poll_result.get('attempts', 'N/A')}")
            print(f"   总耗时: {poll_result.get('total_time', 'N/A')} 秒")
            print()
            print("💡 现在可以使用此UID发送消息了！")
        else:
            print_error(f"❌ 轮询失败: {poll_result.get('msg', '未知错误')}")
            
    except Exception as e:
        logger.error(f"轮询扫码状态失败: {e}")
        print_error(f"轮询扫码状态失败: {e}")


def cmd_messaging_disable(args) -> None:
    """禁用消息提供者"""
    logger = setup_logger(verbose=args.verbose)
    
    try:
        from .messaging import get_messaging_manager
        
        manager = get_messaging_manager()
        provider_name = args.provider.lower()
        
        if provider_name not in manager.get_available_providers():
            print_error(f"不支持的消息提供者: {args.provider}")
            print_info(f"支持的提供者: {', '.join(manager.get_available_providers())}")
            return
        
        if not manager.config["providers"][provider_name].get("enabled", False):
            print_info(f"消息提供者 {provider_name.upper()} 已经是禁用状态")
            return
        
        if manager.disable_provider(provider_name):
            print_success(f"消息提供者 {provider_name.upper()} 已禁用")
        else:
            print_error(f"禁用消息提供者失败")
        
    except Exception as e:
        logger.error(f"禁用消息提供者失败: {e}")
        print_error(f"禁用消息提供者失败: {e}")


def load_token_from_args(args) -> Optional[str]:
    """从参数中加载 token"""

    # 优先使用命令行参数中的 token
    if hasattr(args, "token") and args.token:
        return args.token

    # 从文件加载 token
    if hasattr(args, "token_file") and args.token_file:
        try:
            with open(args.token_file, "r", encoding="utf-8") as f:
                token_data = json.load(f)
                return token_data.get("access_token")
        except Exception as e:
            print_error(f"加载 token 文件失败: {e}")
            return None

    # 尝试从默认位置加载
    default_token_file = "bddriver_token.json"
    if os.path.exists(default_token_file):
        try:
            with open(default_token_file, "r", encoding="utf-8") as f:
                token_data = json.load(f)
                return token_data.get("access_token")
        except:
            pass

    print_error("未找到访问令牌，请先执行授权操作或使用 --token 参数")
    print_info("提示: 使用 'bddriver auth' 命令进行授权")
    return None


def main():
    """CLI 主入口函数"""
    parser = argparse.ArgumentParser(
        prog="bddriver",
        description="BaiduDriver - 零配置百度网盘授权驱动",
        epilog="更多信息请访问: https://github.com/your-repo/bddriver-api",
    )

    parser.add_argument(
        "--version", action="version", version=f"bddriver {__version__}"
    )
    
    # 全局选项
    parser.add_argument(
        "--verbose", "-v", action="store_true", 
        help="显示详细日志信息（DEBUG级别）"
    )

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 设备码授权命令（主命令）
    auth_parser = subparsers.add_parser("auth", help="发起设备码授权请求")
    auth_parser.add_argument("user_id", help="目标用户的 WxPusher UID")
    auth_parser.add_argument(
        "--scope", default="basic,netdisk", help="授权范围 (默认: basic,netdisk)"
    )
    auth_parser.add_argument(
        "--timeout", type=int, default=300, help="授权超时时间（秒）"
    )
    auth_parser.add_argument(
        "--save-token", help="保存 token 到指定文件 (默认: bddriver_token.json)"
    )
    auth_parser.set_defaults(func=cmd_device_auth)

    # 列表命令
    list_parser = subparsers.add_parser("ls", help="列出文件和文件夹")
    list_parser.add_argument("path", nargs="?", default="/", help="目录路径")
    list_parser.add_argument("--token", help="访问令牌")
    list_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    list_parser.add_argument("--limit", type=int, default=100, help="返回数量限制")
    list_parser.add_argument(
        "--order", choices=["time", "size", "name"], default="time", help="排序方式"
    )
    list_parser.add_argument(
        "--sort", choices=["desc", "asc"], default="desc", help="排序顺序"
    )
    list_parser.add_argument(
        "-l", "--detailed", action="store_true", help="显示详细信息"
    )
    list_parser.set_defaults(func=cmd_list)

    # 下载命令
    download_parser = subparsers.add_parser("download", help="下载文件")
    download_parser.add_argument("remote_path", help="远程文件路径")
    download_parser.add_argument("local_path", help="本地保存路径")
    download_parser.add_argument("--token", help="访问令牌")
    download_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    download_parser.add_argument("--progress", action="store_true", help="显示进度条")
    download_parser.set_defaults(func=cmd_download)

    # 上传命令
    upload_parser = subparsers.add_parser("upload", help="上传文件")
    upload_parser.add_argument("local_path", help="本地文件路径")
    upload_parser.add_argument("remote_path", help="远程保存路径")
    upload_parser.add_argument("--token", help="访问令牌")
    upload_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    upload_parser.add_argument("--progress", action="store_true", help="显示进度条")
    upload_parser.set_defaults(func=cmd_upload)

    # 删除命令
    delete_parser = subparsers.add_parser("delete", help="删除文件或文件夹")
    delete_parser.add_argument("path", help="要删除的文件或文件夹路径")
    delete_parser.add_argument("--token", help="访问令牌")
    delete_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    delete_parser.add_argument(
        "--force", action="store_true", help="强制删除（不提示确认）"
    )
    delete_parser.set_defaults(func=cmd_delete)

    # 创建文件夹命令
    mkdir_parser = subparsers.add_parser("mkdir", help="创建文件夹")
    mkdir_parser.add_argument("path", help="要创建的文件夹路径")
    mkdir_parser.add_argument("--token", help="访问令牌")
    mkdir_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    mkdir_parser.set_defaults(func=cmd_mkdir)

    # 复制命令
    copy_parser = subparsers.add_parser("copy", help="复制文件或文件夹")
    copy_parser.add_argument("source", help="源文件或文件夹路径")
    copy_parser.add_argument("dest", help="目标目录路径")
    copy_parser.add_argument("--name", help="新名称（可选）")
    copy_parser.add_argument("--token", help="访问令牌")
    copy_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    copy_parser.set_defaults(func=cmd_copy)

    # 移动命令
    move_parser = subparsers.add_parser("move", help="移动文件或文件夹")
    move_parser.add_argument("source", help="源文件或文件夹路径")
    move_parser.add_argument("dest", help="目标目录路径")
    move_parser.add_argument("--name", help="新名称（可选）")
    move_parser.add_argument("--token", help="访问令牌")
    move_parser.add_argument(
        "--token-file", help="token 文件路径 (默认: bddriver_token.json)"
    )
    move_parser.set_defaults(func=cmd_move)

    # 信息命令
    info_parser = subparsers.add_parser("info", help="显示版本和配置信息")
    info_parser.set_defaults(func=cmd_info)

    # 消息提供者管理命令
    messaging_parser = subparsers.add_parser("messaging", help="管理消息提供者")
    messaging_subparsers = messaging_parser.add_subparsers(dest="messaging_command", help="消息提供者命令")
    
    # 列出所有消息提供者
    list_parser = messaging_subparsers.add_parser("list", help="列出所有可用的消息提供者")
    list_parser.set_defaults(func=cmd_messaging_list)
    
    # 配置消息提供者
    config_parser = messaging_subparsers.add_parser("config", help="配置指定的消息提供者")
    config_parser.add_argument("provider", help="提供者名称")
    config_parser.add_argument("--app-token", help="WxPusher app_token")
    config_parser.add_argument("--webhook-url", help="钉钉 webhook_url")
    config_parser.add_argument("--secret", help="钉钉 secret (可选)")
    config_parser.add_argument("--corp-id", help="企业微信 corp_id")
    config_parser.add_argument("--agent-id", help="企业微信 agent_id")
    config_parser.add_argument("--smtp-host", help="邮件 SMTP 服务器地址")
    config_parser.add_argument("--smtp-port", help="邮件 SMTP 端口 (默认587)")
    config_parser.add_argument("--username", help="邮件 用户名")
    config_parser.add_argument("--password", help="邮件 密码/应用密码")
    config_parser.set_defaults(func=cmd_messaging_config)
    
    # 切换默认消息提供者
    switch_parser = messaging_subparsers.add_parser("switch", help="切换默认消息提供者")
    switch_parser.add_argument("provider", help="提供者名称")
    switch_parser.set_defaults(func=cmd_messaging_switch)
    
    # 测试消息提供者
    test_parser = messaging_subparsers.add_parser("test", help="测试消息提供者")
    test_parser.add_argument("provider", help="提供者名称")
    test_parser.set_defaults(func=cmd_messaging_test)
    
    # 获取订阅信息
    subscribe_parser = messaging_subparsers.add_parser("subscribe", help="获取消息提供者订阅信息")
    subscribe_parser.add_argument("provider", nargs="?", default="wxpusher", help="提供者名称 (默认: wxpusher)")
    subscribe_parser.set_defaults(func=cmd_messaging_subscribe)
    
    # 轮询扫码状态
    poll_parser = messaging_subparsers.add_parser("poll", help="轮询扫码状态直到获得用户UID")
    poll_parser.add_argument("code", help="二维码的code参数")
    poll_parser.add_argument("provider", nargs="?", default="wxpusher", help="提供者名称 (默认: wxpusher)")
    poll_parser.add_argument("--interval", "-i", type=int, default=15, help="轮询间隔，单位秒 (默认: 15)")
    poll_parser.add_argument("--max-attempts", "-m", type=int, default=120, help="最大轮询次数 (默认: 120)")
    poll_parser.set_defaults(func=cmd_messaging_poll)
    
    # 禁用消息提供者
    disable_parser = messaging_subparsers.add_parser("disable", help="禁用消息提供者")
    disable_parser.add_argument("provider", help="提供者名称")
    disable_parser.set_defaults(func=cmd_messaging_disable)
    
    # 设置默认函数
    messaging_parser.set_defaults(func=lambda args: print_error("请指定一个消息提供者命令 (list, config, switch, test, subscribe, poll, disable)"))

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    try:
        args.func(args)
    except KeyboardInterrupt:
        print_warning("操作被用户取消")
        sys.exit(1)
    except Exception as e:
        print_error(f"命令执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
