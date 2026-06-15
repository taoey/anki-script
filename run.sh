#!/bin/bash
# 后台启动 Flask 服务，支持重启

# 停止已有进程
echo "🔄 停止已有服务..."
pkill -f "python app.py" 2>/dev/null || true
sleep 1

# 激活虚拟环境
source venv/bin/activate

# 后台启动服务，日志输出到 app.log
echo "🚀 启动服务..."
nohup python app.py > app.log 2>&1 &

# 获取进程 PID
PID=$!
echo "✅ 服务已启动 (PID: $PID)"
echo "📄 日志文件: app.log"
echo ""
echo "查看日志: tail -f app.log"
echo "停止服务: pkill -f 'python app.py'"
