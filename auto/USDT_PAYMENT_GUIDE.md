# USDT支付功能指南
# USDT Payment Integration Guide

## 概述 (Overview)

本系統已成功整合USDT加密貨幣支付功能，支持ERC-20和TRC-20兩種網絡。用戶可以使用USDT進行贊助支付，享受低手續費和全球通用的優勢。

## 功能特點 (Features)

### 🚀 多網絡支持
- **ERC-20 (Ethereum)**: 以太坊網絡，安全可靠
- **TRC-20 (Tron)**: 波場網絡，手續費最低

### 💰 優惠費率
- ERC-20: 0.5% 手續費
- TRC-20: 0.3% 手續費 (推薦)

### ⚡ 快速處理
- ERC-20: 5-30分鐘確認
- TRC-20: 1-5分鐘確認

### 🔒 安全可靠
- 區塊鏈技術保障
- 多重驗證機制
- 自動狀態檢查

## 錢包地址 (Wallet Addresses)

### ERC-20 (Ethereum)
```
0x732b0b53435977b03c4cef6b7bdffc45e6ec44e6
```

### TRC-20 (Tron)
```
TDejRjcLQa92rrE6SB71LSC7J5VmHs35gq
```

## 技術架構 (Technical Architecture)

### 後端組件 (Backend Components)

1. **USDT支付服務** (`backend/usdt_service.py`)
   - 支付訂單創建
   - 交易狀態監控
   - 網絡連接管理

2. **支付閘道整合** (`backend/payment_gateway.py`)
   - USDT支付方式註冊
   - 統一支付接口

3. **API端點** (`backend/main.py`)
   - `/api/usdt/networks` - 獲取支持網絡
   - `/api/usdt/create-order` - 創建支付訂單
   - `/api/usdt/status/{order_id}` - 檢查支付狀態
   - `/api/usdt/cancel/{order_id}` - 取消訂單

### 前端組件 (Frontend Components)

1. **USDT支付處理器** (`frontend/js/usdt-payment.js`)
   - 支付流程控制
   - QR碼生成
   - 狀態更新

2. **支付界面** (`frontend/payment.html`)
   - USDT支付選項
   - 支付說明面板

3. **樣式文件** (`frontend/css/payment.css`)
   - USDT支付樣式
   - 響應式設計

## 安裝依賴 (Dependencies)

### Python依賴
```bash
pip install web3==6.11.3
pip install tronpy==0.4.0
pip install eth-account==0.9.0
pip install eth-utils==2.2.0
```

### 前端依賴
```html
<script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
```

## 配置說明 (Configuration)

### 1. 網絡配置
在 `backend/usdt_service.py` 中配置網絡參數：

```python
NETWORK_CONFIG = {
    USDTNetwork.ERC20: {
        'rpc_url': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
        'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'enabled': True
    },
    USDTNetwork.TRC20: {
        'rpc_url': 'https://api.trongrid.io',
        'contract_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
        'enabled': True
    }
}
```

### 2. 錢包地址配置
```python
WALLET_ADDRESSES = {
    USDTNetwork.ERC20: "0x732b0b53435977b03c4cef6b7bdffc45e6ec44e6",
    USDTNetwork.TRC20: "TDejRjcLQa92rrE6SB71LSC7J5VmHs35gq"
}
```

## 使用流程 (Usage Flow)

### 1. 用戶選擇USDT支付
用戶在支付頁面選擇USDT支付方式，並選擇網絡（ERC-20或TRC-20）。

### 2. 創建支付訂單
系統創建USDT支付訂單，生成唯一的訂單ID。

### 3. 顯示支付說明
系統顯示：
- 支付金額
- 錢包地址
- QR碼
- 支付步驟
- 重要提醒

### 4. 用戶完成支付
用戶使用錢包掃描QR碼或手動輸入地址完成支付。

### 5. 狀態監控
系統自動檢查支付狀態，確認交易完成。

### 6. 支付完成
支付成功後，系統更新訂單狀態並發放相應獎勵。

## API文檔 (API Documentation)

### 獲取支持網絡
```http
GET /api/usdt/networks
```

**響應:**
```json
{
    "success": true,
    "data": [
        {
            "network": "erc20",
            "name": "Ethereum (ERC-20)",
            "wallet_address": "0x732b0b53435977b03c4cef6b7bdffc45e6ec44e6",
            "min_amount": 1,
            "max_amount": 10000,
            "processing_time": "5-30分鐘",
            "fee_rate": 0.005
        }
    ]
}
```

### 創建支付訂單
```http
POST /api/usdt/create-order
Content-Type: application/json

{
    "amount": 100,
    "network": "trc20"
}
```

**響應:**
```json
{
    "success": true,
    "order": {
        "order_id": "USDT_ABC123DEF456",
        "network": "trc20",
        "amount": 100,
        "total_amount": 100.3,
        "wallet_address": "TDejRjcLQa92rrE6SB71LSC7J5VmHs35gq",
        "status": "pending"
    },
    "payment_instructions": {
        "steps": ["1. 打開您的Tron錢包", "2. 發送 100.3 USDT 到以下地址:"],
        "qr_code_data": "tron:TDejRjcLQa92rrE6SB71LSC7J5VmHs35gq?amount=100.3&token=USDT"
    }
}
```

### 檢查支付狀態
```http
GET /api/usdt/status/{order_id}
```

**響應:**
```json
{
    "success": true,
    "status": "completed",
    "message": "支付成功",
    "confirmations": 19,
    "required_confirmations": 19
}
```

## 安全注意事項 (Security Considerations)

### 1. 私鑰安全
- 永遠不要在代碼中硬編碼私鑰
- 使用環境變量存儲敏感信息
- 定期更換錢包地址

### 2. 網絡安全
- 使用HTTPS協議
- 實施API速率限制
- 驗證所有輸入數據

### 3. 交易驗證
- 驗證交易簽名
- 檢查確認數
- 防止重放攻擊

## 故障排除 (Troubleshooting)

### 常見問題

1. **網絡連接失敗**
   - 檢查RPC URL配置
   - 確認網絡連接
   - 檢查API密鑰

2. **交易確認慢**
   - ERC-20網絡擁堵時確認較慢
   - 建議使用TRC-20網絡

3. **QR碼無法掃描**
   - 檢查QR碼數據格式
   - 確認錢包支持該格式

### 日誌檢查
```bash
# 查看USDT支付日誌
tail -f logs/app.log | grep USDT
```

## 更新日誌 (Changelog)

### v1.0.0 (2024-01-XX)
- ✅ 初始USDT支付功能
- ✅ 支持ERC-20和TRC-20網絡
- ✅ QR碼支付支持
- ✅ 自動狀態檢查
- ✅ 響應式界面設計

## 聯繫支持 (Support)

如有問題或建議，請聯繫技術支持團隊。

---

**注意**: 本功能需要實際的區塊鏈網絡連接才能完全運行。在開發環境中，某些功能可能為模擬實現。 