#!/usr/bin/env python3
"""钩子系统简单演示

展示钩子的基本功能，避免实际的授权流程
"""

from bddriver.hooks import (
    HookEvent, HookContext, HookResult, 
    hook, register_hook, execute_hooks
)


def verify_payment(user_id: str, amount: float) -> bool:
    """模拟支付验证"""
    print(f"🔍 验证用户 {user_id} 的支付: ¥{amount}")
    
    if amount > 0 and user_id.startswith("UID_"):
        print("✅ 支付验证成功")
        return True
    else:
        print("❌ 支付验证失败")
        return False


def check_user_permission(user_id: str, operation: str) -> bool:
    """模拟用户权限检查"""
    print(f"🔐 检查用户 {user_id} 的 {operation} 权限")
    
    if user_id.startswith("UID_"):
        print("✅ 权限检查通过")
        return True
    else:
        print("❌ 权限检查失败")
        return False


def log_operation(context: HookContext) -> HookResult:
    """记录操作日志的钩子"""
    event = context.event
    data = context.data
    
    print(f"📝 钩子日志: {event.value}")
    print(f"   数据: {data}")
    
    return HookResult.success()


# 使用装饰器注册钩子
@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
def payment_verification_hook(context: HookContext) -> HookResult:
    """授权请求前的支付验证钩子"""
    print("💰 执行支付验证钩子...")
    
    user_id = context.data.get("target_user_id")
    amount = context.data.get("payment_amount", 0.0)
    
    if not verify_payment(user_id, amount):
        return HookResult.stop("支付验证失败，无法继续授权")
    
    return HookResult.success()


@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=2)
def permission_check_hook(context: HookContext) -> HookResult:
    """授权请求前的权限检查钩子"""
    print("🔐 执行权限检查钩子...")
    
    user_id = context.data.get("target_user_id")
    operation = "auth_request"
    
    if not check_user_permission(user_id, operation):
        return HookResult.stop("权限不足，无法继续授权")
    
    return HookResult.success()


@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=3)
def rate_limit_hook(context: HookContext) -> HookResult:
    """速率限制钩子"""
    print("⏱️  执行速率限制检查...")
    
    # 简单的速率限制：每秒最多1次调用
    import time
    current_time = time.time()
    
    if hasattr(rate_limit_hook, '_last_call'):
        if current_time - rate_limit_hook._last_call < 1:
            return HookResult.stop("请求过于频繁，请稍后再试")
    
    rate_limit_hook._last_call = current_time
    return HookResult.success()


def demo_hooks():
    """演示钩子系统的使用"""
    print("🎯 钩子系统演示")
    print("=" * 50)
    
    # 注册日志钩子
    register_hook(HookEvent.BEFORE_AUTH_REQUEST, log_operation, priority=4)
    
    print("\n📋 已注册的钩子:")
    from bddriver.hooks import hook_manager
    print(f"   授权前钩子数量: {hook_manager.get_hook_count(HookEvent.BEFORE_AUTH_REQUEST)}")
    
    print("\n🚀 测试钩子执行...")
    
    # 测试1：正常情况
    print("\n--- 测试1：正常情况 ---")
    context1 = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_test_user",
            "payment_amount": 9.99,
            "user_type": "premium"
        }
    )
    
    result1 = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context1)
    print(f"结果: 成功={result1.success}, 继续执行={result1.should_continue}")
    
    # 测试2：支付验证失败
    print("\n--- 测试2：支付验证失败 ---")
    context2 = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_test_user",
            "payment_amount": 0.0,  # 支付金额为0，会失败
            "user_type": "free"
        }
    )
    
    result2 = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context2)
    print(f"结果: 成功={result2.success}, 继续执行={result2.should_continue}")
    if result2.error:
        print(f"错误信息: {result2.error}")
    
    # 测试3：权限检查失败
    print("\n--- 测试3：权限检查失败 ---")
    context3 = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "invalid_user",  # 无效用户ID，会失败
            "payment_amount": 9.99,
            "user_type": "premium"
        }
    )
    
    result3 = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context3)
    print(f"结果: 成功={result3.success}, 继续执行={result3.should_continue}")
    if result3.error:
        print(f"错误信息: {result3.error}")
    
    # 测试4：速率限制
    print("\n--- 测试4：速率限制 ---")
    context4 = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_test_user",
            "payment_amount": 9.99,
            "user_type": "premium"
        }
    )
    
    # 连续执行两次，第二次会被速率限制阻止
    result4a = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context4)
    print(f"第一次执行: 成功={result4a.success}, 继续执行={result4a.should_continue}")
    
    result4b = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context4)
    print(f"第二次执行: 成功={result4b.success}, 继续执行={result4b.should_continue}")
    if result4b.error:
        print(f"错误信息: {result4b.error}")


def demo_custom_hooks():
    """演示自定义钩子的使用"""
    print("\n🎨 自定义钩子演示")
    print("=" * 50)
    
    # 注册自定义钩子
    def custom_business_hook(context: HookContext) -> HookResult:
        """自定义业务逻辑钩子"""
        print("🏢 执行自定义业务逻辑钩子...")
        
        user_type = context.data.get("user_type")
        if user_type == "enterprise":
            print("✅ 企业用户，通过业务逻辑检查")
            return HookResult.success({"business_approved": True})
        else:
            print("❌ 非企业用户，业务逻辑检查失败")
            return HookResult.stop("仅限企业用户使用")
    
    # 注册自定义钩子
    register_hook(HookEvent.BEFORE_AUTH_REQUEST, custom_business_hook, priority=0)
    
    print("📋 更新后的钩子数量:")
    from bddriver.hooks import hook_manager
    print(f"   授权前钩子数量: {hook_manager.get_hook_count(HookEvent.BEFORE_AUTH_REQUEST)}")
    
    # 测试企业用户
    print("\n--- 测试企业用户 ---")
    context_enterprise = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_enterprise_user",
            "payment_amount": 99.99,
            "user_type": "enterprise"
        }
    )
    
    result_enterprise = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context_enterprise)
    print(f"企业用户结果: 成功={result_enterprise.success}, 继续执行={result_enterprise.should_continue}")
    
    # 测试普通用户
    print("\n--- 测试普通用户 ---")
    context_normal = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_normal_user",
            "payment_amount": 9.99,
            "user_type": "normal"
        }
    )
    
    result_normal = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context_normal)
    print(f"普通用户结果: 成功={result_normal.success}, 继续执行={result_normal.should_continue}")
    if result_normal.error:
        print(f"错误信息: {result_normal.error}")


if __name__ == "__main__":
    demo_hooks()
    demo_custom_hooks()
