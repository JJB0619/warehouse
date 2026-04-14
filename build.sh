#!/bin/bash
set -e

echo "=== 安装依赖 ==="
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "=== 执行数据库初始化脚本 ==="
python init_db.py

echo "=== 启动 Gunicorn ==="
gunicorn app:app -b 0.0.0.0:$PORT -w 2 --timeout 120