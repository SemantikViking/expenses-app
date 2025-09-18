"""
Payment Workflow and Status Management System.

This module provides comprehensive workflow management for payment processing,
including status transitions, approval workflows, and automated processing.
"""

import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from .payment_models import (
    PaymentTrackingLog, PaymentStatus, PaymentMethod, PaymentType,
    ApprovalStatus, PaymentPriority, PaymentRecipient, PaymentApproval,
    PaymentDisbursement, PaymentAuditTrail
)
from .payment_validation import PaymentValidator, ValidationResult
from .payment_storage import PaymentStorageManager

logger = logging.getLogger(__name__)


class WorkflowAction(str, Enum):
    """Workflow actions that can be performed."""
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    DISBURSE = "disburse"
    CANCEL = "cancel"
    REFUND = "refund"
    ESCALATE = "escalate"
    RETRY = "retry"


class WorkflowEvent(str, Enum):
    """Workflow events that can trigger actions."""
    PAYMENT_CREATED = "payment_created"
    PAYMENT_SUBMITTED = "payment_submitted"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_REJECTED = "payment_rejected"
    PAYMENT_DISBURSED = "payment_disbursed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_OVERDUE = "payment_overdue"
    APPROVAL_REQUIRED = "approval_required"
    ESCALATION_REQUIRED = "escalation_required"


@dataclass
class WorkflowRule:
    """Workflow rule definition."""
    rule_id: str
    name: str
    description: str
    trigger_event: WorkflowEvent
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[WorkflowAction] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    auto_execute: bool = False
    
    def matches(self, payment: PaymentTrackingLog, event: WorkflowEvent) -> bool:
        """Check if rule matches payment and event."""
        if not self.enabled or self.trigger_event != event:
            return False
        
        # Check conditions
        for condition, expected_value in self.conditions.items():
            if not self._evaluate_condition(payment, condition, expected_value):
                return False
        
        return True
    
    def _evaluate_condition(self, payment: PaymentTrackingLog, condition: str, expected_value: Any) -> bool:
        """Evaluate a single condition."""
        try:
            if condition == "amount_greater_than":
                return payment.amount > Decimal(str(expected_value))
            elif condition == "amount_less_than":
                return payment.amount < Decimal(str(expected_value))
            elif condition == "payment_type":
                return (payment.payment_type.value if hasattr(payment.payment_type, 'value') else str(payment.payment_type)) == expected_value
            elif condition == "payment_method":
                return (payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)) == expected_value
            elif condition == "priority":
                return (payment.payment_priority.value if hasattr(payment.payment_priority, 'value') else str(payment.payment_priority)) == expected_value
            elif condition == "department":
                return payment.department == expected_value
            elif condition == "is_overdue":
                return payment.is_overdue() == expected_value
            elif condition == "requires_approval":
                return payment.requires_approval() == expected_value
            else:
                logger.warning(f"Unknown condition: {condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False


@dataclass
class WorkflowStep:
    """Individual workflow step."""
    step_id: str
    name: str
    action: WorkflowAction
    required_approval_level: int = 1
    auto_approve: bool = False
    timeout_hours: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    error_handler: Optional[str] = None


class PaymentWorkflowEngine:
    """Main payment workflow engine."""
    
    def __init__(self, storage_manager: PaymentStorageManager, 
                 validator: PaymentValidator = None):
        self.storage_manager = storage_manager
        self.validator = validator or PaymentValidator()
        self.workflow_rules: List[WorkflowRule] = []
        self.workflow_steps: Dict[str, List[WorkflowStep]] = {}
        self.event_handlers: Dict[WorkflowEvent, List[Callable]] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._running = False
        self._lock = threading.Lock()
        
        # Initialize default workflow rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default workflow rules."""
        default_rules = [
            # Auto-approve small amounts
            WorkflowRule(
                rule_id="auto_approve_small",
                name="Auto-approve Small Payments",
                description="Automatically approve payments under threshold",
                trigger_event=WorkflowEvent.PAYMENT_SUBMITTED,
                conditions={"amount_less_than": "1000.00"},
                actions=[WorkflowAction.APPROVE],
                auto_execute=True
            ),
            
            # Escalate large amounts
            WorkflowRule(
                rule_id="escalate_large",
                name="Escalate Large Payments",
                description="Escalate large payments for review",
                trigger_event=WorkflowEvent.PAYMENT_SUBMITTED,
                conditions={"amount_greater_than": "10000.00"},
                actions=[WorkflowAction.ESCALATE],
                auto_execute=True
            ),
            
            # Handle overdue payments
            WorkflowRule(
                rule_id="handle_overdue",
                name="Handle Overdue Payments",
                description="Process overdue payments",
                trigger_event=WorkflowEvent.PAYMENT_OVERDUE,
                conditions={"is_overdue": True},
                actions=[WorkflowAction.ESCALATE],
                auto_execute=True
            ),
            
            # Auto-disburse approved payments
            WorkflowRule(
                rule_id="auto_disburse",
                name="Auto-disburse Approved",
                description="Automatically disburse approved payments",
                trigger_event=WorkflowEvent.PAYMENT_APPROVED,
                conditions={},
                actions=[WorkflowAction.DISBURSE],
                auto_execute=True
            )
        ]
        
        for rule in default_rules:
            self.add_workflow_rule(rule)
    
    def add_workflow_rule(self, rule: WorkflowRule):
        """Add a workflow rule."""
        with self._lock:
            self.workflow_rules.append(rule)
            logger.info(f"Added workflow rule: {rule.name}")
    
    def remove_workflow_rule(self, rule_id: str):
        """Remove a workflow rule."""
        with self._lock:
            self.workflow_rules = [r for r in self.workflow_rules if r.rule_id != rule_id]
            logger.info(f"Removed workflow rule: {rule_id}")
    
    def add_event_handler(self, event: WorkflowEvent, handler: Callable):
        """Add event handler."""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
        logger.info(f"Added event handler for {event.value}")
    
    def remove_event_handler(self, event: WorkflowEvent, handler: Callable):
        """Remove event handler."""
        if event in self.event_handlers:
            self.event_handlers[event].remove(handler)
            logger.info(f"Removed event handler for {event.value}")
    
    def process_payment_event(self, payment: PaymentTrackingLog, event: WorkflowEvent) -> bool:
        """Process a payment workflow event."""
        try:
            # Find matching rules
            matching_rules = [rule for rule in self.workflow_rules if rule.matches(payment, event)]
            
            # Sort by priority (higher number = higher priority)
            matching_rules.sort(key=lambda r: r.priority, reverse=True)
            
            # Execute rules
            for rule in matching_rules:
                if rule.auto_execute:
                    self._execute_rule(rule, payment, event)
                else:
                    # Queue for manual execution
                    self._queue_rule_for_execution(rule, payment, event)
            
            # Trigger event handlers
            self._trigger_event_handlers(event, payment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing payment event {event.value}: {e}")
            return False
    
    def _execute_rule(self, rule: WorkflowRule, payment: PaymentTrackingLog, event: WorkflowEvent):
        """Execute a workflow rule."""
        try:
            logger.info(f"Executing rule {rule.name} for payment {payment.payment_id}")
            
            for action in rule.actions:
                self._execute_action(action, payment, rule)
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.name}: {e}")
    
    def _execute_action(self, action: WorkflowAction, payment: PaymentTrackingLog, rule: WorkflowRule):
        """Execute a workflow action."""
        try:
            if action == WorkflowAction.SUBMIT:
                self._submit_payment(payment)
            elif action == WorkflowAction.APPROVE:
                self._approve_payment(payment, rule)
            elif action == WorkflowAction.REJECT:
                self._reject_payment(payment, rule)
            elif action == WorkflowAction.DISBURSE:
                self._disburse_payment(payment)
            elif action == WorkflowAction.CANCEL:
                self._cancel_payment(payment)
            elif action == WorkflowAction.REFUND:
                self._refund_payment(payment)
            elif action == WorkflowAction.ESCALATE:
                self._escalate_payment(payment, rule)
            elif action == WorkflowAction.RETRY:
                self._retry_payment(payment)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
    
    def _submit_payment(self, payment: PaymentTrackingLog):
        """Submit payment for processing."""
        payment.add_status_change(
            PaymentStatus.PROCESSING,
            "Payment submitted for processing",
            "system",
            "Workflow Engine"
        )
        payment.submitted_at = datetime.now()
        self.storage_manager.update_payment(payment)
        
        # Trigger next event
        self.process_payment_event(payment, WorkflowEvent.PAYMENT_SUBMITTED)
    
    def _approve_payment(self, payment: PaymentTrackingLog, rule: WorkflowRule):
        """Approve payment."""
        approval = PaymentApproval(
            approver_id="system",
            approver_name="Workflow Engine",
            approver_email="workflow@system.com",
            approval_date=datetime.now(),
            approval_status=ApprovalStatus.AUTO_APPROVED,
            approval_notes=f"Auto-approved by rule: {rule.name}",
            approval_level=1
        )
        
        payment.add_approval(approval)
        payment.add_status_change(
            PaymentStatus.APPROVED,
            "Payment approved automatically",
            "system",
            "Workflow Engine"
        )
        payment.approved_at = datetime.now()
        self.storage_manager.update_payment(payment)
        
        # Trigger next event
        self.process_payment_event(payment, WorkflowEvent.PAYMENT_APPROVED)
    
    def _reject_payment(self, payment: PaymentTrackingLog, rule: WorkflowRule):
        """Reject payment."""
        payment.add_status_change(
            PaymentStatus.REJECTED,
            f"Payment rejected by rule: {rule.name}",
            "system",
            "Workflow Engine"
        )
        self.storage_manager.update_payment(payment)
        
        # Trigger next event
        self.process_payment_event(payment, WorkflowEvent.PAYMENT_REJECTED)
    
    def _disburse_payment(self, payment: PaymentTrackingLog):
        """Disburse payment."""
        disbursement = PaymentDisbursement(
            disbursement_id=f"disb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            disbursement_date=datetime.now(),
            disbursement_method=payment.payment_method,
            disbursement_notes="Automated disbursement"
        )
        
        payment.disbursement = disbursement
        payment.add_status_change(
            PaymentStatus.DISBURSED,
            "Payment disbursed automatically",
            "system",
            "Workflow Engine"
        )
        payment.disbursed_at = datetime.now()
        self.storage_manager.update_payment(payment)
        
        # Trigger next event
        self.process_payment_event(payment, WorkflowEvent.PAYMENT_DISBURSED)
    
    def _cancel_payment(self, payment: PaymentTrackingLog):
        """Cancel payment."""
        payment.add_status_change(
            PaymentStatus.CANCELLED,
            "Payment cancelled by workflow",
            "system",
            "Workflow Engine"
        )
        self.storage_manager.update_payment(payment)
    
    def _refund_payment(self, payment: PaymentTrackingLog):
        """Refund payment."""
        payment.add_status_change(
            PaymentStatus.REFUNDED,
            "Payment refunded by workflow",
            "system",
            "Workflow Engine"
        )
        self.storage_manager.update_payment(payment)
    
    def _escalate_payment(self, payment: PaymentTrackingLog, rule: WorkflowRule):
        """Escalate payment for manual review."""
        payment.add_status_change(
            PaymentStatus.PROCESSING,
            f"Payment escalated by rule: {rule.name}",
            "system",
            "Workflow Engine"
        )
        payment.add_audit_entry(
            "ESCALATED",
            "system",
            "Workflow Engine",
            reason=f"Escalated by rule: {rule.name}"
        )
        self.storage_manager.update_payment(payment)
        
        # Trigger next event
        self.process_payment_event(payment, WorkflowEvent.ESCALATION_REQUIRED)
    
    def _retry_payment(self, payment: PaymentTrackingLog):
        """Retry failed payment."""
        payment.retry_count += 1
        payment.add_status_change(
            PaymentStatus.PROCESSING,
            f"Payment retry attempt {payment.retry_count}",
            "system",
            "Workflow Engine"
        )
        self.storage_manager.update_payment(payment)
    
    def _queue_rule_for_execution(self, rule: WorkflowRule, payment: PaymentTrackingLog, event: WorkflowEvent):
        """Queue rule for manual execution."""
        # This would typically add to a queue for manual processing
        logger.info(f"Queued rule {rule.name} for manual execution")
    
    def _trigger_event_handlers(self, event: WorkflowEvent, payment: PaymentTrackingLog):
        """Trigger event handlers."""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(payment, event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.value}: {e}")
    
    def create_payment(self, payment_data: Dict[str, Any], user_id: str = None, user_name: str = None) -> Optional[PaymentTrackingLog]:
        """Create a new payment and trigger workflow."""
        try:
            # Validate payment data
            payment = PaymentTrackingLog(**payment_data)
            
            # Validate payment
            validation_result = self.validator.validate_payment(payment)
            if not validation_result.is_valid:
                logger.error(f"Payment validation failed: {validation_result.errors}")
                return None
            
            # Add audit entry
            payment.add_audit_entry(
                "CREATED",
                user_id or "system",
                user_name or "System",
                new_value=payment.payment_id
            )
            
            # Save payment
            if self.storage_manager.add_payment(payment):
                # Trigger workflow event
                self.process_payment_event(payment, WorkflowEvent.PAYMENT_CREATED)
                return payment
            else:
                logger.error("Failed to save payment")
                return None
                
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None
    
    def update_payment_status(self, payment_id: str, new_status: PaymentStatus, 
                            reason: str = None, user_id: str = None, user_name: str = None) -> bool:
        """Update payment status and trigger workflow."""
        try:
            payment = self.storage_manager.get_payment(payment_id)
            if not payment:
                logger.error(f"Payment not found: {payment_id}")
                return False
            
            old_status = payment.current_status
            payment.add_status_change(new_status, reason, user_id, user_name)
            
            # Add audit entry
            payment.add_audit_entry(
                "STATUS_CHANGED",
                user_id or "system",
                user_name or "System",
                old_value=str(old_status),
                new_value=str(new_status),
                reason=reason
            )
            
            # Update payment
            if self.storage_manager.update_payment(payment):
                # Map status to event
                status_to_event = {
                    PaymentStatus.PROCESSING: WorkflowEvent.PAYMENT_SUBMITTED,
                    PaymentStatus.APPROVED: WorkflowEvent.PAYMENT_APPROVED,
                    PaymentStatus.REJECTED: WorkflowEvent.PAYMENT_REJECTED,
                    PaymentStatus.DISBURSED: WorkflowEvent.PAYMENT_DISBURSED,
                    PaymentStatus.FAILED: WorkflowEvent.PAYMENT_FAILED
                }
                
                # Handle both enum and string status values
                event = status_to_event.get(new_status)
                if not event:
                    # Try to find by string value
                    for status_enum, event_enum in status_to_event.items():
                        if str(status_enum) == str(new_status) or (hasattr(new_status, 'value') and str(status_enum) == str(new_status.value)):
                            event = event_enum
                            break
                if event:
                    self.process_payment_event(payment, event)
                
                return True
            else:
                logger.error("Failed to update payment")
                return False
                
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            return False
    
    def approve_payment(self, payment_id: str, approver_id: str, approver_name: str, 
                       approver_email: str, approval_notes: str = None) -> bool:
        """Approve a payment."""
        try:
            payment = self.storage_manager.get_payment(payment_id)
            if not payment:
                logger.error(f"Payment not found: {payment_id}")
                return False
            
            # Create approval
            approval = PaymentApproval(
                approver_id=approver_id,
                approver_name=approver_name,
                approver_email=approver_email,
                approval_date=datetime.now(),
                approval_status=ApprovalStatus.APPROVED,
                approval_notes=approval_notes
            )
            
            payment.add_approval(approval)
            payment.add_status_change(
                PaymentStatus.APPROVED,
                f"Payment approved by {approver_name}",
                approver_id,
                approver_name
            )
            payment.approved_at = datetime.now()
            
            # Add audit entry
            payment.add_audit_entry(
                "APPROVED",
                approver_id,
                approver_name,
                reason=approval_notes
            )
            
            # Update payment
            if self.storage_manager.update_payment(payment):
                self.process_payment_event(payment, WorkflowEvent.PAYMENT_APPROVED)
                return True
            else:
                logger.error("Failed to update payment")
                return False
                
        except Exception as e:
            logger.error(f"Error approving payment: {e}")
            return False
    
    def get_workflow_status(self, payment_id: str) -> Dict[str, Any]:
        """Get workflow status for a payment."""
        try:
            payment = self.storage_manager.get_payment(payment_id)
            if not payment:
                return {"error": "Payment not found"}
            
            return {
                "payment_id": payment.payment_id,
                "current_status": payment.current_status.value if hasattr(payment.current_status, 'value') else str(payment.current_status),
                "approval_status": payment.approval_status.value if hasattr(payment.approval_status, 'value') else str(payment.approval_status),
                "status_history": payment.status_history,
                "approval_workflow": [
                    {
                        "approver": approval.approver_name,
                        "status": approval.approval_status.value if hasattr(approval.approval_status, 'value') else str(approval.approval_status),
                        "date": approval.approval_date,
                        "notes": approval.approval_notes
                    }
                    for approval in payment.approval_workflow
                ],
                "audit_trail": [
                    {
                        "action": audit.action,
                        "user": audit.user_name,
                        "timestamp": audit.timestamp,
                        "reason": audit.reason
                    }
                    for audit in payment.audit_trail
                ],
                "is_overdue": payment.is_overdue(),
                "requires_approval": payment.requires_approval(),
                "ready_for_disbursement": payment.is_ready_for_disbursement()
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {"error": str(e)}
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        try:
            stats = self.storage_manager.get_payment_statistics()
            
            # Add workflow-specific statistics
            workflow_stats = {
                "total_rules": len(self.workflow_rules),
                "enabled_rules": len([r for r in self.workflow_rules if r.enabled]),
                "auto_execute_rules": len([r for r in self.workflow_rules if r.auto_execute]),
                "event_handlers": sum(len(handlers) for handlers in self.event_handlers.values()),
                "workflow_engine_running": self._running
            }
            
            stats.update(workflow_stats)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {e}")
            return {"error": str(e)}
    
    def start_workflow_engine(self):
        """Start the workflow engine."""
        if self._running:
            return
        
        self._running = True
        logger.info("Payment workflow engine started")
    
    def stop_workflow_engine(self):
        """Stop the workflow engine."""
        self._running = False
        logger.info("Payment workflow engine stopped")
    
    def cleanup_old_workflow_data(self, retention_days: int = 90) -> int:
        """Clean up old workflow data."""
        try:
            return self.storage_manager.cleanup_old_payments(retention_days)
        except Exception as e:
            logger.error(f"Error cleaning up workflow data: {e}")
            return 0
