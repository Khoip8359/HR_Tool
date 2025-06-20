#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
JWT 相關的資料庫模型
包含用戶會話、Token 黑名單、登入記錄等功能
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta,timezone
import hashlib
import uuid
import json
import pytz

from flask import current_app

def get_timezone():
    """從配置獲取時區"""
    try:
        tz_name = current_app.config.get('TIMEZONE_CONFIG', {}).get('DEFAULT_TIMEZONE', 'Asia/Taipei')
        return pytz.timezone(tz_name)
    except:
        # 如果 Flask context 不可用，使用預設值
        return pytz.timezone('Asia/Taipei')

def get_local_now():
    """獲取本地時間"""
    return datetime.now(get_timezone())

def get_local_datetime():
    """獲取本地時間的 naive datetime（用於資料庫儲存）"""
    return get_local_now().replace(tzinfo=None)

Base = declarative_base()

class UserSession(Base):
    """用戶會話表 - 記錄活躍的 JWT Token"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    username = Column(String(50), nullable=False, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    
    # Token 資訊
    access_token_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash
    refresh_token_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash
    
    # 時間資訊
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 客戶端資訊
    ip_address = Column(String(45), nullable=True)  # 支援 IPv6
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)  # JSON 格式
    
    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)
    logout_reason = Column(String(50), nullable=True)  # manual, expired, force_logout
    logged_out_at = Column(DateTime, nullable=True)
    
    # 索引
    __table_args__ = (
        Index('idx_user_session_active', 'username', 'is_active'),
        Index('idx_user_session_expires', 'access_expires_at', 'refresh_expires_at'),
    )

class TokenBlacklist(Base):
    """Token 黑名單表"""
    __tablename__ = 'token_blacklist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hash
    token_type = Column(String(10), nullable=False)  # access, refresh
    
    # 相關資訊
    username = Column(String(50), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    
    # 時間資訊
    blacklisted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # 黑名單原因
    reason = Column(String(50), nullable=False)  # logout, expired, force_revoke, security
    blacklisted_by = Column(String(50), nullable=True)  # 誰加入黑名單（管理員操作時）
    
    # 索引
    __table_args__ = (
        Index('idx_token_blacklist_expires', 'expires_at'),
        Index('idx_token_blacklist_user', 'username', 'blacklisted_at'),
    )

class LoginHistory(Base):
    """登入歷史記錄表"""
    __tablename__ = 'login_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    
    # 登入資訊
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    logout_time = Column(DateTime, nullable=True)
    session_duration = Column(Integer, nullable=True)  # 秒數
    
    # 認證方式
    auth_method = Column(String(20), default='ad', nullable=False)  # ad, manual, sso
    auth_server = Column(String(100), nullable=True)  # AD 伺服器 IP
    auth_domain = Column(String(50), nullable=True)   # AD 網域
    
    # 客戶端資訊
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)  # JSON 格式
    location_info = Column(Text, nullable=True)  # JSON 格式（地理位置）
    
    # 狀態
    login_successful = Column(Boolean, default=True, nullable=False)
    logout_reason = Column(String(50), nullable=True)
    failure_reason = Column(String(100), nullable=True)  # 登入失敗原因
    
    # 會話 ID
    session_id = Column(String(36), nullable=True, index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_login_history_user_time', 'username', 'login_time'),
        Index('idx_login_history_success', 'login_successful', 'login_time'),
        Index('idx_login_history_ip', 'ip_address', 'login_time'),
    )

class UserLoginAttempt(Base):
    """用戶登入嘗試表（安全監控）"""
    __tablename__ = 'user_login_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    
    # 嘗試資訊
    attempt_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_successful = Column(Boolean, default=False, nullable=False)
    failure_reason = Column(String(100), nullable=True)
    
    # 客戶端資訊
    user_agent = Column(Text, nullable=True)
    
    # 安全標記
    is_suspicious = Column(Boolean, default=False, nullable=False)
    blocked_until = Column(DateTime, nullable=True)  # 暫時封鎖到什麼時候
    
    # 索引
    __table_args__ = (
        Index('idx_login_attempts_user_time', 'username', 'attempt_time'),
        Index('idx_login_attempts_ip_time', 'ip_address', 'attempt_time'),
        Index('idx_login_attempts_suspicious', 'is_suspicious', 'attempt_time'),
    )

class JWTConfiguration(Base):
    """JWT 配置表（動態配置）"""
    __tablename__ = 'jwt_configuration'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), nullable=False)  # string, integer, boolean, json
    
    # 描述和分類
    description = Column(Text, nullable=True)
    category = Column(String(30), nullable=False, index=True)  # security, timing, feature
    
    # 變更記錄
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(50), nullable=True)
    
    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

# JWT 資料庫管理類
class JWTDatabaseManager:
    """JWT 資料庫管理器"""
    
    def __init__(self, db_manager):
        """
        初始化 JWT 資料庫管理器
        
        Args:
            db_manager: FlaskDatabaseManager 實例
        """
        self.db_manager = db_manager
        self.pool_name = 'mysql_hr'  # 使用哪個連接池
         
    def create_tables(self):
        """創建 JWT 相關表格"""
        try:
            pool = self.db_manager.get_pool(self.pool_name)
            Base.metadata.create_all(pool.engine)
            return True
        except Exception as e:
            raise Exception(f"創建 JWT 表格失敗: {str(e)}")
    
    def hash_token(self, token: str) -> str:
        """計算 Token 的 SHA256 hash"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def create_user_session(self, username: str, user_id: str, access_token: str, 
                          refresh_token: str, access_expires_at: datetime, 
                          refresh_expires_at: datetime, ip_address: str = None, 
                          user_agent: str = None, device_info: dict = None) -> str:
        """
        創建用戶會話記錄
        
        Returns:
            str: session_id
        """
        with self.db_manager.get_session(self.pool_name) as session:
            session_id = str(uuid.uuid4())
            
            user_session = UserSession(
                session_id=session_id,
                username=username,
                user_id=user_id,
                access_token_hash=self.hash_token(access_token),
                refresh_token_hash=self.hash_token(refresh_token),
                access_expires_at=access_expires_at,
                refresh_expires_at=refresh_expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=json.dumps(device_info) if device_info else None
            )
            
            session.add(user_session)
            session.commit()
            return session_id
    
    def update_session_access_time(self, access_token: str):
        """更新會話最後訪問時間"""
        with self.db_manager.get_session(self.pool_name) as session:
            token_hash = self.hash_token(access_token)
            
            user_session = session.query(UserSession).filter(
                UserSession.access_token_hash == token_hash,
                UserSession.is_active == True
            ).first()
            
            if user_session:
                user_session.last_accessed_at = datetime.utcnow()
                session.commit()
    
    def deactivate_session(self, session_id: str = None, access_token: str = None, 
                          logout_reason: str = 'manual'):
        """停用用戶會話"""
        with self.db_manager.get_session(self.pool_name) as session:
            query = session.query(UserSession).filter(UserSession.is_active == True)
            
            if session_id:
                query = query.filter(UserSession.session_id == session_id)
            elif access_token:
                token_hash = self.hash_token(access_token)
                query = query.filter(UserSession.access_token_hash == token_hash)
            else:
                raise ValueError("必須提供 session_id 或 access_token")
            
            user_session = query.first()
            if user_session:
                user_session.is_active = False
                user_session.logout_reason = logout_reason
                user_session.logged_out_at = datetime.utcnow()
                session.commit()
                return True
            return False
    
    def blacklist_token(self, token: str, token_type: str, username: str, 
                       expires_at: datetime, reason: str = 'logout', 
                       blacklisted_by: str = None, session_id: str = None):
        """將 Token 加入黑名單"""
        with self.db_manager.get_session(self.pool_name) as session:
            token_hash = self.hash_token(token)
            
            # 檢查是否已存在
            existing = session.query(TokenBlacklist).filter(
                TokenBlacklist.token_hash == token_hash
            ).first()
            
            if not existing:
                blacklist_entry = TokenBlacklist(
                    token_hash=token_hash,
                    token_type=token_type,
                    username=username,
                    session_id=session_id,
                    expires_at=expires_at,
                    reason=reason,
                    blacklisted_by=blacklisted_by
                )
                session.add(blacklist_entry)
                session.commit()
    
    def is_token_blacklisted(self, token: str) -> bool:
        """檢查 Token 是否在黑名單中"""
        with self.db_manager.get_session(self.pool_name) as session:
            token_hash = self.hash_token(token)
            
            blacklisted = session.query(TokenBlacklist).filter(
                TokenBlacklist.token_hash == token_hash,
                TokenBlacklist.expires_at > datetime.utcnow()
            ).first()
            
            return blacklisted is not None
    
    def record_login_history(self, username: str, user_id: str, session_id: str,
                           login_successful: bool = True, auth_method: str = 'ad',
                           auth_server: str = None, auth_domain: str = None,
                           ip_address: str = None, user_agent: str = None,
                           device_info: dict = None, failure_reason: str = None):
        """記錄登入歷史"""
        with self.db_manager.get_session(self.pool_name) as session:
            login_record = LoginHistory(
                username=username,
                user_id=user_id,
                session_id=session_id,
                login_successful=login_successful,
                auth_method=auth_method,
                auth_server=auth_server,
                auth_domain=auth_domain,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=json.dumps(device_info) if device_info else None,
                failure_reason=failure_reason
            )
            session.add(login_record)
            session.commit()
    
    def record_login_attempt(self, username: str, ip_address: str, 
                           is_successful: bool = False, failure_reason: str = None,
                           user_agent: str = None):
        """記錄登入嘗試"""
        with self.db_manager.get_session(self.pool_name) as session:
            # 檢查是否為可疑活動
            recent_attempts = session.query(UserLoginAttempt).filter(
                UserLoginAttempt.username == username,
                UserLoginAttempt.ip_address == ip_address,
                UserLoginAttempt.attempt_time > datetime.utcnow() - timedelta(minutes=15),
                UserLoginAttempt.is_successful == False
            ).count()
            
            is_suspicious = recent_attempts >= 3  # 15分鐘內失敗3次視為可疑
            
            attempt = UserLoginAttempt(
                username=username,
                ip_address=ip_address,
                is_successful=is_successful,
                failure_reason=failure_reason,
                user_agent=user_agent,
                is_suspicious=is_suspicious
            )
            session.add(attempt)
            session.commit()
    
    def get_user_active_sessions(self, username: str):
        """獲取用戶的活躍會話"""
        with self.db_manager.get_session(self.pool_name) as session:
            sessions = session.query(UserSession).filter(
                UserSession.username == username,
                UserSession.is_active == True,
                UserSession.refresh_expires_at > datetime.utcnow()
            ).order_by(UserSession.last_accessed_at.desc()).all()
            
            return [{
                'session_id': s.session_id,
                'created_at': s.created_at.isoformat(),
                'last_accessed_at': s.last_accessed_at.isoformat(),
                'ip_address': s.ip_address,
                'device_info': json.loads(s.device_info) if s.device_info else None,
                'expires_at': s.refresh_expires_at.isoformat()
            } for s in sessions]
    
    def cleanup_expired_records(self):
        """清理過期記錄"""
        with self.db_manager.get_session(self.pool_name) as session:
            now = datetime.utcnow()
            
            # 清理過期的黑名單記錄
            expired_blacklist = session.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at < now
            ).delete()
            
            # 停用過期的會話
            expired_sessions = session.query(UserSession).filter(
                UserSession.is_active == True,
                UserSession.refresh_expires_at < now
            ).update({
                'is_active': False,
                'logout_reason': 'expired',
                'logged_out_at': now
            })
            
            # 清理舊的登入嘗試記錄（保留30天）
            old_attempts = session.query(UserLoginAttempt).filter(
                UserLoginAttempt.attempt_time < now - timedelta(days=30)
            ).delete()
            
            session.commit()
            
            return {
                'expired_blacklist': expired_blacklist,
                'expired_sessions': expired_sessions,
                'old_attempts': old_attempts
            }
    
    def get_security_stats(self):
        """獲取安全統計"""
        with self.db_manager.get_session(self.pool_name) as session:
            now = datetime.utcnow()
            
            # 活躍會話數
            active_sessions = session.query(UserSession).filter(
                UserSession.is_active == True
            ).count()
            
            # 今日登入次數
            today_logins = session.query(LoginHistory).filter(
                LoginHistory.login_time >= now.replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            # 黑名單 Token 數
            blacklisted_tokens = session.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at > now
            ).count()
            
            # 可疑登入嘗試數（過去24小時）
            suspicious_attempts = session.query(UserLoginAttempt).filter(
                UserLoginAttempt.is_suspicious == True,
                UserLoginAttempt.attempt_time > now - timedelta(hours=24)
            ).count()
            
            return {
                'active_sessions': active_sessions,
                'today_logins': today_logins,
                'blacklisted_tokens': blacklisted_tokens,
                'suspicious_attempts_24h': suspicious_attempts,
                'query_time': now.isoformat()
            }