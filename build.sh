#!/bin/bash
set -e

echo "=== 安装依赖 ==="
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "=== 初始化数据库（强制重建）==="
python init_db.py

echo "=== 启动服务 ==="
gunicorn app:app -b 0.0.0.0:$PORT -w 2 --timeout 120