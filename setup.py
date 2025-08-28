#!/usr/bin/env python3
"""
Setup script for BaiduDriver SDK
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'lib', 'baidu-netdisk-sdk', 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="bddriver",
    version="1.0.0",
    author="Zhang Zao",
    author_email="zzchun12826@gmail.com",
    description="零配置百度网盘授权驱动 - 开箱即用的百度网盘 SDK",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/bddriver-api",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements() + [
        "requests>=2.25.0",
        "cryptography>=3.4.0",

    ],
    extras_require={
        "async": ["aiohttp>=3.8.0"],
        "dev": [
            "pytest>=6.0.0", 
            "pytest-asyncio>=0.18.0",
            "black>=21.0.0",
            "flake8>=4.0.0",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "bddriver=bddriver.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="baidu netdisk sdk oauth wxpusher authorization file-sharing",
)