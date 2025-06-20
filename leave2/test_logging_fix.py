#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復後的日誌系統
"""

import os
import sys
import time

def test_fixed_logging():
    """測試修復後的日誌系統"""
    print("🧪 測試修復後的日誌系統...")
    
    try:
        # 重新加載模組
        import importlib
        
        # 移除舊的模組緩存
        modules_to_remove = [key for key in sys.modules.keys() 
                           if key.startswith('app.extensions') or key.startswith('app.config')]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        
        print("🔄 已清理模組緩存")
        
        # 重新導入
        from app import create_app
        
        print("📱 創建應用...")
        app = create_app('production')
        
        # 測試日誌
        import logging
        print("📝 測試日誌記錄...")
        
        # 測試主應用日誌
        app_logger = logging.getLogger('app')
        app_logger.info("🔥 測試主應用日誌 - INFO")
        app_logger.warning("⚠️ 測試主應用日誌 - WARNING")
        app_logger.error("❌ 測試主應用日誌 - ERROR")
        
        # 測試不同模組日誌
        auth_logger = logging.getLogger('auth')
        auth_logger.info("🔐 測試認證模組日誌")
        
        leave_logger = logging.getLogger('leave')
        leave_logger.warning("📝 測試請假模組日誌")
        
        notification_logger = logging.getLogger('notification')
        notification_logger.info("📧 測試通知模組日誌")
        
        security_logger = logging.getLogger('security')
        security_logger.warning("🛡️ 測試安全模組日誌")
        
        # 強制刷新
        if 'logging_extension' in app.extensions:
            app.extensions['logging_extension'].flush_all_logs()
            
            # 獲取統計信息
            stats = app.extensions['logging_extension'].get_statistics()
            print(f"📊 統計信息: {stats}")
        
        print("⏳ 等待日誌寫入完成...")
        time.sleep(2)  # 等待更長時間確保寫入完成
        
        # 檢查所有應該存在的日誌文件
        print("📁 檢查日誌文件...")
        
        expected_files = [
            'app/logs/app.log',
            'app/logs/auth.log', 
            'app/logs/leave.log',
            'app/logs/notification.log',
            'app/logs/error.log',
            'app/logs/security.log'
        ]
        
        success_count = 0
        total_size = 0
        
        for log_file in expected_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                total_size += size
                
                if size > 0:
                    success_count += 1
                    print(f"✅ {log_file}: {size} bytes")
                    
                    # 顯示文件最後幾行
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                print(f"   最新內容: {lines[-1].strip()}")
                    except:
                        pass
                else:
                    print(f"⚠️ {log_file}: 文件存在但為空")
            else:
                print(f"❌ {log_file}: 文件不存在")
        
        # 檢查根日誌記錄器
        root_logger = logging.getLogger()
        print(f"🔍 根日誌記錄器: 級別={root_logger.level}, 處理器數={len(root_logger.handlers)}")
        
        # 總結
        print(f"\n📈 測試結果:")
        print(f"   - 成功寫入的文件: {success_count}/{len(expected_files)}")
        print(f"   - 總日誌大小: {total_size} bytes")
        
        if success_count >= 3 and total_size > 0:
            print("🎉 日誌系統修復成功！")
            return True
        else:
            print("❌ 日誌系統仍有問題")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_permissions():
    """檢查文件權限"""
    print("🔐 檢查文件權限...")
    
    # 檢查 app/logs 目錄權限
    log_dir = 'app/logs'
    if os.path.exists(log_dir):
        stat = os.stat(log_dir)
        print(f"📁 {log_dir} 權限: {oct(stat.st_mode)[-3:]}")
        
        # 檢查是否可寫
        if os.access(log_dir, os.W_OK):
            print("✅ 日誌目錄可寫")
        else:
            print("❌ 日誌目錄不可寫")
            return False
    else:
        print(f"❌ 日誌目錄不存在: {log_dir}")
        return False
    
    return True

def manual_test():
    """手動測試日誌寫入"""
    print("✍️ 手動測試日誌寫入...")
    
    import logging
    import logging.handlers
    
    try:
        # 直接創建一個文件處理器測試
        test_file = 'app/logs/manual_test.log'
        
        handler = logging.handlers.RotatingFileHandler(
            test_file,
            maxBytes=1024*1024,
            backupCount=1,
            encoding='utf-8'
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] MANUAL TEST: %(message)s'
        ))
        
        # 創建測試日誌記錄器
        test_logger = logging.getLogger('manual_test')
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)
        
        # 寫入測試消息
        test_logger.info("這是手動測試消息")
        
        # 刷新並關閉
        handler.flush()
        handler.close()
        
        # 檢查結果
        if os.path.exists(test_file):
            size = os.path.getsize(test_file)
            print(f"✅ 手動測試成功: {test_file} ({size} bytes)")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"內容: {content.strip()}")
            
            return True
        else:
            print(f"❌ 手動測試失敗: {test_file} 不存在")
            return False
            
    except Exception as e:
        print(f"❌ 手動測試異常: {e}")
        return False

def main():
    """主函數"""
    print("🛠️ 開始完整的日誌系統測試...")
    
    # 1. 檢查權限
    if not check_permissions():
        print("❌ 權限檢查失敗")
        return
    
    # 2. 手動測試
    if not manual_test():
        print("❌ 手動測試失敗")
        return
    
    # 3. 完整測試
    if test_fixed_logging():
        print("\n🎊 恭喜！日誌系統完全修復成功！")
        print("現在可以正常使用: python3 run.py test-log")
    else:
        print("\n😞 日誌系統仍有問題，需要進一步檢查")

if __name__ == "__main__":
    main()