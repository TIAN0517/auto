@echo off
echo 正在創建部署包...

REM 創建部署包目錄
if not exist "deployment_package" mkdir deployment_package

REM 複製前端文件
echo 複製前端文件...
xcopy "frontend" "deployment_package\frontend" /E /I /Y

REM 複製後端文件
echo 複製後端文件...
xcopy "backend" "deployment_package\backend" /E /I /Y

REM 複製數據庫文件
echo 複製數據庫文件...
xcopy "database" "deployment_package\database" /E /I /Y

REM 複製配置文件
echo 複製配置文件...
xcopy "speedpay_config" "deployment_package\speedpay_config" /E /I /Y

REM 複製Nginx配置
echo 複製Nginx配置...
copy "nginx_simple_ip.conf" "deployment_package\"

REM 複製部署腳本
echo 複製部署腳本...
copy "deployment_package\deploy_ip.sh" "deployment_package\"
copy "deployment_package\README_IP.md" "deployment_package\"

REM 創建ZIP文件
echo 創建ZIP文件...
powershell -command "Compress-Archive -Path 'deployment_package\*' -DestinationPath 'itemshop-deployment-ip.zip' -Force"

echo 部署包創建完成！
echo 文件名: itemshop-deployment-ip.zip
echo.
echo 部署步驟:
echo 1. 將 itemshop-deployment-ip.zip 上傳到服務器
echo 2. 解壓縮: unzip itemshop-deployment-ip.zip
echo 3. 運行部署: sudo bash deploy_ip.sh
echo.
pause 