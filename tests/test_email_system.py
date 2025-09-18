"""
Tests for Email Integration System.

This module tests email configuration, template management, SMTP client,
delivery tracking, and Gmail integration capabilities.
"""

import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.receipt_processor.email_system import (
    EmailAuthMethod, EmailProvider, EmailStatus, EmailPriority,
    OAuth2Config, SMTPConfig, EmailConfig, EmailRecipient, EmailAttachment,
    EmailTemplate, EmailMessage, EmailDeliveryResult, EmailProviderConfig,
    OAuth2Manager, EmailTemplateManager, EmailValidator, EmailTracker,
    SMTPClient, EmailSender
)
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)


class TestEmailRecipient:
    """Test cases for email recipient handling."""
    
    def test_valid_email_recipient(self):
        """Test creating valid email recipient."""
        recipient = EmailRecipient(email="test@example.com", name="Test User")
        assert recipient.email == "test@example.com"
        assert recipient.name == "Test User"
        assert recipient.type == "to"
    
    def test_invalid_email_recipient(self):
        """Test creating invalid email recipient."""
        with pytest.raises(ValueError):
            EmailRecipient(email="invalid-email")
    
    def test_format_address_with_name(self):
        """Test formatting address with name."""
        recipient = EmailRecipient(email="test@example.com", name="Test User")
        formatted = recipient.format_address()
        assert "Test User" in formatted
        assert "test@example.com" in formatted
    
    def test_format_address_without_name(self):
        """Test formatting address without name."""
        recipient = EmailRecipient(email="test@example.com")
        formatted = recipient.format_address()
        assert formatted == "test@example.com"


class TestEmailAttachment:
    """Test cases for email attachments."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_file.write(b'test image content')
        temp_file.close()
        yield Path(temp_file.name)
        Path(temp_file.name).unlink()
    
    def test_create_attachment(self, temp_file):
        """Test creating email attachment."""
        attachment = EmailAttachment(file_path=temp_file)
        assert attachment.file_path == temp_file
        assert attachment.filename == temp_file.name
        assert attachment.content_type == 'image/jpeg'
        assert not attachment.inline
    
    def test_custom_attachment_properties(self, temp_file):
        """Test attachment with custom properties."""
        attachment = EmailAttachment(
            file_path=temp_file,
            filename="custom.jpg",
            content_type="image/png",
            inline=True
        )
        assert attachment.filename == "custom.jpg"
        assert attachment.content_type == "image/png"
        assert attachment.inline
    
    def test_content_type_guessing(self, temp_file):
        """Test content type guessing from extension."""
        # Create files with different extensions
        extensions_and_types = [
            ('.pdf', 'application/pdf'),
            ('.txt', 'text/plain'),
            ('.csv', 'text/csv'),
            ('.json', 'application/json'),
            ('.unknown', 'application/octet-stream')
        ]
        
        for ext, expected_type in extensions_and_types:
            test_file = temp_file.with_suffix(ext)
            test_file.write_bytes(b'test content')
            
            attachment = EmailAttachment(file_path=test_file)
            assert attachment.content_type == expected_type
            
            test_file.unlink()


class TestEmailProviderConfig:
    """Test cases for email provider configurations."""
    
    def test_gmail_config_creation(self):
        """Test creating Gmail configuration."""
        config = EmailProviderConfig.create_gmail_config(
            username="test@gmail.com",
            auth_method=EmailAuthMethod.APP_PASSWORD,
            password="app-password-123"
        )
        
        assert config.provider == EmailProvider.GMAIL
        assert config.smtp_config.server == "smtp.gmail.com"
        assert config.smtp_config.port == 587
        assert config.smtp_config.use_tls
        assert config.auth_method == EmailAuthMethod.APP_PASSWORD
        assert config.username == "test@gmail.com"
        assert config.password == "app-password-123"
    
    def test_gmail_oauth2_config(self):
        """Test Gmail OAuth2 configuration."""
        oauth2_config = OAuth2Config(
            client_id="client-id",
            client_secret="client-secret",
            refresh_token="refresh-token"
        )
        
        config = EmailProviderConfig.create_gmail_config(
            username="test@gmail.com",
            auth_method=EmailAuthMethod.OAUTH2,
            oauth2_config=oauth2_config
        )
        
        assert config.auth_method == EmailAuthMethod.OAUTH2
        assert config.oauth2_config == oauth2_config
    
    def test_provider_config_retrieval(self):
        """Test retrieving provider configurations."""
        gmail_config = EmailProviderConfig.get_config(EmailProvider.GMAIL)
        assert "smtp_config" in gmail_config
        assert gmail_config["smtp_config"].server == "smtp.gmail.com"
        
        outlook_config = EmailProviderConfig.get_config(EmailProvider.OUTLOOK)
        assert outlook_config["smtp_config"].server == "smtp-mail.outlook.com"


class TestOAuth2Manager:
    """Test cases for OAuth2 token management."""
    
    @pytest.fixture
    def oauth2_config(self):
        """Create OAuth2 configuration for testing."""
        return OAuth2Config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            refresh_token="test-refresh-token",
            access_token="test-access-token",
            token_expiry=datetime.now() + timedelta(hours=1)
        )
    
    def test_oauth2_manager_creation(self, oauth2_config):
        """Test creating OAuth2 manager."""
        manager = OAuth2Manager(oauth2_config)
        assert manager.config == oauth2_config
    
    def test_token_not_expired(self, oauth2_config):
        """Test token that is not expired."""
        manager = OAuth2Manager(oauth2_config)
        assert not manager._is_token_expired()
    
    def test_token_expired(self, oauth2_config):
        """Test expired token."""
        oauth2_config.token_expiry = datetime.now() - timedelta(hours=1)
        manager = OAuth2Manager(oauth2_config)
        assert manager._is_token_expired()
    
    @patch('requests.post')
    def test_token_refresh(self, mock_post, oauth2_config):
        """Test token refresh."""
        # Make token expired
        oauth2_config.token_expiry = datetime.now() - timedelta(hours=1)
        
        # Mock successful refresh response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        manager = OAuth2Manager(oauth2_config)
        manager._refresh_access_token()
        
        assert oauth2_config.access_token == 'new-access-token'
        assert oauth2_config.token_expiry > datetime.now()


class TestEmailTemplateManager:
    """Test cases for email template management."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for templates."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_manager(self, temp_dir):
        """Create template manager for testing."""
        return EmailTemplateManager(template_dir=temp_dir)
    
    def test_template_manager_creation(self, template_manager, temp_dir):
        """Test creating template manager."""
        assert template_manager.template_dir == temp_dir
        assert template_manager.template_dir.exists()
    
    def test_default_templates_creation(self, template_manager):
        """Test that default templates are created."""
        expected_templates = [
            "receipt_processed.html",
            "receipt_error.html",
            "receipt_summary.html"
        ]
        
        for template_name in expected_templates:
            template_file = template_manager.template_dir / template_name
            assert template_file.exists()
    
    def test_template_rendering(self, template_manager):
        """Test template rendering with variables."""
        # Create simple test template
        test_template = template_manager.template_dir / "test.html"
        test_template.write_text("<h1>Hello {{ name }}!</h1>")
        
        rendered = template_manager.render_template("test.html", {"name": "World"})
        assert rendered == "<h1>Hello World!</h1>"
    
    def test_receipt_template_variables(self, template_manager):
        """Test getting template variables for receipt."""
        receipt_data = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("99.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="receipt.jpg",
            file_path=Path("/test/receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data,
            confidence_score=0.9
        )
        
        variables = template_manager.get_template_vars_for_receipt(log_entry)
        
        assert variables["vendor_name"] == "Test Store"
        assert variables["total_amount"] == Decimal("99.99")
        assert variables["currency"] == "USD"
        assert variables["confidence_score"] == 90
        assert variables["extraction_confidence"] == 95


class TestEmailValidator:
    """Test cases for email validation."""
    
    def test_valid_emails(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.com",
            "user+tag@example.org",
            "123@example.net",
            "test@sub.domain.com"
        ]
        
        for email in valid_emails:
            is_valid, error = EmailValidator.validate_email(email)
            assert is_valid, f"Email {email} should be valid but got error: {error}"
    
    def test_invalid_emails(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            "",
            "invalid",
            "@example.com",
            "test@",
            "test..test@example.com",
            ".test@example.com",
            "test@example."
        ]
        
        for email in invalid_emails:
            is_valid, error = EmailValidator.validate_email(email)
            assert not is_valid, f"Email {email} should be invalid but was marked as valid"
    
    def test_config_validation(self):
        """Test email configuration validation."""
        # Valid configuration
        valid_config = EmailConfig(
            provider=EmailProvider.GMAIL,
            smtp_config=SMTPConfig(server="smtp.gmail.com", port=587),
            auth_method=EmailAuthMethod.PASSWORD,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com"
        )
        
        issues = EmailValidator.validate_config(valid_config)
        assert len(issues) == 0
        
        # Invalid configuration - missing password
        invalid_config = EmailConfig(
            provider=EmailProvider.GMAIL,
            smtp_config=SMTPConfig(server="smtp.gmail.com", port=587),
            auth_method=EmailAuthMethod.PASSWORD,
            username="test@gmail.com",
            from_email="invalid-email"
        )
        
        issues = EmailValidator.validate_config(invalid_config)
        assert len(issues) > 0
        assert any("password" in issue.lower() for issue in issues)
        assert any("from_email" in issue.lower() for issue in issues)


class TestEmailTracker:
    """Test cases for email delivery tracking."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for tracking storage."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        temp_file.close()
        yield Path(temp_file.name)
        Path(temp_file.name).unlink()
    
    @pytest.fixture
    def tracker(self, temp_file):
        """Create email tracker for testing."""
        return EmailTracker(storage_file=temp_file)
    
    def test_tracker_creation(self, tracker):
        """Test creating email tracker."""
        assert isinstance(tracker.delivery_results, dict)
        assert len(tracker.delivery_results) == 0
    
    def test_email_tracking(self, tracker):
        """Test tracking email delivery."""
        message_id = "test-message-123"
        
        # Track sending
        result = tracker.track_email(message_id, EmailStatus.SENDING)
        assert result.message_id == message_id
        assert result.status == EmailStatus.SENDING
        
        # Track sent
        result = tracker.track_email(message_id, EmailStatus.SENT)
        assert result.status == EmailStatus.SENT
        assert result.sent_at is not None
        
        # Track delivered
        result = tracker.track_email(message_id, EmailStatus.DELIVERED)
        assert result.status == EmailStatus.DELIVERED
        assert result.delivered_at is not None
    
    def test_error_tracking(self, tracker):
        """Test tracking email errors."""
        message_id = "error-message-123"
        error_message = "SMTP connection failed"
        
        result = tracker.track_email(message_id, EmailStatus.FAILED, error_message)
        assert result.status == EmailStatus.FAILED
        assert result.error_message == error_message
        assert result.retry_count == 1
    
    def test_delivery_statistics(self, tracker):
        """Test delivery statistics calculation."""
        # Track various email statuses
        tracker.track_email("msg1", EmailStatus.SENT)
        tracker.track_email("msg2", EmailStatus.DELIVERED)
        tracker.track_email("msg3", EmailStatus.FAILED)
        tracker.track_email("msg4", EmailStatus.BOUNCED)
        tracker.track_email("msg5", EmailStatus.PENDING)
        
        stats = tracker.get_delivery_stats()
        assert stats['total_emails'] == 5
        assert stats['sent'] == 1
        assert stats['delivered'] == 1
        assert stats['failed'] == 1
        assert stats['bounced'] == 1
        assert stats['pending'] == 1
        assert stats['success_rate'] == 40.0  # (1+1)/5 * 100
        assert stats['bounce_rate'] == 20.0   # 1/5 * 100
    
    def test_data_persistence(self, tracker, temp_file):
        """Test saving and loading tracking data."""
        # Track some emails
        tracker.track_email("msg1", EmailStatus.SENT)
        tracker.track_email("msg2", EmailStatus.FAILED, "Error message")
        
        # Create new tracker with same file
        new_tracker = EmailTracker(storage_file=temp_file)
        
        # Check data was loaded
        assert len(new_tracker.delivery_results) == 2
        assert "msg1" in new_tracker.delivery_results
        assert "msg2" in new_tracker.delivery_results
        assert new_tracker.delivery_results["msg2"].error_message == "Error message"


class TestSMTPClient:
    """Test cases for SMTP client."""
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration for testing."""
        return EmailConfig(
            provider=EmailProvider.GMAIL,
            smtp_config=SMTPConfig(server="smtp.gmail.com", port=587, use_tls=True),
            auth_method=EmailAuthMethod.PASSWORD,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com"
        )
    
    def test_smtp_client_creation(self, email_config):
        """Test creating SMTP client."""
        client = SMTPClient(email_config)
        assert client.config == email_config
        assert client.oauth2_manager is None
    
    def test_oauth2_smtp_client(self, email_config):
        """Test SMTP client with OAuth2."""
        oauth2_config = OAuth2Config(
            client_id="client-id",
            client_secret="client-secret",
            refresh_token="refresh-token"
        )
        
        email_config.auth_method = EmailAuthMethod.OAUTH2
        email_config.oauth2_config = oauth2_config
        
        client = SMTPClient(email_config)
        assert client.oauth2_manager is not None
    
    @patch('smtplib.SMTP')
    def test_connection_creation(self, mock_smtp, email_config):
        """Test SMTP connection creation."""
        # Mock SMTP connection
        mock_connection = Mock()
        mock_smtp.return_value = mock_connection
        
        client = SMTPClient(email_config)
        
        with patch.object(client, '_authenticate'):
            connection = client.create_connection()
            
            mock_smtp.assert_called_once_with(
                "smtp.gmail.com", 587, timeout=30
            )
            mock_connection.starttls.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_connection_test(self, mock_smtp, email_config):
        """Test SMTP connection testing."""
        # Mock successful connection
        mock_connection = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_connection
        
        client = SMTPClient(email_config)
        
        with patch.object(client, '_authenticate'):
            success, error = client.test_connection()
            
            assert success
            assert error is None
            mock_connection.noop.assert_called_once()


class TestEmailSender:
    """Test cases for email sender."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for templates."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration for testing."""
        return EmailConfig(
            provider=EmailProvider.GMAIL,
            smtp_config=SMTPConfig(server="smtp.gmail.com", port=587, use_tls=True),
            auth_method=EmailAuthMethod.PASSWORD,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com",
            from_name="Test Sender"
        )
    
    @pytest.fixture
    def email_sender(self, email_config, temp_dir):
        """Create email sender for testing."""
        template_manager = EmailTemplateManager(template_dir=temp_dir)
        return EmailSender(email_config, template_manager)
    
    def test_email_sender_creation(self, email_sender, email_config):
        """Test creating email sender."""
        assert email_sender.config == email_config
        assert email_sender.template_manager is not None
        assert email_sender.smtp_client is not None
        assert email_sender.tracker is not None
    
    @patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp, email_sender):
        """Test sending email."""
        # Mock SMTP connection
        mock_connection = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_connection
        
        # Create test message
        recipients = [EmailRecipient(email="recipient@example.com", name="Test Recipient")]
        message = EmailMessage(
            recipients=recipients,
            subject="Test Subject",
            html_body="<p>Test HTML body</p>",
            text_body="Test text body"
        )
        
        # Mock authentication
        with patch.object(email_sender.smtp_client, '_authenticate'):
            result = email_sender.send_email(message)
            
            assert result.status == EmailStatus.SENT
            mock_connection.send_message.assert_called_once()
    
    def test_invalid_recipient_email(self, email_sender):
        """Test sending email with invalid recipient."""
        recipients = [EmailRecipient.__new__(EmailRecipient)]
        recipients[0].email = "invalid-email"
        recipients[0].name = "Test"
        recipients[0].type = "to"
        
        message = EmailMessage(
            recipients=recipients,
            subject="Test Subject",
            html_body="<p>Test HTML body</p>"
        )
        
        result = email_sender.send_email(message)
        assert result.status == EmailStatus.FAILED
        assert "Invalid recipient" in result.error_message
    
    def test_mime_message_creation(self, email_sender):
        """Test MIME message creation."""
        recipients = [
            EmailRecipient(email="to@example.com", name="To User", type="to"),
            EmailRecipient(email="cc@example.com", name="CC User", type="cc"),
            EmailRecipient(email="bcc@example.com", name="BCC User", type="bcc")
        ]
        
        message = EmailMessage(
            recipients=recipients,
            subject="Test Subject",
            html_body="<p>Test HTML body</p>",
            text_body="Test text body",
            priority=EmailPriority.HIGH,
            headers={"X-Custom": "CustomValue"}
        )
        
        mime_msg = email_sender._create_mime_message(message)
        
        assert mime_msg['Subject'] == "Test Subject"
        assert mime_msg['From'] == "Test Sender <test@gmail.com>"
        assert "to@example.com" in mime_msg['To']
        assert "cc@example.com" in mime_msg['Cc']
        assert mime_msg['X-Priority'] == '1'
        assert mime_msg['X-Custom'] == 'CustomValue'
    
    def test_receipt_notification(self, email_sender):
        """Test sending receipt notification."""
        # Create receipt data
        receipt_data = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("99.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="receipt.jpg",
            file_path=Path("/test/receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data
        )
        
        recipients = [EmailRecipient(email="user@example.com")]
        
        # Mock SMTP sending
        with patch.object(email_sender, 'send_template_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                message_id="test-123",
                status=EmailStatus.SENT
            )
            
            result = email_sender.send_receipt_notification(log_entry, recipients)
            
            assert result.status == EmailStatus.SENT
            mock_send.assert_called_once()
            
            # Check template name based on status
            call_args = mock_send.call_args
            assert call_args[0][0] == "receipt_processed"  # template name
    
    @patch('smtplib.SMTP')
    def test_email_system_test(self, mock_smtp, email_sender):
        """Test email system testing functionality."""
        # Mock successful connection and sending
        mock_connection = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_connection
        
        with patch.object(email_sender.smtp_client, '_authenticate'):
            success, message = email_sender.test_email_system("test@example.com")
            
            assert success
            assert "successfully" in message.lower()


class TestIntegration:
    """Integration tests for email system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_complete_email_workflow(self, temp_dir):
        """Test complete email workflow."""
        # Create Gmail configuration
        config = EmailProviderConfig.create_gmail_config(
            username="test@gmail.com",
            auth_method=EmailAuthMethod.APP_PASSWORD,
            password="test-app-password"
        )
        
        # Create email sender
        template_manager = EmailTemplateManager(template_dir=temp_dir)
        sender = EmailSender(config, template_manager)
        
        # Create test receipt
        receipt_data = ReceiptData(
            vendor_name="Apple Store",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("299.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="receipt.jpg",
            file_path=Path("/test/receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data,
            confidence_score=0.9
        )
        
        # Test template variable generation
        template_vars = template_manager.get_template_vars_for_receipt(log_entry)
        assert template_vars["vendor_name"] == "Apple Store"
        assert template_vars["total_amount"] == Decimal("299.99")
        assert template_vars["confidence_score"] == 90
        
        # Test email validation
        recipients = [EmailRecipient(email="user@example.com", name="Test User")]
        is_valid, error = EmailValidator.validate_email(recipients[0].email)
        assert is_valid
        
        # Test configuration validation
        issues = EmailValidator.validate_config(config)
        assert len(issues) == 0
        
        # Test tracking initialization
        tracker = EmailTracker(storage_file=temp_dir / "test_tracking.json")
        stats = tracker.get_delivery_stats()
        assert stats['total_emails'] == 0
        
        print("✅ Email system integration test completed successfully!")
