"""
Payment Reporting and Analytics System.

This module provides comprehensive reporting, analytics, and business intelligence
for payment processing operations.
"""

import json
import csv
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from .payment_models import (
    PaymentTrackingLog, PaymentStatus, PaymentMethod, PaymentType,
    ApprovalStatus, PaymentPriority, PaymentReport
)
from .payment_storage import PaymentStorageManager

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Types of payment reports."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    ANALYTICS = "analytics"
    COMPLIANCE = "compliance"
    RECONCILIATION = "reconciliation"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    TREND = "trend"


class ReportFormat(str, Enum):
    """Report output formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


@dataclass
class ReportFilter:
    """Report filtering criteria."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    payment_status: Optional[List[PaymentStatus]] = None
    payment_method: Optional[List[PaymentMethod]] = None
    payment_type: Optional[List[PaymentType]] = None
    approval_status: Optional[List[ApprovalStatus]] = None
    priority: Optional[List[PaymentPriority]] = None
    department: Optional[List[str]] = None
    project_code: Optional[List[str]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    recipient_email: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_overdue: Optional[bool] = None
    requires_approval: Optional[bool] = None


@dataclass
class ReportMetrics:
    """Report metrics and KPIs."""
    total_payments: int = 0
    total_amount: Decimal = Decimal('0')
    average_amount: Decimal = Decimal('0')
    median_amount: Decimal = Decimal('0')
    min_amount: Decimal = Decimal('0')
    max_amount: Decimal = Decimal('0')
    
    # Status breakdown
    status_counts: Dict[str, int] = field(default_factory=dict)
    status_amounts: Dict[str, Decimal] = field(default_factory=dict)
    
    # Method breakdown
    method_counts: Dict[str, int] = field(default_factory=dict)
    method_amounts: Dict[str, Decimal] = field(default_factory=dict)
    
    # Type breakdown
    type_counts: Dict[str, int] = field(default_factory=dict)
    type_amounts: Dict[str, Decimal] = field(default_factory=dict)
    
    # Approval metrics
    approval_rate: float = 0.0
    average_approval_time_hours: float = 0.0
    rejection_rate: float = 0.0
    
    # Processing metrics
    average_processing_time_hours: float = 0.0
    disbursement_rate: float = 0.0
    error_rate: float = 0.0
    
    # Compliance metrics
    overdue_count: int = 0
    overdue_amount: Decimal = Decimal('0')
    compliance_violations: int = 0
    
    # Trend metrics
    daily_volume: Dict[str, int] = field(default_factory=dict)
    daily_amounts: Dict[str, Decimal] = field(default_factory=dict)
    weekly_volume: Dict[str, int] = field(default_factory=dict)
    monthly_volume: Dict[str, int] = field(default_factory=dict)


class PaymentReporter:
    """Comprehensive payment reporting system."""
    
    def __init__(self, storage_manager: PaymentStorageManager):
        self.storage_manager = storage_manager
        self.report_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def generate_summary_report(self, filters: ReportFilter = None) -> PaymentReport:
        """Generate payment summary report."""
        try:
            # Get filtered payments
            payments = self._get_filtered_payments(filters)
            
            # Create report
            report = PaymentReport(
                report_id=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_name="Payment Summary Report",
                report_type=ReportType.SUMMARY.value,
                generated_by="Payment Reporter",
                start_date=filters.start_date or date.today() - timedelta(days=30),
                end_date=filters.end_date or date.today(),
                filters=self._filters_to_dict(filters) if filters else {}
            )
            
            # Calculate metrics
            metrics = self._calculate_metrics(payments)
            
            # Add payment data
            for payment in payments:
                report.add_payment_data(payment)
            
            # Set summary data
            report.summary_data = {
                "metrics": self._metrics_to_dict(metrics),
                "generated_at": report.generated_at,
                "period": f"{report.start_date} to {report.end_date}",
                "filter_summary": self._get_filter_summary(filters)
            }
            
            # Calculate report metrics
            report.calculate_metrics()
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise
    
    def generate_analytics_report(self, filters: ReportFilter = None) -> PaymentReport:
        """Generate payment analytics report."""
        try:
            payments = self._get_filtered_payments(filters)
            
            report = PaymentReport(
                report_id=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_name="Payment Analytics Report",
                report_type=ReportType.ANALYTICS.value,
                generated_by="Payment Reporter",
                start_date=filters.start_date if filters and filters.start_date else date.today() - timedelta(days=30),
                end_date=filters.end_date if filters and filters.end_date else date.today(),
                filters=self._filters_to_dict(filters) if filters else {}
            )
            
            # Calculate detailed analytics
            analytics = self._calculate_analytics(payments)
            
            # Add payment data
            for payment in payments:
                report.add_payment_data(payment)
            
            # Set analytics data
            report.summary_data = {
                "analytics": analytics,
                "trends": self._calculate_trends(payments),
                "forecasts": self._calculate_forecasts(payments),
                "insights": self._generate_insights(analytics, payments),
                "recommendations": self._generate_recommendations(analytics, payments)
            }
            
            report.calculate_metrics()
            return report
            
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            raise
    
    def generate_compliance_report(self, filters: ReportFilter = None) -> PaymentReport:
        """Generate compliance report."""
        try:
            payments = self._get_filtered_payments(filters)
            
            report = PaymentReport(
                report_id=f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_name="Payment Compliance Report",
                report_type=ReportType.COMPLIANCE.value,
                generated_by="Payment Reporter",
                start_date=filters.start_date or date.today() - timedelta(days=30),
                end_date=filters.end_date or date.today(),
                filters=self._filters_to_dict(filters) if filters else {}
            )
            
            # Calculate compliance metrics
            compliance_data = self._calculate_compliance_metrics(payments)
            
            # Add payment data
            for payment in payments:
                report.add_payment_data(payment)
            
            # Set compliance data
            report.summary_data = {
                "compliance_metrics": compliance_data,
                "violations": self._identify_compliance_violations(payments),
                "audit_trail": self._extract_audit_trail(payments),
                "retention_status": self._check_retention_compliance(payments),
                "regulatory_requirements": self._check_regulatory_requirements(payments)
            }
            
            report.calculate_metrics()
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    def generate_reconciliation_report(self, filters: ReportFilter = None) -> PaymentReport:
        """Generate reconciliation report."""
        try:
            payments = self._get_filtered_payments(filters)
            
            report = PaymentReport(
                report_id=f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_name="Payment Reconciliation Report",
                report_type=ReportType.RECONCILIATION.value,
                generated_by="Payment Reporter",
                start_date=filters.start_date or date.today() - timedelta(days=30),
                end_date=filters.end_date or date.today(),
                filters=self._filters_to_dict(filters) if filters else {}
            )
            
            # Calculate reconciliation metrics
            reconciliation_data = self._calculate_reconciliation_metrics(payments)
            
            # Add payment data
            for payment in payments:
                report.add_payment_data(payment)
            
            # Set reconciliation data
            report.summary_data = {
                "reconciliation_metrics": reconciliation_data,
                "unreconciled_payments": self._get_unreconciled_payments(payments),
                "discrepancies": self._get_reconciliation_discrepancies(payments),
                "bank_statement_matches": self._get_bank_statement_matches(payments),
                "reconciliation_recommendations": self._get_reconciliation_recommendations(payments)
            }
            
            report.calculate_metrics()
            return report
            
        except Exception as e:
            logger.error(f"Error generating reconciliation report: {e}")
            raise
    
    def generate_audit_report(self, filters: ReportFilter = None) -> PaymentReport:
        """Generate audit report."""
        try:
            payments = self._get_filtered_payments(filters)
            
            report = PaymentReport(
                report_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_name="Payment Audit Report",
                report_type=ReportType.AUDIT.value,
                generated_by="Payment Reporter",
                start_date=filters.start_date or date.today() - timedelta(days=30),
                end_date=filters.end_date or date.today(),
                filters=self._filters_to_dict(filters) if filters else {}
            )
            
            # Calculate audit metrics
            audit_data = self._calculate_audit_metrics(payments)
            
            # Add payment data
            for payment in payments:
                report.add_payment_data(payment)
            
            # Set audit data
            report.summary_data = {
                "audit_metrics": audit_data,
                "audit_trail": self._extract_comprehensive_audit_trail(payments),
                "access_logs": self._extract_access_logs(payments),
                "data_integrity": self._check_data_integrity(payments),
                "security_events": self._identify_security_events(payments),
                "compliance_audit": self._perform_compliance_audit(payments)
            }
            
            report.calculate_metrics()
            return report
            
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            raise
    
    def _get_filtered_payments(self, filters: ReportFilter = None) -> List[PaymentTrackingLog]:
        """Get payments filtered by criteria."""
        try:
            if not filters:
                # Get all payments
                data = self.storage_manager._load_data()
                return list(data.get("payments", {}).values())
            
            payments = []
            
            # Apply date filter
            if filters.start_date or filters.end_date:
                start_date = filters.start_date or date.min
                end_date = filters.end_date or date.max
                payments = self.storage_manager.get_payments_by_date_range(start_date, end_date)
            else:
                data = self.storage_manager._load_data()
                payments = list(data.get("payments", {}).values())
            
            # Apply additional filters
            filtered_payments = []
            for payment in payments:
                if self._payment_matches_filters(payment, filters):
                    filtered_payments.append(payment)
            
            return filtered_payments
            
        except Exception as e:
            logger.error(f"Error getting filtered payments: {e}")
            return []
    
    def _payment_matches_filters(self, payment: PaymentTrackingLog, filters: ReportFilter) -> bool:
        """Check if payment matches filter criteria."""
        try:
            # Status filter
            if filters.payment_status and payment.current_status not in filters.payment_status:
                return False
            
            # Method filter
            if filters.payment_method and payment.payment_method not in filters.payment_method:
                return False
            
            # Type filter
            if filters.payment_type and payment.payment_type not in filters.payment_type:
                return False
            
            # Approval status filter
            if filters.approval_status and payment.approval_status not in filters.approval_status:
                return False
            
            # Priority filter
            if filters.priority and payment.payment_priority not in filters.priority:
                return False
            
            # Department filter
            if filters.department and payment.department not in filters.department:
                return False
            
            # Project code filter
            if filters.project_code and payment.project_code not in filters.project_code:
                return False
            
            # Amount range filter
            if filters.min_amount and payment.amount < filters.min_amount:
                return False
            if filters.max_amount and payment.amount > filters.max_amount:
                return False
            
            # Recipient email filter
            if filters.recipient_email and payment.recipient.email not in filters.recipient_email:
                return False
            
            # Tags filter
            if filters.tags and not any(tag in payment.tags for tag in filters.tags):
                return False
            
            # Overdue filter
            if filters.is_overdue is not None and payment.is_overdue() != filters.is_overdue:
                return False
            
            # Approval required filter
            if filters.requires_approval is not None and payment.requires_approval() != filters.requires_approval:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking payment filters: {e}")
            return False
    
    def _calculate_metrics(self, payments: List[PaymentTrackingLog]) -> ReportMetrics:
        """Calculate comprehensive payment metrics."""
        metrics = ReportMetrics()
        
        if not payments:
            return metrics
        
        # Basic counts and amounts
        metrics.total_payments = len(payments)
        amounts = [p.amount for p in payments]
        metrics.total_amount = sum(amounts)
        metrics.average_amount = metrics.total_amount / metrics.total_payments
        metrics.min_amount = min(amounts)
        metrics.max_amount = max(amounts)
        
        # Calculate median
        sorted_amounts = sorted(amounts)
        n = len(sorted_amounts)
        if n % 2 == 0:
            metrics.median_amount = (sorted_amounts[n//2-1] + sorted_amounts[n//2]) / 2
        else:
            metrics.median_amount = sorted_amounts[n//2]
        
        # Status breakdown
        for payment in payments:
            status = payment.current_status.value if hasattr(payment.current_status, 'value') else str(payment.current_status)
            metrics.status_counts[status] = metrics.status_counts.get(status, 0) + 1
            metrics.status_amounts[status] = metrics.status_amounts.get(status, Decimal('0')) + payment.amount
        
        # Method breakdown
        for payment in payments:
            method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
            metrics.method_counts[method] = metrics.method_counts.get(method, 0) + 1
            metrics.method_amounts[method] = metrics.method_amounts.get(method, Decimal('0')) + payment.amount
        
        # Type breakdown
        for payment in payments:
            payment_type = payment.payment_type.value if hasattr(payment.payment_type, 'value') else str(payment.payment_type)
            metrics.type_counts[payment_type] = metrics.type_counts.get(payment_type, 0) + 1
            metrics.type_amounts[payment_type] = metrics.type_amounts.get(payment_type, Decimal('0')) + payment.amount
        
        # Approval metrics
        approved_count = sum(1 for p in payments if p.approval_status == ApprovalStatus.APPROVED)
        rejected_count = sum(1 for p in payments if p.approval_status == ApprovalStatus.REJECTED)
        metrics.approval_rate = (approved_count / metrics.total_payments) * 100 if metrics.total_payments > 0 else 0
        metrics.rejection_rate = (rejected_count / metrics.total_payments) * 100 if metrics.total_payments > 0 else 0
        
        # Processing metrics
        disbursed_count = sum(1 for p in payments if p.current_status == PaymentStatus.DISBURSED)
        failed_count = sum(1 for p in payments if p.current_status == PaymentStatus.FAILED)
        metrics.disbursement_rate = (disbursed_count / metrics.total_payments) * 100 if metrics.total_payments > 0 else 0
        metrics.error_rate = (failed_count / metrics.total_payments) * 100 if metrics.total_payments > 0 else 0
        
        # Overdue metrics
        overdue_payments = [p for p in payments if p.is_overdue()]
        metrics.overdue_count = len(overdue_payments)
        metrics.overdue_amount = sum(p.amount for p in overdue_payments)
        
        return metrics
    
    def _calculate_analytics(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate detailed analytics."""
        analytics = {
            "volume_trends": self._calculate_volume_trends(payments),
            "amount_distribution": self._calculate_amount_distribution(payments),
            "processing_efficiency": self._calculate_processing_efficiency(payments),
            "approval_patterns": self._calculate_approval_patterns(payments),
            "recipient_analysis": self._calculate_recipient_analysis(payments),
            "department_analysis": self._calculate_department_analysis(payments),
            "seasonal_patterns": self._calculate_seasonal_patterns(payments),
            "anomaly_detection": self._detect_anomalies(payments)
        }
        return analytics
    
    def _calculate_volume_trends(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate volume trends."""
        daily_volume = {}
        weekly_volume = {}
        monthly_volume = {}
        
        for payment in payments:
            payment_date = payment.created_at.date()
            
            # Daily
            day_key = payment_date.strftime('%Y-%m-%d')
            daily_volume[day_key] = daily_volume.get(day_key, 0) + 1
            
            # Weekly
            week_key = payment_date.strftime('%Y-W%U')
            weekly_volume[week_key] = weekly_volume.get(week_key, 0) + 1
            
            # Monthly
            month_key = payment_date.strftime('%Y-%m')
            monthly_volume[month_key] = monthly_volume.get(month_key, 0) + 1
        
        return {
            "daily": daily_volume,
            "weekly": weekly_volume,
            "monthly": monthly_volume
        }
    
    def _calculate_amount_distribution(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate amount distribution analysis."""
        amounts = [float(p.amount) for p in payments]
        
        # Amount ranges
        ranges = {
            "0-100": 0,
            "100-500": 0,
            "500-1000": 0,
            "1000-5000": 0,
            "5000-10000": 0,
            "10000+": 0
        }
        
        for amount in amounts:
            if amount < 100:
                ranges["0-100"] += 1
            elif amount < 500:
                ranges["100-500"] += 1
            elif amount < 1000:
                ranges["500-1000"] += 1
            elif amount < 5000:
                ranges["1000-5000"] += 1
            elif amount < 10000:
                ranges["5000-10000"] += 1
            else:
                ranges["10000+"] += 1
        
        return {
            "ranges": ranges,
            "percentiles": {
                "25th": self._percentile(amounts, 25),
                "50th": self._percentile(amounts, 50),
                "75th": self._percentile(amounts, 75),
                "90th": self._percentile(amounts, 90),
                "95th": self._percentile(amounts, 95),
                "99th": self._percentile(amounts, 99)
            }
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _calculate_processing_efficiency(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate processing efficiency metrics."""
        processing_times = []
        approval_times = []
        
        for payment in payments:
            # Processing time
            if payment.disbursed_at and payment.submitted_at:
                processing_time = (payment.disbursed_at - payment.submitted_at).total_seconds() / 3600
                processing_times.append(processing_time)
            
            # Approval time
            if payment.approved_at and payment.submitted_at:
                approval_time = (payment.approved_at - payment.submitted_at).total_seconds() / 3600
                approval_times.append(approval_time)
        
        return {
            "average_processing_time_hours": sum(processing_times) / len(processing_times) if processing_times else 0,
            "average_approval_time_hours": sum(approval_times) / len(approval_times) if approval_times else 0,
            "processing_time_distribution": {
                "min": min(processing_times) if processing_times else 0,
                "max": max(processing_times) if processing_times else 0,
                "median": self._percentile(processing_times, 50) if processing_times else 0
            }
        }
    
    def _calculate_approval_patterns(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate approval patterns."""
        approval_workflow = {}
        approval_times = []
        
        for payment in payments:
            for approval in payment.approval_workflow:
                approver = approval.approver_name
                approval_workflow[approver] = approval_workflow.get(approver, 0) + 1
                
                if approval.approval_date and payment.submitted_at:
                    approval_time = (approval.approval_date - payment.submitted_at).total_seconds() / 3600
                    approval_times.append(approval_time)
        
        return {
            "approver_workload": approval_workflow,
            "approval_time_distribution": {
                "average": sum(approval_times) / len(approval_times) if approval_times else 0,
                "min": min(approval_times) if approval_times else 0,
                "max": max(approval_times) if approval_times else 0
            }
        }
    
    def _calculate_recipient_analysis(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate recipient analysis."""
        recipient_stats = {}
        
        for payment in payments:
            email = payment.recipient.email
            if email not in recipient_stats:
                recipient_stats[email] = {
                    "count": 0,
                    "total_amount": Decimal('0'),
                    "name": payment.recipient.name
                }
            
            recipient_stats[email]["count"] += 1
            recipient_stats[email]["total_amount"] += payment.amount
        
        # Sort by total amount
        sorted_recipients = sorted(recipient_stats.items(), 
                                 key=lambda x: x[1]["total_amount"], reverse=True)
        
        return {
            "top_recipients": sorted_recipients[:10],
            "recipient_count": len(recipient_stats),
            "average_payments_per_recipient": len(payments) / len(recipient_stats) if recipient_stats else 0
        }
    
    def _calculate_department_analysis(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate department analysis."""
        department_stats = {}
        
        for payment in payments:
            dept = payment.department or "Unknown"
            if dept not in department_stats:
                department_stats[dept] = {
                    "count": 0,
                    "total_amount": Decimal('0')
                }
            
            department_stats[dept]["count"] += 1
            department_stats[dept]["total_amount"] += payment.amount
        
        return department_stats
    
    def _calculate_seasonal_patterns(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate seasonal patterns."""
        monthly_patterns = {}
        weekday_patterns = {}
        hour_patterns = {}
        
        for payment in payments:
            # Monthly patterns
            month = payment.created_at.month
            monthly_patterns[month] = monthly_patterns.get(month, 0) + 1
            
            # Weekday patterns
            weekday = payment.created_at.weekday()
            weekday_patterns[weekday] = weekday_patterns.get(weekday, 0) + 1
            
            # Hour patterns
            hour = payment.created_at.hour
            hour_patterns[hour] = hour_patterns.get(hour, 0) + 1
        
        return {
            "monthly": monthly_patterns,
            "weekday": weekday_patterns,
            "hourly": hour_patterns
        }
    
    def _detect_anomalies(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Detect payment anomalies."""
        anomalies = []
        amounts = [float(p.amount) for p in payments]
        
        if not amounts:
            return anomalies
        
        # Calculate statistical thresholds
        mean_amount = sum(amounts) / len(amounts)
        std_amount = (sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
        
        # Detect outliers (amounts > 3 standard deviations from mean)
        threshold = mean_amount + (3 * std_amount)
        
        for payment in payments:
            if float(payment.amount) > threshold:
                anomalies.append({
                    "payment_id": payment.payment_id,
                    "type": "high_amount",
                    "amount": float(payment.amount),
                    "threshold": threshold,
                    "description": f"Amount ${payment.amount} exceeds statistical threshold"
                })
        
        return anomalies
    
    def _filters_to_dict(self, filters: ReportFilter) -> Dict[str, Any]:
        """Convert filters to dictionary."""
        return {
            "start_date": filters.start_date.isoformat() if filters.start_date else None,
            "end_date": filters.end_date.isoformat() if filters.end_date else None,
            "payment_status": [s.value for s in filters.payment_status] if filters.payment_status else None,
            "payment_method": [m.value for m in filters.payment_method] if filters.payment_method else None,
            "payment_type": [t.value for t in filters.payment_type] if filters.payment_type else None,
            "approval_status": [a.value for a in filters.approval_status] if filters.approval_status else None,
            "priority": [p.value for p in filters.priority] if filters.priority else None,
            "department": filters.department,
            "project_code": filters.project_code,
            "min_amount": float(filters.min_amount) if filters.min_amount else None,
            "max_amount": float(filters.max_amount) if filters.max_amount else None,
            "recipient_email": filters.recipient_email,
            "tags": filters.tags,
            "is_overdue": filters.is_overdue,
            "requires_approval": filters.requires_approval
        }
    
    def _metrics_to_dict(self, metrics: ReportMetrics) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_payments": metrics.total_payments,
            "total_amount": float(metrics.total_amount),
            "average_amount": float(metrics.average_amount),
            "median_amount": float(metrics.median_amount),
            "min_amount": float(metrics.min_amount),
            "max_amount": float(metrics.max_amount),
            "status_counts": metrics.status_counts,
            "status_amounts": {k: float(v) for k, v in metrics.status_amounts.items()},
            "method_counts": metrics.method_counts,
            "method_amounts": {k: float(v) for k, v in metrics.method_amounts.items()},
            "type_counts": metrics.type_counts,
            "type_amounts": {k: float(v) for k, v in metrics.type_amounts.items()},
            "approval_rate": metrics.approval_rate,
            "rejection_rate": metrics.rejection_rate,
            "disbursement_rate": metrics.disbursement_rate,
            "error_rate": metrics.error_rate,
            "overdue_count": metrics.overdue_count,
            "overdue_amount": float(metrics.overdue_amount)
        }
    
    def _get_filter_summary(self, filters: ReportFilter) -> str:
        """Get human-readable filter summary."""
        if not filters:
            return "No filters applied"
        
        summary_parts = []
        
        if filters.start_date and filters.end_date:
            summary_parts.append(f"Date range: {filters.start_date} to {filters.end_date}")
        elif filters.start_date:
            summary_parts.append(f"From: {filters.start_date}")
        elif filters.end_date:
            summary_parts.append(f"Until: {filters.end_date}")
        
        if filters.payment_status:
            summary_parts.append(f"Status: {', '.join(s.value for s in filters.payment_status)}")
        
        if filters.min_amount or filters.max_amount:
            amount_range = []
            if filters.min_amount:
                amount_range.append(f"≥${filters.min_amount}")
            if filters.max_amount:
                amount_range.append(f"≤${filters.max_amount}")
            summary_parts.append(f"Amount: {' '.join(amount_range)}")
        
        return "; ".join(summary_parts) if summary_parts else "No filters applied"
    
    # Placeholder methods for additional report types
    def _calculate_trends(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate trend analysis."""
        return {"trends": "Not implemented"}
    
    def _calculate_forecasts(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate forecasting."""
        return {"forecasts": "Not implemented"}
    
    def _generate_insights(self, analytics: Dict[str, Any], payments: List[PaymentTrackingLog]) -> List[str]:
        """Generate business insights."""
        return ["Insights generation not implemented"]
    
    def _generate_recommendations(self, analytics: Dict[str, Any], payments: List[PaymentTrackingLog]) -> List[str]:
        """Generate recommendations."""
        return ["Recommendations generation not implemented"]
    
    def _calculate_compliance_metrics(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate compliance metrics."""
        return {"compliance": "Not implemented"}
    
    def _identify_compliance_violations(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Identify compliance violations."""
        return []
    
    def _extract_audit_trail(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Extract audit trail."""
        return []
    
    def _check_retention_compliance(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Check retention compliance."""
        return {"retention": "Not implemented"}
    
    def _check_regulatory_requirements(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Check regulatory requirements."""
        return {"regulatory": "Not implemented"}
    
    def _calculate_reconciliation_metrics(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate reconciliation metrics."""
        return {"reconciliation": "Not implemented"}
    
    def _get_unreconciled_payments(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Get unreconciled payments."""
        return []
    
    def _get_reconciliation_discrepancies(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Get reconciliation discrepancies."""
        return []
    
    def _get_bank_statement_matches(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Get bank statement matches."""
        return []
    
    def _get_reconciliation_recommendations(self, payments: List[PaymentTrackingLog]) -> List[str]:
        """Get reconciliation recommendations."""
        return []
    
    def _calculate_audit_metrics(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Calculate audit metrics."""
        return {"audit": "Not implemented"}
    
    def _extract_comprehensive_audit_trail(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Extract comprehensive audit trail."""
        return []
    
    def _extract_access_logs(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Extract access logs."""
        return []
    
    def _check_data_integrity(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Check data integrity."""
        return {"integrity": "Not implemented"}
    
    def _identify_security_events(self, payments: List[PaymentTrackingLog]) -> List[Dict[str, Any]]:
        """Identify security events."""
        return []
    
    def _perform_compliance_audit(self, payments: List[PaymentTrackingLog]) -> Dict[str, Any]:
        """Perform compliance audit."""
        return {"compliance_audit": "Not implemented"}
