#!/bin/bash

# BaiduDriver 开发环境设置脚本

set -e

echo "🚀 设置 BaiduDriver 开发环境..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装 uv:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv 已安装"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
uv venv

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装开发依赖
echo "📚 安装开发依赖..."
uv pip install -e ".[dev]"

# 安装 pre-commit hooks
echo "🔒 安装 pre-commit hooks..."
uv pip install pre-commit
pre-commit install

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p reports
mkdir -p htmlcov

# 运行初始检查
echo "🔍 运行初始代码检查..."
make format
make lint

echo ""
echo "🎉 开发环境设置完成！"
echo ""
echo "常用命令:"
echo "  make help          # 查看所有可用命令"
echo "  make test          # 运行测试"
echo "  make test-fast     # 运行快速测试"
echo "  make format        # 格式化代码"
echo "  make lint          # 代码检查"
echo "  make build         # 构建包"
echo "  make clean         # 清理文件"
echo ""
echo "激活虚拟环境:"
echo "  source .venv/bin/activate"
echo ""
echo "运行 CLI:"
echo "  python -m bddriver.cli --help"
