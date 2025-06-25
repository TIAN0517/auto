# 🖥️ 服務器部署指南

## 📋 部署前準備

### 服務器要求
- **操作系統**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **內存**: 最少 2GB RAM
- **磁盤**: 最少 10GB 可用空間
- **網絡**: 公網IP，開放80和443端口

### 本地準備
1. 確保所有項目文件已準備好
2. 記錄服務器IP地址
3. 準備SSH連接工具

## 🚀 快速部署步驟

### 步驟1: 連接服務器
```bash
# 使用SSH連接服務器
ssh root@您的服務器IP

# 或者使用其他用戶
ssh 用戶名@您的服務器IP
```

### 步驟2: 設置服務器環境
```bash
# 下載並運行環境設置腳本
curl -fsSL https://raw.githubusercontent.com/your-repo/itemshop/main/server-setup.sh | bash

# 或者手動運行
chmod +x server-setup.sh
sudo bash server-setup.sh
```

### 步驟3: 上傳項目文件
```bash
# 方法1: 使用scp上傳
scp -r ./itemshop-project/* root@您的服務器IP:/opt/itemshop/

# 方法2: 使用rsync
rsync -avz ./itemshop-project/ root@您的服務器IP:/opt/itemshop/

# 方法3: 使用git克隆
cd /opt/itemshop
git clone https://github.com/your-repo/itemshop.git .
```

### 步驟4: 部署應用
```bash
# 進入部署目錄
cd /opt/itemshop

# 運行部署腳本
sudo bash deploy.sh
```

## 📁 文件上傳方法

### 方法1: 使用SCP (推薦)
```bash
# 從本地電腦上傳
scp -r ./itemshop-project/* root@192.168.1.100:/opt/itemshop/

# 上傳單個文件
scp docker-compose.yml root@192.168.1.100:/opt/itemshop/
```

### 方法2: 使用SFTP
```bash
# 連接SFTP
sftp root@192.168.1.100

# 上傳文件
put -r ./itemshop-project/* /opt/itemshop/
```

### 方法3: 使用Git
```bash
# 在服務器上克隆
cd /opt/itemshop
git clone https://github.com/your-repo/itemshop.git .
```

### 方法4: 使用wget/curl
```bash
# 下載壓縮包
wget https://github.com/your-repo/itemshop/archive/main.zip
unzip main.zip
mv itemshop-main/* /opt/itemshop/
```

## 🔧 部署後配置

### 檢查服務狀態
```bash
# 查看容器狀態
docker-compose ps

# 查看服務日誌
docker-compose logs -f

# 檢查端口
netstat -tlnp | grep -E ":(80|8080)"
```

### 訪問測試
```bash
# 測試本地訪問
curl -I http://localhost

# 測試API
curl -I http://localhost/api/health
```

### 防火牆配置
```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 🌐 域名配置 (可選)

### 設置DNS記錄
1. 登錄您的域名管理面板
2. 添加A記錄指向服務器IP
3. 等待DNS傳播 (最多48小時)

### SSL證書配置
```bash
# 安裝certbot
sudo apt install certbot python3-certbot-nginx

# 獲取SSL證書
sudo certbot --nginx -d your-domain.com

# 設置自動續期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 監控和管理

### 系統監控
```bash
# 查看系統資源
htop
df -h
free -h

# 查看Docker資源
docker stats
docker system df
```

### 日誌管理
```bash
# 查看應用日誌
tail -f /opt/itemshop/logs/app.log

# 查看監控日誌
tail -f /opt/itemshop/logs/monitor.log

# 查看Nginx日誌
tail -f /var/log/nginx/itemshop.access.log
```

### 備份和恢復
```bash
# 手動備份
/opt/itemshop/backup.sh

# 查看備份
ls -la /opt/backups/itemshop/

# 恢復數據庫
docker-compose exec mysql mysql -u root -p itemshop < backup.sql
```

## 🔒 安全配置

### 修改默認密碼
```bash
# 編輯docker-compose.yml
nano docker-compose.yml

# 修改MySQL密碼
environment:
  MYSQL_ROOT_PASSWORD: your_secure_password
  MYSQL_PASSWORD: your_secure_password
```

### 限制SSH訪問
```bash
# 編輯SSH配置
nano /etc/ssh/sshd_config

# 禁用root登錄
PermitRootLogin no

# 更改SSH端口
Port 2222

# 重啟SSH服務
systemctl restart sshd
```

### 設置防火牆規則
```bash
# 只允許必要端口
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 🚨 故障排除

### 常見問題

1. **Docker服務未啟動**
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **端口被佔用**
   ```bash
   # 查看端口使用
   netstat -tlnp | grep :80
   
   # 殺死進程
   sudo kill -9 PID
   ```

3. **容器啟動失敗**
   ```bash
   # 查看詳細錯誤
   docker-compose logs
   
   # 重新構建
   docker-compose build --no-cache
   ```

4. **內存不足**
   ```bash
   # 清理Docker資源
   docker system prune -a
   
   # 增加swap空間
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### 性能優化

1. **增加Docker資源限制**
   ```bash
   # 編輯Docker配置
   nano /etc/docker/daemon.json
   
   {
     "default-ulimits": {
       "nofile": {
         "Hard": 64000,
         "Name": "nofile",
         "Soft": 64000
       }
     }
   }
   ```

2. **優化Nginx配置**
   ```bash
   # 編輯Nginx配置
   nano nginx_simple_ip.conf
   
   # 添加緩存和壓縮
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   ```

## 📞 支持聯繫

### 獲取幫助
1. 查看日誌文件
2. 檢查系統資源
3. 確認網絡連接
4. 聯繫技術支持

### 有用的命令
```bash
# 重啟所有服務
sudo systemctl restart docker
docker-compose restart

# 查看系統狀態
systemctl status docker
systemctl status itemshop

# 清理系統
docker system prune -f
apt autoremove -y
```

## 🎯 部署檢查清單

- [ ] 服務器環境設置完成
- [ ] 項目文件上傳完成
- [ ] Docker容器啟動成功
- [ ] 端口80和8080正常監聽
- [ ] HTTP訪問測試通過
- [ ] 防火牆配置正確
- [ ] 監控腳本設置完成
- [ ] 備份腳本設置完成
- [ ] 安全配置完成
- [ ] 域名解析正確 (可選)
- [ ] SSL證書配置完成 (可選)

部署完成後，您就可以通過 `http://您的服務器IP` 訪問系統了！ 