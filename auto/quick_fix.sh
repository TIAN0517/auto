#!/bin/bash
# 快速修復Nginx配置

echo "🚀 快速修復Nginx配置..."

# 停止Nginx
sudo systemctl stop nginx

# 移除有問題的配置
sudo rm -f /etc/nginx/sites-enabled/lstjks.ip-ddns.com

# 創建最小化HTTP配置
sudo tee /etc/nginx/sites-available/lstjks.ip-ddns.com > /dev/null << 'EOF'
server {
    listen 80;
    server_name lstjks.ip-ddns.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 啟用配置
sudo ln -s /etc/nginx/sites-available/lstjks.ip-ddns.com /etc/nginx/sites-enabled/

# 測試並啟動
if sudo nginx -t; then
    sudo systemctl start nginx
    echo "✅ Nginx已修復並啟動"
    echo "🌐 測試訪問: http://lstjks.ip-ddns.com"
    
    # 獲取SSL證書
    echo "🔒 正在獲取SSL證書..."
    sudo certbot --nginx -d lstjks.ip-ddns.com
    
else
    echo "❌ 配置仍有問題"
fi