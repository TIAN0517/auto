// 管理後台JavaScript - 4D科技風格自動贊助系統
// Admin Dashboard Module

// 管理後台配置
const AdminConfig = {
    REFRESH_INTERVAL: 30000, // 30秒刷新一次
    CHART_COLORS: {
        primary: '#00d4ff',
        secondary: '#ff6b6b',
        success: '#51cf66',
        warning: '#ffd43b',
        danger: '#ff6b6b',
        info: '#74c0fc'
    },
    PAGINATION: {
        DEFAULT_PAGE_SIZE: 20,
        MAX_PAGE_SIZE: 100
    },
    EXPORT_FORMATS: ['csv', 'excel', 'pdf'],
    NOTIFICATION_TYPES: {
        SUCCESS: 'success',
        ERROR: 'error',
        WARNING: 'warning',
        INFO: 'info'
    }
};

// 管理後台主類
class AdminDashboard {
    constructor() {
        this.currentView = 'dashboard';
        this.charts = {};
        this.filters = {
            dateRange: 'today',
            status: 'all',
            method: 'all',
            page: 1,
            pageSize: AdminConfig.PAGINATION.DEFAULT_PAGE_SIZE
        };
        this.refreshTimer = null;
        this.init();
    }

    init() {
        this.setupEventHandlers();
        this.initializeCharts();
        this.loadDashboardData();
        this.startAutoRefresh();
        console.log('🎛️ 管理後台已初始化');
    }

    // 設置事件處理器
    setupEventHandlers() {
        // 側邊欄導航
        document.querySelectorAll('.sidebar-nav a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.target.closest('a').dataset.view;
                this.switchView(view);
            });
        });

        // 過濾器變更
        document.querySelectorAll('.filter-select').forEach(select => {
            select.addEventListener('change', (e) => {
                this.updateFilter(e.target.name, e.target.value);
            });
        });

        // 搜索功能
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.performSearch(e.target.value);
            }, 500));
        }

        // 刷新按鈕
        document.querySelectorAll('.refresh-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.refreshCurrentView();
            });
        });

        // 導出按鈕
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.dataset.format;
                this.exportData(format);
            });
        });

        // 批量操作
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('batch-checkbox')) {
                this.updateBatchSelection();
            }
        });

        // 模態框事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || 
                e.target.classList.contains('modal-overlay')) {
                this.closeModal();
            }
        });

        // WebSocket事件監聽
        if (window.JyWebSocket && window.JyWebSocket.manager()) {
            const wsManager = window.JyWebSocket.manager();
            wsManager.on('transaction_update', (data) => {
                this.handleTransactionUpdate(data);
            });
            wsManager.on('system_notification', (data) => {
                this.handleSystemNotification(data);
            });
        }
    }

    // 切換視圖
    switchView(view) {
        if (this.currentView === view) return;

        // 更新側邊欄狀態
        document.querySelectorAll('.sidebar-nav a').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`).classList.add('active');

        // 隱藏所有內容區域
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });

        // 顯示目標內容區域
        const targetSection = document.querySelector(`#${view}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        this.currentView = view;
        this.loadViewData(view);
    }

    // 載入視圖數據
    async loadViewData(view) {
        try {
            switch (view) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'transactions':
                    await this.loadTransactions();
                    break;
                case 'users':
                    await this.loadUsers();
                    break;
                case 'payments':
                    await this.loadPaymentConfig();
                    break;
                case 'settings':
                    await this.loadSystemSettings();
                    break;
            }
        } catch (error) {
            console.error(`載入${view}數據失敗:`, error);
            this.showNotification('載入數據失敗', 'error');
        }
    }

    // 載入儀表板數據
    async loadDashboardData() {
        try {
            const response = await this.apiCall('/admin/dashboard');
            if (response.success) {
                this.updateDashboardStats(response.data.stats);
                this.updateCharts(response.data.charts);
                this.updateRecentTransactions(response.data.recentTransactions);
            }
        } catch (error) {
            console.error('載入儀表板數據失敗:', error);
        }
    }

    // 更新儀表板統計
    updateDashboardStats(stats) {
        const statCards = {
            'total-revenue': stats.totalRevenue,
            'total-transactions': stats.totalTransactions,
            'success-rate': `${stats.successRate}%`,
            'active-users': stats.activeUsers
        };

        Object.entries(statCards).forEach(([id, value]) => {
            const element = document.querySelector(`#${id}`);
            if (element) {
                this.animateNumber(element, value);
            }
        });
    }

    // 數字動畫
    animateNumber(element, targetValue) {
        const isPercentage = typeof targetValue === 'string' && targetValue.includes('%');
        const isCurrency = typeof targetValue === 'number';
        const numericValue = parseFloat(targetValue.toString().replace(/[^0-9.]/g, ''));
        
        let currentValue = 0;
        const increment = numericValue / 50;
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= numericValue) {
                currentValue = numericValue;
                clearInterval(timer);
            }
            
            let displayValue = Math.floor(currentValue);
            if (isCurrency) {
                displayValue = new Intl.NumberFormat('zh-TW', {
                    style: 'currency',
                    currency: 'TWD',
                    minimumFractionDigits: 0
                }).format(displayValue);
            } else if (isPercentage) {
                displayValue = `${displayValue}%`;
            }
            
            element.textContent = displayValue;
        }, 20);
    }

    // 初始化圖表
    initializeCharts() {
        // 收入趨勢圖
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            this.charts.revenue = new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '收入',
                        data: [],
                        borderColor: AdminConfig.CHART_COLORS.primary,
                        backgroundColor: AdminConfig.CHART_COLORS.primary + '20',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                color: '#ffffff'
                            },
                            grid: {
                                color: '#ffffff20'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#ffffff'
                            },
                            grid: {
                                color: '#ffffff20'
                            }
                        }
                    }
                }
            });
        }

        // 支付方式分布圖
        const methodCtx = document.getElementById('methodChart');
        if (methodCtx) {
            this.charts.method = new Chart(methodCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            AdminConfig.CHART_COLORS.primary,
                            AdminConfig.CHART_COLORS.secondary,
                            AdminConfig.CHART_COLORS.success,
                            AdminConfig.CHART_COLORS.warning
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    }
                }
            });
        }
    }

    // 更新圖表
    updateCharts(chartData) {
        // 更新收入趨勢圖
        if (this.charts.revenue && chartData.revenue) {
            this.charts.revenue.data.labels = chartData.revenue.labels;
            this.charts.revenue.data.datasets[0].data = chartData.revenue.data;
            this.charts.revenue.update();
        }

        // 更新支付方式分布圖
        if (this.charts.method && chartData.methods) {
            this.charts.method.data.labels = chartData.methods.labels;
            this.charts.method.data.datasets[0].data = chartData.methods.data;
            this.charts.method.update();
        }
    }

    // 更新最近交易
    updateRecentTransactions(transactions) {
        const container = document.querySelector('.recent-transactions-list');
        if (!container) return;

        container.innerHTML = transactions.map(transaction => `
            <div class="transaction-item" data-id="${transaction.id}">
                <div class="transaction-info">
                    <div class="transaction-id">#${transaction.id}</div>
                    <div class="transaction-user">${transaction.user}</div>
                    <div class="transaction-amount">${this.formatAmount(transaction.amount)}</div>
                    <div class="transaction-method">${transaction.method}</div>
                    <div class="transaction-status status-${transaction.status}">
                        ${this.getStatusText(transaction.status)}
                    </div>
                    <div class="transaction-time">${this.formatDate(transaction.created_at)}</div>
                </div>
                <div class="transaction-actions">
                    <button class="btn-sm" onclick="adminDashboard.viewTransaction('${transaction.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-sm" onclick="adminDashboard.editTransaction('${transaction.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    // 載入交易列表
    async loadTransactions() {
        try {
            const params = new URLSearchParams({
                page: this.filters.page,
                pageSize: this.filters.pageSize,
                status: this.filters.status,
                method: this.filters.method,
                dateRange: this.filters.dateRange
            });

            const response = await this.apiCall(`/admin/transactions?${params}`);
            if (response.success) {
                this.updateTransactionTable(response.data.transactions);
                this.updatePagination(response.data.pagination);
            }
        } catch (error) {
            console.error('載入交易列表失敗:', error);
        }
    }

    // 更新交易表格
    updateTransactionTable(transactions) {
        const tbody = document.querySelector('#transactions-table tbody');
        if (!tbody) return;

        tbody.innerHTML = transactions.map(transaction => `
            <tr data-id="${transaction.id}">
                <td>
                    <input type="checkbox" class="batch-checkbox" value="${transaction.id}">
                </td>
                <td>#${transaction.id}</td>
                <td>${transaction.user}</td>
                <td>${this.formatAmount(transaction.amount)}</td>
                <td>${transaction.method}</td>
                <td>
                    <span class="status-badge status-${transaction.status}">
                        ${this.getStatusText(transaction.status)}
                    </span>
                </td>
                <td>${this.formatDate(transaction.created_at)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-sm btn-primary" onclick="adminDashboard.viewTransaction('${transaction.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-sm btn-secondary" onclick="adminDashboard.editTransaction('${transaction.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-sm btn-danger" onclick="adminDashboard.deleteTransaction('${transaction.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // 更新分頁
    updatePagination(pagination) {
        const container = document.querySelector('.pagination');
        if (!container) return;

        const { currentPage, totalPages, totalItems } = pagination;
        
        container.innerHTML = `
            <div class="pagination-info">
                顯示第 ${(currentPage - 1) * this.filters.pageSize + 1} - 
                ${Math.min(currentPage * this.filters.pageSize, totalItems)} 項，
                共 ${totalItems} 項
            </div>
            <div class="pagination-controls">
                <button class="btn-sm" ${currentPage <= 1 ? 'disabled' : ''} 
                        onclick="adminDashboard.changePage(${currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </button>
                ${this.generatePageNumbers(currentPage, totalPages)}
                <button class="btn-sm" ${currentPage >= totalPages ? 'disabled' : ''} 
                        onclick="adminDashboard.changePage(${currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
    }

    // 生成頁碼
    generatePageNumbers(currentPage, totalPages) {
        const pages = [];
        const maxVisible = 5;
        
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        
        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }
        
        for (let i = start; i <= end; i++) {
            pages.push(`
                <button class="btn-sm ${i === currentPage ? 'active' : ''}" 
                        onclick="adminDashboard.changePage(${i})">
                    ${i}
                </button>
            `);
        }
        
        return pages.join('');
    }

    // 更改頁面
    changePage(page) {
        this.filters.page = page;
        this.loadTransactions();
    }

    // 更新過濾器
    updateFilter(name, value) {
        this.filters[name] = value;
        this.filters.page = 1; // 重置到第一頁
        this.refreshCurrentView();
    }

    // 執行搜索
    performSearch(query) {
        this.filters.search = query;
        this.filters.page = 1;
        this.refreshCurrentView();
    }

    // 刷新當前視圖
    refreshCurrentView() {
        this.loadViewData(this.currentView);
    }

    // 開始自動刷新
    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.refreshCurrentView();
            }
        }, AdminConfig.REFRESH_INTERVAL);
    }

    // 停止自動刷新
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    // 查看交易詳情
    async viewTransaction(id) {
        try {
            const response = await this.apiCall(`/admin/transactions/${id}`);
            if (response.success) {
                this.showTransactionModal(response.data);
            }
        } catch (error) {
            console.error('載入交易詳情失敗:', error);
            this.showNotification('載入交易詳情失敗', 'error');
        }
    }

    // 顯示交易模態框
    showTransactionModal(transaction) {
        const modal = document.querySelector('#transaction-modal');
        if (!modal) return;

        const content = modal.querySelector('.modal-content');
        content.innerHTML = `
            <div class="modal-header">
                <h3>交易詳情 #${transaction.id}</h3>
                <button class="modal-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="transaction-details">
                    <div class="detail-group">
                        <label>交易ID</label>
                        <span>${transaction.id}</span>
                    </div>
                    <div class="detail-group">
                        <label>用戶</label>
                        <span>${transaction.user}</span>
                    </div>
                    <div class="detail-group">
                        <label>金額</label>
                        <span>${this.formatAmount(transaction.amount)}</span>
                    </div>
                    <div class="detail-group">
                        <label>支付方式</label>
                        <span>${transaction.method}</span>
                    </div>
                    <div class="detail-group">
                        <label>狀態</label>
                        <span class="status-badge status-${transaction.status}">
                            ${this.getStatusText(transaction.status)}
                        </span>
                    </div>
                    <div class="detail-group">
                        <label>創建時間</label>
                        <span>${this.formatDate(transaction.created_at)}</span>
                    </div>
                    <div class="detail-group">
                        <label>更新時間</label>
                        <span>${this.formatDate(transaction.updated_at)}</span>
                    </div>
                    ${transaction.notes ? `
                        <div class="detail-group">
                            <label>備註</label>
                            <span>${transaction.notes}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary modal-close">關閉</button>
                <button class="btn btn-primary" onclick="adminDashboard.editTransaction('${transaction.id}')">
                    編輯
                </button>
            </div>
        `;

        modal.style.display = 'flex';
    }

    // 關閉模態框
    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    // 導出數據
    async exportData(format) {
        try {
            const params = new URLSearchParams({
                format,
                ...this.filters
            });

            const response = await fetch(`/admin/export?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `transactions_${Date.now()}.${format}`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.showNotification('導出成功', 'success');
            } else {
                throw new Error('導出失敗');
            }
        } catch (error) {
            console.error('導出數據失敗:', error);
            this.showNotification('導出失敗', 'error');
        }
    }

    // 處理交易更新
    handleTransactionUpdate(data) {
        // 更新表格中的交易項目
        const row = document.querySelector(`tr[data-id="${data.id}"]`);
        if (row) {
            const statusCell = row.querySelector('.status-badge');
            if (statusCell) {
                statusCell.className = `status-badge status-${data.status}`;
                statusCell.textContent = this.getStatusText(data.status);
            }
        }

        // 更新統計數據
        this.loadDashboardData();
    }

    // 處理系統通知
    handleSystemNotification(data) {
        this.showNotification(data.message, data.type || 'info');
    }

    // 顯示通知
    showNotification(message, type = 'info') {
        if (window.JyMainApp && window.JyMainApp.app()) {
            window.JyMainApp.app().showNotification(message, type);
        }
    }

    // API調用
    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '請求失敗');
        }

        return await response.json();
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
            year: 'numeric',
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
    }
}

// 管理後台工具函數
const AdminUtils = {
    // 格式化文件大小
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },

    // 生成隨機顏色
    generateRandomColor() {
        return '#' + Math.floor(Math.random() * 16777215).toString(16);
    },

    // 驗證電子郵件
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // 複製到剪貼板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('複製失敗:', err);
            return false;
        }
    }
};

// 初始化管理後台
let adminDashboard;
document.addEventListener('DOMContentLoaded', () => {
    // 檢查是否為管理員頁面
    if (window.location.pathname.includes('admin')) {
        adminDashboard = new AdminDashboard();
    }
});

// 導出全局對象
window.JyAdmin = {
    dashboard: () => adminDashboard,
    utils: AdminUtils,
    config: AdminConfig
};

console.log('🎛️ 管理後台模組已載入');