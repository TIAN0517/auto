# DNS設置指南

## 1. 域名配置

### 當前域名
- 主域名: `lstjks.ip-ddns.com`
- 備用域名: `www.lstjks.ip-ddns.com`

### DNS記錄設置

#### A記錄設置
```
類型: A
名稱: lstjks
值: [您的服務器IP地址]
TTL: 300 (5分鐘)
```

#### CNAME記錄設置 (可選)
```
類型: CNAME
名稱: www
值: lstjks.ip-ddns.com
TTL: 300 (5分鐘)
```

## 2. 動態DNS (DDNS) 設置

如果您使用動態IP地址，需要設置DDNS更新：

### 方法1: 使用DDNS客戶端
```bash
# 安裝ddclient
sudo apt-get install ddclient

# 配置ddclient
sudo nano /etc/ddclient.conf
```

配置內容：
```
protocol=namecheap
server=dynamicdns.park-your-domain.com
login=your-domain
password=your-password
lstjks.ip-ddns.com
```

### 方法2: 使用cron任務
```bash
# 創建更新腳本
sudo nano /usr/local/bin/update-dns.sh
```

腳本內容：
```bash
#!/bin/bash
CURRENT_IP=$(curl -s ifconfig.me)
DOMAIN="lstjks.ip-ddns.com"
API_KEY="your-api-key"
API_SECRET="your-api-secret"

curl -X POST "https://api.your-dns-provider.com/v1/domains/$DOMAIN/records" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"A\",\"name\":\"lstjks\",\"content\":\"$CURRENT_IP\"}"
```

設置cron任務：
```bash
# 每5分鐘更新一次
*/5 * * * * /usr/local/bin/update-dns.sh
```

## 3. SSL證書設置

### 使用Let's Encrypt (推薦)
```bash
# 安裝certbot
sudo apt-get install certbot python3-certbot-nginx

# 獲取SSL證書
sudo certbot --nginx -d lstjks.ip-ddns.com -d www.lstjks.ip-ddns.com

# 設置自動續期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 手動SSL證書
如果您有自己的SSL證書：
```bash
# 創建SSL目錄
sudo mkdir -p /etc/ssl/certs /etc/ssl/private

# 複製證書文件
sudo cp your-certificate.crt /etc/ssl/certs/lstjks.crt
sudo cp your-private-key.key /etc/ssl/private/lstjks.key

# 設置權限
sudo chmod 644 /etc/ssl/certs/lstjks.crt
sudo chmod 600 /etc/ssl/private/lstjks.key
```

## 4. Nginx配置部署

### 部署完整配置
```bash
# 備份當前配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 複製新配置
sudo cp nginx_complete.conf /etc/nginx/sites-available/lstjks

# 啟用站點
sudo ln -s /etc/nginx/sites-available/lstjks /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重啟Nginx
sudo systemctl restart nginx
```

## 5. 防火牆設置

### UFW防火牆
```bash
# 允許HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允許SSH (如果需要)
sudo ufw allow 22/tcp

# 啟用防火牆
sudo ufw enable
```

### iptables (替代方案)
```bash
# 允許HTTP
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# 允許HTTPS
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 保存規則
sudo iptables-save > /etc/iptables/rules.v4
```

## 6. 測試DNS設置

### 檢查DNS解析
```bash
# 檢查A記錄
nslookup lstjks.ip-ddns.com

# 檢查CNAME記錄
nslookup www.lstjks.ip-ddns.com

# 使用dig命令
dig lstjks.ip-ddns.com A
```

### 測試網站訪問
```bash
# 測試HTTP
curl -I http://lstjks.ip-ddns.com

# 測試HTTPS
curl -I https://lstjks.ip-ddns.com

# 測試API
curl -I http://lstjks.ip-ddns.com/api/health
```

## 7. 監控和維護

### 設置監控腳本
```bash
# 創建監控腳本
sudo nano /usr/local/bin/monitor-dns.sh
```

腳本內容：
```bash
#!/bin/bash
DOMAIN="lstjks.ip-ddns.com"
LOG_FILE="/var/log/dns-monitor.log"

# 檢查DNS解析
if ! nslookup $DOMAIN > /dev/null 2>&1; then
    echo "$(date): DNS resolution failed for $DOMAIN" >> $LOG_FILE
    # 發送通知郵件或重啟服務
fi

# 檢查網站響應
if ! curl -f -s https://$DOMAIN > /dev/null; then
    echo "$(date): Website not responding for $DOMAIN" >> $LOG_FILE
fi
```

設置cron監控：
```bash
# 每10分鐘檢查一次
*/10 * * * * /usr/local/bin/monitor-dns.sh
```

## 8. 故障排除

### 常見問題

1. **DNS解析失敗**
   - 檢查A記錄是否正確
   - 等待DNS傳播 (最多48小時)
   - 檢查DNS提供商設置

2. **SSL證書問題**
   - 檢查證書路徑是否正確
   - 確認證書未過期
   - 檢查Nginx配置語法

3. **網站無法訪問**
   - 檢查防火牆設置
   - 確認Nginx服務運行
   - 檢查端口是否開放

4. **API無法訪問**
   - 檢查後端服務是否運行
   - 確認反向代理配置
   - 檢查WebSocket支持

### 日誌檢查
```bash
# 檢查Nginx錯誤日誌
sudo tail -f /var/log/nginx/lstjks.error.log

# 檢查訪問日誌
sudo tail -f /var/log/nginx/lstjks.access.log

# 檢查系統日誌
sudo journalctl -u nginx -f
```

## 9. 安全建議

1. **定期更新SSL證書**
2. **監控訪問日誌**
3. **設置防火牆規則**
4. **定期備份配置**
5. **使用強密碼**
6. **啟用安全標頭**
7. **限制文件訪問權限**

## 10. 備份策略

```bash
# 創建備份腳本
sudo nano /usr/local/bin/backup-config.sh
```

腳本內容：
```bash
#!/bin/bash
BACKUP_DIR="/backup/nginx"
DATE=$(date +%Y%m%d_%H%M%S)

# 創建備份目錄
mkdir -p $BACKUP_DIR

# 備份Nginx配置
tar -czf $BACKUP_DIR/nginx-config-$DATE.tar.gz /etc/nginx/

# 備份SSL證書
tar -czf $BACKUP_DIR/ssl-certs-$DATE.tar.gz /etc/ssl/

# 保留最近7天的備份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

設置自動備份：
```bash
# 每天凌晨2點備份
0 2 * * * /usr/local/bin/backup-config.sh
``` 