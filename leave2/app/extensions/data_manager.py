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
# from app.extensions.logger import logger
# 修正導入路徑
from app.core.database.base.db_connection import DBConfig, DBConnection
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱




# logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫連接池管理類別"""
    
    def __init__(
        self,
        db_type: str = "mysql",
        host: str = None,
        port: int = None,
        database: str = None,
        username: str = None,
        password: str = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        section: str = "hr",
        config_path: Path = None
    ):
        """
        初始化資料庫連接池管理器
        
        Args:
            db_type: 資料庫類型 (mysql, postgresql, sqlite, mssql)
            section: 配置區段名稱，預設為 "hr"
            config_path: 配置檔案路徑
            pool_size: 連接池大小
            max_overflow: 最大溢出連接數
            pool_timeout: 連接池超時時間（秒）
            pool_recycle: 連接回收時間（秒）
            echo: 是否輸出 SQL 語句
        """
        self.db_type = db_type.lower()
        self.section = section
            # 日誌檔案路徑配置
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        CONFIG_FILE = os.path.join(BASE_DIR, 'config') + '/config.txt'

        self.config_path = config_path or CONFIG_FILE
        # self.config_path = config_path or (Path(__file__).parent.parent / "config" / "config.txt")
        
        # 連接池設置
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        
        # 初始化資料庫連接
        self._init_connection(host, port, database, username, password)
    
    def _init_connection(self, host, port, database, username, password):
        """初始化資料庫連接"""
        try:
            # 如果提供了直接參數，創建臨時配置檔案
            if all([host, database, username is not None]):
                self._create_temp_config(host, port, database, username, password)
            
            # 使用 DBConnection 來管理連接
            self.db_conn = DBConnection(
                config_path=self.config_path,
                section=self.section,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                echo=self.echo
            )
            
            # 從配置中獲取連接信息
            self.host = self.db_conn.conf.host
            self.port = self.db_conn.conf.port
            self.database = self.db_conn.conf.database
            self.username = self.db_conn.conf.user
            self.password = self.db_conn.conf.password
            self.db_type = self.db_conn.conf.db_type
            
            logger.info(f"資料庫連接池成功初始化: {self.db_type}://{self.host}:{self.port}/{self.database}")
            
        except Exception as e:
            logger.error(f"資料庫連接池初始化失敗: {str(e)}")
            raise
    
    def _create_temp_config(self, host, port, database, username, password):
        """創建臨時配置（如果需要）"""
        # 這裡可以實現臨時配置的邏輯
        # 或者直接修改現有配置
        pass
    
    @property
    def engine(self):
        """獲取 SQLAlchemy engine"""
        return self.db_conn.engine
    
    @contextmanager
    def get_session(self):
        """
        獲取資料庫會話的上下文管理器
        
        Yields:
            Session: 資料庫會話對象
        """
        with self.db_conn.get_session() as session:
            yield session
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        執行 SQL 查詢
        
        Args:
            query: SQL 查詢語句
            params: 查詢參數
            
        Returns:
            Any: 查詢結果
        """
        with self.get_session() as session:
            try:
                result = session.execute(text(query), params or {})
                return result.fetchall()
            except Exception as e:
                logger.error(f"查詢執行失敗: {str(e)}")
                raise
    
    def execute_many(self, query: str, params_list: list) -> None:
        """
        批量執行 SQL 語句
        
        Args:
            query: SQL 語句
            params_list: 參數列表
        """
        with self.get_session() as session:
            try:
                for params in params_list:
                    session.execute(text(query), params)
                session.commit()
            except Exception as e:
                logger.error(f"批量執行失敗: {str(e)}")
                raise
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        獲取連接池統計信息
        
        Returns:
            dict: 連接池統計信息
        """
        return self.db_conn.get_connection_stats()
    
    def dispose(self) -> None:
        """釋放所有連接池資源"""
        if hasattr(self, 'db_conn'):
            self.db_conn.dispose()
            logger.info(f"資料庫連接池資源已釋放")

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
            logger.warning(f"連接池名稱 '{pool_name}' 已存在，將替換現有連接池")
            self.remove_pool(pool_name)
        
        pool = DatabaseManager(
            db_type=db_type or "mysql",
            section=section,
            config_path=self.config_path,
            **kwargs
        )
        
        self._pools[pool_name] = pool
        logger.info(f"成功添加連接池: {pool_name}")
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
            logger.info(f"已移除連接池: {pool_name}")
    
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
            logger.info(f"已釋放連接池: {pool_name}")
        self._pools.clear()
        logger.info("所有連接池資源已釋放")

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
        logger.info("預設 MySQL 連接池創建成功")
    except Exception as e:
        logger.warning(f"預設 MySQL 連接池創建失敗: {str(e)}")

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
        logger.info("預設 MSSQL 連接池創建成功")
    except Exception as e:
        logger.warning(f"預設 MSSQL 連接池創建失敗: {str(e)}")

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