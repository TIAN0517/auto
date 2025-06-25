#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 速買配支付服務
SpeedPay Payment Service for 4D Tech Style Auto Sponsorship System

主要功能:
- 速買配API整合
- 支付訂單創建
- 支付狀態查詢
- 回調驗證
- 錯誤處理
"""

import os
import json
import time
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode, quote_plus
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class SpeedPayConfig:
    """速買配配置"""
    
    # API配置
    API_VERSION = "1.0"
    BASE_URL = os.environ.get('SPEEDPAY_BASE_URL', 'https://api.speedpay.com.tw')
    MERCHANT_ID = os.environ.get('SPEEDPAY_MERCHANT_ID', 'TEST_MERCHANT')
    API_KEY = os.environ.get('SPEEDPAY_API_KEY', 'TEST_API_KEY')
    SECRET_KEY = os.environ.get('SPEEDPAY_SECRET_KEY', 'TEST_SECRET_KEY')
    
    # 環境配置
    IS_SANDBOX = os.environ.get('SPEEDPAY_SANDBOX', 'True').lower() == 'true'
    
    # 請求配置
    TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    # 支付配置
    CURRENCY = 'TWD'
    MIN_AMOUNT = 10
    MAX_AMOUNT = 50000
    
    # 支付方式配置
    PAYMENT_METHODS = {
        'credit_card': {
            'code': 'CC',
            'name': '信用卡',
            'fee_rate': 0.025,
            'min_amount': 10,
            'max_amount': 50000,
            'processing_time': '即時',
            'enabled': True
        },
        'atm': {
            'code': 'ATM',
            'name': 'ATM轉帳',
            'fee_rate': 0.015,
            'min_amount': 10,
            'max_amount': 50000,
            'processing_time': '1-30分鐘',
            'enabled': True
        },
        'cvs': {
            'code': 'CVS',
            'name': '超商代碼',
            'fee_rate': 0.020,
            'min_amount': 10,
            'max_amount': 20000,
            'processing_time': '即時',
            'enabled': True
        },
        'bank_transfer': {
            'code': 'BANK',
            'name': '銀行轉帳',
            'fee_rate': 0.010,
            'min_amount': 100,
            'max_amount': 50000,
            'processing_time': '1-60分鐘',
            'enabled': True
        }
    }
    
    # 銀行代碼
    BANK_CODES = {
        '004': '台灣銀行',
        '005': '土地銀行',
        '006': '合作金庫',
        '007': '第一銀行',
        '008': '華南銀行',
        '009': '彰化銀行',
        '011': '上海銀行',
        '012': '台北富邦',
        '013': '國泰世華',
        '017': '兆豐銀行',
        '021': '花旗銀行',
        '050': '台灣企銀',
        '052': '渣打銀行',
        '103': '台新銀行',
        '108': '陽信銀行',
        '147': '三信銀行',
        '803': '聯邦銀行',
        '805': '遠東銀行',
        '806': '元大銀行',
        '807': '永豐銀行',
        '808': '玉山銀行',
        '809': '凱基銀行',
        '812': '台中銀行',
        '816': '安泰銀行',
        '822': '中國信託'
    }

class SpeedPayService:
    """速買配支付服務"""
    
    def __init__(self):
        """初始化速買配服務"""
        self.config = SpeedPayConfig()
        self.session = requests.Session()
        
        # 設置請求頭
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'JY-4D-Tech-Sponsor-System/1.0',
            'Accept': 'application/json'
        })
        
        logger.info(f"速買配服務初始化完成 - 環境: {'沙盒' if self.config.IS_SANDBOX else '正式'}")
    
    def is_available(self) -> bool:
        """檢查服務可用性"""
        try:
            response = self._make_request('GET', '/api/v1/health')
            return response.get('status') == 'ok'
        except Exception as e:
            logger.warning(f"速買配服務不可用: {e}")
            return False
    
    def get_supported_payment_methods(self, amount: float = None) -> List[Dict]:
        """獲取支援的支付方式"""
        methods = []
        
        for method_id, config in self.config.PAYMENT_METHODS.items():
            if not config['enabled']:
                continue
            
            # 檢查金額限制
            if amount:
                if amount < config['min_amount'] or amount > config['max_amount']:
                    continue
            
            methods.append({
                'id': method_id,
                'code': config['code'],
                'name': config['name'],
                'fee_rate': config['fee_rate'],
                'min_amount': config['min_amount'],
                'max_amount': config['max_amount'],
                'processing_time': config['processing_time']
            })
        
        return methods
    
    def calculate_fee(self, amount: float, payment_method: str) -> float:
        """計算手續費"""
        if payment_method not in self.config.PAYMENT_METHODS:
            return 0
        
        fee_rate = self.config.PAYMENT_METHODS[payment_method]['fee_rate']
        fee = amount * fee_rate
        
        # 四捨五入到分
        return float(Decimal(str(fee)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def create_payment(self, 
                      order_id: str,
                      amount: float,
                      description: str,
                      customer_info: Dict,
                      callback_url: str,
                      return_url: str,
                      payment_method: str = 'credit_card') -> Dict:
        """創建支付訂單"""
        try:
            # 驗證參數
            if not order_id or not amount or amount <= 0:
                return {
                    'success': False,
                    'message': '訂單ID和金額是必要參數'
                }
            
            # 檢查支付方式
            if payment_method not in self.config.PAYMENT_METHODS:
                return {
                    'success': False,
                    'message': '不支援的支付方式'
                }
            
            method_config = self.config.PAYMENT_METHODS[payment_method]
            
            # 檢查金額限制
            if amount < method_config['min_amount']:
                return {
                    'success': False,
                    'message': f'支付金額不能少於 {method_config["min_amount"]} 元'
                }
            
            if amount > method_config['max_amount']:
                return {
                    'success': False,
                    'message': f'支付金額不能超過 {method_config["max_amount"]} 元'
                }
            
            # 計算手續費
            fee = self.calculate_fee(amount, payment_method)
            
            # 構建請求數據
            request_data = {
                'merchant_id': self.config.MERCHANT_ID,
                'order_id': order_id,
                'amount': int(amount),
                'currency': self.config.CURRENCY,
                'payment_method': method_config['code'],
                'description': description[:100],  # 限制描述長度
                'callback_url': callback_url,
                'return_url': return_url,
                'timestamp': int(time.time()),
                'customer': {
                    'name': customer_info.get('name', ''),
                    'email': customer_info.get('email', ''),
                    'phone': customer_info.get('phone', '')
                },
                'extra': {
                    'fee': fee,
                    'system': 'JY-4D-Tech-Sponsor'
                }
            }
            
            # 生成簽名
            request_data['signature'] = self._generate_signature(request_data)
            
            # 發送請求
            response = self._make_request('POST', '/api/v1/payments/create', request_data)
            
            if response.get('success'):
                logger.info(f"速買配支付訂單創建成功: {order_id}")
                
                return {
                    'success': True,
                    'payment_id': response.get('payment_id'),
                    'payment_url': response.get('payment_url'),
                    'qr_code': response.get('qr_code'),
                    'expires_at': response.get('expires_at'),
                    'callback_data': {
                        'payment_id': response.get('payment_id'),
                        'merchant_order_id': order_id
                    },
                    'message': '支付訂單創建成功'
                }
            else:
                error_msg = response.get('message', '創建支付失敗')
                logger.error(f"速買配支付訂單創建失敗: {order_id} - {error_msg}")
                
                return {
                    'success': False,
                    'message': error_msg
                }
                
        except Exception as e:
            logger.error(f"創建速買配支付訂單異常: {e}")
            return {
                'success': False,
                'message': '系統錯誤，請稍後重試'
            }
    
    def query_payment_status(self, order_id: str) -> Dict:
        """查詢支付狀態"""
        try:
            request_data = {
                'merchant_id': self.config.MERCHANT_ID,
                'order_id': order_id,
                'timestamp': int(time.time())
            }
            
            # 生成簽名
            request_data['signature'] = self._generate_signature(request_data)
            
            # 發送請求
            response = self._make_request('POST', '/api/v1/payments/query', request_data)
            
            if response.get('success'):
                status_mapping = {
                    'pending': 'pending',
                    'processing': 'processing',
                    'success': 'completed',
                    'failed': 'failed',
                    'cancelled': 'cancelled',
                    'expired': 'expired'
                }
                
                speedpay_status = response.get('status', 'pending')
                mapped_status = status_mapping.get(speedpay_status, 'pending')
                
                return {
                    'success': True,
                    'status': mapped_status,
                    'amount': response.get('amount'),
                    'fee': response.get('fee'),
                    'paid_at': response.get('paid_at'),
                    'transaction_id': response.get('transaction_id')
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', '查詢失敗')
                }
                
        except Exception as e:
            logger.error(f"查詢速買配支付狀態異常: {e}")
            return {
                'success': False,
                'message': '查詢失敗'
            }
    
    def validate_callback(self, callback_data: Dict) -> Dict:
        """驗證支付回調"""
        try:
            # 檢查必要字段
            required_fields = ['merchant_id', 'order_id', 'amount', 'status', 'signature']
            for field in required_fields:
                if field not in callback_data:
                    return {
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }
            
            # 驗證商戶ID
            if callback_data['merchant_id'] != self.config.MERCHANT_ID:
                return {
                    'success': False,
                    'message': '商戶ID不匹配'
                }
            
            # 驗證簽名
            signature = callback_data.pop('signature')
            expected_signature = self._generate_signature(callback_data)
            
            if signature != expected_signature:
                return {
                    'success': False,
                    'message': '簽名驗證失敗'
                }
            
            # 狀態映射
            status_mapping = {
                'success': 'completed',
                'failed': 'failed',
                'cancelled': 'cancelled',
                'expired': 'expired'
            }
            
            speedpay_status = callback_data.get('status', 'failed')
            mapped_status = status_mapping.get(speedpay_status, 'failed')
            
            logger.info(f"速買配回調驗證成功: {callback_data['order_id']} - {mapped_status}")
            
            return {
                'success': True,
                'order_id': callback_data['order_id'],
                'status': mapped_status,
                'amount': float(callback_data.get('amount', 0)),
                'fee': float(callback_data.get('fee', 0)),
                'transaction_id': callback_data.get('transaction_id'),
                'paid_at': callback_data.get('paid_at')
            }
            
        except Exception as e:
            logger.error(f"驗證速買配回調異常: {e}")
            return {
                'success': False,
                'message': '回調驗證失敗'
            }
    
    def cancel_payment(self, order_id: str, reason: str = None) -> Dict:
        """取消支付"""
        try:
            request_data = {
                'merchant_id': self.config.MERCHANT_ID,
                'order_id': order_id,
                'reason': reason or '用戶取消',
                'timestamp': int(time.time())
            }
            
            # 生成簽名
            request_data['signature'] = self._generate_signature(request_data)
            
            # 發送請求
            response = self._make_request('POST', '/api/v1/payments/cancel', request_data)
            
            if response.get('success'):
                logger.info(f"速買配支付取消成功: {order_id}")
                return {
                    'success': True,
                    'message': '支付已取消'
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', '取消失敗')
                }
                
        except Exception as e:
            logger.error(f"取消速買配支付異常: {e}")
            return {
                'success': False,
                'message': '取消失敗'
            }
    
    def refund_payment(self, order_id: str, amount: float = None, reason: str = None) -> Dict:
        """退款"""
        try:
            request_data = {
                'merchant_id': self.config.MERCHANT_ID,
                'order_id': order_id,
                'refund_amount': int(amount) if amount else None,
                'reason': reason or '商戶退款',
                'timestamp': int(time.time())
            }
            
            # 生成簽名
            request_data['signature'] = self._generate_signature(request_data)
            
            # 發送請求
            response = self._make_request('POST', '/api/v1/payments/refund', request_data)
            
            if response.get('success'):
                logger.info(f"速買配退款成功: {order_id}")
                return {
                    'success': True,
                    'refund_id': response.get('refund_id'),
                    'refund_amount': response.get('refund_amount'),
                    'message': '退款成功'
                }
            else:
                return {
                    'success': False,
                    'message': response.get('message', '退款失敗')
                }
                
        except Exception as e:
            logger.error(f"速買配退款異常: {e}")
            return {
                'success': False,
                'message': '退款失敗'
            }
    
    def get_payment_methods_info(self) -> Dict:
        """獲取支付方式詳細信息"""
        try:
            response = self._make_request('GET', '/api/v1/payment-methods')
            
            if response.get('success'):
                return {
                    'success': True,
                    'methods': response.get('methods', []),
                    'banks': self.config.BANK_CODES
                }
            else:
                # 返回本地配置
                return {
                    'success': True,
                    'methods': list(self.config.PAYMENT_METHODS.values()),
                    'banks': self.config.BANK_CODES
                }
                
        except Exception as e:
            logger.warning(f"獲取速買配支付方式信息失敗: {e}")
            # 返回本地配置
            return {
                'success': True,
                'methods': list(self.config.PAYMENT_METHODS.values()),
                'banks': self.config.BANK_CODES
            }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """發送HTTP請求"""
        url = f"{self.config.BASE_URL}{endpoint}"
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=data, timeout=self.config.TIMEOUT)
                else:
                    response = self.session.post(url, json=data, timeout=self.config.TIMEOUT)
                
                response.raise_for_status()
                
                # 嘗試解析JSON
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': '響應格式錯誤'
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning(f"速買配API請求超時 (嘗試 {attempt + 1}/{self.config.MAX_RETRIES})")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
                
            except requests.exceptions.RequestException as e:
                logger.error(f"速買配API請求失敗: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
        
        return {
            'success': False,
            'message': '請求失敗'
        }
    
    def _generate_signature(self, data: Dict) -> str:
        """生成API簽名"""
        # 移除簽名字段
        sign_data = {k: v for k, v in data.items() if k != 'signature' and v is not None}
        
        # 按鍵名排序
        sorted_items = sorted(sign_data.items())
        
        # 構建簽名字符串
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        sign_string += f"&key={self.config.SECRET_KEY}"
        
        # 計算SHA256
        return hashlib.sha256(sign_string.encode('utf-8')).hexdigest().upper()
    
    def _verify_signature(self, data: Dict, signature: str) -> bool:
        """驗證簽名"""
        expected_signature = self._generate_signature(data)
        return signature.upper() == expected_signature

# 工具函數

def format_speedpay_amount(amount: float) -> int:
    """格式化速買配金額（轉為分）"""
    return int(amount * 100)

def parse_speedpay_amount(amount: int) -> float:
    """解析速買配金額（分轉為元）"""
    return float(amount) / 100

def validate_speedpay_order_id(order_id: str) -> bool:
    """驗證訂單ID格式"""
    if not order_id or len(order_id) < 6 or len(order_id) > 50:
        return False
    
    # 只允許字母、數字、下劃線、連字符
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', order_id))

def get_speedpay_error_message(error_code: str) -> str:
    """獲取錯誤信息"""
    error_messages = {
        'INVALID_MERCHANT': '無效的商戶ID',
        'INVALID_SIGNATURE': '簽名驗證失敗',
        'INVALID_AMOUNT': '金額格式錯誤',
        'AMOUNT_TOO_SMALL': '金額過小',
        'AMOUNT_TOO_LARGE': '金額過大',
        'INVALID_ORDER_ID': '訂單ID格式錯誤',
        'DUPLICATE_ORDER': '重複的訂單',
        'ORDER_NOT_FOUND': '訂單不存在',
        'ORDER_EXPIRED': '訂單已過期',
        'PAYMENT_FAILED': '支付失敗',
        'INSUFFICIENT_BALANCE': '餘額不足',
        'BANK_ERROR': '銀行系統錯誤',
        'NETWORK_ERROR': '網絡錯誤',
        'SYSTEM_MAINTENANCE': '系統維護中'
    }
    
    return error_messages.get(error_code, '未知錯誤')