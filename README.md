# BaiduDriver - 百度网盘授权驱动 SDK

基于设备码授权的百度网盘访问解决方案，支持多通道消息通知，无需回调链接，开箱即用。

## ✨ 功能特性

- 🔐 **设备码授权**：无需公网IP，支持设备码模式授权
- 📱 **智能通知**：WxPusher内置支持，自动轮询用户订阅状态
- 🚀 **零配置**：内置必要配置，支持命令行和程序调用
- 🔌 **可扩展**：基于抽象接口，支持多种消息推送渠道
- 🪝 **钩子系统**：支持在关键操作前执行自定义逻辑，如支付验证、权限检查

## 📦 安装

```bash
pip install bddriver
```

或本地开发安装：

```bash
pip install -e .
```

## 🧭 快速上手

### 设备码授权（推荐）

```python
from bddriver import BaiduDriver

driver = BaiduDriver()

# 设备码授权（无需回调链接）
auth_result = driver.request_device_access(
    target_user_id="UID_xxxxxxxxx",
    scope="basic,netdisk,netdisk_quota",
    timeout=600
)

# 文件操作
files = driver.list_files(auth_result['access_token'], "/")
print(f"根目录文件数量: {len(files)}")
```

更多示例见 `examples/` 目录。

### 钩子系统

钩子系统允许你在关键操作前执行自定义逻辑，如支付验证、权限检查等：

```python
from bddriver import BaiduDriver
from bddriver.hooks import HookEvent, HookContext, HookResult, hook

# 使用装饰器注册钩子
@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
def payment_verification(context: HookContext) -> HookResult:
    """授权请求前的支付验证"""
    user_id = context.data.get("target_user_id")
    amount = context.data.get("payment_amount", 0.0)
    
    if not verify_payment(user_id, amount):
        return HookResult.stop("支付验证失败")
    
    return HookResult.success()

# 创建客户端并传递钩子数据
driver = BaiduDriver()
result = driver.request_device_access(
    target_user_id="UID_user123",
    hook_data={"payment_amount": 9.99}
)
```

支持的事件类型：
- `BEFORE_AUTH_REQUEST`: 授权请求前
- `AFTER_AUTH_SUCCESS`: 授权成功后
- `AFTER_AUTH_FAILURE`: 授权失败后
- `BEFORE_FILE_OPERATION`: 文件操作前
- `AFTER_FILE_OPERATION`: 文件操作后

更多钩子示例见 `examples/hooks_demo.py`。

#### 异步钩子与阻塞行为

- 授权前与文件操作前，SDK 会先执行同步钩子，再顺序等待异步钩子完成（阻塞），全部通过后才继续后续流程。
- 任一钩子返回 `HookResult.stop("原因")` 将中断流程并抛错。
 
示例：授权前等待支付完成（带超时）

```python
from bddriver.hooks import hook, HookEvent, HookContext, HookResult
import asyncio

@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
async def pay_before_auth(ctx: HookContext) -> HookResult:
    async def do_pay():
        # 调用你的支付网关/轮询支付状态
        await asyncio.sleep(2)
        return True

    try:
        ok = await asyncio.wait_for(do_pay(), timeout=300)
    except asyncio.TimeoutError:
        return HookResult.stop("支付超时")

    return HookResult.success() if ok else HookResult.stop("支付失败")

# 使用
from bddriver import BaiduDriver
driver = BaiduDriver()
driver.request_device_access("UID_xxx", hook_data={"amount": 9.99})
```

进阶：分布式场景用 Redis 记录支付状态（可选）

```python
from bddriver.hooks import hook, HookEvent, HookContext, HookResult
import asyncio
import aioredis

@hook(HookEvent.BEFORE_AUTH_REQUEST, priority=1)
async def pay_with_redis(ctx: HookContext) -> HookResult:
    user_id = ctx.data["target_user_id"]
    order_id = ctx.data["order_id"]
    redis = await aioredis.from_url("redis://localhost:6379", decode_responses=True)

    # 假设你的支付回调会把状态写到 key: pay:status:{order_id}
    key = f"pay:status:{order_id}"
    max_wait, interval = 300, 2
    waited = 0
    while waited < max_wait:
        status = await redis.get(key)  # paid / failed / None
        if status == "paid":
            return HookResult.success()
        if status == "failed":
            return HookResult.stop("支付失败")
        await asyncio.sleep(interval)
        waited += interval
    return HookResult.stop("支付超时")
```

更多异步/混合钩子示例见：`examples/async_hooks_demo.py`。

## 🖥️ 命令行 CLI

```bash
# 设备码授权
bddriver auth UID_xxxxx

# 文件操作
bddriver ls /
bddriver download <remote> <local> --progress
bddriver upload <local> <remote> --progress
```
```

### 消息提供者管理

```bash
# 查看所有消息提供者状态
bddriver messaging list

# 配置钉钉消息提供者
bddriver messaging config dingtalk --webhook-url "https://oapi.dingtalk.com/robot/send?access_token=xxx"

# 切换默认消息提供者
bddriver messaging switch dingtalk

# 测试消息提供者配置
bddriver messaging test dingtalk

# 禁用消息提供者
bddriver messaging disable wxpusher

# 获取订阅信息并自动轮询
bddriver messaging subscribe wxpusher

# 手动轮询指定二维码
bddriver messaging poll <qrcode_code>
```

### 订阅功能

WxPusher支持带参数的二维码订阅功能，可以跟踪用户身份，实现用户绑定：

```bash
# 获取订阅信息并自动轮询扫码状态
bddriver messaging subscribe wxpusher

# 手动轮询指定二维码的扫码状态
bddriver messaging poll <qrcode_code>
```

**功能特性**：
- **自动二维码生成**：每次运行生成带时间戳的唯一二维码
- **智能轮询**：默认10秒间隔自动查询扫码状态
- **用户绑定**：获取用户UID后实现业务用户与WxPusher UID的绑定
- **实时监控**：支持Ctrl+C随时退出轮询

**使用场景**：
- 论坛用户订阅：用户扫码后绑定论坛账号
- 网站用户订阅：跟踪用户来源和订阅行为
- 应用内订阅：实现设备或用户身份绑定

### 完整使用流程

```bash
# 1. 配置WxPusher（首次使用）
bddriver messaging config wxpusher --app-token YOUR_APP_TOKEN

# 2. 获取订阅二维码并自动轮询
bddriver messaging subscribe wxpusher

# 3. 用户扫码订阅
# 系统自动获取用户UID，完成用户绑定

# 4. 发送消息
bddriver messaging test wxpusher
```

### Token 管理策略

- **自动保存**：授权成功后自动保存到 `bddriver_token.json`
- **加载优先级**：命令行 `--token` > 指定文件 `--token-file` > 默认文件 `bddriver_token.json`
- **零配置**：其他命令自动使用默认token文件，无需指定 `--token-file`

### 文件操作命令详解

```bash
# 列表文件
bddriver ls [PATH] [--token TOKEN] [--token-file FILE] [--detailed] [--limit N] [--order FIELD] [--sort ORDER]

# 下载文件
bddriver download <REMOTE_PATH> <LOCAL_PATH> [--token TOKEN] [--token-file FILE] [--progress]

# 上传文件
bddriver upload <LOCAL_PATH> <REMOTE_PATH> [--token TOKEN] [--token-file FILE] [--progress]

# 查看信息
bddriver info
bddriver --version
```

## 🔐 设备码授权优势

| 特性 | 设备码授权 |
|------|------------|
| 回调链接 | 无需公网IP |
| 适用环境 | 内网/服务器/任何环境 |
| 用户体验 | 输入用户码授权，简单快捷 |
| 自动化程度 | 高，支持脚本化 |
| 推荐场景 | 生产环境、自动化部署 |

## ⚙️ 配置要求

### 百度网盘应用配置
确保在 `bddriver/config/builtin.py` 中配置了正确的：
- `app_id`：百度网盘应用ID
- `app_key`：百度网盘应用密钥
- `client_id`：OAuth客户端ID
- `client_secret`：OAuth客户端密钥

### 消息推送配置

#### WxPusher配置（默认）
```python
# 在配置中设置
wxpusher_config = {
    "app_token": "AT_xxxxxxxxxxxxx",
    "base_url": "https://wxpusher.zjiecode.com"
}
```

#### 钉钉机器人配置（可选）
```python
dingtalk_config = {
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx",
    "secret": "SEC000000000000000000000"  # 可选
}
```

#### 企业微信配置（可选）
```python
wechat_work_config = {
    "corp_id": "wwxxxxxxxxxxxxxxxxxx",
    "agent_id": "1000001",
    "secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

#### 邮件配置（可选）
```python
email_config = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password"
}
```

### 目标用户准备
目标用户需要：
1. 关注 WxPusher 微信公众号
2. 获取自己的 UID
3. 将 UID 告诉请求者

## ⚙️ 日志与调试

设置环境变量控制日志：

```bash
export BDDRIVER_LOG_LEVEL=DEBUG
export BDDRIVER_LOG_FORMAT=json
```

日志默认包含结构化字段并对敏感信息脱敏（如 `access_token`）。

## 🎯 使用场景

### 快速测试
```bash
# 授权后立即测试
bddriver auth UID_xxxxx
bddriver ls /
```

### 自动化脚本
```bash
#!/bin/bash
# 授权并保存到指定位置
bddriver auth UID_xxxxx --save-token /tmp/baidu_token.json

# 使用保存的token进行操作
bddriver ls / --token-file /tmp/baidu_token.json
bddriver download /important/file.txt ./backup/ --token-file /tmp/baidu_token.json
```

### 多用户管理
```bash
# 用户A的token
bddriver auth UID_userA --save-token userA_token.json

# 用户B的token
bddriver auth UID_userB --save-token userB_token.json

# 分别使用
bddriver ls / --token-file userA_token.json
bddriver ls / --token-file userB_token.json
```

## 🐛 故障排除

### 常见问题

**Q: 设备码授权失败**
A: 检查百度网盘应用配置、网络连接、授权范围是否有效

**Q: WxPusher推送失败**
A: 检查用户UID是否正确、用户是否已关注WxPusher、配置是否正确

**Q: 授权超时**
A: 可能原因：用户未及时完成授权、用户码已过期、网络延迟过高

### 调试技巧

```bash
# 启用详细日志
export BDDRIVER_LOG_LEVEL=DEBUG
export BDDRIVER_LOG_FORMAT=console

# 验证配置
bddriver info
```

## 🔌 消息推送架构

### 抽象接口设计
项目采用抽象接口设计，支持多种消息推送渠道：

```python
from bddriver.messaging import MessageProvider, MessageProviderRegistry

# 创建消息提供者注册表
registry = MessageProviderRegistry()

# 注册不同的消息提供者
registry.register_provider("wxpusher", WxPusherProvider(wxpusher_config))
registry.register_provider("dingtalk", DingTalkProvider(dingtalk_config))
registry.register_provider("email", EmailProvider(email_config))

# 自动检测用户ID格式并选择合适的提供者
provider = registry.detect_provider_by_user_id("UID_xxxxx")  # WxPusher
provider = registry.detect_provider_by_user_id("13800138000")  # 钉钉
provider = registry.detect_provider_by_user_id("user@example.com")  # 邮件
```

### 支持的消息渠道
- **WxPusher**：微信推送（默认）
- **钉钉机器人**：钉钉群组通知
- **企业微信**：企业内部通知
- **邮件**：SMTP邮件推送
- **可扩展**：基于抽象接口轻松添加新渠道

### 用户ID格式自动识别
- `UID_xxxxx` → WxPusher
- `13800138000` → 钉钉（手机号）
- `ding_xxxxx` → 钉钉（用户ID）
- `user@example.com` → 邮件
- `wwxxxxx` → 企业微信

## 📚 参考

- 核心模块：`bddriver/client.py`、`bddriver/cli.py`
- 授权管理：`bddriver/auth/*`
- 文件操作：`bddriver/fileops/*`
- 消息推送：`bddriver/messaging/*`
- 使用示例：`examples/`

## 👨‍💻 作者

**Zhang Zao** - [zzchun12826@gmail.com](mailto:zzchun12826@gmail.com)

## 🤝 参与贡献

欢迎提交 Issue / PR。建议先运行测试：

```bash
pytest -q
```

## 🚀 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black bddriver/ tests/
```

## 📝 更新日志

### v1.1.0 (2025-08-28)
- 🔌 新增消息推送抽象架构
- 📱 支持多种推送渠道
- 🔄 重构WxPusher客户端
- 📚 更新文档

### v1.0.0 (2025-08-28)
- ✨ 移除ngrok依赖
- 🔄 简化授权流程
- 📚 合并文档
- 🛠️ 迁移到pyproject.toml

##  许可证

MIT License
