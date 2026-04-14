#!/bin/bash
set -e

# 1. 升级核心构建工具，避免版本过低导致的安装失败
echo "=== 升级构建工具 ==="
pip install --upgrade pip setuptools wheel

# 2. 安装项目依赖，使用清华镜像加速，解决海外源网络问题
echo "=== 安装项目依赖 ==="
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 3. 验证核心依赖安装成功，提前发现问题
echo "=== 验证依赖安装 ==="
python -c "import flask, pandas, gunicorn, openpyxl; print('所有核心依赖安装成功！')"