#!/bin/bash

# AutoMATA 后端启动脚本

echo "======================================"
echo "AutoMATA Backend Starting"
echo "======================================"

# 检查并激活 conda 环境
if ! command -v conda &> /dev/null; then
    echo "错误：未找到 conda 命令"
    exit 1
fi

# 激活 automata-dev 开发环境（automata 是模型运行环境，Python 3.6）
echo "激活 conda 环境：automata-dev..."
source $(conda info --base)/etc/profile.d/conda.sh

# 检查 automata-dev 环境是否存在，不存在则创建
if ! conda env list | grep -q "^automata-dev "; then
    echo "创建 automata-dev 环境 (Python 3.9)..."
    conda create -n automata-dev python=3.9 -y
fi

conda activate automata-dev

# 验证环境
python_version=$(python --version)
echo "✓ Python 环境：$python_version"
echo "✓ Conda 环境：$(conda info --envs | grep '*' )"

# 安装依赖
echo "检查依赖..."
pip install -r requirements.txt -q

# 初始化数据库（如果不存在）
echo "初始化数据库..."
python init_db.py

# 启动应用
echo "启动 FastAPI 应用..."
python main.py
