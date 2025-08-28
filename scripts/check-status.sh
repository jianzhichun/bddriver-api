#!/bin/bash

# BaiduDriver 项目状态检查脚本

echo "🔍 检查 BaiduDriver 项目状态..."
echo ""

# 检查 Python 版本
echo "🐍 Python 版本:"
python --version
echo ""

# 检查虚拟环境
echo "🌍 虚拟环境状态:"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "❌ 虚拟环境未激活"
fi
echo ""

# 检查依赖
echo "📦 已安装的包:"
uv pip list | grep -E "(bddriver|pytest|black|flake8|mypy)"
echo ""

# 检查代码质量
echo "🔍 代码质量检查:"
if command -v black &> /dev/null; then
    echo "✅ Black 已安装"
else
    echo "❌ Black 未安装"
fi

if command -v flake8 &> /dev/null; then
    echo "✅ Flake8 已安装"
else
    echo "❌ Flake8 未安装"
fi

if command -v mypy &> /dev/null; then
    echo "✅ MyPy 已安装"
else
    echo "❌ MyPy 未安装"
fi
echo ""

# 检查测试
echo "🧪 测试状态:"
if command -v pytest &> /dev/null; then
    echo "✅ Pytest 已安装"
    echo "运行快速测试..."
    make test-fast 2>/dev/null || echo "❌ 测试失败"
else
    echo "❌ Pytest 未安装"
fi
echo ""

# 检查构建
echo "🏗️ 构建状态:"
if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml 存在"
else
    echo "❌ pyproject.toml 不存在"
fi

if [ -f "Makefile" ]; then
    echo "✅ Makefile 存在"
else
    echo "❌ Makefile 不存在"
fi
echo ""

# 检查 CLI
echo "💻 CLI 状态:"
if python -c "import bddriver.cli" 2>/dev/null; then
    echo "✅ CLI 模块可导入"
    echo "CLI 帮助信息:"
    python -m bddriver.cli --help 2>/dev/null || echo "❌ CLI 运行失败"
else
    echo "❌ CLI 模块不可导入"
fi
echo ""

echo "📊 项目状态检查完成！"
