#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
增強的 JWT 認證擴展模組
整合資料庫會話管理功能
"""
import jwt
import datetime
from functools import wraps
from flask import Flask, request, jsonify, current_app, g
from typing import Optional, Dict, Any, List
# import logging
import secrets
import hashlib
from app.models.jwt_models import JWTDatabaseManager
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱


# logger = logging.getLogger(__name__)

class EnhancedJWTManager:
    """增強的 JWT Token 管理器（含資料庫支援）"""
    
    def __init__(self, app: Optional[Flask] = None, db_manager=None):
        self.app = app
        self.db_manager = db_manager
        self.jwt_db = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化 Flask 應用程式"""
        self.app = app
        
        # 設置預設配置
        app.config.setdefault('JWT_SECRET_KEY', self._generate_secret_key())
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', datetime.timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', datetime.timedelta(days=30))
        app.config.setdefault('JWT_TOKEN_LOCATION', ['headers'])
        app.config.setdefault('JWT_HEADER_NAME', 'Authorization')
        app.config.setdefault('JWT_HEADER_TYPE', 'Bearer')
        app.config.setdefault('JWT_BLACKLIST_ENABLED', True)
        app.config.setdefault('JWT_DATABASE_ENABLED', True)
        app.config.setdefault('JWT_SESSION_TRACKING', True)
        
        # 初始化資料庫管理器
        if self.db_manager:
            self.jwt_db = JWTDatabaseManager(self.db_manager)
            
            # 創建表格（如果不存在）
            try:
                self.jwt_db.create_tables()
                logger.info("JWT 資料庫表格初始化完成")
            except Exception as e:
                logger.error(f"JWT 資料庫表格初始化失敗: {str(e)}")
        
        # 將 JWT 管理器附加到應用程式
        app.extensions['enhanced_jwt_manager'] = self
        
        logger.info("增強的 JWT 管理器初始化完成")
    
    def _generate_secret_key(self) -> str:
        """生成安全的密鑰"""
        return secrets.token_urlsafe(32)
    
    def _get_client_info(self) -> Dict[str, Any]:
        """獲取客戶端信息"""
        return {
            'ip_address': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'device_info': self._parse_device_info()
        }
    
    def _get_client_ip(self) -> str:
        """獲取客戶端真實 IP"""
        # 檢查代理頭
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _parse_device_info(self) -> Dict[str, Any]:
        """解析設備信息"""
        user_agent = request.headers.get('User-Agent', '')
        
        device_info = {
            'user_agent': user_agent,
            'browser': 'unknown',
            'os': 'unknown',
            'device_type': 'unknown'
        }
        
        # 簡單的用戶代理解析
        user_agent_lower = user_agent.lower()
        
        # 瀏覽器檢測
        if 'chrome' in user_agent_lower:
            device_info['browser'] = 'Chrome'
        elif 'firefox' in user_agent_lower:
            device_info['browser'] = 'Firefox'
        elif 'safari' in user_agent_lower:
            device_info['browser'] = 'Safari'
        elif 'edge' in user_agent_lower:
            device_info['browser'] = 'Edge'
        
        # 作業系統檢測
        if 'windows' in user_agent_lower:
            device_info['os'] = 'Windows'
        elif 'macintosh' in user_agent_lower or 'mac os' in user_agent_lower:
            device_info['os'] = 'macOS'
        elif 'linux' in user_agent_lower:
            device_info['os'] = 'Linux'
        elif 'android' in user_agent_lower:
            device_info['os'] = 'Android'
        elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            device_info['os'] = 'iOS'
        
        # 設備類型檢測
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
            device_info['device_type'] = 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_info['device_type'] = 'tablet'
        else:
            device_info['device_type'] = 'desktop'
        
        return device_info
    
    def generate_tokens(self, user_data: Dict[str, Any], auth_info: Dict[str, Any] = None) -> Dict[str, str]:
        """
        生成訪問令牌和刷新令牌（含資料庫記錄）
        
        Args:
            user_data: 用戶數據
            auth_info: 認證信息（AD 伺服器等）
            
        Returns:
            dict: 包含 access_token、refresh_token 和 session_id 的字典
        """
        now = datetime.datetime.utcnow()
        
        # 確保配置值是 timedelta 對象
        access_expires_delta = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        refresh_expires_delta = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        
        # 如果配置是整數（秒），轉換為 timedelta
        if isinstance(access_expires_delta, int):
            access_expires_delta = datetime.timedelta(seconds=access_expires_delta)
        if isinstance(refresh_expires_delta, int):
            refresh_expires_delta = datetime.timedelta(seconds=refresh_expires_delta)
        
        access_expires = now + access_expires_delta
        refresh_expires = now + refresh_expires_delta
        
        # 生成會話 ID
        session_id = secrets.token_urlsafe(16)
        
        # 生成訪問令牌
        access_payload = {
            'username': user_data.get('username'),
            'user_id': user_data.get('user_id'),
            'session_id': session_id,
            'department': user_data.get('department'),
            'is_manager': user_data.get('is_manager', False),
            'permissions': user_data.get('permissions', []),
            'iat': now,
            'exp': access_expires,
            'type': 'access'
        }
        
        # 生成刷新令牌
        refresh_payload = {
            'username': user_data.get('username'),
            'user_id': user_data.get('user_id'),
            'session_id': session_id,
            'iat': now,
            'exp': refresh_expires,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        # 獲取客戶端信息
        client_info = self._get_client_info()
        
        # 記錄到資料庫
        if self.jwt_db and current_app.config.get('JWT_DATABASE_ENABLED', True):
            try:
                # 創建會話記錄
                db_session_id = self.jwt_db.create_user_session(
                    username=user_data.get('username'),
                    user_id=user_data.get('user_id'),
                    access_token=access_token,
                    refresh_token=refresh_token,
                    access_expires_at=access_expires,
                    refresh_expires_at=refresh_expires,
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent'],
                    device_info=client_info['device_info']
                )
                
                # 記錄登入歷史
                self.jwt_db.record_login_history(
                    username=user_data.get('username'),
                    user_id=user_data.get('user_id'),
                    session_id=db_session_id,
                    login_successful=True,
                    auth_method='ad',
                    auth_server=auth_info.get('server') if auth_info else None,
                    auth_domain=auth_info.get('domain') if auth_info else None,
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent'],
                    device_info=client_info['device_info']
                )
                
                # 記錄成功的登入嘗試
                self.jwt_db.record_login_attempt(
                    username=user_data.get('username'),
                    ip_address=client_info['ip_address'],
                    is_successful=True,
                    user_agent=client_info['user_agent']
                )
                
            except Exception as e:
                logger.error(f"記錄 JWT 會話到資料庫失敗: {str(e)}")
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(access_expires_delta.total_seconds()),
            'session_id': session_id
        }
    
    def record_failed_login(self, username: str, failure_reason: str):
        """記錄失敗的登入嘗試"""
        if self.jwt_db and current_app.config.get('JWT_DATABASE_ENABLED', True):
            try:
                client_info = self._get_client_info()
                self.jwt_db.record_login_attempt(
                    username=username,
                    ip_address=client_info['ip_address'],
                    is_successful=False,
                    failure_reason=failure_reason,
                    user_agent=client_info['user_agent']
                )
            except Exception as e:
                logger.error(f"記錄失敗登入嘗試失敗: {str(e)}")
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        驗證 JWT 令牌（含資料庫黑名單檢查）
        
        Args:
            token: JWT 令牌
            token_type: 令牌類型 ('access' 或 'refresh')
            
        Returns:
            dict or None: 解碼後的令牌數據，驗證失敗則返回 None
        """
        try:
            # 檢查資料庫黑名單
            if self.jwt_db and self.jwt_db.is_token_blacklisted(token):
                logger.warning("嘗試使用已加入資料庫黑名單的令牌")
                return None
            
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            # 檢查令牌類型
            if payload.get('type') != token_type:
                logger.warning(f"令牌類型不匹配: 期望 {token_type}, 實際 {payload.get('type')}")
                return None
            
            # 更新會話最後訪問時間
            if token_type == 'access' and self.jwt_db:
                try:
                    self.jwt_db.update_session_access_time(token)
                except Exception as e:
                    logger.error(f"更新會話訪問時間失敗: {str(e)}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT 令牌已過期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"無效的 JWT 令牌: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"JWT 令牌驗證錯誤: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        使用刷新令牌生成新的訪問令牌（含資料庫處理）
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            dict or None: 新的令牌組合，失敗則返回 None
        """
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        # 將舊的刷新令牌加入黑名單
        self.blacklist_token(
            token=refresh_token,
            token_type='refresh',
            username=payload.get('username'),
            reason='refresh'
        )
        
        # 停用舊會話
        if self.jwt_db:
            try:
                self.jwt_db.deactivate_session(
                    session_id=payload.get('session_id'),
                    logout_reason='token_refresh'
                )
            except Exception as e:
                logger.error(f"停用舊會話失敗: {str(e)}")
        
        # 生成新的令牌組合
        user_data = {
            'username': payload.get('username'),
            'user_id': payload.get('user_id')
        }
        
        return self.generate_tokens(user_data)
    
    def blacklist_token(self, token: str, token_type: str = 'access', 
                       username: str = None, reason: str = 'logout', 
                       blacklisted_by: str = None):
        """將令牌加入黑名單（資料庫版本）"""
        try:
            # 解碼 token 獲取過期時間和用戶信息
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']],
                options={"verify_exp": False}  # 不驗證過期時間
            )
            
            expires_at = datetime.datetime.fromtimestamp(payload.get('exp', 0))
            username = username or payload.get('username')
            session_id = payload.get('session_id')
            
            # 加入資料庫黑名單
            if self.jwt_db:
                self.jwt_db.blacklist_token(
                    token=token,
                    token_type=token_type,
                    username=username,
                    expires_at=expires_at,
                    reason=reason,
                    blacklisted_by=blacklisted_by,
                    session_id=session_id
                )
            
            logger.info(f"令牌已加入黑名單: {username}, 原因: {reason}")
            
        except Exception as e:
            logger.error(f"加入黑名單失敗: {str(e)}")
    
    def logout_user(self, access_token: str, logout_reason: str = 'manual'):
        """
        用戶登出處理
        
        Args:
            access_token: 訪問令牌
            logout_reason: 登出原因
        """
        try:
            # 解碼 token 獲取會話信息
            payload = jwt.decode(
                access_token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']],
                options={"verify_exp": False}
            )
            
            username = payload.get('username')
            session_id = payload.get('session_id')
            
            # 停用會話
            if self.jwt_db and session_id:
                self.jwt_db.deactivate_session(
                    session_id=session_id,
                    logout_reason=logout_reason
                )
            
            # 將令牌加入黑名單
            self.blacklist_token(
                token=access_token,
                token_type='access',
                username=username,
                reason=logout_reason
            )
            
            logger.info(f"用戶 {username} 登出成功")
            return True
            
        except Exception as e:
            logger.error(f"用戶登出處理失敗: {str(e)}")
            return False
    
    def get_token_from_request(self) -> Optional[str]:
        """從請求中提取 JWT 令牌"""
        auth_header = request.headers.get(current_app.config['JWT_HEADER_NAME'])
        if not auth_header:
            return None
        
        header_type = current_app.config['JWT_HEADER_TYPE']
        if not auth_header.startswith(f"{header_type} "):
            return None
        
        return auth_header[len(f"{header_type} "):]
    
    def get_user_sessions(self, username: str):
        """獲取用戶的活躍會話"""
        if not self.jwt_db:
            return []
        
        try:
            return self.jwt_db.get_user_active_sessions(username)
        except Exception as e:
            logger.error(f"獲取用戶會話失敗: {str(e)}")
            return []
    
    def force_logout_user(self, username: str, admin_username: str = None):
        """強制登出用戶的所有會話"""
        if not self.jwt_db:
            return False
        
        try:
            # 獲取用戶的所有活躍會話
            sessions = self.jwt_db.get_user_active_sessions(username)
            
            # 停用所有會話
            for session in sessions:
                self.jwt_db.deactivate_session(
                    session_id=session['session_id'],
                    logout_reason='force_logout'
                )
            
            logger.info(f"管理員 {admin_username} 強制登出用戶 {username}, 影響 {len(sessions)} 個會話")
            return True
            
        except Exception as e:
            logger.error(f"強制登出用戶失敗: {str(e)}")
            return False
    
    def cleanup_expired_data(self):
        """清理過期數據"""
        if not self.jwt_db:
            return {}
        
        try:
            return self.jwt_db.cleanup_expired_records()
        except Exception as e:
            logger.error(f"清理過期數據失敗: {str(e)}")
            return {}
    
    def get_security_statistics(self):
        """獲取安全統計"""
        if not self.jwt_db:
            return {}
        
        try:
            return self.jwt_db.get_security_stats()
        except Exception as e:
            logger.error(f"獲取安全統計失敗: {str(e)}")
            return {}

# 全局增強 JWT 管理器實例
enhanced_jwt_manager = None

def get_enhanced_jwt_manager() -> EnhancedJWTManager:
    """獲取增強 JWT 管理器實例"""
    if current_app:
        return current_app.extensions.get('enhanced_jwt_manager')
    return enhanced_jwt_manager

# JWT 裝飾器（增強版）
def jwt_required(optional: bool = False):
    """
    JWT 認證裝飾器（增強版）
    
    Args:
        optional: 是否可選認證（為 True 時，無令牌也可通過）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_mgr = get_enhanced_jwt_manager()
            if not jwt_mgr:
                return jsonify({'error': 'JWT 管理器未初始化'}), 500
            
            token = jwt_mgr.get_token_from_request()
            
            if not token:
                if optional:
                    g.current_user = None
                    return func(*args, **kwargs)
                return jsonify({
                    'error': 'Missing authorization token',
                    'error_code': 'TOKEN_MISSING'
                }), 401
            
            payload = jwt_mgr.verify_token(token)
            if not payload:
                if optional:
                    g.current_user = None
                    return func(*args, **kwargs)
                return jsonify({
                    'error': 'Invalid or expired token',
                    'error_code': 'TOKEN_INVALID'
                }), 401
            
            # 將用戶信息存儲在 Flask 的 g 對象中
            g.current_user = payload
            g.jwt_token = token
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def admin_required():
    """管理員權限裝飾器（增強版）"""
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if not g.current_user:
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            # 檢查是否為管理員
            if not g.current_user.get('is_manager', False):
                return jsonify({
                    'error': 'Admin privileges required',
                    'error_code': 'INSUFFICIENT_PRIVILEGES'
                }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def permission_required(required_permissions: List[str]):
    """權限檢查裝飾器（增強版）"""
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if not g.current_user:
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            user_permissions = g.current_user.get('permissions', [])
            
            # 檢查是否具有所需權限
            for permission in required_permissions:
                if permission not in user_permissions:
                    return jsonify({
                        'error': f'Permission "{permission}" required',
                        'error_code': 'INSUFFICIENT_PERMISSIONS'
                    }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user() -> Optional[Dict[str, Any]]:
    """獲取當前用戶信息"""
    return getattr(g, 'current_user', None)

def get_current_token() -> Optional[str]:
    """獲取當前 JWT 令牌"""
    return getattr(g, 'jwt_token', None)

# JWT 工具函數（增強版）
class JWTUtils:
    """JWT 工具類（增強版）"""
    
    @staticmethod
    def create_user_permissions(user_data: Dict[str, Any]) -> List[str]:
        """
        根據用戶數據創建權限列表
        
        Args:
            user_data: 用戶數據
            
        Returns:
            list: 權限列表
        """
        permissions = ['user:read']  # 基本權限
        
        # 根據部門添加權限
        department = user_data.get('department', '').lower()
        if department == 'hr':
            permissions.extend(['hr:read', 'employee:read'])
        elif department == 'finance':
            permissions.extend(['finance:read', 'financial_records:read'])
        elif department == 'it':
            permissions.extend(['it:read', 'system:read'])
        
        # 如果是主管，添加管理權限（重要修正）
        if user_data.get('is_manager', False):
            permissions.extend([
                'user:write',
                'employee:read',     # 主管必須有員工讀取權限
                'employee:write',
                'subordinates:read',
                'reports:read'
            ])
        
        # 調試信息
        print(f"為用戶 {user_data.get('username')} 創建權限:")
        print(f"  部門: {department}")
        print(f"  是否主管: {user_data.get('is_manager', False)}")
        print(f"  下屬數量: {user_data.get('subordinates_count', 0)}")
        print(f"  最終權限: {list(set(permissions))}")
        
        # 移除重複權限
        return list(set(permissions))
    
    @staticmethod
    def extract_user_info_from_ad_result(ad_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        從 AD 認證結果中提取用戶信息
        
        Args:
            ad_result: AD 認證結果
            
        Returns:
            dict: 格式化的用戶信息
        """
        if not ad_result.get('success') or not ad_result.get('data'):
            return {}
        
        user_data = ad_result['data'].get('user', {})
        subordinates = ad_result['data'].get('subordinates', [])
        
        # 判斷是否為主管
        is_manager = len(subordinates) > 0
        
        user_info = {
            'username': user_data.get('username', ''),
            'user_id': user_data.get('employee_id', ''),
            'display_name': user_data.get('display_name', ''),
            'email': user_data.get('email', ''),
            'department': user_data.get('department', ''),
            'title': user_data.get('title', ''),
            'is_manager': is_manager,
            'subordinates_count': len(subordinates),
            'manager_info': ad_result['data'].get('manager', {})
        }
        
        # 創建權限列表
        user_info['permissions'] = JWTUtils.create_user_permissions(user_info)
        
        return user_info