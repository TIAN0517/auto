#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最高階自動贊助系統 - 後端主程序
4D科技風格 - FastAPI + Uvicorn 實現
版本: 1.0.0
作者: AI Assistant
日期: 2024
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Pydantic 模型
from pydantic import BaseModel, EmailStr, field_validator

# 資料庫相關
import aiomysql
# import aioredis  # 暫時註解掉，因為版本相容性問題
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from databases import Database

# 安全相關
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

# 任務調度
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# 其他工具
import json
import uuid
import hashlib
import secrets
from decimal import Decimal
from enum import Enum

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 配置類
class Settings:
    # 應用配置
    APP_NAME = "最高階自動贊助系統"
    APP_VERSION = "1.0.0"
    DEBUG = True
    
    # 服務器配置
    HOST = "localhost"
    PORT = 8080
    WS_PORT = 8081
    
    # 資料庫配置
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASSWORD = "password"
    DB_NAME = "sponsor_system"
    
    # Redis配置
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    
    # JWT配置
    SECRET_KEY = "your-secret-key-here-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # 安全配置
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    
    # 速買配置
    QUICK_BUY_TIMEOUT = 30  # 秒
    MAX_QUICK_BUY_AMOUNT = 100
    
    @property
    def database_url(self):
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_url(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # 開發模式：跳過資料庫連接
    SKIP_DB = True

settings = Settings()

# 資料庫模型
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # 統計字段
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    quick_buy_success = Column(Integer, default=0)
    quick_buy_failed = Column(Integer, default=0)

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String(50))
    image = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_quick_buy = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    is_quick_buy = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    default_payment_method = Column(String(50), default="balance")
    quick_buy_enabled = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    theme = Column(String(20), default="4d-tech")
    language = Column(String(10), default="zh-TW")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QuickBuyStats(Base):
    __tablename__ = "quick_buy_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    total_amount = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    last_purchase = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    description = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic 模型
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用戶名長度必須在3-50字符之間')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密碼長度至少6個字符')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    balance: float
    is_active: bool
    total_orders: int
    total_spent: float
    quick_buy_success: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    image: Optional[str] = None
    is_quick_buy: bool = False

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    category: Optional[str]
    image: Optional[str]
    is_active: bool
    is_quick_buy: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    item_id: int
    amount: int
    payment_method: str = "balance"
    quick_buy: bool = False

class OrderResponse(BaseModel):
    id: int
    order_id: str
    user_id: int
    item_id: int
    amount: int
    total_price: float
    payment_method: str
    status: str
    is_quick_buy: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PreferencesUpdate(BaseModel):
    default_payment_method: Optional[str] = None
    quick_buy_enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None

# 資料庫連接管理
class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.database = None
        self.redis = None
        self.session_maker = None
    
    async def connect(self):
        try:
            # 開發模式：跳過資料庫連接
            if settings.SKIP_DB:
                logger.info("開發模式：跳過資料庫連接")
                return
                
            # MySQL 連接
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.DEBUG,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.database = Database(settings.database_url)
            await self.database.connect()
            
            # Redis 連接
            # self.redis = await aioredis.from_url(
            #     settings.redis_url,
            #     encoding="utf-8",
            #     decode_responses=True
            # )
            
            logger.info("資料庫連接成功")
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise
    
    async def disconnect(self):
        try:
            if self.database:
                await self.database.disconnect()
            if self.redis:
                await self.redis.close()
            if self.engine:
                await self.engine.dispose()
            logger.info("資料庫連接已關閉")
        except Exception as e:
            logger.error(f"關閉資料庫連接時發生錯誤: {e}")
    
    async def get_session(self):
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

# 實例化資料庫管理器
db_manager = DatabaseManager()

# 密碼加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的認證憑證",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 依賴注入
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = verify_token(credentials.credentials)
    
    query = "SELECT * FROM users WHERE id = :user_id AND is_active = 1"
    user = await db_manager.database.fetch_one(query=query, values={"user_id": user_id})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在或已被停用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return dict(user)

# WebSocket 連接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"用戶 {user_id} WebSocket 已連接")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"用戶 {user_id} WebSocket 已斷開")
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"發送消息給用戶 {user_id} 失敗: {e}")
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict):
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"廣播消息給用戶 {user_id} 失敗: {e}")
                disconnected_users.append(user_id)
        
        # 清理斷開的連接
        for user_id in disconnected_users:
            self.disconnect(user_id)

manager = ConnectionManager()

# 速買管理器
class QuickBuyManager:
    def __init__(self):
        self.processing_orders = set()
    
    async def process_quick_buy(self, user_id: int, item_id: int, amount: int, payment_method: str):
        # 生成唯一訂單ID
        order_id = f"QB{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(1000):03d}"
        
        # 檢查是否正在處理
        if order_id in self.processing_orders:
            raise HTTPException(status_code=400, detail="訂單正在處理中")
        
        self.processing_orders.add(order_id)
        
        try:
            # 開始事務
            async with db_manager.session_maker() as session:
                # 檢查商品
                item_query = "SELECT * FROM items WHERE id = :item_id AND is_active = 1"
                item = await db_manager.database.fetch_one(
                    query=item_query, 
                    values={"item_id": item_id}
                )
                
                if not item:
                    raise HTTPException(status_code=404, detail="商品不存在")
                
                if item['stock'] < amount:
                    raise HTTPException(status_code=400, detail="庫存不足")
                
                # 檢查用戶餘額
                user_query = "SELECT * FROM users WHERE id = :user_id AND is_active = 1"
                user = await db_manager.database.fetch_one(
                    query=user_query,
                    values={"user_id": user_id}
                )
                
                if not user:
                    raise HTTPException(status_code=404, detail="用戶不存在")
                
                total_price = item['price'] * amount
                
                if payment_method == "balance" and user['balance'] < total_price:
                    raise HTTPException(status_code=400, detail="餘額不足")
                
                # 創建訂單
                order_insert = """
                    INSERT INTO orders (order_id, user_id, item_id, amount, total_price, 
                                      payment_method, status, is_quick_buy, created_at)
                    VALUES (:order_id, :user_id, :item_id, :amount, :total_price, 
                           :payment_method, 'processing', 1, :created_at)
                """
                
                await db_manager.database.execute(
                    query=order_insert,
                    values={
                        "order_id": order_id,
                        "user_id": user_id,
                        "item_id": item_id,
                        "amount": amount,
                        "total_price": total_price,
                        "payment_method": payment_method,
                        "created_at": datetime.utcnow()
                    }
                )
                
                # 扣除庫存
                stock_update = "UPDATE items SET stock = stock - :amount WHERE id = :item_id"
                await db_manager.database.execute(
                    query=stock_update,
                    values={"amount": amount, "item_id": item_id}
                )
                
                # 扣除餘額（如果使用餘額支付）
                if payment_method == "balance":
                    balance_update = "UPDATE users SET balance = balance - :amount WHERE id = :user_id"
                    await db_manager.database.execute(
                        query=balance_update,
                        values={"amount": total_price, "user_id": user_id}
                    )
                
                # 更新用戶統計
                stats_update = """
                    UPDATE users SET 
                        total_orders = total_orders + 1,
                        total_spent = total_spent + :total_price,
                        quick_buy_success = quick_buy_success + 1
                    WHERE id = :user_id
                """
                await db_manager.database.execute(
                    query=stats_update,
                    values={"total_price": total_price, "user_id": user_id}
                )
                
                # 更新速買統計
                await self.update_quick_buy_stats(user_id, item_id, amount, total_price, True)
                
                # 完成訂單
                order_complete = """
                    UPDATE orders SET status = 'completed', completed_at = :completed_at 
                    WHERE order_id = :order_id
                """
                await db_manager.database.execute(
                    query=order_complete,
                    values={"order_id": order_id, "completed_at": datetime.utcnow()}
                )
                
                # 記錄活動日誌
                await self.log_activity(
                    user_id, 
                    "quick_buy", 
                    f"速買成功: {item['name']} x{amount}"
                )
                
                # 發送WebSocket通知
                await manager.send_personal_message({
                    "type": "quick_buy_result",
                    "payload": {
                        "success": True,
                        "orderId": order_id,
                        "message": "速買成功！",
                        "totalPrice": total_price
                    }
                }, user_id)
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "total_price": total_price,
                    "message": "速買成功！"
                }
                
        except Exception as e:
            # 記錄錯誤
            await self.update_quick_buy_stats(user_id, item_id, amount, 0, False)
            await self.log_activity(
                user_id, 
                "quick_buy_failed", 
                f"速買失敗: {str(e)}"
            )
            
            # 發送WebSocket通知
            await manager.send_personal_message({
                "type": "quick_buy_result",
                "payload": {
                    "success": False,
                    "message": str(e)
                }
            }, user_id)
            
            raise e
        
        finally:
            self.processing_orders.discard(order_id)
    
    async def update_quick_buy_stats(self, user_id: int, item_id: int, amount: int, total_spent: float, success: bool):
        # 檢查是否存在統計記錄
        check_query = "SELECT id FROM quick_buy_stats WHERE user_id = :user_id AND item_id = :item_id"
        existing = await db_manager.database.fetch_one(
            query=check_query,
            values={"user_id": user_id, "item_id": item_id}
        )
        
        if existing:
            # 更新現有記錄
            if success:
                update_query = """
                    UPDATE quick_buy_stats SET 
                        success_count = success_count + 1,
                        total_amount = total_amount + :amount,
                        total_spent = total_spent + :total_spent,
                        last_purchase = :last_purchase,
                        updated_at = :updated_at
                    WHERE user_id = :user_id AND item_id = :item_id
                """
            else:
                update_query = """
                    UPDATE quick_buy_stats SET 
                        failed_count = failed_count + 1,
                        updated_at = :updated_at
                    WHERE user_id = :user_id AND item_id = :item_id
                """
            
            values = {
                "user_id": user_id,
                "item_id": item_id,
                "updated_at": datetime.utcnow()
            }
            
            if success:
                values.update({
                    "amount": amount,
                    "total_spent": total_spent,
                    "last_purchase": datetime.utcnow()
                })
            
            await db_manager.database.execute(query=update_query, values=values)
        else:
            # 創建新記錄
            insert_query = """
                INSERT INTO quick_buy_stats 
                (user_id, item_id, success_count, failed_count, total_amount, total_spent, last_purchase, created_at)
                VALUES (:user_id, :item_id, :success_count, :failed_count, :total_amount, :total_spent, :last_purchase, :created_at)
            """
            
            values = {
                "user_id": user_id,
                "item_id": item_id,
                "success_count": 1 if success else 0,
                "failed_count": 0 if success else 1,
                "total_amount": amount if success else 0,
                "total_spent": total_spent if success else 0,
                "last_purchase": datetime.utcnow() if success else None,
                "created_at": datetime.utcnow()
            }
            
            await db_manager.database.execute(query=insert_query, values=values)
    
    async def log_activity(self, user_id: int, action: str, description: str, ip_address: str = None, user_agent: str = None):
        insert_query = """
            INSERT INTO activity_logs (user_id, action, description, ip_address, user_agent, created_at)
            VALUES (:user_id, :action, :description, :ip_address, :user_agent, :created_at)
        """
        
        await db_manager.database.execute(
            query=insert_query,
            values={
                "user_id": user_id,
                "action": action,
                "description": description,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow()
            }
        )

quick_buy_manager = QuickBuyManager()

# 應用程序生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    logger.info("啟動最高階自動贊助系統...")
    
    # 創建日誌目錄
    os.makedirs("logs", exist_ok=True)
    
    # 連接資料庫
    await db_manager.connect()
    
    # 啟動任務調度器
    scheduler = AsyncIOScheduler()
    
    # 添加定期任務
    scheduler.add_job(
        func=cleanup_expired_sessions,
        trigger=IntervalTrigger(minutes=30),
        id='cleanup_sessions',
        name='清理過期會話'
    )
    
    scheduler.add_job(
        func=update_system_stats,
        trigger=IntervalTrigger(minutes=5),
        id='update_stats',
        name='更新系統統計'
    )
    
    scheduler.start()
    logger.info("系統啟動完成")
    
    yield
    
    # 關閉時執行
    logger.info("🔄 正在關閉系統...")
    scheduler.shutdown()
    await db_manager.disconnect()
    logger.info("系統已安全關閉")

# 創建FastAPI應用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="4D科技風格的最高階自動贊助系統",
    lifespan=lifespan
)

# 添加中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 靜態文件服務
import os
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# 定期任務函數
async def cleanup_expired_sessions():
    """清理過期的Redis會話"""
    try:
        # 這裡可以添加清理邏輯
        logger.info("執行會話清理任務")
    except Exception as e:
        logger.error(f"會話清理任務失敗: {e}")

async def update_system_stats():
    """更新系統統計信息"""
    try:
        # 計算在線用戶數
        online_users = len(manager.active_connections)
        
        # 計算今日訂單數 - 檢查資料庫連接
        today_orders_count = 0
        if db_manager.database is not None:
            today = datetime.now().date()
            today_orders_query = """
                SELECT COUNT(*) as count FROM orders 
                WHERE DATE(created_at) = :today
            """
            today_orders = await db_manager.database.fetch_one(
                query=today_orders_query,
                values={"today": today}
            )
            today_orders_count = today_orders['count'] if today_orders else 0
        
        # 存儲統計信息
        stats = {
            "online_users": online_users,
            "today_orders": today_orders_count,
            "system_load": "正常",
            "last_update": datetime.utcnow().isoformat()
        }
        
        # 如果Redis可用則存儲
        if hasattr(db_manager, 'redis') and db_manager.redis is not None:
            await db_manager.redis.set("system_stats", json.dumps(stats))
        
        # 廣播系統狀態更新
        await manager.broadcast({
            "type": "system_status",
            "payload": {
                "status": "online",
                "stats": stats
            }
        })
        
    except Exception as e:
        logger.error(f"更新系統統計失敗: {e}")

# API 路由
@app.get("/")
async def root():
    return {
        "message": "歡迎使用最高階自動贊助系統",
        "version": settings.APP_VERSION,
        "status": "online",
        "features": ["速買功能", "4D科技風格", "實時通信", "智能自動化"]
    }

@app.get("/api/health")
@app.head("/api/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }

@app.get("/health")
async def simple_health_check():
    try:
        # 檢查資料庫連接
        await db_manager.database.fetch_one("SELECT 1")
        
        # 檢查Redis連接
        await db_manager.redis.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "redis": "connected",
            "websocket_connections": len(manager.active_connections)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# 認證相關路由
@app.post("/api/auth/register")
async def register(user: UserCreate):
    # 檢查用戶是否已存在
    existing_user = await db_manager.database.fetch_one(
        query="SELECT id FROM users WHERE email = :email OR username = :username",
        values={"email": user.email, "username": user.username}
    )
    
    if existing_user:
        raise HTTPException(status_code=400, detail="用戶已存在")
    
    # 創建新用戶
    hashed_password = get_password_hash(user.password)
    
    query = """
        INSERT INTO users (username, email, password_hash, created_at)
        VALUES (:username, :email, :password_hash, :created_at)
    """
    
    user_id = await db_manager.database.execute(
        query=query,
        values={
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow()
        }
    )
    
    # 創建用戶偏好設置
    prefs_query = """
        INSERT INTO user_preferences (user_id, created_at)
        VALUES (:user_id, :created_at)
    """
    
    await db_manager.database.execute(
        query=prefs_query,
        values={"user_id": user_id, "created_at": datetime.utcnow()}
    )
    
    return {"success": True, "message": "註冊成功"}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # 查找用戶
    db_user = await db_manager.database.fetch_one(
        query="SELECT * FROM users WHERE email = :email AND is_active = 1",
        values={"email": user.email}
    )
    
    if not db_user or not verify_password(user.password, db_user['password_hash']):
        raise HTTPException(status_code=400, detail="郵箱或密碼錯誤")
    
    # 更新最後登入時間
    await db_manager.database.execute(
        query="UPDATE users SET last_login = :last_login WHERE id = :user_id",
        values={"last_login": datetime.utcnow(), "user_id": db_user['id']}
    )
    
    # 創建訪問令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user['id'])}, expires_delta=access_token_expires
    )
    
    # 記錄登入活動
    await quick_buy_manager.log_activity(
        db_user['id'], "login", "用戶登入"
    )
    
    return {
        "success": True,
        "data": {
            "token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(db_user)
        }
    }

@app.get("/api/auth/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "user": UserResponse(**current_user)
        }
    }

# 商品相關路由
@app.get("/api/items", response_model=List[ItemResponse])
async def get_items(skip: int = 0, limit: int = 100):
    query = "SELECT * FROM items WHERE is_active = 1 ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
    items = await db_manager.database.fetch_all(
        query=query,
        values={"limit": limit, "skip": skip}
    )
    return [ItemResponse(**dict(item)) for item in items]

@app.get("/api/items/quick-buy", response_model=List[ItemResponse])
async def get_quick_buy_items():
    query = "SELECT * FROM items WHERE is_active = 1 AND is_quick_buy = 1 ORDER BY created_at DESC"
    items = await db_manager.database.fetch_all(query=query)
    return [ItemResponse(**dict(item)) for item in items]

@app.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    query = "SELECT * FROM items WHERE id = :item_id AND is_active = 1"
    item = await db_manager.database.fetch_one(
        query=query,
        values={"item_id": item_id}
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ItemResponse(**dict(item))

# 訂單相關路由
@app.post("/api/orders/quick-buy")
async def create_quick_buy_order(
    order: OrderCreate,
    current_user: dict = Depends(get_current_user)
):
    if not order.quick_buy:
        raise HTTPException(status_code=400, detail="這不是速買訂單")
    
    if order.amount <= 0 or order.amount > settings.MAX_QUICK_BUY_AMOUNT:
        raise HTTPException(status_code=400, detail=f"購買數量必須在1-{settings.MAX_QUICK_BUY_AMOUNT}之間")
    
    result = await quick_buy_manager.process_quick_buy(
        user_id=current_user['id'],
        item_id=order.item_id,
        amount=order.amount,
        payment_method=order.payment_method
    )
    
    return {"success": True, "data": result}

@app.get("/api/orders", response_model=List[OrderResponse])
async def get_user_orders(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    query = """
        SELECT * FROM orders 
        WHERE user_id = :user_id 
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :skip
    """
    
    orders = await db_manager.database.fetch_all(
        query=query,
        values={"user_id": current_user['id'], "limit": limit, "skip": skip}
    )
    
    return [OrderResponse(**dict(order)) for order in orders]

# 用戶偏好設置路由
@app.get("/api/user/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    query = "SELECT * FROM user_preferences WHERE user_id = :user_id"
    prefs = await db_manager.database.fetch_one(
        query=query,
        values={"user_id": current_user['id']}
    )
    
    if not prefs:
        # 創建默認偏好設置
        insert_query = """
            INSERT INTO user_preferences (user_id, created_at)
            VALUES (:user_id, :created_at)
        """
        await db_manager.database.execute(
            query=insert_query,
            values={"user_id": current_user['id'], "created_at": datetime.utcnow()}
        )
        
        prefs = await db_manager.database.fetch_one(
            query=query,
            values={"user_id": current_user['id']}
        )
    
    return {"success": True, "data": dict(prefs)}

@app.put("/api/user/preferences")
async def update_user_preferences(
    preferences: PreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    # 構建更新查詢
    update_fields = []
    values = {"user_id": current_user['id'], "updated_at": datetime.utcnow()}
    
    for field, value in preferences.dict(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            values[field] = value
    
    if update_fields:
        query = f"""
            UPDATE user_preferences 
            SET {', '.join(update_fields)}, updated_at = :updated_at
            WHERE user_id = :user_id
        """
        
        await db_manager.database.execute(query=query, values=values)
    
    return {"success": True, "message": "偏好設置已更新"}

# 支付方式路由
@app.get("/api/payment/methods")
async def get_payment_methods():
    methods = [
        {
            "id": "balance",
            "name": "帳戶餘額",
            "description": "使用帳戶餘額支付",
            "icon": "fas fa-wallet",
            "enabled": True
        },
        {
            "id": "credit_card",
            "name": "信用卡",
            "description": "使用信用卡支付",
            "icon": "fas fa-credit-card",
            "enabled": False
        },
        {
            "id": "paypal",
            "name": "PayPal",
            "description": "使用PayPal支付",
            "icon": "fab fa-paypal",
            "enabled": False
        }
    ]
    
    return {"success": True, "data": methods}

# 統計相關路由
@app.get("/api/stats/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    # 獲取系統統計
    system_stats_raw = await db_manager.redis.get("system_stats")
    system_stats = json.loads(system_stats_raw) if system_stats_raw else {}
    
    # 獲取用戶最近活動
    activities_query = """
        SELECT action, description, created_at 
        FROM activity_logs 
        WHERE user_id = :user_id 
        ORDER BY created_at DESC 
        LIMIT 10
    """
    
    activities = await db_manager.database.fetch_all(
        query=activities_query,
        values={"user_id": current_user['id']}
    )
    
    recent_activities = [
        {
            "type": activity['action'],
            "message": activity['description'],
            "timestamp": activity['created_at'].isoformat()
        }
        for activity in activities
    ]
    
    return {
        "success": True,
        "data": {
            "onlineUsers": system_stats.get("online_users", 0),
            "todayOrders": system_stats.get("today_orders", 0),
            "systemLoad": system_stats.get("system_load", "正常"),
            "recentActivities": recent_activities
        }
    }

# WebSocket 路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    if not token:
        await websocket.close(code=1008, reason="需要認證令牌")
        return
    
    try:
        user_id = verify_token(token)
        await manager.connect(websocket, user_id)
        
        # 發送歡迎消息
        await manager.send_personal_message({
            "type": "notification",
            "payload": {
                "message": "WebSocket連接成功！",
                "type": "success"
            }
        }, user_id)
        
        while True:
            # 保持連接活躍
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 處理客戶端消息
            if message.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "payload": {"timestamp": datetime.utcnow().isoformat()}
                }, user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket錯誤: {e}")
        manager.disconnect(user_id)
        await websocket.close(code=1011, reason="服務器錯誤")

# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"未處理的異常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "內部服務器錯誤",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# USDT支付相關路由
@app.get("/api/usdt/networks")
async def get_usdt_networks():
    """獲取支持的USDT網絡"""
    try:
        from usdt_service import USDTPaymentService
        usdt_service = USDTPaymentService()
        networks = usdt_service.get_supported_networks()
        return {"success": True, "data": networks}
    except Exception as e:
        logger.error(f"獲取USDT網絡失敗: {e}")
        return {"success": False, "message": "獲取網絡信息失敗"}

@app.post("/api/usdt/create-order")
async def create_usdt_order(request: Request):
    """創建USDT支付訂單"""
    try:
        data = await request.json()
        amount = data.get('amount')
        network = data.get('network', 'trc20')  # 默認使用TRC-20
        
        if not amount or amount <= 0:
            return {"success": False, "message": "無效的金額"}
        
        from usdt_service import USDTPaymentService
        usdt_service = USDTPaymentService()
        
        result = usdt_service.create_payment_order(
            amount=amount,
            network=network
        )
        
        return result
        
    except Exception as e:
        logger.error(f"創建USDT訂單失敗: {e}")
        return {"success": False, "message": "創建訂單失敗"}

@app.get("/api/usdt/status/{order_id}")
async def get_usdt_status(order_id: str):
    """獲取USDT支付狀態"""
    try:
        from usdt_service import USDTPaymentService
        usdt_service = USDTPaymentService()
        
        result = await usdt_service.check_payment_status(order_id)
        return result
        
    except Exception as e:
        logger.error(f"檢查USDT狀態失敗: {e}")
        return {"success": False, "message": "檢查狀態失敗"}

@app.post("/api/usdt/cancel/{order_id}")
async def cancel_usdt_order(order_id: str):
    """取消USDT訂單"""
    try:
        from usdt_service import USDTPaymentService
        usdt_service = USDTPaymentService()
        
        result = usdt_service.cancel_order(order_id)
        return result
        
    except Exception as e:
        logger.error(f"取消USDT訂單失敗: {e}")
        return {"success": False, "message": "取消訂單失敗"}

@app.get("/api/usdt/history")
async def get_usdt_history(limit: int = 50):
    """獲取USDT訂單歷史"""
    try:
        from usdt_service import USDTPaymentService
        usdt_service = USDTPaymentService()
        
        history = usdt_service.get_order_history(limit)
        return {"success": True, "data": history}
        
    except Exception as e:
        logger.error(f"獲取USDT歷史失敗: {e}")
        return {"success": False, "message": "獲取歷史失敗"}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"啟動服務器: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"WebSocket服務: ws://{settings.HOST}:{settings.WS_PORT}/ws")
    logger.info(f"健康檢查: http://{settings.HOST}:{settings.PORT}/health")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )