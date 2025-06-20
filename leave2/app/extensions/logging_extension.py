# app/extensions/logging_extension.py
"""
Flask 日誌擴展 - 完全重寫版本
確保所有日誌文件都能正確創建和寫入
"""

import logging
import logging.handlers
import os
import atexit
import queue
import time
from typing import Dict

class CompleteLoggingExtension:
    """完整的 Flask 日誌擴展"""
    
    def __init__(self):
        self.listeners = []
        self.file_handlers = []
        self.queue_handlers = []
        self._initialized = False
        self.log_files_created = []
    
    def init_app(self, app):
        """初始化日誌系統"""
        if self._initialized:
            print("⚠️ 日誌系統已初始化，跳過")
            return
        
        print("🔧 開始完整日誌系統初始化...")
        
        try:
            # 1. 獲取配置
            log_dir = getattr(app.config, 'LOG_DIR', 'logs')
            log_files = getattr(app.config, 'LOG_FILES', {})
            console_enabled = getattr(app.config, 'CONSOLE_LOG_ENABLED', True)
            
            print(f"📁 日誌目錄: {log_dir}")
            print(f"📋 配置文件數量: {len(log_files)}")
            
            # 2. 確保目錄存在
            os.makedirs(log_dir, exist_ok=True)
            
            # 3. 如果沒有配置，使用默認配置
            if not log_files:
                log_files = self._create_default_config(log_dir)
                print("📝 使用默認配置")
            
            # 4. 完全重置日誌系統
            self._reset_logging_system()
            
            # 5. 創建所有日誌處理器
            self._create_all_handlers(log_files, console_enabled)
            
            # 6. 設置根日誌記錄器
            self._setup_root_logger()
            
            # 7. 驗證設置
            self._verify_complete_setup()
            
            # 8. 註冊清理函數
            atexit.register(self._cleanup)
            
            self._initialized = True
            app.extensions['logging_extension'] = self
            
            # 9. 測試所有日誌文件
            self._test_all_loggers()
            
            print("🎉 完整日誌系統初始化成功！")
            
        except Exception as e:
            print(f"❌ 日誌系統初始化失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_default_config(self, log_dir):
        """創建默認日誌配置"""
        return {
            'app': {
                'filename': os.path.join(log_dir, 'app.log'),
                'level': logging.INFO,
                'max_bytes': 10*1024*1024,
                'backup_count': 5
            },
            'auth': {
                'filename': os.path.join(log_dir, 'auth.log'),
                'level': logging.INFO,
                'max_bytes': 5*1024*1024,
                'backup_count': 3
            },
            'leave': {
                'filename': os.path.join(log_dir, 'leave.log'),
                'level': logging.INFO,
                'max_bytes': 5*1024*1024,
                'backup_count': 3
            },
            'notification': {
                'filename': os.path.join(log_dir, 'notification.log'),
                'level': logging.INFO,
                'max_bytes': 5*1024*1024,
                'backup_count': 3
            },
            'error': {
                'filename': os.path.join(log_dir, 'error.log'),
                'level': logging.ERROR,
                'max_bytes': 10*1024*1024,
                'backup_count': 10
            },
            'security': {
                'filename': os.path.join(log_dir, 'security.log'),
                'level': logging.WARNING,
                'max_bytes': 5*1024*1024,
                'backup_count': 10
            }
        }
    
    def _reset_logging_system(self):
        """完全重置日誌系統"""
        print("🧹 重置日誌系統...")
        
        # 獲取根日誌記錄器
        root_logger = logging.getLogger()
        
        # 移除所有現有處理器
        for handler in root_logger.handlers[:]:
            try:
                handler.flush()
                handler.close()
                root_logger.removeHandler(handler)
            except:
                pass
        
        # 清除所有子日誌記錄器的處理器
        for name in ['app', 'auth', 'leave', 'notification', 'security', 'error']:
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                try:
                    handler.flush()
                    handler.close()
                    logger.removeHandler(handler)
                except:
                    pass
            logger.propagate = True  # 確保傳播到根日誌記錄器
        
        # 設置根日誌記錄器級別
        root_logger.setLevel(logging.INFO)
        
        print("✅ 日誌系統重置完成")
    
    def _create_all_handlers(self, log_files: Dict, console_enabled: bool):
        """創建所有日誌處理器"""
        print("🔨 創建日誌處理器...")
        
        # 創建格式器
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 為每個日誌文件創建處理器
        for log_name, log_config in log_files.items():
            success = self._create_single_file_handler(
                log_name, log_config, file_formatter
            )
            if success:
                self.log_files_created.append(log_name)
        
        # 創建控制台處理器
        if console_enabled:
            self._create_console_handler(console_formatter)
        
        print(f"✅ 創建了 {len(self.queue_handlers)} 個隊列處理器")
        print(f"✅ 創建了 {len(self.listeners)} 個監聽器")
        print(f"✅ 將創建 {len(self.log_files_created)} 個日誌文件")
    
    def _create_single_file_handler(self, log_name: str, log_config: Dict, formatter):
        """為單個日誌文件創建處理器"""
        try:
            print(f"  📄 配置 {log_name}: {log_config['filename']}")
            
            # 1. 創建隊列
            log_queue = queue.Queue()
            
            # 2. 創建隊列處理器
            queue_handler = logging.handlers.QueueHandler(log_queue)
            queue_handler.setLevel(log_config.get('level', logging.INFO))
            
            # 3. 創建文件處理器
            file_handler = logging.handlers.RotatingFileHandler(
                log_config['filename'],
                maxBytes=log_config.get('max_bytes', 10*1024*1024),
                backupCount=log_config.get('backup_count', 5),
                encoding='utf-8'
            )
            file_handler.setLevel(log_config.get('level', logging.INFO))
            file_handler.setFormatter(formatter)
            
            # 4. 創建隊列監聽器
            listener = logging.handlers.QueueListener(
                log_queue, 
                file_handler,
                respect_handler_level=True
            )
            
            # 5. 啟動監聽器
            listener.start()
            
            # 6. 保存引用
            self.listeners.append(listener)
            self.file_handlers.append(file_handler)
            self.queue_handlers.append(queue_handler)
            
            print(f"    ✅ {log_name} 處理器創建成功")
            return True
            
        except Exception as e:
            print(f"    ❌ {log_name} 處理器創建失敗: {e}")
            return False
    
    def _create_console_handler(self, formatter):
        """創建控制台處理器"""
        try:
            print("  🖥️ 配置控制台處理器...")
            
            # 1. 創建隊列
            console_queue = queue.Queue()
            
            # 2. 創建隊列處理器
            queue_handler = logging.handlers.QueueHandler(console_queue)
            queue_handler.setLevel(logging.INFO)
            
            # 3. 創建控制台處理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            
            # 4. 創建隊列監聽器
            listener = logging.handlers.QueueListener(
                console_queue, 
                console_handler,
                respect_handler_level=True
            )
            
            # 5. 啟動監聽器
            listener.start()
            
            # 6. 保存引用
            self.listeners.append(listener)
            self.queue_handlers.append(queue_handler)
            
            print("    ✅ 控制台處理器創建成功")
            
        except Exception as e:
            print(f"    ❌ 控制台處理器創建失敗: {e}")
    
    def _setup_root_logger(self):
        """設置根日誌記錄器"""
        print("🌳 設置根日誌記錄器...")
        
        root_logger = logging.getLogger()
        
        # 添加所有隊列處理器到根日誌記錄器
        for queue_handler in self.queue_handlers:
            root_logger.addHandler(queue_handler)
        
        print(f"✅ 根日誌記錄器設置完成，添加了 {len(self.queue_handlers)} 個處理器")
    
    def _verify_complete_setup(self):
        """驗證完整設置"""
        print("🔍 驗證日誌系統設置...")
        
        root_logger = logging.getLogger()
        
        # 檢查根日誌記錄器
        if len(root_logger.handlers) == 0:
            raise Exception("❌ 根日誌記錄器沒有處理器！")
        
        if len(self.listeners) == 0:
            raise Exception("❌ 沒有隊列監聽器！")
        
        print(f"✅ 根日誌記錄器: {len(root_logger.handlers)} 個處理器")
        print(f"✅ 隊列監聽器: {len(self.listeners)} 個")
        print(f"✅ 文件處理器: {len(self.file_handlers)} 個")
        print("✅ 日誌系統驗證通過")
    
    def _test_all_loggers(self):
        """測試所有日誌記錄器"""
        print("🧪 測試所有日誌記錄器...")
        
        test_messages = {
            'app': '應用日誌測試消息',
            'auth': '認證日誌測試消息',
            'leave': '請假日誌測試消息',
            'notification': '通知日誌測試消息',
            'security': '安全日誌測試消息',
            'error': '錯誤日誌測試消息'
        }
        
        for logger_name, message in test_messages.items():
            try:
                logger = logging.getLogger(logger_name)
                if logger_name == 'error':
                    logger.error(message)
                elif logger_name == 'security':
                    logger.warning(message)
                else:
                    logger.info(message)
                print(f"  ✅ {logger_name}: 測試消息已發送")
            except Exception as e:
                print(f"  ❌ {logger_name}: 測試失敗 - {e}")
        
        # 強制刷新所有處理器
        self.flush_all_logs()
        print("🔄 所有測試消息已刷新")
    
    def flush_all_logs(self):
        """強制刷新所有日誌"""
        # 等待隊列處理
        time.sleep(0.5)
        
        # 刷新所有文件處理器
        for handler in self.file_handlers:
            try:
                handler.flush()
            except:
                pass
    
    def get_statistics(self):
        """獲取統計信息"""
        return {
            'initialized': self._initialized,
            'listeners': len(self.listeners),
            'file_handlers': len(self.file_handlers),
            'queue_handlers': len(self.queue_handlers),
            'root_handlers': len(logging.getLogger().handlers),
            'log_files_created': self.log_files_created
        }
    
    def _cleanup(self):
        """清理資源"""
        print("🧹 正在清理完整日誌系統...")
        
        # 停止所有監聽器
        for i, listener in enumerate(self.listeners):
            try:
                listener.stop()
                print(f"  ✅ 停止監聽器 {i}")
            except Exception as e:
                print(f"  ❌ 停止監聽器 {i} 失敗: {e}")
        
        # 刷新並關閉所有文件處理器
        for i, handler in enumerate(self.file_handlers):
            try:
                handler.flush()
                handler.close()
                print(f"  ✅ 關閉文件處理器 {i}")
            except Exception as e:
                print(f"  ❌ 關閉文件處理器 {i} 失敗: {e}")
        
        # 清理引用
        self.listeners.clear()
        self.file_handlers.clear()
        self.queue_handlers.clear()
        self.log_files_created.clear()
        self._initialized = False
        
        print("🎉 完整日誌系統清理完成")

# 創建全局實例
logging_extension = CompleteLoggingExtension()

def setup_logging(app):
    """設置日誌系統"""
    return logging_extension.init_app(app)

def get_logger(name='app'):
    """獲取日誌記錄器"""
    return logging.getLogger(name)

# 向後兼容
def setup_queue_logging(app):
    """向後兼容的設置函數"""
    return setup_logging(app)
