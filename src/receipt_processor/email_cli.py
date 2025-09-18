"""
CLI Commands for Email Workflow Management.

This module provides command-line interface for managing email workflows,
sending manual emails, and monitoring email delivery status.
"""

import click
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from decimal import Decimal
import sys

from .email_workflow import (
    EmailWorkflowIntegrator, EmailTriggerRule, EmailWorkflowConfig,
    EmailTriggerType, EmailPriority, NotificationFrequency
)
from .email_system import (
    EmailSender, EmailConfig, EmailRecipient, EmailProviderConfig,
    EmailAuthMethod, OAuth2Config
)
from .storage import JSONStorageManager
from .models import ProcessingStatus
from .templates.batch_templates import BatchTemplateManager


@click.group()
@click.pass_context
def email_cli(ctx):
    """Email workflow management commands."""
    ctx.ensure_object(dict)


@email_cli.command()
@click.option('--config-file', '-c', type=click.Path(exists=True), 
              help='Email configuration file path')
@click.option('--test-recipient', '-t', required=True,
              help='Email address to send test email to')
@click.pass_context
def test_email(ctx, config_file: str, test_recipient: str):
    """Test email system configuration and connectivity."""
    try:
        # Load email configuration
        email_config = _load_email_config(config_file)
        
        # Create email sender
        email_sender = EmailSender(email_config)
        
        # Test email system
        success, message = email_sender.test_email_system(test_recipient)
        
        if success:
            click.echo(click.style("✅ Email system test successful!", fg='green'))
            click.echo(f"Test email sent to: {test_recipient}")
            click.echo(f"Message: {message}")
        else:
            click.echo(click.style("❌ Email system test failed!", fg='red'))
            click.echo(f"Error: {message}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(click.style(f"❌ Error testing email system: {e}", fg='red'))
        sys.exit(1)


@email_cli.command()
@click.option('--log-id', '-l', required=True,
              help='Receipt log ID to send email for')
@click.option('--recipients', '-r', required=True,
              help='Comma-separated list of recipient email addresses')
@click.option('--template', '-t', default='receipt_processed',
              help='Email template to use')
@click.option('--priority', '-p', 
              type=click.Choice(['low', 'normal', 'high', 'urgent']),
              default='normal', help='Email priority level')
@click.option('--config-file', '-c', type=click.Path(exists=True),
              help='Email configuration file path')
@click.option('--storage-file', '-s', type=click.Path(exists=True),
              help='Receipt storage file path')
@click.pass_context
def send_manual_email(ctx, log_id: str, recipients: str, template: str, 
                     priority: str, config_file: str, storage_file: str):
    """Send manual email for a specific receipt."""
    try:
        # Parse recipients
        recipient_emails = [email.strip() for email in recipients.split(',')]
        recipient_list = [EmailRecipient(email=email) for email in recipient_emails]
        
        # Load configurations
        email_config = _load_email_config(config_file)
        storage_manager = _load_storage_manager(storage_file)
        
        # Create workflow integrator
        email_sender = EmailSender(email_config)
        integrator = EmailWorkflowIntegrator(email_sender, storage_manager)
        
        # Get receipt log
        try:
            from uuid import UUID
            log_uuid = UUID(log_id)
            log_entry = storage_manager.get_log_entry(log_uuid)
        except ValueError:
            click.echo(click.style(f"❌ Invalid log ID format: {log_id}", fg='red'))
            sys.exit(1)
        
        if not log_entry:
            click.echo(click.style(f"❌ Receipt not found: {log_id}", fg='red'))
            sys.exit(1)
        
        # Send manual email
        email_priority = EmailPriority(priority)
        result = integrator.send_manual_email(
            log_entry=log_entry,
            recipients=recipient_list,
            template_name=template,
            priority=email_priority
        )
        
        if result and result.status.value in ['sent', 'delivered']:
            click.echo(click.style("✅ Manual email sent successfully!", fg='green'))
            click.echo(f"Recipients: {', '.join(recipient_emails)}")
            click.echo(f"Template: {template}")
            click.echo(f"Message ID: {result.message_id}")
            click.echo(f"Status: {result.status.value}")
        else:
            click.echo(click.style("❌ Failed to send manual email!", fg='red'))
            if result and result.error_message:
                click.echo(f"Error: {result.error_message}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(click.style(f"❌ Error sending manual email: {e}", fg='red'))
        sys.exit(1)


@email_cli.command()
@click.option('--recipients', '-r', required=True,
              help='Comma-separated list of recipient email addresses')
@click.option('--template', '-t', default='bulk_receipt_summary',
              help='Email template to use for bulk summary')
@click.option('--status', '-s', 
              type=click.Choice(['pending', 'processing', 'processed', 'error', 'retry']),
              help='Filter receipts by status')
@click.option('--days', '-d', type=int, default=1,
              help='Number of days to include in bulk email')
@click.option('--config-file', '-c', type=click.Path(exists=True),
              help='Email configuration file path')
@click.option('--storage-file', type=click.Path(exists=True),
              help='Receipt storage file path')
@click.pass_context
def send_bulk_email(ctx, recipients: str, template: str, status: str, 
                   days: int, config_file: str, storage_file: str):
    """Send bulk email for multiple receipts."""
    try:
        # Parse recipients
        recipient_emails = [email.strip() for email in recipients.split(',')]
        recipient_list = [EmailRecipient(email=email) for email in recipient_emails]
        
        # Load configurations
        email_config = _load_email_config(config_file)
        storage_manager = _load_storage_manager(storage_file)
        
        # Create workflow integrator
        email_sender = EmailSender(email_config)
        integrator = EmailWorkflowIntegrator(email_sender, storage_manager)
        
        # Get recent receipts
        cutoff_date = datetime.now() - timedelta(days=days)
        all_logs = storage_manager.get_recent_logs(limit=1000)
        
        # Filter by date and status
        filtered_logs = [
            log for log in all_logs 
            if log.created_at >= cutoff_date and
            (not status or log.current_status == ProcessingStatus(status.upper()))
        ]
        
        if not filtered_logs:
            click.echo(click.style("⚠️  No receipts found matching criteria", fg='yellow'))
            return
        
        # Send bulk email
        results = integrator.send_bulk_emails(
            log_entries=filtered_logs,
            recipients=recipient_list,
            template_name=template
        )
        
        if results and results[0].status.value in ['sent', 'delivered']:
            click.echo(click.style("✅ Bulk email sent successfully!", fg='green'))
            click.echo(f"Recipients: {', '.join(recipient_emails)}")
            click.echo(f"Receipts included: {len(filtered_logs)}")
            click.echo(f"Template: {template}")
            click.echo(f"Message ID: {results[0].message_id}")
        else:
            click.echo(click.style("❌ Failed to send bulk email!", fg='red'))
            if results and results[0].error_message:
                click.echo(f"Error: {results[0].error_message}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(click.style(f"❌ Error sending bulk email: {e}", fg='red'))
        sys.exit(1)


@email_cli.command()
@click.option('--config-file', '-c', type=click.Path(exists=True),
              help='Email configuration file path')
@click.option('--storage-file', '-s', type=click.Path(exists=True),
              help='Receipt storage file path')
@click.pass_context
def workflow_stats(ctx, config_file: str, storage_file: str):
    """Display email workflow statistics and metrics."""
    try:
        # Load configurations
        email_config = _load_email_config(config_file)
        storage_manager = _load_storage_manager(storage_file)
        
        # Create workflow integrator
        email_sender = EmailSender(email_config)
        integrator = EmailWorkflowIntegrator(email_sender, storage_manager)
        
        # Get workflow statistics
        stats = integrator.get_workflow_statistics()
        
        # Display statistics
        click.echo(click.style("📊 Email Workflow Statistics", fg='cyan', bold=True))
        click.echo("=" * 40)
        
        # Workflow configuration
        click.echo(f"Workflow Enabled: {'✅' if stats['enabled'] else '❌'}")
        click.echo(f"Trigger Rules: {stats['trigger_rules']}")
        click.echo(f"Pending Events: {stats['pending_events']}")
        
        # Delivery statistics
        delivery_stats = stats['delivery_stats']
        click.echo(f"\n📧 Delivery Statistics:")
        click.echo(f"  Total Emails: {delivery_stats['total']}")
        if delivery_stats['total'] > 0:
            click.echo(f"  Successful: {delivery_stats['successful']}")
            click.echo(f"  Failed: {delivery_stats['failed']}")
            click.echo(f"  Success Rate: {delivery_stats['success_rate']:.1f}%")
        
        # Batch summary
        batch_summary = stats['batch_summary']
        click.echo(f"\n📦 Batch Summary:")
        for frequency, count in batch_summary.items():
            if count > 0:
                click.echo(f"  {frequency.replace('_', ' ').title()}: {count} pending")
        
        # Recent activity (if available)
        recent_logs = storage_manager.get_recent_logs(limit=5)
        if recent_logs:
            click.echo(f"\n📋 Recent Activity:")
            for log in recent_logs:
                status_icon = {
                    ProcessingStatus.PROCESSED: "✅",
                    ProcessingStatus.ERROR: "❌",
                    ProcessingStatus.PENDING: "⏳",
                    ProcessingStatus.PROCESSING: "🔄"
                }.get(log.current_status, "📄")
                
                vendor = log.receipt_data.vendor_name if log.receipt_data else "Unknown"
                click.echo(f"  {status_icon} {vendor} - {log.created_at.strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Error getting workflow statistics: {e}", fg='red'))
        sys.exit(1)


@email_cli.command()
@click.option('--template-dir', '-d', type=click.Path(),
              help='Directory to create templates in')
@click.pass_context
def create_batch_templates(ctx, template_dir: str):
    """Create batch email templates for workflow notifications."""
    try:
        if not template_dir:
            template_dir = Path.cwd() / "email_templates"
        else:
            template_dir = Path(template_dir)
        
        # Create batch templates
        template_count = BatchTemplateManager.create_batch_templates(template_dir)
        
        click.echo(click.style("✅ Batch templates created successfully!", fg='green'))
        click.echo(f"Templates directory: {template_dir}")
        click.echo(f"Templates created: {template_count}")
        
        # List created templates
        click.echo(f"\n📝 Available Templates:")
        for template_name in BatchTemplateManager.get_template_list():
            click.echo(f"  - {template_name}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Error creating batch templates: {e}", fg='red'))
        sys.exit(1)


@email_cli.command()
@click.option('--trigger-type', '-t', required=True,
              type=click.Choice(['status_change', 'processing_complete', 'error_occurred', 
                               'manual_send', 'scheduled_report', 'bulk_operation', 'workflow_milestone']),
              help='Type of email trigger')
@click.option('--status', '-s', multiple=True,
              type=click.Choice(['pending', 'processing', 'processed', 'error', 'retry']),
              help='Status conditions for trigger (can specify multiple)')
@click.option('--recipients', '-r', required=True,
              help='Comma-separated list of recipient email addresses')
@click.option('--template', required=True,
              help='Email template name to use')
@click.option('--priority', '-p',
              type=click.Choice(['low', 'normal', 'high', 'urgent']),
              default='normal', help='Email priority level')
@click.option('--frequency', '-f',
              type=click.Choice(['immediate', 'batched_hourly', 'batched_daily', 
                               'weekly_summary', 'monthly_summary', 'disabled']),
              default='immediate', help='Notification frequency')
@click.option('--min-confidence', type=float,
              help='Minimum confidence score condition')
@click.option('--min-amount', type=float,
              help='Minimum amount condition')
@click.option('--vendor', help='Specific vendor name condition')
@click.option('--config-file', '-c', type=click.Path(),
              help='Workflow configuration file to update')
@click.pass_context
def add_trigger_rule(ctx, trigger_type: str, status: tuple, recipients: str, 
                    template: str, priority: str, frequency: str,
                    min_confidence: float, min_amount: float, vendor: str,
                    config_file: str):
    """Add a new email trigger rule to workflow configuration."""
    try:
        # Parse recipients
        recipient_emails = [email.strip() for email in recipients.split(',')]
        recipient_list = [EmailRecipient(email=email) for email in recipient_emails]
        
        # Parse status conditions
        status_conditions = [ProcessingStatus(s.upper()) for s in status] if status else []
        
        # Build conditions dictionary
        conditions = {}
        if min_confidence:
            conditions['min_confidence'] = min_confidence
        if min_amount:
            conditions['min_amount'] = Decimal(str(min_amount))
        if vendor:
            conditions['vendor_name'] = vendor
        
        # Create trigger rule
        trigger_rule = EmailTriggerRule(
            trigger_type=EmailTriggerType(trigger_type),
            status_conditions=status_conditions,
            recipients=recipient_list,
            template_name=template,
            priority=EmailPriority(priority),
            frequency=NotificationFrequency(frequency),
            conditions=conditions
        )
        
        # Save to configuration file
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = {"trigger_rules": []}
            
            # Convert trigger rule to dict for JSON serialization
            rule_dict = {
                "trigger_type": trigger_rule.trigger_type.value,
                "status_conditions": [s.value for s in trigger_rule.status_conditions],
                "recipients": [{"email": r.email, "name": r.name} for r in trigger_rule.recipients],
                "template_name": trigger_rule.template_name,
                "priority": trigger_rule.priority.value,
                "frequency": trigger_rule.frequency.value,
                "conditions": {k: str(v) for k, v in trigger_rule.conditions.items()},
                "enabled": trigger_rule.enabled
            }
            
            if "trigger_rules" not in config_data:
                config_data["trigger_rules"] = []
            config_data["trigger_rules"].append(rule_dict)
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            click.echo(click.style("✅ Trigger rule added to configuration file!", fg='green'))
        
        # Display rule summary
        click.echo(click.style("📧 Email Trigger Rule Created", fg='cyan', bold=True))
        click.echo(f"Trigger Type: {trigger_rule.trigger_type.value}")
        click.echo(f"Status Conditions: {[s.value for s in trigger_rule.status_conditions]}")
        click.echo(f"Recipients: {', '.join([r.email for r in trigger_rule.recipients])}")
        click.echo(f"Template: {trigger_rule.template_name}")
        click.echo(f"Priority: {trigger_rule.priority.value}")
        click.echo(f"Frequency: {trigger_rule.frequency.value}")
        if trigger_rule.conditions:
            click.echo(f"Conditions: {trigger_rule.conditions}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Error adding trigger rule: {e}", fg='red'))
        sys.exit(1)


@email_cli.command()
@click.option('--config-file', '-c', type=click.Path(exists=True),
              help='Workflow configuration file path')
@click.pass_context
def list_trigger_rules(ctx, config_file: str):
    """List all configured email trigger rules."""
    try:
        if not config_file or not Path(config_file).exists():
            click.echo(click.style("⚠️  No configuration file found", fg='yellow'))
            return
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        trigger_rules = config_data.get("trigger_rules", [])
        
        if not trigger_rules:
            click.echo(click.style("⚠️  No trigger rules configured", fg='yellow'))
            return
        
        click.echo(click.style("📧 Email Trigger Rules", fg='cyan', bold=True))
        click.echo("=" * 50)
        
        for i, rule in enumerate(trigger_rules, 1):
            enabled_icon = "✅" if rule.get("enabled", True) else "❌"
            click.echo(f"\n{i}. {enabled_icon} {rule['trigger_type'].upper()}")
            click.echo(f"   Template: {rule['template_name']}")
            click.echo(f"   Priority: {rule['priority']}")
            click.echo(f"   Frequency: {rule['frequency']}")
            click.echo(f"   Recipients: {len(rule.get('recipients', []))} recipient(s)")
            
            if rule.get('status_conditions'):
                click.echo(f"   Status Conditions: {', '.join(rule['status_conditions'])}")
            
            if rule.get('conditions'):
                conditions_str = ', '.join([f"{k}={v}" for k, v in rule['conditions'].items()])
                click.echo(f"   Custom Conditions: {conditions_str}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Error listing trigger rules: {e}", fg='red'))
        sys.exit(1)


def _load_email_config(config_file: Optional[str]) -> EmailConfig:
    """Load email configuration from file or use defaults."""
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Create email configuration from JSON data
        # This is a simplified version - in practice you'd have more robust config loading
        return EmailProviderConfig.create_gmail_config(
            username=config_data.get('username', 'test@gmail.com'),
            auth_method=EmailAuthMethod(config_data.get('auth_method', 'app_password')),
            password=config_data.get('password', 'test-password')
        )
    else:
        # Return default configuration for testing
        return EmailProviderConfig.create_gmail_config(
            username='test@gmail.com',
            auth_method=EmailAuthMethod.APP_PASSWORD,
            password='test-password'
        )


def _load_storage_manager(storage_file: Optional[str]) -> JSONStorageManager:
    """Load storage manager with specified or default file."""
    if storage_file:
        storage_path = Path(storage_file)
    else:
        storage_path = Path("receipt_processing_log.json")
    
    backup_dir = storage_path.parent / "backups"
    return JSONStorageManager(
        log_file_path=storage_path,
        backup_dir=backup_dir
    )


if __name__ == '__main__':
    email_cli()
