// 支付處理 - 4D科技風格自動贊助系統
// 專注於速買配整合和多支付方式支援

// 支付配置
const PaymentConfig = {
    SPEEDPAY: {
        name: '速買配',
        logo: '/assets/payment-logos/speedpay.png',
        enabled: true,
        priority: 1,
        methods: ['credit_card', 'atm', 'convenience_store', 'virtual_account']
    },
    ECPAY: {
        name: '綠界科技',
        logo: '/assets/payment-logos/ecpay.png',
        enabled: true,
        priority: 2,
        methods: ['credit_card', 'atm', 'convenience_store']
    },
    NEWEBPAY: {
        name: '藍新金流',
        logo: '/assets/payment-logos/newebpay.png',
        enabled: true,
        priority: 3,
        methods: ['credit_card', 'atm', 'webatm']
    },
    USDT: {
        name: 'USDT 加密貨幣',
        logo: '/assets/payment-logos/usdt-logo.svg',
        enabled: true,
        priority: 4,
        methods: ['erc20', 'trc20'],
        networks: {
            erc20: {
                name: 'ERC-20 (以太坊)',
                wallet_address: '0x732b0b53435977b03c4cef6b7bdffc45e6ec44e6',
                fee_rate: 0.005,
                processing_time: '5-30分鐘',
                explorer_url: 'https://etherscan.io/tx/'
            },
            trc20: {
                name: 'TRC-20 (波場)',
                wallet_address: 'TDejRjcLQa92rrE6SB71LSC7J5VmHs35gq',
                fee_rate: 0.003,
                processing_time: '1-5分鐘',
                explorer_url: 'https://tronscan.org/#/transaction/'
            }
        }
    }
};

// 支付狀態
const PaymentStatus = {
    PENDING: 'pending',
    PROCESSING: 'processing',
    SUCCESS: 'success',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
    EXPIRED: 'expired'
};

// 支付管理器
class PaymentManager {
    constructor() {
        this.currentOrder = null;
        this.selectedGateway = 'SPEEDPAY';
        this.selectedMethod = null;
        this.paymentTimer = null;
        this.statusCheckInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPaymentMethods();
        this.initPaymentForm();
        console.log('💳 支付系統已初始化');
    }

    // 設置事件監聽器
    setupEventListeners() {
        // 支付方式選擇
        document.querySelectorAll('.payment-gateway').forEach(gateway => {
            gateway.addEventListener('click', (e) => {
                this.selectPaymentGateway(e.currentTarget.dataset.gateway);
            });
        });

        // 支付方法選擇
        document.querySelectorAll('.payment-method').forEach(method => {
            method.addEventListener('click', (e) => {
                this.selectPaymentMethod(e.currentTarget.dataset.method);
            });
        });

        // 支付按鈕
        const payButton = document.getElementById('payButton');
        if (payButton) {
            payButton.addEventListener('click', () => this.processPayment());
        }

        // 取消支付
        const cancelButton = document.getElementById('cancelPayment');
        if (cancelButton) {
            cancelButton.addEventListener('click', () => this.cancelPayment());
        }

        // 重新支付
        const retryButton = document.getElementById('retryPayment');
        if (retryButton) {
            retryButton.addEventListener('click', () => this.retryPayment());
        }

        // 表單驗證
        const paymentForm = document.getElementById('paymentForm');
        if (paymentForm) {
            paymentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.processPayment();
            });
        }
    }

    // 載入支付方式
    loadPaymentMethods() {
        const gatewayContainer = document.querySelector('.payment-gateways');
        if (!gatewayContainer) return;

        gatewayContainer.innerHTML = '';

        // 按優先級排序
        const sortedGateways = Object.entries(PaymentConfig)
            .sort(([,a], [,b]) => a.priority - b.priority)
            .filter(([,config]) => config.enabled);

        sortedGateways.forEach(([key, config]) => {
            const gatewayElement = this.createGatewayElement(key, config);
            gatewayContainer.appendChild(gatewayElement);
        });

        // 默認選擇第一個
        if (sortedGateways.length > 0) {
            this.selectPaymentGateway(sortedGateways[0][0]);
        }
    }

    // 創建支付閘道元素
    createGatewayElement(key, config) {
        const element = document.createElement('div');
        element.className = `payment-gateway ${key === 'SPEEDPAY' ? 'recommended' : ''}`;
        element.dataset.gateway = key;
        
        element.innerHTML = `
            <div class="gateway-content">
                <div class="gateway-logo">
                    <img src="${config.logo}" alt="${config.name}" onerror="this.style.display='none'">
                </div>
                <div class="gateway-info">
                    <h3>${config.name}</h3>
                    ${key === 'SPEEDPAY' ? '<span class="recommended-badge">推薦</span>' : ''}
                    <div class="gateway-methods">
                        ${config.methods.map(method => `<span class="method-tag">${this.getMethodName(method)}</span>`).join('')}
                    </div>
                </div>
                <div class="gateway-status">
                    <div class="status-indicator"></div>
                </div>
            </div>
        `;

        return element;
    }

    // 獲取支付方法名稱
    getMethodName(method) {
        const methodNames = {
            'credit_card': '信用卡',
            'atm': 'ATM轉帳',
            'convenience_store': '超商代碼',
            'virtual_account': '虛擬帳號',
            'webatm': '網路ATM'
        };
        return methodNames[method] || method;
    }

    // 選擇支付閘道
    selectPaymentGateway(gateway) {
        // 移除之前的選擇
        document.querySelectorAll('.payment-gateway').forEach(el => {
            el.classList.remove('selected');
        });

        // 選擇新的閘道
        const selectedGateway = document.querySelector(`[data-gateway="${gateway}"]`);
        if (selectedGateway) {
            selectedGateway.classList.add('selected');
            this.selectedGateway = gateway;
            this.loadPaymentMethodsForGateway(gateway);
            this.updatePaymentForm();
        }
    }

    // 載入指定閘道的支付方法
    loadPaymentMethodsForGateway(gateway) {
        const methodContainer = document.querySelector('.payment-methods');
        if (!methodContainer) return;

        const config = PaymentConfig[gateway];
        if (!config) return;

        methodContainer.innerHTML = '';
        
        config.methods.forEach(method => {
            const methodElement = this.createMethodElement(method);
            methodContainer.appendChild(methodElement);
        });

        // 默認選擇第一個方法
        if (config.methods.length > 0) {
            this.selectPaymentMethod(config.methods[0]);
        }
    }

    // 創建支付方法元素
    createMethodElement(method) {
        const element = document.createElement('div');
        element.className = 'payment-method';
        element.dataset.method = method;
        
        element.innerHTML = `
            <div class="method-content">
                <div class="method-icon">
                    <i class="${this.getMethodIcon(method)}"></i>
                </div>
                <div class="method-info">
                    <h4>${this.getMethodName(method)}</h4>
                    <p>${this.getMethodDescription(method)}</p>
                </div>
                <div class="method-select">
                    <div class="radio-button"></div>
                </div>
            </div>
        `;

        return element;
    }

    // 獲取支付方法圖標
    getMethodIcon(method) {
        const methodIcons = {
            'credit_card': 'fas fa-credit-card',
            'atm': 'fas fa-university',
            'convenience_store': 'fas fa-store',
            'virtual_account': 'fas fa-file-invoice-dollar',
            'webatm': 'fas fa-laptop'
        };
        return methodIcons[method] || 'fas fa-payment';
    }

    // 獲取支付方法描述
    getMethodDescription(method) {
        const descriptions = {
            'credit_card': '支援Visa、MasterCard、JCB等信用卡',
            'atm': '透過ATM轉帳，手續費較低',
            'convenience_store': '7-11、全家、萊爾富等超商繳費',
            'virtual_account': '銀行虛擬帳號轉帳',
            'webatm': '網路ATM即時轉帳'
        };
        return descriptions[method] || '安全便捷的支付方式';
    }

    // 選擇支付方法
    selectPaymentMethod(method) {
        // 移除之前的選擇
        document.querySelectorAll('.payment-method').forEach(el => {
            el.classList.remove('selected');
        });

        // 選擇新的方法
        const selectedMethod = document.querySelector(`[data-method="${method}"]`);
        if (selectedMethod) {
            selectedMethod.classList.add('selected');
            this.selectedMethod = method;
            this.updatePaymentForm();
        }
    }

    // 初始化支付表單
    initPaymentForm() {
        const form = document.getElementById('paymentForm');
        if (!form) return;

        // 添加表單驗證
        this.setupFormValidation(form);
    }

    // 設置表單驗證
    setupFormValidation(form) {
        const inputs = form.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    // 驗證字段
    validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name;
        let isValid = true;
        let errorMessage = '';

        // 基本必填驗證
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = '此欄位為必填';
        }

        // 特定字段驗證
        if (value && fieldName === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = '請輸入有效的電子郵件地址';
            }
        }

        if (value && fieldName === 'phone') {
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(value.replace(/[\s-]/g, ''))) {
                isValid = false;
                errorMessage = '請輸入有效的手機號碼';
            }
        }

        // 顯示錯誤
        this.showFieldError(field, isValid ? '' : errorMessage);
        return isValid;
    }

    // 顯示字段錯誤
    showFieldError(field, message) {
        const errorElement = field.parentNode.querySelector('.field-error');
        
        if (message) {
            field.classList.add('error');
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.style.display = 'block';
            }
        } else {
            field.classList.remove('error');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        }
    }

    // 清除字段錯誤
    clearFieldError(field) {
        field.classList.remove('error');
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    // 更新支付表單
    updatePaymentForm() {
        const payButton = document.getElementById('payButton');
        if (payButton) {
            payButton.disabled = !this.selectedGateway || !this.selectedMethod;
            
            if (this.selectedGateway && this.selectedMethod) {
                const gatewayName = PaymentConfig[this.selectedGateway].name;
                const methodName = this.getMethodName(this.selectedMethod);
                payButton.innerHTML = `
                    <i class="fas fa-lock"></i>
                    使用 ${gatewayName} - ${methodName} 付款
                `;
            }
        }
    }

    // 處理支付
    async processPayment() {
        try {
            // 驗證表單
            if (!this.validatePaymentForm()) {
                return;
            }

            // 顯示處理中狀態
            this.showPaymentStatus('processing');

            // 收集支付數據
            const paymentData = this.collectPaymentData();

            // 創建訂單
            const order = await this.createOrder(paymentData);
            this.currentOrder = order;

            // 根據選擇的閘道處理支付
            let paymentResult;
            switch (this.selectedGateway) {
                case 'SPEEDPAY':
                    paymentResult = await this.processSpeedPayPayment(order);
                    break;
                case 'ECPAY':
                    paymentResult = await this.processECPayPayment(order);
                    break;
                case 'NEWEBPAY':
                    paymentResult = await this.processNewebPayPayment(order);
                    break;
                case 'USDT':
                    paymentResult = await this.processUSDTPayment(order);
                    break;
                default:
                    throw new Error('不支援的支付閘道');
            }

            // 處理支付結果
            this.handlePaymentResult(paymentResult);

        } catch (error) {
            console.error('支付處理失敗:', error);
            this.showPaymentStatus('failed', error.message);
        }
    }

    // 驗證支付表單
    validatePaymentForm() {
        const form = document.getElementById('paymentForm');
        if (!form) return false;

        const requiredFields = form.querySelectorAll('input[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        if (!this.selectedGateway || !this.selectedMethod) {
            this.showError('請選擇支付方式');
            isValid = false;
        }

        return isValid;
    }

    // 收集支付數據
    collectPaymentData() {
        const form = document.getElementById('paymentForm');
        const formData = new FormData(form);
        
        const data = {
            gateway: this.selectedGateway,
            method: this.selectedMethod,
            amount: this.getOrderAmount(),
            currency: 'TWD',
            customer: {
                name: formData.get('customerName'),
                email: formData.get('customerEmail'),
                phone: formData.get('customerPhone')
            },
            items: this.getOrderItems(),
            returnUrl: `${window.location.origin}/payment/return`,
            notifyUrl: `${window.location.origin}/api/payment/notify`
        };

        return data;
    }

    // 獲取訂單金額
    getOrderAmount() {
        const amountElement = document.querySelector('[data-order-amount]');
        return amountElement ? parseInt(amountElement.textContent.replace(/[^0-9]/g, '')) : 0;
    }

    // 獲取訂單項目
    getOrderItems() {
        const items = [];
        document.querySelectorAll('[data-order-item]').forEach(item => {
            items.push({
                name: item.dataset.itemName,
                price: parseInt(item.dataset.itemPrice),
                quantity: parseInt(item.dataset.itemQuantity) || 1
            });
        });
        return items;
    }

    // 創建訂單
    async createOrder(paymentData) {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
            body: JSON.stringify(paymentData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '訂單創建失敗');
        }

        return await response.json();
    }

    // 處理速買配支付
    async processSpeedPayPayment(order) {
        // 調用速買配API
        const response = await fetch('/api/payment/speedpay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orderId: order.id,
                method: this.selectedMethod
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '速買配支付失敗');
        }

        return await response.json();
    }

    // 處理綠界支付
    async processECPayPayment(order) {
        const response = await fetch('/api/payment/ecpay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orderId: order.id,
                method: this.selectedMethod
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '綠界支付失敗');
        }

        return await response.json();
    }

    // 處理藍新支付
    async processNewebPayPayment(order) {
        const response = await fetch('/api/payment/newebpay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orderId: order.id,
                method: this.selectedMethod
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '藍新支付失敗');
        }

        return await response.json();
    }

    // 處理USDT支付
    async processUSDTPayment(order) {
        // 實現USDT支付的處理邏輯
        // 這裡需要根據實際的USDT支付方式來實現
        throw new Error('USDT支付處理邏輯尚未實現');
    }

    // 處理支付結果
    handlePaymentResult(result) {
        if (result.success) {
            if (result.redirectUrl) {
                // 跳轉到支付頁面
                window.location.href = result.redirectUrl;
            } else {
                // 顯示支付成功
                this.showPaymentStatus('success', result.message);
                this.startStatusCheck(result.orderId);
            }
        } else {
            this.showPaymentStatus('failed', result.message);
        }
    }

    // 開始狀態檢查
    startStatusCheck(orderId) {
        this.statusCheckInterval = setInterval(async () => {
            try {
                const status = await this.checkPaymentStatus(orderId);
                if (status.status !== PaymentStatus.PENDING && status.status !== PaymentStatus.PROCESSING) {
                    this.stopStatusCheck();
                    this.handleFinalStatus(status);
                }
            } catch (error) {
                console.error('狀態檢查失敗:', error);
            }
        }, 3000);

        // 設置超時
        this.paymentTimer = setTimeout(() => {
            this.stopStatusCheck();
            this.showPaymentStatus('expired', '支付超時，請重新嘗試');
        }, 300000); // 5分鐘
    }

    // 停止狀態檢查
    stopStatusCheck() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
        if (this.paymentTimer) {
            clearTimeout(this.paymentTimer);
            this.paymentTimer = null;
        }
    }

    // 檢查支付狀態
    async checkPaymentStatus(orderId) {
        const response = await fetch(`/api/orders/${orderId}/status`);
        if (!response.ok) {
            throw new Error('狀態檢查失敗');
        }
        return await response.json();
    }

    // 處理最終狀態
    handleFinalStatus(status) {
        switch (status.status) {
            case PaymentStatus.SUCCESS:
                this.showPaymentStatus('success', '支付成功！');
                setTimeout(() => {
                    window.location.href = '/user-dashboard.html';
                }, 2000);
                break;
            case PaymentStatus.FAILED:
                this.showPaymentStatus('failed', status.message || '支付失敗');
                break;
            case PaymentStatus.CANCELLED:
                this.showPaymentStatus('cancelled', '支付已取消');
                break;
            default:
                this.showPaymentStatus('failed', '未知的支付狀態');
        }
    }

    // 顯示支付狀態
    showPaymentStatus(status, message = '') {
        const statusContainer = document.querySelector('.payment-status');
        if (!statusContainer) return;

        statusContainer.className = `payment-status ${status}`;
        statusContainer.style.display = 'block';

        const statusIcon = statusContainer.querySelector('.status-icon');
        const statusText = statusContainer.querySelector('.status-text');
        const statusMessage = statusContainer.querySelector('.status-message');

        // 更新圖標
        if (statusIcon) {
            const icons = {
                'processing': 'fas fa-spinner fa-spin',
                'success': 'fas fa-check-circle',
                'failed': 'fas fa-times-circle',
                'cancelled': 'fas fa-ban',
                'expired': 'fas fa-clock'
            };
            statusIcon.className = `status-icon ${icons[status] || 'fas fa-question-circle'}`;
        }

        // 更新文字
        if (statusText) {
            const texts = {
                'processing': '處理中...',
                'success': '支付成功',
                'failed': '支付失敗',
                'cancelled': '支付取消',
                'expired': '支付超時'
            };
            statusText.textContent = texts[status] || '未知狀態';
        }

        // 更新消息
        if (statusMessage) {
            statusMessage.textContent = message;
        }

        // 隱藏支付表單
        const paymentForm = document.querySelector('.payment-form');
        if (paymentForm && status !== 'processing') {
            paymentForm.style.display = 'none';
        }
    }

    // 取消支付
    cancelPayment() {
        this.stopStatusCheck();
        
        if (this.currentOrder) {
            // 通知後端取消訂單
            fetch(`/api/orders/${this.currentOrder.id}/cancel`, {
                method: 'POST'
            }).catch(error => {
                console.error('取消訂單失敗:', error);
            });
        }

        this.showPaymentStatus('cancelled', '支付已取消');
    }

    // 重新支付
    retryPayment() {
        // 重置狀態
        this.currentOrder = null;
        this.stopStatusCheck();
        
        // 隱藏狀態顯示
        const statusContainer = document.querySelector('.payment-status');
        if (statusContainer) {
            statusContainer.style.display = 'none';
        }

        // 顯示支付表單
        const paymentForm = document.querySelector('.payment-form');
        if (paymentForm) {
            paymentForm.style.display = 'block';
        }
    }

    // 顯示錯誤
    showError(message) {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showError(message);
        } else {
            alert(message);
        }
    }

    // 顯示成功
    showSuccess(message) {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showSuccess(message);
        } else {
            alert(message);
        }
    }
}

// 支付工具函數
const PaymentUtils = {
    // 格式化金額
    formatAmount(amount) {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD',
            minimumFractionDigits: 0
        }).format(amount);
    },

    // 驗證信用卡號
    validateCreditCard(number) {
        const cleaned = number.replace(/\s/g, '');
        const regex = /^[0-9]{13,19}$/;
        return regex.test(cleaned);
    },

    // 驗證CVV
    validateCVV(cvv) {
        const regex = /^[0-9]{3,4}$/;
        return regex.test(cvv);
    },

    // 驗證到期日
    validateExpiryDate(month, year) {
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        
        const expYear = parseInt(year);
        const expMonth = parseInt(month);
        
        if (expYear < currentYear) return false;
        if (expYear === currentYear && expMonth < currentMonth) return false;
        
        return true;
    }
};

// 初始化支付管理器
let paymentManager;
document.addEventListener('DOMContentLoaded', () => {
    paymentManager = new PaymentManager();
});

// 導出全局對象
window.JyPayment = {
    manager: () => paymentManager,
    utils: PaymentUtils,
    config: PaymentConfig,
    status: PaymentStatus
};

console.log('💳 支付系統模組已載入');