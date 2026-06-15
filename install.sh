#!/bin/bash
# 安装脚本 - 使用清华镜像源

set -e

# 清华 PyPI 镜像源
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip -i $MIRROR

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt -i $MIRROR

echo "✅ 安装完成！"
echo ""
echo "激活虚拟环境：source venv/bin/activate"
echo "启动服务：python app.py"
