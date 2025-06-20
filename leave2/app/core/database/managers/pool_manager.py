#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
資料庫連接池管理模組
提供多個資料庫連接池的創建、管理和使用功能
支援同時管理多個不同類型的資料庫（MySQL、PostgreSQL、SQLite、SQL Server等）
"""
import os
from typing import Optional, Dict, Any
from sqlalchemy import text
from contextlib import contextmanager
# import logging
from pathlib import Path

# 修正導入路徑
# from app.extensions.logger import logger
# from app.core.database.base.db_connection import DBConfig, DBConnection
from .database_manager import DatabaseManager


from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱


# logging = logger(__name__)

class DatabasePoolManager:
    """多資料庫連接池管理器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化多資料庫連接池管理器
        
        Args:
            config_path: 配置文件路徑
        """
        self._pools: Dict[str, DatabaseManager] = {}
        self.config_path = config_path or (Path(__file__).parent.parent / "config" / "config.txt")
    
    def add_pool(
        self,
        pool_name: str,
        db_type: str = None,
        section: str = "hr",
        **kwargs
    ) -> DatabaseManager:
        """
        添加新的資料庫連接池
        
        Args:
            pool_name: 連接池名稱
            db_type: 資料庫類型（可選，會從配置讀取）
            section: 配置區段名稱
            **kwargs: 其他連接池參數
            
        Returns:
            DatabaseManager: 新創建的資料庫管理器實例
        """
        if pool_name in self._pools:
            logging.warning(f"連接池名稱 '{pool_name}' 已存在，將替換現有連接池")
            self.remove_pool(pool_name)
        
        pool = DatabaseManager(
            db_type=db_type or "mysql",
            section=section,
            config_path=self.config_path,
            **kwargs
        )
        
        self._pools[pool_name] = pool
        logging.info(f"成功添加連接池: {pool_name}")
        return pool
    
    def get_pool(self, pool_name: str) -> DatabaseManager:
        """
        獲取指定的連接池
        
        Args:
            pool_name: 連接池名稱
            
        Returns:
            DatabaseManager: 資料庫管理器實例
        """
        if pool_name not in self._pools:
            available_pools = list(self._pools.keys())
            raise ValueError(f"連接池 '{pool_name}' 不存在，可用的連接池: {available_pools}")
        return self._pools[pool_name]
    
    def remove_pool(self, pool_name: str) -> None:
        """
        移除指定的連接池
        
        Args:
            pool_name: 連接池名稱
        """
        if pool_name in self._pools:
            self._pools[pool_name].dispose()
            del self._pools[pool_name]
            logging.info(f"已移除連接池: {pool_name}")
    
    def get_all_pools(self) -> Dict[str, DatabaseManager]:
        """
        獲取所有連接池
        
        Returns:
            Dict[str, DatabaseManager]: 所有連接池的字典
        """
        return self._pools.copy()
    
    def dispose_all(self) -> None:
        """釋放所有連接池資源"""
        for pool_name, pool in self._pools.items():
            pool.dispose()
            logging.info(f"已釋放連接池: {pool_name}")
        self._pools.clear()
        logging.info("所有連接池資源已釋放")

# 創建全局連接池管理器實例
pool_manager = DatabasePoolManager()

# 根據環境變數決定是否創建預設連接池
if os.getenv('AUTO_CREATE_POOLS', 'true').lower() == 'true':
    try:
        # 添加預設的連接池
        mysql_pool = pool_manager.add_pool(
            pool_name="mysql",
            db_type="mysql",
            section=os.getenv('MYSQL_SECTION', 'mysql'),
            pool_size=int(os.getenv('MYSQL_POOL_SIZE', '5')),
            max_overflow=int(os.getenv('MYSQL_MAX_OVERFLOW', '10')),
            pool_timeout=int(os.getenv('MYSQL_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('MYSQL_POOL_RECYCLE', '3600')),
            echo=os.getenv('MYSQL_ECHO', 'false').lower() == 'true'
        )
        logging.info("預設 MySQL 連接池創建成功")
    except Exception as e:
        logging.warning(f"預設 MySQL 連接池創建失敗: {str(e)}")

    try:
        mssql_pool = pool_manager.add_pool(
            pool_name="mssql",
            db_type="mssql",
            section=os.getenv('MSSQL_SECTION', 'hr'),
            pool_size=int(os.getenv('MSSQL_POOL_SIZE', '5')),
            max_overflow=int(os.getenv('MSSQL_MAX_OVERFLOW', '10')),
            pool_timeout=int(os.getenv('MSSQL_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('MSSQL_POOL_RECYCLE', '3600')),
            echo=os.getenv('MSSQL_ECHO', 'false').lower() == 'true'
        )
        logging.info("預設 MSSQL 連接池創建成功")
    except Exception as e:
        logging.warning(f"預設 MSSQL 連接池創建失敗: {str(e)}")

# 使用示例
"""
# 使用預設連接池
try:
    mysql_db = pool_manager.get_pool('mysql')
    with mysql_db.get_session() as session:
        result = session.execute(text("SELECT 1"))
        print("MySQL 連接測試成功")
except Exception as e:
    print(f"MySQL 連接測試失敗: {e}")

# 動態添加新連接池
postgres_pool = pool_manager.add_pool(
    pool_name="postgres",
    db_type="postgresql",
    section="reporting"
)

# 獲取連接池狀態
for pool_name, pool in pool_manager.get_all_pools().items():
    stats = pool.get_connection_stats()
    print(f"連接池 {pool_name} 狀態: {stats}")
"""