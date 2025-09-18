"""
Email Integration System for Receipt Processing.

This module provides comprehensive email capabilities including SMTP client
configuration, template management, delivery tracking, and Gmail integration.
"""

import smtplib
import ssl
import json
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, parseaddr
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader, Template
import logging

from .models import ReceiptProcessingLog, ProcessingStatus, ReceiptData

logger = logging.getLogger(__name__)


class EmailAuthMethod(str, Enum):
    """Email authentication methods."""
    PASSWORD = "password"
    OAUTH2 = "oauth2"
    APP_PASSWORD = "app_password"


class EmailProvider(str, Enum):
    """Supported email providers."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    CUSTOM = "custom"


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    RETRY = "retry"


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class OAuth2Config:
    """OAuth2 configuration for email authentication."""
    client_id: str
    client_secret: str
    refresh_token: str
    access_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    scope: str = "https://mail.google.com/"


@dataclass
class SMTPConfig:
    """SMTP server configuration."""
    server: str
    port: int
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    debug_level: int = 0


@dataclass
class EmailConfig:
    """Email system configuration."""
    provider: EmailProvider
    smtp_config: SMTPConfig
    auth_method: EmailAuthMethod
    username: str
    password: Optional[str] = None
    oauth2_config: Optional[OAuth2Config] = None
    from_email: str = ""
    from_name: str = "Receipt Processor"
    reply_to: Optional[str] = None
    return_path: Optional[str] = None
    max_retries: int = 3
    retry_delay_seconds: int = 300  # 5 minutes
    batch_size: int = 50
    rate_limit_per_hour: int = 500


@dataclass
class EmailRecipient:
    """Email recipient information."""
    email: str
    name: Optional[str] = None
    type: str = "to"  # to, cc, bcc
    
    def __post_init__(self):
        """Validate email address format."""
        if not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email address: {self.email}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def format_address(self) -> str:
        """Format address for email headers."""
        if self.name:
            return formataddr((self.name, self.email))
        return self.email


@dataclass
class EmailAttachment:
    """Email attachment information."""
    file_path: Path
    filename: Optional[str] = None
    content_type: Optional[str] = None
    inline: bool = False
    
    def __post_init__(self):
        """Set default filename and content type."""
        if not self.filename:
            self.filename = self.file_path.name
        
        if not self.content_type:
            self.content_type = self._guess_content_type()
    
    def _guess_content_type(self) -> str:
        """Guess content type from file extension."""
        ext = self.file_path.suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.zip': 'application/zip'
        }
        return content_types.get(ext, 'application/octet-stream')


@dataclass
class EmailTemplate:
    """Email template definition."""
    name: str
    subject_template: str
    html_template: Optional[str] = None
    text_template: Optional[str] = None
    template_vars: Dict[str, Any] = field(default_factory=dict)
    attachments: List[EmailAttachment] = field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL


@dataclass
class EmailMessage:
    """Email message to be sent."""
    recipients: List[EmailRecipient]
    subject: str
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
    headers: Dict[str, str] = field(default_factory=dict)
    template_name: Optional[str] = None
    template_vars: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailDeliveryResult:
    """Email delivery result."""
    message_id: str
    status: EmailStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    bounce_reason: Optional[str] = None
    tracking_data: Dict[str, Any] = field(default_factory=dict)


class EmailProviderConfig:
    """Pre-configured settings for popular email providers."""
    
    PROVIDERS = {
        EmailProvider.GMAIL: {
            "smtp_config": SMTPConfig(
                server="smtp.gmail.com",
                port=587,
                use_tls=True
            ),
            "auth_methods": [EmailAuthMethod.OAUTH2, EmailAuthMethod.APP_PASSWORD],
            "rate_limit_per_hour": 500,
            "max_attachment_size_mb": 25
        },
        EmailProvider.OUTLOOK: {
            "smtp_config": SMTPConfig(
                server="smtp-mail.outlook.com",
                port=587,
                use_tls=True
            ),
            "auth_methods": [EmailAuthMethod.OAUTH2, EmailAuthMethod.PASSWORD],
            "rate_limit_per_hour": 300,
            "max_attachment_size_mb": 20
        },
        EmailProvider.YAHOO: {
            "smtp_config": SMTPConfig(
                server="smtp.mail.yahoo.com",
                port=587,
                use_tls=True
            ),
            "auth_methods": [EmailAuthMethod.APP_PASSWORD],
            "rate_limit_per_hour": 100,
            "max_attachment_size_mb": 15
        }
    }
    
    @classmethod
    def get_config(cls, provider: EmailProvider) -> Dict[str, Any]:
        """Get configuration for a provider."""
        return cls.PROVIDERS.get(provider, {})
    
    @classmethod
    def create_gmail_config(cls, username: str, auth_method: EmailAuthMethod,
                           password: Optional[str] = None,
                           oauth2_config: Optional[OAuth2Config] = None) -> EmailConfig:
        """Create Gmail configuration."""
        provider_config = cls.get_config(EmailProvider.GMAIL)
        
        return EmailConfig(
            provider=EmailProvider.GMAIL,
            smtp_config=provider_config["smtp_config"],
            auth_method=auth_method,
            username=username,
            password=password,
            oauth2_config=oauth2_config,
            from_email=username,
            rate_limit_per_hour=provider_config["rate_limit_per_hour"]
        )


class OAuth2Manager:
    """Manages OAuth2 authentication for email providers."""
    
    def __init__(self, config: OAuth2Config):
        self.config = config
    
    def get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""
        if self._is_token_expired():
            self._refresh_access_token()
        
        return self.config.access_token
    
    def _is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.config.access_token or not self.config.token_expiry:
            return True
        
        # Add 5 minute buffer
        return datetime.now() >= (self.config.token_expiry - timedelta(minutes=5))
    
    def _refresh_access_token(self):
        """Refresh the access token using refresh token."""
        try:
            import requests
            
            data = {
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret,
                'refresh_token': self.config.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.config.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.config.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                logger.info("OAuth2 access token refreshed successfully")
            else:
                raise Exception(f"Failed to refresh token: {response.text}")
                
        except Exception as e:
            logger.error(f"Error refreshing OAuth2 token: {e}")
            raise


class EmailTemplateManager:
    """Manages email templates with Jinja2."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Built-in templates
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default email templates."""
        default_templates = {
            "receipt_processed.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Receipt Processed</title>
</head>
<body>
    <h2>Receipt Successfully Processed</h2>
    <p>Hello,</p>
    <p>Your receipt has been successfully processed with the following details:</p>
    
    <table border="1" cellpadding="10" style="border-collapse: collapse;">
        <tr><td><strong>Vendor:</strong></td><td>{{ vendor_name }}</td></tr>
        <tr><td><strong>Date:</strong></td><td>{{ transaction_date }}</td></tr>
        <tr><td><strong>Amount:</strong></td><td>${{ total_amount }} {{ currency }}</td></tr>
        <tr><td><strong>Processed:</strong></td><td>{{ processed_at }}</td></tr>
        <tr><td><strong>Confidence:</strong></td><td>{{ confidence_score }}%</td></tr>
    </table>
    
    <p>The receipt has been filed and is ready for submission.</p>
    
    <p>Best regards,<br>Receipt Processor</p>
</body>
</html>
            """,
            
            "receipt_error.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Receipt Processing Error</title>
</head>
<body>
    <h2>Receipt Processing Error</h2>
    <p>Hello,</p>
    <p>There was an error processing your receipt:</p>
    
    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; margin: 10px 0;">
        <strong>Error:</strong> {{ error_message }}
    </div>
    
    <p><strong>File:</strong> {{ original_filename }}</p>
    <p><strong>Time:</strong> {{ error_time }}</p>
    
    <p>Please check the receipt image and try again, or contact support if the problem persists.</p>
    
    <p>Best regards,<br>Receipt Processor</p>
</body>
</html>
            """,
            
            "receipt_summary.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Receipt Processing Summary</title>
</head>
<body>
    <h2>Receipt Processing Summary</h2>
    <p>Hello,</p>
    <p>Here's your receipt processing summary for {{ period }}:</p>
    
    <table border="1" cellpadding="10" style="border-collapse: collapse;">
        <tr><td><strong>Total Receipts:</strong></td><td>{{ total_receipts }}</td></tr>
        <tr><td><strong>Successfully Processed:</strong></td><td>{{ processed_count }}</td></tr>
        <tr><td><strong>Errors:</strong></td><td>{{ error_count }}</td></tr>
        <tr><td><strong>Total Amount:</strong></td><td>${{ total_amount }}</td></tr>
        <tr><td><strong>Success Rate:</strong></td><td>{{ success_rate }}%</td></tr>
    </table>
    
    {% if recent_receipts %}
    <h3>Recent Receipts:</h3>
    <ul>
    {% for receipt in recent_receipts %}
        <li>{{ receipt.vendor_name }} - ${{ receipt.total_amount }} ({{ receipt.transaction_date }})</li>
    {% endfor %}
    </ul>
    {% endif %}
    
    <p>Best regards,<br>Receipt Processor</p>
</body>
</html>
            """
        }
        
        # Create default templates if they don't exist
        for filename, content in default_templates.items():
            template_file = self.template_dir / filename
            if not template_file.exists():
                template_file.write_text(content.strip())
    
    def load_template(self, template_name: str) -> Template:
        """Load a template by name."""
        try:
            return self.env.get_template(template_name)
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            raise
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables."""
        template = self.load_template(template_name)
        return template.render(**variables)
    
    def create_template(self, name: str, subject_template: str,
                       html_template: Optional[str] = None,
                       text_template: Optional[str] = None) -> EmailTemplate:
        """Create an email template."""
        return EmailTemplate(
            name=name,
            subject_template=subject_template,
            html_template=html_template,
            text_template=text_template
        )
    
    def get_template_vars_for_receipt(self, log_entry: ReceiptProcessingLog) -> Dict[str, Any]:
        """Get template variables for a receipt log entry."""
        variables = {
            "log_id": str(log_entry.id),
            "original_filename": log_entry.original_filename,
            "current_status": log_entry.current_status.value,
            "created_at": log_entry.created_at,
            "processed_at": log_entry.processed_at,
            "processing_time_seconds": log_entry.processing_time_seconds,
            "confidence_score": int(log_entry.confidence_score * 100) if log_entry.confidence_score else 0,
            "file_size": log_entry.file_size
        }
        
        # Add receipt data if available
        if log_entry.receipt_data:
            variables.update({
                "vendor_name": log_entry.receipt_data.vendor_name,
                "transaction_date": log_entry.receipt_data.transaction_date,
                "total_amount": log_entry.receipt_data.total_amount,
                "currency": log_entry.receipt_data.currency.value,
                "extraction_confidence": int(log_entry.receipt_data.extraction_confidence * 100) if log_entry.receipt_data.extraction_confidence else 0
            })
        
        return variables


class EmailValidator:
    """Validates email addresses and configurations."""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address format."""
        try:
            # Parse email address
            name, addr = parseaddr(email)
            if not addr:
                return False, "Email address is empty"
            
            # Check format with regex
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, addr):
                return False, "Invalid email format"
            
            # Check for common issues
            if '..' in addr:
                return False, "Email contains consecutive dots"
            
            if addr.startswith('.') or addr.endswith('.'):
                return False, "Email starts or ends with dot"
            
            return True, None
            
        except Exception as e:
            return False, f"Email validation error: {str(e)}"
    
    @staticmethod
    def validate_config(config: EmailConfig) -> List[str]:
        """Validate email configuration."""
        issues = []
        
        # Validate SMTP config
        if not config.smtp_config.server:
            issues.append("SMTP server is required")
        
        if not (1 <= config.smtp_config.port <= 65535):
            issues.append("SMTP port must be between 1 and 65535")
        
        # Validate authentication
        if config.auth_method == EmailAuthMethod.PASSWORD and not config.password:
            issues.append("Password is required for password authentication")
        
        if config.auth_method == EmailAuthMethod.OAUTH2 and not config.oauth2_config:
            issues.append("OAuth2 config is required for OAuth2 authentication")
        
        # Validate email addresses
        if config.from_email:
            is_valid, error = EmailValidator.validate_email(config.from_email)
            if not is_valid:
                issues.append(f"Invalid from_email: {error}")
        
        if config.reply_to:
            is_valid, error = EmailValidator.validate_email(config.reply_to)
            if not is_valid:
                issues.append(f"Invalid reply_to: {error}")
        
        return issues


class EmailTracker:
    """Tracks email delivery status and metrics."""
    
    def __init__(self, storage_file: Optional[Path] = None):
        self.storage_file = storage_file or Path("email_tracking.json")
        self.delivery_results: Dict[str, EmailDeliveryResult] = {}
        self.load_tracking_data()
    
    def load_tracking_data(self):
        """Load tracking data from storage."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                
                for message_id, result_data in data.items():
                    result = EmailDeliveryResult(
                        message_id=message_id,
                        status=EmailStatus(result_data['status']),
                        sent_at=datetime.fromisoformat(result_data['sent_at']) if result_data.get('sent_at') else None,
                        delivered_at=datetime.fromisoformat(result_data['delivered_at']) if result_data.get('delivered_at') else None,
                        error_message=result_data.get('error_message'),
                        retry_count=result_data.get('retry_count', 0),
                        bounce_reason=result_data.get('bounce_reason'),
                        tracking_data=result_data.get('tracking_data', {})
                    )
                    self.delivery_results[message_id] = result
                    
            except Exception as e:
                logger.error(f"Error loading email tracking data: {e}")
    
    def save_tracking_data(self):
        """Save tracking data to storage."""
        try:
            data = {}
            for message_id, result in self.delivery_results.items():
                data[message_id] = {
                    'status': result.status.value,
                    'sent_at': result.sent_at.isoformat() if result.sent_at else None,
                    'delivered_at': result.delivered_at.isoformat() if result.delivered_at else None,
                    'error_message': result.error_message,
                    'retry_count': result.retry_count,
                    'bounce_reason': result.bounce_reason,
                    'tracking_data': result.tracking_data
                }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving email tracking data: {e}")
    
    def track_email(self, message_id: str, status: EmailStatus,
                   error_message: Optional[str] = None) -> EmailDeliveryResult:
        """Track email delivery status."""
        if message_id not in self.delivery_results:
            self.delivery_results[message_id] = EmailDeliveryResult(
                message_id=message_id,
                status=status
            )
        
        result = self.delivery_results[message_id]
        result.status = status
        
        if status == EmailStatus.SENT:
            result.sent_at = datetime.now()
        elif status == EmailStatus.DELIVERED:
            result.delivered_at = datetime.now()
        elif status in [EmailStatus.FAILED, EmailStatus.BOUNCED]:
            result.error_message = error_message
            result.retry_count += 1
        
        self.save_tracking_data()
        return result
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics."""
        stats = {
            'total_emails': len(self.delivery_results),
            'sent': 0,
            'delivered': 0,
            'failed': 0,
            'bounced': 0,
            'pending': 0,
            'success_rate': 0.0,
            'bounce_rate': 0.0
        }
        
        for result in self.delivery_results.values():
            if result.status == EmailStatus.SENT:
                stats['sent'] += 1
            elif result.status == EmailStatus.DELIVERED:
                stats['delivered'] += 1
            elif result.status == EmailStatus.FAILED:
                stats['failed'] += 1
            elif result.status == EmailStatus.BOUNCED:
                stats['bounced'] += 1
            elif result.status == EmailStatus.PENDING:
                stats['pending'] += 1
        
        if stats['total_emails'] > 0:
            stats['success_rate'] = (stats['sent'] + stats['delivered']) / stats['total_emails'] * 100
            stats['bounce_rate'] = stats['bounced'] / stats['total_emails'] * 100
        
        return stats


class SMTPClient:
    """SMTP client with connection management and error handling."""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.oauth2_manager = None
        
        if config.auth_method == EmailAuthMethod.OAUTH2 and config.oauth2_config:
            self.oauth2_manager = OAuth2Manager(config.oauth2_config)
    
    def create_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection."""
        try:
            # Create connection
            if self.config.smtp_config.use_ssl:
                smtp = smtplib.SMTP_SSL(
                    self.config.smtp_config.server,
                    self.config.smtp_config.port,
                    timeout=self.config.smtp_config.timeout
                )
            else:
                smtp = smtplib.SMTP(
                    self.config.smtp_config.server,
                    self.config.smtp_config.port,
                    timeout=self.config.smtp_config.timeout
                )
            
            # Set debug level
            smtp.set_debuglevel(self.config.smtp_config.debug_level)
            
            # Start TLS if required
            if self.config.smtp_config.use_tls and not self.config.smtp_config.use_ssl:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
            
            # Authenticate
            self._authenticate(smtp)
            
            return smtp
            
        except Exception as e:
            logger.error(f"Error creating SMTP connection: {e}")
            raise
    
    def _authenticate(self, smtp: smtplib.SMTP):
        """Authenticate with SMTP server."""
        if self.config.auth_method == EmailAuthMethod.PASSWORD:
            smtp.login(self.config.username, self.config.password)
            
        elif self.config.auth_method == EmailAuthMethod.OAUTH2:
            if not self.oauth2_manager:
                raise ValueError("OAuth2 manager not configured")
            
            access_token = self.oauth2_manager.get_access_token()
            auth_string = f"user={self.config.username}\x01auth=Bearer {access_token}\x01\x01"
            smtp.auth("XOAUTH2", lambda: auth_string.encode())
            
        elif self.config.auth_method == EmailAuthMethod.APP_PASSWORD:
            smtp.login(self.config.username, self.config.password)
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SMTP connection."""
        try:
            with self.create_connection() as smtp:
                smtp.noop()
            return True, None
        except Exception as e:
            return False, str(e)


class EmailSender:
    """Main email sending service."""
    
    def __init__(self, config: EmailConfig, template_manager: Optional[EmailTemplateManager] = None):
        self.config = config
        self.template_manager = template_manager or EmailTemplateManager()
        self.smtp_client = SMTPClient(config)
        self.tracker = EmailTracker()
        self.validator = EmailValidator()
    
    def send_email(self, message: EmailMessage) -> EmailDeliveryResult:
        """Send a single email."""
        try:
            # Validate recipients
            for recipient in message.recipients:
                is_valid, error = self.validator.validate_email(recipient.email)
                if not is_valid:
                    raise ValueError(f"Invalid recipient {recipient.email}: {error}")
            
            # Create MIME message
            mime_message = self._create_mime_message(message)
            
            # Generate message ID
            message_id = mime_message['Message-ID']
            
            # Track email
            result = self.tracker.track_email(message_id, EmailStatus.SENDING)
            
            # Send email
            with self.smtp_client.create_connection() as smtp:
                from_addr = self.config.from_email
                to_addrs = [r.email for r in message.recipients if r.type == "to"]
                cc_addrs = [r.email for r in message.recipients if r.type == "cc"]
                bcc_addrs = [r.email for r in message.recipients if r.type == "bcc"]
                
                all_recipients = to_addrs + cc_addrs + bcc_addrs
                
                smtp.send_message(mime_message, from_addr, all_recipients)
            
            # Update tracking
            self.tracker.track_email(message_id, EmailStatus.SENT)
            logger.info(f"Email sent successfully: {message_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            if 'message_id' in locals():
                return self.tracker.track_email(message_id, EmailStatus.FAILED, str(e))
            else:
                # Create a dummy result for failed emails without message ID
                return EmailDeliveryResult(
                    message_id="unknown",
                    status=EmailStatus.FAILED,
                    error_message=str(e)
                )
    
    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message from EmailMessage."""
        # Create multipart message
        mime_msg = MIMEMultipart('mixed')
        
        # Set headers
        mime_msg['From'] = formataddr((self.config.from_name, self.config.from_email))
        
        # Set recipients
        to_recipients = [r for r in message.recipients if r.type == "to"]
        cc_recipients = [r for r in message.recipients if r.type == "cc"]
        
        if to_recipients:
            mime_msg['To'] = ', '.join(r.format_address() for r in to_recipients)
        
        if cc_recipients:
            mime_msg['Cc'] = ', '.join(r.format_address() for r in cc_recipients)
        
        mime_msg['Subject'] = message.subject
        
        if self.config.reply_to:
            mime_msg['Reply-To'] = self.config.reply_to
        
        # Set priority
        if message.priority != EmailPriority.NORMAL:
            priority_headers = {
                EmailPriority.LOW: ('3', 'Low'),
                EmailPriority.HIGH: ('1', 'High'),
                EmailPriority.URGENT: ('1', 'Urgent')
            }
            if message.priority in priority_headers:
                priority, importance = priority_headers[message.priority]
                mime_msg['X-Priority'] = priority
                mime_msg['Importance'] = importance
        
        # Add custom headers
        for header, value in message.headers.items():
            mime_msg[header] = value
        
        # Create body container
        body_container = MIMEMultipart('alternative')
        
        # Add text body
        if message.text_body:
            text_part = MIMEText(message.text_body, 'plain', 'utf-8')
            body_container.attach(text_part)
        
        # Add HTML body
        if message.html_body:
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            body_container.attach(html_part)
        
        mime_msg.attach(body_container)
        
        # Add attachments
        for attachment in message.attachments:
            self._add_attachment(mime_msg, attachment)
        
        return mime_msg
    
    def _add_attachment(self, mime_msg: MIMEMultipart, attachment: EmailAttachment):
        """Add attachment to MIME message."""
        try:
            with open(attachment.file_path, 'rb') as f:
                attachment_data = f.read()
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_data)
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.filename}'
            )
            
            if attachment.content_type:
                part.set_type(attachment.content_type)
            
            mime_msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {attachment.file_path}: {e}")
            raise
    
    def send_template_email(self, template_name: str, recipients: List[EmailRecipient],
                           template_vars: Dict[str, Any],
                           attachments: List[EmailAttachment] = None) -> EmailDeliveryResult:
        """Send email using template."""
        try:
            # Render subject and body
            subject = self.template_manager.render_template(f"{template_name}_subject.txt", template_vars)
            html_body = self.template_manager.render_template(f"{template_name}.html", template_vars)
            
            # Try to render text version
            text_body = None
            try:
                text_body = self.template_manager.render_template(f"{template_name}.txt", template_vars)
            except:
                pass  # Text template is optional
            
            # Create message
            message = EmailMessage(
                recipients=recipients,
                subject=subject.strip(),
                html_body=html_body,
                text_body=text_body,
                attachments=attachments or [],
                template_name=template_name,
                template_vars=template_vars
            )
            
            return self.send_email(message)
            
        except Exception as e:
            logger.error(f"Error sending template email {template_name}: {e}")
            raise
    
    def send_receipt_notification(self, log_entry: ReceiptProcessingLog,
                                 recipients: List[EmailRecipient],
                                 include_attachment: bool = True) -> EmailDeliveryResult:
        """Send receipt processing notification."""
        template_vars = self.template_manager.get_template_vars_for_receipt(log_entry)
        
        # Determine template based on status
        if log_entry.current_status == ProcessingStatus.PROCESSED:
            template_name = "receipt_processed"
        elif log_entry.current_status == ProcessingStatus.ERROR:
            template_name = "receipt_error"
            template_vars['error_message'] = log_entry.last_error or "Unknown error"
            template_vars['error_time'] = datetime.now()
        else:
            template_name = "receipt_status_update"
        
        # Add attachment if requested and file exists
        attachments = []
        if include_attachment and log_entry.file_path and log_entry.file_path.exists():
            attachments.append(EmailAttachment(
                file_path=log_entry.file_path,
                filename=log_entry.original_filename
            ))
        
        return self.send_template_email(template_name, recipients, template_vars, attachments)
    
    def test_email_system(self, test_recipient: str) -> Tuple[bool, str]:
        """Test the email system with a test email."""
        try:
            # Test SMTP connection
            connection_ok, error = self.smtp_client.test_connection()
            if not connection_ok:
                return False, f"SMTP connection failed: {error}"
            
            # Send test email
            recipients = [EmailRecipient(email=test_recipient)]
            message = EmailMessage(
                recipients=recipients,
                subject="Email System Test",
                html_body="<p>This is a test email from the Receipt Processor system.</p>",
                text_body="This is a test email from the Receipt Processor system."
            )
            
            result = self.send_email(message)
            
            if result.status == EmailStatus.SENT:
                return True, "Test email sent successfully"
            else:
                return False, f"Test email failed: {result.error_message}"
                
        except Exception as e:
            return False, f"Email system test failed: {str(e)}"
