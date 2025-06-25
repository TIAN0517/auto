// WebSocket即時通訊模組 - 4D科技風格自動贊助系統
// Real-time Communication Module

// WebSocket配置
const WebSocketConfig = {
    RECONNECT_INTERVAL: 3000,
    MAX_RECONNECT_ATTEMPTS: 10,
    HEARTBEAT_INTERVAL: 30000,
    MESSAGE_TYPES: {
        PAYMENT_STATUS: 'payment_status',
        TRANSACTION_UPDATE: 'transaction_update',
        SYSTEM_NOTIFICATION: 'system_notification',
        USER_MESSAGE: 'user_message',
        HEARTBEAT: 'heartbeat',
        AUTH: 'auth',
        SUBSCRIBE: 'subscribe',
        UNSUBSCRIBE: 'unsubscribe'
    },
    CHANNELS: {
        PAYMENTS: 'payments',
        TRANSACTIONS: 'transactions',
        NOTIFICATIONS: 'notifications',
        SYSTEM: 'system'
    }
};

// WebSocket管理器
class WebSocketManager {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.subscriptions = new Set();
        this.messageHandlers = new Map();
        this.heartbeatTimer = null;
        this.reconnectTimer = null;
        this.userId = null;
        this.token = null;
        this.init();
    }

    init() {
        this.loadUserInfo();
        this.setupEventHandlers();
        this.connect();
        console.log('🔌 WebSocket管理器已初始化');
    }

    // 載入用戶信息
    loadUserInfo() {
        this.token = localStorage.getItem('token');
        this.userId = localStorage.getItem('userId');
    }

    // 設置事件處理器
    setupEventHandlers() {
        // 監聽頁面可見性變化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseHeartbeat();
            } else {
                this.resumeHeartbeat();
                if (!this.isConnected) {
                    this.connect();
                }
            }
        });

        // 監聽網路狀態變化
        window.addEventListener('online', () => {
            console.log('🌐 網路已連接，嘗試重新連接WebSocket');
            this.connect();
        });

        window.addEventListener('offline', () => {
            console.log('🌐 網路已斷線');
            this.disconnect();
        });

        // 監聽頁面卸載
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
    }

    // 連接WebSocket
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            return;
        }

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('🔌 正在連接WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = this.onOpen.bind(this);
            this.ws.onmessage = this.onMessage.bind(this);
            this.ws.onclose = this.onClose.bind(this);
            this.ws.onerror = this.onError.bind(this);
            
        } catch (error) {
            console.error('WebSocket連接失敗:', error);
            this.scheduleReconnect();
        }
    }

    // 連接成功
    onOpen(event) {
        console.log('✅ WebSocket連接成功');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // 發送認證信息
        this.authenticate();
        
        // 重新訂閱頻道
        this.resubscribeChannels();
        
        // 開始心跳
        this.startHeartbeat();
        
        // 觸發連接成功事件
        this.emit('connected', { timestamp: Date.now() });
        
        // 更新UI狀態
        this.updateConnectionStatus(true);
    }

    // 接收消息
    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('📨 收到WebSocket消息:', message);
            
            this.handleMessage(message);
            
        } catch (error) {
            console.error('解析WebSocket消息失敗:', error, event.data);
        }
    }

    // 連接關閉
    onClose(event) {
        console.log('🔌 WebSocket連接已關閉:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        
        // 更新UI狀態
        this.updateConnectionStatus(false);
        
        // 觸發斷線事件
        this.emit('disconnected', { 
            code: event.code, 
            reason: event.reason,
            timestamp: Date.now()
        });
        
        // 如果不是主動斷線，嘗試重連
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }

    // 連接錯誤
    onError(error) {
        console.error('❌ WebSocket錯誤:', error);
        this.emit('error', { error, timestamp: Date.now() });
    }

    // 處理消息
    handleMessage(message) {
        const { type, data, channel } = message;
        
        switch (type) {
            case WebSocketConfig.MESSAGE_TYPES.PAYMENT_STATUS:
                this.handlePaymentStatus(data);
                break;
                
            case WebSocketConfig.MESSAGE_TYPES.TRANSACTION_UPDATE:
                this.handleTransactionUpdate(data);
                break;
                
            case WebSocketConfig.MESSAGE_TYPES.SYSTEM_NOTIFICATION:
                this.handleSystemNotification(data);
                break;
                
            case WebSocketConfig.MESSAGE_TYPES.USER_MESSAGE:
                this.handleUserMessage(data);
                break;
                
            case WebSocketConfig.MESSAGE_TYPES.HEARTBEAT:
                this.handleHeartbeat(data);
                break;
                
            default:
                console.log('未知消息類型:', type, data);
        }
        
        // 觸發通用消息事件
        this.emit('message', message);
        
        // 觸發特定類型事件
        this.emit(type, data);
        
        // 觸發頻道事件
        if (channel) {
            this.emit(`channel:${channel}`, data);
        }
    }

    // 處理支付狀態更新
    handlePaymentStatus(data) {
        console.log('💳 支付狀態更新:', data);
        
        // 更新支付頁面狀態
        if (window.JySpeedPay && window.JySpeedPay.manager()) {
            document.dispatchEvent(new CustomEvent('speedpay:statusUpdate', {
                detail: data
            }));
        }
        
        // 顯示通知
        this.showPaymentNotification(data);
    }

    // 處理交易更新
    handleTransactionUpdate(data) {
        console.log('📊 交易更新:', data);
        
        // 更新交易列表
        this.updateTransactionList(data);
        
        // 更新統計數據
        this.updateStatistics(data);
    }

    // 處理系統通知
    handleSystemNotification(data) {
        console.log('🔔 系統通知:', data);
        
        // 顯示系統通知
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showNotification(data.message, data.type || 'info');
        }
    }

    // 處理用戶消息
    handleUserMessage(data) {
        console.log('👤 用戶消息:', data);
        
        // 顯示用戶消息
        this.showUserMessage(data);
    }

    // 處理心跳
    handleHeartbeat(data) {
        // 回應心跳
        this.send({
            type: WebSocketConfig.MESSAGE_TYPES.HEARTBEAT,
            data: { timestamp: Date.now() }
        });
    }

    // 發送認證信息
    authenticate() {
        if (this.token) {
            this.send({
                type: WebSocketConfig.MESSAGE_TYPES.AUTH,
                data: {
                    token: this.token,
                    userId: this.userId
                }
            });
        }
    }

    // 訂閱頻道
    subscribe(channel) {
        if (this.subscriptions.has(channel)) {
            return;
        }
        
        this.subscriptions.add(channel);
        
        if (this.isConnected) {
            this.send({
                type: WebSocketConfig.MESSAGE_TYPES.SUBSCRIBE,
                data: { channel }
            });
        }
        
        console.log('📺 已訂閱頻道:', channel);
    }

    // 取消訂閱頻道
    unsubscribe(channel) {
        if (!this.subscriptions.has(channel)) {
            return;
        }
        
        this.subscriptions.delete(channel);
        
        if (this.isConnected) {
            this.send({
                type: WebSocketConfig.MESSAGE_TYPES.UNSUBSCRIBE,
                data: { channel }
            });
        }
        
        console.log('📺 已取消訂閱頻道:', channel);
    }

    // 重新訂閱所有頻道
    resubscribeChannels() {
        this.subscriptions.forEach(channel => {
            this.send({
                type: WebSocketConfig.MESSAGE_TYPES.SUBSCRIBE,
                data: { channel }
            });
        });
    }

    // 發送消息
    send(message) {
        if (!this.isConnected || !this.ws) {
            console.warn('WebSocket未連接，無法發送消息:', message);
            return false;
        }
        
        try {
            this.ws.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('發送WebSocket消息失敗:', error);
            return false;
        }
    }

    // 開始心跳
    startHeartbeat() {
        this.stopHeartbeat();
        
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: WebSocketConfig.MESSAGE_TYPES.HEARTBEAT,
                    data: { timestamp: Date.now() }
                });
            }
        }, WebSocketConfig.HEARTBEAT_INTERVAL);
    }

    // 停止心跳
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    // 暫停心跳
    pauseHeartbeat() {
        this.stopHeartbeat();
    }

    // 恢復心跳
    resumeHeartbeat() {
        if (this.isConnected) {
            this.startHeartbeat();
        }
    }

    // 安排重連
    scheduleReconnect() {
        if (this.reconnectAttempts >= WebSocketConfig.MAX_RECONNECT_ATTEMPTS) {
            console.error('❌ WebSocket重連次數已達上限');
            this.emit('maxReconnectAttemptsReached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(WebSocketConfig.RECONNECT_INTERVAL * this.reconnectAttempts, 30000);
        
        console.log(`🔄 將在 ${delay}ms 後嘗試第 ${this.reconnectAttempts} 次重連`);
        
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    // 斷開連接
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        this.stopHeartbeat();
        
        if (this.ws) {
            this.ws.close(1000, '主動斷線');
            this.ws = null;
        }
        
        this.isConnected = false;
        this.updateConnectionStatus(false);
    }

    // 更新連接狀態顯示
    updateConnectionStatus(connected) {
        const statusElements = document.querySelectorAll('.connection-status');
        statusElements.forEach(element => {
            element.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            element.innerHTML = connected 
                ? '<i class="fas fa-wifi"></i> 已連接'
                : '<i class="fas fa-wifi-slash"></i> 已斷線';
        });
        
        // 更新導航欄狀態
        const navStatus = document.querySelector('.nav-status');
        if (navStatus) {
            navStatus.className = `nav-status ${connected ? 'online' : 'offline'}`;
        }
    }

    // 顯示支付通知
    showPaymentNotification(data) {
        const { status, amount, method, orderId } = data;
        
        let message = '';
        let type = 'info';
        
        switch (status) {
            case 'completed':
                message = `支付成功！金額：${this.formatAmount(amount)}`;
                type = 'success';
                break;
            case 'failed':
                message = `支付失敗，訂單：${orderId}`;
                type = 'error';
                break;
            case 'pending':
                message = `支付處理中，請稍候...`;
                type = 'info';
                break;
            case 'expired':
                message = `支付已過期，訂單：${orderId}`;
                type = 'warning';
                break;
        }
        
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showNotification(message, type);
        }
    }

    // 更新交易列表
    updateTransactionList(data) {
        const transactionList = document.querySelector('.transaction-list');
        if (!transactionList) return;
        
        // 添加新交易或更新現有交易
        const existingItem = transactionList.querySelector(`[data-transaction-id="${data.id}"]`);
        
        if (existingItem) {
            // 更新現有項目
            this.updateTransactionItem(existingItem, data);
        } else {
            // 添加新項目
            const newItem = this.createTransactionItem(data);
            transactionList.insertBefore(newItem, transactionList.firstChild);
        }
    }

    // 創建交易項目
    createTransactionItem(data) {
        const item = document.createElement('div');
        item.className = 'transaction-item';
        item.setAttribute('data-transaction-id', data.id);
        
        item.innerHTML = `
            <div class="transaction-info">
                <div class="transaction-id">#${data.id}</div>
                <div class="transaction-amount">${this.formatAmount(data.amount)}</div>
                <div class="transaction-method">${data.method}</div>
                <div class="transaction-status status-${data.status}">${this.getStatusText(data.status)}</div>
                <div class="transaction-time">${this.formatDate(data.created_at)}</div>
            </div>
        `;
        
        return item;
    }

    // 更新交易項目
    updateTransactionItem(item, data) {
        const statusElement = item.querySelector('.transaction-status');
        if (statusElement) {
            statusElement.className = `transaction-status status-${data.status}`;
            statusElement.textContent = this.getStatusText(data.status);
        }
    }

    // 更新統計數據
    updateStatistics(data) {
        // 更新總金額
        const totalAmountElement = document.querySelector('.total-amount');
        if (totalAmountElement && data.totalAmount) {
            totalAmountElement.textContent = this.formatAmount(data.totalAmount);
        }
        
        // 更新交易數量
        const transactionCountElement = document.querySelector('.transaction-count');
        if (transactionCountElement && data.transactionCount) {
            transactionCountElement.textContent = data.transactionCount;
        }
    }

    // 顯示用戶消息
    showUserMessage(data) {
        // 可以在這裡實現聊天功能或用戶通知
        console.log('用戶消息:', data);
    }

    // 事件發射器
    emit(event, data) {
        const handlers = this.messageHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`事件處理器錯誤 (${event}):`, error);
                }
            });
        }
    }

    // 添加事件監聽器
    on(event, handler) {
        if (!this.messageHandlers.has(event)) {
            this.messageHandlers.set(event, []);
        }
        this.messageHandlers.get(event).push(handler);
    }

    // 移除事件監聽器
    off(event, handler) {
        const handlers = this.messageHandlers.get(event);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    // 工具方法
    formatAmount(amount) {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD',
            minimumFractionDigits: 0
        }).format(amount);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('zh-TW', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

    getStatusText(status) {
        const statusTexts = {
            'pending': '待處理',
            'processing': '處理中',
            'completed': '已完成',
            'failed': '失敗',
            'expired': '已過期',
            'cancelled': '已取消'
        };
        return statusTexts[status] || '未知';
    }

    // 獲取連接狀態
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            subscriptions: Array.from(this.subscriptions)
        };
    }
}

// WebSocket工具函數
const WebSocketUtils = {
    // 檢查WebSocket支援
    isSupported() {
        return 'WebSocket' in window;
    },
    
    // 獲取WebSocket狀態文字
    getReadyStateText(readyState) {
        const states = {
            0: 'CONNECTING',
            1: 'OPEN',
            2: 'CLOSING',
            3: 'CLOSED'
        };
        return states[readyState] || 'UNKNOWN';
    }
};

// 初始化WebSocket管理器
let wsManager;
document.addEventListener('DOMContentLoaded', () => {
    if (WebSocketUtils.isSupported()) {
        wsManager = new WebSocketManager();
        
        // 自動訂閱基本頻道
        wsManager.subscribe(WebSocketConfig.CHANNELS.PAYMENTS);
        wsManager.subscribe(WebSocketConfig.CHANNELS.NOTIFICATIONS);
        
        // 如果是管理員頁面，訂閱系統頻道
        if (window.location.pathname.includes('admin')) {
            wsManager.subscribe(WebSocketConfig.CHANNELS.SYSTEM);
            wsManager.subscribe(WebSocketConfig.CHANNELS.TRANSACTIONS);
        }
    } else {
        console.warn('⚠️ 瀏覽器不支援WebSocket');
    }
});

// 導出全局對象
window.JyWebSocket = {
    manager: () => wsManager,
    utils: WebSocketUtils,
    config: WebSocketConfig
};

console.log('🔌 WebSocket模組已載入');