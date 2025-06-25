#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 交易記錄模型
Transaction Model for 4D Tech Style Auto Sponsorship System

主要功能:
- 交易記錄數據模型
- 交易統計分析
- 交易歷史追蹤
- 數據驗證
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

class TransactionType(Enum):
    """交易類型枚舉"""
    SPONSOR = 'sponsor'          # 贊助
    REFUND = 'refund'           # 退款
    ADJUSTMENT = 'adjustment'    # 調整
    BONUS = 'bonus'             # 獎勵
    PENALTY = 'penalty'         # 懲罰

class TransactionStatus(Enum):
    """交易狀態枚舉"""
    PENDING = 'pending'          # 待處理
    PROCESSING = 'processing'    # 處理中
    COMPLETED = 'completed'      # 已完成
    FAILED = 'failed'           # 失敗
    CANCELLED = 'cancelled'      # 已取消
    REVERSED = 'reversed'        # 已撤銷

class Transaction:
    """交易記錄模型"""
    
    def __init__(self,
                 transaction_id: str = None,
                 user_id: int = None,
                 order_id: str = None,
                 amount: float = 0,
                 transaction_type: str = TransactionType.SPONSOR.value,
                 status: str = TransactionStatus.PENDING.value,
                 payment_method: str = None,
                 description: str = None,
                 reference_id: str = None,
                 metadata: Dict = None,
                 created_at: datetime = None,
                 updated_at: datetime = None,
                 completed_at: datetime = None,
                 **kwargs):
        
        self.id = kwargs.get('id')
        self.transaction_id = transaction_id or self._generate_transaction_id()
        self.user_id = user_id
        self.order_id = order_id
        self.amount = float(amount) if amount else 0
        self.transaction_type = transaction_type
        self.status = status
        self.payment_method = payment_method
        self.description = description or ''
        self.reference_id = reference_id
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.completed_at = completed_at
        
        # 額外信息
        self.fee = kwargs.get('fee', 0)
        self.currency = kwargs.get('currency', 'TWD')
        self.exchange_rate = kwargs.get('exchange_rate', 1.0)
        self.original_amount = kwargs.get('original_amount', self.amount)
        self.notes = kwargs.get('notes', '')
        self.admin_id = kwargs.get('admin_id')  # 管理員操作ID
        self.ip_address = kwargs.get('ip_address')
        self.user_agent = kwargs.get('user_agent')
    
    def _generate_transaction_id(self) -> str:
        """生成交易ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"TXN{timestamp}{random_part}"
    
    def validate(self) -> Dict[str, Any]:
        """驗證交易數據"""
        errors = []
        
        # 驗證必要字段
        if not self.user_id:
            errors.append('用戶ID是必要的')
        
        if not self.amount or self.amount == 0:
            errors.append('金額不能為0')
        
        if abs(self.amount) > 999999:
            errors.append('金額不能超過999999元')
        
        # 驗證交易類型
        valid_types = [t.value for t in TransactionType]
        if self.transaction_type not in valid_types:
            errors.append(f'無效的交易類型: {self.transaction_type}')
        
        # 驗證狀態
        valid_statuses = [s.value for s in TransactionStatus]
        if self.status not in valid_statuses:
            errors.append(f'無效的交易狀態: {self.status}')
        
        # 驗證金額符號
        if self.transaction_type in [TransactionType.REFUND.value, TransactionType.PENALTY.value]:
            if self.amount > 0:
                errors.append(f'{self.transaction_type}交易金額應為負數')
        elif self.transaction_type in [TransactionType.SPONSOR.value, TransactionType.BONUS.value]:
            if self.amount < 0:
                errors.append(f'{self.transaction_type}交易金額應為正數')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def is_completed(self) -> bool:
        """檢查是否已完成"""
        return self.status == TransactionStatus.COMPLETED.value
    
    def can_cancel(self) -> bool:
        """檢查是否可以取消"""
        return self.status in [TransactionStatus.PENDING.value, TransactionStatus.PROCESSING.value]
    
    def can_reverse(self) -> bool:
        """檢查是否可以撤銷"""
        return self.status == TransactionStatus.COMPLETED.value and self.transaction_type != TransactionType.REFUND.value
    
    def update_status(self, new_status: str, admin_id: int = None, notes: str = None):
        """更新交易狀態"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if admin_id:
            self.admin_id = admin_id
        
        if notes:
            self.notes = notes
        
        if new_status == TransactionStatus.COMPLETED.value:
            self.completed_at = datetime.now()
    
    def add_metadata(self, key: str, value: Any):
        """添加元數據"""
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def get_processing_time(self) -> Optional[timedelta]:
        """獲取處理時間"""
        if self.completed_at and self.created_at:
            return self.completed_at - self.created_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'status': self.status,
            'payment_method': self.payment_method,
            'description': self.description,
            'reference_id': self.reference_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'fee': self.fee,
            'currency': self.currency,
            'exchange_rate': self.exchange_rate,
            'original_amount': self.original_amount,
            'notes': self.notes,
            'admin_id': self.admin_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """從字典創建對象"""
        # 轉換日期字段
        date_fields = ['created_at', 'updated_at', 'completed_at']
        for field in date_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except ValueError:
                    data[field] = None
        
        return cls(**data)
    
    def __str__(self) -> str:
        return f"Transaction(id={self.transaction_id}, amount={self.amount}, type={self.transaction_type}, status={self.status})"
    
    def __repr__(self) -> str:
        return self.__str__()

class TransactionSummary:
    """交易統計摘要"""
    
    def __init__(self,
                 total_amount: float = 0,
                 total_count: int = 0,
                 completed_amount: float = 0,
                 completed_count: int = 0,
                 pending_amount: float = 0,
                 pending_count: int = 0,
                 failed_amount: float = 0,
                 failed_count: int = 0,
                 period_start: datetime = None,
                 period_end: datetime = None):
        
        self.total_amount = total_amount
        self.total_count = total_count
        self.completed_amount = completed_amount
        self.completed_count = completed_count
        self.pending_amount = pending_amount
        self.pending_count = pending_count
        self.failed_amount = failed_amount
        self.failed_count = failed_count
        self.period_start = period_start
        self.period_end = period_end
    
    def get_success_rate(self) -> float:
        """獲取成功率"""
        if self.total_count == 0:
            return 0
        return (self.completed_count / self.total_count) * 100
    
    def get_average_amount(self) -> float:
        """獲取平均金額"""
        if self.completed_count == 0:
            return 0
        return self.completed_amount / self.completed_count
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'total_amount': self.total_amount,
            'total_count': self.total_count,
            'completed_amount': self.completed_amount,
            'completed_count': self.completed_count,
            'pending_amount': self.pending_amount,
            'pending_count': self.pending_count,
            'failed_amount': self.failed_amount,
            'failed_count': self.failed_count,
            'success_rate': self.get_success_rate(),
            'average_amount': self.get_average_amount(),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None
        }

class TransactionAnalytics:
    """交易分析工具"""
    
    @staticmethod
    def calculate_summary(transactions: List[Transaction], 
                         period_start: datetime = None, 
                         period_end: datetime = None) -> TransactionSummary:
        """計算交易摘要"""
        # 過濾時間範圍
        if period_start or period_end:
            filtered_transactions = []
            for txn in transactions:
                if period_start and txn.created_at < period_start:
                    continue
                if period_end and txn.created_at > period_end:
                    continue
                filtered_transactions.append(txn)
            transactions = filtered_transactions
        
        summary = TransactionSummary(
            period_start=period_start,
            period_end=period_end
        )
        
        for txn in transactions:
            summary.total_count += 1
            summary.total_amount += txn.amount
            
            if txn.status == TransactionStatus.COMPLETED.value:
                summary.completed_count += 1
                summary.completed_amount += txn.amount
            elif txn.status == TransactionStatus.PENDING.value:
                summary.pending_count += 1
                summary.pending_amount += txn.amount
            elif txn.status == TransactionStatus.FAILED.value:
                summary.failed_count += 1
                summary.failed_amount += txn.amount
        
        return summary
    
    @staticmethod
    def group_by_date(transactions: List[Transaction], 
                     date_format: str = '%Y-%m-%d') -> Dict[str, TransactionSummary]:
        """按日期分組統計"""
        groups = {}
        
        for txn in transactions:
            date_key = txn.created_at.strftime(date_format)
            
            if date_key not in groups:
                groups[date_key] = []
            
            groups[date_key].append(txn)
        
        # 計算每組的摘要
        result = {}
        for date_key, txn_list in groups.items():
            result[date_key] = TransactionAnalytics.calculate_summary(txn_list)
        
        return result
    
    @staticmethod
    def group_by_payment_method(transactions: List[Transaction]) -> Dict[str, TransactionSummary]:
        """按支付方式分組統計"""
        groups = {}
        
        for txn in transactions:
            method = txn.payment_method or 'unknown'
            
            if method not in groups:
                groups[method] = []
            
            groups[method].append(txn)
        
        # 計算每組的摘要
        result = {}
        for method, txn_list in groups.items():
            result[method] = TransactionAnalytics.calculate_summary(txn_list)
        
        return result
    
    @staticmethod
    def group_by_user(transactions: List[Transaction]) -> Dict[int, TransactionSummary]:
        """按用戶分組統計"""
        groups = {}
        
        for txn in transactions:
            user_id = txn.user_id
            
            if user_id not in groups:
                groups[user_id] = []
            
            groups[user_id].append(txn)
        
        # 計算每組的摘要
        result = {}
        for user_id, txn_list in groups.items():
            result[user_id] = TransactionAnalytics.calculate_summary(txn_list)
        
        return result
    
    @staticmethod
    def get_top_users(transactions: List[Transaction], limit: int = 10) -> List[Tuple[int, float, int]]:
        """獲取贊助金額最高的用戶"""
        user_stats = TransactionAnalytics.group_by_user(transactions)
        
        # 只考慮已完成的交易
        user_amounts = []
        for user_id, summary in user_stats.items():
            if summary.completed_amount > 0:
                user_amounts.append((user_id, summary.completed_amount, summary.completed_count))
        
        # 按金額排序
        user_amounts.sort(key=lambda x: x[1], reverse=True)
        
        return user_amounts[:limit]
    
    @staticmethod
    def get_daily_trend(transactions: List[Transaction], days: int = 30) -> List[Dict[str, Any]]:
        """獲取每日趨勢"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # 生成日期範圍
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # 按日期分組
        daily_groups = TransactionAnalytics.group_by_date(transactions, '%Y-%m-%d')
        
        # 構建趨勢數據
        trend_data = []
        for date_str in date_range:
            summary = daily_groups.get(date_str, TransactionSummary())
            trend_data.append({
                'date': date_str,
                'amount': summary.completed_amount,
                'count': summary.completed_count,
                'success_rate': summary.get_success_rate()
            })
        
        return trend_data
    
    @staticmethod
    def detect_anomalies(transactions: List[Transaction], 
                        threshold_multiplier: float = 3.0) -> List[Transaction]:
        """檢測異常交易"""
        if len(transactions) < 10:  # 數據太少，無法檢測異常
            return []
        
        # 計算已完成交易的平均金額和標準差
        completed_amounts = [txn.amount for txn in transactions 
                           if txn.status == TransactionStatus.COMPLETED.value and txn.amount > 0]
        
        if len(completed_amounts) < 5:
            return []
        
        import statistics
        mean_amount = statistics.mean(completed_amounts)
        stdev_amount = statistics.stdev(completed_amounts)
        
        # 檢測異常
        anomalies = []
        threshold = mean_amount + (threshold_multiplier * stdev_amount)
        
        for txn in transactions:
            if txn.amount > threshold:
                anomalies.append(txn)
        
        return anomalies

# 工具函數

def create_refund_transaction(original_transaction: Transaction, 
                            refund_amount: float = None,
                            admin_id: int = None,
                            reason: str = None) -> Transaction:
    """創建退款交易"""
    refund_amount = refund_amount or original_transaction.amount
    
    return Transaction(
        user_id=original_transaction.user_id,
        order_id=original_transaction.order_id,
        amount=-abs(refund_amount),  # 退款金額為負數
        transaction_type=TransactionType.REFUND.value,
        status=TransactionStatus.PENDING.value,
        payment_method=original_transaction.payment_method,
        description=f"退款: {original_transaction.description}",
        reference_id=original_transaction.transaction_id,
        admin_id=admin_id,
        notes=reason or '用戶申請退款',
        metadata={
            'original_transaction_id': original_transaction.transaction_id,
            'refund_reason': reason
        }
    )

def format_transaction_amount(amount: float, currency: str = 'TWD') -> str:
    """格式化交易金額"""
    if currency == 'TWD':
        return f"NT$ {amount:,.0f}"
    else:
        return f"{currency} {amount:,.2f}"

def validate_transaction_amount(amount: float, transaction_type: str) -> bool:
    """驗證交易金額"""
    if transaction_type in [TransactionType.REFUND.value, TransactionType.PENALTY.value]:
        return amount <= 0
    elif transaction_type in [TransactionType.SPONSOR.value, TransactionType.BONUS.value]:
        return amount > 0
    else:
        return amount != 0