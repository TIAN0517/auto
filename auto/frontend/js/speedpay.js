// 速買配專用JavaScript - 4D科技風格自動贊助系統
// SpeedPay Integration Module

// 速買配配置
const SpeedPayConfig = {
    API_VERSION: 'v1',
    TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
    SUPPORTED_METHODS: {
        CREDIT_CARD: {
            code: 'CC',
            name: '信用卡',
            icon: 'fas fa-credit-card',
            description: '支援Visa、MasterCard、JCB等主要信用卡',
            processingTime: '即時',
            fee: '2.8%'
        },
        ATM: {
            code: 'ATM',
            name: 'ATM轉帳',
            icon: 'fas fa-university',
            description: '透過ATM進行轉帳，手續費較低',
            processingTime: '1-3個工作天',
            fee: 'NT$15'
        },
        CONVENIENCE_STORE: {
            code: 'CVS',
            name: '超商代碼',
            icon: 'fas fa-store',
            description: '7-11、全家、萊爾富等超商繳費',
            processingTime: '即時確認',
            fee: 'NT$25'
        },
        VIRTUAL_ACCOUNT: {
            code: 'VACC',
            name: '虛擬帳號',
            icon: 'fas fa-file-invoice-dollar',
            description: '銀行虛擬帳號轉帳',
            processingTime: '即時確認',
            fee: 'NT$10'
        }
    },
    BANKS: {
        '004': '台灣銀行',
        '005': '土地銀行',
        '006': '合作金庫',
        '007': '第一銀行',
        '008': '華南銀行',
        '009': '彰化銀行',
        '011': '上海銀行',
        '012': '台北富邦',
        '013': '國泰世華',
        '017': '兆豐銀行'
    }
};

// 速買配API管理器
class SpeedPayManager {
    constructor() {
        this.apiKey = null;
        this.merchantId = null;
        this.environment = 'sandbox'; // sandbox | production
        this.baseUrl = this.getBaseUrl();
        this.currentTransaction = null;
        this.init();
    }

    init() {
        this.loadConfiguration();
        this.setupEventHandlers();
        console.log('🚀 速買配系統已初始化');
    }

    // 載入配置
    async loadConfiguration() {
        try {
            const response = await fetch('/api/speedpay/config');
            if (response.ok) {
                const config = await response.json();
                this.apiKey = config.apiKey;
                this.merchantId = config.merchantId;
                this.environment = config.environment || 'sandbox';
                this.baseUrl = this.getBaseUrl();
            }
        } catch (error) {
            console.error('載入速買配配置失敗:', error);
        }
    }

    // 獲取API基礎URL
    getBaseUrl() {
        return this.environment === 'production' 
            ? 'https://api.speedpay.com.tw'
            : 'https://sandbox-api.speedpay.com.tw';
    }

    // 設置事件處理器
    setupEventHandlers() {
        // 監聽支付方式變更
        document.addEventListener('speedpay:methodChanged', (e) => {
            this.handleMethodChange(e.detail);
        });

        // 監聽支付狀態更新
        document.addEventListener('speedpay:statusUpdate', (e) => {
            this.handleStatusUpdate(e.detail);
        });
    }

    // 創建支付訂單
    async createPayment(orderData) {
        try {
            this.showProcessing('正在創建支付訂單...');

            const paymentData = this.preparePaymentData(orderData);
            const response = await this.apiCall('/payments', 'POST', paymentData);

            if (response.success) {
                this.currentTransaction = response.data;
                return this.handlePaymentCreated(response.data);
            } else {
                throw new Error(response.message || '創建支付訂單失敗');
            }
        } catch (error) {
            console.error('創建支付失敗:', error);
            this.showError(error.message);
            throw error;
        }
    }

    // 準備支付數據
    preparePaymentData(orderData) {
        const timestamp = Date.now();
        const orderId = orderData.orderId || `SP${timestamp}`;
        
        const paymentData = {
            merchant_id: this.merchantId,
            order_id: orderId,
            amount: orderData.amount,
            currency: 'TWD',
            payment_method: orderData.method,
            description: orderData.description || '自動贊助系統付款',
            customer: {
                name: orderData.customer.name,
                email: orderData.customer.email,
                phone: orderData.customer.phone
            },
            return_url: orderData.returnUrl || `${window.location.origin}/payment/return`,
            notify_url: orderData.notifyUrl || `${window.location.origin}/api/speedpay/notify`,
            timestamp: timestamp
        };

        // 添加簽名
        paymentData.signature = this.generateSignature(paymentData);
        
        return paymentData;
    }

    // 生成簽名
    generateSignature(data) {
        // 排序參數
        const sortedKeys = Object.keys(data)
            .filter(key => key !== 'signature' && data[key] !== null && data[key] !== '')
            .sort();
        
        // 組合簽名字符串
        const signString = sortedKeys
            .map(key => `${key}=${data[key]}`)
            .join('&') + `&key=${this.apiKey}`;
        
        // 使用SHA256加密（實際應用中需要後端處理）
        return this.sha256(signString).toUpperCase();
    }

    // SHA256加密（簡化版，實際應用需要後端處理）
    sha256(str) {
        // 這裡應該調用後端API來生成簽名
        // 為了演示，返回一個模擬的簽名
        return 'MOCK_SIGNATURE_' + btoa(str).substring(0, 32);
    }

    // 處理支付創建成功
    handlePaymentCreated(paymentData) {
        const method = paymentData.payment_method;
        
        switch (method) {
            case 'CC':
                return this.handleCreditCardPayment(paymentData);
            case 'ATM':
                return this.handleATMPayment(paymentData);
            case 'CVS':
                return this.handleConvenienceStorePayment(paymentData);
            case 'VACC':
                return this.handleVirtualAccountPayment(paymentData);
            default:
                throw new Error(`不支援的支付方式: ${method}`);
        }
    }

    // 處理信用卡支付
    handleCreditCardPayment(paymentData) {
        if (paymentData.redirect_url) {
            // 跳轉到速買配支付頁面
            this.showProcessing('正在跳轉到支付頁面...');
            setTimeout(() => {
                window.location.href = paymentData.redirect_url;
            }, 1000);
        } else {
            // 顯示信用卡表單
            this.showCreditCardForm(paymentData);
        }
        
        return {
            success: true,
            method: 'credit_card',
            data: paymentData
        };
    }

    // 處理ATM支付
    handleATMPayment(paymentData) {
        this.showATMInstructions(paymentData);
        this.startPaymentStatusCheck(paymentData.transaction_id);
        
        return {
            success: true,
            method: 'atm',
            data: paymentData
        };
    }

    // 處理超商支付
    handleConvenienceStorePayment(paymentData) {
        this.showConvenienceStoreInstructions(paymentData);
        this.startPaymentStatusCheck(paymentData.transaction_id);
        
        return {
            success: true,
            method: 'convenience_store',
            data: paymentData
        };
    }

    // 處理虛擬帳號支付
    handleVirtualAccountPayment(paymentData) {
        this.showVirtualAccountInstructions(paymentData);
        this.startPaymentStatusCheck(paymentData.transaction_id);
        
        return {
            success: true,
            method: 'virtual_account',
            data: paymentData
        };
    }

    // 顯示信用卡表單
    showCreditCardForm(paymentData) {
        const container = document.querySelector('.speedpay-container');
        if (!container) return;

        container.innerHTML = `
            <div class="speedpay-credit-card">
                <div class="payment-header">
                    <h3><i class="fas fa-credit-card"></i> 信用卡支付</h3>
                    <div class="amount">金額: ${this.formatAmount(paymentData.amount)}</div>
                </div>
                
                <form id="speedpayCreditCardForm" class="credit-card-form">
                    <div class="form-group">
                        <label>卡號</label>
                        <input type="text" name="card_number" placeholder="1234 5678 9012 3456" 
                               maxlength="19" required autocomplete="cc-number">
                        <div class="card-types">
                            <img src="/assets/payment-logos/visa.png" alt="Visa">
                            <img src="/assets/payment-logos/mastercard.png" alt="MasterCard">
                            <img src="/assets/payment-logos/jcb.png" alt="JCB">
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>到期日</label>
                            <input type="text" name="expiry_date" placeholder="MM/YY" 
                                   maxlength="5" required autocomplete="cc-exp">
                        </div>
                        <div class="form-group">
                            <label>CVV</label>
                            <input type="text" name="cvv" placeholder="123" 
                                   maxlength="4" required autocomplete="cc-csc">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>持卡人姓名</label>
                        <input type="text" name="cardholder_name" 
                               placeholder="請輸入持卡人姓名" required autocomplete="cc-name">
                    </div>
                    
                    <div class="security-info">
                        <i class="fas fa-shield-alt"></i>
                        <span>您的支付資訊受到SSL加密保護</span>
                    </div>
                    
                    <button type="submit" class="pay-button">
                        <i class="fas fa-lock"></i>
                        確認付款 ${this.formatAmount(paymentData.amount)}
                    </button>
                </form>
            </div>
        `;

        // 設置表單事件
        this.setupCreditCardForm();
    }

    // 設置信用卡表單
    setupCreditCardForm() {
        const form = document.getElementById('speedpayCreditCardForm');
        if (!form) return;

        // 卡號格式化
        const cardNumberInput = form.querySelector('[name="card_number"]');
        cardNumberInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.replace(/(\d{4})(?=\d)/g, '$1 ');
            e.target.value = formattedValue;
        });

        // 到期日格式化
        const expiryInput = form.querySelector('[name="expiry_date"]');
        expiryInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            e.target.value = value;
        });

        // CVV只允許數字
        const cvvInput = form.querySelector('[name="cvv"]');
        cvvInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '');
        });

        // 表單提交
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitCreditCardPayment(form);
        });
    }

    // 提交信用卡支付
    async submitCreditCardPayment(form) {
        try {
            const formData = new FormData(form);
            const cardData = {
                transaction_id: this.currentTransaction.transaction_id,
                card_number: formData.get('card_number').replace(/\s/g, ''),
                expiry_date: formData.get('expiry_date'),
                cvv: formData.get('cvv'),
                cardholder_name: formData.get('cardholder_name')
            };

            this.showProcessing('正在處理支付...');
            
            const response = await this.apiCall('/payments/credit-card', 'POST', cardData);
            
            if (response.success) {
                this.showSuccess('支付成功！');
                this.handlePaymentSuccess(response.data);
            } else {
                throw new Error(response.message || '支付失敗');
            }
        } catch (error) {
            console.error('信用卡支付失敗:', error);
            this.showError(error.message);
        }
    }

    // 顯示ATM轉帳說明
    showATMInstructions(paymentData) {
        const container = document.querySelector('.speedpay-container');
        if (!container) return;

        const bankName = SpeedPayConfig.BANKS[paymentData.bank_code] || '指定銀行';
        
        container.innerHTML = `
            <div class="speedpay-atm">
                <div class="payment-header">
                    <h3><i class="fas fa-university"></i> ATM轉帳</h3>
                    <div class="amount">金額: ${this.formatAmount(paymentData.amount)}</div>
                </div>
                
                <div class="atm-instructions">
                    <div class="bank-info">
                        <h4>轉帳銀行</h4>
                        <div class="bank-details">
                            <span class="bank-code">${paymentData.bank_code}</span>
                            <span class="bank-name">${bankName}</span>
                        </div>
                    </div>
                    
                    <div class="account-info">
                        <h4>轉帳帳號</h4>
                        <div class="account-number">
                            ${paymentData.virtual_account}
                            <button class="copy-btn" onclick="navigator.clipboard.writeText('${paymentData.virtual_account}')">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="amount-info">
                        <h4>轉帳金額</h4>
                        <div class="transfer-amount">
                            NT$ ${paymentData.amount.toLocaleString()}
                            <button class="copy-btn" onclick="navigator.clipboard.writeText('${paymentData.amount}')">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="deadline-info">
                        <h4>繳費期限</h4>
                        <div class="deadline">${this.formatDate(paymentData.expire_time)}</div>
                    </div>
                    
                    <div class="instructions-list">
                        <h4>轉帳步驟</h4>
                        <ol>
                            <li>前往任一ATM或網路銀行</li>
                            <li>選擇「轉帳」功能</li>
                            <li>輸入轉入銀行代碼：${paymentData.bank_code}</li>
                            <li>輸入轉入帳號：${paymentData.virtual_account}</li>
                            <li>輸入轉帳金額：${paymentData.amount}</li>
                            <li>確認轉帳並保留收據</li>
                        </ol>
                    </div>
                    
                    <div class="status-check">
                        <div class="status-indicator processing">
                            <i class="fas fa-clock"></i>
                            <span>等待轉帳確認中...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 顯示超商繳費說明
    showConvenienceStoreInstructions(paymentData) {
        const container = document.querySelector('.speedpay-container');
        if (!container) return;

        container.innerHTML = `
            <div class="speedpay-cvs">
                <div class="payment-header">
                    <h3><i class="fas fa-store"></i> 超商代碼繳費</h3>
                    <div class="amount">金額: ${this.formatAmount(paymentData.amount)}</div>
                </div>
                
                <div class="cvs-instructions">
                    <div class="payment-code">
                        <h4>繳費代碼</h4>
                        <div class="code-display">
                            ${paymentData.payment_code}
                            <button class="copy-btn" onclick="navigator.clipboard.writeText('${paymentData.payment_code}')">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="supported-stores">
                        <h4>支援超商</h4>
                        <div class="store-logos">
                            <div class="store-item">
                                <img src="/assets/payment-logos/7-11.png" alt="7-11">
                                <span>7-11</span>
                            </div>
                            <div class="store-item">
                                <img src="/assets/payment-logos/family.png" alt="全家">
                                <span>全家</span>
                            </div>
                            <div class="store-item">
                                <img src="/assets/payment-logos/hilife.png" alt="萊爾富">
                                <span>萊爾富</span>
                            </div>
                            <div class="store-item">
                                <img src="/assets/payment-logos/okmart.png" alt="OK超商">
                                <span>OK超商</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="deadline-info">
                        <h4>繳費期限</h4>
                        <div class="deadline">${this.formatDate(paymentData.expire_time)}</div>
                    </div>
                    
                    <div class="instructions-list">
                        <h4>繳費步驟</h4>
                        <ol>
                            <li>前往支援的超商門市</li>
                            <li>告知店員要使用「代碼繳費」</li>
                            <li>提供繳費代碼：${paymentData.payment_code}</li>
                            <li>確認金額：NT$ ${paymentData.amount.toLocaleString()}</li>
                            <li>完成付款並保留收據</li>
                        </ol>
                    </div>
                    
                    <div class="status-check">
                        <div class="status-indicator processing">
                            <i class="fas fa-clock"></i>
                            <span>等待繳費確認中...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 顯示虛擬帳號說明
    showVirtualAccountInstructions(paymentData) {
        const container = document.querySelector('.speedpay-container');
        if (!container) return;

        const bankName = SpeedPayConfig.BANKS[paymentData.bank_code] || '指定銀行';
        
        container.innerHTML = `
            <div class="speedpay-vacc">
                <div class="payment-header">
                    <h3><i class="fas fa-file-invoice-dollar"></i> 虛擬帳號轉帳</h3>
                    <div class="amount">金額: ${this.formatAmount(paymentData.amount)}</div>
                </div>
                
                <div class="vacc-instructions">
                    <div class="account-details">
                        <div class="bank-info">
                            <h4>收款銀行</h4>
                            <div class="bank-details">
                                <span class="bank-code">${paymentData.bank_code}</span>
                                <span class="bank-name">${bankName}</span>
                            </div>
                        </div>
                        
                        <div class="account-info">
                            <h4>虛擬帳號</h4>
                            <div class="account-number">
                                ${paymentData.virtual_account}
                                <button class="copy-btn" onclick="navigator.clipboard.writeText('${paymentData.virtual_account}')">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="amount-info">
                            <h4>轉帳金額</h4>
                            <div class="transfer-amount">
                                NT$ ${paymentData.amount.toLocaleString()}
                                <button class="copy-btn" onclick="navigator.clipboard.writeText('${paymentData.amount}')">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="deadline-info">
                            <h4>轉帳期限</h4>
                            <div class="deadline">${this.formatDate(paymentData.expire_time)}</div>
                        </div>
                    </div>
                    
                    <div class="qr-code-section">
                        <h4>QR Code 轉帳</h4>
                        <div class="qr-code">
                            <img src="${paymentData.qr_code_url}" alt="QR Code" onerror="this.style.display='none'">
                            <p>使用銀行APP掃描QR Code快速轉帳</p>
                        </div>
                    </div>
                    
                    <div class="instructions-list">
                        <h4>轉帳方式</h4>
                        <div class="method-tabs">
                            <button class="tab-btn active" onclick="showMethod('atm')">ATM轉帳</button>
                            <button class="tab-btn" onclick="showMethod('online')">網路銀行</button>
                            <button class="tab-btn" onclick="showMethod('app')">手機銀行</button>
                        </div>
                        
                        <div class="method-content" id="atm-method">
                            <ol>
                                <li>前往任一ATM</li>
                                <li>插入金融卡並輸入密碼</li>
                                <li>選擇「轉帳」功能</li>
                                <li>輸入銀行代碼：${paymentData.bank_code}</li>
                                <li>輸入帳號：${paymentData.virtual_account}</li>
                                <li>輸入金額：${paymentData.amount}</li>
                                <li>確認轉帳</li>
                            </ol>
                        </div>
                    </div>
                    
                    <div class="status-check">
                        <div class="status-indicator processing">
                            <i class="fas fa-clock"></i>
                            <span>等待轉帳確認中...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 開始支付狀態檢查
    startPaymentStatusCheck(transactionId) {
        this.statusCheckInterval = setInterval(async () => {
            try {
                const status = await this.checkPaymentStatus(transactionId);
                this.updatePaymentStatus(status);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(this.statusCheckInterval);
                    this.handleFinalStatus(status);
                }
            } catch (error) {
                console.error('狀態檢查失敗:', error);
            }
        }, 5000); // 每5秒檢查一次
    }

    // 檢查支付狀態
    async checkPaymentStatus(transactionId) {
        const response = await this.apiCall(`/payments/${transactionId}/status`, 'GET');
        return response.data;
    }

    // 更新支付狀態顯示
    updatePaymentStatus(status) {
        const statusIndicator = document.querySelector('.status-indicator');
        if (!statusIndicator) return;

        statusIndicator.className = `status-indicator ${status.status}`;
        
        const statusText = statusIndicator.querySelector('span');
        if (statusText) {
            const statusMessages = {
                'pending': '等待付款中...',
                'processing': '處理中...',
                'completed': '付款成功！',
                'failed': '付款失敗',
                'expired': '付款已過期'
            };
            statusText.textContent = statusMessages[status.status] || '未知狀態';
        }
    }

    // 處理最終狀態
    handleFinalStatus(status) {
        if (status.status === 'completed') {
            this.handlePaymentSuccess(status);
        } else {
            this.handlePaymentFailure(status);
        }
    }

    // 處理支付成功
    handlePaymentSuccess(data) {
        this.showSuccess('支付成功！正在跳轉...');
        
        // 觸發成功事件
        document.dispatchEvent(new CustomEvent('speedpay:paymentSuccess', {
            detail: data
        }));
        
        // 跳轉到成功頁面
        setTimeout(() => {
            window.location.href = '/user-dashboard.html?payment=success';
        }, 2000);
    }

    // 處理支付失敗
    handlePaymentFailure(data) {
        this.showError(data.message || '支付失敗，請重試');
        
        // 觸發失敗事件
        document.dispatchEvent(new CustomEvent('speedpay:paymentFailure', {
            detail: data
        }));
    }

    // API調用
    async apiCall(endpoint, method = 'GET', data = null) {
        const url = `/api/speedpay${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '請求失敗');
        }

        return await response.json();
    }

    // 處理方法變更
    handleMethodChange(method) {
        console.log('速買配支付方式變更:', method);
        // 可以在這裡添加方法變更的處理邏輯
    }

    // 處理狀態更新
    handleStatusUpdate(status) {
        console.log('速買配狀態更新:', status);
        this.updatePaymentStatus(status);
    }

    // 顯示處理中狀態
    showProcessing(message) {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showNotification(message, 'info');
        }
    }

    // 顯示成功消息
    showSuccess(message) {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showSuccess(message);
        }
    }

    // 顯示錯誤消息
    showError(message) {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showError(message);
        }
    }

    // 格式化金額
    formatAmount(amount) {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD',
            minimumFractionDigits: 0
        }).format(amount);
    }

    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }
}

// 速買配工具函數
const SpeedPayUtils = {
    // 驗證支付金額
    validateAmount(amount) {
        const numAmount = parseFloat(amount);
        return numAmount >= 1 && numAmount <= 1000000;
    },

    // 生成訂單ID
    generateOrderId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 8);
        return `SP${timestamp}${random}`.toUpperCase();
    },

    // 檢查支付方式是否可用
    isMethodAvailable(method) {
        return Object.keys(SpeedPayConfig.SUPPORTED_METHODS).includes(method.toUpperCase());
    },

    // 獲取支付方式信息
    getMethodInfo(method) {
        return SpeedPayConfig.SUPPORTED_METHODS[method.toUpperCase()];
    },

    // 計算手續費
    calculateFee(amount, method) {
        const methodInfo = this.getMethodInfo(method);
        if (!methodInfo) return 0;

        if (methodInfo.fee.includes('%')) {
            const percentage = parseFloat(methodInfo.fee.replace('%', ''));
            return Math.round(amount * percentage / 100);
        } else {
            return parseInt(methodInfo.fee.replace(/[^0-9]/g, ''));
        }
    }
};

// 初始化速買配管理器
let speedPayManager;
document.addEventListener('DOMContentLoaded', () => {
    speedPayManager = new SpeedPayManager();
});

// 導出全局對象
window.JySpeedPay = {
    manager: () => speedPayManager,
    utils: SpeedPayUtils,
    config: SpeedPayConfig
};

console.log('🚀 速買配模組已載入');