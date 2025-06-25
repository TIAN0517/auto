#!/bin/bash
# 完整系統部署腳本

echo "🎮 Jy自動贊助系統 - 完整部署"
echo "=================================="

# 檢查系統
if [[ $EUID -ne 0 ]]; then
   echo "❌ 請使用sudo運行此腳本"
   exit 1
fi

# 安裝必要軟件
echo "📦 安裝必要軟件..."
apt update > /dev/null 2>&1
apt install -y nginx python3 python3-pip certbot python3-certbot-nginx apache2-utils > /dev/null 2>&1

# 確保Python服務器正在運行
echo "🔍 檢查Python服務器..."
if ! pgrep -f "demo_server" > /dev/null; then
    echo "⚠️  Python服務器未運行，請先啟動:"
    echo "   cd /mnt/d/database\ and\ query\ for\ itemshop\ topup"
    echo "   python3 demo_server.py"
    echo ""
    read -p "服務器已啟動了嗎? (y/N): " server_ready
    if [[ ! "$server_ready" =~ ^[Yy]$ ]]; then
        echo "❌ 請先啟動Python服務器"
        exit 1
    fi
fi

# 配置Nginx
echo "🔧 配置Nginx..."

# 移除舊配置
rm -f /etc/nginx/sites-enabled/lstjks.ip-ddns.com

# 創建新配置
tee /etc/nginx/sites-available/lstjks.ip-ddns.com > /dev/null << 'EOF'
server {
    listen 80;
    server_name lstjks.ip-ddns.com;
    
    # 安全頭部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # 反向代理到Python服務器
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 特殊路由處理
    location /admin {
        proxy_pass http://127.0.0.1:8080/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /sponsor {
        proxy_pass http://127.0.0.1:8080/sponsor;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 阻止惡意請求
    location ~ /(actuator|wp-admin|phpmyadmin|\.env|\.git) {
        deny all;
        return 404;
    }
}
EOF

# 啟用配置
ln -s /etc/nginx/sites-available/lstjks.ip-ddns.com /etc/nginx/sites-enabled/

# 測試配置
echo "🧪 測試Nginx配置..."
if nginx -t; then
    echo "✅ Nginx配置正確"
    
    # 重啟Nginx
    systemctl restart nginx
    systemctl enable nginx
    echo "✅ Nginx已啟動"
    
    # 測試HTTP訪問
    echo "🌐 測試HTTP訪問..."
    sleep 2
    if curl -s -o /dev/null -w "%{http_code}" http://lstjks.ip-ddns.com | grep -q "200\|301\|302"; then
        echo "✅ HTTP訪問正常"
        
        # 獲取SSL證書
        echo "🔒 獲取SSL證書..."
        certbot --nginx -d lstjks.ip-ddns.com --non-interactive --agree-tos --email admin@lstjks.ip-ddns.com --redirect
        
        if [ $? -eq 0 ]; then
            echo "✅ SSL證書安裝成功"
            echo ""
            echo "🎉 部署完成！"
            echo "=================================="
            echo "🌐 訪問地址:"
            echo "   主頁: https://lstjks.ip-ddns.com"
            echo "   贊助: https://lstjks.ip-ddns.com/sponsor"
            echo "   後台: https://lstjks.ip-ddns.com/admin"
            echo "   API: https://lstjks.ip-ddns.com/api/status"
        else
            echo "⚠️  SSL證書獲取失敗，但HTTP可用"
            echo "🌐 訪問地址: http://lstjks.ip-ddns.com"
        fi
    else
        echo "❌ HTTP訪問失敗，請檢查Python服務器"
    fi
else
    echo "❌ Nginx配置有誤"
    nginx -t
    exit 1
fi

echo ""
echo "📋 系統狀態:"
echo "   Nginx: $(systemctl is-active nginx)"
echo "   Python服務器: $(pgrep -f demo_server > /dev/null && echo 'running' || echo 'stopped')"
echo ""
echo "🔧 如需重啟服務:"
echo "   sudo systemctl restart nginx"
echo "   sudo systemctl status nginx"