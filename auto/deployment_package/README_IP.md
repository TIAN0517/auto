# ItemShop 系統部署指南 (IP訪問)

## 快速部署

### 1. 解壓縮
```bash
unzip itemshop-deployment.zip
cd itemshop-deployment
```

### 2. 自動部署 (推薦)
```bash
sudo bash deploy.sh
```

### 3. 手動部署

#### 安裝依賴
```bash
# 安裝Python依賴
pip3 install -r backend/requirements.txt

# 安裝Nginx
sudo apt update
sudo apt install nginx python3-pip
```

#### 部署前端
```bash
# 複製前端文件
sudo cp -r frontend/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

#### 配置Nginx
```bash
# 備份默認配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 部署IP配置
sudo cp nginx_simple_ip.conf /etc/nginx/sites-available/itemshop
sudo ln -s /etc/nginx/sites-available/itemshop /etc/nginx/sites-enabled/

# 移除默認站點
sudo rm -f /etc/nginx/sites-enabled/default

# 測試配置
sudo nginx -t

# 重啟Nginx
sudo systemctl restart nginx
```

#### 啟動後端
```bash
cd backend
python3 main.py
```

## 訪問地址

假設您的服務器IP是 `192.168.1.100`：

- 主頁: http://192.168.1.100
- 支付頁面: http://192.168.1.100/payment
- 贊助頁面: http://192.168.1.100/sponsor
- 用戶儀表板: http://192.168.1.100/dashboard
- 管理員頁面: http://192.168.1.100/admin

## 防火牆設置

```bash
# 允許HTTP
sudo ufw allow 80/tcp

# 允許SSH (如果需要)
sudo ufw allow 22/tcp

# 啟用防火牆
sudo ufw enable
```

## 服務管理

### 檢查服務狀態
```bash
# Nginx狀態
sudo systemctl status nginx

# 後端服務 (如果使用systemd)
sudo systemctl status itemshop
```

### 重啟服務
```bash
# 重啟Nginx
sudo systemctl restart nginx

# 重啟後端
sudo systemctl restart itemshop
```

### 查看日誌
```bash
# Nginx日誌
sudo tail -f /var/log/nginx/itemshop.error.log
sudo tail -f /var/log/nginx/itemshop.access.log

# 後端日誌
tail -f logs/app.log
```

## 故障排除

### 常見問題

1. **無法訪問網站**
   - 檢查Nginx是否運行: `sudo systemctl status nginx`
   - 檢查端口80是否開放: `sudo netstat -tlnp | grep :80`
   - 檢查防火牆: `sudo ufw status`

2. **API無法訪問**
   - 檢查後端服務是否運行: `ps aux | grep python3`
   - 檢查端口8080: `sudo netstat -tlnp | grep :8080`

3. **靜態文件無法加載**
   - 檢查文件權限: `ls -la /var/www/html/`
   - 檢查Nginx配置: `sudo nginx -t`

### 測試命令

```bash
# 測試HTTP訪問
curl -I http://localhost

# 測試API
curl -I http://localhost/api/health

# 檢查端口
sudo netstat -tlnp | grep -E ":(80|8080)"
```

## 安全建議

1. 設置防火牆規則
2. 定期更新系統
3. 監控訪問日誌
4. 備份重要數據
5. 使用強密碼

## 備份

```bash
# 備份前端文件
sudo tar -czf frontend-backup.tar.gz /var/www/html/

# 備份後端文件
tar -czf backend-backup.tar.gz backend/

# 備份Nginx配置
sudo tar -czf nginx-backup.tar.gz /etc/nginx/
``` 