@echo off
echo 🐳 ItemShop Docker 部署腳本
echo ================================

REM 檢查Docker是否安裝
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安裝，請先安裝Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker已安裝

REM 檢查Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安裝
    pause
    exit /b 1
)

echo ✅ Docker Compose已安裝

REM 停止舊容器
echo 📦 清理舊容器...
docker-compose down --remove-orphans 2>nul

REM 清理未使用的資源
echo 🧹 清理Docker資源...
docker system prune -f

REM 構建鏡像
echo 🔨 構建Docker鏡像...
docker-compose build --no-cache

REM 啟動服務
echo 🚀 啟動服務...
docker-compose up -d

REM 等待服務啟動
echo ⏳ 等待服務啟動...
timeout /t 10 /nobreak >nul

REM 檢查服務狀態
echo 📊 檢查服務狀態...
docker-compose ps

echo.
echo 🎉 部署完成！
echo.
echo 🌐 訪問地址：
echo    主頁: http://localhost
echo    支付頁面: http://localhost/payment
echo    贊助頁面: http://localhost/sponsor
echo    用戶儀表板: http://localhost/dashboard
echo    管理員頁面: http://localhost/admin
echo.
echo 📝 管理命令：
echo    查看日誌: docker-compose logs -f
echo    停止服務: docker-compose down
echo    重啟服務: docker-compose restart
echo.
pause 