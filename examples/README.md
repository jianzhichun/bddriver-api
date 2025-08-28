# BaiduDriver 示例代码

本目录包含了 BaiduDriver SDK 的各种使用示例，帮助您快速上手和了解 SDK 的功能。

## 📁 示例文件列表

### 🔐 授权相关示例

#### `device_auth.py` - 设备码授权示例 ⭐ **推荐**
- **功能**: 演示如何使用设备码模式进行百度网盘授权
- **特点**: 无需回调链接，适合任何环境部署
- **适用场景**: 命令行工具、服务器应用、内网环境
- **使用方法**: `python device_auth.py`

#### `auth.py` - 授权码授权示例（已废弃）
- **功能**: 演示如何使用授权码模式进行百度网盘授权
- **特点**: 需要临时服务器和公网IP（已废弃）
- **适用场景**: 仅用于历史参考
- **使用方法**: `python auth.py`（不推荐使用）

### 📁 文件操作示例

#### `file_operations.py` - 基础文件操作
- **功能**: 演示文件列表获取、下载、上传等基础操作
- **使用方法**: `python file_operations.py`

#### `fileinfo.py` - 文件信息查询
- **功能**: 演示如何获取文件的详细信息
- **使用方法**: `python fileinfo.py`

#### `filemanager.py` - 文件管理操作
- **功能**: 演示文件重命名、移动、删除等管理操作
- **使用方法**: `python filemanager.py`

#### `upload.py` - 文件上传示例
- **功能**: 演示单文件和批量文件上传
- **使用方法**: `python upload.py`

### 👤 用户信息示例

#### `userinfo.py` - 用户信息查询
- **功能**: 演示如何获取用户基本信息和网盘配额
- **使用方法**: `python userinfo.py`

### 📱 通知集成示例

#### `cli_demo.py` - 命令行演示
- **功能**: 演示完整的命令行交互流程
- **使用方法**: `python cli_demo.py`

#### `context_manager.py` - 上下文管理器示例
- **功能**: 演示如何使用上下文管理器简化授权流程
- **使用方法**: `python context_manager.py`

#### `multimedia_file.py` - 多媒体文件处理
- **功能**: 演示音视频文件的特殊处理
- **使用方法**: `python multimedia_file.py`

## 🚀 快速开始

### 1. 安装依赖
```bash
# 进入项目根目录
cd /path/to/bddriver-api

# 安装开发依赖
pip install -e ".[dev]"
```

### 2. 运行设备码授权示例（推荐）
```bash
cd examples
python device_auth.py
```

### 3. 运行其他示例
```bash
# 基础文件操作
python file_operations.py

# 用户信息查询
python userinfo.py

# 文件上传
python upload.py
```

## 🎯 示例选择建议

### 首次使用
- **推荐**: `device_auth.py` - 设备码授权示例
- **原因**: 无需复杂配置，开箱即用

### 生产环境
- **推荐**: `device_auth.py` - 设备码授权示例
- **原因**: 部署简单，无需公网IP

### 开发测试
- **推荐**: `device_auth.py` - 设备码授权示例
- **原因**: 无需复杂配置，开箱即用

### 文件操作学习
- **推荐**: `file_operations.py` - 基础文件操作
- **原因**: 涵盖常用的文件操作API

## 📋 使用前准备

### 1. 获取WxPusher UID
目标用户需要：
1. 关注 WxPusher 微信公众号
2. 获取自己的 UID（通过 WxPusher 官方工具）
3. 将 UID 告诉请求者

### 2. 确认授权范围
常用的授权范围：
- `basic,netdisk` - 基础权限（推荐）
- `basic,netdisk,netdisk_quota` - 包含配额查询
- `basic,netdisk,netdisk_share` - 包含分享功能

### 3. 设置超时时间
- **默认**: 300秒（5分钟）
- **建议**: 根据用户响应速度调整
- **最大**: 600秒（10分钟，受用户码有效期限制）

## 🔧 自定义配置

### 修改授权超时
```python
result = driver.request_device_access(
    target_user_id="user_uid",
    timeout=600  # 10分钟超时
)
```

### 自定义授权范围
```python
result = driver.request_device_access(
    target_user_id="user_uid",
    scope="basic,netdisk,netdisk_quota"
)
```

### 批量授权处理
```python
users = ["user1_uid", "user2_uid", "user3_uid"]
results = []

for user_id in users:
    try:
        result = driver.request_device_access(user_id)
        results.append({"user_id": user_id, "status": "success", "result": result})
    except Exception as e:
        results.append({"user_id": user_id, "status": "failed", "error": str(e)})
```

## 🐛 常见问题

### Q: 设备码授权和授权码授权有什么区别？
**A**: 
- **设备码授权**: 无需回调链接，用户输入用户码完成授权，适合任何环境
- **授权码授权**: 需要回调链接，用户点击链接完成授权，需要公网IP

### Q: 用户码有效期是多久？
**A**: 默认10分钟，超时后需要重新获取设备码

### Q: 支持批量授权吗？
**A**: 支持，可以循环调用 `request_device_access` 方法

### Q: 授权失败怎么办？
**A**: 检查错误信息，常见原因：
1. 用户UID错误
2. 用户未关注WxPusher
3. 网络连接问题
4. 百度网盘应用配置问题

## 📚 更多资源

- [项目主页](https://github.com/your-repo/bddriver-api)
- [完整文档](https://bddriver.readthedocs.io)
- [问题反馈](https://github.com/your-repo/bddriver-api/issues)
- [技术讨论](微信群/QQ群)

## 🤝 贡献

欢迎提交示例代码和改进建议！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request