/**
 * 最高階自動贊助系統 - 主要JavaScript文件
 * 4D科技風格 - 速買功能核心實現
 * 版本: 1.0.0
 * 作者: AI Assistant
 * 日期: 2024
 */

// 全局配置
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api',
    WS_URL: 'ws://localhost:8001/ws',
    QUICK_BUY_TIMEOUT: 30000, // 30秒
    NOTIFICATION_TIMEOUT: 5000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000
};

// 全局狀態管理
class StateManager {
    constructor() {
        this.state = {
            user: null,
            isLoggedIn: false,
            cart: [],
            quickBuyItems: [],
            notifications: [],
            systemStatus: 'online',
            paymentMethods: [],
            preferences: {},
            stats: {}
        };
        this.listeners = {};
    }

    setState(key, value) {
        this.state[key] = value;
        this.notifyListeners(key, value);
    }

    getState(key) {
        return this.state[key];
    }

    subscribe(key, callback) {
        if (!this.listeners[key]) {
            this.listeners[key] = [];
        }
        this.listeners[key].push(callback);
    }

    notifyListeners(key, value) {
        if (this.listeners[key]) {
            this.listeners[key].forEach(callback => callback(value));
        }
    }
}

// 實例化狀態管理器
const stateManager = new StateManager();

// API 請求處理類
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: data
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }
}

// 實例化API客戶端
const apiClient = new APIClient(CONFIG.API_BASE_URL);

// WebSocket 連接管理
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = {};
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                stateManager.setState('systemStatus', 'online');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                stateManager.setState('systemStatus', 'offline');
                this.reconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                stateManager.setState('systemStatus', 'error');
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.reconnect();
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    handleMessage(data) {
        const { type, payload } = data;
        
        switch (type) {
            case 'notification':
                notificationManager.show(payload.message, payload.type);
                break;
            case 'order_update':
                this.handleOrderUpdate(payload);
                break;
            case 'system_status':
                stateManager.setState('systemStatus', payload.status);
                break;
            case 'quick_buy_result':
                this.handleQuickBuyResult(payload);
                break;
            default:
                console.log('Unknown message type:', type);
        }

        // 通知監聽器
        if (this.listeners[type]) {
            this.listeners[type].forEach(callback => callback(payload));
        }
    }

    handleOrderUpdate(payload) {
        const { orderId, status, message } = payload;
        notificationManager.show(`訂單 ${orderId} 狀態更新: ${message}`, 
            status === 'completed' ? 'success' : 'info');
    }

    handleQuickBuyResult(payload) {
        const { success, message, orderId } = payload;
        if (success) {
            notificationManager.show(`速買成功！訂單號: ${orderId}`, 'success');
            quickBuyManager.onSuccess(payload);
        } else {
            notificationManager.show(`速買失敗: ${message}`, 'error');
            quickBuyManager.onError(payload);
        }
    }

    send(type, payload) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, payload }));
        } else {
            console.warn('WebSocket is not connected');
        }
    }

    subscribe(type, callback) {
        if (!this.listeners[type]) {
            this.listeners[type] = [];
        }
        this.listeners[type].push(callback);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// 實例化WebSocket管理器
const wsManager = new WebSocketManager(CONFIG.WS_URL);

// 通知管理器
class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.init();
    }

    init() {
        this.container = document.querySelector('.notification-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = CONFIG.NOTIFICATION_TIMEOUT) {
        const notification = this.createNotification(message, type);
        this.container.appendChild(notification);
        this.notifications.push(notification);

        // 觸發動畫
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // 自動移除
        setTimeout(() => {
            this.remove(notification);
        }, duration);

        return notification;
    }

    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getIcon(type);
        notification.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="notificationManager.remove(this.parentElement)">
                <i class="fas fa-times"></i>
            </button>
        `;

        return notification;
    }

    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    remove(notification) {
        if (notification && notification.parentElement) {
            notification.classList.add('hide');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.parentElement.removeChild(notification);
                }
                const index = this.notifications.indexOf(notification);
                if (index > -1) {
                    this.notifications.splice(index, 1);
                }
            }, 300);
        }
    }

    clear() {
        this.notifications.forEach(notification => {
            this.remove(notification);
        });
    }
}

// 實例化通知管理器
const notificationManager = new NotificationManager();

// 速買管理器
class QuickBuyManager {
    constructor() {
        this.isProcessing = false;
        this.quickBuyItems = [];
        this.preferences = {};
        this.init();
    }

    init() {
        this.loadPreferences();
        this.bindEvents();
    }

    async loadPreferences() {
        try {
            const response = await apiClient.get('/user/preferences');
            this.preferences = response.data;
            stateManager.setState('preferences', this.preferences);
        } catch (error) {
            console.error('Failed to load preferences:', error);
        }
    }

    bindEvents() {
        // 綁定速買按鈕事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-buy-btn')) {
                const itemId = e.target.dataset.itemId;
                const amount = e.target.dataset.amount || 1;
                this.quickBuy(itemId, amount);
            }
        });

        // 綁定快捷鍵
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'q') {
                e.preventDefault();
                this.showQuickBuyModal();
            }
        });
    }

    async quickBuy(itemId, amount = 1) {
        if (this.isProcessing) {
            notificationManager.show('速買正在處理中，請稍候...', 'warning');
            return;
        }

        if (!stateManager.getState('isLoggedIn')) {
            notificationManager.show('請先登入後再使用速買功能', 'warning');
            authManager.showLoginModal();
            return;
        }

        this.isProcessing = true;
        const loadingNotification = notificationManager.show('正在處理速買請求...', 'info', 30000);

        try {
            // 獲取商品信息
            const item = await apiClient.get(`/items/${itemId}`);
            
            // 檢查庫存
            if (item.data.stock < amount) {
                throw new Error('庫存不足');
            }

            // 檢查用戶餘額
            const user = stateManager.getState('user');
            const totalPrice = item.data.price * amount;
            
            if (user.balance < totalPrice) {
                throw new Error('餘額不足，請先充值');
            }

            // 創建速買訂單
            const orderData = {
                itemId: itemId,
                amount: amount,
                paymentMethod: this.preferences.defaultPaymentMethod || 'balance',
                quickBuy: true
            };

            const response = await apiClient.post('/orders/quick-buy', orderData);
            
            notificationManager.remove(loadingNotification);
            
            if (response.success) {
                notificationManager.show(
                    `速買成功！訂單號: ${response.data.orderId}`, 
                    'success'
                );
                this.onSuccess(response.data);
            } else {
                throw new Error(response.message || '速買失敗');
            }

        } catch (error) {
            notificationManager.remove(loadingNotification);
            notificationManager.show(`速買失敗: ${error.message}`, 'error');
            this.onError({ error: error.message });
        } finally {
            this.isProcessing = false;
        }
    }

    onSuccess(data) {
        // 更新用戶餘額
        const user = stateManager.getState('user');
        if (user) {
            user.balance -= data.totalPrice;
            stateManager.setState('user', user);
        }

        // 更新統計
        this.updateStats('success');
        
        // 觸發成功動畫
        this.showSuccessAnimation();
    }

    onError(data) {
        // 更新統計
        this.updateStats('error');
        
        // 觸發錯誤動畫
        this.showErrorAnimation();
    }

    updateStats(type) {
        const stats = stateManager.getState('stats');
        if (type === 'success') {
            stats.quickBuySuccess = (stats.quickBuySuccess || 0) + 1;
        } else {
            stats.quickBuyError = (stats.quickBuyError || 0) + 1;
        }
        stateManager.setState('stats', stats);
    }

    showSuccessAnimation() {
        const animation = document.createElement('div');
        animation.className = 'quick-buy-success-animation';
        animation.innerHTML = '<i class="fas fa-check-circle"></i><span>速買成功！</span>';
        document.body.appendChild(animation);
        
        setTimeout(() => {
            animation.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            animation.classList.add('hide');
            setTimeout(() => {
                document.body.removeChild(animation);
            }, 500);
        }, 2000);
    }

    showErrorAnimation() {
        const animation = document.createElement('div');
        animation.className = 'quick-buy-error-animation';
        animation.innerHTML = '<i class="fas fa-times-circle"></i><span>速買失敗</span>';
        document.body.appendChild(animation);
        
        setTimeout(() => {
            animation.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            animation.classList.add('hide');
            setTimeout(() => {
                document.body.removeChild(animation);
            }, 500);
        }, 2000);
    }

    showQuickBuyModal() {
        const modal = document.getElementById('quickBuyModal');
        if (modal) {
            modal.classList.add('show');
            this.loadQuickBuyItems();
        }
    }

    async loadQuickBuyItems() {
        try {
            const response = await apiClient.get('/items/quick-buy');
            this.quickBuyItems = response.data;
            this.renderQuickBuyItems();
        } catch (error) {
            console.error('Failed to load quick buy items:', error);
        }
    }

    renderQuickBuyItems() {
        const container = document.querySelector('.quick-buy-items');
        if (!container) return;

        container.innerHTML = this.quickBuyItems.map(item => `
            <div class="quick-buy-item" data-item-id="${item.id}">
                <div class="item-image">
                    <img src="${item.image}" alt="${item.name}">
                </div>
                <div class="item-info">
                    <h4>${item.name}</h4>
                    <p class="item-price">$${item.price}</p>
                    <p class="item-stock">庫存: ${item.stock}</p>
                </div>
                <div class="item-actions">
                    <input type="number" class="amount-input" value="1" min="1" max="${item.stock}">
                    <button class="btn btn-primary quick-buy-btn" 
                            data-item-id="${item.id}" 
                            data-amount="1">
                        <i class="fas fa-bolt"></i> 速買
                    </button>
                </div>
            </div>
        `).join('');

        // 綁定數量輸入事件
        container.querySelectorAll('.amount-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const btn = e.target.parentElement.querySelector('.quick-buy-btn');
                btn.dataset.amount = e.target.value;
            });
        });
    }
}

// 實例化速買管理器
const quickBuyManager = new QuickBuyManager();

// 認證管理器
class AuthManager {
    constructor() {
        this.init();
    }

    init() {
        this.checkAuthStatus();
        this.bindEvents();
    }

    async checkAuthStatus() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            try {
                const response = await apiClient.get('/auth/verify');
                if (response.success) {
                    stateManager.setState('user', response.data.user);
                    stateManager.setState('isLoggedIn', true);
                    this.updateUI(true);
                } else {
                    this.logout();
                }
            } catch (error) {
                console.error('Auth verification failed:', error);
                this.logout();
            }
        }
    }

    bindEvents() {
        // 登入表單
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.login();
            });
        }

        // 註冊表單
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.register();
            });
        }

        // 登出按鈕
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('logout-btn')) {
                this.logout();
            }
        });
    }

    async login() {
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        if (!email || !password) {
            notificationManager.show('請填寫完整的登入信息', 'warning');
            return;
        }

        try {
            const response = await apiClient.post('/auth/login', {
                email,
                password
            });

            if (response.success) {
                apiClient.setToken(response.data.token);
                stateManager.setState('user', response.data.user);
                stateManager.setState('isLoggedIn', true);
                
                notificationManager.show('登入成功！', 'success');
                this.updateUI(true);
                this.hideLoginModal();
            } else {
                throw new Error(response.message || '登入失敗');
            }
        } catch (error) {
            notificationManager.show(`登入失敗: ${error.message}`, 'error');
        }
    }

    async register() {
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const username = document.getElementById('registerUsername').value;

        if (!email || !password || !confirmPassword || !username) {
            notificationManager.show('請填寫完整的註冊信息', 'warning');
            return;
        }

        if (password !== confirmPassword) {
            notificationManager.show('密碼確認不一致', 'warning');
            return;
        }

        try {
            const response = await apiClient.post('/auth/register', {
                email,
                password,
                username
            });

            if (response.success) {
                notificationManager.show('註冊成功！請登入', 'success');
                this.showLoginModal();
            } else {
                throw new Error(response.message || '註冊失敗');
            }
        } catch (error) {
            notificationManager.show(`註冊失敗: ${error.message}`, 'error');
        }
    }

    logout() {
        apiClient.setToken(null);
        stateManager.setState('user', null);
        stateManager.setState('isLoggedIn', false);
        
        notificationManager.show('已登出', 'info');
        this.updateUI(false);
    }

    updateUI(isLoggedIn) {
        const loginBtn = document.querySelector('.login-btn');
        const userInfo = document.querySelector('.user-info');
        const quickBuySection = document.querySelector('.quick-buy-section');

        if (isLoggedIn) {
            if (loginBtn) loginBtn.style.display = 'none';
            if (userInfo) userInfo.style.display = 'block';
            if (quickBuySection) quickBuySection.style.display = 'block';
            
            const user = stateManager.getState('user');
            if (user) {
                const usernameElement = document.querySelector('.username');
                const balanceElement = document.querySelector('.balance');
                
                if (usernameElement) usernameElement.textContent = user.username;
                if (balanceElement) balanceElement.textContent = `$${user.balance}`;
            }
        } else {
            if (loginBtn) loginBtn.style.display = 'block';
            if (userInfo) userInfo.style.display = 'none';
            if (quickBuySection) quickBuySection.style.display = 'none';
        }
    }

    showLoginModal() {
        const modal = document.getElementById('loginModal');
        if (modal) {
            modal.classList.add('show');
        }
    }

    hideLoginModal() {
        const modal = document.getElementById('loginModal');
        if (modal) {
            modal.classList.remove('show');
        }
    }
}

// 實例化認證管理器
const authManager = new AuthManager();

// 支付管理器
class PaymentManager {
    constructor() {
        this.paymentMethods = [];
        this.init();
    }

    init() {
        this.loadPaymentMethods();
        this.bindEvents();
    }

    async loadPaymentMethods() {
        try {
            const response = await apiClient.get('/payment/methods');
            this.paymentMethods = response.data;
            stateManager.setState('paymentMethods', this.paymentMethods);
            this.renderPaymentMethods();
        } catch (error) {
            console.error('Failed to load payment methods:', error);
        }
    }

    renderPaymentMethods() {
        const container = document.querySelector('.payment-methods');
        if (!container) return;

        container.innerHTML = this.paymentMethods.map(method => `
            <div class="payment-method" data-method="${method.id}">
                <div class="method-icon">
                    <i class="${method.icon}"></i>
                </div>
                <div class="method-info">
                    <h4>${method.name}</h4>
                    <p>${method.description}</p>
                </div>
                <div class="method-status">
                    ${method.enabled ? '<span class="status-enabled">可用</span>' : '<span class="status-disabled">不可用</span>'}
                </div>
            </div>
        `).join('');
    }

    bindEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('payment-method')) {
                this.selectPaymentMethod(e.target.dataset.method);
            }
        });
    }

    selectPaymentMethod(methodId) {
        const method = this.paymentMethods.find(m => m.id === methodId);
        if (method && method.enabled) {
            // 更新用戶偏好
            const preferences = stateManager.getState('preferences');
            preferences.defaultPaymentMethod = methodId;
            stateManager.setState('preferences', preferences);
            
            // 保存到服務器
            this.savePreferences(preferences);
            
            notificationManager.show(`已選擇 ${method.name} 作為默認支付方式`, 'success');
        }
    }

    async savePreferences(preferences) {
        try {
            await apiClient.put('/user/preferences', preferences);
        } catch (error) {
            console.error('Failed to save preferences:', error);
        }
    }
}

// 實例化支付管理器
const paymentManager = new PaymentManager();

// 統計管理器
class StatsManager {
    constructor() {
        this.stats = {};
        this.init();
    }

    init() {
        this.loadStats();
        this.bindEvents();
    }

    async loadStats() {
        try {
            const response = await apiClient.get('/stats/dashboard');
            this.stats = response.data;
            stateManager.setState('stats', this.stats);
            this.renderStats();
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    renderStats() {
        // 渲染系統狀態
        this.renderSystemStatus();
        
        // 渲染用戶統計
        this.renderUserStats();
        
        // 渲染活動日誌
        this.renderActivityLog();
    }

    renderSystemStatus() {
        const container = document.querySelector('.system-status');
        if (!container) return;

        const status = stateManager.getState('systemStatus');
        const statusClass = {
            'online': 'status-online',
            'offline': 'status-offline',
            'error': 'status-error'
        }[status] || 'status-unknown';

        container.innerHTML = `
            <div class="status-indicator ${statusClass}">
                <div class="status-dot"></div>
                <span class="status-text">${this.getStatusText(status)}</span>
            </div>
            <div class="system-metrics">
                <div class="metric">
                    <span class="metric-label">在線用戶</span>
                    <span class="metric-value">${this.stats.onlineUsers || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">今日訂單</span>
                    <span class="metric-value">${this.stats.todayOrders || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">系統負載</span>
                    <span class="metric-value">${this.stats.systemLoad || '0%'}</span>
                </div>
            </div>
        `;
    }

    renderUserStats() {
        const container = document.querySelector('.user-stats');
        if (!container) return;

        const user = stateManager.getState('user');
        if (!user) return;

        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-shopping-cart"></i>
                </div>
                <div class="stat-info">
                    <h4>總訂單</h4>
                    <p class="stat-value">${user.totalOrders || 0}</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-bolt"></i>
                </div>
                <div class="stat-info">
                    <h4>速買成功</h4>
                    <p class="stat-value">${user.quickBuySuccess || 0}</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-wallet"></i>
                </div>
                <div class="stat-info">
                    <h4>總消費</h4>
                    <p class="stat-value">$${user.totalSpent || 0}</p>
                </div>
            </div>
        `;
    }

    renderActivityLog() {
        const container = document.querySelector('.activity-log');
        if (!container) return;

        const activities = this.stats.recentActivities || [];
        
        container.innerHTML = `
            <h3>最近活動</h3>
            <div class="activity-list">
                ${activities.map(activity => `
                    <div class="activity-item">
                        <div class="activity-icon">
                            <i class="${this.getActivityIcon(activity.type)}"></i>
                        </div>
                        <div class="activity-content">
                            <p class="activity-message">${activity.message}</p>
                            <span class="activity-time">${this.formatTime(activity.timestamp)}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    getStatusText(status) {
        const statusTexts = {
            'online': '系統正常',
            'offline': '系統離線',
            'error': '系統錯誤'
        };
        return statusTexts[status] || '未知狀態';
    }

    getActivityIcon(type) {
        const icons = {
            'order': 'fas fa-shopping-cart',
            'payment': 'fas fa-credit-card',
            'login': 'fas fa-sign-in-alt',
            'register': 'fas fa-user-plus',
            'quick_buy': 'fas fa-bolt'
        };
        return icons[type] || 'fas fa-info-circle';
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) {
            return '剛剛';
        } else if (diff < 3600000) {
            return `${Math.floor(diff / 60000)}分鐘前`;
        } else if (diff < 86400000) {
            return `${Math.floor(diff / 3600000)}小時前`;
        } else {
            return date.toLocaleDateString();
        }
    }

    bindEvents() {
        // 定期更新統計
        setInterval(() => {
            this.loadStats();
        }, 30000); // 每30秒更新一次
    }
}

// 實例化統計管理器
const statsManager = new StatsManager();

// 模態框管理器
class ModalManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 關閉模態框
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay') || 
                e.target.classList.contains('modal-close')) {
                this.closeModal(e.target.closest('.modal'));
            }
        });

        // ESC鍵關閉模態框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    this.closeModal(openModal);
                }
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.classList.add('modal-open');
        }
    }

    closeModal(modal) {
        if (modal) {
            modal.classList.remove('show');
            document.body.classList.remove('modal-open');
        }
    }
}

// 實例化模態框管理器
const modalManager = new ModalManager();

// 載入動畫管理器
class LoadingManager {
    constructor() {
        this.loadingElement = null;
        this.init();
    }

    init() {
        this.loadingElement = document.querySelector('.loading-screen');
    }

    show() {
        if (this.loadingElement) {
            this.loadingElement.classList.add('show');
        }
    }

    hide() {
        if (this.loadingElement) {
            this.loadingElement.classList.remove('show');
            setTimeout(() => {
                this.loadingElement.style.display = 'none';
            }, 500);
        }
    }
}

// 實例化載入管理器
const loadingManager = new LoadingManager();

// 主應用程序初始化
class App {
    constructor() {
        this.init();
    }

    async init() {
        try {
            // 顯示載入畫面
            loadingManager.show();
            
            // 初始化各個管理器
            await this.initializeManagers();
            
            // 綁定全局事件
            this.bindGlobalEvents();
            
            // 連接WebSocket
            wsManager.connect();
            
            // 隱藏載入畫面
            setTimeout(() => {
                loadingManager.hide();
            }, 1000);
            
            console.log('Application initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            notificationManager.show('應用程序初始化失敗', 'error');
        }
    }

    async initializeManagers() {
        // 檢查認證狀態
        await authManager.checkAuthStatus();
        
        // 載入用戶偏好設置
        if (stateManager.getState('isLoggedIn')) {
            await quickBuyManager.loadPreferences();
            await paymentManager.loadPaymentMethods();
            await statsManager.loadStats();
        }
    }

    bindGlobalEvents() {
        // 頁面可見性變化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // 頁面隱藏時暫停某些操作
                console.log('Page hidden');
            } else {
                // 頁面顯示時恢復操作
                console.log('Page visible');
                if (stateManager.getState('isLoggedIn')) {
                    statsManager.loadStats();
                }
            }
        });

        // 網絡狀態變化
        window.addEventListener('online', () => {
            notificationManager.show('網絡連接已恢復', 'success');
            wsManager.connect();
        });

        window.addEventListener('offline', () => {
            notificationManager.show('網絡連接已斷開', 'warning');
        });

        // 頁面卸載前清理
        window.addEventListener('beforeunload', () => {
            wsManager.disconnect();
        });
    }
}

// 主要JavaScript功能 - 4D科技風格自動贊助系統

// 全局變量
const MAIN_CONFIG = {
    API_BASE_URL: 'http://localhost:8080/api',
    WEBSOCKET_URL: 'ws://localhost:8080/ws',
    PAYMENT_TIMEOUT: 300000, // 5分鐘
    REFRESH_INTERVAL: 30000,  // 30秒
    ANIMATION_DURATION: 300
};

// 應用程序狀態
const AppState = {
    user: null,
    theme: 'dark',
    notifications: [],
    isLoading: false,
    currentPage: 'home'
};

// DOM元素緩存
const Elements = {
    loadingScreen: null,
    themeToggle: null,
    notificationBell: null,
    userMenu: null,
    modals: {}
};

// 主應用程序類
class MainApp {
    constructor() {
        this.init();
    }

    async init() {
        try {
            // 緩存DOM元素
            this.cacheElements();
            
            // 設置事件監聽器
            this.setupEventListeners();
            
            // 初始化主題
            this.initTheme();
            
            // 初始化載入效果
            this.initLoadingEffects();
            
            // 初始化背景效果
            this.initBackgroundEffects();
            
            // 檢查用戶登入狀態
            await this.checkAuthStatus();
            
            // 隱藏載入畫面
            this.hideLoadingScreen();
            
            console.log('🚀 Jy自動贊助系統已初始化');
        } catch (error) {
            console.error('❌ 應用程序初始化失敗:', error);
            this.showError('系統初始化失敗，請刷新頁面重試');
        }
    }

    // 緩存DOM元素
    cacheElements() {
        Elements.loadingScreen = document.getElementById('loading-screen');
        Elements.themeToggle = document.getElementById('themeToggle');
        Elements.notificationBell = document.getElementById('notificationBell');
        Elements.userMenu = document.getElementById('userDropdown');
        
        // 緩存所有模態框
        document.querySelectorAll('.modal').forEach(modal => {
            Elements.modals[modal.id] = modal;
        });
    }

    // 設置事件監聽器
    setupEventListeners() {
        // 主題切換
        if (Elements.themeToggle) {
            Elements.themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // 通知鈴鐺
        if (Elements.notificationBell) {
            Elements.notificationBell.addEventListener('click', () => this.toggleNotifications());
        }

        // 用戶菜單
        const userAvatar = document.getElementById('userAvatar');
        if (userAvatar) {
            userAvatar.addEventListener('click', () => this.toggleUserMenu());
        }

        // 模態框事件
        this.setupModalEvents();

        // 導航鏈接
        this.setupNavigationEvents();

        // 全局鍵盤事件
        document.addEventListener('keydown', (e) => this.handleKeyboardEvents(e));

        // 窗口大小變化
        window.addEventListener('resize', () => this.handleResize());

        // 頁面可見性變化
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
    }

    // 設置模態框事件
    setupModalEvents() {
        // 關閉按鈕
        document.querySelectorAll('.modal-close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) this.closeModal(modal.id);
            });
        });

        // 點擊背景關閉
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    // 設置導航事件
    setupNavigationEvents() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                if (link.getAttribute('href').startsWith('#')) {
                    e.preventDefault();
                    const targetId = link.getAttribute('href').substring(1);
                    this.navigateToSection(targetId);
                }
            });
        });
    }

    // 初始化主題
    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
    }

    // 切換主題
    toggleTheme() {
        const newTheme = AppState.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    // 設置主題
    setTheme(theme) {
        AppState.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // 更新主題圖標
        if (Elements.themeToggle) {
            const icon = Elements.themeToggle.querySelector('.theme-icon');
            if (icon) {
                icon.textContent = theme === 'dark' ? '🌙' : '☀️';
            }
        }
    }

    // 初始化載入效果
    initLoadingEffects() {
        if (!Elements.loadingScreen) return;

        const progressBar = Elements.loadingScreen.querySelector('.progress-bar');
        const loadingText = Elements.loadingScreen.querySelector('.loading-text');
        
        const loadingSteps = [
            '正在連接服務器...',
            '載入用戶數據...',
            '初始化支付系統...',
            '準備就緒！'
        ];

        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep < loadingSteps.length) {
                if (loadingText) loadingText.textContent = loadingSteps[currentStep];
                if (progressBar) {
                    progressBar.style.width = `${(currentStep + 1) * 25}%`;
                }
                currentStep++;
            } else {
                clearInterval(stepInterval);
            }
        }, 500);
    }

    // 隱藏載入畫面
    hideLoadingScreen() {
        if (Elements.loadingScreen) {
            setTimeout(() => {
                Elements.loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    Elements.loadingScreen.style.display = 'none';
                }, MAIN_CONFIG.ANIMATION_DURATION);
            }, 1000);
        }
    }

    // 初始化背景效果
    initBackgroundEffects() {
        this.createParticleField();
        this.createEnergyWaves();
    }

    // 創建粒子場
    createParticleField() {
        const particleField = document.querySelector('.particle-field');
        if (!particleField) return;

        const particleCount = 50;
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: rgba(0, 255, 255, 0.6);
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: float ${3 + Math.random() * 4}s infinite ease-in-out;
                animation-delay: ${Math.random() * 2}s;
            `;
            particleField.appendChild(particle);
        }
    }

    // 創建能量波
    createEnergyWaves() {
        const energyWaves = document.querySelector('.energy-waves');
        if (!energyWaves) return;

        for (let i = 0; i < 3; i++) {
            const wave = document.createElement('div');
            wave.className = 'energy-wave';
            wave.style.cssText = `
                position: absolute;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.5), transparent);
                top: ${20 + i * 30}%;
                animation: wave ${4 + i}s infinite ease-in-out;
                animation-delay: ${i * 0.5}s;
            `;
            energyWaves.appendChild(wave);
        }
    }

    // 檢查認證狀態
    async checkAuthStatus() {
        try {
            const response = await this.apiCall('/auth/status');
            if (response.success) {
                AppState.user = response.user;
                this.updateUserInterface();
            }
        } catch (error) {
            console.log('用戶未登入或會話已過期');
        }
    }

    // 更新用戶界面
    updateUserInterface() {
        if (!AppState.user) return;

        // 更新用戶頭像
        const userAvatar = document.getElementById('userAvatar');
        if (userAvatar) {
            const avatarText = userAvatar.querySelector('.avatar-text');
            if (avatarText) {
                avatarText.textContent = AppState.user.name.substring(0, 2).toUpperCase();
            }
        }

        // 更新用戶名稱
        const userNameElements = document.querySelectorAll('[data-user-name]');
        userNameElements.forEach(element => {
            element.textContent = AppState.user.name;
        });

        // 更新用戶郵箱
        const userEmailElements = document.querySelectorAll('[data-user-email]');
        userEmailElements.forEach(element => {
            element.textContent = AppState.user.email;
        });
    }

    // API調用
    async apiCall(endpoint, options = {}) {
        const url = `${MAIN_CONFIG.API_BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || '請求失敗');
            }
            
            return data;
        } catch (error) {
            console.error('API調用失敗:', error);
            throw error;
        }
    }

    // 顯示通知
    showNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date()
        };

        AppState.notifications.unshift(notification);
        this.updateNotificationBell();
        this.displayToast(notification);

        // 自動移除通知
        setTimeout(() => {
            this.removeNotification(notification.id);
        }, duration);
    }

    // 顯示Toast通知
    displayToast(notification) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${notification.type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-message">${notification.message}</div>
                <button class="toast-close">×</button>
            </div>
        `;

        // 添加樣式
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, rgba(15, 15, 25, 0.95), rgba(25, 25, 35, 0.95));
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 10px;
            padding: 15px 20px;
            color: var(--text-primary);
            z-index: 10000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            backdrop-filter: blur(10px);
        `;

        document.body.appendChild(toast);

        // 動畫顯示
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);

        // 關閉按鈕事件
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.removeToast(toast);
        });

        // 自動移除
        setTimeout(() => {
            this.removeToast(toast);
        }, 5000);
    }

    // 移除Toast
    removeToast(toast) {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    // 更新通知鈴鐺
    updateNotificationBell() {
        if (!Elements.notificationBell) return;

        const countElement = Elements.notificationBell.querySelector('.notification-count');
        if (countElement) {
            const unreadCount = AppState.notifications.length;
            countElement.textContent = unreadCount;
            countElement.style.display = unreadCount > 0 ? 'block' : 'none';
        }
    }

    // 切換通知面板
    toggleNotifications() {
        console.log('切換通知面板');
    }

    // 切換用戶菜單
    toggleUserMenu() {
        if (!Elements.userMenu) return;

        const isVisible = Elements.userMenu.style.display === 'block';
        Elements.userMenu.style.display = isVisible ? 'none' : 'block';
    }

    // 打開模態框
    openModal(modalId) {
        const modal = Elements.modals[modalId];
        if (!modal) return;

        modal.style.display = 'flex';
        modal.style.opacity = '0';
        
        setTimeout(() => {
            modal.style.opacity = '1';
        }, 10);

        // 防止背景滾動
        document.body.style.overflow = 'hidden';
    }

    // 關閉模態框
    closeModal(modalId) {
        const modal = Elements.modals[modalId];
        if (!modal) return;

        modal.style.opacity = '0';
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, MAIN_CONFIG.ANIMATION_DURATION);
    }

    // 導航到指定區域
    navigateToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return;

        // 平滑滾動
        section.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });

        // 更新活動導航鏈接
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`[href="#${sectionId}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    // 處理鍵盤事件
    handleKeyboardEvents(e) {
        // ESC鍵關閉模態框
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="display: flex"]');
            if (openModal) {
                this.closeModal(openModal.id);
            }
        }
    }

    // 處理窗口大小變化
    handleResize() {
        // 重新計算背景效果
        this.updateBackgroundEffects();
    }

    // 處理頁面可見性變化
    handleVisibilityChange() {
        if (document.hidden) {
            console.log('頁面隱藏');
        } else {
            console.log('頁面顯示');
            // 刷新數據
            this.refreshData();
        }
    }

    // 刷新數據
    async refreshData() {
        try {
            await this.checkAuthStatus();
            this.showNotification('數據已更新', 'success', 2000);
        } catch (error) {
            console.error('數據刷新失敗:', error);
        }
    }

    // 顯示錯誤
    showError(message) {
        this.showNotification(message, 'error');
    }

    // 顯示成功消息
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    // 格式化金額
    formatCurrency(amount) {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD'
        }).format(amount);
    }

    // 格式化日期
    formatDate(date) {
        return new Intl.DateTimeFormat('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }

    // 更新背景效果
    updateBackgroundEffects() {
        // 根據窗口大小調整背景效果
        const particles = document.querySelectorAll('.particle');
        particles.forEach(particle => {
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
        });
    }
}

// 工具函數
const Utils = {
    // 防抖函數
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 生成UUID
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },

    // 檢查是否為移動設備
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
};

// 當DOM載入完成後初始化應用程序
let mainApp;
document.addEventListener('DOMContentLoaded', () => {
    mainApp = new MainApp();
    new App();
});

// 導出全局對象
window.JyMainApp = {
    app: () => mainApp,
    utils: Utils,
    config: MAIN_CONFIG,
    state: AppState
};

// 導出全局對象供其他腳本使用
window.AppManagers = {
    stateManager,
    apiClient,
    wsManager,
    notificationManager,
    quickBuyManager,
    authManager,
    paymentManager,
    statsManager,
    modalManager,
    loadingManager
};

// 全局錯誤處理
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    notificationManager.show('發生未預期的錯誤', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    notificationManager.show('請求處理失敗', 'error');
});

console.log('🚀 最高階自動贊助系統已載入完成！');
console.log('💡 使用 Ctrl+Q 快速開啟速買功能');
console.log('⚡ 4D科技風格界面已就緒');