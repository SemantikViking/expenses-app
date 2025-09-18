"""
Tests for Email Workflow Integration System.

This module tests email workflow triggers, batch processing, delivery tracking,
and integration with the receipt processing system.
"""

import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import pytest
import threading
import time

from src.receipt_processor.email_workflow import (
    EmailTriggerType, EmailPriority, NotificationFrequency,
    EmailTriggerRule, EmailWorkflowConfig, EmailWorkflowEvent,
    EmailBatchManager, EmailWorkflowLogger, EmailWorkflowIntegrator
)
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)
from src.receipt_processor.email_system import (
    EmailSender, EmailConfig, EmailRecipient, EmailStatus, EmailDeliveryResult,
    EmailTemplateManager, EmailProviderConfig, EmailAuthMethod
)
from src.receipt_processor.storage import JSONStorageManager


class TestEmailTriggerRule:
    """Test cases for email trigger rules."""
    
    @pytest.fixture
    def sample_receipt_log(self):
        """Create a sample receipt log for testing."""
        receipt_data = ReceiptData(
            vendor_name="Apple Store",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("299.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        return ReceiptProcessingLog(
            original_filename="receipt.jpg",
            file_path=Path("/test/receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data,
            confidence_score=0.9
        )
    
    def test_trigger_rule_creation(self):
        """Test creating email trigger rule."""
        recipients = [EmailRecipient(email="test@example.com")]
        
        rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            status_conditions=[ProcessingStatus.PROCESSED],
            recipients=recipients,
            template_name="receipt_processed",
            priority=EmailPriority.NORMAL
        )
        
        assert rule.trigger_type == EmailTriggerType.STATUS_CHANGE
        assert ProcessingStatus.PROCESSED in rule.status_conditions
        assert len(rule.recipients) == 1
        assert rule.template_name == "receipt_processed"
        assert rule.enabled
    
    def test_trigger_rule_matches_status(self, sample_receipt_log):
        """Test trigger rule status matching."""
        rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            status_conditions=[ProcessingStatus.PROCESSED],
            recipients=[EmailRecipient(email="test@example.com")],
            template_name="receipt_processed"
        )
        
        assert rule.matches_conditions(sample_receipt_log)
        
        # Change status to non-matching
        sample_receipt_log.current_status = ProcessingStatus.ERROR
        assert not rule.matches_conditions(sample_receipt_log)
    
    def test_trigger_rule_custom_conditions(self, sample_receipt_log):
        """Test trigger rule with custom conditions."""
        # Rule with minimum confidence condition
        rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.PROCESSING_COMPLETE,
            recipients=[EmailRecipient(email="test@example.com")],
            template_name="high_confidence_receipt",
            conditions={"min_confidence": 0.85}  # Lower than sample's 0.9
        )
        
        assert rule.matches_conditions(sample_receipt_log)
        
        # Higher confidence requirement should not match
        rule.conditions["min_confidence"] = 0.95
        assert not rule.matches_conditions(sample_receipt_log)
        
        # Rule with minimum amount condition
        rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.PROCESSING_COMPLETE,
            recipients=[EmailRecipient(email="test@example.com")],
            template_name="high_value_receipt",
            conditions={"min_amount": Decimal("200.00")}
        )
        assert rule.matches_conditions(sample_receipt_log)
        
        # Lower amount should not match
        sample_receipt_log.receipt_data.total_amount = Decimal("50.00")
        assert not rule.matches_conditions(sample_receipt_log)
    
    def test_trigger_rule_disabled(self, sample_receipt_log):
        """Test disabled trigger rule."""
        rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            status_conditions=[ProcessingStatus.PROCESSED],
            recipients=[EmailRecipient(email="test@example.com")],
            template_name="receipt_processed",
            enabled=False
        )
        
        assert not rule.matches_conditions(sample_receipt_log)


class TestEmailBatchManager:
    """Test cases for email batch management."""
    
    @pytest.fixture
    def batch_config(self):
        """Create batch configuration for testing."""
        return EmailWorkflowConfig(
            batch_size=3,
            batch_timeout_minutes=60
        )
    
    @pytest.fixture
    def batch_manager(self, batch_config):
        """Create batch manager for testing."""
        return EmailBatchManager(batch_config)
    
    @pytest.fixture
    def sample_event(self):
        """Create sample workflow event."""
        receipt_data = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime.now(),
            total_amount=Decimal("50.00"),
            currency=Currency.USD,
            extraction_confidence=0.9,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="test.jpg",
            file_path=Path("/test/test.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data
        )
        
        return EmailWorkflowEvent(
            event_id="test_event_1",
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            log_entry=log_entry,
            recipients=[EmailRecipient(email="test@example.com")],
            template_name="receipt_processed",
            priority=EmailPriority.NORMAL
        )
    
    def test_batch_manager_creation(self, batch_manager):
        """Test creating batch manager."""
        assert len(batch_manager.pending_events) == len(NotificationFrequency)
        assert batch_manager.config.batch_size == 3
    
    def test_add_immediate_event(self, batch_manager, sample_event):
        """Test that immediate events are not batched."""
        added = batch_manager.add_event(sample_event, NotificationFrequency.IMMEDIATE)
        assert not added  # Immediate events should not be batched
    
    def test_add_batched_event(self, batch_manager, sample_event):
        """Test adding events to batch."""
        added = batch_manager.add_event(sample_event, NotificationFrequency.BATCHED_HOURLY)
        assert added
        
        summary = batch_manager.get_batch_summary()
        assert summary[NotificationFrequency.BATCHED_HOURLY.value] == 1
    
    def test_batch_size_trigger(self, batch_manager, sample_event):
        """Test that batch is ready when size limit is reached."""
        frequency = NotificationFrequency.BATCHED_HOURLY
        
        # Add events up to batch size
        for i in range(batch_manager.config.batch_size):
            event = EmailWorkflowEvent(
                event_id=f"test_event_{i}",
                trigger_type=EmailTriggerType.STATUS_CHANGE,
                log_entry=sample_event.log_entry,
                recipients=sample_event.recipients,
                template_name="receipt_processed",
                priority=EmailPriority.NORMAL
            )
            batch_manager.add_event(event, frequency)
        
        # Should be ready due to size
        ready_batches = batch_manager.get_ready_batches()
        assert frequency in ready_batches
        assert len(ready_batches[frequency]) == batch_manager.config.batch_size
    
    def test_batch_summary(self, batch_manager, sample_event):
        """Test batch summary functionality."""
        batch_manager.add_event(sample_event, NotificationFrequency.BATCHED_HOURLY)
        batch_manager.add_event(sample_event, NotificationFrequency.BATCHED_DAILY)
        
        summary = batch_manager.get_batch_summary()
        assert summary[NotificationFrequency.BATCHED_HOURLY.value] == 1
        assert summary[NotificationFrequency.BATCHED_DAILY.value] == 1
        assert summary[NotificationFrequency.IMMEDIATE.value] == 0


class TestEmailWorkflowLogger:
    """Test cases for email workflow logging."""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.log', delete=False)
        temp_file.close()
        yield Path(temp_file.name)
        Path(temp_file.name).unlink()
    
    @pytest.fixture
    def workflow_logger(self, temp_log_file):
        """Create workflow logger for testing."""
        return EmailWorkflowLogger(log_file=temp_log_file)
    
    @pytest.fixture
    def sample_event(self):
        """Create sample workflow event."""
        receipt_data = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime.now(),
            total_amount=Decimal("50.00"),
            currency=Currency.USD,
            extraction_confidence=0.9,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="test.jpg",
            file_path=Path("/test/test.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data
        )
        
        return EmailWorkflowEvent(
            event_id="test_event_1",
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            log_entry=log_entry,
            recipients=[EmailRecipient(email="test@example.com")],
            template_name="receipt_processed",
            priority=EmailPriority.NORMAL
        )
    
    def test_workflow_logger_creation(self, workflow_logger, temp_log_file):
        """Test creating workflow logger."""
        assert workflow_logger.log_file == temp_log_file
        assert len(workflow_logger.delivery_confirmations) == 0
    
    def test_log_trigger(self, workflow_logger, sample_event, temp_log_file):
        """Test logging trigger events."""
        workflow_logger.log_trigger(sample_event)
        
        # Check that log file was written
        assert temp_log_file.exists()
        log_content = temp_log_file.read_text()
        assert "Email triggered" in log_content
        assert sample_event.event_id in log_content
    
    def test_log_delivery(self, workflow_logger, sample_event):
        """Test logging delivery results."""
        delivery_result = EmailDeliveryResult(
            message_id="test_message_123",
            status=EmailStatus.SENT
        )
        
        workflow_logger.log_delivery(sample_event, delivery_result)
        
        assert sample_event.event_id in workflow_logger.delivery_confirmations
        assert workflow_logger.delivery_confirmations[sample_event.event_id] == delivery_result
    
    def test_delivery_statistics(self, workflow_logger, sample_event):
        """Test delivery statistics calculation."""
        # Add successful delivery
        success_result = EmailDeliveryResult(
            message_id="success_123",
            status=EmailStatus.SENT
        )
        workflow_logger.log_delivery(sample_event, success_result)
        
        # Add failed delivery
        failed_event = EmailWorkflowEvent(
            event_id="failed_event",
            trigger_type=EmailTriggerType.STATUS_CHANGE,
            log_entry=sample_event.log_entry,
            recipients=sample_event.recipients,
            template_name="receipt_processed",
            priority=EmailPriority.NORMAL
        )
        
        failed_result = EmailDeliveryResult(
            message_id="failed_123",
            status=EmailStatus.FAILED,
            error_message="SMTP error"
        )
        workflow_logger.log_delivery(failed_event, failed_result)
        
        # Check statistics
        stats = workflow_logger.get_delivery_stats()
        assert stats["total"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["success_rate"] == 50.0


class TestEmailWorkflowIntegrator:
    """Test cases for email workflow integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration for testing."""
        return EmailProviderConfig.create_gmail_config(
            username="test@gmail.com",
            auth_method=EmailAuthMethod.APP_PASSWORD,
            password="test-password"
        )
    
    @pytest.fixture
    def email_sender(self, email_config, temp_dir):
        """Create email sender for testing."""
        template_manager = EmailTemplateManager(template_dir=temp_dir)
        return EmailSender(email_config, template_manager)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create storage manager for testing."""
        return JSONStorageManager(
            log_file_path=temp_dir / "test_logs.json",
            backup_dir=temp_dir / "backups"
        )
    
    @pytest.fixture
    def workflow_config(self):
        """Create workflow configuration for testing."""
        return EmailWorkflowConfig(
            enabled=True,
            default_recipients=[EmailRecipient(email="default@example.com")],
            batch_size=2,
            batch_timeout_minutes=1
        )
    
    @pytest.fixture
    def workflow_integrator(self, email_sender, storage_manager, workflow_config):
        """Create workflow integrator for testing."""
        return EmailWorkflowIntegrator(
            email_sender=email_sender,
            storage_manager=storage_manager,
            config=workflow_config
        )
    
    @pytest.fixture
    def sample_receipt_log(self):
        """Create sample receipt log for testing."""
        receipt_data = ReceiptData(
            vendor_name="Apple Store",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("299.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        return ReceiptProcessingLog(
            original_filename="receipt.jpg",
            file_path=Path("/test/receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data,
            confidence_score=0.9
        )
    
    def test_workflow_integrator_creation(self, workflow_integrator, workflow_config):
        """Test creating workflow integrator."""
        assert workflow_integrator.config == workflow_config
        assert len(workflow_integrator.config.trigger_rules) > 0  # Default rules added
        assert workflow_integrator.batch_manager is not None
        assert workflow_integrator.workflow_logger is not None
    
    def test_default_trigger_rules(self, workflow_integrator):
        """Test that default trigger rules are created."""
        rules = workflow_integrator.config.trigger_rules
        
        # Should have default rules for success, error, high-value, and summary
        trigger_types = [rule.trigger_type for rule in rules]
        assert EmailTriggerType.STATUS_CHANGE in trigger_types
        assert EmailTriggerType.ERROR_OCCURRED in trigger_types
        assert EmailTriggerType.PROCESSING_COMPLETE in trigger_types
        assert EmailTriggerType.SCHEDULED_REPORT in trigger_types
    
    def test_add_trigger_rule(self, workflow_integrator):
        """Test adding custom trigger rule."""
        initial_count = len(workflow_integrator.config.trigger_rules)
        
        custom_rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.MANUAL_SEND,
            recipients=[EmailRecipient(email="custom@example.com")],
            template_name="custom_template",
            priority=EmailPriority.HIGH
        )
        
        workflow_integrator.add_trigger_rule(custom_rule)
        
        assert len(workflow_integrator.config.trigger_rules) == initial_count + 1
        assert custom_rule in workflow_integrator.config.trigger_rules
    
    def test_remove_trigger_rule(self, workflow_integrator):
        """Test removing trigger rules."""
        initial_count = len(workflow_integrator.config.trigger_rules)
        
        # Remove error trigger rules
        workflow_integrator.remove_trigger_rule(EmailTriggerType.ERROR_OCCURRED)
        
        # Should have fewer rules now
        assert len(workflow_integrator.config.trigger_rules) < initial_count
        
        # Should not have any error trigger rules
        remaining_types = [rule.trigger_type for rule in workflow_integrator.config.trigger_rules]
        assert EmailTriggerType.ERROR_OCCURRED not in remaining_types
    
    @patch('src.receipt_processor.email_workflow.EmailWorkflowIntegrator._process_immediate_event')
    def test_trigger_email_for_receipt(self, mock_process, workflow_integrator, sample_receipt_log):
        """Test triggering emails for a receipt."""
        events = workflow_integrator.trigger_email_for_receipt(
            sample_receipt_log,
            EmailTriggerType.STATUS_CHANGE
        )
        
        # Should have triggered events based on default rules
        assert len(events) > 0
        
        # Should have called process for immediate events
        assert mock_process.called
    
    @patch.object(EmailSender, 'send_template_email')
    def test_manual_email_sending(self, mock_send, workflow_integrator, sample_receipt_log):
        """Test sending manual emails."""
        # Mock successful email sending
        mock_result = EmailDeliveryResult(
            message_id="manual_123",
            status=EmailStatus.SENT
        )
        mock_send.return_value = mock_result
        
        recipients = [EmailRecipient(email="manual@example.com")]
        result = workflow_integrator.send_manual_email(
            log_entry=sample_receipt_log,
            recipients=recipients,
            template_name="receipt_processed"
        )
        
        assert mock_send.called
        assert result == mock_result
    
    @patch.object(EmailSender, 'send_template_email')
    def test_bulk_email_sending(self, mock_send, workflow_integrator, sample_receipt_log):
        """Test sending bulk emails."""
        # Mock successful email sending
        mock_result = EmailDeliveryResult(
            message_id="bulk_123",
            status=EmailStatus.SENT
        )
        mock_send.return_value = mock_result
        
        # Create multiple receipt logs
        log_entries = [sample_receipt_log]
        recipients = [EmailRecipient(email="bulk@example.com")]
        
        results = workflow_integrator.send_bulk_emails(
            log_entries=log_entries,
            recipients=recipients
        )
        
        assert len(results) == 1
        assert results[0].status == EmailStatus.SENT
        assert mock_send.called
    
    def test_workflow_statistics(self, workflow_integrator):
        """Test getting workflow statistics."""
        stats = workflow_integrator.get_workflow_statistics()
        
        assert "delivery_stats" in stats
        assert "batch_summary" in stats
        assert "trigger_rules" in stats
        assert "enabled" in stats
        assert "pending_events" in stats
        
        assert stats["enabled"] == True
        assert stats["trigger_rules"] > 0  # Should have default rules
    
    def test_custom_template_creation(self, workflow_integrator, temp_dir):
        """Test creating custom email templates."""
        template_name = "custom_notification"
        html_content = "<h1>Custom Template</h1><p>{{ vendor_name }}</p>"
        subject_template = "Custom: {{ vendor_name }}"
        text_content = "Custom Template\n{{ vendor_name }}"
        
        workflow_integrator.create_custom_template(
            template_name=template_name,
            html_content=html_content,
            subject_template=subject_template,
            text_content=text_content
        )
        
        # Check that files were created
        template_dir = workflow_integrator.email_sender.template_manager.template_dir
        assert (template_dir / f"{template_name}.html").exists()
        assert (template_dir / f"{template_name}_subject.txt").exists()
        assert (template_dir / f"{template_name}.txt").exists()
    
    @patch.object(EmailSender, 'send_template_email')
    def test_workflow_integration_test(self, mock_send, workflow_integrator):
        """Test the workflow integration testing functionality."""
        # Mock successful email sending
        mock_result = EmailDeliveryResult(
            message_id="test_123",
            status=EmailStatus.SENT
        )
        mock_send.return_value = mock_result
        
        test_result = workflow_integrator.test_workflow_integration("test@example.com")
        
        assert test_result["success"] == True
        assert test_result["message_id"] == "test_123"
        assert test_result["status"] == "sent"
        assert "workflow_stats" in test_result
        assert mock_send.called


class TestWorkflowProcessing:
    """Test cases for workflow processing and batch operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def workflow_integrator(self, temp_dir):
        """Create workflow integrator for batch testing."""
        email_config = EmailProviderConfig.create_gmail_config(
            username="test@gmail.com",
            auth_method=EmailAuthMethod.APP_PASSWORD,
            password="test-password"
        )
        
        template_manager = EmailTemplateManager(template_dir=temp_dir)
        email_sender = EmailSender(email_config, template_manager)
        storage_manager = JSONStorageManager(
            log_file_path=temp_dir / "test_logs.json",
            backup_dir=temp_dir / "backups"
        )
        
        config = EmailWorkflowConfig(
            enabled=True,
            default_recipients=[EmailRecipient(email="test@example.com")],
            batch_size=2,
            batch_timeout_minutes=1
        )
        
        return EmailWorkflowIntegrator(
            email_sender=email_sender,
            storage_manager=storage_manager,
            config=config
        )
    
    def test_batch_processing(self, workflow_integrator):
        """Test batch processing of email events."""
        # Create sample events
        receipt_data = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime.now(),
            total_amount=Decimal("50.00"),
            currency=Currency.USD,
            extraction_confidence=0.9,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="test.jpg",
            file_path=Path("/test/test.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data
        )
        
        # Add events to batch
        for i in range(3):  # More than batch size
            event = EmailWorkflowEvent(
                event_id=f"batch_event_{i}",
                trigger_type=EmailTriggerType.STATUS_CHANGE,
                log_entry=log_entry,
                recipients=[EmailRecipient(email="batch@example.com")],
                template_name="receipt_processed",
                priority=EmailPriority.NORMAL
            )
            workflow_integrator.batch_manager.add_event(event, NotificationFrequency.BATCHED_HOURLY)
        
        # Check that batch is ready
        ready_batches = workflow_integrator.batch_manager.get_ready_batches()
        assert NotificationFrequency.BATCHED_HOURLY in ready_batches
        assert len(ready_batches[NotificationFrequency.BATCHED_HOURLY]) >= workflow_integrator.config.batch_size
    
    def test_workflow_processor_lifecycle(self, workflow_integrator):
        """Test starting and stopping the workflow processor."""
        # Initially not running
        assert not workflow_integrator._running
        
        # Start processor
        workflow_integrator.start_workflow_processor()
        assert workflow_integrator._running
        
        # Stop processor
        workflow_integrator.stop_workflow_processor()
        assert not workflow_integrator._running


class TestIntegration:
    """Integration tests for email workflow system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_complete_workflow_integration(self, temp_dir):
        """Test complete email workflow integration."""
        # Create email system components
        email_config = EmailProviderConfig.create_gmail_config(
            username="receipts@company.com",
            auth_method=EmailAuthMethod.APP_PASSWORD,
            password="test-app-password"
        )
        
        template_manager = EmailTemplateManager(template_dir=temp_dir)
        email_sender = EmailSender(email_config, template_manager)
        storage_manager = JSONStorageManager(
            log_file_path=temp_dir / "test_logs.json",
            backup_dir=temp_dir / "backups"
        )
        
        # Create workflow configuration
        workflow_config = EmailWorkflowConfig(
            enabled=True,
            default_recipients=[
                EmailRecipient(email="finance@company.com", name="Finance Team"),
                EmailRecipient(email="manager@company.com", name="Manager")
            ],
            batch_size=5,
            batch_timeout_minutes=30
        )
        
        # Create workflow integrator
        integrator = EmailWorkflowIntegrator(
            email_sender=email_sender,
            storage_manager=storage_manager,
            config=workflow_config
        )
        
        # Test configuration
        assert integrator.config.enabled
        assert len(integrator.config.default_recipients) == 2
        assert len(integrator.config.trigger_rules) > 0  # Default rules
        
        # Test custom trigger rule
        custom_rule = EmailTriggerRule(
            trigger_type=EmailTriggerType.WORKFLOW_MILESTONE,
            recipients=[EmailRecipient(email="audit@company.com")],
            template_name="audit_notification",
            priority=EmailPriority.HIGH,
            conditions={"min_amount": Decimal("1000.00")}
        )
        integrator.add_trigger_rule(custom_rule)
        
        # Create test receipt
        receipt_data = ReceiptData(
            vendor_name="Enterprise Software Inc",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("1500.00"),
            currency=Currency.USD,
            extraction_confidence=0.98,
            has_required_data=True
        )
        
        log_entry = ReceiptProcessingLog(
            original_filename="enterprise_receipt.jpg",
            file_path=Path("/receipts/enterprise_receipt.jpg"),
            file_size=2048,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=receipt_data,
            confidence_score=0.95
        )
        
        # Test workflow statistics
        stats = integrator.get_workflow_statistics()
        assert stats["enabled"]
        assert stats["trigger_rules"] > 4  # Default + custom rule
        
        # Test batch summary
        batch_summary = integrator.batch_manager.get_batch_summary()
        assert all(count == 0 for count in batch_summary.values())  # No batched events yet
        
        print("✅ Complete email workflow integration test passed!")
        print(f"   - Configuration: {len(integrator.config.trigger_rules)} trigger rules")
        print(f"   - Recipients: {len(workflow_config.default_recipients)} default recipients")
        print(f"   - Batch settings: {workflow_config.batch_size} size, {workflow_config.batch_timeout_minutes}min timeout")
        print(f"   - Templates: {len(list(template_manager.template_dir.glob('*.html')))} HTML templates")
        print(f"   - Workflow enabled: {stats['enabled']}")
