// 狀態監控模組
class StatusMonitor {
    constructor() {
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.init();
    }

    init() {
        this.setupStatusIndicator();
        this.startMonitoring();
        this.bindEvents();
        console.log('Status Monitor initialized');
    }

    setupStatusIndicator() {
        // 創建狀態指示器
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'status-indicator';
        statusIndicator.className = 'status-indicator';
        statusIndicator.innerHTML = `
            <div class="status-dot"></div>
            <span class="status-text">連線中...</span>
        `;
        
        // 添加到頁面
        document.body.appendChild(statusIndicator);
    }

    bindEvents() {
        // 綁定狀態按鈕事件
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="status"]')) {
                this.showStatusModal();
            }
        });
    }

    startMonitoring() {
        // 模擬連線狀態檢查
        this.checkConnection();
        
        // 定期檢查連線狀態
        setInterval(() => {
            this.checkConnection();
        }, 10000);
    }

    checkConnection() {
        // 模擬連線檢查
        fetch('/api/health', { method: 'HEAD' })
            .then(() => {
                this.updateStatus(true);
                this.reconnectAttempts = 0;
            })
            .catch(() => {
                this.updateStatus(false);
                this.handleReconnect();
            });
    }

    updateStatus(connected) {
        this.isConnected = connected;
        const indicator = document.getElementById('status-indicator');
        const dot = indicator?.querySelector('.status-dot');
        const text = indicator?.querySelector('.status-text');
        
        if (connected) {
            dot?.classList.remove('disconnected');
            dot?.classList.add('connected');
            if (text) text.textContent = '已連線';
        } else {
            dot?.classList.remove('connected');
            dot?.classList.add('disconnected');
            if (text) text.textContent = '連線中斷';
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                this.checkConnection();
            }, this.reconnectDelay);
        }
    }

    showStatusModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>系統狀態</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="status-info">
                        <div class="status-item">
                            <span class="status-label">連線狀態:</span>
                            <span class="status-value ${this.isConnected ? 'connected' : 'disconnected'}">
                                ${this.isConnected ? '已連線' : '連線中斷'}
                            </span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">重連次數:</span>
                            <span class="status-value">${this.reconnectAttempts}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">系統時間:</span>
                            <span class="status-value">${new Date().toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 綁定關閉事件
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    getSystemInfo() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            timestamp: new Date().toISOString()
        };
    }
}

// 初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.statusMonitor = new StatusMonitor();
    });
} else {
    window.statusMonitor = new StatusMonitor();
}