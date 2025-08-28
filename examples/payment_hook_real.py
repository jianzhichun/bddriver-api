#!/usr/bin/env python3
"""真实支付 Hook 场景（方案一）

在授权前注册异步支付钩子：创建订单 -> 等待支付成功 -> 放行授权。
无 Redis 依赖，内部使用异步等待模拟支付完成（实际项目中替换为你的支付逻辑）。
"""

import asyncio
from typing import Any, Dict
from bddriver import BaiduDriver
from bddriver.hooks import hook, HookEvent, HookContext, HookResult


# ===================== 需替换为你的真实支付逻辑 =====================
async def create_order(user_id: str, amount: float) -> str:
    """调用你的支付服务创建订单，返回订单号"""
    print(f"🧾 创建支付订单 | 用户: {user_id} | 金额: ¥{amount}")
    await asyncio.sleep(0.3)  # 模拟网络延迟
    return "ORDER_REAL_001"


async def wait_payment_ok(order_id: str) -> bool:
    """等待支付完成（实际场景：轮询支付网关或等回调写入状态）"""
    print(f"⏳ 等待支付完成: {order_id}")
    # 占位：3 秒后视为支付成功
    for i in range(3, 0, -1):
        print(f"   … {i}s")
        await asyncio.sleep(1)
    print("✅ 支付完成")
    return True
# =================================================================


@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
async def pay_before_auth(ctx: HookContext) -> HookResult:
    """授权前支付验证：未支付则阻止继续，支付完成才放行"""
    user_id = ctx.data["target_user_id"]
    amount = float(ctx.data.get("amount", 0))

    async def do_pay() -> bool:
        order_id = await create_order(user_id, amount)
        ok = await wait_payment_ok(order_id)
        return ok

    try:
        ok = await asyncio.wait_for(do_pay(), timeout=300)  # 5 分钟超时
    except asyncio.TimeoutError:
        return HookResult.stop("支付超时")

    return HookResult.success() if ok else HookResult.stop("支付失败")


def main() -> None:
    # 你的真实 UID（如需替换，从命令行或环境变量读取亦可）
    uid = "UID_fa9vPh2i7k6Xu45xAaHY3TkDmJQa"

    # 创建客户端并发起授权
    driver = BaiduDriver()
    print("\n🎯 开始：带支付钩子的设备码授权")
    result: Dict[str, Any] = driver.request_device_access(
        target_user_id=uid,
        scope="basic,netdisk",
        timeout=600,
        hook_data={
            "amount": 9.99,  # 传给支付钩子的上下文数据
        },
    )
    print("\n✅ 授权完成:")
    print(result)


if __name__ == "__main__":
    main()
