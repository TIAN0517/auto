#!/bin/bash

# 服務器環境設置腳本
# 適用於 Ubuntu 20.04+ / CentOS 7+ / Debian 10+

echo "🖥️  開始設置服務器環境..."

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

# 檢測操作系統
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    log_error "無法檢測操作系統"
    exit 1
fi

log_info "檢測到操作系統: $OS $VER"

# 更新系統
log_step "更新系統包..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt update && apt upgrade -y
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum update -y
else
    log_warn "未知操作系統，請手動更新"
fi

# 安裝Docker
log_step "安裝Docker..."
if ! command -v docker &> /dev/null; then
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Ubuntu/Debian
        apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt update
        apt install -y docker-ce docker-ce-cli containerd.io
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        # CentOS/RHEL
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
    fi
    
    # 啟動Docker服務
    systemctl start docker
    systemctl enable docker
    
    # 將當前用戶添加到docker組
    usermod -aG docker $USER
    
    log_info "Docker安裝完成"
else
    log_info "Docker已安裝"
fi

# 安裝Docker Compose
log_step "安裝Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose安裝完成"
else
    log_info "Docker Compose已安裝"
fi

# 安裝必要工具
log_step "安裝必要工具..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt install -y curl wget git htop net-tools
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum install -y curl wget git htop net-tools
fi

# 設置防火牆
log_step "配置防火牆..."
if command -v ufw &> /dev/null; then
    # Ubuntu UFW
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
elif command -v firewall-cmd &> /dev/null; then
    # CentOS firewalld
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
fi

# 創建部署目錄
log_step "創建部署目錄..."
mkdir -p /opt/itemshop
cd /opt/itemshop

# 顯示系統信息
log_step "系統信息："
echo "操作系統: $OS $VER"
echo "內核版本: $(uname -r)"
echo "CPU核心: $(nproc)"
echo "內存: $(free -h | awk 'NR==2{printf "%s", $2}')"
echo "磁盤: $(df -h / | awk 'NR==2{printf "%s", $4}') 可用"

# 顯示Docker信息
if command -v docker &> /dev/null; then
    echo "Docker版本: $(docker --version)"
    echo "Docker Compose版本: $(docker-compose --version)"
fi

echo ""
log_info "服務器環境設置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 上傳項目文件到 /opt/itemshop/"
echo "2. 運行部署腳本: bash deploy.sh"
echo "3. 訪問 http://您的服務器IP"
echo ""
echo "🔧 常用命令："
echo "   查看系統狀態: htop"
echo "   查看端口: netstat -tlnp"
echo "   查看Docker狀態: docker ps"
echo "" 