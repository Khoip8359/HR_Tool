#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Flask 資料庫擴展模組
提供多資料庫連接池的 Flask 擴展功能
"""
from flask import Flask, current_app
from contextlib import contextmanager
import atexit
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from pathlib import Path
import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# 修正導入路徑 - 使用相對導入
from .data_manager import DatabasePoolManager, DatabaseManager
# from .logger import logger
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱


class FlaskDatabaseManager:
    """Flask 資料庫管理擴展"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.pool_manager = DatabasePoolManager()
        self.app = app
        self._pool_configs = []  # 儲存連接池配置
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化 Flask 應用程式"""
        self.app = app
        
        # 從應用程式配置讀取資料庫配置
        self._load_config_from_app()
        
        # 初始化資料庫連接池
        self._init_database_pools()
        
        # 註冊應用程式關閉時的清理函數
        atexit.register(self._cleanup)
        
        # 將資料庫管理器附加到應用程式
        app.extensions['database_manager'] = self
        
        logger.info("Flask 資料庫管理器初始化完成")
    
    def _load_config_from_app(self):
        """從 Flask 應用程式配置載入資料庫配置"""
        # 從 Flask 配置讀取資料庫配置
        db_configs = self.app.config.get('DATABASE_CONFIGS', [])
        
        # 驗證配置
        self._validate_configs(db_configs)
        
        # 設置配置路徑
        config_path = Path(self.app.config.get('DB_CONFIG_PATH', ''))
        if not config_path.exists():
            raise ValueError(f"資料庫配置文件不存在: {config_path}")
        
        self._pool_configs = db_configs
        self.config_path = config_path
        logger.info(f"載入了 {len(db_configs)} 個資料庫配置")
    
    def _validate_configs(self, configs: list):
        """驗證資料庫配置"""
        required_fields = ['pool_name', 'section']
        for config in configs:
            # 檢查必要欄位
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"資料庫配置缺少必要欄位: {field}")
            
            # 驗證連接池大小
            pool_size = config.get('pool_size', 5)
            if not isinstance(pool_size, int) or pool_size < 1:
                raise ValueError(f"無效的連接池大小: {pool_size}")
            
            # 驗證最大溢出連接數
            max_overflow = config.get('max_overflow', 10)
            if not isinstance(max_overflow, int) or max_overflow < 0:
                raise ValueError(f"無效的最大溢出連接數: {max_overflow}")
            
            # 驗證超時設置
            pool_timeout = config.get('pool_timeout', 30)
            if not isinstance(pool_timeout, int) or pool_timeout < 1:
                raise ValueError(f"無效的連接池超時時間: {pool_timeout}")
            
            # 驗證回收時間
            pool_recycle = config.get('pool_recycle', 3600)
            if not isinstance(pool_recycle, int) or pool_recycle < 1:
                raise ValueError(f"無效的連接回收時間: {pool_recycle}")
    
    def _init_database_pools(self):
        """初始化所有資料庫連接池"""
        for config in self._pool_configs:
            try:
                pool_name = config['pool_name']
                
                # 創建資料庫管理器實例
                self.pool_manager.add_pool(
                    pool_name=pool_name,
                    section=config.get('section', 'hr'),
                    # config_path=self.config_path,
                    pool_size=config.get('pool_size', 5),
                    max_overflow=config.get('max_overflow', 10),
                    pool_timeout=config.get('pool_timeout', 30),
                    pool_recycle=config.get('pool_recycle', 3600),
                    echo=config.get('echo', False)
                )
                
                logger.info(f"連接池 '{pool_name}' 初始化成功")
                
            except Exception as e:
                logger.error(f"連接池 '{config.get('pool_name', 'unknown')}' 初始化失敗: {str(e)}")
                # 不要中斷，繼續初始化其他連接池
                continue
    
    def add_pool_config(self, pool_name: str, section: str, **kwargs):
        """動態添加連接池配置"""
        config = {
            'pool_name': pool_name,
            'section': section,
            **kwargs
        }
        
        self._pool_configs.append(config)
        
        # 如果應用程式已經初始化，立即創建連接池
        if self.app:
            try:
                self.pool_manager.add_pool(
                    pool_name=pool_name,
                    section=section,
                    **kwargs
                )
                logger.info(f"動態添加連接池 '{pool_name}' 成功")
            except Exception as e:
                logger.error(f"動態添加連接池 '{pool_name}' 失敗: {str(e)}")
                raise
    
    def get_pool(self, pool_name: str) -> DatabaseManager:
        """獲取指定的連接池"""
        return self.pool_manager.get_pool(pool_name)
    
    def get_all_pools(self) -> Dict[str, DatabaseManager]:
        """獲取所有連接池"""
        return self.pool_manager.get_all_pools()
    
    def get_pool_stats(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
        """獲取連接池統計信息"""
        if pool_name:
            pool = self.get_pool(pool_name)
            return {pool_name: pool.get_connection_stats()}
        else:
            stats = {}
            for name, pool in self.get_all_pools().items():
                stats[name] = pool.get_connection_stats()
            return stats
    
    def execute_query(self, pool_name: str, query: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """在指定連接池上執行查詢"""
        pool = self.get_pool(pool_name)
        return pool.execute_query(query, params)
    
    def execute_transaction(self, pool_name: str, operations: List[Dict[str, Any]]) -> bool:
        """在指定連接池上執行事務"""
        pool = self.get_pool(pool_name)
        
        with pool.get_session() as session:
            try:
                for operation in operations:
                    query = operation.get('query')
                    params = operation.get('params', {})
                    if query:
                        session.execute(text(query), params)
                
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"事務執行失敗: {str(e)}")
                raise
    
    @contextmanager
    def get_session(self, pool_name: str):
        """獲取指定連接池的會話上下文管理器"""
        pool = self.get_pool(pool_name)
        with pool.get_session() as session:
            yield session
    
    def _cleanup(self):
        """清理所有資源"""
        logger.info("正在清理資料庫連接池資源...")
        self.pool_manager.dispose_all()
