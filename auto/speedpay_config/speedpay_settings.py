#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 速買配專用設置
SpeedPay Configuration for 4D Tech Style Auto Sponsorship System

主要功能:
- 速買配API配置
- 支付參數設置
- 環境配置管理
- 安全設置
"""

import os
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

class SpeedPayEnvironment(Enum):
    """速買配環境枚舉"""
    SANDBOX = 'sandbox'      # 測試環境
    PRODUCTION = 'production'  # 正式環境

class SpeedPayPaymentType(Enum):
    """速買配支付類型"""
    CREDIT_CARD = 'credit_card'        # 信用卡
    ATM = 'atm'                       # ATM轉帳
    CONVENIENCE_STORE = 'cvs'          # 超商代碼
    VIRTUAL_ACCOUNT = 'virtual_account' # 虛擬帳號
    MOBILE_PAYMENT = 'mobile_payment'   # 行動支付
    BANK_TRANSFER = 'bank_transfer'     # 銀行轉帳

@dataclass
class SpeedPayAPIConfig:
    """速買配API配置"""
    merchant_id: str
    api_key: str
    api_secret: str
    environment: str = SpeedPayEnvironment.SANDBOX.value
    api_version: str = 'v1'
    timeout: int = 30
    max_retries: int = 3
    
    # API端點
    base_url: str = None
    payment_url: str = None
    query_url: str = None
    callback_url: str = None
    return_url: str = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.base_url is None:
            if self.environment == SpeedPayEnvironment.PRODUCTION.value:
                self.base_url = 'https://api.speedpay.com.tw'
            else:
                self.base_url = 'https://sandbox-api.speedpay.com.tw'
        
        # 設置API端點
        if self.payment_url is None:
            self.payment_url = f"{self.base_url}/{self.api_version}/payment"
        
        if self.query_url is None:
            self.query_url = f"{self.base_url}/{self.api_version}/query"
    
    def get_headers(self) -> Dict[str, str]:
        """獲取API請求標頭"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': self.api_key,
            'X-Merchant-ID': self.merchant_id,
            'User-Agent': 'SpeedPay-4D-AutoSponsor/1.0'
        }

class SpeedPaySettings:
    """速買配設置管理器"""
    
    def __init__(self):
        self._load_settings()
    
    def _load_settings(self):
        """載入設置"""
        # 從環境變數載入
        self.api_config = SpeedPayAPIConfig(
            merchant_id=os.getenv('SPEEDPAY_MERCHANT_ID', 'TEST_MERCHANT'),
            api_key=os.getenv('SPEEDPAY_API_KEY', 'test_api_key'),
            api_secret=os.getenv('SPEEDPAY_API_SECRET', 'test_api_secret'),
            environment=os.getenv('SPEEDPAY_ENVIRONMENT', SpeedPayEnvironment.SANDBOX.value),
            callback_url=os.getenv('SPEEDPAY_CALLBACK_URL', 'http://localhost:8080/api/payment/speedpay/callback'),
            return_url=os.getenv('SPEEDPAY_RETURN_URL', 'http://localhost:8080/payment/success')
        )
        
        # 支付方式配置
        self.payment_methods = {
            SpeedPayPaymentType.CREDIT_CARD.value: {
                'enabled': True,
                'name': '信用卡',
                'description': '支援VISA、MasterCard、JCB等信用卡',
                'fee_rate': 0.028,  # 2.8%手續費
                'min_amount': 1,
                'max_amount': 100000,
                'processing_time': '即時',
                'icon': 'credit-card'
            },
            SpeedPayPaymentType.ATM.value: {
                'enabled': True,
                'name': 'ATM轉帳',
                'description': '透過ATM進行轉帳付款',
                'fee_rate': 0.015,  # 1.5%手續費
                'min_amount': 10,
                'max_amount': 50000,
                'processing_time': '1-3個工作天',
                'icon': 'atm'
            },
            SpeedPayPaymentType.CONVENIENCE_STORE.value: {
                'enabled': True,
                'name': '超商代碼',
                'description': '7-11、全家、萊爾富、OK超商代碼繳費',
                'fee_rate': 0.02,   # 2%手續費
                'min_amount': 30,
                'max_amount': 20000,
                'processing_time': '即時',
                'icon': 'store'
            },
            SpeedPayPaymentType.VIRTUAL_ACCOUNT.value: {
                'enabled': True,
                'name': '虛擬帳號',
                'description': '銀行虛擬帳號轉帳',
                'fee_rate': 0.01,   # 1%手續費
                'min_amount': 1,
                'max_amount': 200000,
                'processing_time': '即時',
                'icon': 'bank'
            },
            SpeedPayPaymentType.MOBILE_PAYMENT.value: {
                'enabled': True,
                'name': '行動支付',
                'description': 'LINE Pay、街口支付、Apple Pay等',
                'fee_rate': 0.025,  # 2.5%手續費
                'min_amount': 1,
                'max_amount': 50000,
                'processing_time': '即時',
                'icon': 'mobile'
            }
        }
        
        # 安全設置
        self.security_settings = {
            'signature_algorithm': 'SHA256',
            'encryption_algorithm': 'AES-256-CBC',
            'token_expiry': 3600,  # 1小時
            'max_payment_attempts': 3,
            'ip_whitelist': [],
            'require_https': True,
            'validate_callback_ip': True
        }
        
        # 業務設置
        self.business_settings = {
            'default_currency': 'TWD',
            'supported_currencies': ['TWD'],
            'order_expiry_minutes': 30,
            'auto_capture': True,
            'enable_refund': True,
            'enable_partial_refund': True,
            'max_refund_days': 180,
            'notification_retry_times': 5,
            'notification_retry_interval': 300  # 5分鐘
        }
        
        # 日誌設置
        self.logging_settings = {
            'log_level': 'INFO',
            'log_requests': True,
            'log_responses': True,
            'log_sensitive_data': False,
            'log_file_path': 'logs/speedpay.log',
            'max_log_size': 10485760,  # 10MB
            'backup_count': 5
        }
        
        # 監控設置
        self.monitoring_settings = {
            'enable_health_check': True,
            'health_check_interval': 300,  # 5分鐘
            'alert_on_failure': True,
            'alert_email': os.getenv('SPEEDPAY_ALERT_EMAIL', ''),
            'performance_tracking': True,
            'error_rate_threshold': 0.05  # 5%錯誤率閾值
        }
    
    def get_payment_method_config(self, payment_type: str) -> Optional[Dict[str, Any]]:
        """獲取支付方式配置"""
        return self.payment_methods.get(payment_type)
    
    def get_enabled_payment_methods(self) -> List[Dict[str, Any]]:
        """獲取啟用的支付方式"""
        enabled_methods = []
        for method_type, config in self.payment_methods.items():
            if config.get('enabled', False):
                enabled_methods.append({
                    'type': method_type,
                    **config
                })
        return enabled_methods
    
    def calculate_fee(self, amount: float, payment_type: str) -> float:
        """計算手續費"""
        method_config = self.get_payment_method_config(payment_type)
        if not method_config:
            return 0
        
        fee_rate = method_config.get('fee_rate', 0)
        return round(amount * fee_rate, 0)
    
    def validate_amount(self, amount: float, payment_type: str) -> Dict[str, Any]:
        """驗證金額"""
        method_config = self.get_payment_method_config(payment_type)
        if not method_config:
            return {
                'valid': False,
                'error': '不支援的支付方式'
            }
        
        min_amount = method_config.get('min_amount', 0)
        max_amount = method_config.get('max_amount', float('inf'))
        
        if amount < min_amount:
            return {
                'valid': False,
                'error': f'金額不能少於 NT$ {min_amount}'
            }
        
        if amount > max_amount:
            return {
                'valid': False,
                'error': f'金額不能超過 NT$ {max_amount:,}'
            }
        
        return {'valid': True}
    
    def is_production(self) -> bool:
        """檢查是否為正式環境"""
        return self.api_config.environment == SpeedPayEnvironment.PRODUCTION.value
    
    def get_callback_url(self, order_id: str = None) -> str:
        """獲取回調URL"""
        base_url = self.api_config.callback_url
        if order_id:
            return f"{base_url}?order_id={order_id}"
        return base_url
    
    def get_return_url(self, order_id: str = None, status: str = None) -> str:
        """獲取返回URL"""
        base_url = self.api_config.return_url
        params = []
        
        if order_id:
            params.append(f"order_id={order_id}")
        
        if status:
            params.append(f"status={status}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        
        return base_url
    
    def update_setting(self, category: str, key: str, value: Any) -> bool:
        """更新設置"""
        try:
            if category == 'api':
                setattr(self.api_config, key, value)
            elif category == 'payment_methods':
                if key in self.payment_methods:
                    self.payment_methods[key].update(value)
            elif category == 'security':
                self.security_settings[key] = value
            elif category == 'business':
                self.business_settings[key] = value
            elif category == 'logging':
                self.logging_settings[key] = value
            elif category == 'monitoring':
                self.monitoring_settings[key] = value
            else:
                return False
            
            return True
        except Exception:
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """匯出配置"""
        return {
            'api_config': {
                'merchant_id': self.api_config.merchant_id,
                'environment': self.api_config.environment,
                'api_version': self.api_config.api_version,
                'timeout': self.api_config.timeout,
                'max_retries': self.api_config.max_retries,
                'base_url': self.api_config.base_url
            },
            'payment_methods': self.payment_methods,
            'security_settings': self.security_settings,
            'business_settings': self.business_settings,
            'logging_settings': self.logging_settings,
            'monitoring_settings': self.monitoring_settings
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """驗證配置"""
        errors = []
        warnings = []
        
        # 驗證API配置
        if not self.api_config.merchant_id:
            errors.append('商戶ID不能為空')
        
        if not self.api_config.api_key:
            errors.append('API Key不能為空')
        
        if not self.api_config.api_secret:
            errors.append('API Secret不能為空')
        
        # 驗證回調URL
        if not self.api_config.callback_url:
            errors.append('回調URL不能為空')
        elif not self.api_config.callback_url.startswith('http'):
            errors.append('回調URL必須是有效的HTTP(S)地址')
        
        # 檢查生產環境設置
        if self.is_production():
            if 'test' in self.api_config.merchant_id.lower():
                warnings.append('生產環境使用測試商戶ID')
            
            if not self.api_config.callback_url.startswith('https'):
                warnings.append('生產環境建議使用HTTPS回調URL')
        
        # 檢查支付方式
        enabled_methods = self.get_enabled_payment_methods()
        if not enabled_methods:
            errors.append('至少需要啟用一種支付方式')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

# 全域設置實例
speedpay_settings = SpeedPaySettings()

# 便捷函數
def get_speedpay_config() -> SpeedPayAPIConfig:
    """獲取速買配API配置"""
    return speedpay_settings.api_config

def get_payment_methods() -> List[Dict[str, Any]]:
    """獲取支付方式列表"""
    return speedpay_settings.get_enabled_payment_methods()

def calculate_payment_fee(amount: float, payment_type: str) -> float:
    """計算支付手續費"""
    return speedpay_settings.calculate_fee(amount, payment_type)

def validate_payment_amount(amount: float, payment_type: str) -> Dict[str, Any]:
    """驗證支付金額"""
    return speedpay_settings.validate_amount(amount, payment_type)

def is_production_environment() -> bool:
    """檢查是否為生產環境"""
    return speedpay_settings.is_production()