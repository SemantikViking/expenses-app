#!/usr/bin/env python3
"""
Example usage of the Email Integration System with Gmail.

This script demonstrates comprehensive email capabilities including Gmail SMTP
configuration, OAuth2 authentication, template management, and delivery tracking.
"""

import tempfile
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Import the email system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

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


def main():
    """Demonstrate the email integration system with Gmail."""
    print("📧 Email Integration System with Gmail Demo")
    print("=" * 60)
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"📁 Using temporary directory: {temp_path}")
        print()
        
        # Demonstrate Gmail configuration options
        print("🔧 Demonstrating Gmail configuration options...")
        demonstrate_gmail_configurations()
        print()
        
        # Demonstrate OAuth2 token management
        print("🔐 Demonstrating OAuth2 token management...")
        demonstrate_oauth2_management()
        print()
        
        # Demonstrate email validation
        print("✅ Demonstrating email validation...")
        demonstrate_email_validation()
        print()
        
        # Demonstrate email templates
        print("📝 Demonstrating email templates...")
        demonstrate_email_templates(temp_path)
        print()
        
        # Demonstrate email composition
        print("✉️  Demonstrating email composition...")
        demonstrate_email_composition(temp_path)
        print()
        
        # Demonstrate delivery tracking
        print("📊 Demonstrating delivery tracking...")
        demonstrate_delivery_tracking(temp_path)
        print()
        
        # Demonstrate receipt notifications
        print("📧 Demonstrating receipt notifications...")
        demonstrate_receipt_notifications(temp_path)
        print()
        
        print("🎉 Email integration system demo completed successfully!")
        print("\n📋 Next Steps for Gmail Integration:")
        print("1. Set up Gmail App Password or OAuth2 credentials")
        print("2. Configure email settings in your application")
        print("3. Test email delivery with your Gmail account")
        print("4. Set up email templates for your organization")
        print("5. Configure delivery tracking and bounce handling")


def demonstrate_gmail_configurations():
    """Demonstrate different Gmail configuration options."""
    print("  📧 Gmail Configuration Options:")
    
    # App Password configuration (simpler)
    print("    🔑 App Password Configuration:")
    app_password_config = EmailProviderConfig.create_gmail_config(
        username="receipts@yourcompany.com",
        auth_method=EmailAuthMethod.APP_PASSWORD,
        password="abcd-efgh-ijkl-mnop"  # 16-character app password
    )
    
    print(f"      SMTP Server: {app_password_config.smtp_config.server}")
    print(f"      Port: {app_password_config.smtp_config.port}")
    print(f"      TLS: {app_password_config.smtp_config.use_tls}")
    print(f"      Auth Method: {app_password_config.auth_method.value}")
    print(f"      Rate Limit: {app_password_config.rate_limit_per_hour}/hour")
    
    # OAuth2 configuration (more secure)
    print("    🔐 OAuth2 Configuration:")
    oauth2_config = OAuth2Config(
        client_id="your-oauth-client-id.googleusercontent.com",
        client_secret="your-oauth-client-secret",
        refresh_token="your-refresh-token"
    )
    
    oauth2_email_config = EmailProviderConfig.create_gmail_config(
        username="receipts@yourcompany.com",
        auth_method=EmailAuthMethod.OAUTH2,
        oauth2_config=oauth2_config
    )
    
    print(f"      OAuth2 Client ID: {oauth2_config.client_id[:20]}...")
    print(f"      Scope: {oauth2_config.scope}")
    print(f"      Auth Method: {oauth2_email_config.auth_method.value}")
    
    # Custom SMTP configuration
    print("    ⚙️  Custom SMTP Configuration:")
    custom_config = EmailConfig(
        provider=EmailProvider.GMAIL,
        smtp_config=SMTPConfig(
            server="smtp.gmail.com",
            port=465,  # SSL port
            use_ssl=True,
            use_tls=False,
            timeout=60
        ),
        auth_method=EmailAuthMethod.APP_PASSWORD,
        username="receipts@yourcompany.com",
        password="your-app-password",
        from_email="receipts@yourcompany.com",
        from_name="Receipt Processing System",
        reply_to="noreply@yourcompany.com"
    )
    
    print(f"      SSL Port: {custom_config.smtp_config.port}")
    print(f"      SSL: {custom_config.smtp_config.use_ssl}")
    print(f"      From Name: {custom_config.from_name}")
    print(f"      Reply-To: {custom_config.reply_to}")


def demonstrate_oauth2_management():
    """Demonstrate OAuth2 token management."""
    print("  🔐 OAuth2 Token Management:")
    
    # Create OAuth2 configuration
    oauth2_config = OAuth2Config(
        client_id="123456789.apps.googleusercontent.com",
        client_secret="your-client-secret",
        refresh_token="1//04-refresh-token",
        access_token="ya29.current-access-token",
        token_expiry=datetime.now()  # Expired token for demo
    )
    
    oauth2_manager = OAuth2Manager(oauth2_config)
    
    print(f"    Client ID: {oauth2_config.client_id}")
    print(f"    Token Expired: {oauth2_manager._is_token_expired()}")
    print(f"    Scope: {oauth2_config.scope}")
    
    print("    📝 OAuth2 Setup Instructions:")
    print("      1. Go to Google Cloud Console")
    print("      2. Enable Gmail API")
    print("      3. Create OAuth2 credentials")
    print("      4. Get authorization code")
    print("      5. Exchange for refresh token")
    print("      6. Use refresh token in configuration")


def demonstrate_email_validation():
    """Demonstrate email address and configuration validation."""
    print("  ✅ Email Validation Examples:")
    
    # Test email addresses
    test_emails = [
        "user@gmail.com",
        "receipts@yourcompany.com",
        "finance.team@company.co.uk",
        "invalid-email",
        "@gmail.com",
        "user@"
    ]
    
    print("    📧 Email Address Validation:")
    for email in test_emails:
        is_valid, error = EmailValidator.validate_email(email)
        status = "✅" if is_valid else "❌"
        print(f"      {status} {email}")
        if error:
            print(f"        Error: {error}")
    
    # Test configuration validation
    print("    ⚙️  Configuration Validation:")
    
    # Valid configuration
    valid_config = EmailProviderConfig.create_gmail_config(
        username="receipts@yourcompany.com",
        auth_method=EmailAuthMethod.APP_PASSWORD,
        password="valid-app-password"
    )
    
    issues = EmailValidator.validate_config(valid_config)
    print(f"      Valid config issues: {len(issues)}")
    
    # Invalid configuration
    invalid_config = EmailConfig(
        provider=EmailProvider.GMAIL,
        smtp_config=SMTPConfig(server="", port=0),  # Invalid
        auth_method=EmailAuthMethod.PASSWORD,
        username="invalid-email",
        from_email="another-invalid-email"
    )
    
    issues = EmailValidator.validate_config(invalid_config)
    print(f"      Invalid config issues: {len(issues)}")
    for issue in issues:
        print(f"        - {issue}")


def demonstrate_email_templates(temp_path):
    """Demonstrate email template management."""
    print("  📝 Email Template Management:")
    
    # Create template manager
    template_manager = EmailTemplateManager(template_dir=temp_path)
    
    # List default templates
    print("    📄 Default Templates Created:")
    for template_file in template_manager.template_dir.glob("*.html"):
        print(f"      - {template_file.name}")
    
    # Create custom template
    custom_template = temp_path / "custom_notification.html"
    custom_template.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Custom Receipt Notification</title>
</head>
<body>
    <h2>Receipt Processed: {{ vendor_name }}</h2>
    <p>Dear {{ recipient_name }},</p>
    <p>Your receipt from <strong>{{ vendor_name }}</strong> has been processed:</p>
    
    <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
        <p><strong>Amount:</strong> ${{ total_amount }} {{ currency }}</p>
        <p><strong>Date:</strong> {{ transaction_date }}</p>
        <p><strong>Status:</strong> {{ current_status }}</p>
    </div>
    
    <p>Thank you for using our receipt processing system!</p>
</body>
</html>
    """.strip())
    
    # Render template with variables
    template_vars = {
        "vendor_name": "Apple Store",
        "recipient_name": "John Doe",
        "total_amount": "299.99",
        "currency": "USD",
        "transaction_date": "2023-12-25",
        "current_status": "Processed"
    }
    
    rendered = template_manager.render_template("custom_notification.html", template_vars)
    print(f"    📝 Custom template rendered successfully ({len(rendered)} characters)")
    
    # Test receipt template variables
    receipt_data = ReceiptData(
        vendor_name="Starbucks",
        transaction_date=datetime(2023, 12, 25),
        total_amount=Decimal("4.75"),
        currency=Currency.USD,
        extraction_confidence=0.95,
        has_required_data=True
    )
    
    log_entry = ReceiptProcessingLog(
        original_filename="starbucks_receipt.jpg",
        file_path=Path("/receipts/starbucks_receipt.jpg"),
        file_size=1024,
        current_status=ProcessingStatus.PROCESSED,
        receipt_data=receipt_data,
        confidence_score=0.9
    )
    
    receipt_vars = template_manager.get_template_vars_for_receipt(log_entry)
    print(f"    📊 Receipt template variables: {len(receipt_vars)} variables")
    print(f"      - Vendor: {receipt_vars['vendor_name']}")
    print(f"      - Amount: ${receipt_vars['total_amount']}")
    print(f"      - Confidence: {receipt_vars['confidence_score']}%")


def demonstrate_email_composition(temp_path):
    """Demonstrate email message composition."""
    print("  ✉️  Email Message Composition:")
    
    # Create recipients
    recipients = [
        EmailRecipient(email="finance@yourcompany.com", name="Finance Team", type="to"),
        EmailRecipient(email="manager@yourcompany.com", name="Manager", type="cc"),
        EmailRecipient(email="audit@yourcompany.com", name="Audit Team", type="bcc")
    ]
    
    print(f"    👥 Recipients: {len(recipients)} total")
    for recipient in recipients:
        print(f"      - {recipient.type.upper()}: {recipient.format_address()}")
    
    # Create attachment (mock file)
    receipt_file = temp_path / "sample_receipt.jpg"
    receipt_file.write_bytes(b"Mock receipt image content")
    
    attachment = EmailAttachment(
        file_path=receipt_file,
        filename="apple_store_receipt.jpg",
        content_type="image/jpeg"
    )
    
    print(f"    📎 Attachment: {attachment.filename} ({attachment.content_type})")
    
    # Create email message
    message = EmailMessage(
        recipients=recipients,
        subject="Receipt Processed: Apple Store - $299.99",
        html_body="""
        <h2>Receipt Successfully Processed</h2>
        <p>A new receipt has been processed and is ready for review.</p>
        <p><strong>Vendor:</strong> Apple Store<br>
           <strong>Amount:</strong> $299.99<br>
           <strong>Date:</strong> 2023-12-25</p>
        """,
        text_body="Receipt Successfully Processed\n\nA new receipt has been processed and is ready for review.\n\nVendor: Apple Store\nAmount: $299.99\nDate: 2023-12-25",
        attachments=[attachment],
        priority=EmailPriority.NORMAL,
        headers={"X-Receipt-ID": "12345", "X-Processing-System": "Receipt-Processor"}
    )
    
    print(f"    📧 Message created:")
    print(f"      Subject: {message.subject}")
    print(f"      Priority: {message.priority.value}")
    print(f"      Attachments: {len(message.attachments)}")
    print(f"      Custom Headers: {len(message.headers)}")
    print(f"      HTML Body: {len(message.html_body)} characters")
    print(f"      Text Body: {len(message.text_body)} characters")


def demonstrate_delivery_tracking(temp_path):
    """Demonstrate email delivery tracking."""
    print("  📊 Email Delivery Tracking:")
    
    # Create tracker
    tracker = EmailTracker(storage_file=temp_path / "email_tracking.json")
    
    # Simulate email tracking
    messages = [
        ("msg-001", EmailStatus.SENT, None),
        ("msg-002", EmailStatus.DELIVERED, None),
        ("msg-003", EmailStatus.FAILED, "SMTP connection timeout"),
        ("msg-004", EmailStatus.BOUNCED, "Recipient inbox full"),
        ("msg-005", EmailStatus.RETRY, "Temporary server error")
    ]
    
    print("    📈 Tracking Email Deliveries:")
    for msg_id, status, error in messages:
        result = tracker.track_email(msg_id, status, error)
        status_icon = {
            EmailStatus.SENT: "✅",
            EmailStatus.DELIVERED: "📬",
            EmailStatus.FAILED: "❌",
            EmailStatus.BOUNCED: "⚠️",
            EmailStatus.RETRY: "🔄"
        }.get(status, "📧")
        
        print(f"      {status_icon} {msg_id}: {status.value}")
        if error:
            print(f"        Error: {error}")
    
    # Get delivery statistics
    stats = tracker.get_delivery_stats()
    print(f"    📊 Delivery Statistics:")
    print(f"      Total Emails: {stats['total_emails']}")
    print(f"      Success Rate: {stats['success_rate']:.1f}%")
    print(f"      Bounce Rate: {stats['bounce_rate']:.1f}%")
    print(f"      Sent: {stats['sent']}")
    print(f"      Delivered: {stats['delivered']}")
    print(f"      Failed: {stats['failed']}")
    print(f"      Bounced: {stats['bounced']}")


def demonstrate_receipt_notifications(temp_path):
    """Demonstrate receipt notification emails."""
    print("  📧 Receipt Notification System:")
    
    # Create email configuration (mock)
    config = EmailProviderConfig.create_gmail_config(
        username="receipts@yourcompany.com",
        auth_method=EmailAuthMethod.APP_PASSWORD,
        password="mock-app-password"
    )
    
    # Create email sender
    template_manager = EmailTemplateManager(template_dir=temp_path)
    sender = EmailSender(config, template_manager)
    
    print(f"    ⚙️  Email System Configuration:")
    print(f"      Provider: {config.provider.value}")
    print(f"      SMTP Server: {config.smtp_config.server}")
    print(f"      Auth Method: {config.auth_method.value}")
    print(f"      From: {config.from_name} <{config.from_email}>")
    
    # Create sample receipts
    receipts = [
        {
            "vendor": "Apple Store",
            "amount": Decimal("299.99"),
            "status": ProcessingStatus.PROCESSED,
            "confidence": 0.95
        },
        {
            "vendor": "Starbucks",
            "amount": Decimal("4.75"),
            "status": ProcessingStatus.PROCESSED,
            "confidence": 0.88
        },
        {
            "vendor": "Unknown Vendor",
            "amount": None,
            "status": ProcessingStatus.ERROR,
            "confidence": 0.45
        }
    ]
    
    print(f"    📧 Sample Receipt Notifications:")
    
    for i, receipt_info in enumerate(receipts):
        # Create receipt data
        receipt_data = None
        if receipt_info["amount"]:
            receipt_data = ReceiptData(
                vendor_name=receipt_info["vendor"],
                transaction_date=datetime(2023, 12, 25),
                total_amount=receipt_info["amount"],
                currency=Currency.USD,
                extraction_confidence=receipt_info["confidence"],
                has_required_data=True
            )
        
        # Create log entry
        log_entry = ReceiptProcessingLog(
            original_filename=f"receipt_{i+1}.jpg",
            file_path=Path(f"/receipts/receipt_{i+1}.jpg"),
            file_size=1024,
            current_status=receipt_info["status"],
            receipt_data=receipt_data,
            confidence_score=receipt_info["confidence"]
        )
        
        # Get template variables
        template_vars = template_manager.get_template_vars_for_receipt(log_entry)
        
        # Determine notification type
        if log_entry.current_status == ProcessingStatus.PROCESSED:
            notification_type = "✅ Success"
            template_name = "receipt_processed"
        elif log_entry.current_status == ProcessingStatus.ERROR:
            notification_type = "❌ Error"
            template_name = "receipt_error"
        else:
            notification_type = "📧 Status Update"
            template_name = "receipt_status_update"
        
        print(f"      {notification_type}: {receipt_info['vendor']}")
        print(f"        Template: {template_name}")
        print(f"        Variables: {len(template_vars)} template variables")
        if receipt_data:
            print(f"        Amount: ${receipt_data.total_amount}")
            print(f"        Confidence: {int(receipt_data.extraction_confidence * 100)}%")
    
    # Test email system (mock)
    print(f"    🧪 Email System Test:")
    print(f"      SMTP Connection: Would test connection to {config.smtp_config.server}")
    print(f"      Authentication: Would authenticate using {config.auth_method.value}")
    print(f"      Template Rendering: Templates loaded and ready")
    print(f"      Delivery Tracking: Tracking system initialized")
    
    print(f"    📋 Gmail Setup Checklist:")
    print(f"      ☐ Enable 2-factor authentication on Gmail")
    print(f"      ☐ Generate App Password (if using app password method)")
    print(f"      ☐ Or set up OAuth2 credentials (recommended)")
    print(f"      ☐ Configure email settings in application")
    print(f"      ☐ Test email delivery")
    print(f"      ☐ Set up email templates")
    print(f"      ☐ Configure bounce handling")


if __name__ == "__main__":
    main()
