import smtplib
import os
import re
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import List, Union, Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from flask import current_app
import ssl


class EmailManager:
    """郵件管理器"""
    
    def __init__(self, provider='smtp', config=None):
        """初始化郵件管理器"""
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        
       # 優先從EMAIL_CONFIG讀取，fallback到舊格式
        email_config = current_app.config.get('EMAIL_CONFIG', {})
        smtp_config = email_config.get('providers', {}).get('smtp', {})
        sender_config = email_config.get('default_sender', {})

        # 讀取SMTP配置（新格式優先，舊格式備用）
        self.smtp_server = smtp_config.get('host') or current_app.config.get('SMTP_SERVER') or os.getenv('SMTP_SERVER')
        self.smtp_port = smtp_config.get('port') or current_app.config.get('SMTP_PORT') or int(os.getenv('SMTP_PORT', 25))
        self.smtp_username = smtp_config.get('username') or current_app.config.get('SMTP_USERNAME') or os.getenv('SMTP_USERNAME')
        self.smtp_password = smtp_config.get('password') or current_app.config.get('SMTP_PASSWORD') or os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = smtp_config.get('use_tls', current_app.config.get('SMTP_USE_TLS', False))
        self.smtp_use_ssl = smtp_config.get('use_ssl', current_app.config.get('SMTP_USE_SSL', False))
        self.sender_name = sender_config.get('name') or current_app.config.get('SENDER_NAME') or os.getenv('SENDER_NAME', '')
        self.sender_email = sender_config.get('email') or current_app.config.get('SENDER_EMAIL') or os.getenv('SENDER_EMAIL')
               
        # 驗證必要配置（用戶名和密碼在某些SMTP服務器上可能不是必需的）
        if not all([self.smtp_server, self.sender_email]):
            raise ValueError("缺少必要的SMTP配置參數")
    
    def send_email(self, to_emails, subject, body, html_body=None, 
                   attachments=None, cc=None, bcc=None):
        """發送郵件主函數"""
        try:
            # 驗證郵件地址
            if not self.validate_email_addresses(to_emails):
                raise ValueError("收件人郵件地址格式錯誤")
            
            if cc and not self.validate_email_addresses(cc):
                raise ValueError("CC郵件地址格式錯誤")
                
            if bcc and not self.validate_email_addresses(bcc):
                raise ValueError("BCC郵件地址格式錯誤")
            
            # 創建郵件
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.sender_name, self.sender_email))
            msg['To'] = ', '.join(to_emails) if isinstance(to_emails, list) else to_emails
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
            
            # 添加郵件內容
            if body:
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 添加附件
            if attachments:
                self._add_attachments(msg, attachments)
            
            # 準備收件人列表
            recipients = []
            if isinstance(to_emails, list):
                recipients.extend(to_emails)
            else:
                recipients.append(to_emails)
            
            if cc:
                if isinstance(cc, list):
                    recipients.extend(cc)
                else:
                    recipients.append(cc)
            
            if bcc:
                if isinstance(bcc, list):
                    recipients.extend(bcc)
                else:
                    recipients.append(bcc)
            
            # 發送郵件
            self._send_smtp_email(msg, recipients)
            
            self.logger.info(f"郵件發送成功: {subject} -> {to_emails}")
            return True
            
        except Exception as e:
            self.logger.error(f"郵件發送失敗: {str(e)}")
            raise
    
    def send_template_email(self, to_emails, template_name, 
                           template_data, subject=None):
        """使用模板發送郵件"""
        try:
            # 獲取模板路徑
            # template_path = current_app.config.get('EMAIL_TEMPLATE_PATH', 'templates/email')
            email_config = current_app.config.get('EMAIL_CONFIG', {})
            template_path = email_config.get('templates', {}).get('base_template_path') or current_app.config.get('EMAIL_TEMPLATE_PATH', 'templates/email')
            template_manager = EmailTemplate(template_path)
            
            # 渲染模板
            rendered_content = template_manager.render_template(template_name, template_data)
            
            # 從渲染結果中提取主題和內容
            if isinstance(rendered_content, dict):
                email_subject = subject or rendered_content.get('subject', '系統通知')
                html_body = rendered_content.get('html')
                text_body = rendered_content.get('text')
            else:
                email_subject = subject or '系統通知'
                html_body = rendered_content
                text_body = None
            
            return self.send_email(
                to_emails=to_emails,
                subject=email_subject,
                body=text_body,
                html_body=html_body
            )
            
        except Exception as e:
            self.logger.error(f"模板郵件發送失敗: {str(e)}")
            raise
    
    def validate_email_addresses(self, emails):
        """驗證郵件地址格式"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if isinstance(emails, str):
            emails = [emails]
        
        if not isinstance(emails, (list, tuple)):
            return False
        
        for email in emails:
            if not isinstance(email, str) or not email_pattern.match(email.strip()):
                return False
        
        return True
    
    def test_connection(self):
        """測試郵件服務器連接"""
        try:
            # 根據配置選擇連接方式
            if self.smtp_use_ssl:
                # 使用SSL連接（通常是465端口）
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.ehlo()
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
            else:
                # 使用普通SMTP連接
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.ehlo()
                    
                    # 如果配置了TLS，則啟用STARTTLS
                    if self.smtp_use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()
                    
                    # 如果有用戶名密碼，則進行認證
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                
            self.logger.info("SMTP連接測試成功")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP連接測試失敗: {str(e)}")
            return False
    
    def _add_attachments(self, msg, attachments):
        """添加附件到郵件"""
        if isinstance(attachments, str):
            attachments = [attachments]
        
        for attachment in attachments:
            if isinstance(attachment, str):
                # 文件路徑
                if os.path.isfile(attachment):
                    with open(attachment, "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
            
            elif isinstance(attachment, dict):
                # 附件字典格式: {'filename': 'name.txt', 'content': b'content'}
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
    
    def _send_smtp_email(self, msg, recipients):
        """發送SMTP郵件"""
        if self.smtp_use_ssl:
            # 使用SSL連接（通常是465端口）
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.ehlo()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, to_addrs=recipients)
        else:
            # 使用普通SMTP連接
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                
                # 如果配置了TLS，則啟用STARTTLS
                if self.smtp_use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                
                # 如果有用戶名密碼，則進行認證
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg, to_addrs=recipients)


class EmailTemplate:
    """郵件模板管理器"""
    
    def __init__(self, template_path):
        """初始化模板管理器"""
        self.template_path = Path(template_path)
        
        if not self.template_path.exists():
            self.template_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2環境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_path)),
            autoescape=True
        )
    
    def render_template(self, template_name, data):
        """渲染郵件模板"""
        try:
            # 支持不同格式的模板文件
            template_files = {
                'html': f"{template_name}.html",
                'txt': f"{template_name}.txt",
                'json': f"{template_name}.json"
            }
            
            result = {}
            
            # 嘗試加載HTML模板
            if (self.template_path / template_files['html']).exists():
                html_template = self.env.get_template(template_files['html'])
                result['html'] = html_template.render(**data)
            
            # 嘗試加載文本模板
            if (self.template_path / template_files['txt']).exists():
                txt_template = self.env.get_template(template_files['txt'])
                result['text'] = txt_template.render(**data)
            
            # 嘗試加載JSON配置模板
            if (self.template_path / template_files['json']).exists():
                json_template = self.env.get_template(template_files['json'])
                import json
                config = json.loads(json_template.render(**data))
                result.update(config)
            
            # 如果只有HTML模板，直接返回HTML內容
            if len(result) == 1 and 'html' in result:
                return result['html']
            
            return result
            
        except Exception as e:
            raise ValueError(f"模板渲染失敗: {str(e)}")
    
    def get_available_templates(self):
        """獲取可用模板列表"""
        templates = set()
        
        for file_path in self.template_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.html', '.txt', '.json']:
                template_name = file_path.stem
                templates.add(template_name)
        
        return sorted(list(templates))


# 便捷函數
def send_notification_email(user_email, notification_type, data):
    """發送通知郵件"""
    try:
        email_manager = EmailManager()
        
        # 通知類型對應的模板和主題
        notification_configs = {
            'welcome': {
                'template': 'welcome',
                'subject': '歡迎加入我們的平台！'
            },
            'password_reset': {
                'template': 'password_reset',
                'subject': '密碼重置請求'
            },
            'account_verification': {
                'template': 'account_verification',
                'subject': '請驗證您的帳戶'
            },
            'general': {
                'template': 'notification',
                'subject': '系統通知'
            }
        }
        
        config = notification_configs.get(notification_type, notification_configs['general'])
        
        return email_manager.send_template_email(
            to_emails=user_email,
            template_name=config['template'],
            template_data=data,
            subject=config['subject']
        )
        
    except Exception as e:
        logging.error(f"通知郵件發送失敗: {str(e)}")
        raise


def send_leave_approval_email(approver_email, leave_request_data):
    """發送請假審核郵件"""
    try:
        email_manager = EmailManager()
        
        # 準備模板數據
        template_data = {
            'approver_name': leave_request_data.get('approver_name', '審核者'),
            'employee_name': leave_request_data.get('employee_name'),
            'leave_type': leave_request_data.get('leave_type'),
            'start_date': leave_request_data.get('start_date'),
            'end_date': leave_request_data.get('end_date'),
            'days_count': leave_request_data.get('days_count'),
            'reason': leave_request_data.get('reason'),
            'approval_url': leave_request_data.get('approval_url'),
            'request_id': leave_request_data.get('request_id')
        }
        
        return email_manager.send_template_email(
            to_emails=approver_email,
            template_name='leave_approval',
            template_data=template_data,
            subject=f"請假申請待審核 - {leave_request_data.get('employee_name')}"
        )
        
    except Exception as e:
        logging.error(f"請假審核郵件發送失敗: {str(e)}")
        raise


def send_system_alert_email(admin_emails, alert_data):
    """發送系統警報郵件"""
    try:
        email_manager = EmailManager()
        
        # 警報級別對應的主題前綴
        alert_prefixes = {
            'critical': '🚨 [緊急]',
            'warning': '⚠️ [警告]',
            'info': 'ℹ️ [資訊]'
        }
        
        alert_level = alert_data.get('level', 'info')
        prefix = alert_prefixes.get(alert_level, '[系統警報]')
        
        # 準備模板數據
        template_data = {
            'alert_title': alert_data.get('title', '系統警報'),
            'alert_level': alert_level,
            'alert_message': alert_data.get('message'),
            'alert_time': alert_data.get('time'),
            'system_name': alert_data.get('system_name', '系統'),
            'details': alert_data.get('details', {}),
            'action_required': alert_data.get('action_required', False)
        }
        
        return email_manager.send_template_email(
            to_emails=admin_emails,
            template_name='system_alert',
            template_data=template_data,
            subject=f"{prefix} {alert_data.get('title', '系統警報')}"
        )
        
    except Exception as e:
        logging.error(f"系統警報郵件發送失敗: {str(e)}")
        raise


# Flask配置示例
"""
# 在Flask應用配置中添加以下設置：

# SMTP配置 - 使用 port 25 無加密連接
SMTP_SERVER = 'your-smtp-server.com'
SMTP_PORT = 25
SMTP_USERNAME = None  # 如果不需要認證可設為None
SMTP_PASSWORD = None  # 如果不需要認證可設為None
SMTP_USE_TLS = False  # 關閉TLS
SMTP_USE_SSL = False  # 關閉SSL
SENDER_NAME = '您的應用名稱'
SENDER_EMAIL = 'noreply@your-domain.com'

# 模板路徑
EMAIL_TEMPLATE_PATH = 'templates/email'

# 其他常見配置示例：

# 1. 使用 Gmail SMTP (需要TLS/SSL)
# SMTP_SERVER = 'smtp.gmail.com'
# SMTP_PORT = 587
# SMTP_USE_TLS = True

# 2. 使用 Gmail SMTP SSL
# SMTP_SERVER = 'smtp.gmail.com' 
# SMTP_PORT = 465
# SMTP_USE_SSL = True

# 3. 本地 SMTP 服務器 (通常port 25，無加密)
# SMTP_SERVER = 'localhost'
# SMTP_PORT = 25
# SMTP_USE_TLS = False
# SMTP_USE_SSL = False
# SMTP_USERNAME = None
# SMTP_PASSWORD = None

# 4. 企業內部郵件服務器
# SMTP_SERVER = 'mail.company.com'
# SMTP_PORT = 25
# SMTP_USE_TLS = False
# SMTP_USE_SSL = False

# 使用示例：
from your_email_utility import EmailManager, send_notification_email

# 初始化郵件管理器
email_manager = EmailManager()

# 發送簡單郵件
email_manager.send_email(
    to_emails='user@example.com',
    subject='測試郵件',
    body='這是一封測試郵件',
    html_body='<h1>這是一封測試郵件</h1>'
)

# 發送通知郵件
send_notification_email(
    user_email='user@example.com',
    notification_type='welcome',
    data={'username': 'John', 'login_url': 'https://example.com/login'}
)
"""