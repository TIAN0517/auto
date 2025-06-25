#!/bin/bash

# Docker啟動腳本
set -e

echo "🚀 啟動 ItemShop 系統..."

# 檢查環境變量
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8080}
export DEBUG=${DEBUG:-false}

# 創建日誌目錄
mkdir -p /app/logs

# 啟動後端服務
echo "📡 啟動後端服務..."
cd /app/backend
python3 main.py &
BACKEND_PID=$!

# 等待後端啟動
echo "⏳ 等待後端服務啟動..."
sleep 5

# 檢查後端是否正常運行
if ! curl -f -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "❌ 後端服務啟動失敗"
    exit 1
fi

echo "✅ 後端服務啟動成功"

# 啟動Nginx
echo "🌐 啟動Nginx服務..."
nginx -g "daemon off;" &
NGINX_PID=$!

echo "✅ Nginx服務啟動成功"

# 顯示服務信息
echo ""
echo "🎉 系統啟動完成！"
echo ""
echo "📊 服務狀態："
echo "   後端服務 PID: $BACKEND_PID"
echo "   Nginx服務 PID: $NGINX_PID"
echo ""
echo "🌐 訪問地址："
echo "   HTTP: http://localhost"
echo "   API: http://localhost/api"
echo ""
echo "📝 日誌位置："
echo "   後端日誌: /app/logs/app.log"
echo "   Nginx日誌: /var/log/nginx/itemshop.error.log"
echo ""

# 監控進程
wait $BACKEND_PID $NGINX_PID 