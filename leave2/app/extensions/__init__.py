# app/extensions/__init__.py

# 日誌配置
import logging
# ==================== 日誌系統選擇 ====================
LOGGING_TYPE = None
logging_extension = None

try:
    # 優先使用隊列日誌系統（解決文件鎖定問題）
    from .logging_extension import setup_logging, get_logger, logging_extension
    LOGGING_TYPE = "queue"
    print("✓ 使用隊列日誌系統")
    
except ImportError:
    # 後備使用基本日誌系統
    import os
    from logging.handlers import RotatingFileHandler
    
    def setup_logging(app):
        """基本日誌設置"""
        # 獲取日誌目錄
        log_dir = getattr(app.config, 'LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 創建文件處理器
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        ))
        
        # 創建控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s'
        ))
        
        # 配置根日誌記錄器
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)
        
        # 配置 Flask 日誌記錄器
        app.logger.handlers.clear()
        app.logger.propagate = True
        app.logger.setLevel(logging.INFO)
        
        return root_logger
    
    def get_logger(name='app'):
        """基本日誌記錄器"""
        return logging.getLogger(name)
    
    LOGGING_TYPE = "basic"
    print("⚠ 使用基本日誌系統（後備方案）")

# 創建全局日誌記錄器
logger = get_logger('app')

#--------------------------------------------------------------------
# JWT 相關擴展
JWT_AVAILABLE = False
try:
    from .jwt_manager import EnhancedJWTManager, create_tokens
    from .jwt_decorators import (
        jwt_required, 
        admin_required, 
        permission_required,
        get_current_user,
        get_current_token
    )
    from .jwt_utils import JWTUtils

    # 創建 JWT 管理器實例
    enhanced_jwt_manager = EnhancedJWTManager()
    JWT_AVAILABLE = True
except ImportError as e:  
    print(f"⚠ JWT 擴展不可用: {e}")
    # 創建佔位符
    class PlaceholderJWTManager:
        def init_app(self, app):
            pass
    
    enhanced_jwt_manager = PlaceholderJWTManager()
    
    # 佔位符函數
    def jwt_required(f):
        return f
    def admin_required(f):
        return f
    def permission_required(permission):
        def decorator(f):
            return f
        return decorator
    def get_current_user():
        return None
    def get_current_token():
        return None
    def create_tokens(user_id):
        return None, None
    
    class JWTUtils:
        pass


#--------------------------------------------------------------------

# 資料庫管理佔位符
DATABASE_AVAILABLE = False
try:
    from .flask_database import FlaskDatabaseManager
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠ 資料庫擴展不可用: {e}")
    
    class PlaceholderDatabaseManager:
        def init_app(self, app):
            pass
        
        def health_check(self):
            return {'status': 'unavailable'}
    
    FlaskDatabaseManager = PlaceholderDatabaseManager

    # from core.flask_db_extension import (
    #     FlaskDatabaseManager, 
    #     get_db_manager, 
    #     get_mysql_session, 
    #     get_mssql_session,
    #     with_database,
    #     QueryBuilder
    # )
    
#--------------------------------------------------------------------
# AD 認證佔位符（暫時保留原有結構）
AD_AUTH_AVAILABLE = False
try:
    from .ad_authenticator import ADAuthenticator,ADAuth, authenticate_user
    AD_AUTH_AVAILABLE = True
    
    # 創建 AD 認證實例
    ad_auth = ADAuth()
    
except ImportError as e:
    print(f"⚠ AD 認證擴展不可用: {e}")
    
    # AD 認證佔位符（暫時保留原有結構）

    class ADAuth:
        def __init__(self):
            self.app = None
            
        def init_app(self, app):
            """初始化 AD 認證擴展"""
            self.app = app
            # 這裡可以添加 AD 認證的初始化邏輯
            app.logger.info("AD Authentication extension initialized (placeholder)")
        
        
        def authenticate(self, username, password):
            """認證用戶"""
            return {'success': False, 'message': 'AD認證未實現'}
        
        def get_user_info(self, username):
            """獲取用戶信息"""
            return {'success': False, 'message': 'AD用戶信息獲取未實現'}
        
        def validate_token(self, token):
            """驗證令牌"""
            return {'success': False, 'message': 'AD令牌驗證未實現'}
        
        def health_check(self):
            """健康檢查"""
            return {
                'status': 'unavailable',
                'message': 'AD authentication not available (placeholder)',
                'ldap_available': False,
                'authenticator_ready': False
            }


    ad_auth = ADAuth()
    def authenticate_user(username, password, get_manager_info=True, get_subordinates=True):
            """認證用戶佔位符函數"""
            return ad_auth.authenticate(username, password)

#--------------------------------------------------------------------
# # 資料庫管理佔位符
# class DatabaseManager:
#     def __init__(self):
#         pass
# database_manager = DatabaseManager()

# 資料池管理佔位符
class DataPoolManager:
    def __init__(self):
        self.app = None
        self.pools = {}

    def init_app(self, app):
        """初始化資料池管理器"""
        self.app = app
        
        # 設定預設配置
        app.config.setdefault('DATA_POOL_ENABLED', False)
        app.config.setdefault('DATA_POOL_CONFIGS', {})
        
        # 初始化資料池（如果有配置的話）
        pool_configs = app.config.get('DATA_POOL_CONFIGS', {})
        for pool_name, pool_config in pool_configs.items():
            try:
                self.add_pool(pool_name, pool_config)
                app.logger.info(f"Data pool '{pool_name}' initialized")
            except Exception as e:
                app.logger.error(f"Failed to initialize data pool '{pool_name}': {str(e)}")
        
        # 註冊到 Flask 應用程式
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['data_pool_manager'] = self
        
        app.logger.info("Data Pool Manager extension initialized (placeholder)")
    
    def health_check(self):
        """健康檢查"""
        return {
            'status': 'healthy', 
            'pools_count': len(self.pools),
            'pools': list(self.pools.keys()),
            'message': 'Data pool manager is running (placeholder)',
            'enabled': self.app.config.get('DATA_POOL_ENABLED', False) if self.app else False
        }
    
    def get_pool(self, pool_name):
        """獲取指定的資料池"""
        pool = self.pools.get(pool_name)
        if self.app and pool:
            self.app.logger.debug(f"Retrieved data pool: {pool_name}")
        elif self.app:
            self.app.logger.warning(f"Data pool '{pool_name}' not found")
        return pool
    
    def add_pool(self, pool_name, pool_config):
        """添加新的資料池"""
        # 這裡可以添加實際的資料池創建邏輯
        self.pools[pool_name] = {
            'name': pool_name,
            'config': pool_config,
            'status': 'active',
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if self.app:
            self.app.logger.info(f"Added data pool: {pool_name}")
    
    def remove_pool(self, pool_name):
        """移除資料池"""
        if pool_name in self.pools:
            del self.pools[pool_name]
            if self.app:
                self.app.logger.info(f"Removed data pool: {pool_name}")
            return True
        else:
            if self.app:
                self.app.logger.warning(f"Cannot remove data pool '{pool_name}': not found")
            return False
    
    def list_pools(self):
        """列出所有資料池"""
        return list(self.pools.keys())
    
    def get_pool_status(self, pool_name):
        """獲取資料池狀態"""
        pool = self.pools.get(pool_name)
        if pool:
            return {
                'name': pool_name,
                'status': pool.get('status', 'unknown'),
                'created_at': pool.get('created_at', 'unknown')
            }
        return None
    
data_pool_manager = DataPoolManager()
# 為了向後兼容，創建一個別名
database_manager = data_pool_manager
# 設定資料池狀態（總是可用，因為使用佔位符）
DATA_POOL_AVAILABLE = True


# 定義可導出的名稱
__all__ = [
    # 日誌相關
    'setup_logging',
    'get_logger',
    'logger',
    'LOGGING_TYPE',
    
    # 資料庫管理器
    'FlaskDatabaseManager',
    
    # JWT 管理器
    'enhanced_jwt_manager',
    'EnhancedJWTManager',
    'create_tokens',
    
    # JWT 裝飾器
    'jwt_required',
    'admin_required', 
    'permission_required',
    'get_current_user',
    'get_current_token',
    
    # JWT 工具
    'JWTUtils',
    
    # 其他擴展
    'ADAuthenticator',
    'ad_auth',
    'ADAuth',
    'authenticate_user',
    'AD_AUTH_AVAILABLE',
    'database_manager',
    'DATA_POOL_AVAILABLE'
    'data_pool_manager'
]

# 加載完成提示
# print(f"📦 Extensions loaded: 日誌={LOGGING_TYPE}, 資料庫={'✓' if DATABASE_AVAILABLE else '✗'}, JWT={'✓' if JWT_AVAILABLE else '✗'}")

# 加載完成提示，顯示所有擴展狀態
extensions_status = []
extensions_status.append(f"日誌={LOGGING_TYPE}")
extensions_status.append(f"資料庫={'✓' if DATABASE_AVAILABLE else '✗'}")
extensions_status.append(f"JWT={'✓' if JWT_AVAILABLE else '✗'}")
extensions_status.append(f"AD認證={'✓' if AD_AUTH_AVAILABLE else '✗'}")
extensions_status.append(f"資料池={'✓' if DATA_POOL_AVAILABLE else '✗'}")

print(f"📦 Extensions loaded: {', '.join(extensions_status)}")

# 顯示詳細狀態
print("📊 擴展狀態詳情:")
print(f"   • 日誌系統: {LOGGING_TYPE}")
print(f"   • 資料庫管理器: {'✓ 可用' if DATABASE_AVAILABLE else '✗ 不可用'}")
print(f"   • JWT 管理器: {'✓ 可用' if JWT_AVAILABLE else '✗ 不可用'}")
print(f"   • AD 認證: {'✓ 可用' if AD_AUTH_AVAILABLE else '✗ 不可用'}")
print(f"   • 資料池管理器: {'✓ 可用' if DATA_POOL_AVAILABLE else '✗ 不可用'}")

# 如果有擴展不可用，顯示詳細信息
unavailable_extensions = []
if not DATABASE_AVAILABLE:
    unavailable_extensions.append("資料庫管理器")
if not JWT_AVAILABLE:
    unavailable_extensions.append("JWT管理器")
if not AD_AUTH_AVAILABLE:
    unavailable_extensions.append("AD認證")

if unavailable_extensions:
    print(f"⚠️  使用佔位符的擴展: {', '.join(unavailable_extensions)}")
else:
    print("✅ 所有擴展都已成功載入")# app/extensions/__init__.py

