-- 最高階自動贊助系統 - 資料庫初始化腳本
-- 4D科技風格 - MySQL 8.0+
-- 版本: 1.0.0
-- 作者: AI Assistant
-- 日期: 2024

-- 創建資料庫
CREATE DATABASE IF NOT EXISTS sponsor_system 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE sponsor_system;

-- 設置時區
SET time_zone = '+08:00';

-- 用戶表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    -- 統計字段
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    quick_buy_success INT DEFAULT 0,
    quick_buy_failed INT DEFAULT 0,
    
    -- 索引
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    category VARCHAR(50),
    image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_quick_buy BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_name (name),
    INDEX idx_category (category),
    INDEX idx_active (is_active),
    INDEX idx_quick_buy (is_quick_buy),
    INDEX idx_price (price),
    INDEX idx_stock (stock)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 訂單表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    amount INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'cancelled', 'failed') DEFAULT 'pending',
    is_quick_buy BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    -- 外鍵約束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_status (status),
    INDEX idx_quick_buy (is_quick_buy),
    INDEX idx_created_at (created_at),
    INDEX idx_payment_method (payment_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用戶偏好設置表
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    default_payment_method VARCHAR(50) DEFAULT 'balance',
    quick_buy_enabled BOOLEAN DEFAULT TRUE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    theme VARCHAR(20) DEFAULT '4d-tech',
    language VARCHAR(10) DEFAULT 'zh-TW',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 速買統計表
CREATE TABLE IF NOT EXISTS quick_buy_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    success_count INT DEFAULT 0,
    failed_count INT DEFAULT 0,
    total_amount INT DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    last_purchase TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    
    -- 唯一約束
    UNIQUE KEY unique_user_item (user_id, item_id),
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_last_purchase (last_purchase)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 購買歷史緩存表
CREATE TABLE IF NOT EXISTS purchase_history_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    purchase_count INT DEFAULT 0,
    last_purchase_price DECIMAL(10,2),
    avg_purchase_amount DECIMAL(5,2) DEFAULT 1.00,
    preference_score DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    
    -- 唯一約束
    UNIQUE KEY unique_user_item_cache (user_id, item_id),
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_preference_score (preference_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 活動日誌表
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 支付方式表
CREATE TABLE IF NOT EXISTS payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    method_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    is_enabled BOOLEAN DEFAULT TRUE,
    processing_fee DECIMAL(5,4) DEFAULT 0.0000,
    min_amount DECIMAL(10,2) DEFAULT 0.01,
    max_amount DECIMAL(10,2) DEFAULT 999999.99,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_method_id (method_id),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 系統配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_config_key (config_key),
    INDEX idx_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    is_global BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_read (is_read),
    INDEX idx_global (is_global),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始數據

-- 插入管理員用戶
INSERT INTO users (username, email, password_hash, balance, is_admin, total_orders, total_spent) VALUES
('admin', 'admin@sponsor-system.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS', 10000.00, TRUE, 0, 0.00),
('demo_user', 'demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS', 1000.00, FALSE, 5, 250.00),
('speed_buyer', 'speed@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS', 5000.00, FALSE, 15, 750.00);

-- 插入商品數據
INSERT INTO items (name, description, price, stock, category, image, is_quick_buy) VALUES
('遊戲點數 100點', '通用遊戲點數，可用於多種遊戲內購買', 10.00, 1000, 'game_points', '/images/game-points-100.jpg', TRUE),
('遊戲點數 500點', '通用遊戲點數，可用於多種遊戲內購買', 45.00, 800, 'game_points', '/images/game-points-500.jpg', TRUE),
('遊戲點數 1000點', '通用遊戲點數，可用於多種遊戲內購買', 85.00, 500, 'game_points', '/images/game-points-1000.jpg', TRUE),
('VIP會員 1個月', '享受VIP專屬特權和優惠', 29.99, 200, 'membership', '/images/vip-1month.jpg', TRUE),
('VIP會員 3個月', '享受VIP專屬特權和優惠', 79.99, 150, 'membership', '/images/vip-3month.jpg', FALSE),
('VIP會員 12個月', '享受VIP專屬特權和優惠', 299.99, 100, 'membership', '/images/vip-12month.jpg', FALSE),
('特殊道具包', '包含稀有道具和裝備', 19.99, 300, 'items', '/images/special-pack.jpg', TRUE),
('經驗加速器', '2倍經驗獲得，持續24小時', 5.99, 500, 'boosters', '/images/exp-booster.jpg', TRUE),
('金幣加速器', '2倍金幣獲得，持續24小時', 5.99, 500, 'boosters', '/images/gold-booster.jpg', TRUE),
('限定皮膚', '限時發售的角色皮膚', 39.99, 50, 'cosmetics', '/images/limited-skin.jpg', FALSE);

-- 插入用戶偏好設置
INSERT INTO user_preferences (user_id, default_payment_method, quick_buy_enabled, notifications_enabled) VALUES
(1, 'balance', TRUE, TRUE),
(2, 'balance', TRUE, TRUE),
(3, 'balance', TRUE, TRUE);

-- 插入支付方式
INSERT INTO payment_methods (method_id, name, description, icon, is_enabled, processing_fee, min_amount, max_amount) VALUES
('balance', '帳戶餘額', '使用帳戶餘額進行支付，即時到帳', 'fas fa-wallet', TRUE, 0.0000, 0.01, 999999.99),
('credit_card', '信用卡', '支持Visa、MasterCard等主流信用卡', 'fas fa-credit-card', FALSE, 0.0300, 1.00, 10000.00),
('paypal', 'PayPal', '安全便捷的PayPal支付', 'fab fa-paypal', FALSE, 0.0350, 1.00, 5000.00),
('alipay', '支付寶', '支付寶快捷支付', 'fab fa-alipay', FALSE, 0.0200, 1.00, 20000.00),
('wechat_pay', '微信支付', '微信掃碼支付', 'fab fa-weixin', FALSE, 0.0200, 1.00, 20000.00);

-- 插入系統配置
INSERT INTO system_config (config_key, config_value, description, is_public) VALUES
('system_name', '最高階自動贊助系統', '系統名稱', TRUE),
('system_version', '1.0.0', '系統版本', TRUE),
('maintenance_mode', 'false', '維護模式開關', FALSE),
('quick_buy_enabled', 'true', '速買功能開關', TRUE),
('max_quick_buy_amount', '100', '單次速買最大數量', TRUE),
('quick_buy_timeout', '30', '速買超時時間（秒）', FALSE),
('default_currency', 'USD', '默認貨幣', TRUE),
('support_email', 'support@sponsor-system.com', '客服郵箱', TRUE),
('announcement', '歡迎使用最高階自動贊助系統！享受4D科技風格的極致體驗。', '系統公告', TRUE),
('terms_of_service', '使用本系統即表示您同意我們的服務條款...', '服務條款', TRUE);

-- 插入示例訂單數據
INSERT INTO orders (order_id, user_id, item_id, amount, total_price, payment_method, status, is_quick_buy, completed_at) VALUES
('QB20241201120001', 2, 1, 5, 50.00, 'balance', 'completed', TRUE, NOW() - INTERVAL 1 DAY),
('QB20241201120002', 2, 4, 1, 29.99, 'balance', 'completed', TRUE, NOW() - INTERVAL 2 DAY),
('OR20241201120003', 3, 2, 10, 450.00, 'balance', 'completed', FALSE, NOW() - INTERVAL 3 DAY),
('QB20241201120004', 3, 7, 2, 39.98, 'balance', 'completed', TRUE, NOW() - INTERVAL 1 HOUR),
('QB20241201120005', 3, 8, 3, 17.97, 'balance', 'completed', TRUE, NOW() - INTERVAL 30 MINUTE);

-- 插入速買統計數據
INSERT INTO quick_buy_stats (user_id, item_id, success_count, failed_count, total_amount, total_spent, last_purchase) VALUES
(2, 1, 3, 0, 15, 150.00, NOW() - INTERVAL 1 DAY),
(2, 4, 1, 0, 1, 29.99, NOW() - INTERVAL 2 DAY),
(3, 2, 2, 0, 20, 900.00, NOW() - INTERVAL 3 DAY),
(3, 7, 5, 1, 10, 199.90, NOW() - INTERVAL 1 HOUR),
(3, 8, 8, 0, 24, 143.76, NOW() - INTERVAL 30 MINUTE);

-- 插入購買歷史緩存
INSERT INTO purchase_history_cache (user_id, item_id, purchase_count, last_purchase_price, avg_purchase_amount, preference_score) VALUES
(2, 1, 3, 10.00, 5.00, 0.85),
(2, 4, 1, 29.99, 1.00, 0.60),
(3, 2, 2, 45.00, 10.00, 0.90),
(3, 7, 5, 19.99, 2.00, 0.95),
(3, 8, 8, 5.99, 3.00, 0.88);

-- 插入活動日誌
INSERT INTO activity_logs (user_id, action, description, ip_address) VALUES
(1, 'login', '管理員登入系統', '127.0.0.1'),
(2, 'register', '用戶註冊', '192.168.1.100'),
(2, 'login', '用戶登入', '192.168.1.100'),
(2, 'quick_buy', '速買成功: 遊戲點數 100點 x5', '192.168.1.100'),
(3, 'register', '用戶註冊', '192.168.1.101'),
(3, 'login', '用戶登入', '192.168.1.101'),
(3, 'quick_buy', '速買成功: 特殊道具包 x2', '192.168.1.101'),
(3, 'quick_buy', '速買成功: 經驗加速器 x3', '192.168.1.101');

-- 插入通知數據
INSERT INTO notifications (user_id, title, message, type, is_global) VALUES
(NULL, '系統維護通知', '系統將於今晚23:00-01:00進行維護升級，期間可能影響服務使用。', 'warning', TRUE),
(2, '速買成功', '您的速買訂單 QB20241201120001 已完成處理。', 'success', FALSE),
(3, '餘額提醒', '您的帳戶餘額充足，可以繼續享受速買服務。', 'info', FALSE),
(NULL, '新功能上線', '4D科技風格界面全新升級，帶來更極致的視覺體驗！', 'info', TRUE);

-- 創建視圖

-- 用戶統計視圖
CREATE VIEW user_stats_view AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.balance,
    u.total_orders,
    u.total_spent,
    u.quick_buy_success,
    u.quick_buy_failed,
    u.created_at,
    u.last_login,
    COUNT(DISTINCT o.id) as actual_orders,
    SUM(CASE WHEN o.is_quick_buy = 1 THEN 1 ELSE 0 END) as actual_quick_buys,
    AVG(o.total_price) as avg_order_value
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed'
GROUP BY u.id;

-- 商品統計視圖
CREATE VIEW item_stats_view AS
SELECT 
    i.id,
    i.name,
    i.price,
    i.stock,
    i.category,
    i.is_quick_buy,
    COUNT(DISTINCT o.id) as total_orders,
    SUM(o.amount) as total_sold,
    SUM(o.total_price) as total_revenue,
    AVG(o.amount) as avg_order_amount,
    COUNT(DISTINCT o.user_id) as unique_buyers
FROM items i
LEFT JOIN orders o ON i.id = o.item_id AND o.status = 'completed'
GROUP BY i.id;

-- 每日統計視圖
CREATE VIEW daily_stats_view AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_orders,
    SUM(CASE WHEN is_quick_buy = 1 THEN 1 ELSE 0 END) as quick_buy_orders,
    SUM(total_price) as total_revenue,
    AVG(total_price) as avg_order_value,
    COUNT(DISTINCT user_id) as unique_users
FROM orders 
WHERE status = 'completed'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 創建存儲過程

DELIMITER //

-- 用戶餘額充值存儲過程
CREATE PROCEDURE AddUserBalance(
    IN p_user_id INT,
    IN p_amount DECIMAL(10,2),
    IN p_description VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 更新用戶餘額
    UPDATE users 
    SET balance = balance + p_amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_user_id AND is_active = 1;
    
    -- 記錄活動日誌
    INSERT INTO activity_logs (user_id, action, description, created_at)
    VALUES (p_user_id, 'balance_add', p_description, CURRENT_TIMESTAMP);
    
    COMMIT;
END //

-- 清理過期通知存儲過程
CREATE PROCEDURE CleanupExpiredNotifications()
BEGIN
    DELETE FROM notifications 
    WHERE expires_at IS NOT NULL 
    AND expires_at < CURRENT_TIMESTAMP;
    
    SELECT ROW_COUNT() as deleted_count;
END //

-- 獲取用戶推薦商品存儲過程
CREATE PROCEDURE GetUserRecommendations(
    IN p_user_id INT,
    IN p_limit INT DEFAULT 10
)
BEGIN
    SELECT 
        i.id,
        i.name,
        i.price,
        i.image,
        i.is_quick_buy,
        COALESCE(phc.preference_score, 0) as preference_score,
        COALESCE(phc.purchase_count, 0) as purchase_count
    FROM items i
    LEFT JOIN purchase_history_cache phc ON i.id = phc.item_id AND phc.user_id = p_user_id
    WHERE i.is_active = 1 AND i.stock > 0
    ORDER BY 
        COALESCE(phc.preference_score, 0) DESC,
        i.is_quick_buy DESC,
        RAND()
    LIMIT p_limit;
END //

DELIMITER ;

-- 創建觸發器

-- 訂單完成後更新用戶統計
DELIMITER //
CREATE TRIGGER update_user_stats_after_order
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE users 
        SET 
            total_orders = total_orders + 1,
            total_spent = total_spent + NEW.total_price,
            quick_buy_success = CASE WHEN NEW.is_quick_buy = 1 
                               THEN quick_buy_success + 1 
                               ELSE quick_buy_success END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.user_id;
        
        -- 更新購買歷史緩存
        INSERT INTO purchase_history_cache 
        (user_id, item_id, purchase_count, last_purchase_price, avg_purchase_amount, preference_score)
        VALUES (NEW.user_id, NEW.item_id, 1, NEW.total_price / NEW.amount, NEW.amount, 0.5)
        ON DUPLICATE KEY UPDATE
            purchase_count = purchase_count + 1,
            last_purchase_price = NEW.total_price / NEW.amount,
            avg_purchase_amount = (avg_purchase_amount + NEW.amount) / 2,
            preference_score = LEAST(1.0, preference_score + 0.1),
            updated_at = CURRENT_TIMESTAMP;
    END IF;
END //
DELIMITER ;

-- 創建索引優化查詢性能
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_created_status ON orders(created_at, status);
CREATE INDEX idx_activity_logs_user_action ON activity_logs(user_id, action);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);

-- 創建全文索引用於搜索
ALTER TABLE items ADD FULLTEXT(name, description);
ALTER TABLE notifications ADD FULLTEXT(title, message);

-- 設置自動清理任務（需要事件調度器支持）
SET GLOBAL event_scheduler = ON;

-- 每天清理過期通知
CREATE EVENT IF NOT EXISTS cleanup_expired_notifications
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
  CALL CleanupExpiredNotifications();

-- 每週清理舊的活動日誌（保留3個月）
CREATE EVENT IF NOT EXISTS cleanup_old_activity_logs
ON SCHEDULE EVERY 1 WEEK
STARTS CURRENT_TIMESTAMP
DO
  DELETE FROM activity_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- 插入初始化完成標記
INSERT INTO system_config (config_key, config_value, description, is_public) 
VALUES ('database_initialized', 'true', '資料庫初始化完成標記', FALSE);

-- 顯示初始化結果
SELECT 
    '資料庫初始化完成' as status,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM items) as total_items,
    (SELECT COUNT(*) FROM orders) as total_orders,
    (SELECT COUNT(*) FROM payment_methods WHERE is_enabled = 1) as enabled_payment_methods,
    NOW() as initialized_at;

-- 顯示管理員登入信息
SELECT 
    '管理員帳戶信息' as info,
    'admin' as username,
    'admin@sponsor-system.com' as email,
    'password123' as default_password,
    '請立即修改默認密碼！' as security_notice;

COMMIT;