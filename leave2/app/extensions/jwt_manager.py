#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
增強的 JWT 認證擴展模組 - 主要管理器
"""
import jwt
import datetime
from datetime import timezone
from flask import Flask, request, current_app
from typing import Optional, Dict, Any
# import logging
import secrets
from app.extensions import get_logger
import pytz

def get_app_timezone():
    """從 Flask 配置獲取時區"""
    tz_name = current_app.config.get('TIMEZONE_CONFIG', {}).get('DEFAULT_TIMEZONE', 'Asia/Ho_Chi_Minh')
    return pytz.timezone(tz_name)

def get_local_now():
    """獲取本地時間"""
    return datetime.datetime.now(get_app_timezone())

def get_local_datetime():
    """獲取本地時間的 naive datetime"""
    return get_local_now().replace(tzinfo=None)

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
            try:
                from app.models.jwt_models import JWTDatabaseManager
                self.jwt_db = JWTDatabaseManager(self.db_manager)
                self.jwt_db.create_tables()
                logger.info("JWT 資料庫表格初始化完成")
            except ImportError:
                logger.warning("JWT 資料庫模型未找到，跳過資料庫初始化")
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
        """生成訪問令牌和刷新令牌（含資料庫記錄）"""
        # now = datetime.datetime.utcnow()
        now = get_local_datetime()
        
        # 確保配置值是 timedelta 對象
        access_expires_delta = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        refresh_expires_delta = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        
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
                self._record_session_to_db(user_data, access_token, refresh_token, 
                                         access_expires, refresh_expires, client_info, auth_info)
            except Exception as e:
                logger.error(f"記錄 JWT 會話到資料庫失敗: {str(e)}")
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(access_expires_delta.total_seconds()),
            'session_id': session_id
        }
    
    def _record_session_to_db(self, user_data, access_token, refresh_token, 
                             access_expires, refresh_expires, client_info, auth_info):
        """記錄會話到資料庫"""
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
        """驗證 JWT 令牌（含資料庫黑名單檢查）"""
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
    
    def blacklist_token(self, token: str, token_type: str = 'access', 
                       username: str = None, reason: str = 'logout', 
                       blacklisted_by: str = None):
        """將令牌加入黑名單"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']],
                options={"verify_exp": False}
            )
            
            expires_at = datetime.datetime.fromtimestamp(payload.get('exp', 0))
            username = username or payload.get('username')
            session_id = payload.get('session_id')
            
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
    
    def get_token_from_request(self) -> Optional[str]:
        """從請求中提取 JWT 令牌"""
        auth_header = request.headers.get(current_app.config['JWT_HEADER_NAME'])
        if not auth_header:
            return None
        
        header_type = current_app.config['JWT_HEADER_TYPE']
        if not auth_header.startswith(f"{header_type} "):
            return None
        
        return auth_header[len(f"{header_type} "):]
    
    def logout_user(self, access_token: str, logout_reason: str = 'manual'):
        """用戶登出處理"""
        try:
            payload = jwt.decode(
                access_token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']],
                options={"verify_exp": False}
            )
            
            username = payload.get('username')
            session_id = payload.get('session_id')
            
            if self.jwt_db and session_id:
                self.jwt_db.deactivate_session(
                    session_id=session_id,
                    logout_reason=logout_reason
                )
            
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

# 為了簡化，暫時保留一個簡化版本的 create_tokens 方法
def create_tokens(user_info, remember_me=False):
    """簡化版本的 create_tokens 方法"""
    if not current_app or 'enhanced_jwt_manager' not in current_app.extensions:
        logger.error("Enhanced JWT Manager 未初始化")
        return None
    
    jwt_manager = current_app.extensions['enhanced_jwt_manager']
    return jwt_manager.generate_tokens(user_info)