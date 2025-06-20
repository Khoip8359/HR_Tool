import os
import sys
import time
import datetime  # 添加 datetime 導入
import logging
from pathlib import Path

class BaseConfig:
    # 基礎日誌配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 日誌檔案路徑配置
    # 獲取當前文件目錄

    # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
     # 獲取項目根目錄（app/ 的上一層）
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 項目根目錄
    
    default_config_dir = os.path.join(BASE_DIR, 'app', 'config')  # 拼接預設路徑
    CONFIG_DIR = os.getenv('CONFIG_DIR', default_config_dir)
    LOG_DIR = os.path.join(BASE_DIR, 'logs')  # 現在指向 /project_root/logs
    
    # 確保日誌目錄存在
    @classmethod
    def ensure_log_dir(cls):
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)
    
    # 日誌檔案配置
    LOG_FILES = {
        'app': {
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'level': logging.INFO,
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        },
        'auth': {
            'filename': os.path.join(LOG_DIR, 'auth.log'),
            'level': logging.INFO,
            'max_bytes': 5 * 1024 * 1024,   # 5MB
            'backup_count': 3
        },
        'leave': {
            'filename': os.path.join(LOG_DIR, 'leave.log'),
            'level': logging.INFO,
            'max_bytes': 5 * 1024 * 1024,
            'backup_count': 3
        },
        'notification': {
            'filename': os.path.join(LOG_DIR, 'notification.log'),
            'level': logging.INFO,
            'max_bytes': 5 * 1024 * 1024,
            'backup_count': 3
        },
        'error': {
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'level': logging.ERROR,
            'max_bytes': 10 * 1024 * 1024,
            'backup_count': 10
        },
        'security': {
            'filename': os.path.join(LOG_DIR, 'security.log'),
            'level': logging.WARNING,
            'max_bytes': 5 * 1024 * 1024,
            'backup_count': 10
        }
    }
    
    # 控制台輸出配置
    CONSOLE_LOG_ENABLED = True
    CONSOLE_LOG_LEVEL = logging.INFO
    
    # 結構化日誌配置
    STRUCTURED_LOGGING = False
    LOG_REQUEST_ID = True
    
    # 日誌過濾配置
    LOG_FILTERS = {
        'exclude_paths': ['/health', '/metrics'],
        'exclude_user_agents': ['kube-probe', 'health-checker']
    }
    # ------------------------------------------------------------------------- logging 配置 END
    
    # JWT 配置
    JWT_CONFIGS = {
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'your-super-secret-key-change-in-production'),
        'JWT_ACCESS_TOKEN_EXPIRES': datetime.timedelta(hours=1),  # 使用 timedelta 對象
        'JWT_REFRESH_TOKEN_EXPIRES': datetime.timedelta(days=30),  # 使用 timedelta 對象
        'JWT_ALGORITHM': 'HS256',
        'JWT_BLACKLIST_ENABLED': True,
        'JWT_DATABASE_ENABLED': True,
        'JWT_SESSION_TRACKING': True
    }
    
    # 時區配置
    TIMEZONE_CONFIG = {
    'DEFAULT_TIMEZONE': 'Asia/Ho_Chi_Minh',  # 預設時區
    'UTC_TIMEZONE': 'UTC',             # UTC 時區
    'STORE_TIMEZONE_AWARE': False,     # 資料庫是否儲存時區感知的時間
    'DISPLAY_TIMEZONE': 'Asia/Ho_Chi_Minh', # 顯示給用戶的時區
    }
    
    # AD 配置
    AD_CONFIG = {
        # AD 伺服器預設設定
        'DEFAULT_AD_SERVER': "192.168.1.245",
        'DEFAULT_DOMAIN': "FULINVN_TN",
        'DEFAULT_ORGANIZATION': "fulinvn.com"
    }

    # 資料庫配置路徑
    DB_CONFIG_PATH = os.getenv('DB_CONFIG_PATH', str(Path(CONFIG_DIR) / 'config.txt'))
    
    # 資料庫連接池配置
    DATABASE_CONFIGS = [
        {
            'pool_name': 'mysql_hr',
            'section': 'mysql',
            'pool_size': int(os.getenv('MYSQL_POOL_SIZE', '5')),
            'max_overflow': int(os.getenv('MYSQL_MAX_OVERFLOW', '10')),
            'pool_timeout': int(os.getenv('MYSQL_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('MYSQL_POOL_RECYCLE', '3600')),
            'echo': os.getenv('MYSQL_ECHO', 'false').lower() == 'true'
        },
        {
            'pool_name': 'mssql_hr',
            'section': 'hr',
            'pool_size': int(os.getenv('MSSQL_POOL_SIZE', '3')),
            'max_overflow': int(os.getenv('MSSQL_MAX_OVERFLOW', '8')),
            'pool_timeout': int(os.getenv('MSSQL_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('MSSQL_POOL_RECYCLE', '3600')),
            'echo': os.getenv('MSSQL_ECHO', 'false').lower() == 'true'
        }
    ]
    
    # 郵件服務配置
    EMAIL_CONFIG = {
        'default_provider': 'smtp',  # 預設提供商
        'providers': {
            'smtp': {
                'host': os.getenv('SMTP_HOST', '192.168.1.211'),
                'port': int(os.getenv('SMTP_PORT', 25)),
                'use_tls': False,
                'use_ssl': False,
                'username': None,
                'password': None,
                'timeout': int(os.getenv('SMTP_TIMEOUT', 30))
            }
        },
        'default_sender': {
            'name': os.getenv('EMAIL_SENDER_NAME', '請假系統'),
            'email': os.getenv('EMAIL_SENDER_EMAIL','leave_system@fulinvn.com')
        },
        'templates': {
            'base_template_path': 'templates/email',
            'default_charset': 'utf-8'
        },
        'limits': {
            'max_recipients': int(os.getenv('EMAIL_MAX_RECIPIENTS', 50)),
            'max_attachments': int(os.getenv('EMAIL_MAX_ATTACHMENTS', 5)),
            'max_attachment_size': int(os.getenv('EMAIL_MAX_ATTACHMENT_SIZE', 10485760))  # 10MB
        },
        'retry': {
            'max_attempts': int(os.getenv('EMAIL_MAX_ATTEMPTS', 3)),
            'delay_seconds': int(os.getenv('EMAIL_RETRY_DELAY', 5))
        }
    }

class DevelopmentConfig(BaseConfig):
    """開發環境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(BaseConfig):
    """生產環境配置"""
    DEBUG = False
    TESTING = False

class TestingConfig(BaseConfig):
    """測試環境配置"""
    DEBUG = True
    TESTING = True

