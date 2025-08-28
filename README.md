# BaiduDriver - 百度网盘授权驱动 SDK

让用户 A 在授权后安全访问用户 B 的百度网盘文件。支持程序调用与命令行使用，默认非交互、可脚本化，开箱即用。

## ✨ 功能特性

- 🔐 零额外配置：内置必要配置，直接使用
- 📱 微信通知：通过 WxPusher 发送授权请求链接

- 🧪 覆盖测试：提供示例与测试，便于集成验证
- 🚀 设备码授权：支持无需回调链接的设备码模式授权

## 📦 安装

```bash
pip install bddriver
```

或本地开发安装：

```bash
pip install -e .
```

## 🧭 快速上手（Python）

### 基础用法

```python
from bddriver import BaiduDriver

driver = BaiduDriver()

# 发起授权请求（WxPusher 会向目标用户推送授权链接）
result = driver.request_access(
    target_user_id="UID_xxx",   # WxPusher UID
    file_path="/",
    description="申请访问根目录"
)

access_token = result["access_token"]
files = driver.list_files(access_token, path="/")
```

### 设备码授权（推荐）

```python
from bddriver import BaiduDriver
from bddriver.utils.errors import AuthTimeoutError, WxPusherError

try:
    driver = BaiduDriver()
    
    # 设备码授权（无需回调链接）
    auth_result = driver.request_device_access(
        target_user_id="UID_xxxxxxxxx",
        scope="basic,netdisk,netdisk_quota",
        timeout=600
    )
    
    print(f"授权成功！Token: {auth_result['access_token'][:20]}...")
    
    # 文件操作
    files = driver.list_files(auth_result['access_token'], "/")
    print(f"根目录文件数量: {len(files)}")
    
except AuthTimeoutError:
    print("授权超时，请检查用户是否及时完成授权")
except WxPusherError as e:
    print(f"WxPusher推送失败: {e}")
```

更多示例见 `examples/`：

- `examples/basic_usage.py`
- `examples/file_operations.py`
- `examples/device_auth.py`

## 🖥️ 命令行 CLI

安装后提供 `bddriver` 命令，支持设备码授权模式：

```bash
# 基础设备码授权（自动保存到 bddriver_token.json）
bddriver device-auth UID_xxxxx

# 指定授权范围和超时时间
bddriver device-auth UID_xxxxx --scope "basic,netdisk,netdisk_quota" --timeout 600

# 自定义保存路径
bddriver device-auth UID_xxxxx --save-token my_custom_token.json
```

### 完整使用流程

```bash
# 1. 设备码授权（自动保存token）
bddriver device-auth UID_xxxxx

# 2. 授权成功后的输出示例
✅ 设备码授权成功！
✅ Token 已自动保存到: bddriver_token.json
ℹ️  访问令牌: 123456789abc...
ℹ️  过期时间: 2025-08-28 09:00:00

# 3. 立即使用文件操作命令（自动使用默认token文件）
bddriver ls /
bddriver download /photos/vacation.jpg ./vacation.jpg --progress
bddriver upload ./new_photo.jpg /photos/new_photo.jpg --progress

# 4. 或指定token文件
bddriver ls / --token-file my_custom_token.json
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

### WxPusher配置
确保在配置中设置了：
- `app_token`：WxPusher应用令牌
- `base_url`：WxPusher API基础URL

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
bddriver device-auth UID_xxxxx
bddriver ls /
```

### 自动化脚本
```bash
#!/bin/bash
# 授权并保存到指定位置
bddriver device-auth UID_xxxxx --save-token /tmp/baidu_token.json

# 使用保存的token进行操作
bddriver ls / --token-file /tmp/baidu_token.json
bddriver download /important/file.txt ./backup/ --token-file /tmp/baidu_token.json
```

### 多用户管理
```bash
# 用户A的token
bddriver device-auth UID_userA --save-token userA_token.json

# 用户B的token
bddriver device-auth UID_userB --save-token userB_token.json

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

## 📚 参考与示例

- 代码结构与入口：`bddriver/client.py`、`bddriver/cli.py`
- 授权与服务器：`bddriver/auth/*`
- 文件操作：`bddriver/fileops/*`
- WxPusher：`bddriver/wxpusher/*`
- 示例：`examples/`

## 👨‍💻 作者

**Zhang Zao** - [zzchun12826@gmail.com](mailto:zzchun12826@gmail.com)

## 🤝 参与贡献

欢迎提交 Issue / PR。建议先运行测试：

```bash
pytest -q
```

## 🚀 开发环境设置

### 使用 uv 管理依赖

本项目使用 `uv` 作为包管理器和构建工具：

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装开发依赖
uv pip install -e ".[dev]"

# 或使用 Makefile
make dev
```

### 开发命令

```bash
# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint

# 清理构建文件
make clean

# 构建包
make build
```

### 项目结构

```
bddriver-api/
├── bddriver/           # 主包
├── examples/           # 使用示例
├── tests/             # 测试文件
├── lib/               # 第三方库
├── pyproject.toml     # 项目配置
├── Makefile          # 开发命令
└── README.md         # 项目文档
```

## 📝 更新日志

### v1.0.0 (2025-08-28)
- ✨ 移除 ngrok 和临时服务器依赖
- 🔄 简化授权流程，仅支持设备码授权
- 📚 合并文档到单一 README.md
- 🛠️ 迁移到 uv + pyproject.toml
- 👨‍💻 更新作者信息
- 🧹 清理代码和配置

##  许可证

MIT License
