.PHONY: help install install-dev test lint format clean build publish

help: ## 显示帮助信息
	@echo "BaiduDriver SDK 开发命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装项目依赖
	uv pip install -e .

install-dev: ## 安装开发依赖
	uv pip install -e ".[dev]"

install-docs: ## 安装文档依赖
	uv pip install -e ".[docs]"

install-all: ## 安装所有依赖
	uv pip install -e ".[dev,docs,async]"

test: ## 运行测试
	pytest tests/ -v

test-fast: ## 运行快速测试（跳过慢速测试）
	pytest tests/ -v -m "not slow"

test-unit: ## 运行单元测试
	pytest tests/ -v -m "unit"

test-integration: ## 运行集成测试
	pytest tests/ -v -m "integration"

test-cov: ## 运行测试并生成覆盖率报告
	pytest tests/ --cov=bddriver --cov-report=html --cov-report=term

test-html: ## 生成测试HTML报告
	pytest tests/ --html=reports/test-report.html --self-contained-html

lint: ## 运行代码检查
	flake8 bddriver/ tests/ examples/
	mypy bddriver/

format: ## 格式化代码
	black bddriver/ tests/ examples/
	isort bddriver/ tests/ examples/

format-check: ## 检查代码格式
	black --check bddriver/ tests/ examples/
	isort --check-only bddriver/ tests/ examples/

clean: ## 清理构建文件
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf reports/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## 构建包
	uv build

publish: ## 发布到 PyPI (需要配置)
	uv build
	uv publish

venv: ## 创建虚拟环境
	uv venv

sync: ## 同步依赖
	uv sync

lock: ## 锁定依赖版本
	uv lock

run: ## 运行 CLI 命令
	python -m bddriver.cli

dev: install-dev ## 开发环境设置
	@echo "开发环境设置完成！"
	@echo ""
	@echo "常用命令:"
	@echo "  运行测试: make test"
	@echo "  快速测试: make test-fast"
	@echo "  单元测试: make test-unit"
	@echo "  格式化代码: make format"
	@echo "  代码检查: make lint"
	@echo "  构建包: make build"
	@echo "  清理文件: make clean"
