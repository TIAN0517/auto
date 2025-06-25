#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 速買配回調處理邏輯
SpeedPay Callback Handler for 4D Tech Style Auto Sponsorship System

主要功能:
- 處理速買配支付回調
- 驗證回調數據
- 更新訂單狀態
- 發送通知
"""

import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from dataclasses import dataclass

class CallbackType(Enum):
    """回調類型枚舉"""
    PAYMENT_SUCCESS = 'payment_success'      # 支付成功
    PAYMENT_FAILED = 'payment_failed'        # 支付失敗
    PAYMENT_PENDING = 'payment_pending'      # 支付待處理
    PAYMENT_CANCELLED = 'payment_cancelled'  # 支付取消
    REFUND_SUCCESS = 'refund_success'        # 退款成功
    REFUND_FAILED = 'refund_failed'          # 退款失敗

class CallbackStatus(Enum):
    """回調處理狀態"""
    RECEIVED = 'received'        # 已接收
    PROCESSING = 'processing'    # 處理中
    COMPLETED = 'completed'      # 已完成
    FAILED = 'failed'           # 處理失敗
    IGNORED = 'ignored'         # 已忽略

@dataclass
class CallbackData:
    """回調數據結構"""
    merchant_id: str
    order_id: str
    transaction_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    timestamp: str
    signature: str
    
    # 可選字段
    fee: Optional[float] = None
    bank_code: Optional[str] = None
    card_last4: Optional[str] = None
    card_type: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    reference_id: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'merchant_id': self.merchant_id,
            'order_id': self.order_id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'fee': self.fee,
            'bank_code': self.bank_code,
            'card_last4': self.card_last4,
            'card_type': self.card_type,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'reference_id': self.reference_id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

class SpeedPayCallbackHandler:
    """速買配回調處理器"""
    
    def __init__(self, api_secret: str, logger: logging.Logger = None):
        self.api_secret = api_secret
        self.logger = logger or logging.getLogger(__name__)
        
        # 回調處理記錄
        self.processed_callbacks = set()
        self.callback_history = []
        
        # 配置
        self.max_timestamp_diff = 300  # 5分鐘時間差容忍
        self.max_history_size = 1000
        
    def parse_callback_data(self, raw_data: Dict[str, Any]) -> CallbackData:
        """解析回調數據"""
        try:
            return CallbackData(
                merchant_id=raw_data.get('merchant_id', ''),
                order_id=raw_data.get('order_id', ''),
                transaction_id=raw_data.get('transaction_id', ''),
                amount=float(raw_data.get('amount', 0)),
                currency=raw_data.get('currency', 'TWD'),
                status=raw_data.get('status', ''),
                payment_method=raw_data.get('payment_method', ''),
                timestamp=raw_data.get('timestamp', ''),
                signature=raw_data.get('signature', ''),
                fee=float(raw_data.get('fee', 0)) if raw_data.get('fee') else None,
                bank_code=raw_data.get('bank_code'),
                card_last4=raw_data.get('card_last4'),
                card_type=raw_data.get('card_type'),
                error_code=raw_data.get('error_code'),
                error_message=raw_data.get('error_message'),
                reference_id=raw_data.get('reference_id'),
                user_id=raw_data.get('user_id'),
                ip_address=raw_data.get('ip_address'),
                user_agent=raw_data.get('user_agent')
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"無效的回調數據格式: {str(e)}")
    
    def validate_signature(self, callback_data: CallbackData) -> bool:
        """驗證簽名"""
        try:
            # 構建簽名字符串
            sign_string = self._build_sign_string(callback_data)
            
            # 計算期望的簽名
            expected_signature = self._calculate_signature(sign_string)
            
            # 比較簽名
            return hmac.compare_digest(expected_signature, callback_data.signature)
            
        except Exception as e:
            self.logger.error(f"簽名驗證失敗: {str(e)}")
            return False
    
    def _build_sign_string(self, callback_data: CallbackData) -> str:
        """構建簽名字符串"""
        # 按字母順序排列參數
        params = {
            'merchant_id': callback_data.merchant_id,
            'order_id': callback_data.order_id,
            'transaction_id': callback_data.transaction_id,
            'amount': str(callback_data.amount),
            'currency': callback_data.currency,
            'status': callback_data.status,
            'payment_method': callback_data.payment_method,
            'timestamp': callback_data.timestamp
        }
        
        # 添加可選參數
        if callback_data.fee is not None:
            params['fee'] = str(callback_data.fee)
        if callback_data.bank_code:
            params['bank_code'] = callback_data.bank_code
        if callback_data.error_code:
            params['error_code'] = callback_data.error_code
        
        # 排序並構建字符串
        sorted_params = sorted(params.items())
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        return sign_string
    
    def _calculate_signature(self, sign_string: str) -> str:
        """計算簽名"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
    
    def validate_timestamp(self, timestamp_str: str) -> bool:
        """驗證時間戳"""
        try:
            # 解析時間戳
            callback_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.now()
            
            # 檢查時間差
            time_diff = abs((current_time - callback_time).total_seconds())
            
            return time_diff <= self.max_timestamp_diff
            
        except (ValueError, TypeError):
            return False
    
    def is_duplicate_callback(self, callback_data: CallbackData) -> bool:
        """檢查是否為重複回調"""
        callback_key = f"{callback_data.order_id}_{callback_data.transaction_id}_{callback_data.status}"
        return callback_key in self.processed_callbacks
    
    def mark_callback_processed(self, callback_data: CallbackData):
        """標記回調已處理"""
        callback_key = f"{callback_data.order_id}_{callback_data.transaction_id}_{callback_data.status}"
        self.processed_callbacks.add(callback_key)
        
        # 記錄到歷史
        self.callback_history.append({
            'key': callback_key,
            'timestamp': datetime.now().isoformat(),
            'data': callback_data.to_dict()
        })
        
        # 限制歷史記錄大小
        if len(self.callback_history) > self.max_history_size:
            self.callback_history = self.callback_history[-self.max_history_size:]
    
    def validate_callback(self, raw_data: Dict[str, Any]) -> Tuple[bool, str, Optional[CallbackData]]:
        """驗證回調數據"""
        try:
            # 解析數據
            callback_data = self.parse_callback_data(raw_data)
            
            # 基本字段驗證
            if not callback_data.merchant_id:
                return False, "缺少商戶ID", None
            
            if not callback_data.order_id:
                return False, "缺少訂單ID", None
            
            if not callback_data.transaction_id:
                return False, "缺少交易ID", None
            
            if not callback_data.signature:
                return False, "缺少簽名", None
            
            # 驗證時間戳
            if not self.validate_timestamp(callback_data.timestamp):
                return False, "時間戳無效或過期", None
            
            # 驗證簽名
            if not self.validate_signature(callback_data):
                return False, "簽名驗證失敗", None
            
            # 檢查重複
            if self.is_duplicate_callback(callback_data):
                return False, "重複的回調", None
            
            return True, "驗證成功", callback_data
            
        except Exception as e:
            return False, f"驗證過程中發生錯誤: {str(e)}", None
    
    def determine_callback_type(self, callback_data: CallbackData) -> CallbackType:
        """確定回調類型"""
        status = callback_data.status.lower()
        
        if 'success' in status or 'completed' in status or status == 'paid':
            return CallbackType.PAYMENT_SUCCESS
        elif 'failed' in status or 'error' in status:
            return CallbackType.PAYMENT_FAILED
        elif 'pending' in status or 'processing' in status:
            return CallbackType.PAYMENT_PENDING
        elif 'cancelled' in status or 'canceled' in status:
            return CallbackType.PAYMENT_CANCELLED
        elif 'refund' in status:
            if 'success' in status:
                return CallbackType.REFUND_SUCCESS
            else:
                return CallbackType.REFUND_FAILED
        else:
            return CallbackType.PAYMENT_PENDING  # 默認為待處理
    
    def process_callback(self, raw_data: Dict[str, Any], 
                        order_update_callback=None,
                        notification_callback=None) -> Dict[str, Any]:
        """處理回調"""
        start_time = time.time()
        
        try:
            # 驗證回調
            is_valid, message, callback_data = self.validate_callback(raw_data)
            
            if not is_valid:
                self.logger.warning(f"回調驗證失敗: {message}")
                return {
                    'success': False,
                    'message': message,
                    'processing_time': time.time() - start_time
                }
            
            # 確定回調類型
            callback_type = self.determine_callback_type(callback_data)
            
            # 標記為已處理
            self.mark_callback_processed(callback_data)
            
            # 更新訂單狀態
            if order_update_callback:
                try:
                    order_update_result = order_update_callback(callback_data, callback_type)
                    if not order_update_result.get('success', False):
                        self.logger.error(f"訂單更新失敗: {order_update_result.get('message')}")
                except Exception as e:
                    self.logger.error(f"訂單更新回調執行失敗: {str(e)}")
            
            # 發送通知
            if notification_callback:
                try:
                    notification_callback(callback_data, callback_type)
                except Exception as e:
                    self.logger.error(f"通知回調執行失敗: {str(e)}")
            
            self.logger.info(f"回調處理成功: 訂單 {callback_data.order_id}, 狀態 {callback_data.status}")
            
            return {
                'success': True,
                'message': '回調處理成功',
                'order_id': callback_data.order_id,
                'transaction_id': callback_data.transaction_id,
                'status': callback_data.status,
                'callback_type': callback_type.value,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            self.logger.error(f"回調處理異常: {str(e)}")
            return {
                'success': False,
                'message': f"處理異常: {str(e)}",
                'processing_time': time.time() - start_time
            }
    
    def get_callback_statistics(self) -> Dict[str, Any]:
        """獲取回調統計信息"""
        total_callbacks = len(self.callback_history)
        
        if total_callbacks == 0:
            return {
                'total_callbacks': 0,
                'success_rate': 0,
                'average_processing_time': 0,
                'callback_types': {},
                'recent_callbacks': []
            }
        
        # 統計回調類型
        callback_types = {}
        for record in self.callback_history:
            status = record['data'].get('status', 'unknown')
            callback_types[status] = callback_types.get(status, 0) + 1
        
        # 最近的回調
        recent_callbacks = self.callback_history[-10:] if len(self.callback_history) >= 10 else self.callback_history
        
        return {
            'total_callbacks': total_callbacks,
            'processed_callbacks': len(self.processed_callbacks),
            'callback_types': callback_types,
            'recent_callbacks': recent_callbacks,
            'history_size': len(self.callback_history)
        }
    
    def clear_old_records(self, days: int = 7):
        """清理舊記錄"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 清理歷史記錄
        self.callback_history = [
            record for record in self.callback_history
            if datetime.fromisoformat(record['timestamp']) > cutoff_time
        ]
        
        # 重建處理記錄集合
        self.processed_callbacks = {
            record['key'] for record in self.callback_history
        }
        
        self.logger.info(f"清理了 {days} 天前的回調記錄")

class CallbackResponseBuilder:
    """回調響應構建器"""
    
    @staticmethod
    def success_response(message: str = "OK") -> Dict[str, Any]:
        """成功響應"""
        return {
            'status': 'success',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def error_response(message: str, error_code: str = None) -> Dict[str, Any]:
        """錯誤響應"""
        response = {
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if error_code:
            response['error_code'] = error_code
        
        return response
    
    @staticmethod
    def validation_error_response(errors: List[str]) -> Dict[str, Any]:
        """驗證錯誤響應"""
        return {
            'status': 'validation_error',
            'message': '數據驗證失敗',
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }

# 工具函數

def create_callback_handler(api_secret: str, logger: logging.Logger = None) -> SpeedPayCallbackHandler:
    """創建回調處理器"""
    return SpeedPayCallbackHandler(api_secret, logger)

def validate_callback_ip(request_ip: str, allowed_ips: List[str]) -> bool:
    """驗證回調IP"""
    if not allowed_ips:
        return True  # 如果沒有設置IP白名單，則允許所有IP
    
    return request_ip in allowed_ips

def log_callback_request(logger: logging.Logger, request_data: Dict[str, Any], 
                        request_ip: str = None, user_agent: str = None):
    """記錄回調請求"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'request_data': request_data,
        'request_ip': request_ip,
        'user_agent': user_agent
    }
    
    logger.info(f"收到回調請求: {json.dumps(log_data, ensure_ascii=False)}")