#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
時區處理工具模組
"""
from datetime import datetime
import pytz
from flask import current_app

class TimezoneManager:
    """時區管理器"""
    
    @staticmethod
    def get_timezone(tz_name=None):
        """獲取時區物件"""
        if tz_name is None:
            tz_name = current_app.config.get('TIMEZONE_CONFIG', {}).get('DEFAULT_TIMEZONE', 'Asia/Ho_Chi_Minh')
        return pytz.timezone(tz_name)
    
    @staticmethod
    def get_local_now(tz_name=None):
        """獲取本地時間（時區感知）"""
        tz = TimezoneManager.get_timezone(tz_name)
        return datetime.now(tz)
    
    @staticmethod
    def get_local_datetime(tz_name=None):
        """獲取本地時間（naive datetime，用於資料庫）"""
        return TimezoneManager.get_local_now(tz_name).replace(tzinfo=None)
    
    @staticmethod
    def convert_timezone(dt, from_tz=None, to_tz=None):
        """轉換時區"""
        if from_tz is None:
            from_tz = TimezoneManager.get_timezone()
        if to_tz is None:
            to_tz = TimezoneManager.get_timezone()
            
        if dt.tzinfo is None:
            dt = from_tz.localize(dt)
        
        return dt.astimezone(to_tz)
    
    @staticmethod
    def format_local_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
        """格式化本地時間顯示"""
        if dt.tzinfo is None:
            # 如果是 naive datetime，假設是本地時間
            tz = TimezoneManager.get_timezone()
            dt = tz.localize(dt)
        
        display_tz_name = current_app.config.get('TIMEZONE_CONFIG', {}).get('DISPLAY_TIMEZONE', 'Asia/Ho_Chi_Minh')
        display_tz = pytz.timezone(display_tz_name)
        local_dt = dt.astimezone(display_tz)
        
        return local_dt.strftime(format_str)