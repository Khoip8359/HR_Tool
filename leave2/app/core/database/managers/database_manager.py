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
from flask import current_app

# 修正導入路徑
# from app.extensions.logger import logger
from app.core.database.base.db_connection import DBConfig, DBConnection
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱



# logging = logger(__name__)

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
        config_path: Optional[Path] = None
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
        
        # 從 Flask 應用配置或環境變數獲取配置路徑
        if current_app:
            self.config_path = Path(current_app.config.get('DB_CONFIG_PATH', ''))
        else:
            self.config_path = config_path or Path(os.getenv('DB_CONFIG_PATH', ''))
            
        if not self.config_path or not self.config_path.exists():
            raise ValueError(f"資料庫配置文件不存在: {self.config_path}")
        
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
            
            logging.info(f"資料庫連接池成功初始化: {self.db_type}://{self.host}:{self.port}/{self.database}")
            
        except Exception as e:
            logging.error(f"資料庫連接池初始化失敗: {str(e)}")
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
                logging.error(f"查詢執行失敗: {str(e)}")
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
                logging.error(f"批量執行失敗: {str(e)}")
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
            logging.info(f"資料庫連接池資源已釋放")
