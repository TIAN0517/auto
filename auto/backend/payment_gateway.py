#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 支付閘道
Payment Gateway for 4D Tech Style Auto Sponsorship System

主要功能:
- 統一支付接口
- 多支付方式管理
- 訂單狀態追蹤
- 支付流程控制
- 錯誤處理和重試
"""

import os
import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

# 支付服務
from speedpay_service import SpeedPayService
from ecpay_service import ECPayService
from newebpay_service import NewebPayService
from usdt_service import USDTPaymentService

# 模型
from models.payment import Payment
from models.transaction import Transaction

logger = logging.getLogger(__name__)

class PaymentMethod(Enum):
    """支付方式枚舉"""
    SPEEDPAY = "speedpay"
    ECPAY = "ecpay"
    NEWEBPAY = "newebpay"
    USDT_ERC20 = "usdt_erc20"
    USDT_TRC20 = "usdt_trc20"

class PaymentStatus(Enum):
    """支付狀態枚舉"""
    PENDING = "pending"          # 待支付
    PROCESSING = "processing"    # 處理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失敗
    CANCELLED = "cancelled"      # 已取消
    EXPIRED = "expired"          # 已過期
    REFUNDED = "refunded"        # 已退款

class PackageType(Enum):
    """套餐類型枚舉"""
    BASIC = "basic"              # 基礎套餐
    ADVANCED = "advanced"        # 進階套餐
    VIP = "vip"                  # VIP套餐
    SUPREME = "supreme"          # 至尊套餐

class PaymentGateway:
    """支付閘道主類"""
    
    def __init__(self):
        """初始化支付閘道"""
        self.speedpay = SpeedPayService()
        self.ecpay = ECPayService()
        self.newebpay = NewebPayService()
        self.usdt = USDTPaymentService()
        
        # 支付方式配置
        self.payment_methods = {
            PaymentMethod.SPEEDPAY.value: {
                'name': '速買配',
                'service': self.speedpay,
                'enabled': True,
                'priority': 1,
                'fee_rate': 0.025,  # 2.5%
                'min_amount': 10,
                'max_amount': 50000,
                'supported_currencies': ['TWD'],
                'processing_time': '即時',
                'description': '台灣本土化支付，支援超商、ATM、信用卡'
            },
            PaymentMethod.ECPAY.value: {
                'name': '綠界科技',
                'service': self.ecpay,
                'enabled': True,
                'priority': 2,
                'fee_rate': 0.028,  # 2.8%
                'min_amount': 1,
                'max_amount': 20000,
                'supported_currencies': ['TWD'],
                'processing_time': '1-3分鐘',
                'description': '多元支付方式，信用卡、ATM、超商代碼'
            },
            PaymentMethod.NEWEBPAY.value: {
                'name': '藍新金流',
                'service': self.newebpay,
                'enabled': True,
                'priority': 3,
                'fee_rate': 0.030,  # 3.0%
                'min_amount': 10,
                'max_amount': 30000,
                'supported_currencies': ['TWD'],
                'processing_time': '1-5分鐘',
                'description': '安全可靠，支援多種銀行和支付方式'
            },
            PaymentMethod.USDT_ERC20.value: {
                'name': 'USDT (ERC-20)',
                'service': self.usdt,
                'enabled': True,
                'priority': 4,
                'fee_rate': 0.005,  # 0.5%
                'min_amount': 1,
                'max_amount': 10000,
                'supported_currencies': ['USDT'],
                'processing_time': '5-30分鐘',
                'description': 'Ethereum網絡USDT支付，安全可靠',
                'network': 'erc20',
                'wallet_address': '0x732b0b53435977b03c4cef6b7bdffc45e6ec44e6'
            },
            PaymentMethod.USDT_TRC20.value: {
                'name': 'USDT (TRC-20)',
                'service': self.usdt,
                'enabled': True,
                'priority': 5,
                'fee_rate': 0.003,  # 0.3%
                'min_amount': 1,
                'max_amount': 50000,
                'supported_currencies': ['USDT'],
                'processing_time': '1-5分鐘',
                'description': 'Tron網絡USDT支付，手續費最低',
                'network': 'trc20',
                'wallet_address': 'TDejRjcLQa92rrE6SB71LSC7J5VmHs35gq'
            }
        }
        
        # 套餐配置
        self.packages = {
            PackageType.BASIC.value: {
                'name': '基礎套餐',
                'price': 99,
                'original_price': 149,
                'discount': 50,
                'features': [
                    '基礎功能訪問',
                    '標準客服支援',
                    '30天有效期',
                    '基礎數據分析'
                ],
                'popular': False,
                'color': 'blue'
            },
            PackageType.ADVANCED.value: {
                'name': '進階套餐',
                'price': 299,
                'original_price': 399,
                'discount': 100,
                'features': [
                    '進階功能訪問',
                    '優先客服支援',
                    '90天有效期',
                    '進階數據分析',
                    '自定義設置'
                ],
                'popular': True,
                'color': 'purple'
            },
            PackageType.VIP.value: {
                'name': 'VIP套餐',
                'price': 599,
                'original_price': 799,
                'discount': 200,
                'features': [
                    '全功能訪問',
                    'VIP專屬客服',
                    '180天有效期',
                    '專業數據分析',
                    '高級自定義',
                    'API訪問權限'
                ],
                'popular': False,
                'color': 'gold'
            },
            PackageType.SUPREME.value: {
                'name': '至尊套餐',
                'price': 999,
                'original_price': 1299,
                'discount': 300,
                'features': [
                    '無限制訪問',
                    '24/7專屬客服',
                    '365天有效期',
                    '企業級分析',
                    '完全自定義',
                    '完整API權限',
                    '專屬技術支援'
                ],
                'popular': False,
                'color': 'diamond'
            }
        }
        
        # 折扣碼配置
        self.discount_codes = {
            'WELCOME10': {
                'type': 'percentage',
                'value': 10,
                'min_amount': 100,
                'max_discount': 50,
                'expires_at': '2024-12-31',
                'usage_limit': 1000,
                'used_count': 0,
                'description': '新用戶專享10%折扣'
            },
            'SAVE50': {
                'type': 'fixed',
                'value': 50,
                'min_amount': 200,
                'max_discount': 50,
                'expires_at': '2024-12-31',
                'usage_limit': 500,
                'used_count': 0,
                'description': '滿200減50'
            },
            'VIP20': {
                'type': 'percentage',
                'value': 20,
                'min_amount': 500,
                'max_discount': 200,
                'expires_at': '2024-12-31',
                'usage_limit': 100,
                'used_count': 0,
                'description': 'VIP用戶專享20%折扣'
            }
        }
        
        logger.info("支付閘道初始化完成")
    
    def get_available_payment_methods(self, amount: float = None) -> List[Dict]:
        """獲取可用支付方式"""
        available_methods = []
        
        for method_id, config in self.payment_methods.items():
            if not config['enabled']:
                continue
            
            # 檢查金額限制
            if amount:
                if amount < config['min_amount'] or amount > config['max_amount']:
                    continue
            
            # 檢查服務可用性
            try:
                service = config['service']
                if hasattr(service, 'is_available') and not service.is_available():
                    continue
            except Exception as e:
                logger.warning(f"檢查支付方式 {method_id} 可用性失敗: {e}")
                continue
            
            available_methods.append({
                'id': method_id,
                'name': config['name'],
                'fee_rate': config['fee_rate'],
                'min_amount': config['min_amount'],
                'max_amount': config['max_amount'],
                'processing_time': config['processing_time'],
                'description': config['description'],
                'priority': config['priority']
            })
        
        # 按優先級排序
        available_methods.sort(key=lambda x: x['priority'])
        
        return available_methods
    
    def get_packages(self) -> Dict:
        """獲取套餐信息"""
        return self.packages
    
    def get_package_info(self, package_id: str) -> Optional[Dict]:
        """獲取套餐詳情"""
        return self.packages.get(package_id)
    
    def validate_discount_code(self, code: str, amount: float) -> Dict:
        """驗證折扣碼"""
        if not code or code not in self.discount_codes:
            return {
                'valid': False,
                'message': '折扣碼不存在或已失效'
            }
        
        discount_info = self.discount_codes[code]
        
        # 檢查過期時間
        if datetime.now() > datetime.strptime(discount_info['expires_at'], '%Y-%m-%d'):
            return {
                'valid': False,
                'message': '折扣碼已過期'
            }
        
        # 檢查使用次數
        if discount_info['used_count'] >= discount_info['usage_limit']:
            return {
                'valid': False,
                'message': '折扣碼使用次數已達上限'
            }
        
        # 檢查最小金額
        if amount < discount_info['min_amount']:
            return {
                'valid': False,
                'message': f'訂單金額需滿 {discount_info["min_amount"]} 元'
            }
        
        # 計算折扣金額
        if discount_info['type'] == 'percentage':
            discount_amount = amount * (discount_info['value'] / 100)
            discount_amount = min(discount_amount, discount_info['max_discount'])
        else:  # fixed
            discount_amount = discount_info['value']
        
        return {
            'valid': True,
            'discount_amount': discount_amount,
            'final_amount': amount - discount_amount,
            'description': discount_info['description']
        }
    
    def calculate_fee(self, amount: float, payment_method: str) -> float:
        """計算手續費"""
        if payment_method not in self.payment_methods:
            return 0
        
        fee_rate = self.payment_methods[payment_method]['fee_rate']
        fee = amount * fee_rate
        
        # 四捨五入到分
        return float(Decimal(str(fee)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def generate_order_id(self) -> str:
        """生成訂單ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"JY{timestamp}{random_part}"
    
    def create_payment_order(self, 
                           user_id: Optional[int],
                           package_id: str,
                           amount: float,
                           original_amount: float,
                           discount_amount: float,
                           discount_code: Optional[str],
                           payment_method: str,
                           customer_info: Dict) -> Dict:
        """創建支付訂單"""
        try:
            # 驗證套餐
            package_info = self.get_package_info(package_id)
            if not package_info:
                return {
                    'success': False,
                    'message': '套餐不存在'
                }
            
            # 驗證支付方式
            if payment_method not in self.payment_methods:
                return {
                    'success': False,
                    'message': '不支援的支付方式'
                }
            
            method_config = self.payment_methods[payment_method]
            
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
            
            # 生成訂單ID
            order_id = self.generate_order_id()
            
            # 計算手續費
            fee = self.calculate_fee(amount, payment_method)
            
            # 設置過期時間（30分鐘）
            expires_at = datetime.now() + timedelta(minutes=30)
            
            # 創建支付訂單記錄
            from main_app import db_manager
            
            query = '''
                INSERT INTO payment_orders (
                    order_id, user_id, package_id, amount, original_amount,
                    discount_amount, discount_code, payment_method, status,
                    expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            '''
            
            db_manager.execute_update(query, (
                order_id, user_id, package_id, amount, original_amount,
                discount_amount, discount_code, payment_method, PaymentStatus.PENDING.value,
                expires_at.isoformat()
            ))
            
            # 調用對應支付服務創建支付
            service = method_config['service']
            
            # USDT支付特殊處理
            if payment_method in [PaymentMethod.USDT_ERC20.value, PaymentMethod.USDT_TRC20.value]:
                network = method_config.get('network', 'erc20')
                payment_result = service.create_payment_order(
                    amount=amount,
                    network=network,
                    order_id=order_id
                )
            else:
                # 傳統支付方式
                payment_result = service.create_payment(
                    order_id=order_id,
                    amount=amount,
                    description=f"{package_info['name']} - {package_id}",
                    customer_info=customer_info,
                    callback_url=f"/webhook/{payment_method}",
                    return_url=f"/payment/result?order_id={order_id}"
                )
            
            if not payment_result['success']:
                # 更新訂單狀態為失敗
                db_manager.execute_update(
                    'UPDATE payment_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?',
                    (PaymentStatus.FAILED.value, order_id)
                )
                
                return {
                    'success': False,
                    'message': payment_result.get('message', '創建支付失敗')
                }
            
            # 更新支付URL
            db_manager.execute_update(
                'UPDATE payment_orders SET payment_url = ?, callback_data = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?',
                (payment_result.get('payment_url'), json.dumps(payment_result.get('callback_data', {})), order_id)
            )
            
            logger.info(f"支付訂單創建成功: {order_id}")
            
            return {
                'success': True,
                'order_id': order_id,
                'payment_url': payment_result.get('payment_url'),
                'amount': amount,
                'fee': fee,
                'payment_method': payment_method,
                'expires_at': expires_at.isoformat(),
                'package_info': package_info,
                'message': '支付訂單創建成功'
            }
            
        except Exception as e:
            logger.error(f"創建支付訂單失敗: {e}")
            return {
                'success': False,
                'message': '系統錯誤，請稍後重試'
            }
    
    def get_payment_status(self, order_id: str) -> Dict:
        """獲取支付狀態"""
        try:
            from main_app import db_manager
            
            # 查詢訂單信息
            orders = db_manager.execute_query(
                'SELECT * FROM payment_orders WHERE order_id = ?',
                (order_id,)
            )
            
            if not orders:
                return {
                    'success': False,
                    'message': '訂單不存在'
                }
            
            order = orders[0]
            
            # 檢查訂單是否過期
            if order['status'] == PaymentStatus.PENDING.value:
                expires_at = datetime.fromisoformat(order['expires_at'])
                if datetime.now() > expires_at:
                    # 更新為過期狀態
                    db_manager.execute_update(
                        'UPDATE payment_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?',
                        (PaymentStatus.EXPIRED.value, order_id)
                    )
                    order['status'] = PaymentStatus.EXPIRED.value
            
            # 如果是待支付或處理中狀態，查詢支付服務商狀態
            if order['status'] in [PaymentStatus.PENDING.value, PaymentStatus.PROCESSING.value]:
                payment_method = order['payment_method']
                if payment_method in self.payment_methods:
                    service = self.payment_methods[payment_method]['service']
                    
                    try:
                        service_status = service.query_payment_status(order_id)
                        if service_status['success'] and service_status.get('status'):
                            new_status = service_status['status']
                            
                            # 更新訂單狀態
                            if new_status != order['status']:
                                update_data = {
                                    'status': new_status,
                                    'updated_at': datetime.now().isoformat()
                                }
                                
                                if new_status == PaymentStatus.COMPLETED.value:
                                    update_data['paid_at'] = datetime.now().isoformat()
                                
                                db_manager.execute_update(
                                    'UPDATE payment_orders SET status = ?, updated_at = ?, paid_at = ? WHERE order_id = ?',
                                    (new_status, update_data['updated_at'], update_data.get('paid_at'), order_id)
                                )
                                
                                order['status'] = new_status
                                order['paid_at'] = update_data.get('paid_at')
                    
                    except Exception as e:
                        logger.warning(f"查詢支付服務商狀態失敗: {e}")
            
            return {
                'success': True,
                'order_id': order_id,
                'status': order['status'],
                'amount': order['amount'],
                'payment_method': order['payment_method'],
                'payment_url': order['payment_url'],
                'created_at': order['created_at'],
                'updated_at': order['updated_at'],
                'paid_at': order['paid_at'],
                'expires_at': order['expires_at']
            }
            
        except Exception as e:
            logger.error(f"獲取支付狀態失敗: {e}")
            return {
                'success': False,
                'message': '系統錯誤'
            }
    
    def process_payment_callback(self, payment_method: str, callback_data: Dict) -> Dict:
        """處理支付回調"""
        try:
            if payment_method not in self.payment_methods:
                return {
                    'success': False,
                    'message': '不支援的支付方式'
                }
            
            service = self.payment_methods[payment_method]['service']
            
            # 驗證回調數據
            validation_result = service.validate_callback(callback_data)
            
            if not validation_result['success']:
                logger.warning(f"支付回調驗證失敗: {validation_result.get('message')}")
                return validation_result
            
            order_id = validation_result['order_id']
            payment_status = validation_result['status']
            
            # 更新訂單狀態
            from main_app import db_manager
            
            update_data = {
                'status': payment_status,
                'updated_at': datetime.now().isoformat()
            }
            
            if payment_status == PaymentStatus.COMPLETED.value:
                update_data['paid_at'] = datetime.now().isoformat()
            
            db_manager.execute_update(
                'UPDATE payment_orders SET status = ?, updated_at = ?, paid_at = ? WHERE order_id = ?',
                (payment_status, update_data['updated_at'], update_data.get('paid_at'), order_id)
            )
            
            # 創建交易記錄
            transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"
            
            db_manager.execute_update('''
                INSERT INTO transactions (
                    transaction_id, order_id, payment_method, amount, fee, status,
                    gateway_response, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                transaction_id, order_id, payment_method,
                validation_result.get('amount', 0),
                validation_result.get('fee', 0),
                payment_status,
                json.dumps(callback_data)
            ))
            
            logger.info(f"支付回調處理完成: {order_id} - {payment_status}")
            
            return {
                'success': True,
                'order_id': order_id,
                'transaction_id': transaction_id,
                'status': payment_status,
                'message': '回調處理成功'
            }
            
        except Exception as e:
            logger.error(f"處理支付回調失敗: {e}")
            return {
                'success': False,
                'message': '回調處理失敗'
            }
    
    def cancel_payment(self, order_id: str, reason: str = None) -> Dict:
        """取消支付"""
        try:
            from main_app import db_manager
            
            # 查詢訂單
            orders = db_manager.execute_query(
                'SELECT * FROM payment_orders WHERE order_id = ?',
                (order_id,)
            )
            
            if not orders:
                return {
                    'success': False,
                    'message': '訂單不存在'
                }
            
            order = orders[0]
            
            # 檢查訂單狀態
            if order['status'] not in [PaymentStatus.PENDING.value, PaymentStatus.PROCESSING.value]:
                return {
                    'success': False,
                    'message': '訂單狀態不允許取消'
                }
            
            # 更新訂單狀態
            db_manager.execute_update(
                'UPDATE payment_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?',
                (PaymentStatus.CANCELLED.value, order_id)
            )
            
            logger.info(f"支付訂單已取消: {order_id} - {reason}")
            
            return {
                'success': True,
                'message': '訂單已取消'
            }
            
        except Exception as e:
            logger.error(f"取消支付失敗: {e}")
            return {
                'success': False,
                'message': '取消失敗'
            }
    
    def get_payment_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """獲取支付統計"""
        try:
            from main_app import db_manager
            
            # 構建查詢條件
            where_clause = "WHERE 1=1"
            params = []
            
            if start_date:
                where_clause += " AND created_at >= ?"
                params.append(start_date)
            
            if end_date:
                where_clause += " AND created_at <= ?"
                params.append(end_date)
            
            # 總體統計
            total_stats = db_manager.execute_query(f'''
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) as pending_orders,
                    COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed_orders
                FROM payment_orders {where_clause}
            ''', params)[0]
            
            # 按支付方式統計
            method_stats = db_manager.execute_query(f'''
                SELECT 
                    payment_method,
                    COUNT(*) as order_count,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as revenue
                FROM payment_orders {where_clause}
                GROUP BY payment_method
                ORDER BY revenue DESC
            ''', params)
            
            # 按套餐統計
            package_stats = db_manager.execute_query(f'''
                SELECT 
                    package_id,
                    COUNT(*) as order_count,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as revenue
                FROM payment_orders {where_clause}
                GROUP BY package_id
                ORDER BY revenue DESC
            ''', params)
            
            return {
                'success': True,
                'total_stats': total_stats,
                'method_stats': method_stats,
                'package_stats': package_stats
            }
            
        except Exception as e:
            logger.error(f"獲取支付統計失敗: {e}")
            return {
                'success': False,
                'message': '獲取統計失敗'
            }

# 工具函數

def format_amount(amount: float) -> str:
    """格式化金額"""
    return f"NT$ {amount:,.0f}"

def validate_amount(amount: Any) -> Tuple[bool, float]:
    """驗證金額"""
    try:
        amount = float(amount)
        if amount <= 0:
            return False, 0
        return True, amount
    except (ValueError, TypeError):
        return False, 0

def generate_signature(data: Dict, secret: str) -> str:
    """生成簽名"""
    # 按鍵名排序
    sorted_items = sorted(data.items())
    
    # 構建簽名字符串
    sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items if v is not None])
    sign_string += f"&key={secret}"
    
    # 計算MD5
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

def verify_signature(data: Dict, signature: str, secret: str) -> bool:
    """驗證簽名"""
    expected_signature = generate_signature(data, secret)
    return signature.upper() == expected_signature