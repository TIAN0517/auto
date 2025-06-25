#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 主應用服務器
Main Application Server for 4D Tech Style Auto Sponsorship System

主要功能:
- HTTP服務器 (端口8080)
- 靜態文件服務
- API路由管理
- WebSocket支援
- 支付閘道整合
- 用戶認證
- 資料庫連接
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Web框架
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# 資料庫
import sqlite3
from contextlib import contextmanager

# 支付服務
from payment_gateway import PaymentGateway
from speedpay_service import SpeedPayService
from ecpay_service import ECPayService
from newebpay_service import NewebPayService
from webhook_handler import WebhookHandler

# 模型
from models.payment import Payment
from models.transaction import Transaction

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 應用配置
class AppConfig:
    """應用程序配置"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'jy-4d-tech-sponsor-system-2024')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8080))
    
    # 資料庫配置
    DATABASE_PATH = os.path.join('database', 'sponsor_system.db')
    
    # 支付配置
    PAYMENT_TIMEOUT = 300  # 5分鐘
    MAX_PAYMENT_AMOUNT = 50000  # 最大支付金額
    MIN_PAYMENT_AMOUNT = 10     # 最小支付金額
    
    # 文件上傳配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}
    
    # 安全配置
    SESSION_TIMEOUT = 3600  # 1小時
    MAX_LOGIN_ATTEMPTS = 5
    RATE_LIMIT_PER_MINUTE = 60
    
    # WebSocket配置
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

# 創建Flask應用
app = Flask(__name__, 
           static_folder='../frontend',
           template_folder='../frontend')
app.config.from_object(AppConfig)

# 啟用CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 初始化SocketIO
socketio = SocketIO(app, 
                   cors_allowed_origins=AppConfig.SOCKETIO_CORS_ALLOWED_ORIGINS,
                   async_mode=AppConfig.SOCKETIO_ASYNC_MODE)

# 初始化支付服務
payment_gateway = PaymentGateway()
speedpay_service = SpeedPayService()
ecpay_service = ECPayService()
newebpay_service = NewebPayService()
webhook_handler = WebhookHandler()

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化資料庫"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with self.get_connection() as conn:
                # 創建用戶表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        phone VARCHAR(20),
                        is_active BOOLEAN DEFAULT 1,
                        is_admin BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 創建支付訂單表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS payment_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id VARCHAR(50) UNIQUE NOT NULL,
                        user_id INTEGER,
                        package_id VARCHAR(20) NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        original_amount DECIMAL(10,2) NOT NULL,
                        discount_amount DECIMAL(10,2) DEFAULT 0,
                        discount_code VARCHAR(20),
                        payment_method VARCHAR(20) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        payment_url TEXT,
                        callback_data TEXT,
                        expires_at TIMESTAMP,
                        paid_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # 創建交易記錄表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_id VARCHAR(50) UNIQUE NOT NULL,
                        order_id VARCHAR(50) NOT NULL,
                        payment_method VARCHAR(20) NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        fee DECIMAL(10,2) DEFAULT 0,
                        status VARCHAR(20) NOT NULL,
                        gateway_response TEXT,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (order_id) REFERENCES payment_orders (order_id)
                    )
                ''')
                
                # 創建系統設置表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_settings (
                        key VARCHAR(50) PRIMARY KEY,
                        value TEXT NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 創建日誌表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level VARCHAR(10) NOT NULL,
                        message TEXT NOT NULL,
                        module VARCHAR(50),
                        user_id INTEGER,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("資料庫初始化完成")
                
        except Exception as e:
            logger.error(f"資料庫初始化失敗: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """執行查詢"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """執行更新"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

# 初始化資料庫管理器
db_manager = DatabaseManager(AppConfig.DATABASE_PATH)

class AuthManager:
    """認證管理器"""
    
    @staticmethod
    def create_user(username: str, email: str, password: str, phone: str = None) -> Dict:
        """創建用戶"""
        try:
            password_hash = generate_password_hash(password)
            
            query = '''
                INSERT INTO users (username, email, password_hash, phone)
                VALUES (?, ?, ?, ?)
            '''
            
            db_manager.execute_update(query, (username, email, password_hash, phone))
            
            # 獲取創建的用戶
            user = AuthManager.get_user_by_email(email)
            logger.info(f"用戶創建成功: {username}")
            
            return {
                'success': True,
                'user': user,
                'message': '用戶創建成功'
            }
            
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'message': '用戶名已存在'}
            elif 'email' in str(e):
                return {'success': False, 'message': '電子郵件已存在'}
            else:
                return {'success': False, 'message': '創建用戶失敗'}
        except Exception as e:
            logger.error(f"創建用戶失敗: {e}")
            return {'success': False, 'message': '系統錯誤'}
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Dict:
        """用戶認證"""
        try:
            user = AuthManager.get_user_by_email(email)
            
            if not user:
                return {'success': False, 'message': '用戶不存在'}
            
            if not user['is_active']:
                return {'success': False, 'message': '帳戶已停用'}
            
            if not check_password_hash(user['password_hash'], password):
                return {'success': False, 'message': '密碼錯誤'}
            
            # 更新最後登入時間
            db_manager.execute_update(
                'UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            
            logger.info(f"用戶登入成功: {email}")
            
            return {
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'is_admin': user['is_admin']
                },
                'message': '登入成功'
            }
            
        except Exception as e:
            logger.error(f"用戶認證失敗: {e}")
            return {'success': False, 'message': '系統錯誤'}
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """根據郵箱獲取用戶"""
        users = db_manager.execute_query(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        )
        return users[0] if users else None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """根據ID獲取用戶"""
        users = db_manager.execute_query(
            'SELECT * FROM users WHERE id = ?',
            (user_id,)
        )
        return users[0] if users else None

# 路由定義

@app.route('/')
def index():
    """主頁"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """靜態文件服務"""
    return send_from_directory(app.static_folder, filename)

# API路由

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'services': {
            'database': 'connected',
            'payment_gateway': 'active',
            'websocket': 'running'
        }
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用戶註冊"""
    try:
        data = request.get_json()
        
        # 驗證必要字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} 是必要字段'}), 400
        
        # 創建用戶
        result = AuthManager.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            phone=data.get('phone')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"註冊失敗: {e}")
        return jsonify({'success': False, 'message': '系統錯誤'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用戶登入"""
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': '郵箱和密碼是必要字段'}), 400
        
        # 認證用戶
        result = AuthManager.authenticate_user(email, password)
        
        if result['success']:
            # 設置會話
            session['user_id'] = result['user']['id']
            session['user_email'] = result['user']['email']
            session['login_time'] = datetime.now().isoformat()
            
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"登入失敗: {e}")
        return jsonify({'success': False, 'message': '系統錯誤'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用戶登出"""
    session.clear()
    return jsonify({'success': True, 'message': '登出成功'})

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """獲取用戶資料"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登入'}), 401
    
    user = AuthManager.get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用戶不存在'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'phone': user['phone'],
            'is_admin': user['is_admin'],
            'created_at': user['created_at']
        }
    })

@app.route('/api/payments/create', methods=['POST'])
def create_payment():
    """創建支付訂單"""
    try:
        data = request.get_json()
        
        # 驗證必要字段
        required_fields = ['package_id', 'amount', 'payment_method']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} 是必要字段'}), 400
        
        # 創建支付訂單
        result = payment_gateway.create_payment_order(
            user_id=session.get('user_id'),
            package_id=data['package_id'],
            amount=data['amount'],
            original_amount=data.get('original_amount', data['amount']),
            discount_amount=data.get('discount_amount', 0),
            discount_code=data.get('discount_code'),
            payment_method=data['payment_method'],
            customer_info=data.get('customer', {})
        )
        
        if result['success']:
            # 發送WebSocket通知
            socketio.emit('payment_created', {
                'order_id': result['order_id'],
                'amount': data['amount'],
                'payment_method': data['payment_method']
            })
            
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"創建支付訂單失敗: {e}")
        return jsonify({'success': False, 'message': '系統錯誤'}), 500

@app.route('/api/payments/<order_id>/status', methods=['GET'])
def get_payment_status(order_id):
    """獲取支付狀態"""
    try:
        result = payment_gateway.get_payment_status(order_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"獲取支付狀態失敗: {e}")
        return jsonify({'success': False, 'message': '系統錯誤'}), 500

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """管理後台儀表板"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登入'}), 401
    
    user = AuthManager.get_user_by_id(user_id)
    if not user or not user['is_admin']:
        return jsonify({'success': False, 'message': '權限不足'}), 403
    
    try:
        # 獲取統計數據
        stats = {
            'total_orders': db_manager.execute_query('SELECT COUNT(*) as count FROM payment_orders')[0]['count'],
            'total_revenue': db_manager.execute_query('SELECT COALESCE(SUM(amount), 0) as total FROM payment_orders WHERE status = "completed"')[0]['total'],
            'pending_orders': db_manager.execute_query('SELECT COUNT(*) as count FROM payment_orders WHERE status = "pending"')[0]['count'],
            'total_users': db_manager.execute_query('SELECT COUNT(*) as count FROM users')[0]['count']
        }
        
        # 獲取最近交易
        recent_transactions = db_manager.execute_query('''
            SELECT po.order_id, po.amount, po.payment_method, po.status, po.created_at,
                   u.username, u.email
            FROM payment_orders po
            LEFT JOIN users u ON po.user_id = u.id
            ORDER BY po.created_at DESC
            LIMIT 10
        ''')
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_transactions': recent_transactions
        })
        
    except Exception as e:
        logger.error(f"獲取管理後台數據失敗: {e}")
        return jsonify({'success': False, 'message': '系統錯誤'}), 500

# WebSocket事件處理

@socketio.on('connect')
def handle_connect():
    """WebSocket連接"""
    logger.info(f"WebSocket客戶端連接: {request.sid}")
    emit('connected', {'message': '連接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket斷開連接"""
    logger.info(f"WebSocket客戶端斷開: {request.sid}")

@socketio.on('join_room')
def handle_join_room(data):
    """加入房間"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined_room', {'room': room})
        logger.info(f"客戶端 {request.sid} 加入房間 {room}")

@socketio.on('leave_room')
def handle_leave_room(data):
    """離開房間"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left_room', {'room': room})
        logger.info(f"客戶端 {request.sid} 離開房間 {room}")

# 支付回調處理

@app.route('/webhook/speedpay', methods=['POST'])
def speedpay_webhook():
    """速買配回調"""
    return webhook_handler.handle_speedpay_callback(request)

@app.route('/webhook/ecpay', methods=['POST'])
def ecpay_webhook():
    """綠界回調"""
    return webhook_handler.handle_ecpay_callback(request)

@app.route('/webhook/newebpay', methods=['POST'])
def newebpay_webhook():
    """藍新回調"""
    return webhook_handler.handle_newebpay_callback(request)

# 錯誤處理

@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    return jsonify({'error': '頁面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    logger.error(f"內部錯誤: {error}")
    return jsonify({'error': '內部服務器錯誤'}), 500

# 應用啟動
def create_directories():
    """創建必要目錄"""
    directories = ['logs', 'uploads', 'database']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """主函數"""
    try:
        # 創建必要目錄
        create_directories()
        
        logger.info("4D科技風格自動贊助系統啟動中...")
        logger.info(f"服務器地址: http://{AppConfig.HOST}:{AppConfig.PORT}")
        logger.info(f"調試模式: {AppConfig.DEBUG}")
        logger.info(f"資料庫路徑: {AppConfig.DATABASE_PATH}")
        
        # 啟動應用
        socketio.run(
            app,
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            debug=AppConfig.DEBUG,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("\n系統正在關閉...")
    except Exception as e:
        logger.error(f"系統啟動失敗: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()