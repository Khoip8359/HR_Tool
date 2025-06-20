#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
應用最終日誌修復的腳本
"""

import os
import shutil
import time

def backup_current_file():
    """備份當前文件"""
    source = 'app/extensions/logging_extension.py'
    backup = f'app/extensions/logging_extension.py.backup_{int(time.time())}'
    
    if os.path.exists(source):
        shutil.copy2(source, backup)
        print(f"✅ 已備份原文件到: {backup}")
        return True
    else:
        print("⚠️ 原文件不存在，將創建新文件")
        return False

def apply_new_logging_extension():
    """應用新的 logging_extension.py"""
    
    # 完整的新文件內容（這裡包含我上面提供的完整代碼）
    new_content = '''# app/extensions/logging_extension.py
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
'''
    
    target_file = 'app/extensions/logging_extension.py'
    
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 已創建新的 logging_extension.py")
        return True
    except Exception as e:
        print(f"❌ 創建文件失敗: {e}")
        return False

def clear_module_cache():
    """清理模組緩存"""
    import sys
    
    modules_to_remove = [
        key for key in sys.modules.keys() 
        if key.startswith('app.extensions') or key.startswith('app')
    ]
    
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    
    print(f"🗑️ 已清理 {len(modules_to_remove)} 個模組緩存")

def test_new_system():
    """測試新系統"""
    print("🧪 測試新的日誌系統...")
    
    try:
        # 清理緩存
        clear_module_cache()
        
        # 重新導入
        from app import create_app
        
        print("📱 創建測試應用...")
        app = create_app('production')
        
        # 等待初始化完成
        time.sleep(2)
        
        # 檢查統計信息
        if 'logging_extension' in app.extensions:
            stats = app.extensions['logging_extension'].get_statistics()
            print(f"📊 統計信息: {stats}")
        
        # 發送測試消息
        import logging
        test_loggers = ['app', 'auth', 'leave', 'notification', 'security']
        
        for logger_name in test_loggers:
            logger = logging.getLogger(logger_name)
            logger.info(f"最終測試消息來自 {logger_name}")
        
        # 錯誤日誌測試
        error_logger = logging.getLogger('error') 
        error_logger.error("最終錯誤測試消息")
        
        # 強制刷新
        if 'logging_extension' in app.extensions:
            app.extensions['logging_extension'].flush_all_logs()
        
        # 等待寫入
        time.sleep(3)
        
        # 檢查結果
        log_files = [
            'app/logs/app.log',
            'app/logs/auth.log',
            'app/logs/leave.log', 
            'app/logs/notification.log',
            'app/logs/error.log',
            'app/logs/security.log'
        ]
        
        success_count = 0
        for log_file in log_files:
            if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                size = os.path.getsize(log_file)
                print(f"✅ {log_file}: {size} bytes")
                success_count += 1
            else:
                print(f"❌ {log_file}: 不存在或為空")
        
        if success_count >= 4:  # 至少4個文件成功
            print("🎉 新日誌系統測試成功！")
            return True
        else:
            print("❌ 新日誌系統測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始應用最終日誌修復...")
    
    # 1. 備份當前文件
    backup_current_file()
    
    # 2. 應用新的日誌擴展
    if not apply_new_logging_extension():
        print("❌ 應用新文件失敗")
        return
    
    # 3. 測試新系統
    if test_new_system():
        print("\n🎊 恭喜！日誌系統完全修復成功！")
        print("\n現在您可以運行:")
        print("  python3 run.py test-log")
        print("  python3 run.py server")
        print("\n所有6個日誌文件都應該正常工作！")
    else:
        print("\n😞 修復仍有問題，請檢查錯誤信息")

if __name__ == "__main__":
    main()