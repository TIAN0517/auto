@echo off
REM 啟動後端服務
cd backend
start "後端API" cmd /k python main.py
cd ..

REM 啟動 Nginx（請確認 nginx.exe 路徑正確）
cd nginx
start "Nginx" cmd /k nginx.exe
cd ..

REM 等待服務啟動後自動開啟首頁
TIMEOUT /T 3 >nul
start http://localhost

echo 所有服務已啟動，請在瀏覽器中訪問 http://localhost 或 http://lstjks.ip-ddns.com
pause 