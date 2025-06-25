#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 藍新金流支付服務
Neweb Pay Payment Service for 4D Tech Style Auto Sponsorship System

主要功能:
- 藍新金流API整合
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
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger(__name__)

class NewebPayConfig:
    """藍新金流配置"""
    
    # API配置
    API_VERSION = "2.0"
    BASE_URL = os.environ.get('NEWEBPAY_BASE_URL', 'https://ccore.newebpay.com')
    MERCHANT_ID = os.environ.get('NEWEBPAY_MERCHANT_ID', 'MS350720000')
    HASH_KEY = os.environ.get('NEWEBPAY_HASH_KEY', 'abcdefghijklmnopqrstuvwxyz123456')
    HASH_IV = os.environ.get('NEWEBPAY_HASH_IV', '1234567890123456')
    
    # 環境配置
    IS_SANDBOX = os.environ.get('NEWEBPAY_SANDBOX', 'True').lower() == 'true'
    
    # 請求配置
    TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    # 支付配置
    CURRENCY = 'TWD'
    MIN_AMOUNT = 1
    MAX_AMOUNT = 99999
    
    # 支付方式配置
    PAYMENT_METHODS = {
        'credit_card': {
            'code': 'CREDIT',
            'name': '信用卡',
            'fee_rate': 0.028,
            'min_amount': 1,
            'max_amount': 99999,
            'processing_time': '即時',
            'enabled': True
        },
        'webatm': {
            'code': 'WEBATM',
            'name': '網路ATM',
            'fee_rate': 0.020,
            'min_amount': 10,
            'max_amount': 99999,
            'processing_time': '即時',
            'enabled': True
        },
        'atm': {
            'code': 'VACC',
            'name': 'ATM轉帳',
            'fee_rate': 0.015,
            'min_amount': 10,
            'max_amount': 99999,
            'processing_time': '1-30分鐘',
            'enabled': True
        },
        'cvs': {
            'code': 'CVS',
            'name': '超商代碼',
            'fee_rate': 0.025,
            'min_amount': 30,
            'max_amount': 20000,
            'processing_time': '即時',
            'enabled': True
        },
        'barcode': {
            'code': 'BARCODE',
            'name': '超商條碼',
            'fee_rate': 0.025,
            'min_amount': 20,
            'max_amount': 40000,
            'processing_time': '即時',
            'enabled': True
        },
        'linepay': {
            'code': 'LINEPAY',
            'name': 'LINE Pay',
            'fee_rate': 0.030,
            'min_amount': 1,
            'max_amount': 99999,
            'processing_time': '即時',
            'enabled': True
        },
        'googlepay': {
            'code': 'GOOGLEPAY',
            'name': 'Google Pay',
            'fee_rate': 0.030,
            'min_amount': 1,
            'max_amount': 99999,
            'processing_time': '即時',
            'enabled': True
        },
        'samsungpay': {
            'code': 'SAMSUNGPAY',
            'name': 'Samsung Pay',
            'fee_rate': 0.030,
            'min_amount': 1,
            'max_amount': 99999,
            'processing_time': '即時',
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
        '822': '中國信託'
    }
    
    # 超商代碼
    CVS_CODES = {
        '001': '7-ELEVEN',
        '002': '全家便利商店',
        '003': 'OK便利商店',
        '004': '萊爾富便利商店'
    }

class NewebPayService:
    """藍新金流支付服務"""
    
    def __init__(self):
        """初始化藍新金流服務"""
        self.config = NewebPayConfig()
        self.session = requests.Session()
        
        # 設置請求頭
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'JY-4D-Tech-Sponsor-System/1.0',
            'Accept': 'application/json'
        })
        
        logger.info(f"藍新金流服務初始化完成 - 環境: {'測試' if self.config.IS_SANDBOX else '正式'}")
    
    def is_available(self) -> bool:
        """檢查服務可用性"""
        try:
            # 藍新沒有健康檢查接口，嘗試訪問主頁
            response = self.session.get(self.config.BASE_URL, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"藍新金流服務不可用: {e}")
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
            
            # 構建交易資料
            trade_info = {
                'MerchantID': self.config.MERCHANT_ID,
                'RespondType': 'JSON',
                'TimeStamp': int(time.time()),
                'Version': self.config.API_VERSION,
                'MerchantOrderNo': order_id,
                'Amt': int(amount),
                'ItemDesc': description[:50],  # 限制描述長度
                'ReturnURL': callback_url,
                'NotifyURL': callback_url,
                'ClientBackURL': return_url,
                'Email': customer_info.get('email', ''),
                'LoginType': 0,
                'OrderComment': f"JY-4D-Tech-Sponsor|{customer_info.get('name', '')}",
                'CREDIT': 1 if payment_method == 'credit_card' else 0,
                'WEBATM': 1 if payment_method == 'webatm' else 0,
                'VACC': 1 if payment_method == 'atm' else 0,
                'CVS': 1 if payment_method == 'cvs' else 0,
                'BARCODE': 1 if payment_method == 'barcode' else 0,
                'LINEPAY': 1 if payment_method == 'linepay' else 0,
                'GOOGLEPAY': 1 if payment_method == 'googlepay' else 0,
                'SAMSUNGPAY': 1 if payment_method == 'samsungpay' else 0
            }
            
            # 根據支付方式設置特殊參數
            if payment_method == 'atm':
                trade_info['ExpireDate'] = (datetime.now() + timedelta(days=3)).strftime('%Y%m%d')
            elif payment_method in ['cvs', 'barcode']:
                trade_info['ExpireDate'] = (datetime.now() + timedelta(days=7)).strftime('%Y%m%d')
            
            # 加密交易資料
            encrypted_trade_info = self._encrypt_trade_info(trade_info)
            
            # 構建請求數據
            request_data = {
                'MerchantID': self.config.MERCHANT_ID,
                'TradeInfo': encrypted_trade_info,
                'TradeSha': self._generate_trade_sha(encrypted_trade_info),
                'Version': self.config.API_VERSION
            }
            
            # 發送請求
            response = self._make_request('POST', '/MPG/mpg_gateway', request_data)
            
            if response:
                # 藍新金流返回HTML表單，需要解析
                if 'form' in response.lower() and 'action' in response.lower():
                    import re
                    action_match = re.search(r'action="([^"]+)"', response)
                    payment_url = action_match.group(1) if action_match else None
                    
                    if payment_url:
                        logger.info(f"藍新金流支付訂單創建成功: {order_id}")
                        
                        return {
                            'success': True,
                            'payment_id': order_id,
                            'payment_url': payment_url,
                            'form_html': response,
                            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
                            'callback_data': {
                                'merchant_order_no': order_id,
                                'payment_method': method_config['code']
                            },
                            'message': '支付訂單創建成功'
                        }
                    else:
                        return {
                            'success': False,
                            'message': '無法解析支付URL'
                        }
                else:
                    return {
                        'success': False,
                        'message': '未知響應格式'
                    }
            else:
                return {
                    'success': False,
                    'message': '創建支付失敗'
                }
                
        except Exception as e:
            logger.error(f"創建藍新金流支付訂單異常: {e}")
            return {
                'success': False,
                'message': '系統錯誤，請稍後重試'
            }
    
    def query_payment_status(self, order_id: str) -> Dict:
        """查詢支付狀態"""
        try:
            # 構建查詢資料
            query_data = {
                'MerchantID': self.config.MERCHANT_ID,
                'Version': '1.3',
                'RespondType': 'JSON',
                'CheckValue': self._generate_query_check_value(order_id),
                'TimeStamp': int(time.time()),
                'MerchantOrderNo': order_id,
                'Amt': 1  # 查詢時金額可以是任意值
            }
            
            # 發送請求
            response = self._make_request('POST', '/API/QueryTradeInfo', query_data)
            
            if response:
                try:
                    result = json.loads(response)
                    
                    if result.get('Status') == 'SUCCESS':
                        result_data = result.get('Result', {})
                        
                        # 狀態映射
                        trade_status = result_data.get('TradeStatus')
                        if trade_status == '1':
                            status = 'completed'
                        elif trade_status == '0':
                            status = 'failed'
                        else:
                            status = 'pending'
                        
                        return {
                            'success': True,
                            'status': status,
                            'amount': float(result_data.get('Amt', 0)),
                            'paid_at': result_data.get('PayTime'),
                            'transaction_id': result_data.get('TradeNo')
                        }
                    else:
                        return {
                            'success': False,
                            'message': result.get('Message', '查詢失敗')
                        }
                        
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': '查詢響應格式錯誤'
                    }
            else:
                return {
                    'success': False,
                    'message': '查詢請求失敗'
                }
                
        except Exception as e:
            logger.error(f"查詢藍新金流支付狀態異常: {e}")
            return {
                'success': False,
                'message': '查詢失敗'
            }
    
    def validate_callback(self, callback_data: Dict) -> Dict:
        """驗證支付回調"""
        try:
            # 檢查必要字段
            if 'TradeInfo' not in callback_data or 'TradeSha' not in callback_data:
                return {
                    'success': False,
                    'message': '缺少必要字段'
                }
            
            trade_info = callback_data['TradeInfo']
            trade_sha = callback_data['TradeSha']
            
            # 驗證簽名
            expected_trade_sha = self._generate_trade_sha(trade_info)
            if trade_sha.upper() != expected_trade_sha.upper():
                return {
                    'success': False,
                    'message': '簽名驗證失敗'
                }
            
            # 解密交易資料
            decrypted_data = self._decrypt_trade_info(trade_info)
            
            if not decrypted_data:
                return {
                    'success': False,
                    'message': '解密失敗'
                }
            
            # 解析JSON
            try:
                trade_data = json.loads(decrypted_data)
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'message': '交易資料格式錯誤'
                }
            
            # 驗證商戶ID
            if trade_data.get('MerchantID') != self.config.MERCHANT_ID:
                return {
                    'success': False,
                    'message': '商戶ID不匹配'
                }
            
            # 狀態映射
            status_code = trade_data.get('Status')
            if status_code == 'SUCCESS':
                status = 'completed'
            elif status_code == 'FAIL':
                status = 'failed'
            else:
                status = 'pending'
            
            logger.info(f"藍新金流回調驗證成功: {trade_data.get('MerchantOrderNo')} - {status}")
            
            return {
                'success': True,
                'order_id': trade_data.get('MerchantOrderNo'),
                'status': status,
                'amount': float(trade_data.get('Amt', 0)),
                'transaction_id': trade_data.get('TradeNo'),
                'paid_at': trade_data.get('PayTime')
            }
            
        except Exception as e:
            logger.error(f"驗證藍新金流回調異常: {e}")
            return {
                'success': False,
                'message': '回調驗證失敗'
            }
    
    def cancel_payment(self, order_id: str, reason: str = None) -> Dict:
        """取消支付（藍新不支持主動取消）"""
        logger.warning(f"藍新金流不支持主動取消支付: {order_id}")
        return {
            'success': False,
            'message': '藍新金流不支持主動取消支付'
        }
    
    def refund_payment(self, order_id: str, amount: float = None, reason: str = None) -> Dict:
        """退款（需要人工處理）"""
        logger.info(f"藍新金流退款請求: {order_id} - {amount} - {reason}")
        return {
            'success': False,
            'message': '藍新金流退款需要人工處理，請聯繫客服'
        }
    
    def get_payment_methods_info(self) -> Dict:
        """獲取支付方式詳細信息"""
        return {
            'success': True,
            'methods': list(self.config.PAYMENT_METHODS.values()),
            'banks': self.config.BANK_CODES,
            'cvs': self.config.CVS_CODES
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> str:
        """發送HTTP請求"""
        url = f"{self.config.BASE_URL}{endpoint}"
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=data, timeout=self.config.TIMEOUT)
                else:
                    response = self.session.post(url, data=data, timeout=self.config.TIMEOUT)
                
                response.raise_for_status()
                return response.text
                    
            except requests.exceptions.Timeout:
                logger.warning(f"藍新金流API請求超時 (嘗試 {attempt + 1}/{self.config.MAX_RETRIES})")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
                
            except requests.exceptions.RequestException as e:
                logger.error(f"藍新金流API請求失敗: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
        
        return ''
    
    def _encrypt_trade_info(self, trade_info: Dict) -> str:
        """加密交易資料"""
        try:
            # 轉換為查詢字符串
            query_string = urlencode(trade_info)
            
            # AES加密
            key = self.config.HASH_KEY.encode('utf-8')
            iv = self.config.HASH_IV.encode('utf-8')
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = pad(query_string.encode('utf-8'), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Base64編碼
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"加密交易資料失敗: {e}")
            return ''
    
    def _decrypt_trade_info(self, encrypted_data: str) -> str:
        """解密交易資料"""
        try:
            # Base64解碼
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # AES解密
            key = self.config.HASH_KEY.encode('utf-8')
            iv = self.config.HASH_IV.encode('utf-8')
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(encrypted_bytes)
            
            # 移除填充
            unpadded_data = unpad(decrypted_data, AES.block_size)
            
            return unpadded_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"解密交易資料失敗: {e}")
            return ''
    
    def _generate_trade_sha(self, trade_info: str) -> str:
        """生成交易簽名"""
        sha_string = f"HashKey={self.config.HASH_KEY}&{trade_info}&HashIV={self.config.HASH_IV}"
        return hashlib.sha256(sha_string.encode('utf-8')).hexdigest().upper()
    
    def _generate_query_check_value(self, order_id: str) -> str:
        """生成查詢檢查值"""
        check_string = f"IV={self.config.HASH_IV}&Amt=1&MerchantID={self.config.MERCHANT_ID}&MerchantOrderNo={order_id}&Key={self.config.HASH_KEY}"
        return hashlib.sha256(check_string.encode('utf-8')).hexdigest().upper()

# 工具函數

def format_newebpay_date(date_obj: datetime) -> str:
    """格式化藍新日期"""
    return date_obj.strftime('%Y%m%d')

def parse_newebpay_date(date_str: str) -> Optional[datetime]:
    """解析藍新日期"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None

def validate_newebpay_order_id(order_id: str) -> bool:
    """驗證訂單ID格式"""
    if not order_id or len(order_id) < 6 or len(order_id) > 30:
        return False
    
    # 只允許字母、數字、底線
    import re
    return bool(re.match(r'^[a-zA-Z0-9_]+$', order_id))

def get_newebpay_error_message(error_code: str) -> str:
    """獲取錯誤信息"""
    error_messages = {
        'TRA10001': '參數錯誤',
        'TRA10002': '商店代號錯誤',
        'TRA10003': '檢查碼錯誤',
        'TRA10004': '金額錯誤',
        'TRA10005': '訂單編號重複',
        'TRA10006': '商品名稱錯誤',
        'TRA10007': '付款方式錯誤',
        'TRA10008': '商店未啟用',
        'TRA10009': 'IP限制',
        'TRA10010': '訂單不存在',
        'TRA10011': '訂單已付款',
        'TRA10012': '訂單已取消',
        'TRA10013': '訂單已過期',
        'TRA10014': '付款失敗',
        'TRA10015': '系統維護中'
    }
    
    return error_messages.get(error_code, '未知錯誤')