#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
AD 認證模組
提供 AD 帳號密碼驗證和完整組織資訊查詢服務
包含使用者、主管和下屬員工的詳細資訊
"""
import time
from typing import Dict, Any, List, Tuple, Optional
from flask import Flask, current_app

try:
    from ldap3 import Server, Connection, SIMPLE
    from ldap3.core.exceptions import LDAPException, LDAPBindError
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    
class ADAuthenticator:
    """AD 認證類別"""
    
    def __init__(self, server_ip: str, domain: str, organization: Optional[str] = None):
        """
        初始化 AD 認證器
        
        Args:
            server_ip: AD 伺服器 IP
            domain: 網域名稱
            organization: 組織名稱，預設為 fulinvn.com
        """
        self.server_ip = server_ip
        self.domain = domain
        self.organization = organization or "fulinvn.com"
        
    def authenticate_and_get_info(self, username: str, password: str, get_manager_info: bool = True, get_subordinates: bool = True) -> Dict[str, Any]:
        """
        認證使用者並取得完整組織資訊
        
        Args:
            username: 使用者名稱
            password: 密碼
            get_manager_info: 是否取得管理人員資訊
            get_subordinates: 是否取得下屬員工資訊
            
        Returns:
            dict: 包含認證結果和使用者資訊的字典
        """
        if not LDAP_AVAILABLE:
            return {
                'success': False,
                'message': 'LDAP library not available',
                'error_code': 'LDAP_UNAVAILABLE',
                'data': None
            }
            
        start_time = time.time()
        
        try:
            # 建立伺服器連接
            server = Server(self.server_ip, port=389)
            server_time = time.time() - start_time
            
            # 嘗試認證
            auth_start = time.time()
            successful_conn, auth_format = self._authenticate_user(server, username, password)
            auth_time = time.time() - auth_start
            
            if not successful_conn:
                return {
                    'success': False,
                    'message': 'Authentication failed',
                    'error_code': 'AUTH_FAILED',
                    'data': None,
                    'timing': {
                        'server_connection': round(server_time, 2),
                        'authentication': round(auth_time, 2),
                        'total': round(time.time() - start_time, 2)
                    }
                }
            
            # 取得使用者、主管和下屬資訊
            user_info = None
            manager_info = None
            subordinates = []
            timing_details = {
                'server_connection': server_time,
                'authentication': auth_time,
                'user_search': 0,
                'manager_search': 0,
                'subordinates_search': 0,
                'total': 0
            }
            
            if get_manager_info or get_subordinates:
                user_info, manager_info, subordinates, search_timing = self._get_user_and_manager_info(
                    successful_conn, username, get_manager_info, get_subordinates
                )
                timing_details.update(search_timing)
            
            successful_conn.unbind()
            
            total_time = time.time() - start_time
            timing_details['total'] = total_time
            
            return {
                'success': True,
                'message': 'Authentication successful',
                'error_code': None,
                'data': {
                    'user': user_info,
                    'manager': manager_info,
                    'subordinates': subordinates,
                    'auth_info': {
                        'username': username,
                        'domain': self.domain,
                        'auth_format': auth_format,
                        'login_time': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                },
                'timing': {
                    'server_connection': round(timing_details['server_connection'], 2),
                    'authentication': round(timing_details['authentication'], 2),
                    'user_search': round(timing_details['user_search'], 2),
                    'manager_search': round(timing_details['manager_search'], 2),
                    'subordinates_search': round(timing_details['subordinates_search'], 2),
                    'total': round(timing_details['total'], 2)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Internal server error',
                'error_code': 'INTERNAL_ERROR',
                'error_details': str(e),
                'data': None,
                'timing': {
                    'total': round(time.time() - start_time, 2)
                }
            }
    
    def _authenticate_user(self, server: Server, username: str, password: str) -> Tuple[Optional[Connection], Optional[str]]:
        """
        嘗試使用者認證
        
        Returns:
            tuple: (Connection, auth_format) 成功的連接物件和認證格式，失敗則返回 (None, None)
        """
        user_formats = [
            f"{username}@{self.domain}",
            f"{username}@{self.organization}",
            f"{self.domain}\\{username}",
            username
        ]
        
        for user_format in user_formats:
            try:
                conn = Connection(
                    server,
                    user=user_format,
                    password=password,
                    authentication=SIMPLE,
                    auto_bind=True
                )
                return conn, user_format
                
            except LDAPBindError:
                continue
            except Exception:
                continue
        
        return None, None
    
    def _get_user_and_manager_info(self, conn: Connection, username: str, get_manager_info: bool = True, get_subordinates: bool = True) -> Tuple[Optional[Dict], Optional[Dict], List[Dict], Dict[str, float]]:
        """
        取得使用者、管理人員和下屬員工的詳細資訊
        
        Args:
            conn: LDAP 連接物件
            username: 使用者名稱
            get_manager_info: 是否取得管理人員資訊
            get_subordinates: 是否取得下屬員工資訊
            
        Returns:
            tuple: (使用者資訊, 管理人員資訊, 下屬員工清單, 時間統計)
        """
        timing = {
            'user_search': 0,
            'manager_search': 0,
            'subordinates_search': 0
        }
        
        # 建立可能的 Base DN
        base_dn_options = [
            f"DC={self.organization.replace('.', ',DC=')}",
            f"DC={self.domain}",
            f"DC={self.domain},DC=local",
            ""  # 根搜尋
        ]
        
        user_info = None
        manager_info = None
        subordinates = []
        user_dn = None
        
        # 搜尋使用者
        user_search_start = time.time()
        
        for base_dn in base_dn_options:
            try:
                search_filter = f"(sAMAccountName={username})"
                
                success = conn.search(
                    search_base=base_dn,
                    search_filter=search_filter,
                    search_scope="SUBTREE",
                    attributes=[
                        'sAMAccountName', 'displayName', 'givenName', 'sn', 'cn',
                        'mail', 'userPrincipalName', 'department', 'title',
                        'telephoneNumber', 'mobile', 'manager', 'employeeID',
                        'company', 'distinguishedName', 'directReports'
                    ]
                )
                
                if success and conn.entries:
                    entry = conn.entries[0]
                    user_dn = str(getattr(entry, 'distinguishedName', ''))
                    
                    # 取得使用者基本資訊
                    user_info = {
                        'sam_account': str(getattr(entry, 'sAMAccountName', '') or ''),
                        'display_name': str(getattr(entry, 'displayName', '') or ''),
                        'given_name': str(getattr(entry, 'givenName', '') or ''),
                        'surname': str(getattr(entry, 'sn', '') or ''),
                        'cn': str(getattr(entry, 'cn', '') or ''),
                        'mail': str(getattr(entry, 'mail', '') or ''),
                        'upn': str(getattr(entry, 'userPrincipalName', '') or ''),
                        'department': str(getattr(entry, 'department', '') or ''),
                        'title': str(getattr(entry, 'title', '') or ''),
                        'phone': str(getattr(entry, 'telephoneNumber', '') or ''),
                        'mobile': str(getattr(entry, 'mobile', '') or ''),
                        'employee_id': str(getattr(entry, 'employeeID', '') or ''),
                        'company': str(getattr(entry, 'company', '') or ''),
                        'dn': user_dn
                    }
                    
                    # 檢查是否有直屬下屬
                    direct_reports = getattr(entry, 'directReports', None)
                    if direct_reports:
                        pass
                    
                    break
                    
            except Exception:
                continue
        
        timing['user_search'] = time.time() - user_search_start
        
        # 取得管理人員資訊
        if user_info and get_manager_info:
            manager_search_start = time.time()
            
            # 從使用者資料中找到主管 DN
            for base_dn in base_dn_options:
                try:
                    search_filter = f"(sAMAccountName={username})"
                    success = conn.search(
                        search_base=base_dn,
                        search_filter=search_filter,
                        search_scope="SUBTREE",
                        attributes=['manager']
                    )
                    
                    if success and conn.entries:
                        entry = conn.entries[0]
                        manager_dn = getattr(entry, 'manager', None)
                        if manager_dn:
                            manager_info = self._get_manager_details(conn, str(manager_dn))
                            break
                        else:
                            break
                except Exception:
                    continue
            
            timing['manager_search'] = time.time() - manager_search_start
        
        # 如果找到使用者且需要搜尋下屬，搜尋其下屬員工
        if user_dn and get_subordinates:
            subordinates_start = time.time()
            
            subordinates = self._get_subordinates(conn, user_dn, base_dn_options)
            
            timing['subordinates_search'] = time.time() - subordinates_start
        
        return user_info, manager_info, subordinates, timing
    
    def _get_subordinates(self, conn: Connection, manager_dn: str, base_dn_options: List[str]) -> List[Dict]:
        """
        取得指定主管的所有下屬員工 (最佳化版本)
        
        Args:
            conn: LDAP 連接物件
            manager_dn: 主管的 Distinguished Name
            base_dn_options: 可能的 Base DN 列表
            
        Returns:
            list: 下屬員工清單
        """
        subordinates = []
        
        # 最佳化：優先使用較具體的 Base DN，避免根目錄搜尋
        optimized_base_dn = [dn for dn in base_dn_options if dn != ""]  # 排除根目錄
        if "" in base_dn_options:
            optimized_base_dn.append("")  # 根目錄放最後
        
        for base_dn in optimized_base_dn:
            try:
                # 搜尋以此人為主管的所有員工
                search_filter = f"(manager={manager_dn})"
                base_desc = base_dn if base_dn else "根目錄"
                
                search_start = time.time()
                success = conn.search(
                    search_base=base_dn,
                    search_filter=search_filter,
                    search_scope="SUBTREE",
                    attributes=[
                        'sAMAccountName', 'displayName', 'givenName', 'sn',
                        'mail', 'department', 'title', 'telephoneNumber',
                        'mobile', 'employeeID', 'distinguishedName'
                    ],
                    size_limit=100,  # 限制最多100個結果，避免過大查詢
                    time_limit=15    # 單次搜尋最多15秒
                )
                
                search_time = time.time() - search_start
                
                if success and conn.entries:
                    for entry in conn.entries:
                        subordinate = {
                            'sam_account': str(getattr(entry, 'sAMAccountName', '') or ''),
                            'display_name': str(getattr(entry, 'displayName', '') or ''),
                            'given_name': str(getattr(entry, 'givenName', '') or ''),
                            'surname': str(getattr(entry, 'sn', '') or ''),
                            'mail': str(getattr(entry, 'mail', '') or ''),
                            'department': str(getattr(entry, 'department', '') or ''),
                            'title': str(getattr(entry, 'title', '') or ''),
                            'phone': str(getattr(entry, 'telephoneNumber', '') or ''),
                            'mobile': str(getattr(entry, 'mobile', '') or ''),
                            'employee_id': str(getattr(entry, 'employeeID', '') or ''),
                            'dn': str(getattr(entry, 'distinguishedName', '') or '')
                        }
                        subordinates.append(subordinate)
                    
                    break  # 找到結果就立即停止，不搜尋其他 Base DN
                else:
                    # 如果在具體的 Base DN 中沒找到，但搜尋很快，可能真的沒有下屬
                    # 如果搜尋時間很短（< 2秒），就不再嘗試其他 Base DN
                    if search_time < 2.0 and base_dn != "":
                        break
                        
            except Exception:
                # 如果是超時錯誤，直接跳過後續搜尋
                if "time limit" in str(e).lower() or search_time > 10:
                    break
                continue
        
        return subordinates
    
    def _get_manager_details(self, conn: Connection, manager_dn: str) -> Optional[Dict]:
        """
        取得管理人員的詳細資訊
        
        Args:
            conn: LDAP 連接物件
            manager_dn: 管理人員的 Distinguished Name
            
        Returns:
            dict: 管理人員資訊
        """
        try:
            success = conn.search(
                search_base=manager_dn,
                search_filter="(objectClass=user)",
                search_scope="BASE",
                attributes=[
                    'sAMAccountName',
                    'displayName',
                    'givenName',
                    'sn',
                    'mail',
                    'department',
                    'title',
                    'telephoneNumber',
                    'mobile',
                    'manager'  # 管理人員的上級主管
                ]
            )
            
            if success and conn.entries:
                entry = conn.entries[0]
                
                manager_info = {
                    'sam_account': str(getattr(entry, 'sAMAccountName', '') or ''),
                    'display_name': str(getattr(entry, 'displayName', '') or ''),
                    'given_name': str(getattr(entry, 'givenName', '') or ''),
                    'surname': str(getattr(entry, 'sn', '') or ''),
                    'mail': str(getattr(entry, 'mail', '') or ''),
                    'department': str(getattr(entry, 'department', '') or ''),
                    'title': str(getattr(entry, 'title', '') or ''),
                    'phone': str(getattr(entry, 'telephoneNumber', '') or ''),
                    'mobile': str(getattr(entry, 'mobile', '') or ''),
                    'dn': manager_dn
                }
                
                # 如果管理人員還有上級主管，也取得其資訊
                upper_manager_dn = getattr(entry, 'manager', None)
                if upper_manager_dn:
                    manager_info['upper_manager_dn'] = str(upper_manager_dn)
                    # 從 DN 中提取上級主管名稱
                    upper_manager_cn = str(upper_manager_dn).split(',')[0].replace('CN=', '')
                    manager_info['upper_manager_name'] = upper_manager_cn
                
                return manager_info
                
        except Exception:
            pass
        
        return None 
    
class ADAuth:
    """AD 認證擴展類別 - Flask 擴展包裝器"""
    
    def __init__(self, app: Flask = None):
        """
        初始化 AD 認證擴展
        
        Args:
            app: Flask 應用程式實例
        """
        self.app = None
        self.authenticator = None
        self._logger = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化 Flask 應用程式
        
        Args:
            app: Flask 應用程式實例
        """
        self.app = app
        
        # 設定預設配置
        app.config.setdefault('AD_SERVER_IP', '192.168.1.200')
        app.config.setdefault('AD_DOMAIN', 'fulin')
        app.config.setdefault('AD_ORGANIZATION', 'fulinvn.com')
        app.config.setdefault('AD_ENABLED', LDAP_AVAILABLE)
        
        # 建立 AD 認證器實例
        if LDAP_AVAILABLE:
            self.authenticator = ADAuthenticator(
                server_ip=app.config['AD_SERVER_IP'],
                domain=app.config['AD_DOMAIN'],
                organization=app.config['AD_ORGANIZATION']
            )
        
        # 設定日誌記錄器
        try:
            from ..extensions import get_logger
            self._logger = get_logger('auth')
        except:
            self._logger = app.logger
        
        # 將擴展註冊到 Flask 應用程式
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['ad_auth'] = self
        
        self._logger.info(f"AD Authentication extension initialized (LDAP Available: {LDAP_AVAILABLE})")
    
    def authenticate(self, username: str, password: str, get_manager_info: bool = True, get_subordinates: bool = True) -> Dict[str, Any]:
        """
        認證使用者
        
        Args:
            username: 使用者名稱
            password: 密碼
            get_manager_info: 是否取得管理人員資訊
            get_subordinates: 是否取得下屬員工資訊
            
        Returns:
            dict: 認證結果
        """
        if not LDAP_AVAILABLE:
            self._logger.warning("AD authentication attempted but LDAP library not available")
            return {
                'success': False,
                'message': 'AD authentication not available - LDAP library missing',
                'error_code': 'LDAP_UNAVAILABLE',
                'data': None
            }
        
        if not self.authenticator:
            self._logger.error("AD authenticator not initialized")
            return {
                'success': False,
                'message': 'AD authenticator not initialized',
                'error_code': 'NOT_INITIALIZED',
                'data': None
            }
        
        try:
            self._logger.info(f"Attempting AD authentication for user: {username}")
            
            result = self.authenticator.authenticate_and_get_info(
                username=username,
                password=password,
                get_manager_info=get_manager_info,
                get_subordinates=get_subordinates
            )
            
            if result['success']:
                self._logger.info(f"AD authentication successful for user: {username}")
                # 記錄額外的使用者資訊（不包含敏感資料）
                if result.get('data', {}).get('user'):
                    user_info = result['data']['user']
                    self._logger.info(f"User details - Display Name: {user_info.get('display_name')}, "
                                    f"Department: {user_info.get('department')}, "
                                    f"Title: {user_info.get('title')}")
            else:
                self._logger.warning(f"AD authentication failed for user: {username} - {result.get('message')}")
            
            return result
            
        except Exception as e:
            self._logger.error(f"AD authentication error for user {username}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Authentication service error',
                'error_code': 'SERVICE_ERROR',
                'error_details': str(e),
                'data': None
            }
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """
        獲取使用者資訊（不進行密碼驗證）
        注意：這需要使用系統帳號進行查詢
        
        Args:
            username: 使用者名稱
            
        Returns:
            dict: 使用者資訊
        """
        # 這個功能需要額外的系統帳號配置，暫時返回未實現
        self._logger.warning(f"get_user_info called for {username} but not implemented")
        return {
            'success': False,
            'message': 'User info lookup not implemented - requires system account',
            'error_code': 'NOT_IMPLEMENTED',
            'data': None
        }
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        驗證令牌（如果有實現令牌機制的話）
        
        Args:
            token: 令牌
            
        Returns:
            dict: 驗證結果
        """
        # AD 通常不直接提供令牌驗證，這通常由 JWT 或其他機制處理
        self._logger.warning("Token validation called but not implemented for AD")
        return {
            'success': False,
            'message': 'Token validation not implemented for AD authentication',
            'error_code': 'NOT_IMPLEMENTED',
            'data': None
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        
        Returns:
            dict: 健康狀態
        """
        if not LDAP_AVAILABLE:
            return {
                'status': 'unavailable',
                'message': 'LDAP library not available',
                'ldap_available': False,
                'authenticator_ready': False
            }
        
        return {
            'status': 'healthy' if self.authenticator else 'error',
            'message': 'AD authentication service ready' if self.authenticator else 'Authenticator not initialized',
            'ldap_available': LDAP_AVAILABLE,
            'authenticator_ready': self.authenticator is not None,
            'config': {
                'server_ip': self.app.config.get('AD_SERVER_IP') if self.app else None,
                'domain': self.app.config.get('AD_DOMAIN') if self.app else None,
                'organization': self.app.config.get('AD_ORGANIZATION') if self.app else None
            } if self.app else {}
        }


# 創建全域實例
ad_auth = ADAuth()

# 為了向後兼容，提供一個簡單的認證函數
def authenticate_user(username: str, password: str, get_manager_info: bool = True, get_subordinates: bool = True) -> Dict[str, Any]:
    """
    簡單的 AD 認證函數
    
    Args:
        username: 使用者名稱
        password: 密碼
        get_manager_info: 是否取得管理人員資訊
        get_subordinates: 是否取得下屬員工資訊
        
    Returns:
        dict: 認證結果
    """
    return ad_auth.authenticate(username, password, get_manager_info, get_subordinates)