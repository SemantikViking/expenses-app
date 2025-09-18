"""
Email Workflow Integration System for Receipt Processing.

This module integrates email notifications with the receipt processing workflow,
providing automated triggers, status-based notifications, and workflow management.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

from .models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData
)
from .email_system import (
    EmailSender, EmailConfig, EmailRecipient, EmailMessage, EmailStatus,
    EmailDeliveryResult, EmailTemplateManager, EmailTracker
)
from .status_tracker import EnhancedStatusTracker
from .storage import JSONStorageManager

logger = logging.getLogger(__name__)


class EmailTriggerType(str, Enum):
    """Types of email triggers."""
    STATUS_CHANGE = "status_change"
    PROCESSING_COMPLETE = "processing_complete"
    ERROR_OCCURRED = "error_occurred"
    MANUAL_SEND = "manual_send"
    SCHEDULED_REPORT = "scheduled_report"
    BULK_OPERATION = "bulk_operation"
    WORKFLOW_MILESTONE = "workflow_milestone"


class EmailPriority(str, Enum):
    """Email priority levels for workflow notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationFrequency(str, Enum):
    """Notification frequency settings."""
    IMMEDIATE = "immediate"
    BATCHED_HOURLY = "batched_hourly"
    BATCHED_DAILY = "batched_daily"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    DISABLED = "disabled"


@dataclass
class EmailTriggerRule:
    """Defines when and how emails should be triggered."""
    trigger_type: EmailTriggerType
    status_conditions: List[ProcessingStatus] = field(default_factory=list)
    recipients: List[EmailRecipient] = field(default_factory=list)
    template_name: str = ""
    priority: EmailPriority = EmailPriority.NORMAL
    frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    conditions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    def matches_conditions(self, log_entry: ReceiptProcessingLog) -> bool:
        """Check if the log entry matches trigger conditions."""
        if not self.enabled:
            return False
        
        # Check status conditions
        if self.status_conditions and log_entry.current_status not in self.status_conditions:
            return False
        
        # Check custom conditions
        for condition, expected_value in self.conditions.items():
            if condition == "min_confidence" and log_entry.confidence_score:
                if log_entry.confidence_score < expected_value:
                    return False
            elif condition == "vendor_name" and log_entry.receipt_data:
                if log_entry.receipt_data.vendor_name != expected_value:
                    return False
            elif condition == "min_amount" and log_entry.receipt_data:
                if log_entry.receipt_data.total_amount < expected_value:
                    return False
        
        return True


@dataclass
class EmailWorkflowConfig:
    """Configuration for email workflow integration."""
    enabled: bool = True
    default_recipients: List[EmailRecipient] = field(default_factory=list)
    trigger_rules: List[EmailTriggerRule] = field(default_factory=list)
    batch_size: int = 50
    batch_timeout_minutes: int = 60
    max_retries: int = 3
    retry_delay_minutes: int = 15
    delivery_confirmation_required: bool = True
    error_escalation_enabled: bool = True
    escalation_threshold_hours: int = 24


@dataclass
class EmailWorkflowEvent:
    """Represents an email workflow event."""
    event_id: str
    trigger_type: EmailTriggerType
    log_entry: ReceiptProcessingLog
    recipients: List[EmailRecipient]
    template_name: str
    priority: EmailPriority
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    processed: bool = False
    delivery_result: Optional[EmailDeliveryResult] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class EmailBatchManager:
    """Manages batching of email notifications."""
    
    def __init__(self, config: EmailWorkflowConfig):
        self.config = config
        self.pending_events: Dict[NotificationFrequency, List[EmailWorkflowEvent]] = {
            freq: [] for freq in NotificationFrequency
        }
        self.last_batch_sent: Dict[NotificationFrequency, datetime] = {}
        self._lock = threading.Lock()
    
    def add_event(self, event: EmailWorkflowEvent, frequency: NotificationFrequency):
        """Add an event to the appropriate batch."""
        with self._lock:
            if frequency == NotificationFrequency.IMMEDIATE:
                # Don't batch immediate events
                return False
            
            self.pending_events[frequency].append(event)
            return True
    
    def get_ready_batches(self) -> Dict[NotificationFrequency, List[EmailWorkflowEvent]]:
        """Get batches that are ready to be sent."""
        ready_batches = {}
        current_time = datetime.now()
        
        with self._lock:
            for frequency, events in self.pending_events.items():
                if not events or frequency == NotificationFrequency.IMMEDIATE:
                    continue
                
                should_send = False
                last_sent = self.last_batch_sent.get(frequency)
                
                if frequency == NotificationFrequency.BATCHED_HOURLY:
                    should_send = not last_sent or (current_time - last_sent).total_seconds() >= 3600
                elif frequency == NotificationFrequency.BATCHED_DAILY:
                    should_send = not last_sent or (current_time - last_sent).days >= 1
                elif frequency == NotificationFrequency.WEEKLY_SUMMARY:
                    should_send = not last_sent or (current_time - last_sent).days >= 7
                elif frequency == NotificationFrequency.MONTHLY_SUMMARY:
                    should_send = not last_sent or (current_time - last_sent).days >= 30
                
                # Also check if batch is full
                if len(events) >= self.config.batch_size:
                    should_send = True
                
                if should_send:
                    ready_batches[frequency] = events.copy()
                    self.pending_events[frequency].clear()
                    self.last_batch_sent[frequency] = current_time
        
        return ready_batches
    
    def get_batch_summary(self) -> Dict[str, int]:
        """Get summary of pending batches."""
        with self._lock:
            return {
                freq.value: len(events) 
                for freq, events in self.pending_events.items()
            }


class EmailWorkflowLogger:
    """Logs email workflow activities and delivery confirmations."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path("email_workflow.log")
        self.delivery_confirmations: Dict[str, EmailDeliveryResult] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up workflow logging."""
        self.workflow_logger = logging.getLogger("email_workflow")
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.workflow_logger.addHandler(handler)
        self.workflow_logger.setLevel(logging.INFO)
    
    def log_trigger(self, event: EmailWorkflowEvent):
        """Log email trigger event."""
        self.workflow_logger.info(
            f"Email triggered - Event: {event.event_id}, "
            f"Type: {event.trigger_type.value}, "
            f"Recipients: {len(event.recipients)}, "
            f"Template: {event.template_name}"
        )
    
    def log_delivery(self, event: EmailWorkflowEvent, result: EmailDeliveryResult):
        """Log email delivery result."""
        event.delivery_result = result
        self.delivery_confirmations[event.event_id] = result
        
        self.workflow_logger.info(
            f"Email delivery - Event: {event.event_id}, "
            f"Status: {result.status.value}, "
            f"Message ID: {result.message_id}"
        )
        
        if result.error_message:
            self.workflow_logger.error(
                f"Email delivery error - Event: {event.event_id}, "
                f"Error: {result.error_message}"
            )
    
    def log_batch_operation(self, frequency: NotificationFrequency, 
                           events: List[EmailWorkflowEvent], success_count: int):
        """Log batch operation results."""
        self.workflow_logger.info(
            f"Batch operation completed - Frequency: {frequency.value}, "
            f"Total: {len(events)}, Success: {success_count}, "
            f"Failed: {len(events) - success_count}"
        )
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics."""
        total = len(self.delivery_confirmations)
        if total == 0:
            return {"total": 0, "success_rate": 0.0}
        
        successful = sum(
            1 for result in self.delivery_confirmations.values()
            if result.status in [EmailStatus.SENT, EmailStatus.DELIVERED]
        )
        
        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total) * 100
        }


class EmailWorkflowIntegrator:
    """Main class for integrating email workflows with receipt processing."""
    
    def __init__(self, 
                 email_sender: EmailSender,
                 storage_manager: JSONStorageManager,
                 status_tracker: Optional[EnhancedStatusTracker] = None,
                 config: Optional[EmailWorkflowConfig] = None):
        self.email_sender = email_sender
        self.storage_manager = storage_manager
        self.status_tracker = status_tracker
        self.config = config or EmailWorkflowConfig()
        
        # Initialize components
        self.batch_manager = EmailBatchManager(self.config)
        self.workflow_logger = EmailWorkflowLogger()
        self.event_queue: List[EmailWorkflowEvent] = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._running = False
        self._lock = threading.Lock()
        
        # Set up default trigger rules
        self._setup_default_triggers()
        
        # Connect to status tracker if provided
        if self.status_tracker:
            self._connect_status_tracker()
    
    def _setup_default_triggers(self):
        """Set up default email trigger rules."""
        if not self.config.trigger_rules:
            default_rules = [
                # Success notification
                EmailTriggerRule(
                    trigger_type=EmailTriggerType.STATUS_CHANGE,
                    status_conditions=[ProcessingStatus.PROCESSED],
                    recipients=self.config.default_recipients,
                    template_name="receipt_processed",
                    priority=EmailPriority.NORMAL,
                    frequency=NotificationFrequency.IMMEDIATE
                ),
                
                # Error notification
                EmailTriggerRule(
                    trigger_type=EmailTriggerType.ERROR_OCCURRED,
                    status_conditions=[ProcessingStatus.ERROR],
                    recipients=self.config.default_recipients,
                    template_name="receipt_error",
                    priority=EmailPriority.HIGH,
                    frequency=NotificationFrequency.IMMEDIATE
                ),
                
                # High-value receipt notification
                EmailTriggerRule(
                    trigger_type=EmailTriggerType.PROCESSING_COMPLETE,
                    status_conditions=[ProcessingStatus.PROCESSED],
                    recipients=self.config.default_recipients,
                    template_name="high_value_receipt",
                    priority=EmailPriority.HIGH,
                    frequency=NotificationFrequency.IMMEDIATE,
                    conditions={"min_amount": 1000.00}
                ),
                
                # Daily summary
                EmailTriggerRule(
                    trigger_type=EmailTriggerType.SCHEDULED_REPORT,
                    recipients=self.config.default_recipients,
                    template_name="daily_summary",
                    priority=EmailPriority.NORMAL,
                    frequency=NotificationFrequency.BATCHED_DAILY
                )
            ]
            
            self.config.trigger_rules.extend(default_rules)
    
    def _connect_status_tracker(self):
        """Connect to status tracker for automatic triggers."""
        # This would be implemented to listen for status changes
        # For now, we'll use manual triggering
        pass
    
    def add_trigger_rule(self, rule: EmailTriggerRule):
        """Add a new email trigger rule."""
        with self._lock:
            self.config.trigger_rules.append(rule)
    
    def remove_trigger_rule(self, trigger_type: EmailTriggerType, 
                           status_condition: Optional[ProcessingStatus] = None):
        """Remove trigger rules matching criteria."""
        with self._lock:
            self.config.trigger_rules = [
                rule for rule in self.config.trigger_rules
                if not (rule.trigger_type == trigger_type and
                       (status_condition is None or status_condition in rule.status_conditions))
            ]
    
    def trigger_email_for_receipt(self, log_entry: ReceiptProcessingLog,
                                 trigger_type: EmailTriggerType = EmailTriggerType.STATUS_CHANGE):
        """Trigger email notifications for a receipt based on workflow rules."""
        if not self.config.enabled:
            return []
        
        triggered_events = []
        
        for rule in self.config.trigger_rules:
            if rule.trigger_type != trigger_type:
                continue
            
            if not rule.matches_conditions(log_entry):
                continue
            
            # Create workflow event
            event = EmailWorkflowEvent(
                event_id=f"{log_entry.id}_{rule.trigger_type.value}_{datetime.now().timestamp()}",
                trigger_type=trigger_type,
                log_entry=log_entry,
                recipients=rule.recipients or self.config.default_recipients,
                template_name=rule.template_name,
                priority=rule.priority
            )
            
            # Handle based on frequency
            if rule.frequency == NotificationFrequency.IMMEDIATE:
                self._process_immediate_event(event)
            elif rule.frequency != NotificationFrequency.DISABLED:
                self.batch_manager.add_event(event, rule.frequency)
            
            triggered_events.append(event)
            self.workflow_logger.log_trigger(event)
        
        return triggered_events
    
    def _process_immediate_event(self, event: EmailWorkflowEvent):
        """Process an immediate email event."""
        try:
            # Get template variables
            template_vars = self.email_sender.template_manager.get_template_vars_for_receipt(
                event.log_entry
            )
            
            # Add workflow-specific variables
            template_vars.update({
                "event_id": event.event_id,
                "trigger_type": event.trigger_type.value,
                "priority": event.priority.value,
                "notification_time": datetime.now()
            })
            
            # Send email
            result = self.email_sender.send_template_email(
                template_name=event.template_name,
                recipients=event.recipients,
                template_vars=template_vars,
                attachments=[]
            )
            
            # Log delivery
            self.workflow_logger.log_delivery(event, result)
            event.processed = True
            
        except Exception as e:
            event.error_message = str(e)
            event.retry_count += 1
            logger.error(f"Failed to process immediate email event {event.event_id}: {e}")
    
    def process_batched_emails(self):
        """Process batched email notifications."""
        ready_batches = self.batch_manager.get_ready_batches()
        
        for frequency, events in ready_batches.items():
            if not events:
                continue
            
            try:
                success_count = self._send_batch_emails(frequency, events)
                self.workflow_logger.log_batch_operation(frequency, events, success_count)
            except Exception as e:
                logger.error(f"Failed to process batch for {frequency.value}: {e}")
    
    def _send_batch_emails(self, frequency: NotificationFrequency, 
                          events: List[EmailWorkflowEvent]) -> int:
        """Send a batch of emails."""
        success_count = 0
        
        # Group events by template and recipients for efficiency
        grouped_events = self._group_events_for_batch(events)
        
        for group_key, group_events in grouped_events.items():
            try:
                template_name, recipients_key = group_key
                recipients = group_events[0].recipients  # All events in group have same recipients
                
                # Create batch template variables
                batch_vars = self._create_batch_template_vars(group_events, frequency)
                
                # Send batch email
                result = self.email_sender.send_template_email(
                    template_name=f"{template_name}_batch",
                    recipients=recipients,
                    template_vars=batch_vars
                )
                
                # Log results for all events in the batch
                for event in group_events:
                    self.workflow_logger.log_delivery(event, result)
                    event.processed = True
                
                success_count += len(group_events)
                
            except Exception as e:
                for event in group_events:
                    event.error_message = str(e)
                    event.retry_count += 1
                logger.error(f"Failed to send batch email: {e}")
        
        return success_count
    
    def _group_events_for_batch(self, events: List[EmailWorkflowEvent]) -> Dict[tuple, List[EmailWorkflowEvent]]:
        """Group events by template and recipients for batch processing."""
        groups = {}
        
        for event in events:
            # Create a key based on template and recipients
            recipients_key = tuple(sorted([r.email for r in event.recipients]))
            group_key = (event.template_name, recipients_key)
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(event)
        
        return groups
    
    def _create_batch_template_vars(self, events: List[EmailWorkflowEvent], 
                                   frequency: NotificationFrequency) -> Dict[str, Any]:
        """Create template variables for batch emails."""
        receipts_data = []
        total_amount = 0
        
        for event in events:
            receipt_vars = self.email_sender.template_manager.get_template_vars_for_receipt(
                event.log_entry
            )
            receipts_data.append(receipt_vars)
            
            if event.log_entry.receipt_data and event.log_entry.receipt_data.total_amount:
                total_amount += float(event.log_entry.receipt_data.total_amount)
        
        return {
            "batch_frequency": frequency.value,
            "batch_size": len(events),
            "receipts": receipts_data,
            "total_amount": total_amount,
            "batch_created_at": datetime.now(),
            "period_start": min(event.created_at for event in events),
            "period_end": max(event.created_at for event in events)
        }
    
    def send_manual_email(self, log_entry: ReceiptProcessingLog,
                         recipients: List[EmailRecipient],
                         template_name: str,
                         priority: EmailPriority = EmailPriority.NORMAL) -> EmailDeliveryResult:
        """Send a manual email for a specific receipt."""
        event = EmailWorkflowEvent(
            event_id=f"manual_{log_entry.id}_{datetime.now().timestamp()}",
            trigger_type=EmailTriggerType.MANUAL_SEND,
            log_entry=log_entry,
            recipients=recipients,
            template_name=template_name,
            priority=priority
        )
        
        self.workflow_logger.log_trigger(event)
        self._process_immediate_event(event)
        
        return event.delivery_result
    
    def send_bulk_emails(self, log_entries: List[ReceiptProcessingLog],
                        recipients: List[EmailRecipient],
                        template_name: str = "bulk_receipt_summary") -> List[EmailDeliveryResult]:
        """Send bulk emails for multiple receipts."""
        results = []
        
        # Create bulk template variables
        receipts_data = []
        total_amount = 0
        
        for log_entry in log_entries:
            receipt_vars = self.email_sender.template_manager.get_template_vars_for_receipt(log_entry)
            receipts_data.append(receipt_vars)
            
            if log_entry.receipt_data and log_entry.receipt_data.total_amount:
                total_amount += float(log_entry.receipt_data.total_amount)
        
        bulk_vars = {
            "receipts": receipts_data,
            "total_receipts": len(log_entries),
            "total_amount": total_amount,
            "bulk_created_at": datetime.now(),
            "period_start": min(entry.created_at for entry in log_entries),
            "period_end": max(entry.created_at for entry in log_entries)
        }
        
        # Send bulk email
        try:
            result = self.email_sender.send_template_email(
                template_name=template_name,
                recipients=recipients,
                template_vars=bulk_vars
            )
            
            # Log bulk operation
            self.workflow_logger.workflow_logger.info(
                f"Bulk email sent - Recipients: {len(recipients)}, "
                f"Receipts: {len(log_entries)}, Status: {result.status.value}"
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Failed to send bulk email: {e}")
            # Create error result
            error_result = EmailDeliveryResult(
                message_id="bulk_error",
                status=EmailStatus.FAILED,
                error_message=str(e)
            )
            results.append(error_result)
        
        return results
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics and metrics."""
        delivery_stats = self.workflow_logger.get_delivery_stats()
        batch_summary = self.batch_manager.get_batch_summary()
        
        return {
            "delivery_stats": delivery_stats,
            "batch_summary": batch_summary,
            "trigger_rules": len(self.config.trigger_rules),
            "enabled": self.config.enabled,
            "pending_events": len(self.event_queue)
        }
    
    def start_workflow_processor(self):
        """Start the workflow processor for batched emails."""
        if self._running:
            return
        
        self._running = True
        
        def process_loop():
            while self._running:
                try:
                    self.process_batched_emails()
                    # Sleep for batch timeout / 4 to check frequently
                    sleep_time = (self.config.batch_timeout_minutes * 60) // 4
                    threading.Event().wait(sleep_time)
                except Exception as e:
                    logger.error(f"Error in workflow processor: {e}")
                    threading.Event().wait(60)  # Wait 1 minute on error
        
        # Start processor in background thread
        processor_thread = threading.Thread(target=process_loop, daemon=True)
        processor_thread.start()
        
        logger.info("Email workflow processor started")
    
    def stop_workflow_processor(self):
        """Stop the workflow processor."""
        self._running = False
        logger.info("Email workflow processor stopped")
    
    def create_custom_template(self, template_name: str, 
                              html_content: str, 
                              subject_template: str,
                              text_content: Optional[str] = None):
        """Create a custom email template for workflow notifications."""
        # Save HTML template
        html_file = self.email_sender.template_manager.template_dir / f"{template_name}.html"
        html_file.write_text(html_content)
        
        # Save subject template
        subject_file = self.email_sender.template_manager.template_dir / f"{template_name}_subject.txt"
        subject_file.write_text(subject_template)
        
        # Save text template if provided
        if text_content:
            text_file = self.email_sender.template_manager.template_dir / f"{template_name}.txt"
            text_file.write_text(text_content)
        
        logger.info(f"Custom template '{template_name}' created successfully")
    
    def test_workflow_integration(self, test_recipient: str) -> Dict[str, Any]:
        """Test the workflow integration with a sample receipt."""
        try:
            # Create test receipt
            from .models import ReceiptData, Currency
            from decimal import Decimal
            
            test_receipt_data = ReceiptData(
                vendor_name="Test Vendor",
                transaction_date=datetime.now(),
                total_amount=Decimal("99.99"),
                currency=Currency.USD,
                extraction_confidence=0.95,
                has_required_data=True
            )
            
            test_log_entry = ReceiptProcessingLog(
                original_filename="test_receipt.jpg",
                file_path=Path("/test/test_receipt.jpg"),
                file_size=1024,
                current_status=ProcessingStatus.PROCESSED,
                receipt_data=test_receipt_data,
                confidence_score=0.9
            )
            
            # Test manual email
            test_recipients = [EmailRecipient(email=test_recipient)]
            result = self.send_manual_email(
                log_entry=test_log_entry,
                recipients=test_recipients,
                template_name="receipt_processed"
            )
            
            return {
                "success": result.status in [EmailStatus.SENT, EmailStatus.DELIVERED],
                "message_id": result.message_id,
                "status": result.status.value,
                "error": result.error_message,
                "workflow_stats": self.get_workflow_statistics()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflow_stats": self.get_workflow_statistics()
            }
