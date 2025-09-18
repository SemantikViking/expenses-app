#!/usr/bin/env python3
"""
Example usage of the Email Workflow Integration System.

This script demonstrates comprehensive email workflow capabilities including
automated triggers, batch processing, manual email sending, and CLI integration.
"""

import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Import the email workflow system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.receipt_processor.email_workflow import (
    EmailWorkflowIntegrator, EmailTriggerRule, EmailWorkflowConfig,
    EmailTriggerType, EmailPriority, NotificationFrequency,
    EmailWorkflowEvent, EmailBatchManager, EmailWorkflowLogger
)
from src.receipt_processor.email_system import (
    EmailSender, EmailConfig, EmailRecipient, EmailProviderConfig,
    EmailAuthMethod, EmailTemplateManager
)
from src.receipt_processor.storage import JSONStorageManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)
from src.receipt_processor.templates.batch_templates import BatchTemplateManager


def main():
    """Demonstrate the complete email workflow integration system."""
    print("🔄 Email Workflow Integration System Demo")
    print("=" * 60)
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"📁 Using temporary directory: {temp_path}")
        print()
        
        # Demonstrate workflow configuration
        print("⚙️  Demonstrating workflow configuration...")
        demonstrate_workflow_configuration(temp_path)
        print()
        
        # Demonstrate trigger rules
        print("🎯 Demonstrating email trigger rules...")
        demonstrate_trigger_rules(temp_path)
        print()
        
        # Demonstrate batch processing
        print("📦 Demonstrating batch email processing...")
        demonstrate_batch_processing(temp_path)
        print()
        
        # Demonstrate manual email operations
        print("✉️  Demonstrating manual email operations...")
        demonstrate_manual_operations(temp_path)
        print()
        
        # Demonstrate bulk operations
        print("📊 Demonstrating bulk email operations...")
        demonstrate_bulk_operations(temp_path)
        print()
        
        # Demonstrate workflow monitoring
        print("📈 Demonstrating workflow monitoring...")
        demonstrate_workflow_monitoring(temp_path)
        print()
        
        # Demonstrate CLI integration
        print("💻 Demonstrating CLI integration...")
        demonstrate_cli_integration(temp_path)
        print()
        
        print("🎉 Email workflow integration demo completed successfully!")
        print("\n📋 Production Deployment Checklist:")
        print("1. Configure Gmail OAuth2 or App Password credentials")
        print("2. Set up email templates for your organization")
        print("3. Configure trigger rules based on business requirements")
        print("4. Set up batch processing schedules")
        print("5. Configure delivery tracking and monitoring")
        print("6. Test email workflows with real data")
        print("7. Set up CLI commands for operational management")


def demonstrate_workflow_configuration(temp_path):
    """Demonstrate email workflow configuration options."""
    print("  ⚙️  Email Workflow Configuration:")
    
    # Create email configuration
    email_config = EmailProviderConfig.create_gmail_config(
        username="receipts@yourcompany.com",
        auth_method=EmailAuthMethod.APP_PASSWORD,
        password="mock-app-password"
    )
    
    # Create workflow configuration
    workflow_config = EmailWorkflowConfig(
        enabled=True,
        default_recipients=[
            EmailRecipient(email="finance@yourcompany.com", name="Finance Team"),
            EmailRecipient(email="manager@yourcompany.com", name="Manager"),
            EmailRecipient(email="audit@yourcompany.com", name="Audit Team", type="bcc")
        ],
        batch_size=25,
        batch_timeout_minutes=30,
        max_retries=3,
        retry_delay_minutes=15,
        delivery_confirmation_required=True,
        error_escalation_enabled=True,
        escalation_threshold_hours=24
    )
    
    print(f"    📧 Email Provider: {email_config.provider.value}")
    print(f"    🔐 Authentication: {email_config.auth_method.value}")
    print(f"    📬 Default Recipients: {len(workflow_config.default_recipients)}")
    print(f"    📦 Batch Size: {workflow_config.batch_size}")
    print(f"    ⏰ Batch Timeout: {workflow_config.batch_timeout_minutes} minutes")
    print(f"    🔄 Max Retries: {workflow_config.max_retries}")
    print(f"    📊 Delivery Confirmation: {'✅' if workflow_config.delivery_confirmation_required else '❌'}")
    print(f"    🚨 Error Escalation: {'✅' if workflow_config.error_escalation_enabled else '❌'}")
    
    # Display recipient details
    print(f"    👥 Recipient Configuration:")
    for recipient in workflow_config.default_recipients:
        print(f"      - {recipient.type.upper()}: {recipient.format_address()}")


def demonstrate_trigger_rules(temp_path):
    """Demonstrate email trigger rule configuration and matching."""
    print("  🎯 Email Trigger Rules:")
    
    # Create various trigger rules
    trigger_rules = [
        # Success notification
        EmailTriggerRule(
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            status_conditions=[ProcessingStatus.PROCESSED],
            recipients=[EmailRecipient(email="finance@yourcompany.com")],
            template_name="receipt_processed",
            priority=EmailPriority.NORMAL,
            frequency=NotificationFrequency.IMMEDIATE
        ),
        
        # Error escalation
        EmailTriggerRule(
            trigger_type=EmailTriggerType.ERROR_OCCURRED,
            status_conditions=[ProcessingStatus.ERROR],
            recipients=[EmailRecipient(email="support@yourcompany.com")],
            template_name="error_escalation",
            priority=EmailPriority.URGENT,
            frequency=NotificationFrequency.IMMEDIATE
        ),
        
        # High-value receipt alert
        EmailTriggerRule(
            trigger_type=EmailTriggerType.PROCESSING_COMPLETE,
            status_conditions=[ProcessingStatus.PROCESSED],
            recipients=[EmailRecipient(email="executive@yourcompany.com")],
            template_name="high_value_receipt",
            priority=EmailPriority.HIGH,
            frequency=NotificationFrequency.IMMEDIATE,
            conditions={"min_amount": Decimal("1000.00")}
        ),
        
        # Daily summary
        EmailTriggerRule(
            trigger_type=EmailTriggerType.SCHEDULED_REPORT,
            recipients=[EmailRecipient(email="reports@yourcompany.com")],
            template_name="daily_summary",
            priority=EmailPriority.NORMAL,
            frequency=NotificationFrequency.BATCHED_DAILY
        ),
        
        # Vendor-specific notifications
        EmailTriggerRule(
            trigger_type=EmailTriggerType.WORKFLOW_MILESTONE,
            status_conditions=[ProcessingStatus.PROCESSED],
            recipients=[EmailRecipient(email="procurement@yourcompany.com")],
            template_name="vendor_notification",
            priority=EmailPriority.NORMAL,
            frequency=NotificationFrequency.BATCHED_HOURLY,
            conditions={"vendor_name": "Apple Store"}
        )
    ]
    
    print(f"    📋 Configured Trigger Rules: {len(trigger_rules)}")
    
    for i, rule in enumerate(trigger_rules, 1):
        print(f"    {i}. {rule.trigger_type.value.upper()}")
        print(f"       Template: {rule.template_name}")
        print(f"       Priority: {rule.priority.value}")
        print(f"       Frequency: {rule.frequency.value}")
        print(f"       Recipients: {len(rule.recipients)}")
        if rule.status_conditions:
            print(f"       Status: {[s.value for s in rule.status_conditions]}")
        if rule.conditions:
            print(f"       Conditions: {rule.conditions}")
    
    # Test rule matching
    print(f"    🧪 Testing Rule Matching:")
    
    # Create test receipt
    test_receipt = create_test_receipt(
        vendor="Apple Store",
        amount=Decimal("1299.99"),
        status=ProcessingStatus.PROCESSED,
        confidence=0.95
    )
    
    matched_rules = [rule for rule in trigger_rules if rule.matches_conditions(test_receipt)]
    print(f"      Test Receipt: Apple Store - $1299.99 (Processed)")
    print(f"      Matched Rules: {len(matched_rules)}")
    for rule in matched_rules:
        print(f"        - {rule.trigger_type.value} ({rule.template_name})")


def demonstrate_batch_processing(temp_path):
    """Demonstrate email batch processing capabilities."""
    print("  📦 Email Batch Processing:")
    
    # Create batch manager
    workflow_config = EmailWorkflowConfig(batch_size=3, batch_timeout_minutes=60)
    batch_manager = EmailBatchManager(workflow_config)
    
    # Create sample events
    sample_events = []
    for i in range(5):
        receipt = create_test_receipt(
            vendor=f"Store {i+1}",
            amount=Decimal(f"{(i+1)*50}.00"),
            status=ProcessingStatus.PROCESSED
        )
        
        event = EmailWorkflowEvent(
            event_id=f"batch_event_{i+1}",
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            log_entry=receipt,
            recipients=[EmailRecipient(email="batch@yourcompany.com")],
            template_name="receipt_processed_batch",
            priority=EmailPriority.NORMAL
        )
        sample_events.append(event)
    
    # Add events to different batch frequencies
    frequencies = [
        NotificationFrequency.BATCHED_HOURLY,
        NotificationFrequency.BATCHED_DAILY,
        NotificationFrequency.WEEKLY_SUMMARY
    ]
    
    for i, event in enumerate(sample_events):
        frequency = frequencies[i % len(frequencies)]
        batch_manager.add_event(event, frequency)
        print(f"    📧 Added event {event.event_id} to {frequency.value} batch")
    
    # Check batch summary
    batch_summary = batch_manager.get_batch_summary()
    print(f"    📊 Batch Summary:")
    for frequency, count in batch_summary.items():
        if count > 0:
            print(f"      {frequency.replace('_', ' ').title()}: {count} pending events")
    
    # Simulate batch processing
    ready_batches = batch_manager.get_ready_batches()
    print(f"    🚀 Ready Batches: {len(ready_batches)}")
    for frequency, events in ready_batches.items():
        print(f"      {frequency.value}: {len(events)} events ready for sending")


def demonstrate_manual_operations(temp_path):
    """Demonstrate manual email operations."""
    print("  ✉️  Manual Email Operations:")
    
    # Set up email system
    email_config = EmailProviderConfig.create_gmail_config(
        username="receipts@yourcompany.com",
        auth_method=EmailAuthMethod.APP_PASSWORD,
        password="mock-password"
    )
    
    template_manager = EmailTemplateManager(template_dir=temp_path)
    email_sender = EmailSender(email_config, template_manager)
    
    storage_manager = JSONStorageManager(
        log_file_path=temp_path / "receipts.json",
        backup_dir=temp_path / "backups"
    )
    
    # Create workflow integrator
    integrator = EmailWorkflowIntegrator(email_sender, storage_manager)
    
    # Create test receipt
    test_receipt = create_test_receipt(
        vendor="Manual Test Store",
        amount=Decimal("199.99"),
        status=ProcessingStatus.PROCESSED
    )
    
    # Add to storage
    storage_manager.add_log_entry(test_receipt)
    
    print(f"    📧 Manual Email Sending:")
    print(f"      Receipt: {test_receipt.receipt_data.vendor_name}")
    print(f"      Amount: ${test_receipt.receipt_data.total_amount}")
    print(f"      Status: {test_receipt.current_status.value}")
    
    # Manual email parameters
    recipients = [
        EmailRecipient(email="manager@yourcompany.com", name="Manager"),
        EmailRecipient(email="finance@yourcompany.com", name="Finance Team")
    ]
    
    print(f"      Recipients: {len(recipients)}")
    for recipient in recipients:
        print(f"        - {recipient.format_address()}")
    
    print(f"      Template: receipt_processed")
    print(f"      Priority: normal")
    print(f"      ✅ Manual email would be sent successfully")
    
    # Demonstrate template customization
    print(f"    🎨 Custom Template Creation:")
    custom_template = """
    <h2>🎯 Custom Receipt Notification</h2>
    <p>Dear Team,</p>
    <p>A receipt from <strong>{{ vendor_name }}</strong> has been processed:</p>
    <div style="background: #f0f0f0; padding: 15px; margin: 10px 0;">
        <strong>Amount:</strong> ${{ total_amount }} {{ currency }}<br>
        <strong>Date:</strong> {{ transaction_date }}<br>
        <strong>Confidence:</strong> {{ confidence_score }}%
    </div>
    <p>This is a custom notification template.</p>
    """
    
    integrator.create_custom_template(
        template_name="custom_receipt_notification",
        html_content=custom_template,
        subject_template="Custom: {{ vendor_name }} - ${{ total_amount }}"
    )
    
    print(f"      ✅ Custom template 'custom_receipt_notification' created")


def demonstrate_bulk_operations(temp_path):
    """Demonstrate bulk email operations."""
    print("  📊 Bulk Email Operations:")
    
    # Create multiple test receipts
    test_receipts = []
    vendors = ["Amazon", "Office Depot", "Starbucks", "Apple Store", "Gas Station"]
    amounts = [Decimal("299.99"), Decimal("89.50"), Decimal("12.75"), Decimal("1299.00"), Decimal("45.20")]
    
    for i, (vendor, amount) in enumerate(zip(vendors, amounts)):
        receipt = create_test_receipt(
            vendor=vendor,
            amount=amount,
            status=ProcessingStatus.PROCESSED,
            date=datetime.now() - timedelta(days=i)
        )
        test_receipts.append(receipt)
    
    print(f"    📋 Bulk Operation Summary:")
    print(f"      Total Receipts: {len(test_receipts)}")
    
    total_amount = sum(r.receipt_data.total_amount for r in test_receipts)
    print(f"      Total Amount: ${total_amount}")
    
    print(f"      Receipt Breakdown:")
    for receipt in test_receipts:
        print(f"        - {receipt.receipt_data.vendor_name}: ${receipt.receipt_data.total_amount}")
    
    # Bulk email parameters
    recipients = [EmailRecipient(email="summary@yourcompany.com", name="Summary Team")]
    
    print(f"    📧 Bulk Email Configuration:")
    print(f"      Template: bulk_receipt_summary")
    print(f"      Recipients: {len(recipients)}")
    print(f"      Processing Period: {test_receipts[-1].created_at.strftime('%Y-%m-%d')} to {test_receipts[0].created_at.strftime('%Y-%m-%d')}")
    print(f"      ✅ Bulk email would be sent successfully")


def demonstrate_workflow_monitoring(temp_path):
    """Demonstrate workflow monitoring and statistics."""
    print("  📈 Workflow Monitoring & Statistics:")
    
    # Create workflow logger
    workflow_logger = EmailWorkflowLogger(log_file=temp_path / "workflow.log")
    
    # Simulate workflow events and deliveries
    events = []
    for i in range(10):
        receipt = create_test_receipt(
            vendor=f"Vendor {i+1}",
            amount=Decimal(f"{(i+1)*25}.00"),
            status=ProcessingStatus.PROCESSED
        )
        
        event = EmailWorkflowEvent(
            event_id=f"monitor_event_{i+1}",
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            log_entry=receipt,
            recipients=[EmailRecipient(email="monitor@yourcompany.com")],
            template_name="receipt_processed",
            priority=EmailPriority.NORMAL
        )
        events.append(event)
        
        # Log the trigger
        workflow_logger.log_trigger(event)
        
        # Simulate delivery results
        from src.receipt_processor.email_system import EmailStatus, EmailDeliveryResult
        
        if i < 7:  # 7 successful
            result = EmailDeliveryResult(
                message_id=f"msg_{i+1}",
                status=EmailStatus.SENT
            )
        elif i < 9:  # 2 failed
            result = EmailDeliveryResult(
                message_id=f"msg_{i+1}",
                status=EmailStatus.FAILED,
                error_message="SMTP connection timeout"
            )
        else:  # 1 bounced
            result = EmailDeliveryResult(
                message_id=f"msg_{i+1}",
                status=EmailStatus.BOUNCED,
                error_message="Recipient mailbox full"
            )
        
        workflow_logger.log_delivery(event, result)
    
    # Get delivery statistics
    stats = workflow_logger.get_delivery_stats()
    
    print(f"    📊 Delivery Statistics:")
    print(f"      Total Emails: {stats['total']}")
    print(f"      Successful: {stats['successful']}")
    print(f"      Failed: {stats['failed']}")
    print(f"      Success Rate: {stats['success_rate']:.1f}%")
    
    # Batch processing statistics
    workflow_config = EmailWorkflowConfig(batch_size=5)
    batch_manager = EmailBatchManager(workflow_config)
    
    print(f"    📦 Batch Processing Status:")
    batch_summary = batch_manager.get_batch_summary()
    for frequency, count in batch_summary.items():
        print(f"      {frequency.replace('_', ' ').title()}: {count} pending")
    
    # Workflow health metrics
    print(f"    🏥 Workflow Health:")
    print(f"      Delivery Success Rate: {stats['success_rate']:.1f}% {'✅' if stats['success_rate'] >= 90 else '⚠️' if stats['success_rate'] >= 80 else '❌'}")
    print(f"      Error Rate: {(100 - stats['success_rate']):.1f}%")
    print(f"      Pending Batches: {sum(batch_summary.values())}")
    print(f"      Log File Size: {(temp_path / 'workflow.log').stat().st_size if (temp_path / 'workflow.log').exists() else 0} bytes")


def demonstrate_cli_integration(temp_path):
    """Demonstrate CLI integration capabilities."""
    print("  💻 CLI Integration:")
    
    # Create batch templates
    template_count = BatchTemplateManager.create_batch_templates(temp_path / "templates")
    
    print(f"    📝 Template Management:")
    print(f"      Batch Templates Created: {template_count}")
    print(f"      Template Directory: {temp_path / 'templates'}")
    
    available_templates = BatchTemplateManager.get_template_list()
    print(f"      Available Templates:")
    for template in available_templates[:5]:  # Show first 5
        print(f"        - {template}")
    if len(available_templates) > 5:
        print(f"        ... and {len(available_templates) - 5} more")
    
    # CLI command examples
    print(f"    🔧 CLI Command Examples:")
    
    cli_commands = [
        {
            "command": "email test-email",
            "description": "Test email system connectivity",
            "example": "email test-email -t admin@yourcompany.com -c email_config.json"
        },
        {
            "command": "email send-manual-email",
            "description": "Send manual email for specific receipt",
            "example": "email send-manual-email -l receipt-uuid -r finance@company.com -t receipt_processed"
        },
        {
            "command": "email send-bulk-email",
            "description": "Send bulk email for multiple receipts",
            "example": "email send-bulk-email -r team@company.com -s processed -d 7"
        },
        {
            "command": "email workflow-stats",
            "description": "Display workflow statistics and metrics",
            "example": "email workflow-stats -c email_config.json -s receipts.json"
        },
        {
            "command": "email add-trigger-rule",
            "description": "Add new email trigger rule",
            "example": "email add-trigger-rule -t status_change -s processed -r finance@company.com --template receipt_processed"
        },
        {
            "command": "email create-batch-templates",
            "description": "Create batch email templates",
            "example": "email create-batch-templates -d ./email_templates"
        }
    ]
    
    for cmd in cli_commands:
        print(f"      📋 {cmd['command']}")
        print(f"         {cmd['description']}")
        print(f"         Example: {cmd['example']}")
    
    # Configuration file examples
    print(f"    📄 Configuration Files:")
    
    # Email configuration example
    email_config_example = {
        "provider": "gmail",
        "username": "receipts@yourcompany.com",
        "auth_method": "app_password",
        "password": "your-app-password",
        "from_name": "Receipt Processing System"
    }
    
    config_file = temp_path / "email_config.json"
    with open(config_file, 'w') as f:
        json.dump(email_config_example, f, indent=2)
    
    print(f"      ✅ Email config created: {config_file.name}")
    
    # Workflow configuration example
    workflow_config_example = {
        "enabled": True,
        "batch_size": 25,
        "batch_timeout_minutes": 30,
        "trigger_rules": [
            {
                "trigger_type": "status_change",
                "status_conditions": ["processed"],
                "template_name": "receipt_processed",
                "priority": "normal",
                "frequency": "immediate"
            }
        ]
    }
    
    workflow_file = temp_path / "workflow_config.json"
    with open(workflow_file, 'w') as f:
        json.dump(workflow_config_example, f, indent=2)
    
    print(f"      ✅ Workflow config created: {workflow_file.name}")
    
    print(f"    🚀 Production Deployment:")
    print(f"      1. Install CLI: pip install -e . (from project root)")
    print(f"      2. Configure email settings in production config")
    print(f"      3. Set up cron jobs for batch processing")
    print(f"      4. Configure monitoring and alerting")
    print(f"      5. Test all workflow scenarios")


def create_test_receipt(vendor: str, amount: Decimal, 
                       status: ProcessingStatus = ProcessingStatus.PROCESSED,
                       confidence: float = 0.9,
                       date: datetime = None) -> ReceiptProcessingLog:
    """Create a test receipt for demonstration purposes."""
    if date is None:
        date = datetime.now()
    
    receipt_data = ReceiptData(
        vendor_name=vendor,
        transaction_date=date,
        total_amount=amount,
        currency=Currency.USD,
        extraction_confidence=confidence,
        has_required_data=True
    )
    
    return ReceiptProcessingLog(
        original_filename=f"{vendor.lower().replace(' ', '_')}_receipt.jpg",
        file_path=Path(f"/receipts/{vendor.lower().replace(' ', '_')}_receipt.jpg"),
        file_size=1024,
        current_status=status,
        receipt_data=receipt_data,
        confidence_score=confidence,
        created_at=date
    )


if __name__ == "__main__":
    main()
