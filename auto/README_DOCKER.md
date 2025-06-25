# ItemShop 系統 Docker 部署指南

## 🐳 快速部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用內存
- 至少 5GB 可用磁盤空間

### 一鍵部署

```bash
# 克隆或下載項目文件
# 進入項目目錄
cd itemshop-project

# 運行部署腳本
bash docker-deploy.sh
```

### 手動部署

```bash
# 1. 構建並啟動服務
docker-compose up -d

# 2. 查看服務狀態
docker-compose ps

# 3. 查看日誌
docker-compose logs -f
```

## 📁 項目結構

```
itemshop-project/
├── Dockerfile                 # Docker鏡像配置
├── docker-compose.yml         # Docker Compose配置
├── docker-entrypoint.sh       # 容器啟動腳本
├── .dockerignore             # Docker忽略文件
├── nginx_simple_ip.conf      # Nginx配置
├── backend/                  # 後端代碼
├── frontend/                 # 前端文件
├── database/                 # 數據庫文件
├── speedpay_config/          # 支付配置
├── assets/                   # 媒體文件
└── logs/                     # 日誌目錄
```

## 🌐 訪問地址

部署完成後，您可以通過以下地址訪問：

- **主頁**: http://localhost
- **支付頁面**: http://localhost/payment
- **贊助頁面**: http://localhost/sponsor
- **用戶儀表板**: http://localhost/dashboard
- **管理員頁面**: http://localhost/admin
- **API接口**: http://localhost/api

## 🔧 服務管理

### 查看服務狀態
```bash
docker-compose ps
```

### 查看日誌
```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f itemshop
docker-compose logs -f redis
docker-compose logs -f mysql
```

### 重啟服務
```bash
# 重啟所有服務
docker-compose restart

# 重啟特定服務
docker-compose restart itemshop
```

### 停止服務
```bash
docker-compose down
```

### 更新服務
```bash
# 拉取最新代碼後重新構建
docker-compose pull
docker-compose build --no-cache
docker-compose up -d
```

## 🗄️ 數據庫管理

### 連接MySQL
```bash
# 進入MySQL容器
docker-compose exec mysql mysql -u itemshop -p itemshop

# 或使用root用戶
docker-compose exec mysql mysql -u root -p
```

### 備份數據庫
```bash
docker-compose exec mysql mysqldump -u root -p itemshop > backup.sql
```

### 恢復數據庫
```bash
docker-compose exec -T mysql mysql -u root -p itemshop < backup.sql
```

## 🔍 故障排除

### 常見問題

1. **端口衝突**
   ```bash
   # 檢查端口使用情況
   netstat -tlnp | grep -E ":(80|8080|3306|6379)"
   
   # 修改docker-compose.yml中的端口映射
   ports:
     - "8080:80"  # 改為其他端口
   ```

2. **容器啟動失敗**
   ```bash
   # 查看詳細錯誤日誌
   docker-compose logs itemshop
   
   # 重新構建鏡像
   docker-compose build --no-cache
   ```

3. **內存不足**
   ```bash
   # 清理Docker資源
   docker system prune -a
   
   # 增加Docker內存限制
   # 在Docker Desktop設置中調整
   ```

4. **數據庫連接問題**
   ```bash
   # 檢查MySQL容器狀態
   docker-compose ps mysql
   
   # 查看MySQL日誌
   docker-compose logs mysql
   ```

### 性能優化

1. **增加資源限制**
   ```yaml
   # 在docker-compose.yml中添加
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

2. **啟用緩存**
   ```bash
   # Redis已包含在配置中，確保啟用
   docker-compose up -d redis
   ```

3. **數據持久化**
   ```bash
   # 確保數據卷正確掛載
   docker volume ls
   ```

## 🔒 安全配置

### 修改默認密碼
```bash
# 編輯docker-compose.yml
environment:
  MYSQL_ROOT_PASSWORD: your_secure_password
  MYSQL_PASSWORD: your_secure_password
```

### 限制網絡訪問
```yaml
# 在docker-compose.yml中添加
networks:
  itemshop-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 啟用SSL (可選)
```bash
# 使用Nginx代理和Let's Encrypt
# 需要額外的SSL配置
```

## 📊 監控和維護

### 健康檢查
```bash
# 查看健康狀態
docker-compose ps

# 手動健康檢查
curl -f http://localhost/
```

### 資源使用情況
```bash
# 查看容器資源使用
docker stats

# 查看磁盤使用
docker system df
```

### 定期維護
```bash
# 清理未使用的資源
docker system prune -f

# 更新基礎鏡像
docker-compose pull
docker-compose build --no-cache
```

## 🚀 生產環境部署

### 使用Docker Swarm
```bash
# 初始化Swarm
docker swarm init

# 部署服務
docker stack deploy -c docker-compose.yml itemshop
```

### 使用Kubernetes
```bash
# 需要額外的K8s配置文件
# 參考kubernetes/目錄
```

### 負載均衡
```bash
# 使用Nginx或HAProxy
# 配置多個實例
```

## 📞 支持

如有問題，請檢查：
1. Docker和Docker Compose版本
2. 系統資源使用情況
3. 端口衝突
4. 日誌文件

### 聯繫方式
- 查看項目文檔
- 檢查GitHub Issues
- 聯繫技術支持 