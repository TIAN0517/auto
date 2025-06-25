// USDT支付處理 - 4D科技風格自動贊助系統
// USDT Payment Handler for 4D Tech Style Auto Sponsorship System

class USDTPaymentHandler {
    constructor() {
        this.currentOrder = null;
        this.statusCheckInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadNetworks();
    }

    bindEvents() {
        // USDT支付方式選擇
        document.addEventListener('click', (e) => {
            if (e.target.closest('.payment-option[data-option="erc20"]')) {
                this.selectNetwork('erc20');
            } else if (e.target.closest('.payment-option[data-option="trc20"]')) {
                this.selectNetwork('trc20');
            }
        });

        // 創建USDT訂單
        const createUsdtOrderBtn = document.getElementById('createUsdtOrder');
        if (createUsdtOrderBtn) {
            createUsdtOrderBtn.addEventListener('click', () => this.createOrder());
        }

        // 檢查支付狀態
        const checkStatusBtn = document.getElementById('checkUsdtStatus');
        if (checkStatusBtn) {
            checkStatusBtn.addEventListener('click', () => this.checkStatus());
        }

        // 取消訂單
        const cancelOrderBtn = document.getElementById('cancelUsdtOrder');
        if (cancelOrderBtn) {
            cancelOrderBtn.addEventListener('click', () => this.cancelOrder());
        }
    }

    async loadNetworks() {
        try {
            const response = await fetch('/api/usdt/networks');
            const result = await response.json();
            
            if (result.success) {
                this.networks = result.data;
                this.renderNetworks();
            }
        } catch (error) {
            console.error('載入USDT網絡失敗:', error);
        }
    }

    renderNetworks() {
        const container = document.querySelector('.usdt-networks');
        if (!container || !this.networks) return;

        container.innerHTML = this.networks.map(network => `
            <div class="network-option" data-network="${network.network}">
                <div class="network-info">
                    <h4>${network.name}</h4>
                    <p>錢包地址: ${network.wallet_address}</p>
                    <p>手續費: ${(network.fee_rate * 100).toFixed(1)}%</p>
                    <p>處理時間: ${network.processing_time}</p>
                </div>
            </div>
        `).join('');
    }

    selectNetwork(network) {
        // 移除之前的選擇
        document.querySelectorAll('.payment-option').forEach(el => {
            el.classList.remove('selected');
        });

        // 選擇新的網絡
        const selectedOption = document.querySelector(`[data-option="${network}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
            this.selectedNetwork = network;
            this.updatePaymentForm();
        }
    }

    async createOrder() {
        if (!this.selectedNetwork) {
            this.showMessage('請選擇USDT網絡', 'error');
            return;
        }

        const amount = this.getOrderAmount();
        if (!amount || amount <= 0) {
            this.showMessage('請輸入有效的金額', 'error');
            return;
        }

        try {
            this.showLoading('創建USDT支付訂單中...');

            const response = await fetch('/api/usdt/create-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: amount,
                    network: this.selectedNetwork
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentOrder = result.order;
                this.showPaymentInstructions(result.payment_instructions);
                this.startStatusCheck();
            } else {
                this.showMessage(result.error || '創建訂單失敗', 'error');
            }
        } catch (error) {
            console.error('創建USDT訂單失敗:', error);
            this.showMessage('創建訂單失敗，請稍後重試', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showPaymentInstructions(instructions) {
        const container = document.getElementById('usdtPaymentInstructions');
        if (!container) return;

        const qrCodeData = instructions.qr_code_data;
        
        container.innerHTML = `
            <div class="usdt-payment-panel">
                <div class="payment-header">
                    <h3>USDT支付說明</h3>
                    <p class="network-name">${instructions.network_name}</p>
                </div>
                
                <div class="payment-details">
                    <div class="amount-info">
                        <span class="label">支付金額:</span>
                        <span class="amount">${instructions.amount} USDT</span>
                    </div>
                    
                    <div class="wallet-info">
                        <span class="label">錢包地址:</span>
                        <div class="wallet-address">
                            <code>${instructions.wallet_address}</code>
                            <button class="copy-btn" onclick="copyToClipboard('${instructions.wallet_address}')">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="qr-code-section">
                    <h4>掃描QR碼支付</h4>
                    <div id="usdtQrCode" class="qr-code"></div>
                </div>

                <div class="payment-steps">
                    <h4>支付步驟</h4>
                    <ol>
                        ${instructions.steps.map(step => `<li>${step}</li>`).join('')}
                    </ol>
                </div>

                <div class="important-notes">
                    <h4>重要提醒</h4>
                    <ul>
                        ${instructions.important_notes.map(note => `<li>${note}</li>`).join('')}
                    </ul>
                </div>

                <div class="payment-actions">
                    <button id="checkUsdtStatus" class="btn btn-primary">
                        <i class="fas fa-sync"></i> 檢查支付狀態
                    </button>
                    <button id="cancelUsdtOrder" class="btn btn-secondary">
                        <i class="fas fa-times"></i> 取消訂單
                    </button>
                </div>
            </div>
        `;

        // 生成QR碼
        this.generateQRCode(qrCodeData);
        
        // 重新綁定事件
        this.bindEvents();
    }

    generateQRCode(data) {
        const qrContainer = document.getElementById('usdtQrCode');
        if (!qrContainer) return;

        // 使用qrcode.js生成QR碼
        if (typeof QRCode !== 'undefined') {
            new QRCode(qrContainer, {
                text: data,
                width: 200,
                height: 200,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        } else {
            // 如果沒有qrcode.js，顯示文本
            qrContainer.innerHTML = `
                <div class="qr-fallback">
                    <p>請手動輸入以下地址:</p>
                    <code>${data}</code>
                </div>
            `;
        }
    }

    async checkStatus() {
        if (!this.currentOrder) {
            this.showMessage('沒有進行中的訂單', 'error');
            return;
        }

        try {
            this.showLoading('檢查支付狀態中...');

            const response = await fetch(`/api/usdt/status/${this.currentOrder.order_id}`);
            const result = await response.json();

            if (result.success) {
                this.updatePaymentStatus(result);
                
                if (result.status === 'completed') {
                    this.showMessage('支付成功！', 'success');
                    this.stopStatusCheck();
                    // 跳轉到成功頁面
                    setTimeout(() => {
                        window.location.href = '/payment/success?order_id=' + this.currentOrder.order_id;
                    }, 2000);
                } else if (result.status === 'expired') {
                    this.showMessage('訂單已過期', 'error');
                    this.stopStatusCheck();
                }
            } else {
                this.showMessage(result.error || '檢查狀態失敗', 'error');
            }
        } catch (error) {
            console.error('檢查USDT狀態失敗:', error);
            this.showMessage('檢查狀態失敗，請稍後重試', 'error');
        } finally {
            this.hideLoading();
        }
    }

    updatePaymentStatus(statusResult) {
        const statusContainer = document.getElementById('usdtPaymentStatus');
        if (!statusContainer) return;

        const statusText = {
            'pending': '等待付款',
            'processing': '處理中',
            'confirmed': '已確認',
            'completed': '已完成',
            'failed': '失敗',
            'expired': '已過期',
            'cancelled': '已取消'
        };

        statusContainer.innerHTML = `
            <div class="status-info">
                <span class="status-label">支付狀態:</span>
                <span class="status-value ${statusResult.status}">${statusText[statusResult.status] || statusResult.status}</span>
            </div>
            ${statusResult.confirmations !== undefined ? `
                <div class="confirmations-info">
                    <span class="confirmations-label">確認數:</span>
                    <span class="confirmations-value">${statusResult.confirmations}/${statusResult.required_confirmations}</span>
                </div>
            ` : ''}
            <div class="status-message">${statusResult.message || ''}</div>
        `;
    }

    async cancelOrder() {
        if (!this.currentOrder) {
            this.showMessage('沒有進行中的訂單', 'error');
            return;
        }

        if (!confirm('確定要取消這個訂單嗎？')) {
            return;
        }

        try {
            this.showLoading('取消訂單中...');

            const response = await fetch(`/api/usdt/cancel/${this.currentOrder.order_id}`, {
                method: 'POST'
            });
            const result = await response.json();

            if (result.success) {
                this.showMessage('訂單已取消', 'success');
                this.stopStatusCheck();
                this.currentOrder = null;
                this.hidePaymentInstructions();
            } else {
                this.showMessage(result.error || '取消訂單失敗', 'error');
            }
        } catch (error) {
            console.error('取消USDT訂單失敗:', error);
            this.showMessage('取消訂單失敗，請稍後重試', 'error');
        } finally {
            this.hideLoading();
        }
    }

    startStatusCheck() {
        // 每30秒檢查一次狀態
        this.statusCheckInterval = setInterval(() => {
            this.checkStatus();
        }, 30000);
    }

    stopStatusCheck() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    hidePaymentInstructions() {
        const container = document.getElementById('usdtPaymentInstructions');
        if (container) {
            container.innerHTML = '';
        }
    }

    getOrderAmount() {
        // 從頁面獲取訂單金額
        const amountElement = document.querySelector('.order-amount');
        if (amountElement) {
            return parseFloat(amountElement.textContent.replace(/[^\d.]/g, ''));
        }
        return 0;
    }

    updatePaymentForm() {
        const createOrderBtn = document.getElementById('createUsdtOrder');
        if (createOrderBtn) {
            createOrderBtn.disabled = !this.selectedNetwork;
            
            if (this.selectedNetwork) {
                const networkConfig = PaymentConfig.USDT.networks[this.selectedNetwork];
                createOrderBtn.innerHTML = `
                    <i class="fas fa-crypto"></i>
                    使用 ${networkConfig.name} 支付
                `;
            }
        }
    }

    showMessage(message, type = 'info') {
        // 顯示消息提示
        const messageContainer = document.getElementById('messageContainer');
        if (messageContainer) {
            messageContainer.innerHTML = `
                <div class="message ${type}">
                    <span>${message}</span>
                    <button onclick="this.parentElement.remove()">×</button>
                </div>
            `;
        }
    }

    showLoading(message) {
        // 顯示加載提示
        const loadingContainer = document.getElementById('loadingContainer');
        if (loadingContainer) {
            loadingContainer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <span>${message}</span>
                </div>
            `;
        }
    }

    hideLoading() {
        // 隱藏加載提示
        const loadingContainer = document.getElementById('loadingContainer');
        if (loadingContainer) {
            loadingContainer.innerHTML = '';
        }
    }
}

// 複製到剪貼板功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // 顯示複製成功提示
        const copyBtn = event.target.closest('.copy-btn');
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i>';
            copyBtn.style.color = '#00ff00';
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.style.color = '';
            }, 2000);
        }
    }).catch(err => {
        console.error('複製失敗:', err);
        alert('複製失敗，請手動複製');
    });
}

// 初始化USDT支付處理器
document.addEventListener('DOMContentLoaded', () => {
    window.usdtPaymentHandler = new USDTPaymentHandler();
}); 