#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速檢查日誌文件是否正常寫入
"""

import os
import time

def check_all_log_files():
    """檢查所有日誌文件"""
    print("📁 檢查所有日誌文件狀態...")
    
    # 預期的日誌文件列表
    expected_files = [
        'app/logs/app.log',
        'app/logs/auth.log', 
        'app/logs/leave.log',
        'app/logs/notification.log',
        'app/logs/error.log',
        'app/logs/security.log',
        'app/logs/manual_test.log'  # 剛才手動測試創建的
    ]
    
    found_files = 0
    total_size = 0
    
    for log_file in expected_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            total_size += size
            
            if size > 0:
                found_files += 1
                print(f"✅ {log_file}: {size} bytes")
                
                # 顯示最後幾行內容
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            # 顯示最後2行
                            for line in lines[-2:]:
                                print(f"   📝 {line.strip()}")
                        print()  # 空行分隔
                except Exception as e:
                    print(f"   ❌ 讀取失敗: {e}")
            else:
                print(f"⚠️ {log_file}: 存在但為空")
        else:
            print(f"❌ {log_file}: 不存在")
    
    print(f"📊 總結: 找到 {found_files} 個有內容的日誌文件，總大小 {total_size} bytes")
    
    # 檢查 logs 目錄下的所有文件
    log_dir = 'app/logs'
    if os.path.exists(log_dir):
        all_files = os.listdir(log_dir)
        print(f"\n📁 {log_dir} 目錄下的所有文件:")
        for file in all_files:
            file_path = os.path.join(log_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"   📄 {file}: {size} bytes")
    
    return found_files > 0

def test_current_logging():
    """測試當前的日誌系統"""
    print("\n🧪 測試當前日誌系統...")
    
    try:
        # 直接測試日誌記錄
        import logging
        
        # 測試不同的日誌記錄器
        loggers = ['app', 'auth', 'leave', 'notification', 'security']
        
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            logger.info(f"快速測試 {logger_name} 日誌記錄器")
        
        print("✅ 日誌測試消息已發送")
        
        # 等待一下讓日誌寫入
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ 日誌測試失敗: {e}")
        return False

def verify_logging_working():
    """驗證日誌系統是否正常工作"""
    print("🔍 驗證日誌系統工作狀態...\n")
    
    # 1. 檢查現有文件
    initial_files = check_all_log_files()
    
    # 2. 測試新的日誌記錄
    if test_current_logging():
        print("\n⏳ 等待日誌寫入...")
        time.sleep(2)
        
        # 3. 再次檢查文件
        print("🔄 重新檢查日誌文件...")
        final_files = check_all_log_files()
        
        if final_files:
            print("\n🎉 日誌系統正常工作！")
            return True
    
    print("\n❌ 日誌系統可能有問題")
    return False

def check_logging_config():
    """檢查日誌配置"""
    print("🔧 檢查日誌配置...")
    
    try:
        import logging
        
        # 檢查根日誌記錄器
        root_logger = logging.getLogger()
        print(f"📋 根日誌記錄器:")
        print(f"   - 級別: {root_logger.level} ({logging.getLevelName(root_logger.level)})")
        print(f"   - 處理器數量: {len(root_logger.handlers)}")
        
        # 檢查每個處理器
        for i, handler in enumerate(root_logger.handlers):
            handler_type = type(handler).__name__
            print(f"   - 處理器 {i}: {handler_type}")
            if hasattr(handler, 'level'):
                print(f"     級別: {handler.level} ({logging.getLevelName(handler.level)})")
        
        # 檢查特定的日誌記錄器
        test_loggers = ['app', 'auth', 'leave']
        for logger_name in test_loggers:
            logger = logging.getLogger(logger_name)
            print(f"📝 {logger_name} 記錄器:")
            print(f"   - 級別: {logger.level}")
            print(f"   - 處理器數量: {len(logger.handlers)}")
            print(f"   - 傳播: {logger.propagate}")
        
        return len(root_logger.handlers) > 0
        
    except Exception as e:
        print(f"❌ 配置檢查失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 快速日誌系統檢查\n")
    
    # 1. 檢查配置
    config_ok = check_logging_config()
    print()
    
    # 2. 驗證工作狀態
    working_ok = verify_logging_working()
    
    # 3. 總結
    print("\n" + "="*50)
    if config_ok and working_ok:
        print("🎊 恭喜！日誌系統完全正常！")
        print("\n可以放心使用:")
        print("  python3 run.py test-log")
        print("  python3 run.py server")
    elif working_ok:
        print("✅ 日誌系統基本正常，可以寫入文件")
        print("⚠️ 但配置可能需要調整")
    else:
        print("❌ 日誌系統需要進一步修復")

if __name__ == "__main__":
    main()