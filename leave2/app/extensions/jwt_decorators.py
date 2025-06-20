#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
JWT 裝飾器模組
"""
from functools import wraps
from flask import jsonify, current_app, g
from typing import List, Optional, Dict, Any
# import logging

# logger = logging.getLogger(__name__)
from app.extensions import get_logger

# 使用模組特定的 logger
logger = get_logger(__name__)  # 或者指定名稱



def get_enhanced_jwt_manager():
    """獲取增強 JWT 管理器實例"""
    if current_app:
        return current_app.extensions.get('enhanced_jwt_manager')
    return None

def jwt_required(optional: bool = False):
    """
    JWT 認證裝飾器（增強版）
    
    Args:
        optional: 是否可選認證（為 True 時，無令牌也可通過）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_mgr = get_enhanced_jwt_manager()
            if not jwt_mgr:
                return jsonify({'error': 'JWT 管理器未初始化'}), 500
            
            token = jwt_mgr.get_token_from_request()
            
            if not token:
                if optional:
                    g.current_user = None
                    return func(*args, **kwargs)
                return jsonify({
                    'error': 'Missing authorization token',
                    'error_code': 'TOKEN_MISSING'
                }), 401
            
            payload = jwt_mgr.verify_token(token)
            if not payload:
                if optional:
                    g.current_user = None
                    return func(*args, **kwargs)
                return jsonify({
                    'error': 'Invalid or expired token',
                    'error_code': 'TOKEN_INVALID'
                }), 401
            
            # 將用戶信息存儲在 Flask 的 g 對象中
            g.current_user = payload
            g.jwt_token = token
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def admin_required():
    """管理員權限裝飾器（增強版）"""
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if not g.current_user:
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            # 檢查是否為管理員
            if not g.current_user.get('is_manager', False):
                return jsonify({
                    'error': 'Admin privileges required',
                    'error_code': 'INSUFFICIENT_PRIVILEGES'
                }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def permission_required(required_permissions: List[str]):
    """權限檢查裝飾器（增強版）"""
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if not g.current_user:
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            user_permissions = g.current_user.get('permissions', [])
            
            # 檢查是否具有所需權限
            for permission in required_permissions:
                if permission not in user_permissions:
                    return jsonify({
                        'error': f'Permission "{permission}" required',
                        'error_code': 'INSUFFICIENT_PERMISSIONS'
                    }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user() -> Optional[Dict[str, Any]]:
    """獲取當前用戶信息"""
    return getattr(g, 'current_user', None)

def get_current_token() -> Optional[str]:
    """獲取當前 JWT 令牌"""
    return getattr(g, 'jwt_token', None)