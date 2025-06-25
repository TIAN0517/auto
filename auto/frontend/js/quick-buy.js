// Quick Buy功能模組
class QuickBuy {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        console.log('Quick Buy module initialized');
    }

    bindEvents() {
        // 綁定快速購買按鈕事件
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="quick-buy"]')) {
                this.showQuickBuyModal();
            }
        });
    }

    showQuickBuyModal() {
        // 顯示快速購買模態框
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>快速購買</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p>快速購買功能開發中...</p>
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
}

// 初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new QuickBuy();
    });
} else {
    new QuickBuy();
}