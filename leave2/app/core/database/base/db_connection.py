import configparser
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from urllib.parse import quote_plus
# from app.extensions.logger import logger
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱
# import logging

# logger = logging.getLogger(__name__)

class DBConfig:
    def __init__(self, config_path: Path, section: str):
        self.config_path = config_path
        self.section = section
        self.config = {}
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        cf = configparser.ConfigParser()
        cf.read(self.config_path, encoding='utf-8')
        
        if not cf.has_section(self.section):
            available_sections = cf.sections()
            raise ValueError(f"找不到 section: {self.section}, 可用的 sections: {available_sections}")
        
        self.config = dict(cf[self.section])
        logger.info(f"成功載入配置 section: {self.section}")

    @property
    def db_type(self):
        return self.config.get('type', '').lower()

    @property
    def host(self):
        return self.config.get('host')

    @property
    def port(self):
        return int(self.config.get('port', 3306 if self.db_type == 'mysql' else 1433))

    @property
    def user(self):
        return self.config.get('user')

    @property
    def password(self):
        return self.config.get('password')

    @property
    def database(self):
        return self.config.get('database')

class DBConnection:
    def __init__(self, config_path: Path, section: str, **kwargs):
        self.conf = DBConfig(config_path, section)
        
        # 支援額外的連接池參數
        self.pool_size = kwargs.get('pool_size', 5)
        self.max_overflow = kwargs.get('max_overflow', 10)
        self.pool_timeout = kwargs.get('pool_timeout', 30)
        self.pool_recycle = kwargs.get('pool_recycle', 3600)
        self.echo = kwargs.get('echo', False)
        
        self.engine = self._create_engine()
        self._session_maker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def _create_engine(self):
        db_type = self.conf.db_type
        
        try:
            if db_type == 'mysql':
                    conn_str = (
                        f"mysql+pymysql://{self.conf.user}:{quote_plus(self.conf.password)}"
                        f"@{self.conf.host}:{self.conf.port}/{self.conf.database}"
                        f"?charset=utf8mb4"
                    )
            elif db_type == 'mssql':
                user = quote_plus(self.conf.user)
                password = quote_plus(self.conf.password)
                conn_str = (
                    f"mssql+pymssql://{user}:{password}"
                    f"@{self.conf.host}:{self.conf.port}/{self.conf.database}"
                )
            else:
                raise ValueError(f"不支援的資料庫類型: {db_type}")
            
            engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                pool_recycle=self.pool_recycle,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                echo=self.echo
            )
            
            logger.info(f"成功創建 {db_type} 資料庫引擎: {self.conf.host}:{self.conf.port}/{self.conf.database}")
        
            return engine
        except Exception as e:
            logger.error(f"創建資料庫引擎失敗: {str(e)}")
            raise
        
    @contextmanager
    def get_session(self) -> Session:
        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"資料庫操作失敗: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_connection_stats(self):
        """獲取連接池統計"""
        if not self.engine:
            return {}
        
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checkedin': pool.checkedin(),
            'overflow': pool.overflow(),
            'checkedout': pool.checkedout(),
            'max_overflow': pool._max_overflow,
            'timeout': pool._timeout,
            'recycle': pool._recycle,
            'db_type': self.conf.db_type,
            'host': self.conf.host,
            'port': self.conf.port,
            'database': self.conf.database
        }

    def dispose(self):
        """釋放連接池資源"""
        if self.engine:
            self.engine.dispose()
            logger.info("資料庫引擎已釋放")