#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Application Factory - 使用日誌擴展版本
"""
import time
from flask import Flask, g, request
from flask_cors import CORS
# from .extensions.flask_database import FlaskDatabaseManager

def init_logging_extension(app):
    """初始化日誌擴展"""
    from .extensions.logging_extension import logging_extension
    logging_extension.init_app(app)
    
def init_other_extensions(app):
    """初始化其他擴展"""
    # from .extensions.logging_extension import get_logger
    from .extensions import get_logger, FlaskDatabaseManager, enhanced_jwt_manager, ad_auth, data_pool_manager
    logger = get_logger('app')
    
    try:
        # 初始化資料庫管理器
        
        # from .extensions.flask_database import FlaskDatabaseManager
        db_manager = FlaskDatabaseManager()
        db_manager.init_app(app)
        logger.info("Database manager initialized")
        
        # 2026-06-19 # Add
        # 從 app.extensions 中獲取資料庫管理器並傳遞給 JWT 管理器
        enhanced_jwt_manager.db_manager = app.extensions['database_manager']
        
        # 初始化其他擴展（如果有的話）
        # 初始化 JWT 管理器
        enhanced_jwt_manager.init_app(app)
        logger.info("JWT manager initialized")
        
         # 初始化 AD 認證
        ad_auth.init_app(app)
        logger.info("AD auth initialized")
        
         # 初始化資料池管理器
        data_pool_manager.init_app(app)
        logger.info("Data pool manager initialized")
        
        # from .extensions import data_pool_manager, ad_auth
        # data_pool_manager.init_app(app)
        # ad_auth.init_app(app)
        # logger.info("Additional extensions initialized")
        
    except Exception as e:
        logger.error(f"Extension initialization failed: {str(e)}", exc_info=True)
        raise
    
    logger.info("All extensions initialization completed")

def register_request_hooks(app):
    """註冊請求鉤子"""
    from .extensions.logging_extension import get_logger
    logger = get_logger('app')
    
    @app.before_request
    def log_request():
        """記錄請求信息"""
        # 檢查是否需要過濾此請求的日誌
        if hasattr(app.config, 'LOG_FILTERS'):
            exclude_paths = app.config.LOG_FILTERS.get('exclude_paths', [])
            if request.path in exclude_paths:
                return
            
            exclude_user_agents = app.config.LOG_FILTERS.get('exclude_user_agents', [])
            user_agent = request.headers.get('User-Agent', '')
            if any(agent in user_agent for agent in exclude_user_agents):
                return
        
        # 記錄請求
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        
        # 如果啟用了請求 ID 追蹤
        if hasattr(app.config, 'LOG_REQUEST_ID') and app.config.LOG_REQUEST_ID:
            import uuid
            g.request_id = str(uuid.uuid4())[:8]
            logger.info(f"Request ID: {g.request_id}")
    
    @app.after_request
    def log_response(response):
        """記錄響應信息"""
        # 檢查是否需要過濾
        if hasattr(app.config, 'LOG_FILTERS'):
            exclude_paths = app.config.LOG_FILTERS.get('exclude_paths', [])
            if request.path in exclude_paths:
                return response
        
        logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        return response

def register_error_handlers(app):
    """註冊錯誤處理器"""
    from .extensions.logging_extension import get_logger
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """處理未捕獲的異常"""
        logger = get_logger('app')
        security_logger = get_logger('security')
        
        # 記錄詳細錯誤信息
        error_info = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'path': request.path,
            'method': request.method,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True, extra=error_info)
        security_logger.error(f"Security alert - Unhandled exception from {request.remote_addr}: {str(e)}")
        
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """處理 404 錯誤"""
        logger = get_logger('app')
        logger.warning(f"404 Not Found: {request.method} {request.path} from {request.remote_addr}")
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(401)
    def handle_unauthorized(e):
        """處理 401 錯誤"""
        auth_logger = get_logger('auth')
        auth_logger.warning(f"Unauthorized access attempt: {request.path} from {request.remote_addr}")
        return {'error': 'Unauthorized access'}, 401
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        """處理 403 錯誤"""
        security_logger = get_logger('security')
        security_logger.warning(f"Forbidden access attempt: {request.path} from {request.remote_addr}")
        return {'error': 'Forbidden access'}, 403

def register_management_routes(app):
    """註冊管理和監控路由"""
    from .extensions.logging_extension import get_logger
    logger = get_logger('app')
    
    @app.route('/health')
    def health_check():
        """簡單的健康檢查端點"""
        return {'status': 'healthy', 'service': 'leave-management-system'}
    
    @app.route('/test-log')
    def test_log():
        """測試各種日誌記錄器的路由"""
        logger.info("Testing main app logger from /test-log route")
        
        # 測試不同模組的日誌記錄器
        auth_logger = get_logger('auth')
        leave_logger = get_logger('leave')
        notification_logger = get_logger('notification')
        security_logger = get_logger('security')
        
        auth_logger.info("Testing auth logger from web route")
        leave_logger.info("Testing leave logger from web route")
        notification_logger.info("Testing notification logger from web route")
        security_logger.warning("Testing security logger from web route")
        
        # 測試錯誤級別日誌
        logger.error("Testing error level log from web route")
        
        # 測試結構化日誌
        logger.info("Testing structured logging from web route", extra={
            'user_id': 'web_test_user',
            'action': 'test_log_route',
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        })
        
        return {
            'message': 'Log test completed from web route',
            'timestamp': '{{timestamp}}',
            'check_files': [
                'logs/app.log',
                'logs/auth.log', 
                'logs/leave.log',
                'logs/notification.log',
                'logs/security.log',
                'logs/error.log'
            ]
        }
    
    @app.route('/log-info')
    def log_info():
        """顯示日誌配置信息"""
        import os
        
        # 獲取日誌統計信息
        try:
            log_stats = app.extensions['logging'].get_log_statistics()
        except:
            log_stats = {'error': 'Logging extension not available'}
        
        log_info = {
            'logging_extension_stats': log_stats,
            'log_level': getattr(app.config, 'LOG_LEVEL', 'INFO'),
            'log_directory': getattr(app.config, 'LOG_DIR', 'logs'),
            'console_enabled': getattr(app.config, 'CONSOLE_LOG_ENABLED', True),
            'structured_logging': getattr(app.config, 'STRUCTURED_LOGGING', False),
            'log_files': {}
        }
        
        # 檢查日誌文件狀態
        if hasattr(app.config, 'LOG_FILES'):
            for log_name, log_config in app.config.LOG_FILES.items():
                file_path = log_config['filename']
                file_exists = os.path.exists(file_path)
                file_size = os.path.getsize(file_path) if file_exists else 0
                
                log_info['log_files'][log_name] = {
                    'path': file_path,
                    'exists': file_exists,
                    'size_bytes': file_size,
                    'level': getattr(log_config, 'level', 'INFO'),
                    'max_bytes': log_config.get('max_bytes', 0),
                    'backup_count': log_config.get('backup_count', 0)
                }
        
        return log_info
    
    @app.route('/log-flush')
    def flush_logs():
        """強制刷新所有日誌到文件"""
        try:
            app.extensions['logging'].flush_all_logs()
            logger.info("Manual log flush requested via web interface")
            return {'message': 'All logs flushed successfully', 'status': 'success'}
        except Exception as e:
            logger.error(f"Log flush failed: {str(e)}")
            return {'message': f'Log flush failed: {str(e)}', 'status': 'error'}, 500
    
    @app.route('/log-stats')
    def log_statistics():
        """獲取詳細的日誌統計信息"""
        try:
            stats = app.extensions['logging'].get_log_statistics()
            
            # 添加文件系統統計
            import os
            file_stats = {}
            if hasattr(app.config, 'LOG_FILES'):
                for log_name, log_config in app.config.LOG_FILES.items():
                    file_path = log_config['filename']
                    if os.path.exists(file_path):
                        stat = os.stat(file_path)
                        file_stats[log_name] = {
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'created': stat.st_ctime
                        }
            
            stats['file_statistics'] = file_stats
            return stats
        except Exception as e:
            logger.error(f"Failed to get log statistics: {str(e)}")
            return {'error': str(e)}, 500

def register_blueprints(app):
    """註冊業務 Blueprint"""
    from .extensions.logging_extension import get_logger
    logger = get_logger('app')
    
    try:
        # 註冊認證模組
        from app.blueprints.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.info("Auth blueprint registered")
        
        # 註冊其他模組（如果存在）
        try:
            from app.blueprints.leave import leave_bp
            app.register_blueprint(leave_bp, url_prefix='/leave')
            logger.info("Leave blueprint registered")
        except ImportError:
            logger.warning("Leave blueprint not available")
        
        try:
            from app.blueprints.hr import hr_bp
            app.register_blueprint(hr_bp, url_prefix='/hr')
            logger.info("HR blueprint registered")
        except ImportError:
            logger.warning("HR blueprint not available")
            
        try:
            from app.blueprints.admin import admin_bp
            app.register_blueprint(admin_bp, url_prefix='/admin')
            logger.info("admin_bp blueprint registered")
        except ImportError:
            logger.warning("admin_bp blueprint not available")

        
    except ImportError as e:
        logger.warning(f"Some blueprints not available: {str(e)}")
    except Exception as e:
        logger.error(f"Blueprint registration failed: {str(e)}", exc_info=True)
        raise

# 向後兼容的輔助函數
def get_logger(name=None):
    """
    向後兼容的獲取日誌記錄器函數
    
    Args:
        name: 日誌記錄器名稱，如果為 None 則返回主應用記錄器
    
    Returns:
        Logger: 配置好的日誌記錄器
    """
    from .extensions.logging_extension import get_logger as ext_get_logger
    return ext_get_logger(name or 'app')
    
def create_app(config_name='production'):
    """
    Flask 應用工廠函數 - 使用日誌擴展版本
    
    Args:
        config_name: 配置環境名稱 ('development', 'production', 'testing')
    
    Returns:
        Flask: 配置好的 Flask 應用實例
    """
    app = Flask(__name__)
    
    from .extensions.logging_extension import get_logger
    logger = get_logger('app')
    logger.info(f"Flask application initialization completed successfully with config: {config_name}")
            
    CORS(app, 
        origins="*",
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
        supports_credentials=True)
    logger.info("CORS initialized")
    
    # 載入配置
    config_class = {
        'development': 'app.config.DevelopmentConfig',
        'production': 'app.config.ProductionConfig',
        'testing': 'app.config.TestingConfig'
    }
    
    app.config.from_object(config_class[config_name])
    
    # 按順序初始化擴展
    # 1. 優先初始化日誌系統（作為第一個擴展）
    init_logging_extension(app)     # 在這裡調用調試函數
    
    # 2. 然後初始化其他組件
    init_other_extensions(app)
    # db_manager = FlaskDatabaseManager()
    # db_manager.init_app(app)
    
    # 3. 註冊應用組件
    register_request_hooks(app)
    register_error_handlers(app)
    register_management_routes(app)
    register_blueprints(app)
    
    # 3. 註冊健康檢查路由
    # @app.route('/health')
    # def health_check():
    #     db_health = database_manager.health_check()
    #     pool_health = data_pool_manager.health_check()
        
    #     overall_status = 'healthy'
    #     for service_health in [db_health, pool_health]:
    #         for status in service_health.values():
    #             if status.get('status') != 'healthy':
    #                 overall_status = 'unhealthy'
    #                 break
        
    #     return {
    #         'status': overall_status,
    #         'database': db_health,
    #         'data_pools': pool_health
    #     }
    
    # # 註冊 Blueprint
    # from app.blueprints.auth import auth_bp
    
    # app.register_blueprint(auth_bp, url_prefix='/auth')
    
     # 獲取日誌記錄器並記錄完成信息
    
    
    return app