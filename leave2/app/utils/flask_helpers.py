#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Flask 資料庫擴展模組
提供多資料庫連接池的 Flask 擴展功能
"""
from flask import Flask, current_app
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import text
from pathlib import Path
from contextlib import contextmanager
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱

# from app.extensions.logger import logger

# logging = logger(__name__)

if TYPE_CHECKING:
    from extensions.flask_database import FlaskDatabaseManager

# 便利函數
def get_db_manager() -> 'FlaskDatabaseManager':
    """獲取當前應用程式的資料庫管理器"""
    if not current_app:
        raise RuntimeError("必須在 Flask 應用程式上下文中使用")
    
    db_manager = current_app.extensions.get('database_manager')
    if not db_manager:
        raise RuntimeError("資料庫管理器未初始化")
    
    return db_manager

@contextmanager
def get_db_session(pool_name: str):
    """獲取資料庫會話的便利函數"""
    db_mgr = get_db_manager()
    with db_mgr.get_session(pool_name) as session:
        yield session

# 預定義的便利函數
@contextmanager
def get_mysql_session():
    """獲取 MySQL 資料庫會話的便利函數"""
    db_mgr = get_db_manager()
    with db_mgr.get_session('mysql_hr') as session:
        yield session

@contextmanager
def get_mssql_session():
    """獲取 MSSQL 資料庫會話的便利函數"""
    db_mgr = get_db_manager()
    with db_mgr.get_session('mssql_hr') as session:
        yield session

# 裝飾器
def with_database(pool_name: str):
    """資料庫會話裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with get_db_session(pool_name) as session:
                return func(session, *args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# 查詢建構器輔助類
class QueryBuilder:
    """簡單的查詢建構器"""
    
    def __init__(self, pool_name: str):
        self.pool_name = pool_name
        self.db_mgr = get_db_manager()
    
    def select(self, table: str, columns: str = "*", where: str = "", params: Dict[str, Any] = None) -> List[Any]:
        """執行 SELECT 查詢"""
        query = f"SELECT {columns} FROM {table}"
        if where:
            query += f" WHERE {where}"
        
        return self.db_mgr.execute_query(self.pool_name, query, params or {})
    
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """執行 INSERT 操作"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{key}" for key in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            with self.db_mgr.get_session(self.pool_name) as session:
                session.execute(text(query), data)
                session.commit()
            return True
        except Exception as e:
            logging.error(f"插入操作失敗: {str(e)}")
            return False
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: Dict[str, Any] = None) -> bool:
        """執行 UPDATE 操作"""
        set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        # 合併參數
        all_params = {**data}
        if where_params:
            all_params.update(where_params)
        
        try:
            with self.db_mgr.get_session(self.pool_name) as session:
                session.execute(text(query), all_params)
                session.commit()
            return True
        except Exception as e:
            logging.error(f"更新操作失敗: {str(e)}")
            return False
    
    def delete(self, table: str, where: str, params: Dict[str, Any] = None) -> bool:
        """執行 DELETE 操作"""
        query = f"DELETE FROM {table} WHERE {where}"
        
        try:
            with self.db_mgr.get_session(self.pool_name) as session:
                session.execute(text(query), params or {})
                session.commit()
            return True
        except Exception as e:
            logging.error(f"刪除操作失敗: {str(e)}")
            return False