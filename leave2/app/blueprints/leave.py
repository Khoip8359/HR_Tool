#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
請假模組
"""
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
    permission_required,
    JWTUtils
)
from app.utils.jwt_auth_enhanced import get_current_user, get_current_token
from app.utils import get_db_manager

leave_bp = Blueprint('leave', __name__)

@leave_bp.route('/attendance', methods=['POST'])
@jwt_required()
# @permission_required(['employee:read'])
def get_employee_attendance_protected():
    """
    受保護的查詢員工出勤記錄（增強版）
    """
    try:
        current_user = get_current_user()
        
        # 改進的權限檢查邏輯
        user_permissions = current_user.get('permissions', [])
        is_manager = current_user.get('is_manager', False)
        user_id = current_user.get('user_id', '')
        user_department = current_user.get('department', '').lower()
        
        print(f"權限檢查調試信息:")
        print(f"  用戶ID: {user_id}")
        print(f"  是否主管: {is_manager}")
        print(f"  部門: {user_department}")
        print(f"  權限列表: {user_permissions}")
        

        # 驗證請求格式
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': '請求必須為 JSON 格式'
            }), 400
            
        # 獲取請求數據
        data = request.get_json()
        employee_id = data.get('employee_id')
        tran_year = data.get('tran_year')
        
        # 驗證必填參數
        if not employee_id:
            return jsonify({
                'success': False,
                'message': '員工編號為必填參數'
            }), 400
        
        # 權限檢查：檢查用戶是否有查詢權限
        user_permissions = current_user.get('permissions', [])
        is_manager = current_user.get('is_manager', False)
        user_id = current_user.get('user_id', '')
        user_department = current_user.get('department', '').lower()
        
        # 權限檢查邏輯：
        # 1. 主管可以查詢任何員工
        # 2. HR 部門可以查詢任何員工 
        # 3. 有 employee:read 權限可以查詢任何員工
        # 4. 普通用戶只能查詢自己
        
        has_employee_read_permission = 'employee:read' in user_permissions
        is_hr_department = user_department == 'hr'
        is_self_query = employee_id == user_id
        
        # if not (is_manager or is_hr_department or has_employee_read_permission or is_self_query):
        #     return jsonify({
        #         'success': False,
        #         'message': f'權限不足。主管: {is_manager}, HR部門: {is_hr_department}, 權限: {user_permissions}',
        #         'error_code': 'INSUFFICIENT_PRIVILEGES'
        #     }), 403
        
        # 構建查詢
        query = """
        SELECT A.EmployeeID,A.LeaveTypeID,B.LeaveTypeNameU,A.Quantity,A.LeaveDate,A.TranYear,
        (
                CONVERT(int,
                DATEDIFF(MONTH, C.DateJoined, GETDATE()) -
                ISNULL((
                    SELECT SUM(Quantity)
                    FROM D15T2020
                    WHERE LeaveDate IS NOT NULL
                        AND EmployeeID = :employee_id
                        AND LeaveTypeID IN ('PN', 'PT')
                        AND TransType != 'I03'
                ), 0))
            ) AS remain
        FROM D15T2020 A
        inner join D15T1020 B on A.LeaveTypeID = B.LeaveTypeID
        inner join D09T0201 C on A.EmployeeID = C.EmployeeID
        WHERE A.EmployeeID = :employee_id and A.LeaveDate is not null and A.TransType != 'I03'
        """
        params = {'employee_id': employee_id}
        
        # 如果指定了年份，添加到查詢條件
        if tran_year:
            query += " AND TranYear = :tran_year"
            params['tran_year'] = int(tran_year)
        
        # 執行查詢
        try:
            db_mgr = get_db_manager()
            mssql_pool = db_mgr.get_pool('mssql_hr')
            results = mssql_pool.execute_query(query, params)
            
            # 將結果轉換為字典列表
            attendance_records = []
            for row in results:
                record = dict(row._mapping)
                # 處理日期時間類型
                for key, value in record.items():
                    if hasattr(value, 'isoformat'):
                        record[key] = value.isoformat()
                attendance_records.append(record)
            
            # 記錄查詢操作
            logger.info(f"用戶 {current_user.get('username')} (會話: {current_user.get('session_id')}) 查詢員工 {employee_id} 的出勤記錄")
            
            return jsonify({
                'success': True,
                'employee_id': employee_id,
                'tran_year': tran_year,
                'records': attendance_records,
                'count': len(attendance_records),
                'accessed_by': {
                    'username': current_user.get('username'),
                    'session_id': current_user.get('session_id')
                },
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            logger.error(f"查詢出勤記錄失敗: {str(e)}")
            return jsonify({
                'success': False,
                'message': '查詢出勤記錄失敗',
                'error': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': '處理請求時發生錯誤',
            'error': str(e)
        }), 500
        
        
@leave_bp.route('/type', methods=['POST'])
@jwt_required()
def get_leave_type() :
    query = "select LeaveTypeID,LeaveTypeNameU from D15T1020 where IsLemonWeb = 1"
    
    try:
        db_mgr = get_db_manager()
        mssql_pool = db_mgr.get_pool('mssql_hr')
        results = mssql_pool.execute_query(query) 
        
        attendance_records = []
        for row in results:
            record = dict(row._mapping)
            # 處理日期時間類型
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
            attendance_records.append(record)
        
        return jsonify({
            'success': True,
            'message': 'Lấy loại nghỉ phép thành công',
            'data': attendance_records
        }), 200
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': '處理請求時發生錯誤',
            'error': str(e)
        }), 500