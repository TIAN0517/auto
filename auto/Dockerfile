# 使用Python 3.11作為基礎鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    wget \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件並安裝Python依賴
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程序文件
COPY backend/ ./backend/
COPY database/ ./database/
COPY speedpay_config/ ./speedpay_config/
COPY frontend/ ./frontend/
COPY assets/ ./assets/

# 創建必要的目錄
RUN mkdir -p /var/www/html /var/log/nginx /app/logs

# 複製前端文件到Nginx目錄
RUN cp -r frontend/* /var/www/html/

# 複製Nginx配置
COPY nginx_simple_ip.conf /etc/nginx/sites-available/itemshop
RUN ln -sf /etc/nginx/sites-available/itemshop /etc/nginx/sites-enabled/ && \
    rm -f /etc/nginx/sites-enabled/default

# 設置權限
RUN chown -R www-data:www-data /var/www/html /app/logs && \
    chmod -R 755 /var/www/html

# 創建啟動腳本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 暴露端口
EXPOSE 80 8080

# 設置健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 啟動命令
ENTRYPOINT ["docker-entrypoint.sh"] 