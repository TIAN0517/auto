#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4D科技風格自動贊助系統 - 速買配簽名工具
SpeedPay Signature Utils for 4D Tech Style Auto Sponsorship System

主要功能:
- 生成API請求簽名
- 驗證回調簽名
- 加密解密工具
- 安全工具函數
"""

import hashlib
import hmac
import base64
import json
import time
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class SignatureAlgorithm(Enum):
    """簽名算法枚舉"""
    MD5 = 'md5'
    SHA1 = 'sha1'
    SHA256 = 'sha256'
    SHA512 = 'sha512'

class EncryptionAlgorithm(Enum):
    """加密算法枚舉"""
    AES_128_CBC = 'aes-128-cbc'
    AES_256_CBC = 'aes-256-cbc'
    AES_128_GCM = 'aes-128-gcm'
    AES_256_GCM = 'aes-256-gcm'

class SpeedPaySignature:
    """速買配簽名工具"""
    
    def __init__(self, api_secret: str, algorithm: str = SignatureAlgorithm.SHA256.value):
        self.api_secret = api_secret
        self.algorithm = algorithm
        self.encoding = 'utf-8'
    
    def generate_signature(self, data: Dict[str, Any], 
                          exclude_fields: List[str] = None,
                          include_timestamp: bool = True) -> str:
        """生成簽名"""
        exclude_fields = exclude_fields or ['signature', 'sign']
        
        # 添加時間戳
        if include_timestamp and 'timestamp' not in data:
            data['timestamp'] = str(int(time.time()))
        
        # 構建簽名字符串
        sign_string = self._build_sign_string(data, exclude_fields)
        
        # 計算簽名
        return self._calculate_signature(sign_string)
    
    def verify_signature(self, data: Dict[str, Any], 
                        signature: str,
                        exclude_fields: List[str] = None,
                        timestamp_tolerance: int = 300) -> bool:
        """驗證簽名"""
        try:
            exclude_fields = exclude_fields or ['signature', 'sign']
            
            # 驗證時間戳（如果存在）
            if 'timestamp' in data and timestamp_tolerance > 0:
                if not self._validate_timestamp(data['timestamp'], timestamp_tolerance):
                    return False
            
            # 構建簽名字符串
            sign_string = self._build_sign_string(data, exclude_fields)
            
            # 計算期望簽名
            expected_signature = self._calculate_signature(sign_string)
            
            # 比較簽名
            return hmac.compare_digest(expected_signature.lower(), signature.lower())
            
        except Exception:
            return False
    
    def _build_sign_string(self, data: Dict[str, Any], exclude_fields: List[str]) -> str:
        """構建簽名字符串"""
        # 過濾和排序參數
        filtered_data = {
            k: v for k, v in data.items() 
            if k not in exclude_fields and v is not None and str(v) != ''
        }
        
        # 按鍵名排序
        sorted_items = sorted(filtered_data.items())
        
        # 構建查詢字符串
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        
        # 添加密鑰
        sign_string += f"&key={self.api_secret}"
        
        return sign_string
    
    def _calculate_signature(self, sign_string: str) -> str:
        """計算簽名"""
        if self.algorithm == SignatureAlgorithm.MD5.value:
            return hashlib.md5(sign_string.encode(self.encoding)).hexdigest().upper()
        elif self.algorithm == SignatureAlgorithm.SHA1.value:
            return hashlib.sha1(sign_string.encode(self.encoding)).hexdigest().upper()
        elif self.algorithm == SignatureAlgorithm.SHA256.value:
            return hashlib.sha256(sign_string.encode(self.encoding)).hexdigest().upper()
        elif self.algorithm == SignatureAlgorithm.SHA512.value:
            return hashlib.sha512(sign_string.encode(self.encoding)).hexdigest().upper()
        else:
            raise ValueError(f"不支援的簽名算法: {self.algorithm}")
    
    def _validate_timestamp(self, timestamp: Union[str, int], tolerance: int) -> bool:
        """驗證時間戳"""
        try:
            if isinstance(timestamp, str):
                timestamp = int(timestamp)
            
            current_time = int(time.time())
            time_diff = abs(current_time - timestamp)
            
            return time_diff <= tolerance
            
        except (ValueError, TypeError):
            return False
    
    def generate_nonce(self, length: int = 16) -> str:
        """生成隨機字符串"""
        return secrets.token_hex(length)
    
    def url_encode_params(self, params: Dict[str, Any]) -> str:
        """URL編碼參數"""
        encoded_params = []
        for key, value in sorted(params.items()):
            if value is not None:
                encoded_key = urllib.parse.quote_plus(str(key))
                encoded_value = urllib.parse.quote_plus(str(value))
                encoded_params.append(f"{encoded_key}={encoded_value}")
        
        return '&'.join(encoded_params)

class SpeedPayHMAC:
    """HMAC簽名工具"""
    
    def __init__(self, secret_key: str, algorithm: str = 'sha256'):
        self.secret_key = secret_key.encode('utf-8')
        self.algorithm = algorithm
    
    def sign(self, message: str) -> str:
        """生成HMAC簽名"""
        if self.algorithm == 'sha256':
            hash_func = hashlib.sha256
        elif self.algorithm == 'sha1':
            hash_func = hashlib.sha1
        elif self.algorithm == 'md5':
            hash_func = hashlib.md5
        else:
            raise ValueError(f"不支援的HMAC算法: {self.algorithm}")
        
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hash_func
        ).hexdigest()
        
        return signature.upper()
    
    def verify(self, message: str, signature: str) -> bool:
        """驗證HMAC簽名"""
        expected_signature = self.sign(message)
        return hmac.compare_digest(expected_signature.lower(), signature.lower())
    
    def sign_json(self, data: Dict[str, Any]) -> str:
        """簽名JSON數據"""
        json_string = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return self.sign(json_string)
    
    def verify_json(self, data: Dict[str, Any], signature: str) -> bool:
        """驗證JSON數據簽名"""
        expected_signature = self.sign_json(data)
        return hmac.compare_digest(expected_signature.lower(), signature.lower())

class SpeedPayEncryption:
    """加密工具"""
    
    def __init__(self, encryption_key: str, algorithm: str = EncryptionAlgorithm.AES_256_CBC.value):
        self.encryption_key = self._derive_key(encryption_key)
        self.algorithm = algorithm
    
    def _derive_key(self, key: str) -> bytes:
        """派生密鑰"""
        # 使用SHA256生成固定長度的密鑰
        return hashlib.sha256(key.encode('utf-8')).digest()
    
    def encrypt(self, plaintext: str) -> str:
        """加密文本"""
        try:
            if self.algorithm in [EncryptionAlgorithm.AES_128_CBC.value, EncryptionAlgorithm.AES_256_CBC.value]:
                return self._encrypt_cbc(plaintext)
            elif self.algorithm in [EncryptionAlgorithm.AES_128_GCM.value, EncryptionAlgorithm.AES_256_GCM.value]:
                return self._encrypt_gcm(plaintext)
            else:
                raise ValueError(f"不支援的加密算法: {self.algorithm}")
        except Exception as e:
            raise ValueError(f"加密失敗: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """解密文本"""
        try:
            if self.algorithm in [EncryptionAlgorithm.AES_128_CBC.value, EncryptionAlgorithm.AES_256_CBC.value]:
                return self._decrypt_cbc(ciphertext)
            elif self.algorithm in [EncryptionAlgorithm.AES_128_GCM.value, EncryptionAlgorithm.AES_256_GCM.value]:
                return self._decrypt_gcm(ciphertext)
            else:
                raise ValueError(f"不支援的解密算法: {self.algorithm}")
        except Exception as e:
            raise ValueError(f"解密失敗: {str(e)}")
    
    def _encrypt_cbc(self, plaintext: str) -> str:
        """CBC模式加密"""
        # 生成隨機IV
        iv = get_random_bytes(16)
        
        # 創建加密器
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        
        # 填充和加密
        padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        
        # 組合IV和密文
        encrypted_data = iv + ciphertext
        
        # Base64編碼
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def _decrypt_cbc(self, ciphertext: str) -> str:
        """CBC模式解密"""
        # Base64解碼
        encrypted_data = base64.b64decode(ciphertext.encode('utf-8'))
        
        # 分離IV和密文
        iv = encrypted_data[:16]
        ciphertext_bytes = encrypted_data[16:]
        
        # 創建解密器
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        
        # 解密和去填充
        padded_data = cipher.decrypt(ciphertext_bytes)
        plaintext = unpad(padded_data, AES.block_size)
        
        return plaintext.decode('utf-8')
    
    def _encrypt_gcm(self, plaintext: str) -> str:
        """GCM模式加密"""
        # 生成隨機nonce
        nonce = get_random_bytes(12)
        
        # 創建加密器
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=nonce)
        
        # 加密
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        # 組合nonce、tag和密文
        encrypted_data = nonce + tag + ciphertext
        
        # Base64編碼
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def _decrypt_gcm(self, ciphertext: str) -> str:
        """GCM模式解密"""
        # Base64解碼
        encrypted_data = base64.b64decode(ciphertext.encode('utf-8'))
        
        # 分離nonce、tag和密文
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext_bytes = encrypted_data[28:]
        
        # 創建解密器
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=nonce)
        
        # 解密和驗證
        plaintext = cipher.decrypt_and_verify(ciphertext_bytes, tag)
        
        return plaintext.decode('utf-8')

class TokenGenerator:
    """令牌生成器"""
    
    @staticmethod
    def generate_api_token(length: int = 32) -> str:
        """生成API令牌"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_session_token(length: int = 24) -> str:
        """生成會話令牌"""
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_order_id(prefix: str = 'SP') -> str:
        """生成訂單ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(4).upper()
        return f"{prefix}{timestamp}{random_part}"
    
    @staticmethod
    def generate_transaction_id(prefix: str = 'TXN') -> str:
        """生成交易ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(6).upper()
        return f"{prefix}{timestamp}{random_part}"
    
    @staticmethod
    def generate_reference_id(length: int = 16) -> str:
        """生成參考ID"""
        return secrets.token_hex(length).upper()

class SecurityValidator:
    """安全驗證器"""
    
    @staticmethod
    def validate_amount(amount: Union[str, float, int]) -> bool:
        """驗證金額格式"""
        try:
            amount_float = float(amount)
            return amount_float > 0 and amount_float <= 999999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_currency(currency: str) -> bool:
        """驗證貨幣代碼"""
        valid_currencies = ['TWD', 'USD', 'CNY', 'HKD', 'JPY']
        return currency.upper() in valid_currencies
    
    @staticmethod
    def validate_order_id(order_id: str) -> bool:
        """驗證訂單ID格式"""
        if not order_id or len(order_id) < 8 or len(order_id) > 64:
            return False
        
        # 只允許字母、數字、連字符和下劃線
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, order_id))
    
    @staticmethod
    def validate_merchant_id(merchant_id: str) -> bool:
        """驗證商戶ID格式"""
        if not merchant_id or len(merchant_id) < 4 or len(merchant_id) > 32:
            return False
        
        import re
        pattern = r'^[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, merchant_id))
    
    @staticmethod
    def validate_callback_url(url: str) -> bool:
        """驗證回調URL格式"""
        if not url:
            return False
        
        import re
        pattern = r'^https?://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/.*)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """清理字符串"""
        if not text:
            return ''
        
        # 移除危險字符
        import re
        sanitized = re.sub(r'[<>"\'\\\/]', '', str(text))
        
        # 限制長度
        return sanitized[:max_length]
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', 
                          show_first: int = 2, show_last: int = 2) -> str:
        """遮罩敏感數據"""
        if not data or len(data) <= show_first + show_last:
            return mask_char * len(data) if data else ''
        
        first_part = data[:show_first]
        last_part = data[-show_last:] if show_last > 0 else ''
        middle_part = mask_char * (len(data) - show_first - show_last)
        
        return first_part + middle_part + last_part

# 便捷函數

def create_signature_tool(api_secret: str, algorithm: str = 'sha256') -> SpeedPaySignature:
    """創建簽名工具"""
    return SpeedPaySignature(api_secret, algorithm)

def create_hmac_tool(secret_key: str, algorithm: str = 'sha256') -> SpeedPayHMAC:
    """創建HMAC工具"""
    return SpeedPayHMAC(secret_key, algorithm)

def create_encryption_tool(encryption_key: str, algorithm: str = 'aes-256-cbc') -> SpeedPayEncryption:
    """創建加密工具"""
    return SpeedPayEncryption(encryption_key, algorithm)

def quick_sign(data: Dict[str, Any], api_secret: str, algorithm: str = 'sha256') -> str:
    """快速簽名"""
    signer = SpeedPaySignature(api_secret, algorithm)
    return signer.generate_signature(data)

def quick_verify(data: Dict[str, Any], signature: str, api_secret: str, 
                algorithm: str = 'sha256', timestamp_tolerance: int = 300) -> bool:
    """快速驗證"""
    signer = SpeedPaySignature(api_secret, algorithm)
    return signer.verify_signature(data, signature, timestamp_tolerance=timestamp_tolerance)

def generate_secure_token(length: int = 32) -> str:
    """生成安全令牌"""
    return TokenGenerator.generate_api_token(length)

def mask_card_number(card_number: str) -> str:
    """遮罩信用卡號"""
    return SecurityValidator.mask_sensitive_data(card_number, show_first=4, show_last=4)

def mask_phone_number(phone: str) -> str:
    """遮罩電話號碼"""
    return SecurityValidator.mask_sensitive_data(phone, show_first=3, show_last=3)