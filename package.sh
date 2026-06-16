#!/bin/bash
# 打包脚本 - 打包项目文件

set -e

# 项目名称
PROJECT_NAME="anki-script"
# 获取版本号（使用日期）
VERSION=$(date +%Y%m%d_%H%M%S)
# 打包文件名
PACKAGE_NAME="${PROJECT_NAME}_${VERSION}"

echo "📦 开始打包 ${PROJECT_NAME}..."

# 创建临时目录
TEMP_DIR="/tmp/${PACKAGE_NAME}"
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# 复制项目文件（排除不需要的目录）
echo "📁 复制文件..."
rsync -av \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='data/' \
    --exclude='app.log' \
    --exclude='*.wav' \
    --exclude='*.mp3' \
    . "${TEMP_DIR}/"

# 确保 .env 文件被复制
if [ -f ".env" ]; then
    cp .env "${TEMP_DIR}/"
    echo "✅ 已包含 .env 文件"
fi

# 创建 data 目录结构（不包含实际数据）
mkdir -p "${TEMP_DIR}/data/words"
mkdir -p "${TEMP_DIR}/data/sentences"

# 创建打包文件
echo "🗜️ 压缩文件..."
cd /tmp
tar -czf "${OLDPWD}/${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

# 清理临时目录
rm -rf "${TEMP_DIR}"

# 显示结果
FILE_SIZE=$(du -h "${OLDPWD}/${PACKAGE_NAME}.tar.gz" | cut -f1)
echo ""
echo "✅ 打包完成！"
echo "📄 文件: ${PACKAGE_NAME}.tar.gz"
echo "📏 大小: ${FILE_SIZE}"
echo ""
echo "解压命令: tar -xzf ${PACKAGE_NAME}.tar.gz"
