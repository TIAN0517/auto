#!/bin/bash

# Docker部署腳本
# 使用方法: bash docker-deploy.sh

set -e

echo "🐳 開始Docker部署 ItemShop 系統..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 檢查Docker是否安裝
if ! command -v docker &> /dev/null; then
    log_error "Docker未安裝，請先安裝Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose未安裝，請先安裝Docker Compose"
    exit 1
fi

# 檢查端口是否被佔用
log_step "檢查端口可用性..."
if netstat -tlnp | grep -q ":80 "; then
    log_warn "端口80已被佔用，請確保沒有其他服務使用此端口"
fi

if netstat -tlnp | grep -q ":8080 "; then
    log_warn "端口8080已被佔用，請確保沒有其他服務使用此端口"
fi

# 停止並移除舊容器
log_step "清理舊容器..."
docker-compose down --remove-orphans 2>/dev/null || true
docker system prune -f

# 構建鏡像
log_step "構建Docker鏡像..."
docker-compose build --no-cache

# 啟動服務
log_step "啟動服務..."
docker-compose up -d

# 等待服務啟動
log_step "等待服務啟動..."
sleep 10

# 檢查服務狀態
log_step "檢查服務狀態..."
if docker-compose ps | grep -q "Up"; then
    log_info "✅ 服務啟動成功"
else
    log_error "❌ 服務啟動失敗"
    docker-compose logs
    exit 1
fi

# 檢查健康狀態
log_step "檢查健康狀態..."
sleep 30
if docker-compose exec itemshop curl -f http://localhost/ > /dev/null 2>&1; then
    log_info "✅ 健康檢查通過"
else
    log_warn "⚠️  健康檢查失敗，但服務可能仍在啟動中"
fi

# 獲取容器IP
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' itemshop-app)

# 顯示部署完成信息
echo ""
echo "🎉 Docker部署完成！"
echo ""
echo "📊 容器狀態："
docker-compose ps
echo ""
echo "🌐 訪問地址："
echo "   主頁: http://localhost"
echo "   支付頁面: http://localhost/payment"
echo "   贊助頁面: http://localhost/sponsor"
echo "   用戶儀表板: http://localhost/dashboard"
echo "   管理員頁面: http://localhost/admin"
echo "   API: http://localhost/api"
echo ""
echo "📝 日誌查看："
echo "   查看所有日誌: docker-compose logs -f"
echo "   查看應用日誌: docker-compose logs -f itemshop"
echo "   查看Redis日誌: docker-compose logs -f redis"
echo "   查看MySQL日誌: docker-compose logs -f mysql"
echo ""
echo "🔧 管理命令："
echo "   停止服務: docker-compose down"
echo "   重啟服務: docker-compose restart"
echo "   更新服務: docker-compose pull && docker-compose up -d"
echo "   進入容器: docker-compose exec itemshop bash"
echo ""

log_info "部署腳本執行完成！" 