#!/usr/bin/env python3
"""异步钩子演示

展示如何使用异步钩子处理需要等待的操作，如支付验证、API调用等
"""

import asyncio
import time
from bddriver.hooks import (
    HookEvent, HookContext, HookResult,
    hook, register_hook, execute_async_hooks, execute_hooks
)


async def simulate_payment_verification(user_id: str, amount: float) -> bool:
    """模拟异步支付验证
    
    Args:
        user_id: 用户ID
        amount: 支付金额
        
    Returns:
        支付是否成功
    """
    print(f"💳 开始验证用户 {user_id} 的支付: ¥{amount}")
    
    # 模拟支付验证的异步过程
    # 1. 调用支付系统API
    print("   📡 调用支付系统API...")
    await asyncio.sleep(1)  # 模拟网络延迟
    
    # 2. 等待支付结果
    print("   ⏳ 等待支付结果...")
    await asyncio.sleep(2)  # 模拟支付处理时间
    
    # 3. 验证支付状态
    print("   🔍 验证支付状态...")
    await asyncio.sleep(0.5)  # 模拟验证时间
    
    # 模拟支付结果
    if amount > 0 and user_id.startswith("UID_"):
        print("   ✅ 支付验证成功")
        return True
    else:
        print("   ❌ 支付验证失败")
        return False


async def simulate_permission_check(user_id: str, operation: str) -> bool:
    """模拟异步权限检查
    
    Args:
        user_id: 用户ID
        operation: 操作类型
        
    Returns:
        是否有权限
    """
    print(f"🔐 开始检查用户 {user_id} 的 {operation} 权限")
    
    # 模拟权限检查的异步过程
    # 1. 查询用户数据库
    print("   📊 查询用户数据库...")
    await asyncio.sleep(0.8)  # 模拟数据库查询时间
    
    # 2. 检查权限规则
    print("   📋 检查权限规则...")
    await asyncio.sleep(0.6)  # 模拟权限计算时间
    
    # 3. 返回权限结果
    if user_id.startswith("UID_"):
        print("   ✅ 权限检查通过")
        return True
    else:
        print("   ❌ 权限检查失败")
        return False


async def simulate_rate_limit_check(user_id: str) -> bool:
    """模拟异步速率限制检查
    
    Args:
        user_id: 用户ID
        
    Returns:
        是否通过速率限制
    """
    print(f"⏱️  开始检查用户 {user_id} 的速率限制")
    
    # 模拟速率限制检查的异步过程
    # 1. 查询Redis缓存
    print("   🗄️  查询Redis缓存...")
    await asyncio.sleep(0.3)  # 模拟缓存查询时间
    
    # 2. 计算调用频率
    print("   📈 计算调用频率...")
    await asyncio.sleep(0.2)  # 模拟计算时间
    
    # 简单的速率限制：每秒最多1次调用
    current_time = time.time()
    
    if hasattr(simulate_rate_limit_check, '_last_call'):
        if current_time - simulate_rate_limit_check._last_call.get(user_id, 0) < 1:
            print("   ❌ 请求过于频繁，请稍后再试")
            return False
    
    if not hasattr(simulate_rate_limit_check, '_last_call'):
        simulate_rate_limit_check._last_call = {}
    
    simulate_rate_limit_check._last_call[user_id] = current_time
    print("   ✅ 速率限制检查通过")
    return True


async def log_operation_async(context: HookContext) -> HookResult:
    """异步记录操作日志的钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    event = context.event
    data = context.data
    
    print(f"📝 异步钩子日志: {event.value}")
    print(f"   数据: {data}")
    
    # 模拟异步日志记录
    await asyncio.sleep(0.1)
    
    return HookResult.success()


# 使用装饰器注册异步钩子
@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
async def async_payment_verification_hook(context: HookContext) -> HookResult:
    """授权请求前的异步支付验证钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("💰 执行异步支付验证钩子...")
    
    user_id = context.data.get("target_user_id")
    amount = context.data.get("payment_amount", 0.0)
    
    # 等待支付验证完成
    payment_success = await simulate_payment_verification(user_id, amount)
    
    if not payment_success:
        return HookResult.stop("支付验证失败，无法继续授权")
    
    return HookResult.success()


@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=2)
async def async_permission_check_hook(context: HookContext) -> HookResult:
    """授权请求前的异步权限检查钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("🔐 执行异步权限检查钩子...")
    
    user_id = context.data.get("target_user_id")
    operation = "auth_request"
    
    # 等待权限检查完成
    permission_granted = await simulate_permission_check(user_id, operation)
    
    if not permission_granted:
        return HookResult.stop("权限不足，无法继续授权")
    
    return HookResult.success()


@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=0)
async def async_rate_limit_hook(context: HookContext) -> HookResult:
    """异步速率限制钩子
    
    Args:
        context: 钩子上下文
        
    Returns:
        钩子执行结果
    """
    print("⏱️  执行异步速率限制检查...")
    
    user_id = context.data.get("target_user_id", "unknown")
    
    # 等待速率限制检查完成
    rate_limit_passed = await simulate_rate_limit_check(user_id)
    
    if not rate_limit_passed:
        return HookResult.stop("请求过于频繁，请稍后再试")
    
    return HookResult.success()


async def demo_async_hooks():
    """演示异步钩子系统的使用"""
    print("🎯 异步钩子系统演示")
    print("=" * 50)
    
    # 注册异步日志钩子
    register_hook(HookEvent.BEFORE_AUTH_REQUEST, log_operation_async, priority=3)
    
    print("\n📋 已注册的异步钩子:")
    from bddriver.hooks import hook_manager
    print(f"   授权前钩子数量: {hook_manager.get_hook_count(HookEvent.BEFORE_AUTH_REQUEST)}")
    
    print("\n🚀 测试异步钩子执行...")
    
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
    
    start_time = time.time()
    result1 = await execute_async_hooks(HookEvent.BEFORE_AUTH_REQUEST, context1)
    end_time = time.time()
    
    print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")
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
    
    start_time = time.time()
    result2 = await execute_async_hooks(HookEvent.BEFORE_AUTH_REQUEST, context2)
    end_time = time.time()
    
    print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")
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
    
    start_time = time.time()
    result3 = await execute_async_hooks(HookEvent.BEFORE_AUTH_REQUEST, context3)
    end_time = time.time()
    
    print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")
    print(f"结果: 成功={result3.success}, 继续执行={result3.should_continue}")
    if result3.error:
        print(f"错误信息: {result3.error}")


async def demo_mixed_hooks():
    """演示混合使用同步和异步钩子"""
    print("\n🔄 混合钩子演示")
    print("=" * 50)
    
    # 注册同步钩子
    def sync_log_hook(context: HookContext) -> HookResult:
        """同步日志钩子"""
        print("📝 同步钩子日志记录")
        return HookResult.success()
    
    register_hook(HookEvent.BEFORE_AUTH_REQUEST, sync_log_hook, priority=4)
    
    print("📋 混合钩子数量:")
    from bddriver.hooks import hook_manager
    print(f"   授权前钩子数量: {hook_manager.get_hook_count(HookEvent.BEFORE_AUTH_REQUEST)}")
    
    # 测试混合钩子
    print("\n--- 测试混合钩子 ---")
    context = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_mixed_user",
            "payment_amount": 19.99,
            "user_type": "enterprise"
        }
    )
    
    start_time = time.time()
    
    # 先执行同步钩子
    sync_result = execute_hooks(HookEvent.BEFORE_AUTH_REQUEST, context)
    print(f"同步钩子结果: 成功={sync_result.success}, 继续执行={sync_result.should_continue}")
    
    if sync_result.should_continue:
        # 再执行异步钩子
        async_result = await execute_async_hooks(HookEvent.BEFORE_AUTH_REQUEST, context)
        print(f"异步钩子结果: 成功={async_result.success}, 继续执行={async_result.should_continue}")
    
    end_time = time.time()
    print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")


async def demo_real_world_scenario():
    """演示真实世界的支付场景"""
    print("\n🌍 真实支付场景演示")
    print("=" * 50)
    
    print("💡 场景：用户发起授权请求，需要完成支付验证")
    print("   1. 检查速率限制")
    print("   2. 验证支付状态")
    print("   3. 检查用户权限")
    print("   4. 记录操作日志")
    
    context = HookContext(
        event=HookEvent.BEFORE_AUTH_REQUEST,
        data={
            "target_user_id": "UID_real_user",
            "payment_amount": 29.99,
            "user_type": "premium",
            "payment_method": "alipay",
            "request_ip": "192.168.1.100"
        }
    )
    
    print(f"\n📋 用户信息:")
    print(f"   用户ID: {context.data['target_user_id']}")
    print(f"   支付金额: ¥{context.data['payment_amount']}")
    print(f"   用户类型: {context.data['user_type']}")
    print(f"   支付方式: {context.data['payment_method']}")
    
    print(f"\n🚀 开始执行钩子链...")
    start_time = time.time()
    
    try:
        result = await execute_async_hooks(HookEvent.BEFORE_AUTH_REQUEST, context)
        
        end_time = time.time()
        print(f"\n⏱️  钩子执行完成，总耗时: {end_time - start_time:.2f} 秒")
        
        if result.success and result.should_continue:
            print("✅ 所有检查通过，可以继续授权流程")
            print("🔐 现在可以调用百度网盘授权API了")
        else:
            print(f"❌ 检查未通过: {result.error}")
            
    except Exception as e:
        print(f"❌ 钩子执行异常: {e}")


async def main():
    """主函数"""
    await demo_async_hooks()
    await demo_mixed_hooks()
    await demo_real_world_scenario()


if __name__ == "__main__":
    # 运行异步演示
    asyncio.run(main())
