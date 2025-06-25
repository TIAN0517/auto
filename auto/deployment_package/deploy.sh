#!/bin/bash

# 自動部署腳本
# 使用方法: sudo bash deploy.sh

set -e

echo "🚀 開始部署 ItemShop 系統..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 檢查是否為root用戶
if [ "$EUID" -ne 0 ]; then
    log_error "請使用 sudo 運行此腳本"
    exit 1
fi

# 更新系統
log_info "更新系統包..."
apt update -y

# 安裝必要軟件
log_info "安裝必要軟件..."
apt install -y nginx certbot python3-certbot-nginx python3-pip curl wget

# 安裝Python依賴
log_info "安裝Python依賴..."
pip3 install -r backend/requirements.txt

# 創建必要的目錄
log_info "創建目錄結構..."
mkdir -p /var/www/html
mkdir -p /var/log/nginx
mkdir -p /etc/ssl/certs
mkdir -p /etc/ssl/private

# 部署前端文件
log_info "部署前端文件..."
cp -r frontend/* /var/www/html/
chown -R www-data:www-data /var/www/html/
chmod -R 755 /var/www/html/

# 配置Nginx
log_info "配置Nginx..."
# 備份默認配置
if [ -f /etc/nginx/sites-available/default ]; then
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
fi

# 部署新配置
cp nginx_complete.conf /etc/nginx/sites-available/lstjks

# 移除舊的站點配置
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/4d-sponsor

# 啟用新站點
ln -sf /etc/nginx/sites-available/lstjks /etc/nginx/sites-enabled/

# 測試Nginx配置
log_info "測試Nginx配置..."
if nginx -t; then
    log_info "Nginx配置測試通過"
else
    log_error "Nginx配置測試失敗"
    exit 1
fi

# 重啟Nginx
log_info "重啟Nginx服務..."
systemctl restart nginx
systemctl enable nginx

# 設置防火牆
log_info "配置防火牆..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw --force enable

# 創建後端服務目錄
log_info "設置後端服務..."
mkdir -p /opt/itemshop
cp -r backend/* /opt/itemshop/
cp -r database /opt/itemshop/
cp -r speedpay_config /opt/itemshop/
mkdir -p /opt/itemshop/logs

# 創建systemd服務文件
cat > /etc/systemd/system/itemshop.service << EOF
[Unit]
Description=ItemShop Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/itemshop
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 重新加載systemd
systemctl daemon-reload

# 啟動後端服務
log_info "啟動後端服務..."
systemctl start itemshop
systemctl enable itemshop

# 檢查服務狀態
log_info "檢查服務狀態..."
if systemctl is-active --quiet nginx; then
    log_info "✅ Nginx 服務運行正常"
else
    log_error "❌ Nginx 服務啟動失敗"
fi

if systemctl is-active --quiet itemshop; then
    log_info "✅ 後端服務運行正常"
else
    log_error "❌ 後端服務啟動失敗"
fi

# 檢查端口
log_info "檢查端口狀態..."
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
log_info "測試HTTP訪問..."
if curl -f -s http://localhost > /dev/null; then
    log_info "✅ HTTP 訪問正常"
else
    log_warn "⚠️  HTTP 訪問失敗"
fi

# 顯示部署完成信息
echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 下一步操作："
echo "1. 設置DNS記錄指向此服務器IP"
echo "2. 運行SSL證書設置："
echo "   sudo certbot --nginx -d lstjks.ip-ddns.com -d www.lstjks.ip-ddns.com"
echo ""
echo "🌐 訪問地址："
echo "   HTTP:  http://lstjks.ip-ddns.com"
echo "   HTTPS: https://lstjks.ip-ddns.com (設置SSL後)"
echo ""
echo "📊 服務狀態："
echo "   sudo systemctl status nginx"
echo "   sudo systemctl status itemshop"
echo ""
echo "📝 日誌查看："
echo "   sudo tail -f /var/log/nginx/lstjks.error.log"
echo "   sudo journalctl -u itemshop -f"
echo ""

log_info "部署腳本執行完成！" 