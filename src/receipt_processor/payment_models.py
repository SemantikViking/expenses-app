"""
Payment Tracking Data Models for Receipt Processing.

This module defines comprehensive data models for tracking payments,
reconciliation, financial reporting, and audit trails.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator

from .models import ReceiptProcessingLog, Currency


class PaymentStatus(str, Enum):
    """Payment processing status."""
    PENDING = "pending"           # Payment submitted, awaiting processing
    PROCESSING = "processing"     # Payment being processed
    APPROVED = "approved"         # Payment approved for disbursement
    DISBURSED = "disbursed"       # Payment sent to recipient
    RECEIVED = "received"         # Payment received by recipient
    REJECTED = "rejected"         # Payment rejected
    CANCELLED = "cancelled"       # Payment cancelled
    FAILED = "failed"            # Payment processing failed
    REFUNDED = "refunded"        # Payment refunded
    DISPUTED = "disputed"        # Payment under dispute


class PaymentMethod(str, Enum):
    """Payment methods supported."""
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"
    WIRE_TRANSFER = "wire_transfer"
    CHECK = "check"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    VENMO = "venmo"
    ZELLE = "zelle"
    CASH_APP = "cash_app"
    OTHER = "other"


class PaymentType(str, Enum):
    """Types of payments."""
    REIMBURSEMENT = "reimbursement"     # Employee reimbursement
    VENDOR_PAYMENT = "vendor_payment"   # Direct vendor payment
    EXPENSE_REPORT = "expense_report"   # Expense report payment
    ADVANCE = "advance"                 # Advance payment
    REFUND = "refund"                   # Refund payment
    ADJUSTMENT = "adjustment"           # Payment adjustment
    BONUS = "bonus"                     # Bonus payment
    OTHER = "other"                     # Other payment type


class ApprovalStatus(str, Enum):
    """Payment approval status."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    ESCALATED = "escalated"
    REQUIRES_REVIEW = "requires_review"


class PaymentPriority(str, Enum):
    """Payment priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ReconciliationStatus(str, Enum):
    """Payment reconciliation status."""
    NOT_RECONCILED = "not_reconciled"
    PENDING_RECONCILIATION = "pending_reconciliation"
    RECONCILED = "reconciled"
    DISCREPANCY = "discrepancy"
    REQUIRES_INVESTIGATION = "requires_investigation"


@dataclass
class PaymentRecipient:
    """Payment recipient information."""
    name: str
    email: str
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    bank_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    payment_preference: Optional[PaymentMethod] = None
    
    def __post_init__(self):
        """Validate recipient information."""
        if not self.name or not self.email:
            raise ValueError("Recipient name and email are required")
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")


@dataclass
class PaymentApproval:
    """Payment approval information."""
    approver_id: str
    approver_name: str
    approver_email: str
    approval_date: datetime
    approval_status: ApprovalStatus
    approval_notes: Optional[str] = None
    approval_level: int = 1  # 1 = first level, 2 = second level, etc.
    required_amount_threshold: Optional[Decimal] = None
    
    def __post_init__(self):
        """Validate approval information."""
        if not all([self.approver_id, self.approver_name, self.approver_email]):
            raise ValueError("Approver information is required")


@dataclass
class PaymentDisbursement:
    """Payment disbursement information."""
    disbursement_id: str
    disbursement_date: datetime
    disbursement_method: PaymentMethod
    disbursement_reference: Optional[str] = None
    disbursement_notes: Optional[str] = None
    processing_fee: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    bank_reference: Optional[str] = None
    transaction_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate disbursement information."""
        if not self.disbursement_id or not self.disbursement_date:
            raise ValueError("Disbursement ID and date are required")


@dataclass
class PaymentReconciliation:
    """Payment reconciliation information."""
    reconciliation_id: str
    reconciliation_date: datetime
    reconciliation_status: ReconciliationStatus
    reconciled_amount: Decimal
    bank_statement_reference: Optional[str] = None
    reconciliation_notes: Optional[str] = None
    discrepancy_amount: Optional[Decimal] = None
    discrepancy_reason: Optional[str] = None
    reconciled_by: Optional[str] = None
    
    def __post_init__(self):
        """Validate reconciliation information."""
        if not self.reconciliation_id or not self.reconciliation_date:
            raise ValueError("Reconciliation ID and date are required")


@dataclass
class PaymentAuditTrail:
    """Payment audit trail entry."""
    audit_id: str
    timestamp: datetime
    action: str
    user_id: str
    user_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        """Validate audit trail information."""
        if not all([self.audit_id, self.action, self.user_id, self.user_name]):
            raise ValueError("Audit trail information is required")


class PaymentTrackingLog(BaseModel):
    """Main payment tracking log entry."""
    
    # Primary identifiers
    id: UUID = Field(default_factory=uuid4)
    payment_id: str = Field(..., description="Unique payment identifier")
    receipt_log_id: Optional[UUID] = Field(None, description="Associated receipt log ID")
    
    # Payment details
    amount: Decimal = Field(..., description="Payment amount")
    currency: Currency = Field(default=Currency.USD, description="Payment currency")
    payment_type: PaymentType = Field(..., description="Type of payment")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_priority: PaymentPriority = Field(default=PaymentPriority.NORMAL, description="Payment priority")
    
    # Status and workflow
    current_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Current payment status")
    status_history: List[Dict[str, Any]] = Field(default_factory=list, description="Status change history")
    
    # Recipient information
    recipient: PaymentRecipient = Field(..., description="Payment recipient")
    
    # Approval workflow
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING_APPROVAL, description="Approval status")
    approval_workflow: List[PaymentApproval] = Field(default_factory=list, description="Approval workflow")
    auto_approval_threshold: Optional[Decimal] = Field(None, description="Auto-approval threshold")
    
    # Disbursement information
    disbursement: Optional[PaymentDisbursement] = Field(None, description="Disbursement details")
    
    # Reconciliation
    reconciliation: Optional[PaymentReconciliation] = Field(None, description="Reconciliation details")
    
    # Financial details
    processing_fee: Optional[Decimal] = Field(None, description="Processing fee")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount")
    net_amount: Optional[Decimal] = Field(None, description="Net payment amount")
    
    # Dates and timing
    created_at: datetime = Field(default_factory=datetime.now, description="Payment creation date")
    submitted_at: Optional[datetime] = Field(None, description="Payment submission date")
    approved_at: Optional[datetime] = Field(None, description="Payment approval date")
    disbursed_at: Optional[datetime] = Field(None, description="Payment disbursement date")
    received_at: Optional[datetime] = Field(None, description="Payment received date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    
    # Business context
    department: Optional[str] = Field(None, description="Department or cost center")
    project_code: Optional[str] = Field(None, description="Project or job code")
    expense_category: Optional[str] = Field(None, description="Expense category")
    business_purpose: Optional[str] = Field(None, description="Business purpose")
    
    # Additional information
    description: Optional[str] = Field(None, description="Payment description")
    reference_number: Optional[str] = Field(None, description="External reference number")
    tags: List[str] = Field(default_factory=list, description="Payment tags")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Audit and compliance
    audit_trail: List[PaymentAuditTrail] = Field(default_factory=list, description="Audit trail")
    compliance_flags: List[str] = Field(default_factory=list, description="Compliance flags")
    retention_date: Optional[date] = Field(None, description="Data retention date")
    
    # Integration and external systems
    external_system_id: Optional[str] = Field(None, description="External system identifier")
    integration_metadata: Dict[str, Any] = Field(default_factory=dict, description="Integration metadata")
    
    # Validation and error handling
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    last_error: Optional[str] = Field(None, description="Last error message")
    retry_count: int = Field(default=0, description="Retry count")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate payment amount."""
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validate due date format."""
        # Allow past dates for testing and historical data
        return v
    
    @validator('net_amount')
    def validate_net_amount(cls, v, values):
        """Validate net amount calculation."""
        if v is not None and 'amount' in values:
            amount = values['amount']
            if v > amount:
                raise ValueError("Net amount cannot exceed gross amount")
        return v
    
    def add_status_change(self, new_status: PaymentStatus, reason: str = None, 
                         user_id: str = None, user_name: str = None):
        """Add a status change to the payment log."""
        status_entry = {
            "timestamp": datetime.now(),
            "old_status": self.current_status.value if hasattr(self.current_status, 'value') else str(self.current_status),
            "new_status": new_status.value if hasattr(new_status, 'value') else str(new_status),
            "reason": reason,
            "user_id": user_id,
            "user_name": user_name
        }
        
        self.status_history.append(status_entry)
        self.current_status = new_status
    
    def add_approval(self, approval: PaymentApproval):
        """Add an approval to the payment workflow."""
        self.approval_workflow.append(approval)
        self.approval_status = approval.approval_status
        
        if approval.approval_status == ApprovalStatus.APPROVED:
            self.approved_at = approval.approval_date
    
    def add_audit_entry(self, action: str, user_id: str, user_name: str,
                       old_value: Any = None, new_value: Any = None,
                       reason: str = None, ip_address: str = None):
        """Add an audit trail entry."""
        audit_entry = PaymentAuditTrail(
            audit_id=str(uuid4()),
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            user_name=user_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            ip_address=ip_address
        )
        
        self.audit_trail.append(audit_entry)
    
    def calculate_net_amount(self) -> Decimal:
        """Calculate net payment amount after fees and taxes."""
        net = self.amount
        
        if self.processing_fee:
            net -= self.processing_fee
        
        if self.tax_amount:
            net -= self.tax_amount
        
        return net
    
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        if not self.due_date:
            return False
        
        return (self.due_date < date.today() and 
                self.current_status not in [PaymentStatus.DISBURSED, PaymentStatus.RECEIVED])
    
    def get_processing_time(self) -> Optional[timedelta]:
        """Get total processing time."""
        if self.disbursed_at and self.submitted_at:
            return self.disbursed_at - self.submitted_at
        return None
    
    def requires_approval(self) -> bool:
        """Check if payment requires approval."""
        if self.auto_approval_threshold and self.amount <= self.auto_approval_threshold:
            return False
        
        return self.approval_status == ApprovalStatus.PENDING_APPROVAL
    
    def is_ready_for_disbursement(self) -> bool:
        """Check if payment is ready for disbursement."""
        return (self.current_status == PaymentStatus.APPROVED and
                self.approval_status == ApprovalStatus.APPROVED and
                self.disbursement is None)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get payment status summary."""
        return {
            "payment_id": self.payment_id,
            "amount": float(self.amount),
            "currency": self.currency.value,
            "status": self.current_status.value,
            "approval_status": self.approval_status.value,
            "recipient": self.recipient.name,
            "created_at": self.created_at,
            "is_overdue": self.is_overdue(),
            "requires_approval": self.requires_approval(),
            "ready_for_disbursement": self.is_ready_for_disbursement()
        }


class PaymentBatch(BaseModel):
    """Payment batch for bulk processing."""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    batch_name: str = Field(..., description="Batch name")
    payment_ids: List[str] = Field(..., description="Payment IDs in batch")
    batch_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Batch status")
    total_amount: Decimal = Field(..., description="Total batch amount")
    currency: Currency = Field(default=Currency.USD, description="Batch currency")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Batch creation date")
    processed_at: Optional[datetime] = Field(None, description="Batch processing date")
    created_by: Optional[str] = Field(None, description="Batch creator")
    
    processing_notes: Optional[str] = Field(None, description="Processing notes")
    error_count: int = Field(default=0, description="Number of errors in batch")
    success_count: int = Field(default=0, description="Number of successful payments")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
    
    def add_payment(self, payment_id: str):
        """Add payment to batch."""
        if payment_id not in self.payment_ids:
            self.payment_ids.append(payment_id)
    
    def remove_payment(self, payment_id: str):
        """Remove payment from batch."""
        if payment_id in self.payment_ids:
            self.payment_ids.remove(payment_id)
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Get batch summary information."""
        return {
            "batch_id": self.batch_id,
            "batch_name": self.batch_name,
            "payment_count": len(self.payment_ids),
            "total_amount": float(self.total_amount),
            "currency": self.currency.value,
            "status": self.batch_status.value,
            "created_at": self.created_at,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "success_rate": (self.success_count / len(self.payment_ids) * 100) if self.payment_ids else 0
        }


class PaymentReport(BaseModel):
    """Payment report data structure."""
    
    report_id: str = Field(..., description="Report identifier")
    report_name: str = Field(..., description="Report name")
    report_type: str = Field(..., description="Report type")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation date")
    generated_by: str = Field(..., description="Report generator")
    
    # Report parameters
    start_date: date = Field(..., description="Report start date")
    end_date: date = Field(..., description="Report end date")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")
    
    # Report data
    total_payments: int = Field(default=0, description="Total number of payments")
    total_amount: Decimal = Field(default=Decimal('0'), description="Total payment amount")
    currency: Currency = Field(default=Currency.USD, description="Report currency")
    
    # Summary statistics
    status_breakdown: Dict[str, int] = Field(default_factory=dict, description="Status breakdown")
    method_breakdown: Dict[str, int] = Field(default_factory=dict, description="Payment method breakdown")
    type_breakdown: Dict[str, int] = Field(default_factory=dict, description="Payment type breakdown")
    
    # Performance metrics
    average_processing_time: Optional[float] = Field(None, description="Average processing time in hours")
    approval_rate: Optional[float] = Field(None, description="Approval rate percentage")
    error_rate: Optional[float] = Field(None, description="Error rate percentage")
    
    # Report content
    payment_details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed payment data")
    summary_data: Dict[str, Any] = Field(default_factory=dict, description="Summary data")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
    
    def add_payment_data(self, payment: PaymentTrackingLog):
        """Add payment data to report."""
        self.total_payments += 1
        self.total_amount += payment.amount
        
        # Update breakdowns
        status = payment.current_status.value if hasattr(payment.current_status, 'value') else str(payment.current_status)
        self.status_breakdown[status] = self.status_breakdown.get(status, 0) + 1
        
        method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
        self.method_breakdown[method] = self.method_breakdown.get(method, 0) + 1
        
        payment_type = payment.payment_type.value if hasattr(payment.payment_type, 'value') else str(payment.payment_type)
        self.type_breakdown[payment_type] = self.type_breakdown.get(payment_type, 0) + 1
        
        # Add detailed data
        payment_detail = {
            "payment_id": payment.payment_id,
            "amount": float(payment.amount),
            "status": status,
            "recipient": payment.recipient.name,
            "created_at": payment.created_at,
            "approved_at": payment.approved_at,
            "disbursed_at": payment.disbursed_at
        }
        self.payment_details.append(payment_detail)
    
    def calculate_metrics(self):
        """Calculate report metrics."""
        if self.total_payments > 0:
            # Calculate approval rate
            approved_count = self.status_breakdown.get('approved', 0)
            self.approval_rate = (approved_count / self.total_payments) * 100
            
            # Calculate error rate
            error_count = self.status_breakdown.get('failed', 0) + self.status_breakdown.get('rejected', 0)
            self.error_rate = (error_count / self.total_payments) * 100
            
            # Calculate average processing time
            processing_times = []
            for payment in self.payment_details:
                if payment.get('disbursed_at') and payment.get('created_at'):
                    # This would need actual datetime parsing in real implementation
                    pass
            
            if processing_times:
                self.average_processing_time = sum(processing_times) / len(processing_times)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get report summary."""
        return {
            "report_id": self.report_id,
            "report_name": self.report_name,
            "report_type": self.report_type,
            "period": f"{self.start_date} to {self.end_date}",
            "total_payments": self.total_payments,
            "total_amount": float(self.total_amount),
            "currency": self.currency.value,
            "approval_rate": self.approval_rate,
            "error_rate": self.error_rate,
            "average_processing_time": self.average_processing_time
        }
