#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leave Management System - 優化版啟動程式
消除重複導入，統一應用和日誌管理
"""

import os
import sys

# 全局變量，避免重複創建
_app_instance = None
_logger_instance = None

def get_config():
    """獲取配置環境"""
    return os.environ.get('FLASK_ENV', 'production')

def get_app_and_logger(config_name):
    """
    單一入口點獲取應用實例和日誌記錄器
    避免重複創建和導入
    """
    global _app_instance, _logger_instance
    
    # 如果已經創建過，直接返回（但允許不同配置重新創建）
    if _app_instance is not None and hasattr(_app_instance, 'config_name') and _app_instance.config_name == config_name:
        return _app_instance, _logger_instance
    
    # 創建新的應用實例
    from app import create_app
    app = create_app(config_name)
    app.config_name = config_name  # 記錄配置名稱
    
    # 獲取日誌記錄器
    from app.extensions.logging_extension import get_logger
    logger = get_logger('app')
    
    # 緩存實例
    _app_instance = app
    _logger_instance = logger
    
    return app, logger

def main():
    """主函數 - 優化版本"""
    config_name = get_config()
    
    if len(sys.argv) < 2:
        print("Usage: python run.py [server|init-db|health|test-log]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # 統一獲取應用和日誌記錄器
    try:
        app, logger = get_app_and_logger(config_name)
    except Exception as e:
        print(f"Failed to initialize application: {str(e)}")
        sys.exit(1)
    
    # 根據命令執行相應操作
    command_handlers = {
        'server': run_server,
        'init-db': init_database,
        'health': health_check,
        'test-log': test_logging_system
    }
    
    handler = command_handlers.get(command)
    if handler is None:
        logger.error(f"Unknown command: {command}")
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(command_handlers.keys())}")
        sys.exit(1)
    
    try:
        handler(app, logger, config_name)
    except Exception as e:
        logger.error(f"Command '{command}' failed: {str(e)}", exc_info=True)
        print(f"Command '{command}' failed: {str(e)}")
        sys.exit(1)

def run_server(app, logger, config_name):
    """啟動 Flask 服務器"""
    logger.info(f"Starting Flask server with config: {config_name}")
    
    # 從環境變數或默認值獲取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5002'))
    debug = config_name == 'development' and os.environ.get('DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Server configuration: host={host}, port={port}, debug={debug}")
    print(f"Starting server on {host}:{port} (debug={debug})")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

def init_database(app, logger, config_name):
    """初始化資料庫"""
    logger.info(f"Initializing database with config: {config_name}")
    print(f"Initializing database with config: {config_name}")
    
    with app.app_context():
        try:
            # 檢查是否有資料庫管理器
            if 'database_manager' not in app.extensions:
                logger.error("Database manager not found in extensions")
                print("Error: Database manager not configured")
                return
            
            from app.models import Base
            
            # 創建資料表
            engine = app.extensions['database_manager'].get_engine('primary')
            Base.metadata.create_all(engine)
            
            logger.info("Database tables created successfully")
            print("✓ Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
            print(f"✗ Database initialization failed: {str(e)}")
            raise

def health_check(app, logger, config_name):
    """系統健康檢查"""
    logger.info(f"Performing health check with config: {config_name}")
    print(f"Performing health check with config: {config_name}")
    print("=" * 50)
    
    with app.app_context():
        try:
            health_status = {'overall': 'healthy', 'services': {}}
            
            # 檢查日誌系統
            check_logging_system(app, logger, health_status)
            
            # 檢查資料庫
            check_database(app, logger, health_status)
            
            # 檢查其他服務
            check_redis(app, logger, health_status)
            check_jwt(app, logger, health_status)
            check_celery(app, logger, health_status)
            
            # 設置整體狀態
            unhealthy_services = [name for name, status in health_status['services'].items() 
                                if status == 'unhealthy']
            
            if unhealthy_services:
                health_status['overall'] = 'unhealthy'
                print(f"\n⚠️  Unhealthy services: {', '.join(unhealthy_services)}")
            else:
                print(f"\n✅ All services are healthy!")
            
            logger.info(f"Health check completed - Overall status: {health_status['overall']}")
            print(f"\nOverall System Health: {health_status['overall'].upper()}")
            print("=" * 50)
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            print("❌ Health check: CRITICAL FAILURE")
            raise

def check_logging_system(app, logger, health_status):
    """檢查日誌系統"""
    try:
        if 'logging' in app.extensions:
            log_stats = app.extensions['logging'].get_log_statistics()
            status = 'healthy' if log_stats['initialized'] else 'unhealthy'
            health_status['services']['logging'] = status
            
            print(f"📝 Logging System: {status.upper()}")
            print(f"   - Queues: {log_stats['queues']}")
            print(f"   - Handlers: {log_stats['handlers']}")
            print(f"   - Queue sizes: {log_stats['queue_sizes']}")
            
            logger.info(f"Logging system health check: {status} - {log_stats}")
        else:
            health_status['services']['logging'] = 'not_configured'
            print("📝 Logging System: NOT CONFIGURED")
    except Exception as e:
        health_status['services']['logging'] = 'unhealthy'
        logger.error(f"Logging system health check failed: {str(e)}")
        print("📝 Logging System: FAIL")

def check_database(app, logger, health_status):
    """檢查資料庫"""
    try:
        if 'database_manager' in app.extensions:
            db_health = app.extensions['database_manager'].health_check()
            status = 'healthy' if all(s.get('status') == 'healthy' for s in db_health.values()) else 'unhealthy'
            health_status['services']['database'] = status
            
            print(f"🗄️  Database: {status.upper()}")
            for db_name, db_status in db_health.items():
                print(f"   - {db_name}: {db_status.get('status', 'unknown').upper()}")
            
            logger.info(f"Database health check: {status} - {db_health}")
        else:
            health_status['services']['database'] = 'not_configured'
            print("🗄️  Database: NOT CONFIGURED")
    except Exception as e:
        health_status['services']['database'] = 'unhealthy'
        logger.error(f"Database health check failed: {str(e)}")
        print("🗄️  Database: FAIL")

def check_redis(app, logger, health_status):
    """檢查 Redis"""
    try:
        if 'data_pool_manager' in app.extensions:
            redis_health = app.extensions['data_pool_manager'].health_check()
            status = 'healthy' if all(s.get('status') == 'healthy' for s in redis_health.values()) else 'unhealthy'
            health_status['services']['redis'] = status
            print(f"🔴 Redis: {status.upper()}")
            logger.info(f"Redis health check: {status}")
        else:
            health_status['services']['redis'] = 'not_configured'
            print("🔴 Redis: NOT CONFIGURED")
    except Exception as e:
        health_status['services']['redis'] = 'unhealthy'
        logger.error(f"Redis health check failed: {str(e)}")
        print("🔴 Redis: FAIL")

def check_jwt(app, logger, health_status):
    """檢查 JWT"""
    try:
        if 'jwt_extension' in app.extensions:
            jwt_stats = app.extensions['jwt_extension'].get_token_statistics()
            active_tokens = jwt_stats.get('active_tokens', 0)
            health_status['services']['jwt'] = 'healthy'
            print(f"🔐 JWT: OK (Active tokens: {active_tokens})")
            logger.info(f"JWT health check: OK, active tokens: {active_tokens}")
        else:
            health_status['services']['jwt'] = 'not_configured'
            print("🔐 JWT: NOT CONFIGURED")
    except Exception as e:
        health_status['services']['jwt'] = 'unhealthy'
        logger.error(f"JWT health check failed: {str(e)}")
        print("🔐 JWT: FAIL")

def check_celery(app, logger, health_status):
    """檢查 Celery"""
    try:
        if 'celery' in app.extensions:
            celery = app.extensions['celery']
            inspect = celery.control.inspect()
            stats = inspect.stats()
            worker_count = len(stats) if stats else 0
            status = 'healthy' if worker_count > 0 else 'no_workers'
            health_status['services']['celery'] = status
            print(f"🐰 Celery: {status.upper()} (Workers: {worker_count})")
            logger.info(f"Celery health check: {status}, workers: {worker_count}")
        else:
            health_status['services']['celery'] = 'not_configured'
            print("🐰 Celery: NOT CONFIGURED")
    except Exception as e:
        health_status['services']['celery'] = 'unhealthy'
        logger.error(f"Celery health check failed: {str(e)}")
        print("🐰 Celery: FAIL")

def test_logging_system(app, logger, config_name):
    """測試日誌系統"""
    logger.info(f"Testing logging system with config: {config_name}")
    print(f"Testing logging system with config: {config_name}")
    print("=" * 50)
    
    # 測試不同模組的日誌記錄器
    loggers_to_test = ['app', 'auth', 'leave', 'notification', 'security']
    
    from app.extensions.logging_extension import get_logger
    
    for logger_name in loggers_to_test:
        print(f"📝 Testing {logger_name} logger...")
        test_logger = get_logger(logger_name)
        test_logger.info(f"Testing {logger_name} logger - INFO level")
        test_logger.warning(f"Testing {logger_name} logger - WARNING level")
        test_logger.error(f"Testing {logger_name} logger - ERROR level")
    
    # 測試結構化日誌
    logger.info("Structured logging test", extra={
        'user_id': 'test_user',
        'action': 'test_logging',
        'ip_address': '127.0.0.1',
        'request_id': 'test_12345'
    })
    
    # 獲取和顯示日誌統計信息
    try:
        with app.app_context():
            log_stats = app.extensions['logging'].get_log_statistics()
            print(f"\n📊 日誌系統統計:")
            print(f"   - 初始化狀態: {'✅' if log_stats['initialized'] else '❌'}")
            print(f"   - 隊列數量: {log_stats['queues']}")
            print(f"   - 處理器數量: {log_stats['handlers']}")
            print(f"   - 格式器數量: {log_stats['formatters']}")
            print(f"   - 隊列大小: {log_stats['queue_sizes']}")
    except Exception as e:
        print(f"❌ 無法獲取日誌統計: {str(e)}")
    
    # 檢查日誌文件
    print(f"\n📁 日誌文件檢查:")
    import os
    log_files_found = 0
    total_size = 0
    
    if hasattr(app.config, 'LOG_FILES'):
        for log_name, log_config in app.config.LOG_FILES.items():
            log_file = log_config['filename']
            if os.path.exists(log_file):
                file_size = os.path.getsize(log_file)
                total_size += file_size
                log_files_found += 1
                print(f"   ✅ {log_name}: {log_file} ({file_size} bytes)")
            else:
                print(f"   ❌ {log_name}: {log_file} (NOT FOUND)")
    
    print(f"\n📈 總結:")
    print(f"   - 找到日誌文件: {log_files_found}")
    print(f"   - 總日誌大小: {total_size} bytes")
    
    # 強制刷新所有日誌
    try:
        with app.app_context():
            app.extensions['logging'].flush_all_logs()
            print(f"   ✅ 所有日誌已刷新到文件")
    except Exception as e:
        print(f"   ❌ 日誌刷新失敗: {str(e)}")
    
    logger.info("=== Logging System Test Completed ===")
    print("=" * 50)
    print("🎉 日誌測試完成！")

if __name__ == '__main__':
    main()
