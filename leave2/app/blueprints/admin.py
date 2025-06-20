#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from datetime import datetime

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

from app.utils.smtp_utils import EmailManager, EmailTemplate
# 或者直接導入配置
from app.config import BaseConfig
EMAIL_CONFIG = BaseConfig.EMAIL_CONFIG

# 為認證模組創建專用 logger

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/email/test', methods=['GET', 'POST'])
# @jwt_required()
# @permission_required(['admin:write'])
# @handle_api_error
def test_email():
    """測試郵件發送功能"""
    
    if request.method == 'GET':
        # 返回測試頁面或配置信息
        return jsonify({
            'success': True,
            'data': {
                'available_test_types': [
                    'simple_text',
                    'html_content', 
                    'template_email',
                    'attachment_test'
                ],
                'default_templates': [
                    'test_email',
                    'system_test'
                ]
            }
        })
    
    elif request.method == 'POST':
        # 執行郵件發送測試
        data = request.get_json() or {}
        
        # 驗證必要參數
        test_email_addr = data.get('test_email')
        test_type = data.get('test_type', 'simple_text')
        
        if not test_email_addr:
            return jsonify({
                'success': False,
                'message': '請提供測試郵件地址'
            }), 400
        
        # # 獲取當前用戶信息
        # current_user_id = get_jwt_identity()
        # user = User.query.get(current_user_id)
        
        try:
            # email_manager = EmailManager()
            email_config = current_app.config.get('EMAIL_CONFIG') or BaseConfig.EMAIL_CONFIG
            email_manager = EmailManager(config=email_config)
            # 確認郵件地址格式            
            # 根據測試類型發送不同的測試郵件
            if test_type == 'simple_text':
                success = email_manager.send_email(
                    to_emails=test_email_addr,
                    subject='郵件系統測試 - 純文本',
                    body=f'這是一封測試郵件。\n\n測試時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n測試用戶:  系統管理員'
                )
                
            elif test_type == 'html_content':
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #2c5aa0;">📧 郵件系統測試</h2>
                    <p>這是一封HTML格式的測試郵件。</p>
                    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>測試信息:</h3>
                        <ul>
                            <li><strong>測試時間:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
                            <li><strong>測試用戶:</strong> 系統管理員 </li>
                            <li><strong>郵件類型:</strong> HTML內容測試</li>
                        </ul>
                    </div>
                    <p style="color: #666;">如果您收到這封郵件，說明郵件系統運行正常。</p>
                </body>
                </html>
                """
                
                success = email_manager.send_email(
                    to_emails=test_email_addr,
                    subject='郵件系統測試 - HTML格式',
                    body='這是一封HTML格式的測試郵件（純文本版本）',
                    html_body=html_content
                )
                
            elif test_type == 'template_email':
                template_data = {
                    'test_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'tester_name': "系統管理員",
                    # 'system_name': current_app.config.get('APP_NAME', '系統'),
                    'system_name': current_app.config.get('APP_NAME') or BaseConfig.EMAIL_CONFIG.get('default_sender', {}).get('name', '系統'),
                    'test_message': data.get('custom_message', '這是一封模板測試郵件')
                }
                
                success = email_manager.send_template_email(
                    to_emails=test_email_addr,
                    template_name='test_email',
                    template_data=template_data,
                    subject='郵件系統測試 - 模板郵件'
                )
                
            elif test_type == 'attachment_test':
                # 創建一個簡單的測試附件
                test_content = f"""郵件系統測試報告
                
測試時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
測試用戶: 系統管理員
測試類型: 附件功能測試

此文件為自動生成的測試附件。
"""
                
                attachment = {
                    'filename': 'test_report.txt',
                    'content': test_content.encode('utf-8')
                }
                
                success = email_manager.send_email(
                    to_emails=test_email_addr,
                    subject='郵件系統測試 - 附件功能',
                    body='這是一封帶有附件的測試郵件，請查看附件內容。',
                    attachments=[attachment]
                )
            
            else:
                return jsonify({
                    'success': False,
                    'message': f'不支持的測試類型: {test_type}'
                }), 400
            
            # # 記錄測試日誌
            # log_entry = EmailLog(
            #     sender_id=current_user_id,
            #     recipients=test_email_addr,
            #     subject=f'郵件系統測試 - {test_type}',
            #     email_type='test',
            #     status='sent' if success else 'failed',
            #     created_at=datetime.now()
            # )
            # db.session.add(log_entry)
            # db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '測試郵件發送成功' if success else '測試郵件發送失敗',
                'data': {
                    'test_type': test_type,
                    'recipient': test_email_addr,
                    'sent_at': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"郵件測試失敗: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'郵件測試失敗: {str(e)}'
            }), 500


# @admin_bp.route('/email/config', methods=['GET'])
# @jwt_required()
# @permission_required(['admin:read'])
# @handle_api_error
# def get_email_config():
#     """獲取郵件配置信息（脫敏）"""
    
#     try:
#         # 獲取配置信息（脫敏處理）
#         config_info = {
#             'smtp_server': current_app.config.get('SMTP_SERVER', '未配置'),
#             'smtp_port': current_app.config.get('SMTP_PORT', '未配置'),
#             'smtp_use_tls': current_app.config.get('SMTP_USE_TLS', False),
#             'smtp_use_ssl': current_app.config.get('SMTP_USE_SSL', False),
#             'sender_email': current_app.config.get('SENDER_EMAIL', '未配置'),
#             'sender_name': current_app.config.get('SENDER_NAME', '未配置'),
#             'template_path': current_app.config.get('EMAIL_TEMPLATE_PATH', 'templates/email'),
#             # 敏感信息脫敏
#             'smtp_username': _mask_sensitive_data(current_app.config.get('SMTP_USERNAME', '')) if current_app.config.get('SMTP_USERNAME') else '未配置認證',
#             'smtp_password_configured': bool(current_app.config.get('SMTP_PASSWORD')),
#             'authentication_required': bool(current_app.config.get('SMTP_USERNAME') and current_app.config.get('SMTP_PASSWORD'))
#         }
        
#         # 檢查配置完整性
#         required_configs = ['SMTP_SERVER', 'SENDER_EMAIL']  # 移除用戶名密碼的必需性
#         optional_configs = ['SMTP_USERNAME', 'SMTP_PASSWORD']  # 認證配置為可選
#         missing_configs = [config for config in required_configs 
#                           if not current_app.config.get(config)]
        
#         # 檢查認證配置的一致性
#         has_username = bool(current_app.config.get('SMTP_USERNAME'))
#         has_password = bool(current_app.config.get('SMTP_PASSWORD'))
#         auth_inconsistent = has_username != has_password  # 用戶名和密碼應該同時存在或不存在
        
#         config_status = {
#             'is_configured': len(missing_configs) == 0 and not auth_inconsistent,
#             'missing_configs': missing_configs,
#             'auth_inconsistent': auth_inconsistent,
#             'auth_configured': has_username and has_password,
#             'config_complete_percentage': int((len(required_configs) - len(missing_configs)) / len(required_configs) * 100),
#             'warnings': []
#         }
        
#         # 添加警告信息
#         if auth_inconsistent:
#             config_status['warnings'].append('SMTP認證配置不一致：用戶名和密碼必須同時配置或同時留空')
        
#         if not config_status['auth_configured'] and current_app.config.get('SMTP_PORT', 25) != 25:
#             config_status['warnings'].append('未配置SMTP認證但使用非標準25端口，可能需要認證')
        
#         if current_app.config.get('SMTP_USE_TLS') and current_app.config.get('SMTP_USE_SSL'):
#             config_status['warnings'].append('同時啟用TLS和SSL可能導致連接問題')
        
#         return jsonify({
#             'success': True,
#             'data': {
#                 'config': config_info,
#                 'status': config_status,
#                 'last_updated': datetime.now().isoformat()
#             }
#         })
        
#     except Exception as e:
#         logger.error(f"獲取郵件配置失敗: {str(e)}")
#         raise


@admin_bp.route('/email/templates', methods=['GET'])
# @jwt_required()
# @permission_required(['admin:read'])
# @handle_api_error
def list_email_templates():
    """列出可用的郵件模板"""
    
    try:
        template_path = current_app.config.get('EMAIL_TEMPLATE_PATH', 'templates/email')
        template_manager = EmailTemplate(template_path)
        
        # 獲取可用模板列表
        available_templates = template_manager.get_available_templates()
        
        # 獲取模板詳細信息
        template_details = []
        for template_name in available_templates:
            template_info = {
                'name': template_name,
                'files': [],
                'last_modified': None,
                'description': None
            }
            
            # 檢查模板文件
            template_files = [
                f"{template_name}.html",
                f"{template_name}.txt", 
                f"{template_name}.json"
            ]
            
            for file_name in template_files:
                file_path = template_manager.template_path / file_name
                if file_path.exists():
                    template_info['files'].append({
                        'name': file_name,
                        'type': file_path.suffix[1:],  # 去掉點
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                    
                    # 更新最後修改時間
                    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if not template_info['last_modified'] or modified_time > datetime.fromisoformat(template_info['last_modified']):
                        template_info['last_modified'] = modified_time.isoformat()
            
            # 嘗試從JSON配置文件中讀取描述
            json_file = template_manager.template_path / f"{template_name}.json"
            if json_file.exists():
                try:
                    import json
                    with open(json_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        template_info['description'] = config.get('description', '無描述')
                except:
                    pass
            
            template_details.append(template_info)
        
        # 按名稱排序
        template_details.sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'data': {
                'templates': template_details,
                'total_count': len(template_details),
                'template_path': str(template_manager.template_path),
                'last_scan': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"獲取郵件模板列表失敗: {str(e)}")
        raise


# @admin_bp.route('/email/send', methods=['POST'])
# @jwt_required()
# @permission_required(['admin:write'])
# @handle_api_error
# def send_admin_email():
#     """管理員發送郵件"""
    
#     data = request.get_json() or {}
    
#     # 驗證必要參數
#     required_fields = ['recipients', 'subject']
#     missing_fields = [field for field in required_fields if not data.get(field)]
    
#     if missing_fields:
#         return jsonify({
#             'success': False,
#             'message': f'缺少必要參數: {", ".join(missing_fields)}'
#         }), 400
    
#     # 驗證郵件內容
#     if not data.get('body') and not data.get('html_body') and not data.get('template_name'):
#         return jsonify({
#             'success': False,
#             'message': '必須提供郵件內容（body、html_body或template_name）'
#         }), 400
    
#     try:
#         email_manager = EmailManager()
#         current_user_id = get_jwt_identity()
        
#         recipients = data['recipients']
#         subject = data['subject']
#         body = data.get('body')
#         html_body = data.get('html_body')
#         cc = data.get('cc')
#         bcc = data.get('bcc')
#         attachments = data.get('attachments')
#         template_name = data.get('template_name')
#         template_data = data.get('template_data', {})
        
#         # 驗證收件人格式
#         if isinstance(recipients, str):
#             recipients = [recipients]
        
#         if not email_manager.validate_email_addresses(recipients):
#             return jsonify({
#                 'success': False,
#                 'message': '收件人郵件地址格式錯誤'
#             }), 400
        
#         # 發送郵件
#         success = False
        
#         if template_name:
#             # 使用模板發送
#             success = email_manager.send_template_email(
#                 to_emails=recipients,
#                 template_name=template_name,
#                 template_data=template_data,
#                 subject=subject
#             )
#         else:
#             # 直接發送
#             success = email_manager.send_email(
#                 to_emails=recipients,
#                 subject=subject,
#                 body=body,
#                 html_body=html_body,
#                 cc=cc,
#                 bcc=bcc,
#                 attachments=attachments
#             )
        
#         # 記錄發送日誌
#         log_entry = EmailLog(
#             sender_id=current_user_id,
#             recipients=', '.join(recipients) if isinstance(recipients, list) else recipients,
#             subject=subject,
#             email_type='admin_sent',
#             status='sent' if success else 'failed',
#             template_used=template_name,
#             created_at=datetime.now()
#         )
#         db.session.add(log_entry)
#         db.session.commit()
        
#         return jsonify({
#             'success': True,
#             'message': '郵件發送成功',
#             'data': {
#                 'recipients_count': len(recipients) if isinstance(recipients, list) else 1,
#                 'sent_at': datetime.now().isoformat(),
#                 'email_id': log_entry.id
#             }
#         })
        
#     except Exception as e:
#         logger.error(f"管理員郵件發送失敗: {str(e)}")
#         raise


@admin_bp.route('/email/connection/test', methods=['POST'])
# @jwt_required()
# @permission_required(['admin:write'])
# @handle_api_error
def test_email_connection():
    """測試郵件服務器連接"""
    
    try:
        email_manager = EmailManager()
        
        # 測試連接
        connection_success = email_manager.test_connection()
        
        # 獲取連接詳細信息
        connection_info = {
            'smtp_server': email_manager.smtp_server,
            'smtp_port': email_manager.smtp_port,
            'use_tls': email_manager.smtp_use_tls,
            'use_ssl': email_manager.smtp_use_ssl,
            'username': '',
            'authentication_enabled': False
        }
        
        # # 記錄測試結果
        # current_user_id = get_jwt_identity()
        # log_entry = EmailLog(
        #     sender_id=current_user_id,
        #     recipients='system_test',
        #     subject='SMTP連接測試',
        #     email_type='connection_test',
        #     status='success' if connection_success else 'failed',
        #     created_at=datetime.now()
        # )
        # db.session.add(log_entry)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'connection_status': 'connected' if connection_success else 'failed',
                'connection_info': connection_info,
                'test_time': datetime.now().isoformat(),
                'message': 'SMTP服务器连接成功' if connection_success else 'SMTP服务器连接失败'
            }
        })
        
    except Exception as e:
        logger.error(f"SMTP連接測試失敗: {str(e)}")
        
        return jsonify({
            'success': False,
            'message': f'連接測試失敗: {str(e)}',
            'data': {
                'connection_status': 'error',
                'test_time': datetime.now().isoformat()
            }
        })


# def _mask_sensitive_data(data):
#     """脫敏處理敏感數據"""
#     if not data or len(data) <= 4:
#         return '****'
    
#     return data[:2] + '*' * (len(data) - 4) + data[-2:]


# # 郵件日誌查詢路由（額外功能）
# @admin_bp.route('/email/logs', methods=['GET'])
# @jwt_required()
# @permission_required(['admin:read'])
# @handle_api_error
# def get_email_logs():
#     """獲取郵件發送日誌"""
    
#     page = request.args.get('page', 1, type=int)
#     per_page = min(request.args.get('per_page', 20, type=int), 100)
#     email_type = request.args.get('type')
#     status = request.args.get('status')
    
#     try:
#         query = EmailLog.query
        
#         # 篩選條件
#         if email_type:
#             query = query.filter(EmailLog.email_type == email_type)
#         if status:
#             query = query.filter(EmailLog.status == status)
        
#         # 分頁查詢
#         pagination = query.order_by(EmailLog.created_at.desc()).paginate(
#             page=page, per_page=per_page, error_out=False
#         )
        
#         logs = []
#         for log in pagination.items:
#             logs.append({
#                 'id': log.id,
#                 'sender': log.sender.username if log.sender else '系統',
#                 'recipients': log.recipients,
#                 'subject': log.subject,
#                 'email_type': log.email_type,
#                 'status': log.status,
#                 'template_used': log.template_used,
#                 'created_at': log.created_at.isoformat()
#             })
        
#         return jsonify({
#             'success': True,
#             'data': {
#                 'logs': logs,
#                 'pagination': {
#                     'page': page,
#                     'per_page': per_page,
#                     'total': pagination.total,
#                     'pages': pagination.pages,
#                     'has_next': pagination.has_next,
#                     'has_prev': pagination.has_prev
#                 }
#             }
#         })
        
#     except Exception as e:
#         logger.error(f"獲取郵件日誌失敗: {str(e)}")
#         raise


# # 郵件統計路由（額外功能）
# @admin_bp.route('/email/stats', methods=['GET'])
# @jwt_required()
# @permission_required(['admin:read'])
# @handle_api_error
# def get_email_stats():
    # """獲取郵件發送統計"""
    
    # try:
    #     from sqlalchemy import func
    #     from datetime import timedelta
        
    #     # 獲取統計時間範圍
    #     days = request.args.get('days', 7, type=int)
    #     start_date = datetime.now() - timedelta(days=days)
        
    #     # 總體統計
    #     total_sent = EmailLog.query.filter(
    #         EmailLog.status == 'sent',
    #         EmailLog.created_at >= start_date
    #     ).count()
        
    #     total_failed = EmailLog.query.filter(
    #         EmailLog.status == 'failed',
    #         EmailLog.created_at >= start_date
    #     ).count()
        
    #     # 按類型統計
    #     type_stats = db.session.query(
    #         EmailLog.email_type,
    #         func.count(EmailLog.id).label('count')
    #     ).filter(
    #         EmailLog.created_at >= start_date
    #     ).group_by(EmailLog.email_type).all()
        
    #     # 按日期統計
    #     daily_stats = db.session.query(
    #         func.date(EmailLog.created_at).label('date'),
    #         func.count(EmailLog.id).label('count')
    #     ).filter(
    #         EmailLog.created_at >= start_date
    #     ).group_by(func.date(EmailLog.created_at)).all()
        
    #     return jsonify({
    #         'success': True,
    #         'data': {
    #             'summary': {
    #                 'total_sent': total_sent,
    #                 'total_failed': total_failed,
    #                 'success_rate': round(total_sent / (total_sent + total_failed) * 100, 2) if (total_sent + total_failed) > 0 else 0,
    #                 'period_days': days
    #             },
    #             'by_type': [{'type': row.email_type, 'count': row.count} for row in type_stats],
    #             'daily': [{'date': str(row.date), 'count': row.count} for row in daily_stats]
    #         }
    #     })
        
    # except Exception as e:
    #     logger.error(f"獲取郵件統計失敗: {str(e)}")
    #     raise