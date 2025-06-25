# 項目部署包

## 快速部署指南

### 1. 解壓縮
```bash
unzip itemshop-deployment.zip
cd itemshop-deployment
```

### 2. 安裝依賴
```bash
# 安裝Python依賴
pip3 install -r backend/requirements.txt

# 安裝Nginx (Ubuntu/Debian)
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### 3. 部署前端
```bash
# 複製前端文件到Nginx目錄
sudo cp -r frontend/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

### 4. 配置Nginx
```bash
# 備份默認配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 部署新配置
sudo cp nginx_complete.conf /etc/nginx/sites-available/lstjks
sudo ln -s /etc/nginx/sites-available/lstjks /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重啟Nginx
sudo systemctl restart nginx
```

### 5. 啟動後端服務
```bash
# 進入後端目錄
cd backend

# 啟動後端服務
python3 main.py
```

### 6. 設置SSL證書
```bash
# 獲取SSL證書
sudo certbot --nginx -d lstjks.ip-ddns.com -d www.lstjks.ip-ddns.com
```

### 7. 防火牆設置
```bash
# 允許HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 文件結構

```
itemshop-deployment/
├── frontend/           # 前端文件
├── backend/            # 後端服務
├── database/           # 數據庫文件
├── assets/             # 媒體文件
├── nginx_complete.conf # Nginx配置
├── DNS_SETUP_GUIDE.md  # DNS設置指南
└── README.md          # 本文件
```

## 訪問地址

- 主頁: https://lstjks.ip-ddns.com
- 支付頁面: https://lstjks.ip-ddns.com/payment
- 贊助頁面: https://lstjks.ip-ddns.com/sponsor
- 用戶儀表板: https://lstjks.ip-ddns.com/dashboard
- 管理員頁面: https://lstjks.ip-ddns.com/admin

## 故障排除

### 檢查服務狀態
```bash
# 檢查Nginx狀態
sudo systemctl status nginx

# 檢查後端服務
ps aux | grep python3

# 檢查端口
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

### 查看日誌
```bash
# Nginx錯誤日誌
sudo tail -f /var/log/nginx/lstjks.error.log

# Nginx訪問日誌
sudo tail -f /var/log/nginx/lstjks.access.log

# 後端日誌
tail -f logs/app.log
```

### 常見問題

1. **Nginx啟動失敗**
   - 檢查配置文件語法: `sudo nginx -t`
   - 檢查端口衝突: `sudo netstat -tlnp | grep :80`

2. **SSL證書問題**
   - 確保域名解析正確: `nslookup lstjks.ip-ddns.com`
   - 重新獲取證書: `sudo certbot renew --force-renewal`

3. **後端服務無法啟動**
   - 檢查Python依賴: `pip3 list`
   - 檢查端口8080是否被佔用

## 聯繫支持

如有問題，請檢查日誌文件或聯繫技術支持。 