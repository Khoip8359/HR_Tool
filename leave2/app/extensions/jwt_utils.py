#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
JWT 工具類模組
"""
from typing import Dict, Any, List
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱

# import logging

# logger = logging.getLogger(__name__)

class JWTUtils:
    """JWT 工具類（增強版）"""
    
    @staticmethod
    def create_user_permissions(user_data: Dict[str, Any]) -> List[str]:
        """
        根據用戶數據創建權限列表
        
        Args:
            user_data: 用戶數據
            
        Returns:
            list: 權限列表
        """
        permissions = ['user:read']  # 基本權限
        
        # 根據部門添加權限
        department = user_data.get('department', '').lower()
        if department == 'hr':
            permissions.extend(['hr:read', 'employee:read'])
        elif department == 'finance':
            permissions.extend(['finance:read', 'financial_records:read'])
        elif department == 'it':
            permissions.extend(['it:read', 'system:read'])
        
        # 如果是主管，添加管理權限
        if user_data.get('is_manager', False):
            permissions.extend([
                'user:write',
                'employee:read',     # 主管必須有員工讀取權限
                'employee:write',
                'subordinates:read',
                'reports:read'
            ])
        
        # 調試信息
        logger.debug(f"為用戶 {user_data.get('username')} 創建權限:")
        logger.debug(f"  部門: {department}")
        logger.debug(f"  是否主管: {user_data.get('is_manager', False)}")
        logger.debug(f"  下屬數量: {user_data.get('subordinates_count', 0)}")
        logger.debug(f"  最終權限: {list(set(permissions))}")
        
        # 移除重複權限
        return list(set(permissions))
    
    @staticmethod
    def extract_user_info_from_ad_result(ad_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        從 AD 認證結果中提取用戶信息
        
        Args:
            ad_result: AD 認證結果
            
        Returns:
            dict: 格式化的用戶信息
        """
        if not ad_result.get('success') or not ad_result.get('data'):
            logger.warning("AD 認證結果無效或缺少數據")
            return {}
        
        user_data = ad_result['data'].get('user', {})
        subordinates = ad_result['data'].get('subordinates', [])
        
        # 判斷是否為主管
        is_manager = len(subordinates) > 0
        
        user_info = {
            'username': user_data.get('username', ''),
            'user_id': user_data.get('employee_id', ''),
            'sam_account': user_data.get('sam_account', ''),
            'display_name': user_data.get('display_name', ''),
            'email': user_data.get('email', ''),
            'department': user_data.get('department', ''),
            'title': user_data.get('title', ''),
            'is_manager': is_manager,
            'subordinates_count': len(subordinates),
            'subordinates': subordinates, # 下屬列表 add 2025-06-16
            'manager_info': ad_result['data'].get('manager', {})
        }
        
        # 創建權限列表
        user_info['permissions'] = JWTUtils.create_user_permissions(user_info)
        
        logger.info(f"成功提取用戶信息: {user_info['username']}, 權限數量: {len(user_info['permissions'])}")
        
        return user_info
    
    @staticmethod
    def validate_token_payload(payload: Dict[str, Any]) -> bool:
        """
        驗證 token payload 的完整性
        
        Args:
            payload: token payload
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['username', 'user_id', 'exp', 'type']
        
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Token payload 缺少必要欄位: {field}")
                return False
        
        return True
    
    @staticmethod
    def format_user_response(user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化用戶響應數據
        
        Args:
            user_info: 用戶信息
            
        Returns:
            dict: 格式化後的響應數據
        """
        return {
            'username': user_info.get('username'),
            'display_name': user_info.get('display_name'),
            'email': user_info.get('email'),
            'department': user_info.get('department'),
            'title': user_info.get('title'),
            'is_manager': user_info.get('is_manager', False),
            'permissions': user_info.get('permissions', [])
        }