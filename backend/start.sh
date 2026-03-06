#!/bin/bash

# AutoMATA 后端启动脚本

echo "======================================"
echo "AutoMATA Backend Starting"
echo "======================================"

# 检查 Python 版本
python_version=$(python3 --version)
echo "Python 环境：$python_version"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 安装依赖
echo "检查依赖..."
pip install -r requirements.txt -q

# 初始化数据库（如果不存在）
echo "初始化数据库..."
python init_db.py

# 启动应用
echo "启动 FastAPI 应用..."
python main.py
