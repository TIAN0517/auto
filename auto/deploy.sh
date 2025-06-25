#!/bin/bash

# ItemShop 服務器部署腳本
# 使用方法: bash deploy.sh

set -e

echo "🚀 開始部署 ItemShop 系統到服務器..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 檢查是否為root用戶
if [ "$EUID" -ne 0 ]; then
    log_error "請使用 sudo 運行此腳本"
    exit 1
fi

# 獲取服務器IP
SERVER_IP=$(hostname -I | awk '{print $1}')
log_info "檢測到服務器IP: $SERVER_IP"

# 檢查Docker
log_step "檢查Docker環境..."
if ! command -v docker &> /dev/null; then
    log_error "Docker未安裝，請先運行 server-setup.sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose未安裝，請先運行 server-setup.sh"
    exit 1
fi

# 檢查必要文件
log_step "檢查項目文件..."
if [ ! -f "docker-compose.yml" ]; then
    log_error "找不到 docker-compose.yml 文件"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    log_error "找不到 Dockerfile 文件"
    exit 1
fi

# 停止舊容器
log_step "清理舊容器..."
docker-compose down --remove-orphans 2>/dev/null || true
docker system prune -f

# 創建日誌目錄
log_step "創建必要目錄..."
mkdir -p logs
mkdir -p database
mkdir -p speedpay_config

# 設置權限
chmod +x docker-entrypoint.sh
chmod +x docker-deploy.sh

# 構建鏡像
log_step "構建Docker鏡像..."
docker-compose build --no-cache

# 啟動服務
log_step "啟動服務..."
docker-compose up -d

# 等待服務啟動
log_step "等待服務啟動..."
sleep 15

# 檢查服務狀態
log_step "檢查服務狀態..."
if docker-compose ps | grep -q "Up"; then
    log_info "✅ 服務啟動成功"
else
    log_error "❌ 服務啟動失敗"
    docker-compose logs
    exit 1
fi

# 檢查端口
log_step "檢查端口狀態..."
if netstat -tlnp | grep -q ":80 "; then
    log_info "✅ 端口 80 正常監聽"
else
    log_warn "⚠️  端口 80 未監聽"
fi

if netstat -tlnp | grep -q ":8080 "; then
    log_info "✅ 端口 8080 正常監聽"
else
    log_warn "⚠️  端口 8080 未監聽"
fi

# 測試HTTP訪問
log_step "測試HTTP訪問..."
if curl -f -s http://localhost > /dev/null; then
    log_info "✅ HTTP 訪問正常"
else
    log_warn "⚠️  HTTP 訪問失敗"
fi

# 創建系統服務（可選）
log_step "創建系統服務..."
cat > /etc/systemd/system/itemshop.service << EOF
[Unit]
Description=ItemShop Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/itemshop
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable itemshop.service

# 創建監控腳本
log_step "創建監控腳本..."
cat > /opt/itemshop/monitor.sh << 'EOF'
#!/bin/bash

# 監控腳本
LOG_FILE="/opt/itemshop/logs/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 檢查Docker服務
if ! systemctl is-active --quiet docker; then
    echo "[$DATE] Docker服務未運行，嘗試重啟..." >> $LOG_FILE
    systemctl restart docker
fi

# 檢查容器狀態
if ! docker-compose ps | grep -q "Up"; then
    echo "[$DATE] 容器未運行，嘗試重啟..." >> $LOG_FILE
    docker-compose up -d
fi

# 檢查HTTP訪問
if ! curl -f -s http://localhost > /dev/null; then
    echo "[$DATE] HTTP訪問失敗，重啟服務..." >> $LOG_FILE
    docker-compose restart
fi
EOF

chmod +x /opt/itemshop/monitor.sh

# 設置cron監控
log_step "設置自動監控..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/itemshop/monitor.sh") | crontab -

# 創建備份腳本
log_step "創建備份腳本..."
cat > /opt/itemshop/backup.sh << 'EOF'
#!/bin/bash

# 備份腳本
BACKUP_DIR="/opt/backups/itemshop"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 備份數據庫
docker-compose exec mysql mysqldump -u root -pitemshop123 itemshop > $BACKUP_DIR/db_backup_$DATE.sql

# 備份配置文件
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz database/ speedpay_config/

# 保留最近7天的備份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "備份完成: $BACKUP_DIR"
EOF

chmod +x /opt/itemshop/backup.sh

# 設置每日備份
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/itemshop/backup.sh") | crontab -

# 顯示部署完成信息
echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 服務信息："
echo "   服務器IP: $SERVER_IP"
echo "   主頁: http://$SERVER_IP"
echo "   支付頁面: http://$SERVER_IP/payment"
echo "   贊助頁面: http://$SERVER_IP/sponsor"
echo "   用戶儀表板: http://$SERVER_IP/dashboard"
echo "   管理員頁面: http://$SERVER_IP/admin"
echo "   API: http://$SERVER_IP/api"
echo ""
echo "📝 管理命令："
echo "   查看狀態: docker-compose ps"
echo "   查看日誌: docker-compose logs -f"
echo "   重啟服務: docker-compose restart"
echo "   停止服務: docker-compose down"
echo "   系統服務: systemctl status itemshop"
echo ""
echo "🔧 監控和備份："
echo "   監控腳本: /opt/itemshop/monitor.sh"
echo "   備份腳本: /opt/itemshop/backup.sh"
echo "   監控日誌: tail -f /opt/itemshop/logs/monitor.log"
echo ""
echo "📋 安全建議："
echo "   1. 修改默認密碼"
echo "   2. 設置SSL證書"
echo "   3. 定期更新系統"
echo "   4. 監控訪問日誌"
echo ""

log_info "部署腳本執行完成！" 