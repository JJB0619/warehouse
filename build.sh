#!/bin/bash
set -e

# 升级工具
echo "=== 升级构建工具 ==="
pip install --upgrade pip setuptools wheel

# 安装依赖
echo "=== 安装项目依赖 ==="
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 自动初始化管理员（部署时自动运行）
echo "=== 初始化管理员账号 ==="
python init_admin.py

echo "=== 构建完成 ==="