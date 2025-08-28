#!/usr/bin/env python3
"""钩子系统使用示例

展示如何使用钩子在关键操作前执行自定义逻辑，如支付验证、权限检查等
"""

import time
from bddriver import BaiduDriver
from bddriver.hooks import (
    HookEvent, HookContext, HookResult, 
    hook, global_hook, register_hook, execute_hooks
)


def verify_payment(user_id: str, amount: float) -> bool:
    """模拟支付验证
    
    Args:
        user_id: 用户ID
        amount: 支付金额
        
    Returns:
        支付是否成功
    """
    print(f"🔍 验证用户 {user_id} 的支付: ¥{amount}")
    
    # 模拟支付验证逻辑
    # 在实际应用中，这里会调用支付系统API
    if amount > 0 and user_id.startswith("UID_"):
        print("✅ 支付验证成功")
        return True
    else:
        print("❌ 支付验证失败")
        return False


def check_user_permission(user_id: str, operation: str) -> bool:
    """模拟用户权限检查
    
    Args:
        user_id: 用户ID
        operation: 操作类型
        
    Returns:
        是否有权限
    """
    print(f"🔐 检查用户 {user_id} 的 {operation} 权限")
    
    # 模拟权限检查逻辑
    # 在实际应用中，这里会查询用户权限数据库
    if user_id.startswith("UID_"):
        print("✅ 权限检查通过")
        return True
    else:
        print("❌ 权限检查失败")
        return False


def log_operation(context: HookContext) -> HookResult:
    """记录操作日志的钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    event = context.event
    data = context.data
    
    print(f"📝 钩子日志: {event.value}")
    print(f"   数据: {data}")
    
    return HookResult.success()


# 使用装饰器注册钩子
@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
def payment_verification_hook(context: HookContext) -> HookResult:
    """授权请求前的支付验证钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("💰 执行支付验证钩子...")
    
    user_id = context.data.get("target_user_id")
    amount = context.data.get("payment_amount", 0.0)
    
    if not verify_payment(user_id, amount):
        return HookResult.stop("支付验证失败，无法继续授权")
    
    return HookResult.success()


@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=2)
def permission_check_hook(context: HookContext) -> HookResult:
    """授权请求前的权限检查钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("🔐 执行权限检查钩子...")
    
    user_id = context.data.get("target_user_id")
    operation = "auth_request"
    
    if not check_user_permission(user_id, operation):
        return HookResult.stop("权限不足，无法继续授权")
    
    return HookResult.success()


@hook(HookEvent.AFTER_AUTH_SUCCESS, priority=1)
def auth_success_hook(context: HookContext) -> HookResult:
    """授权成功后的钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("🎉 授权成功钩子执行...")
    
    user_id = context.data.get("target_user_id")
    auth_result = context.data.get("auth_result", {})
    
    print(f"   用户 {user_id} 授权成功")
    print(f"   访问令牌: {auth_result.get('access_token', 'N/A')[:20]}...")
    
    return HookResult.success()


@hook(HookEvent.BEFORE_FILE_OPERATION, priority=1)
def file_operation_hook(context: HookContext) -> HookResult:
    """文件操作前的钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("📁 执行文件操作钩子...")
    
    operation = context.data.get("operation")
    path = context.data.get("path")
    
    print(f"   操作类型: {operation}")
    print(f"   操作路径: {path}")
    
    # 可以在这里添加文件操作的限制逻辑
    if path.startswith("/private/") and operation == "list_files":
        return HookResult.stop("访问私有目录需要特殊权限")
    
    return HookResult.success()


# 使用函数注册钩子
def rate_limit_hook(context: HookContext) -> HookResult:
    """速率限制钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("⏱️  执行速率限制检查...")
    
    # 模拟速率限制检查
    # 在实际应用中，这里会检查用户的API调用频率
    current_time = time.time()
    user_id = context.data.get("target_user_id", "unknown")
    
    # 简单的速率限制：每秒最多1次调用
    if hasattr(rate_limit_hook, '_last_call') and \
       current_time - rate_limit_hook._last_call.get(user_id, 0) < 1:
        return HookResult.stop("请求过于频繁，请稍后再试")
    
    if not hasattr(rate_limit_hook, '_last_call'):
        rate_limit_hook._last_call = {}
    
    rate_limit_hook._last_call[user_id] = current_time
    
    return HookResult.success()


def demo_hooks():
    """演示钩子系统的使用"""
    print("🎯 钩子系统演示")
    print("=" * 50)
    
    # 注册速率限制钩子
    register_hook(HookEvent.BEFORE_AUTH_REQUEST, rate_limit_hook, priority=0)
    
    # 注册日志钩子
    register_hook(HookEvent.BEFORE_AUTH_REQUEST, log_operation, priority=3)
    register_hook(HookEvent.AFTER_AUTH_SUCCESS, log_operation, priority=2)
    
    # 创建客户端实例
    driver = BaiduDriver()
    
    print("\n📋 已注册的钩子:")
    print(f"   授权前钩子数量: {driver.hook_manager.get_hook_count(HookEvent.BEFORE_AUTH_REQUEST)}")
    print(f"   授权成功钩子数量: {driver.hook_manager.get_hook_count(HookEvent.AFTER_AUTH_SUCCESS)}")
    print(f"   文件操作钩子数量: {driver.hook_manager.get_hook_count(HookEvent.BEFORE_FILE_OPERATION)}")
    
    print("\n🚀 测试授权请求（带钩子）...")
    
    try:
        # 发起授权请求，传递钩子数据
        result = driver.request_device_access(
            target_user_id="UID_test_user",
            scope="basic,netdisk",
            timeout=60,
            hook_data={
                "payment_amount": 9.99,
                "user_type": "premium"
            }
        )
        
        print(f"✅ 授权成功: {result}")
        
    except Exception as e:
        print(f"❌ 授权失败: {e}")
    
    print("\n📁 测试文件操作（带钩子）...")
    
    try:
        # 测试文件列表操作
        files = driver.list_files(
            access_token="test_token",
            path="/documents",
            hook_data={
                "user_id": "UID_test_user",
                "operation_type": "read"
            }
        )
        
        print(f"✅ 文件操作成功: 获取到 {len(files)} 个文件")
        
    except Exception as e:
        print(f"❌ 文件操作失败: {e}")
    
    print("\n🔍 测试钩子执行顺序...")
    
    # 手动执行钩子
    context = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_test_user",
            "payment_amount": 19.99,
            "test_mode": True
        }
    )
    
    result = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context)
    print(f"钩子执行结果: {result.success}, 继续执行: {result.should_continue}")


def demo_custom_hooks():
    """演示自定义钩子的使用"""
    print("\n🎨 自定义钩子演示")
    print("=" * 50)
    
    # 注册自定义钩子
    @global_hook("before_payment", priority=1)
    def payment_processing_hook(context: HookContext) -> HookResult:
        """支付处理钩子"""
        print("💳 执行支付处理钩子...")
        
        amount = context.data.get("amount", 0)
        if amount > 100:
            return HookResult.stop("金额过大，需要人工审核")
        
        return HookResult.success({"processed": True})
    
    # 手动执行自定义钩子
    context = HookContext(
        event=HookEvent.CUSTOM,
        data={
            "amount": 50.0,
            "payment_method": "alipay"
        }
    )
    
    from bddriver.hooks import hook_manager
    result = hook_manager.execute_global_hooks("before_payment", context)
    
    print(f"自定义钩子执行结果: {result.success}, 继续执行: {result.should_continue}")


if __name__ == "__main__":
    demo_hooks()
    demo_custom_hooks()
