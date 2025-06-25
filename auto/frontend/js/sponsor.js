// 贊助頁面JavaScript - 4D科技風格自動贊助系統
// Sponsor Page Module

// 贊助配置
const SponsorConfig = {
    PACKAGES: {
        BASIC: {
            id: 'basic',
            name: '基礎套餐',
            price: 100,
            originalPrice: 150,
            features: [
                '基礎功能訪問',
                '7天有效期',
                '基礎客服支援',
                '標準處理速度'
            ],
            popular: false,
            color: '#74c0fc'
        },
        ADVANCED: {
            id: 'advanced',
            name: '進階套餐',
            price: 300,
            originalPrice: 450,
            features: [
                '進階功能訪問',
                '30天有效期',
                '優先客服支援',
                '快速處理速度',
                '專屬功能解鎖'
            ],
            popular: true,
            color: '#51cf66'
        },
        VIP: {
            id: 'vip',
            name: 'VIP套餐',
            price: 800,
            originalPrice: 1200,
            features: [
                '全功能訪問',
                '90天有效期',
                '24/7專屬客服',
                '極速處理',
                '所有功能解鎖',
                'VIP專屬特權'
            ],
            popular: false,
            color: '#ffd43b'
        },
        SUPREME: {
            id: 'supreme',
            name: '至尊套餐',
            price: 1500,
            originalPrice: 2000,
            features: [
                '終極功能訪問',
                '365天有效期',
                '專屬客戶經理',
                '瞬間處理',
                '全部功能解鎖',
                '至尊專屬特權',
                '定制化服務'
            ],
            popular: false,
            color: '#ff6b6b'
        }
    },
    PAYMENT_METHODS: {
        SPEEDPAY: {
            id: 'speedpay',
            name: '速買配',
            icon: 'fas fa-bolt',
            description: '台灣本土支付，快速安全',
            fee: '2.8%',
            processingTime: '即時',
            primary: true
        },
        ECPAY: {
            id: 'ecpay',
            name: '綠界科技',
            icon: 'fas fa-credit-card',
            description: '多元支付選擇',
            fee: '2.5%',
            processingTime: '即時',
            primary: false
        },
        NEWEBPAY: {
            id: 'newebpay',
            name: '藍新金流',
            icon: 'fas fa-university',
            description: '銀行級安全保障',
            fee: '2.2%',
            processingTime: '即時',
            primary: false
        }
    },
    DISCOUNT_CODES: {
        'WELCOME10': { discount: 10, type: 'percentage', description: '新用戶專享10%折扣' },
        'VIP20': { discount: 20, type: 'percentage', description: 'VIP用戶20%折扣' },
        'SAVE50': { discount: 50, type: 'fixed', description: '滿額減50元' }
    }
};

// 贊助頁面主類
class SponsorPage {
    constructor() {
        this.selectedPackage = null;
        this.selectedPaymentMethod = 'speedpay';
        this.discountCode = null;
        this.appliedDiscount = 0;
        this.userInfo = null;
        this.init();
    }

    init() {
        this.loadUserInfo();
        this.setupEventHandlers();
        this.initializePackages();
        this.initializePaymentMethods();
        this.setupAnimations();
        console.log('💎 贊助頁面已初始化');
    }

    // 載入用戶信息
    loadUserInfo() {
        const token = localStorage.getItem('token');
        if (token) {
            this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
        }
    }

    // 設置事件處理器
    setupEventHandlers() {
        // 套餐選擇
        document.querySelectorAll('.package-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const packageId = e.currentTarget.dataset.package;
                this.selectPackage(packageId);
            });
        });

        // 支付方式選擇
        document.querySelectorAll('.payment-method').forEach(method => {
            method.addEventListener('click', (e) => {
                const methodId = e.currentTarget.dataset.method;
                this.selectPaymentMethod(methodId);
            });
        });

        // 折扣碼輸入
        const discountInput = document.querySelector('#discount-code');
        const applyDiscountBtn = document.querySelector('#apply-discount');
        
        if (discountInput && applyDiscountBtn) {
            applyDiscountBtn.addEventListener('click', () => {
                this.applyDiscountCode(discountInput.value);
            });
            
            discountInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.applyDiscountCode(discountInput.value);
                }
            });
        }

        // 立即購買按鈕
        document.querySelectorAll('.buy-now-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const packageId = e.target.closest('.package-card').dataset.package;
                this.quickPurchase(packageId);
            });
        });

        // 確認購買按鈕
        const confirmBtn = document.querySelector('#confirm-purchase');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.confirmPurchase();
            });
        }

        // 模態框關閉
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay') || 
                e.target.classList.contains('modal-close')) {
                this.closeModal();
            }
        });

        // 鍵盤事件
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    // 初始化套餐
    initializePackages() {
        Object.entries(SponsorConfig.PACKAGES).forEach(([key, pkg]) => {
            const card = document.querySelector(`[data-package="${pkg.id}"]`);
            if (card) {
                this.updatePackageCard(card, pkg);
            }
        });
    }

    // 更新套餐卡片
    updatePackageCard(card, pkg) {
        // 設置價格
        const priceElement = card.querySelector('.package-price');
        if (priceElement) {
            priceElement.innerHTML = `
                <span class="current-price">NT$ ${pkg.price.toLocaleString()}</span>
                ${pkg.originalPrice ? `<span class="original-price">NT$ ${pkg.originalPrice.toLocaleString()}</span>` : ''}
            `;
        }

        // 設置特色
        const featuresElement = card.querySelector('.package-features');
        if (featuresElement) {
            featuresElement.innerHTML = pkg.features.map(feature => 
                `<li><i class="fas fa-check"></i> ${feature}</li>`
            ).join('');
        }

        // 設置熱門標籤
        if (pkg.popular) {
            card.classList.add('popular');
            const popularBadge = card.querySelector('.popular-badge');
            if (popularBadge) {
                popularBadge.style.display = 'block';
            }
        }

        // 設置主題色
        card.style.setProperty('--package-color', pkg.color);
    }

    // 初始化支付方式
    initializePaymentMethods() {
        const container = document.querySelector('.payment-methods');
        if (!container) return;

        container.innerHTML = Object.entries(SponsorConfig.PAYMENT_METHODS).map(([key, method]) => `
            <div class="payment-method ${method.primary ? 'primary' : ''}" data-method="${method.id}">
                <div class="method-icon">
                    <i class="${method.icon}"></i>
                </div>
                <div class="method-info">
                    <div class="method-name">${method.name}</div>
                    <div class="method-description">${method.description}</div>
                    <div class="method-details">
                        <span class="fee">手續費: ${method.fee}</span>
                        <span class="processing-time">處理時間: ${method.processingTime}</span>
                    </div>
                </div>
                ${method.primary ? '<div class="primary-badge">推薦</div>' : ''}
            </div>
        `).join('');

        // 默認選擇速買配
        this.selectPaymentMethod('speedpay');
    }

    // 選擇套餐
    selectPackage(packageId) {
        // 移除之前的選擇
        document.querySelectorAll('.package-card').forEach(card => {
            card.classList.remove('selected');
        });

        // 選擇新套餐
        const selectedCard = document.querySelector(`[data-package="${packageId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
            this.selectedPackage = SponsorConfig.PACKAGES[packageId.toUpperCase()];
            this.updateOrderSummary();
            this.showPackageDetails(this.selectedPackage);
        }
    }

    // 選擇支付方式
    selectPaymentMethod(methodId) {
        // 移除之前的選擇
        document.querySelectorAll('.payment-method').forEach(method => {
            method.classList.remove('selected');
        });

        // 選擇新支付方式
        const selectedMethod = document.querySelector(`[data-method="${methodId}"]`);
        if (selectedMethod) {
            selectedMethod.classList.add('selected');
            this.selectedPaymentMethod = methodId;
            this.updateOrderSummary();
        }
    }

    // 快速購買
    quickPurchase(packageId) {
        this.selectPackage(packageId);
        this.showPurchaseModal();
    }

    // 顯示套餐詳情
    showPackageDetails(pkg) {
        const detailsContainer = document.querySelector('.package-details');
        if (!detailsContainer) return;

        detailsContainer.innerHTML = `
            <div class="details-header">
                <h3>${pkg.name}</h3>
                <div class="price-info">
                    <span class="current-price">NT$ ${pkg.price.toLocaleString()}</span>
                    ${pkg.originalPrice ? `<span class="original-price">NT$ ${pkg.originalPrice.toLocaleString()}</span>` : ''}
                    ${pkg.originalPrice ? `<span class="discount-percent">省 ${Math.round((1 - pkg.price / pkg.originalPrice) * 100)}%</span>` : ''}
                </div>
            </div>
            <div class="details-features">
                <h4>套餐特色</h4>
                <ul>
                    ${pkg.features.map(feature => `<li><i class="fas fa-star"></i> ${feature}</li>`).join('')}
                </ul>
            </div>
            <div class="details-actions">
                <button class="btn btn-primary" onclick="sponsorPage.showPurchaseModal()">
                    <i class="fas fa-shopping-cart"></i>
                    立即購買
                </button>
            </div>
        `;

        detailsContainer.style.display = 'block';
    }

    // 顯示購買模態框
    showPurchaseModal() {
        if (!this.selectedPackage) {
            this.showNotification('請先選擇套餐', 'warning');
            return;
        }

        const modal = document.querySelector('#purchase-modal');
        if (!modal) return;

        this.updateModalContent();
        modal.style.display = 'flex';
        
        // 添加動畫
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    // 更新模態框內容
    updateModalContent() {
        const modal = document.querySelector('#purchase-modal');
        if (!modal) return;

        const content = modal.querySelector('.modal-content');
        content.innerHTML = `
            <div class="modal-header">
                <h3>確認購買</h3>
                <button class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="purchase-summary">
                    <div class="selected-package">
                        <h4>${this.selectedPackage.name}</h4>
                        <div class="package-price">
                            <span class="current-price">NT$ ${this.selectedPackage.price.toLocaleString()}</span>
                            ${this.selectedPackage.originalPrice ? `<span class="original-price">NT$ ${this.selectedPackage.originalPrice.toLocaleString()}</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="discount-section">
                        <div class="discount-input">
                            <input type="text" id="discount-code" placeholder="輸入折扣碼">
                            <button id="apply-discount" class="btn btn-secondary">套用</button>
                        </div>
                        ${this.discountCode ? `
                            <div class="applied-discount">
                                <i class="fas fa-tag"></i>
                                已套用折扣碼: ${this.discountCode}
                                <span class="discount-amount">-NT$ ${this.appliedDiscount}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="payment-method-selection">
                        <h4>選擇支付方式</h4>
                        <div class="payment-methods-modal">
                            ${Object.entries(SponsorConfig.PAYMENT_METHODS).map(([key, method]) => `
                                <div class="payment-option ${method.id === this.selectedPaymentMethod ? 'selected' : ''}" 
                                     data-method="${method.id}" onclick="sponsorPage.selectPaymentMethod('${method.id}')">
                                    <i class="${method.icon}"></i>
                                    <span>${method.name}</span>
                                    ${method.primary ? '<span class="primary-tag">推薦</span>' : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="order-total">
                        <div class="total-line">
                            <span>套餐價格</span>
                            <span>NT$ ${this.selectedPackage.price.toLocaleString()}</span>
                        </div>
                        ${this.appliedDiscount > 0 ? `
                            <div class="total-line discount">
                                <span>折扣</span>
                                <span>-NT$ ${this.appliedDiscount.toLocaleString()}</span>
                            </div>
                        ` : ''}
                        <div class="total-line fee">
                            <span>手續費</span>
                            <span>NT$ ${this.calculateFee()}</span>
                        </div>
                        <div class="total-line final">
                            <span>總計</span>
                            <span>NT$ ${this.calculateTotal().toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary modal-close">取消</button>
                <button class="btn btn-primary" id="confirm-purchase">
                    <i class="fas fa-credit-card"></i>
                    確認付款 NT$ ${this.calculateTotal().toLocaleString()}
                </button>
            </div>
        `;

        // 重新綁定事件
        this.setupModalEvents();
    }

    // 設置模態框事件
    setupModalEvents() {
        const discountInput = document.querySelector('#discount-code');
        const applyDiscountBtn = document.querySelector('#apply-discount');
        const confirmBtn = document.querySelector('#confirm-purchase');

        if (applyDiscountBtn) {
            applyDiscountBtn.addEventListener('click', () => {
                this.applyDiscountCode(discountInput.value);
            });
        }

        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.confirmPurchase();
            });
        }
    }

    // 套用折扣碼
    applyDiscountCode(code) {
        if (!code) {
            this.showNotification('請輸入折扣碼', 'warning');
            return;
        }

        const discount = SponsorConfig.DISCOUNT_CODES[code.toUpperCase()];
        if (!discount) {
            this.showNotification('無效的折扣碼', 'error');
            return;
        }

        this.discountCode = code.toUpperCase();
        
        if (discount.type === 'percentage') {
            this.appliedDiscount = Math.round(this.selectedPackage.price * discount.discount / 100);
        } else {
            this.appliedDiscount = discount.discount;
        }

        this.showNotification(`折扣碼套用成功！節省 NT$ ${this.appliedDiscount}`, 'success');
        this.updateModalContent();
    }

    // 計算手續費
    calculateFee() {
        const method = SponsorConfig.PAYMENT_METHODS[this.selectedPaymentMethod.toUpperCase()];
        if (!method) return 0;

        const baseAmount = this.selectedPackage.price - this.appliedDiscount;
        
        if (method.fee.includes('%')) {
            const percentage = parseFloat(method.fee.replace('%', ''));
            return Math.round(baseAmount * percentage / 100);
        } else {
            return parseInt(method.fee.replace(/[^0-9]/g, ''));
        }
    }

    // 計算總計
    calculateTotal() {
        const baseAmount = this.selectedPackage.price - this.appliedDiscount;
        const fee = this.calculateFee();
        return baseAmount + fee;
    }

    // 更新訂單摘要
    updateOrderSummary() {
        const summaryContainer = document.querySelector('.order-summary');
        if (!summaryContainer || !this.selectedPackage) return;

        summaryContainer.innerHTML = `
            <h3>訂單摘要</h3>
            <div class="summary-item">
                <span>套餐</span>
                <span>${this.selectedPackage.name}</span>
            </div>
            <div class="summary-item">
                <span>價格</span>
                <span>NT$ ${this.selectedPackage.price.toLocaleString()}</span>
            </div>
            <div class="summary-item">
                <span>支付方式</span>
                <span>${SponsorConfig.PAYMENT_METHODS[this.selectedPaymentMethod.toUpperCase()].name}</span>
            </div>
            ${this.appliedDiscount > 0 ? `
                <div class="summary-item discount">
                    <span>折扣</span>
                    <span>-NT$ ${this.appliedDiscount.toLocaleString()}</span>
                </div>
            ` : ''}
            <div class="summary-item fee">
                <span>手續費</span>
                <span>NT$ ${this.calculateFee()}</span>
            </div>
            <div class="summary-total">
                <span>總計</span>
                <span>NT$ ${this.calculateTotal().toLocaleString()}</span>
            </div>
        `;
    }

    // 確認購買
    async confirmPurchase() {
        if (!this.selectedPackage) {
            this.showNotification('請選擇套餐', 'warning');
            return;
        }

        try {
            this.showProcessing('正在處理購買請求...');

            const orderData = {
                packageId: this.selectedPackage.id,
                amount: this.calculateTotal(),
                originalAmount: this.selectedPackage.price,
                discount: this.appliedDiscount,
                discountCode: this.discountCode,
                paymentMethod: this.selectedPaymentMethod,
                customer: {
                    name: this.userInfo?.name || '訪客',
                    email: this.userInfo?.email || '',
                    phone: this.userInfo?.phone || ''
                }
            };

            // 跳轉到支付頁面
            const params = new URLSearchParams({
                package: this.selectedPackage.id,
                amount: this.calculateTotal(),
                method: this.selectedPaymentMethod,
                discount: this.discountCode || ''
            });

            window.location.href = `/payment.html?${params.toString()}`;

        } catch (error) {
            console.error('購買失敗:', error);
            this.showError('購買失敗，請重試');
        }
    }

    // 關閉模態框
    closeModal() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        });
    }

    // 設置動畫
    setupAnimations() {
        // 套餐卡片懸停效果
        document.querySelectorAll('.package-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-10px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });

        // 滾動動畫
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.package-card, .payment-method').forEach(el => {
            observer.observe(el);
        });
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

    // 顯示通知
    showNotification(message, type = 'info') {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showNotification(message, type);
        }
    }
}

// 贊助工具函數
const SponsorUtils = {
    // 計算節省金額
    calculateSavings(originalPrice, currentPrice) {
        return originalPrice - currentPrice;
    },

    // 計算折扣百分比
    calculateDiscountPercentage(originalPrice, currentPrice) {
        return Math.round((1 - currentPrice / originalPrice) * 100);
    },

    // 格式化價格
    formatPrice(price) {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD',
            minimumFractionDigits: 0
        }).format(price);
    },

    // 獲取推薦套餐
    getRecommendedPackage() {
        return Object.values(SponsorConfig.PACKAGES).find(pkg => pkg.popular);
    }
};

// 初始化贊助頁面
let sponsorPage;
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('sponsor')) {
        sponsorPage = new SponsorPage();
    }
});

// 導出全局對象
window.JySponsor = {
    page: () => sponsorPage,
    utils: SponsorUtils,
    config: SponsorConfig
};

console.log('💎 贊助模組已載入');