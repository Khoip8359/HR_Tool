#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from flask import Blueprint, request, jsonify, current_app, g

# 從擴展中導入需要的組件
from app.extensions import (
    logger, 
    ADAuthenticator,
    enhanced_jwt_manager,
    jwt_required,
    admin_required,
    get_current_user,
    JWTUtils
)
from app.utils.jwt_auth_enhanced import get_current_user, get_current_token
# 為認證模組創建專用 logger

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用戶登入並獲取 JWT Token（增強版）
    
    Request Body:
    {
        "username": "u6001",
        "password": "password123",
        "server": "192.168.1.245",         // 可選
        "domain": "FULINVN_TN",           // 可選
        "remember_me": false              // 可選，是否延長 Token 有效期
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON',
                'error_code': 'INVALID_REQUEST_FORMAT'
            }), 400
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required',
                'error_code': 'MISSING_CREDENTIALS'
            }), 400
            
        DEFAULT_AD_SERVER = current_app.config['AD_CONFIG']['DEFAULT_AD_SERVER']
        DEFAULT_DOMAIN = current_app.config['AD_CONFIG']['DEFAULT_DOMAIN']
        DEFAULT_ORGANIZATION = current_app.config['AD_CONFIG']['DEFAULT_ORGANIZATION']
        
        server_ip = data.get('server', DEFAULT_AD_SERVER)
        domain = data.get('domain', DEFAULT_DOMAIN)
        remember_me = data.get('remember_me', False)
        
        # AD 認證
        authenticator = ADAuthenticator(server_ip, domain, DEFAULT_ORGANIZATION)
        auth_result = authenticator.authenticate_and_get_info(
            username, password, get_manager_info=True, get_subordinates=True
        )
        
        if not auth_result['success']:
            # 記錄失敗的登入嘗試
            enhanced_jwt_manager.record_failed_login(username, 'auth_failed')
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed',
                'error_code': 'AUTH_FAILED'
            }), 401
        
        # 提取用戶信息
        user_info = JWTUtils.extract_user_info_from_ad_result(auth_result)
        
        # 如果記住我，延長 Token 有效期
        if remember_me:
            import datetime
            current_app.config['JWT_CONFIGS']['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=7)  # 7天
        
        # 生成 JWT Token（含資料庫記錄）
        auth_info = {
            'server': server_ip,
            'domain': domain
        }
        tokens = enhanced_jwt_manager.generate_tokens(user_info, auth_info)
        
        # 記錄登入
        logger.info(f"用戶 {username} 登入成功，會話 ID: {tokens.get('session_id')}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user_info,
                'tokens': tokens,
                'login_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'session_management': {
                    'database_tracking': True,
                    'session_id': tokens.get('session_id')
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"登入錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'LOGIN_ERROR'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    刷新 JWT Token（增強版）
    
    Request Body:
    {
        "refresh_token": "..."
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON',
                'error_code': 'INVALID_REQUEST_FORMAT'
            }), 400
        
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'success': False,
                'message': 'Refresh token is required',
                'error_code': 'MISSING_REFRESH_TOKEN'
            }), 400
        
        # 刷新 Token（含資料庫處理）
        new_tokens = enhanced_jwt_manager.refresh_token(refresh_token)
        
        if not new_tokens:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired refresh token',
                'error_code': 'INVALID_REFRESH_TOKEN'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'data': {
                'tokens': new_tokens,
                'refresh_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token 刷新錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'REFRESH_ERROR'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用戶登出（增強版，含資料庫會話管理）
    """
    try:
        current_token = get_current_token()
        current_user = get_current_user()
        
        if current_token:
            # 使用增強的登出功能
            success = enhanced_jwt_manager.logout_user(current_token, 'manual')
            
            if success:
                logger.info(f"用戶 {current_user.get('username', 'unknown')} 登出成功")
                return jsonify({
                    'success': True,
                    'message': 'Logout successful',
                    'logout_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Logout failed',
                    'error_code': 'LOGOUT_FAILED'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': 'No active session found',
                'error_code': 'NO_ACTIVE_SESSION'
            }), 400
        
    except Exception as e:
        logger.error(f"登出錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 'LOGOUT_ERROR'
        }), 500
