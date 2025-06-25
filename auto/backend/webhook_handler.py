#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 支付回調處理
Webhook Handler for 4D Tech Style Auto Sponsorship System

主要功能:
- 處理各支付平台回調
- 驗證回調請求
- 更新訂單狀態
- 發送WebSocket通知
- 記錄交易日誌
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from flask import request, Response, Blueprint, current_app
from functools import wraps

logger = logging.getLogger(__name__)

# 創建藍圖
webhook_bp = Blueprint('webhook', __name__)

# 回調處理鎖
callback_locks = {}

# 回調處理裝飾器
def payment_callback(payment_type: str):
    """支付回調處理裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 獲取訂單ID
            order_id = None
            try:
                if payment_type == 'speedpay':
                    order_id = request.form.get('out_trade_no') or request.json.get('out_trade_no')
                elif payment_type == 'ecpay':
                    order_id = request.form.get('MerchantTradeNo')
                elif payment_type == 'newebpay':
                    # 藍新需要解密TradeInfo才能獲取訂單ID
                    # 這裡先設置為None，在處理函數中獲取
                    pass
            except Exception as e:
                logger.error(f"獲取訂單ID失敗: {e}")
            
            # 如果沒有訂單ID，直接處理
            if not order_id:
                return func(*args, **kwargs)
            
            # 使用訂單ID作為鎖的鍵值
            lock = callback_locks.setdefault(order_id, threading.Lock())
            
            # 嘗試獲取鎖
            if not lock.acquire(blocking=False):
                logger.warning(f"訂單 {order_id} 的回調正在處理中，忽略重複請求")
                return Response("處理中", status=200)
            
            try:
                # 執行回調處理
                return func(*args, **kwargs)
            finally:
                # 釋放鎖
                lock.release()
                
                # 清理鎖（可選，防止鎖過多）
                if len(callback_locks) > 1000:  # 如果鎖太多，清理一些
                    try:
                        old_locks = list(callback_locks.keys())[:500]  # 清理前500個
                        for old_key in old_locks:
                            callback_locks.pop(old_key, None)
                    except Exception as e:
                        logger.error(f"清理回調鎖失敗: {e}")
        
        return wrapper
    return decorator

# 速買配回調處理
@webhook_bp.route('/speedpay/callback', methods=['POST'])
@payment_callback('speedpay')
def speedpay_callback():
    """處理速買配回調"""
    try:
        logger.info("收到速買配回調請求")
        
        # 獲取回調數據
        callback_data = {}
        if request.is_json:
            callback_data = request.json
        else:
            callback_data = request.form.to_dict()
        
        logger.debug(f"速買配回調數據: {callback_data}")
        
        # 獲取訂單ID
        order_id = callback_data.get('out_trade_no')
        if not order_id:
            logger.error("速買配回調缺少訂單ID")
            return Response("缺少訂單ID", status=400)
        
        # 獲取支付閘道
        payment_gateway = current_app.payment_gateway
        if not payment_gateway:
            logger.error("支付閘道未初始化")
            return Response("系統錯誤", status=500)
        
        # 驗證回調
        result = payment_gateway.validate_callback('speedpay', callback_data)
        
        if not result['success']:
            logger.error(f"速買配回調驗證失敗: {result['message']}")
            return Response("驗證失敗", status=400)
        
        # 處理支付結果
        process_result = process_payment_result(result)
        
        if process_result['success']:
            # 返回成功響應（速買配要求返回success字符串）
            return Response("success", status=200)
        else:
            logger.error(f"處理速買配回調失敗: {process_result['message']}")
            return Response("處理失敗", status=500)
        
    except Exception as e:
        logger.error(f"處理速買配回調異常: {e}")
        return Response("系統錯誤", status=500)

# 綠界回調處理
@webhook_bp.route('/ecpay/callback', methods=['POST'])
@payment_callback('ecpay')
def ecpay_callback():
    """處理綠界回調"""
    try:
        logger.info("收到綠界回調請求")
        
        # 獲取回調數據
        callback_data = request.form.to_dict()
        
        logger.debug(f"綠界回調數據: {callback_data}")
        
        # 獲取訂單ID
        order_id = callback_data.get('MerchantTradeNo')
        if not order_id:
            logger.error("綠界回調缺少訂單ID")
            return Response("缺少訂單ID", status=400)
        
        # 獲取支付閘道
        payment_gateway = current_app.payment_gateway
        if not payment_gateway:
            logger.error("支付閘道未初始化")
            return Response("系統錯誤", status=500)
        
        # 驗證回調
        result = payment_gateway.validate_callback('ecpay', callback_data)
        
        if not result['success']:
            logger.error(f"綠界回調驗證失敗: {result['message']}")
            return Response("驗證失敗", status=400)
        
        # 處理支付結果
        process_result = process_payment_result(result)
        
        if process_result['success']:
            # 返回成功響應（綠界要求返回1|OK）
            return Response("1|OK", status=200)
        else:
            logger.error(f"處理綠界回調失敗: {process_result['message']}")
            return Response("0|處理失敗", status=200)  # 綠界要求返回200狀態碼
        
    except Exception as e:
        logger.error(f"處理綠界回調異常: {e}")
        return Response("0|系統錯誤", status=200)  # 綠界要求返回200狀態碼

# 藍新回調處理
@webhook_bp.route('/newebpay/callback', methods=['POST'])
@payment_callback('newebpay')
def newebpay_callback():
    """處理藍新回調"""
    try:
        logger.info("收到藍新回調請求")
        
        # 獲取回調數據
        callback_data = request.form.to_dict()
        
        logger.debug(f"藍新回調數據: {callback_data}")
        
        # 獲取支付閘道
        payment_gateway = current_app.payment_gateway
        if not payment_gateway:
            logger.error("支付閘道未初始化")
            return Response("系統錯誤", status=500)
        
        # 驗證回調
        result = payment_gateway.validate_callback('newebpay', callback_data)
        
        if not result['success']:
            logger.error(f"藍新回調驗證失敗: {result['message']}")
            return Response("驗證失敗", status=400)
        
        # 處理支付結果
        process_result = process_payment_result(result)
        
        if process_result['success']:
            # 返回成功響應
            return Response("SUCCESS", status=200)
        else:
            logger.error(f"處理藍新回調失敗: {process_result['message']}")
            return Response("FAIL", status=200)  # 藍新要求返回200狀態碼
        
    except Exception as e:
        logger.error(f"處理藍新回調異常: {e}")
        return Response("FAIL", status=200)  # 藍新要求返回200狀態碼

# 通用支付結果處理
def process_payment_result(result: Dict) -> Dict:
    """處理支付結果"""
    try:
        # 獲取訂單ID
        order_id = result.get('order_id')
        if not order_id:
            logger.error("支付結果缺少訂單ID")
            return {
                'success': False,
                'message': '缺少訂單ID'
            }
        
        # 獲取支付狀態
        status = result.get('status')
        if not status:
            logger.error("支付結果缺少狀態")
            return {
                'success': False,
                'message': '缺少狀態'
            }
        
        # 獲取數據庫管理器
        db_manager = current_app.db_manager
        if not db_manager:
            logger.error("數據庫管理器未初始化")
            return {
                'success': False,
                'message': '系統錯誤'
            }
        
        # 獲取WebSocket管理器
        ws_manager = current_app.ws_manager
        
        # 更新訂單狀態
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # 查詢訂單
            cursor.execute(
                "SELECT id, user_id, amount, status FROM payment_orders WHERE order_id = ?",
                (order_id,)
            )
            order = cursor.fetchone()
            
            if not order:
                logger.error(f"訂單不存在: {order_id}")
                return {
                    'success': False,
                    'message': '訂單不存在'
                }
            
            order_db_id, user_id, amount, current_status = order
            
            # 檢查訂單狀態
            if current_status == 'completed':
                logger.info(f"訂單已完成，忽略重複回調: {order_id}")
                return {
                    'success': True,
                    'message': '訂單已完成'
                }
            
            # 更新訂單狀態
            cursor.execute(
                "UPDATE payment_orders SET status = ?, updated_at = ?, transaction_id = ? WHERE order_id = ?",
                (status, datetime.now().isoformat(), result.get('transaction_id'), order_id)
            )
            
            # 如果支付成功，創建交易記錄
            if status == 'completed':
                cursor.execute(
                    "INSERT INTO transactions (user_id, order_id, amount, type, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, order_id, amount, 'sponsor', 'completed', datetime.now().isoformat())
                )
                
                # 更新用戶贊助金額
                cursor.execute(
                    "UPDATE users SET total_sponsored = total_sponsored + ?, updated_at = ? WHERE id = ?",
                    (amount, datetime.now().isoformat(), user_id)
                )
            
            # 提交事務
            conn.commit()
            
            # 發送WebSocket通知
            if ws_manager:
                # 發送給用戶
                if user_id:
                    ws_manager.send_to_user(user_id, {
                        'type': 'payment_update',
                        'order_id': order_id,
                        'status': status,
                        'amount': amount,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # 發送給管理員
                ws_manager.send_to_room('admin', {
                    'type': 'payment_update',
                    'order_id': order_id,
                    'user_id': user_id,
                    'status': status,
                    'amount': amount,
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"訂單狀態更新成功: {order_id} - {status}")
            
            return {
                'success': True,
                'message': '處理成功'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新訂單狀態失敗: {e}")
            return {
                'success': False,
                'message': f'更新訂單狀態失敗: {e}'
            }
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"處理支付結果異常: {e}")
        return {
            'success': False,
            'message': f'處理支付結果異常: {e}'
        }

# 註冊藍圖
def register_webhook_handlers(app):
    """註冊回調處理器"""
    app.register_blueprint(webhook_bp, url_prefix='/webhook')
    logger.info("支付回調處理器註冊成功")