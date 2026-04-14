#!/bin/bash
set -e

# 1. 升级核心构建工具
echo "=== 升级构建工具 ==="
pip install --upgrade pip setuptools wheel

# 2. 安装依赖，使用清华镜像加速（解决海外源下载慢/失败问题）
echo "=== 安装项目依赖 ==="
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 3. 验证pandas安装成功
echo "=== 验证依赖安装 ==="
python -c "import pandas; print(f'pandas版本: {pandas.__version__}')"