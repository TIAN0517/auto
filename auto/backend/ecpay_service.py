#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 綠界科技支付服務
ECPay Payment Service for 4D Tech Style Auto Sponsorship System

主要功能:
- 綠界科技API整合
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

class ECPayConfig:
    """綠界科技配置"""
    
    # API配置
    API_VERSION = "1.0"
    BASE_URL = os.environ.get('ECPAY_BASE_URL', 'https://payment-stage.ecpay.com.tw')
    MERCHANT_ID = os.environ.get('ECPAY_MERCHANT_ID', '2000132')
    HASH_KEY = os.environ.get('ECPAY_HASH_KEY', '5294y06JbISpM5x9')
    HASH_IV = os.environ.get('ECPAY_HASH_IV', 'v77hoKGq4kWxNNIS')
    
    # 環境配置
    IS_SANDBOX = os.environ.get('ECPAY_SANDBOX', 'True').lower() == 'true'
    
    # 請求配置
    TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    # 支付配置
    CURRENCY = 'TWD'
    MIN_AMOUNT = 1
    MAX_AMOUNT = 20000
    
    # 支付方式配置
    PAYMENT_METHODS = {
        'credit_card': {
            'code': 'Credit',
            'name': '信用卡',
            'fee_rate': 0.028,
            'min_amount': 1,
            'max_amount': 20000,
            'processing_time': '即時',
            'enabled': True
        },
        'atm': {
            'code': 'ATM',
            'name': 'ATM轉帳',
            'fee_rate': 0.015,
            'min_amount': 10,
            'max_amount': 20000,
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
        'webatm': {
            'code': 'WebATM',
            'name': '網路ATM',
            'fee_rate': 0.020,
            'min_amount': 10,
            'max_amount': 20000,
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

class ECPayService:
    """綠界科技支付服務"""
    
    def __init__(self):
        """初始化綠界科技服務"""
        self.config = ECPayConfig()
        self.session = requests.Session()
        
        # 設置請求頭
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'JY-4D-Tech-Sponsor-System/1.0',
            'Accept': 'text/html'
        })
        
        logger.info(f"綠界科技服務初始化完成 - 環境: {'測試' if self.config.IS_SANDBOX else '正式'}")
    
    def is_available(self) -> bool:
        """檢查服務可用性"""
        try:
            # 綠界沒有健康檢查接口，嘗試訪問主頁
            response = self.session.get(self.config.BASE_URL, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"綠界科技服務不可用: {e}")
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
                'MerchantID': self.config.MERCHANT_ID,
                'MerchantTradeNo': order_id,
                'MerchantTradeDate': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'PaymentType': 'aio',
                'TotalAmount': int(amount),
                'TradeDesc': description[:200],  # 限制描述長度
                'ItemName': description[:400],   # 商品名稱
                'ReturnURL': callback_url,
                'ChoosePayment': method_config['code'],
                'ClientBackURL': return_url,
                'Remark': f"JY-4D-Tech-Sponsor|{customer_info.get('email', '')}",
                'ChooseSubPayment': '',
                'OrderResultURL': return_url,
                'NeedExtraPaidInfo': 'N',
                'DeviceSource': 'P',  # PC版
                'IgnorePayment': '',
                'PlatformID': '',
                'InvoiceMark': 'N',
                'CustomField1': customer_info.get('name', ''),
                'CustomField2': customer_info.get('phone', ''),
                'CustomField3': customer_info.get('email', ''),
                'CustomField4': str(fee)
            }
            
            # 根據支付方式設置特殊參數
            if payment_method == 'atm':
                request_data['ExpireDate'] = 3  # ATM 3天有效期
                request_data['PaymentInfoURL'] = callback_url
            elif payment_method == 'cvs':
                request_data['StoreExpireDate'] = 10080  # 超商代碼7天有效期（分鐘）
                request_data['PaymentInfoURL'] = callback_url
            elif payment_method == 'barcode':
                request_data['StoreExpireDate'] = 10080  # 超商條碼7天有效期（分鐘）
                request_data['PaymentInfoURL'] = callback_url
            
            # 生成檢查碼
            request_data['CheckMacValue'] = self._generate_check_mac_value(request_data)
            
            # 發送請求
            response = self._make_request('POST', '/Cashier/AioCheckOut/V5', request_data)
            
            if 'form' in response.lower() and 'action' in response.lower():
                # 解析HTML表單獲取支付URL
                import re
                action_match = re.search(r'action="([^"]+)"', response)
                payment_url = action_match.group(1) if action_match else None
                
                if payment_url:
                    logger.info(f"綠界科技支付訂單創建成功: {order_id}")
                    
                    return {
                        'success': True,
                        'payment_id': order_id,
                        'payment_url': payment_url,
                        'form_html': response,
                        'expires_at': (datetime.now() + timedelta(days=3)).isoformat(),
                        'callback_data': {
                            'merchant_trade_no': order_id,
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
                # 檢查是否有錯誤信息
                if 'error' in response.lower() or 'fail' in response.lower():
                    logger.error(f"綠界科技支付訂單創建失敗: {order_id} - {response[:200]}")
                    return {
                        'success': False,
                        'message': '創建支付失敗'
                    }
                else:
                    return {
                        'success': False,
                        'message': '未知響應格式'
                    }
                
        except Exception as e:
            logger.error(f"創建綠界科技支付訂單異常: {e}")
            return {
                'success': False,
                'message': '系統錯誤，請稍後重試'
            }
    
    def query_payment_status(self, order_id: str) -> Dict:
        """查詢支付狀態"""
        try:
            request_data = {
                'MerchantID': self.config.MERCHANT_ID,
                'MerchantTradeNo': order_id,
                'TimeStamp': int(time.time())
            }
            
            # 生成檢查碼
            request_data['CheckMacValue'] = self._generate_check_mac_value(request_data)
            
            # 發送請求
            response = self._make_request('POST', '/Cashier/QueryTradeInfo/V5', request_data)
            
            # 解析響應
            if '=' in response and '&' in response:
                # URL編碼格式響應
                from urllib.parse import parse_qs
                parsed_data = parse_qs(response)
                
                trade_status = parsed_data.get('TradeStatus', ['0'])[0]
                
                # 狀態映射
                status_mapping = {
                    '0': 'failed',      # 失敗
                    '1': 'completed',   # 成功
                    '2': 'pending',     # 處理中
                    '10100073': 'pending',  # 等待付款
                    '10200047': 'pending',  # 等待付款
                    '10200095': 'pending'   # 等待付款
                }
                
                mapped_status = status_mapping.get(trade_status, 'pending')
                
                return {
                    'success': True,
                    'status': mapped_status,
                    'amount': float(parsed_data.get('TradeAmt', ['0'])[0]),
                    'paid_at': parsed_data.get('PaymentDate', [None])[0],
                    'transaction_id': parsed_data.get('TradeNo', [None])[0]
                }
            else:
                return {
                    'success': False,
                    'message': '查詢響應格式錯誤'
                }
                
        except Exception as e:
            logger.error(f"查詢綠界科技支付狀態異常: {e}")
            return {
                'success': False,
                'message': '查詢失敗'
            }
    
    def validate_callback(self, callback_data: Dict) -> Dict:
        """驗證支付回調"""
        try:
            # 檢查必要字段
            required_fields = ['MerchantID', 'MerchantTradeNo', 'TradeAmt', 'RtnCode', 'CheckMacValue']
            for field in required_fields:
                if field not in callback_data:
                    return {
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }
            
            # 驗證商戶ID
            if callback_data['MerchantID'] != self.config.MERCHANT_ID:
                return {
                    'success': False,
                    'message': '商戶ID不匹配'
                }
            
            # 驗證檢查碼
            check_mac_value = callback_data.pop('CheckMacValue')
            expected_check_mac_value = self._generate_check_mac_value(callback_data)
            
            if check_mac_value.upper() != expected_check_mac_value.upper():
                return {
                    'success': False,
                    'message': '檢查碼驗證失敗'
                }
            
            # 狀態映射
            rtn_code = callback_data.get('RtnCode', '0')
            if rtn_code == '1':
                status = 'completed'
            elif rtn_code in ['2', '10100073', '10200047', '10200095']:
                status = 'pending'
            else:
                status = 'failed'
            
            logger.info(f"綠界科技回調驗證成功: {callback_data['MerchantTradeNo']} - {status}")
            
            return {
                'success': True,
                'order_id': callback_data['MerchantTradeNo'],
                'status': status,
                'amount': float(callback_data.get('TradeAmt', 0)),
                'transaction_id': callback_data.get('TradeNo'),
                'paid_at': callback_data.get('PaymentDate')
            }
            
        except Exception as e:
            logger.error(f"驗證綠界科技回調異常: {e}")
            return {
                'success': False,
                'message': '回調驗證失敗'
            }
    
    def cancel_payment(self, order_id: str, reason: str = None) -> Dict:
        """取消支付（綠界不支持主動取消）"""
        logger.warning(f"綠界科技不支持主動取消支付: {order_id}")
        return {
            'success': False,
            'message': '綠界科技不支持主動取消支付'
        }
    
    def refund_payment(self, order_id: str, amount: float = None, reason: str = None) -> Dict:
        """退款（需要人工處理）"""
        logger.info(f"綠界科技退款請求: {order_id} - {amount} - {reason}")
        return {
            'success': False,
            'message': '綠界科技退款需要人工處理，請聯繫客服'
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
                logger.warning(f"綠界科技API請求超時 (嘗試 {attempt + 1}/{self.config.MAX_RETRIES})")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
                
            except requests.exceptions.RequestException as e:
                logger.error(f"綠界科技API請求失敗: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
        
        return ''
    
    def _generate_check_mac_value(self, data: Dict) -> str:
        """生成檢查碼"""
        # 移除檢查碼字段
        check_data = {k: v for k, v in data.items() if k != 'CheckMacValue' and v is not None}
        
        # 按鍵名排序（忽略大小寫）
        sorted_items = sorted(check_data.items(), key=lambda x: x[0].lower())
        
        # 構建檢查字符串
        check_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        
        # URL編碼
        check_string = quote_plus(check_string, safe='=&')
        
        # 加上HashKey和HashIV
        check_string = f"HashKey={self.config.HASH_KEY}&{check_string}&HashIV={self.config.HASH_IV}"
        
        # URL編碼
        check_string = quote_plus(check_string, safe='=&')
        
        # 轉小寫
        check_string = check_string.lower()
        
        # 計算SHA256
        return hashlib.sha256(check_string.encode('utf-8')).hexdigest().upper()
    
    def _verify_check_mac_value(self, data: Dict, check_mac_value: str) -> bool:
        """驗證檢查碼"""
        expected_check_mac_value = self._generate_check_mac_value(data)
        return check_mac_value.upper() == expected_check_mac_value.upper()

# 工具函數

def format_ecpay_date(date_obj: datetime) -> str:
    """格式化綠界日期"""
    return date_obj.strftime('%Y/%m/%d %H:%M:%S')

def parse_ecpay_date(date_str: str) -> Optional[datetime]:
    """解析綠界日期"""
    try:
        return datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
    except (ValueError, TypeError):
        return None

def validate_ecpay_order_id(order_id: str) -> bool:
    """驗證訂單ID格式"""
    if not order_id or len(order_id) < 6 or len(order_id) > 20:
        return False
    
    # 只允許字母、數字
    import re
    return bool(re.match(r'^[a-zA-Z0-9]+$', order_id))

def get_ecpay_error_message(error_code: str) -> str:
    """獲取錯誤信息"""
    error_messages = {
        '10100001': '參數錯誤',
        '10100002': '商店代號錯誤',
        '10100003': '檢查碼錯誤',
        '10100004': '金額錯誤',
        '10100005': '訂單編號重複',
        '10100006': '商品名稱錯誤',
        '10100007': '付款方式錯誤',
        '10100008': '商店未啟用',
        '10100009': 'IP限制',
        '10100010': '訂單不存在',
        '10100011': '訂單已付款',
        '10100012': '訂單已取消',
        '10100013': '訂單已過期',
        '10100014': '付款失敗',
        '10100015': '系統維護中'
    }
    
    return error_messages.get(error_code, '未知錯誤')