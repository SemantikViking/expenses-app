"""
Payment Validation and Reconciliation System.

This module provides comprehensive validation, reconciliation,
and compliance checking for payment processing.
"""

import re
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
import logging

from .payment_models import (
    PaymentTrackingLog, PaymentRecipient, PaymentStatus, PaymentMethod,
    PaymentType, ApprovalStatus, ReconciliationStatus
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationRule(str, Enum):
    """Payment validation rules."""
    # Amount validation
    AMOUNT_POSITIVE = "amount_positive"
    AMOUNT_WITHIN_LIMITS = "amount_within_limits"
    AMOUNT_REASONABLE = "amount_reasonable"
    
    # Recipient validation
    RECIPIENT_EMAIL_VALID = "recipient_email_valid"
    RECIPIENT_NAME_REQUIRED = "recipient_name_required"
    RECIPIENT_ACCOUNT_VALID = "recipient_account_valid"
    
    # Business logic validation
    DUPLICATE_PAYMENT = "duplicate_payment"
    APPROVAL_REQUIRED = "approval_required"
    BUDGET_CHECK = "budget_check"
    
    # Compliance validation
    TAX_ID_VALID = "tax_id_valid"
    COMPLIANCE_FLAGS = "compliance_flags"
    RETENTION_POLICY = "retention_policy"
    
    # Data integrity validation
    REQUIRED_FIELDS = "required_fields"
    DATE_CONSISTENCY = "date_consistency"
    STATUS_CONSISTENCY = "status_consistency"


@dataclass
class ValidationResult:
    """Payment validation result."""
    is_valid: bool
    errors: List[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = None
    info: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.info is None:
            self.info = []
    
    def add_error(self, rule: ValidationRule, message: str, field: str = None, value: Any = None):
        """Add validation error."""
        self.errors.append({
            "rule": rule.value,
            "message": message,
            "field": field,
            "value": str(value) if value is not None else None,
            "severity": ValidationSeverity.ERROR.value,
            "timestamp": datetime.now()
        })
        self.is_valid = False
    
    def add_warning(self, rule: ValidationRule, message: str, field: str = None, value: Any = None):
        """Add validation warning."""
        self.warnings.append({
            "rule": rule.value,
            "message": message,
            "field": field,
            "value": str(value) if value is not None else None,
            "severity": ValidationSeverity.WARNING.value,
            "timestamp": datetime.now()
        })
    
    def add_info(self, rule: ValidationRule, message: str, field: str = None, value: Any = None):
        """Add validation info."""
        self.info.append({
            "rule": rule.value,
            "message": message,
            "field": field,
            "value": str(value) if value is not None else None,
            "severity": ValidationSeverity.INFO.value,
            "timestamp": datetime.now()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "total_issues": len(self.errors) + len(self.warnings) + len(self.info)
        }


class PaymentValidator:
    """Comprehensive payment validation system."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.validation_rules = self._initialize_validation_rules()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration."""
        return {
            "amount_limits": {
                "min_amount": Decimal("0.01"),
                "max_amount": Decimal("100000.00"),
                "auto_approval_threshold": Decimal("1000.00")
            },
            "recipient_validation": {
                "require_account_info": True,
                "require_tax_id_for_large_amounts": Decimal("10000.00")
            },
            "business_rules": {
                "max_daily_amount_per_recipient": Decimal("50000.00"),
                "duplicate_payment_window_days": 30,
                "approval_required_threshold": Decimal("5000.00")
            },
            "compliance": {
                "require_tax_id": True,
                "tax_id_threshold": Decimal("600.00"),
                "retention_years": 7
            }
        }
    
    def _initialize_validation_rules(self) -> Dict[ValidationRule, callable]:
        """Initialize validation rules."""
        return {
            ValidationRule.AMOUNT_POSITIVE: self._validate_amount_positive,
            ValidationRule.AMOUNT_WITHIN_LIMITS: self._validate_amount_limits,
            ValidationRule.AMOUNT_REASONABLE: self._validate_amount_reasonable,
            ValidationRule.RECIPIENT_EMAIL_VALID: self._validate_recipient_email,
            ValidationRule.RECIPIENT_NAME_REQUIRED: self._validate_recipient_name,
            ValidationRule.RECIPIENT_ACCOUNT_VALID: self._validate_recipient_account,
            ValidationRule.DUPLICATE_PAYMENT: self._validate_duplicate_payment,
            ValidationRule.APPROVAL_REQUIRED: self._validate_approval_required,
            ValidationRule.BUDGET_CHECK: self._validate_budget_check,
            ValidationRule.TAX_ID_VALID: self._validate_tax_id,
            ValidationRule.COMPLIANCE_FLAGS: self._validate_compliance_flags,
            ValidationRule.RETENTION_POLICY: self._validate_retention_policy,
            ValidationRule.REQUIRED_FIELDS: self._validate_required_fields,
            ValidationRule.DATE_CONSISTENCY: self._validate_date_consistency,
            ValidationRule.STATUS_CONSISTENCY: self._validate_status_consistency
        }
    
    def validate_payment(self, payment: PaymentTrackingLog, 
                        existing_payments: List[PaymentTrackingLog] = None) -> ValidationResult:
        """Validate a payment comprehensively."""
        result = ValidationResult(is_valid=True)
        existing_payments = existing_payments or []
        
        # Run all validation rules
        for rule, validator_func in self.validation_rules.items():
            try:
                validator_func(payment, result, existing_payments)
            except Exception as e:
                logger.error(f"Error in validation rule {rule.value}: {e}")
                result.add_error(rule, f"Validation error: {str(e)}")
        
        return result
    
    def _validate_amount_positive(self, payment: PaymentTrackingLog, result: ValidationResult, 
                                 existing_payments: List[PaymentTrackingLog]):
        """Validate payment amount is positive."""
        if payment.amount <= 0:
            result.add_error(
                ValidationRule.AMOUNT_POSITIVE,
                "Payment amount must be positive",
                "amount",
                payment.amount
            )
    
    def _validate_amount_limits(self, payment: PaymentTrackingLog, result: ValidationResult,
                               existing_payments: List[PaymentTrackingLog]):
        """Validate payment amount is within configured limits."""
        min_amount = self.config["amount_limits"]["min_amount"]
        max_amount = self.config["amount_limits"]["max_amount"]
        
        if payment.amount < min_amount:
            result.add_error(
                ValidationRule.AMOUNT_WITHIN_LIMITS,
                f"Payment amount below minimum: ${min_amount}",
                "amount",
                payment.amount
            )
        elif payment.amount > max_amount:
            result.add_error(
                ValidationRule.AMOUNT_WITHIN_LIMITS,
                f"Payment amount above maximum: ${max_amount}",
                "amount",
                payment.amount
            )
    
    def _validate_amount_reasonable(self, payment: PaymentTrackingLog, result: ValidationResult,
                                   existing_payments: List[PaymentTrackingLog]):
        """Validate payment amount is reasonable for the type."""
        # Check for unusually large amounts
        if payment.amount > Decimal("50000.00"):
            result.add_warning(
                ValidationRule.AMOUNT_REASONABLE,
                "Large payment amount - may require additional approval",
                "amount",
                payment.amount
            )
        
        # Check for round numbers (potential data entry errors)
        if payment.amount % Decimal("1000") == 0 and payment.amount > Decimal("10000"):
            result.add_warning(
                ValidationRule.AMOUNT_REASONABLE,
                "Round number amount - please verify accuracy",
                "amount",
                payment.amount
            )
    
    def _validate_recipient_email(self, payment: PaymentTrackingLog, result: ValidationResult,
                                 existing_payments: List[PaymentTrackingLog]):
        """Validate recipient email format."""
        email = payment.recipient.email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            result.add_error(
                ValidationRule.RECIPIENT_EMAIL_VALID,
                "Invalid email format",
                "recipient.email",
                email
            )
    
    def _validate_recipient_name(self, payment: PaymentTrackingLog, result: ValidationResult,
                                existing_payments: List[PaymentTrackingLog]):
        """Validate recipient name is provided."""
        if not payment.recipient.name or payment.recipient.name.strip() == "":
            result.add_error(
                ValidationRule.RECIPIENT_NAME_REQUIRED,
                "Recipient name is required",
                "recipient.name"
            )
    
    def _validate_recipient_account(self, payment: PaymentTrackingLog, result: ValidationResult,
                                   existing_payments: List[PaymentTrackingLog]):
        """Validate recipient account information."""
        # Make account validation optional for now - just warn if missing
        if payment.payment_method in [PaymentMethod.BANK_TRANSFER, PaymentMethod.ACH, PaymentMethod.WIRE_TRANSFER]:
            if not payment.recipient.account_number:
                result.add_warning(
                    ValidationRule.RECIPIENT_ACCOUNT_VALID,
                    "Account number recommended for bank transfers",
                    "recipient.account_number"
                )
            if not payment.recipient.routing_number:
                result.add_warning(
                    ValidationRule.RECIPIENT_ACCOUNT_VALID,
                    "Routing number recommended for bank transfers",
                    "recipient.routing_number"
                )
    
    def _validate_duplicate_payment(self, payment: PaymentTrackingLog, result: ValidationResult,
                                   existing_payments: List[PaymentTrackingLog]):
        """Validate no duplicate payments."""
        window_days = self.config["business_rules"]["duplicate_payment_window_days"]
        cutoff_date = datetime.now() - timedelta(days=window_days)
        
        for existing_payment in existing_payments:
            if (existing_payment.payment_id != payment.payment_id and
                existing_payment.recipient.email == payment.recipient.email and
                existing_payment.amount == payment.amount and
                existing_payment.created_at >= cutoff_date):
                
                result.add_error(
                    ValidationRule.DUPLICATE_PAYMENT,
                    f"Potential duplicate payment found: {existing_payment.payment_id}",
                    "payment_id",
                    payment.payment_id
                )
                break
    
    def _validate_approval_required(self, payment: PaymentTrackingLog, result: ValidationResult,
                                   existing_payments: List[PaymentTrackingLog]):
        """Validate approval requirements."""
        threshold = self.config["business_rules"]["approval_required_threshold"]
        
        if payment.amount > threshold and payment.approval_status == ApprovalStatus.PENDING_APPROVAL:
            result.add_info(
                ValidationRule.APPROVAL_REQUIRED,
                f"Payment requires approval (amount > ${threshold})",
                "approval_status"
            )
    
    def _validate_budget_check(self, payment: PaymentTrackingLog, result: ValidationResult,
                              existing_payments: List[PaymentTrackingLog]):
        """Validate budget constraints."""
        # Check daily amount per recipient
        max_daily_amount = self.config["business_rules"]["max_daily_amount_per_recipient"]
        today = date.today()
        
        daily_amount = sum(
            p.amount for p in existing_payments
            if (p.recipient.email == payment.recipient.email and
                p.created_at.date() == today and
                p.payment_id != payment.payment_id)
        )
        
        if daily_amount + payment.amount > max_daily_amount:
            result.add_warning(
                ValidationRule.BUDGET_CHECK,
                f"Daily amount limit exceeded for recipient: ${daily_amount + payment.amount}",
                "amount"
            )
    
    def _validate_tax_id(self, payment: PaymentTrackingLog, result: ValidationResult,
                        existing_payments: List[PaymentTrackingLog]):
        """Validate tax ID requirements."""
        if self.config["compliance"]["require_tax_id"]:
            threshold = self.config["compliance"]["tax_id_threshold"]
            
            if payment.amount >= threshold and not payment.recipient.tax_id:
                result.add_error(
                    ValidationRule.TAX_ID_VALID,
                    f"Tax ID required for payments >= ${threshold}",
                    "recipient.tax_id"
                )
    
    def _validate_compliance_flags(self, payment: PaymentTrackingLog, result: ValidationResult,
                                  existing_payments: List[PaymentTrackingLog]):
        """Validate compliance flags."""
        # Check for suspicious patterns
        if payment.amount > Decimal("10000.00") and not payment.business_purpose:
            result.add_warning(
                ValidationRule.COMPLIANCE_FLAGS,
                "Business purpose recommended for large payments",
                "business_purpose"
            )
        
        # Check for weekend/holiday payments
        if payment.created_at.weekday() >= 5:  # Weekend
            result.add_info(
                ValidationRule.COMPLIANCE_FLAGS,
                "Payment created on weekend",
                "created_at"
            )
    
    def _validate_retention_policy(self, payment: PaymentTrackingLog, result: ValidationResult,
                                  existing_payments: List[PaymentTrackingLog]):
        """Validate retention policy compliance."""
        retention_years = self.config["compliance"]["retention_years"]
        retention_date = payment.created_at.date() + timedelta(days=retention_years * 365)
        
        if payment.retention_date and payment.retention_date != retention_date:
            result.add_warning(
                ValidationRule.RETENTION_POLICY,
                f"Retention date should be {retention_date}",
                "retention_date"
            )
    
    def _validate_required_fields(self, payment: PaymentTrackingLog, result: ValidationResult,
                                 existing_payments: List[PaymentTrackingLog]):
        """Validate required fields are present."""
        required_fields = [
            ("payment_id", payment.payment_id),
            ("amount", payment.amount),
            ("recipient", payment.recipient),
            ("payment_type", payment.payment_type),
            ("payment_method", payment.payment_method)
        ]
        
        for field_name, field_value in required_fields:
            if not field_value:
                result.add_error(
                    ValidationRule.REQUIRED_FIELDS,
                    f"Required field missing: {field_name}",
                    field_name
                )
    
    def _validate_date_consistency(self, payment: PaymentTrackingLog, result: ValidationResult,
                                  existing_payments: List[PaymentTrackingLog]):
        """Validate date consistency."""
        # Check that submitted_at is after created_at
        if payment.submitted_at and payment.submitted_at < payment.created_at:
            result.add_error(
                ValidationRule.DATE_CONSISTENCY,
                "Submitted date cannot be before created date",
                "submitted_at"
            )
        
        # Check that approved_at is after submitted_at
        if (payment.approved_at and payment.submitted_at and 
            payment.approved_at < payment.submitted_at):
            result.add_error(
                ValidationRule.DATE_CONSISTENCY,
                "Approved date cannot be before submitted date",
                "approved_at"
            )
        
        # Check that disbursed_at is after approved_at
        if (payment.disbursed_at and payment.approved_at and
            payment.disbursed_at < payment.approved_at):
            result.add_error(
                ValidationRule.DATE_CONSISTENCY,
                "Disbursed date cannot be before approved date",
                "disbursed_at"
            )
    
    def _validate_status_consistency(self, payment: PaymentTrackingLog, result: ValidationResult,
                                    existing_payments: List[PaymentTrackingLog]):
        """Validate status consistency."""
        # Check that disbursed payments have approval
        if (payment.current_status == PaymentStatus.DISBURSED and
            payment.approval_status != ApprovalStatus.APPROVED):
            result.add_error(
                ValidationRule.STATUS_CONSISTENCY,
                "Disbursed payments must be approved",
                "approval_status"
            )
        
        # Check that received payments were disbursed
        if (payment.current_status == PaymentStatus.RECEIVED and
            payment.current_status != PaymentStatus.DISBURSED):
            result.add_warning(
                ValidationRule.STATUS_CONSISTENCY,
                "Received payments should have been disbursed first",
                "current_status"
            )


class PaymentReconciler:
    """Payment reconciliation system."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default reconciliation configuration."""
        return {
            "tolerance_amount": Decimal("0.01"),
            "tolerance_percentage": Decimal("0.1"),
            "auto_reconcile_threshold": Decimal("1000.00"),
            "require_manual_review": True
        }
    
    def reconcile_payment(self, payment: PaymentTrackingLog, 
                         bank_statement_amount: Decimal,
                         bank_statement_date: date,
                         bank_reference: str = None) -> Dict[str, Any]:
        """Reconcile payment with bank statement."""
        reconciliation_result = {
            "payment_id": payment.payment_id,
            "reconciliation_status": ReconciliationStatus.NOT_RECONCILED,
            "discrepancy_amount": Decimal("0"),
            "discrepancy_reason": None,
            "requires_manual_review": False,
            "auto_reconciled": False
        }
        
        # Calculate discrepancy
        expected_amount = payment.amount
        actual_amount = bank_statement_amount
        discrepancy = abs(expected_amount - actual_amount)
        
        # Check if within tolerance
        tolerance_amount = self.config["tolerance_amount"]
        tolerance_percentage = self.config["tolerance_percentage"]
        
        is_within_tolerance = (
            discrepancy <= tolerance_amount or
            discrepancy <= (expected_amount * tolerance_percentage / 100)
        )
        
        if is_within_tolerance:
            # Auto-reconcile if within threshold
            if payment.amount <= self.config["auto_reconcile_threshold"]:
                reconciliation_result["reconciliation_status"] = ReconciliationStatus.RECONCILED
                reconciliation_result["auto_reconciled"] = True
            else:
                reconciliation_result["reconciliation_status"] = ReconciliationStatus.PENDING_RECONCILIATION
                reconciliation_result["requires_manual_review"] = True
        else:
            # Discrepancy found
            reconciliation_result["reconciliation_status"] = ReconciliationStatus.DISCREPANCY
            reconciliation_result["discrepancy_amount"] = discrepancy
            reconciliation_result["discrepancy_reason"] = "Amount mismatch"
            reconciliation_result["requires_manual_review"] = True
        
        # Check date consistency
        if payment.due_date and bank_statement_date != payment.due_date:
            if reconciliation_result["discrepancy_reason"]:
                reconciliation_result["discrepancy_reason"] += "; Date mismatch"
            else:
                reconciliation_result["discrepancy_reason"] = "Date mismatch"
        
        return reconciliation_result
    
    def batch_reconcile_payments(self, payments: List[PaymentTrackingLog],
                                bank_statement_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reconcile multiple payments with bank statement data."""
        reconciliation_summary = {
            "total_payments": len(payments),
            "reconciled": 0,
            "pending": 0,
            "discrepancies": 0,
            "auto_reconciled": 0,
            "requires_review": 0,
            "total_discrepancy_amount": Decimal("0"),
            "reconciliation_results": []
        }
        
        # Create lookup for bank statement data
        bank_data_lookup = {}
        for bank_entry in bank_statement_data:
            key = bank_entry.get("reference") or bank_entry.get("description", "")
            bank_data_lookup[key] = bank_entry
        
        for payment in payments:
            # Try to find matching bank entry
            bank_entry = None
            for key, entry in bank_data_lookup.items():
                if (payment.payment_id in key or
                    payment.reference_number in key or
                    str(payment.amount) in key):
                    bank_entry = entry
                    break
            
            if bank_entry:
                result = self.reconcile_payment(
                    payment,
                    Decimal(str(bank_entry["amount"])),
                    bank_entry["date"],
                    bank_entry.get("reference")
                )
                
                reconciliation_summary["reconciliation_results"].append(result)
                
                # Update summary counts
                if result["reconciliation_status"] == ReconciliationStatus.RECONCILED:
                    reconciliation_summary["reconciled"] += 1
                elif result["reconciliation_status"] == ReconciliationStatus.PENDING_RECONCILIATION:
                    reconciliation_summary["pending"] += 1
                elif result["reconciliation_status"] == ReconciliationStatus.DISCREPANCY:
                    reconciliation_summary["discrepancies"] += 1
                    reconciliation_summary["total_discrepancy_amount"] += result["discrepancy_amount"]
                
                if result["auto_reconciled"]:
                    reconciliation_summary["auto_reconciled"] += 1
                
                if result["requires_manual_review"]:
                    reconciliation_summary["requires_review"] += 1
            else:
                # No matching bank entry found
                reconciliation_summary["reconciliation_results"].append({
                    "payment_id": payment.payment_id,
                    "reconciliation_status": ReconciliationStatus.NOT_RECONCILED,
                    "discrepancy_reason": "No matching bank entry found"
                })
        
        return reconciliation_summary
    
    def generate_reconciliation_report(self, reconciliation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate reconciliation report."""
        report = {
            "report_generated_at": datetime.now(),
            "total_payments": len(reconciliation_results),
            "reconciled_count": 0,
            "pending_count": 0,
            "discrepancy_count": 0,
            "not_reconciled_count": 0,
            "total_discrepancy_amount": Decimal("0"),
            "discrepancy_details": [],
            "recommendations": []
        }
        
        for result in reconciliation_results:
            status = result["reconciliation_status"]
            
            if status == ReconciliationStatus.RECONCILED:
                report["reconciled_count"] += 1
            elif status == ReconciliationStatus.PENDING_RECONCILIATION:
                report["pending_count"] += 1
            elif status == ReconciliationStatus.DISCREPANCY:
                report["discrepancy_count"] += 1
                report["total_discrepancy_amount"] += result.get("discrepancy_amount", 0)
                report["discrepancy_details"].append({
                    "payment_id": result["payment_id"],
                    "discrepancy_amount": float(result.get("discrepancy_amount", 0)),
                    "reason": result.get("discrepancy_reason")
                })
            else:
                report["not_reconciled_count"] += 1
        
        # Generate recommendations
        if report["discrepancy_count"] > 0:
            report["recommendations"].append("Review discrepancies and investigate root causes")
        
        if report["not_reconciled_count"] > report["total_payments"] * 0.1:  # More than 10%
            report["recommendations"].append("High number of unreconciled payments - review matching criteria")
        
        if report["total_discrepancy_amount"] > Decimal("1000"):
            report["recommendations"].append("Significant discrepancy amount - requires immediate attention")
        
        return report
