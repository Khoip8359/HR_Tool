# 診斷腳本 - debug_logging.py
"""
診斷日誌系統問題
"""

def debug_logging_system():
    """診斷日誌系統配置"""
    print("=== 診斷日誌系統 ===")
    
    # 1. 檢查 config.py 中的 LOG_FILES 配置
    try:
        from app.config import BaseConfig
        print(f"LOG_DIR: {BaseConfig.LOG_DIR}")
        print(f"LOG_FILES: {BaseConfig.LOG_FILES}")
        
        # 檢查是否有 LOG_FILES 配置
        if hasattr(BaseConfig, 'LOG_FILES') and BaseConfig.LOG_FILES:
            print(f"✓ 找到 {len(BaseConfig.LOG_FILES)} 個日誌文件配置")
            for name, config in BaseConfig.LOG_FILES.items():
                print(f"  - {name}: {config['filename']}")
        else:
            print("❌ 沒有找到 LOG_FILES 配置")
            
    except Exception as e:
        print(f"❌ 配置檢查失敗: {e}")
    
    # 2. 檢查日誌目錄和文件
    import os
    log_dir = 'logs'
    print(f"\n=== 檢查日誌目錄: {log_dir} ===")
    
    if os.path.exists(log_dir):
        print(f"✓ 日誌目錄存在")
        files = os.listdir(log_dir)
        if files:
            print(f"找到 {len(files)} 個文件:")
            for file in files:
                file_path = os.path.join(log_dir, file)
                size = os.path.getsize(file_path)
                print(f"  - {file}: {size} bytes")
        else:
            print("❌ 日誌目錄為空")
    else:
        print(f"❌ 日誌目錄不存在")
    
    # 3. 檢查當前日誌配置
    import logging
    print(f"\n=== 檢查日誌記錄器配置 ===")
    
    root_logger = logging.getLogger()
    print(f"根日誌記錄器級別: {root_logger.level}")
    print(f"根日誌記錄器處理器數量: {len(root_logger.handlers)}")
    
    for i, handler in enumerate(root_logger.handlers):
        print(f"處理器 {i}: {type(handler).__name__}")
        if hasattr(handler, 'baseFilename'):
            print(f"  文件: {handler.baseFilename}")
        if hasattr(handler, 'stream'):
            print(f"  流: {handler.stream}")

if __name__ == "__main__":
    debug_logging_system()