#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 支付模型
Payment Model for 4D Tech Style Auto Sponsorship System

主要功能:
- 支付訂單數據模型
- 支付方式管理
- 訂單狀態追蹤
- 數據驗證
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

class PaymentStatus(Enum):
    """支付狀態枚舉"""
    PENDING = 'pending'          # 待支付
    PROCESSING = 'processing'    # 處理中
    COMPLETED = 'completed'      # 已完成
    FAILED = 'failed'           # 失敗
    CANCELLED = 'cancelled'      # 已取消
    REFUNDED = 'refunded'       # 已退款
    EXPIRED = 'expired'         # 已過期

class PaymentMethod(Enum):
    """支付方式枚舉"""
    SPEEDPAY = 'speedpay'       # 速買配
    ECPAY = 'ecpay'            # 綠界科技
    NEWEBPAY = 'newebpay'      # 藍新金流

class SponsorPackage(Enum):
    """贊助套餐枚舉"""
    BASIC = 'basic'            # 基礎套餐
    ADVANCED = 'advanced'      # 進階套餐
    VIP = 'vip'               # VIP套餐
    SUPREME = 'supreme'        # 至尊套餐
    CUSTOM = 'custom'          # 自定義金額

class PaymentOrder:
    """支付訂單模型"""
    
    def __init__(self, 
                 order_id: str = None,
                 user_id: int = None,
                 amount: float = 0,
                 package_type: str = None,
                 payment_method: str = None,
                 status: str = PaymentStatus.PENDING.value,
                 description: str = None,
                 customer_info: Dict = None,
                 callback_url: str = None,
                 return_url: str = None,
                 expires_at: datetime = None,
                 created_at: datetime = None,
                 updated_at: datetime = None,
                 **kwargs):
        
        self.id = kwargs.get('id')
        self.order_id = order_id or self._generate_order_id()
        self.user_id = user_id
        self.amount = float(amount) if amount else 0
        self.package_type = package_type
        self.payment_method = payment_method
        self.status = status
        self.description = description or ''
        self.customer_info = customer_info or {}
        self.callback_url = callback_url
        self.return_url = return_url
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24))
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # 支付相關信息
        self.payment_id = kwargs.get('payment_id')
        self.payment_url = kwargs.get('payment_url')
        self.transaction_id = kwargs.get('transaction_id')
        self.paid_at = kwargs.get('paid_at')
        self.fee = kwargs.get('fee', 0)
        
        # 額外信息
        self.discount_code = kwargs.get('discount_code')
        self.discount_amount = kwargs.get('discount_amount', 0)
        self.original_amount = kwargs.get('original_amount', self.amount)
        self.notes = kwargs.get('notes', '')
        self.metadata = kwargs.get('metadata', {})
    
    def _generate_order_id(self) -> str:
        """生成訂單ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"JY{timestamp}{random_part}"
    
    def validate(self) -> Dict[str, Any]:
        """驗證訂單數據"""
        errors = []
        
        # 驗證必要字段
        if not self.user_id:
            errors.append('用戶ID是必要的')
        
        if not self.amount or self.amount <= 0:
            errors.append('金額必須大於0')
        
        if self.amount > 99999:
            errors.append('金額不能超過99999元')
        
        if not self.package_type:
            errors.append('套餐類型是必要的')
        
        if not self.payment_method:
            errors.append('支付方式是必要的')
        
        # 驗證支付方式
        valid_methods = [method.value for method in PaymentMethod]
        if self.payment_method not in valid_methods:
            errors.append(f'無效的支付方式: {self.payment_method}')
        
        # 驗證套餐類型
        valid_packages = [package.value for package in SponsorPackage]
        if self.package_type not in valid_packages:
            errors.append(f'無效的套餐類型: {self.package_type}')
        
        # 驗證狀態
        valid_statuses = [status.value for status in PaymentStatus]
        if self.status not in valid_statuses:
            errors.append(f'無效的支付狀態: {self.status}')
        
        # 驗證客戶信息
        if not self.customer_info.get('name'):
            errors.append('客戶姓名是必要的')
        
        if not self.customer_info.get('email'):
            errors.append('客戶郵箱是必要的')
        
        # 驗證郵箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if self.customer_info.get('email') and not re.match(email_pattern, self.customer_info['email']):
            errors.append('郵箱格式不正確')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def is_expired(self) -> bool:
        """檢查是否已過期"""
        return datetime.now() > self.expires_at
    
    def can_cancel(self) -> bool:
        """檢查是否可以取消"""
        return self.status in [PaymentStatus.PENDING.value, PaymentStatus.PROCESSING.value]
    
    def can_refund(self) -> bool:
        """檢查是否可以退款"""
        return self.status == PaymentStatus.COMPLETED.value
    
    def update_status(self, new_status: str, transaction_id: str = None, paid_at: datetime = None):
        """更新訂單狀態"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if transaction_id:
            self.transaction_id = transaction_id
        
        if paid_at:
            self.paid_at = paid_at
        elif new_status == PaymentStatus.COMPLETED.value:
            self.paid_at = datetime.now()
    
    def calculate_fee(self, fee_rate: float) -> float:
        """計算手續費"""
        fee = self.amount * fee_rate
        self.fee = float(Decimal(str(fee)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        return self.fee
    
    def apply_discount(self, discount_code: str, discount_amount: float):
        """應用折扣"""
        self.discount_code = discount_code
        self.discount_amount = discount_amount
        self.original_amount = self.amount
        self.amount = max(1, self.amount - discount_amount)  # 最低1元
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'package_type': self.package_type,
            'payment_method': self.payment_method,
            'status': self.status,
            'description': self.description,
            'customer_info': self.customer_info,
            'callback_url': self.callback_url,
            'return_url': self.return_url,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'payment_id': self.payment_id,
            'payment_url': self.payment_url,
            'transaction_id': self.transaction_id,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'fee': self.fee,
            'discount_code': self.discount_code,
            'discount_amount': self.discount_amount,
            'original_amount': self.original_amount,
            'notes': self.notes,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentOrder':
        """從字典創建對象"""
        # 轉換日期字段
        date_fields = ['expires_at', 'created_at', 'updated_at', 'paid_at']
        for field in date_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except ValueError:
                    data[field] = None
        
        return cls(**data)
    
    def __str__(self) -> str:
        return f"PaymentOrder(order_id={self.order_id}, amount={self.amount}, status={self.status})"
    
    def __repr__(self) -> str:
        return self.__str__()

class PaymentMethodConfig:
    """支付方式配置"""
    
    def __init__(self, 
                 method_id: str,
                 name: str,
                 code: str,
                 fee_rate: float,
                 min_amount: float,
                 max_amount: float,
                 processing_time: str,
                 enabled: bool = True,
                 icon: str = None,
                 description: str = None):
        
        self.method_id = method_id
        self.name = name
        self.code = code
        self.fee_rate = fee_rate
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.processing_time = processing_time
        self.enabled = enabled
        self.icon = icon
        self.description = description
    
    def is_amount_valid(self, amount: float) -> bool:
        """檢查金額是否有效"""
        return self.min_amount <= amount <= self.max_amount
    
    def calculate_fee(self, amount: float) -> float:
        """計算手續費"""
        fee = amount * self.fee_rate
        return float(Decimal(str(fee)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'method_id': self.method_id,
            'name': self.name,
            'code': self.code,
            'fee_rate': self.fee_rate,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'processing_time': self.processing_time,
            'enabled': self.enabled,
            'icon': self.icon,
            'description': self.description
        }

class SponsorPackageConfig:
    """贊助套餐配置"""
    
    def __init__(self,
                 package_id: str,
                 name: str,
                 amount: float,
                 description: str,
                 features: List[str] = None,
                 popular: bool = False,
                 enabled: bool = True,
                 icon: str = None,
                 color: str = None):
        
        self.package_id = package_id
        self.name = name
        self.amount = amount
        self.description = description
        self.features = features or []
        self.popular = popular
        self.enabled = enabled
        self.icon = icon
        self.color = color
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'package_id': self.package_id,
            'name': self.name,
            'amount': self.amount,
            'description': self.description,
            'features': self.features,
            'popular': self.popular,
            'enabled': self.enabled,
            'icon': self.icon,
            'color': self.color
        }

# 預設套餐配置
DEFAULT_PACKAGES = {
    'basic': SponsorPackageConfig(
        package_id='basic',
        name='基礎套餐',
        amount=100,
        description='支持我們的基礎運營',
        features=['感謝名單', '專屬徽章', '優先客服'],
        icon='🌟',
        color='#3B82F6'
    ),
    'advanced': SponsorPackageConfig(
        package_id='advanced',
        name='進階套餐',
        amount=500,
        description='獲得更多專屬權益',
        features=['基礎套餐所有權益', '專屬頭像框', '內測資格', '月度報告'],
        popular=True,
        icon='ROCKET',
        color='#10B981'
    ),
    'vip': SponsorPackageConfig(
        package_id='vip',
        name='VIP套餐',
        amount=1000,
        description='享受VIP級別服務',
        features=['進階套餐所有權益', 'VIP專屬群組', '一對一諮詢', '定制服務'],
        icon='👑',
        color='#F59E0B'
    ),
    'supreme': SponsorPackageConfig(
        package_id='supreme',
        name='至尊套餐',
        amount=2000,
        description='最高級別的支持',
        features=['VIP套餐所有權益', '產品共同決策權', '年度聚會邀請', '專屬定制'],
        icon='💎',
        color='#8B5CF6'
    )
}

# 預設支付方式配置
DEFAULT_PAYMENT_METHODS = {
    'speedpay_credit': PaymentMethodConfig(
        method_id='speedpay_credit',
        name='速買配-信用卡',
        code='credit_card',
        fee_rate=0.028,
        min_amount=1,
        max_amount=50000,
        processing_time='即時',
        icon='💳',
        description='支持各大銀行信用卡'
    ),
    'speedpay_atm': PaymentMethodConfig(
        method_id='speedpay_atm',
        name='速買配-ATM轉帳',
        code='atm',
        fee_rate=0.015,
        min_amount=10,
        max_amount=50000,
        processing_time='1-30分鐘',
        icon='🏧',
        description='ATM轉帳，手續費最低'
    ),
    'ecpay_credit': PaymentMethodConfig(
        method_id='ecpay_credit',
        name='綠界-信用卡',
        code='credit_card',
        fee_rate=0.028,
        min_amount=1,
        max_amount=20000,
        processing_time='即時',
        icon='💳',
        description='綠界科技信用卡支付'
    ),
    'newebpay_credit': PaymentMethodConfig(
        method_id='newebpay_credit',
        name='藍新-信用卡',
        code='credit_card',
        fee_rate=0.028,
        min_amount=1,
        max_amount=99999,
        processing_time='即時',
        icon='💳',
        description='藍新金流信用卡支付'
    )
}