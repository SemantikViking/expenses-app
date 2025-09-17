"""
Enhanced Reporting & Analytics System for Receipt Processing.

This module provides comprehensive reporting, analytics, filtering, search,
and export capabilities for the receipt processing workflow.
"""

import json
import csv
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Union, Any, Set, Tuple, Iterator
from pathlib import Path
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging

from .models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, 
    StatusTransition, Currency
)
from .storage import JSONStorageManager

logger = logging.getLogger(__name__)


class FilterOperator(str, Enum):
    """Filter operators for querying."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class SortDirection(str, Enum):
    """Sort directions for querying."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class FilterCondition:
    """A single filter condition."""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False


@dataclass
class SortCondition:
    """A single sort condition."""
    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class QueryOptions:
    """Options for querying logs."""
    filters: List[FilterCondition] = None
    sort_by: List[SortCondition] = None
    limit: Optional[int] = None
    offset: int = 0
    include_metadata: bool = True
    include_transitions: bool = True


@dataclass
class ReportSummary:
    """Summary statistics for reports."""
    total_receipts: int
    processed_count: int
    error_count: int
    pending_count: int
    retry_count: int
    no_data_count: int
    emailed_count: int
    submitted_count: int
    payment_received_count: int
    success_rate: float
    error_rate: float
    avg_processing_time: Optional[float]
    total_amount: Optional[Decimal]
    unique_vendors: int
    date_range: Tuple[Optional[datetime], Optional[datetime]]


@dataclass
class VendorAnalysis:
    """Analysis data for a specific vendor."""
    vendor_name: str
    receipt_count: int
    total_amount: Decimal
    avg_amount: Decimal
    first_receipt: Optional[datetime]
    last_receipt: Optional[datetime]
    success_rate: float
    error_count: int
    common_issues: List[str]


@dataclass
class WorkflowMetrics:
    """Workflow performance metrics."""
    avg_processing_time: float
    median_processing_time: float
    p95_processing_time: float
    p99_processing_time: float
    total_processing_time: float
    avg_retries_per_receipt: float
    max_retries: int
    error_recovery_rate: float
    workflow_efficiency: float


class LogFilter:
    """Advanced filtering system for receipt processing logs."""
    
    def __init__(self, storage_manager: JSONStorageManager):
        self.storage = storage_manager
    
    def apply_filters(self, logs: List[ReceiptProcessingLog], 
                     filters: List[FilterCondition]) -> List[ReceiptProcessingLog]:
        """Apply filters to a list of logs."""
        if not filters:
            return logs
        
        filtered_logs = []
        for log in logs:
            if self._matches_filters(log, filters):
                filtered_logs.append(log)
        
        return filtered_logs
    
    def _matches_filters(self, log: ReceiptProcessingLog, 
                        filters: List[FilterCondition]) -> bool:
        """Check if a log matches all filter conditions."""
        for filter_cond in filters:
            if not self._matches_condition(log, filter_cond):
                return False
        return True
    
    def _matches_condition(self, log: ReceiptProcessingLog, 
                          condition: FilterCondition) -> bool:
        """Check if a log matches a single filter condition."""
        field_value = self._get_field_value(log, condition.field)
        
        if condition.operator == FilterOperator.IS_NULL:
            return field_value is None
        elif condition.operator == FilterOperator.IS_NOT_NULL:
            return field_value is not None
        
        if field_value is None:
            return False
        
        # Convert values for comparison
        if isinstance(field_value, str) and not condition.case_sensitive:
            field_value = field_value.lower()
            if isinstance(condition.value, str):
                condition_value = condition.value.lower()
            else:
                condition_value = condition.value
        else:
            condition_value = condition.value
        
        if condition.operator == FilterOperator.EQUALS:
            return field_value == condition_value
        elif condition.operator == FilterOperator.NOT_EQUALS:
            return field_value != condition_value
        elif condition.operator == FilterOperator.CONTAINS:
            return condition_value in field_value
        elif condition.operator == FilterOperator.NOT_CONTAINS:
            return condition_value not in field_value
        elif condition.operator == FilterOperator.STARTS_WITH:
            return field_value.startswith(condition_value)
        elif condition.operator == FilterOperator.ENDS_WITH:
            return field_value.endswith(condition_value)
        elif condition.operator == FilterOperator.GREATER_THAN:
            return field_value > condition_value
        elif condition.operator == FilterOperator.LESS_THAN:
            return field_value < condition_value
        elif condition.operator == FilterOperator.GREATER_EQUAL:
            return field_value >= condition_value
        elif condition.operator == FilterOperator.LESS_EQUAL:
            return field_value <= condition_value
        elif condition.operator == FilterOperator.IN:
            return field_value in condition_value
        elif condition.operator == FilterOperator.NOT_IN:
            return field_value not in condition_value
        elif condition.operator == FilterOperator.BETWEEN:
            return condition_value[0] <= field_value <= condition_value[1]
        
        return False
    
    def _get_field_value(self, log: ReceiptProcessingLog, field: str) -> Any:
        """Get field value from log entry."""
        # Direct fields
        if field == "id":
            return str(log.id)
        elif field == "original_filename":
            return log.original_filename
        elif field == "file_size":
            return log.file_size
        elif field == "current_status":
            return log.current_status.value
        elif field == "created_at":
            return log.created_at
        elif field == "processed_at":
            return log.processed_at
        elif field == "processing_time_seconds":
            return log.processing_time_seconds
        elif field == "confidence_score":
            return log.confidence_score
        
        # Receipt data fields
        elif field == "vendor_name" and log.receipt_data:
            return log.receipt_data.vendor_name
        elif field == "transaction_date" and log.receipt_data:
            return log.receipt_data.transaction_date
        elif field == "total_amount" and log.receipt_data:
            return log.receipt_data.total_amount
        elif field == "currency" and log.receipt_data:
            return log.receipt_data.currency.value
        elif field == "extraction_confidence" and log.receipt_data:
            return log.receipt_data.extraction_confidence
        
        # Status transition fields
        elif field == "status_count":
            return len(log.status_history)
        elif field == "last_status_change":
            if log.status_history:
                return log.status_history[-1].timestamp
            return None
        
        # Payment fields
        elif field == "payment_received_at":
            return log.payment_received_at
        elif field == "payment_amount":
            return log.payment_amount
        elif field == "payment_reference":
            return log.payment_reference
        
        # Tags and notes
        elif field == "tags":
            return log.tags
        elif field == "notes":
            return log.notes
        
        return None


class LogSorter:
    """Sorting system for receipt processing logs."""
    
    def sort_logs(self, logs: List[ReceiptProcessingLog], 
                  sort_conditions: List[SortCondition]) -> List[ReceiptProcessingLog]:
        """Sort logs according to sort conditions."""
        if not sort_conditions:
            return logs
        
        def sort_key(log: ReceiptProcessingLog) -> Tuple[Any, ...]:
            key_values = []
            for condition in sort_conditions:
                value = self._get_field_value(log, condition.field)
                # Convert None to a sortable value
                if value is None:
                    value = "" if condition.direction == SortDirection.ASC else "zzz"
                key_values.append(value)
            return tuple(key_values)
        
        reverse = any(condition.direction == SortDirection.DESC for condition in sort_conditions)
        return sorted(logs, key=sort_key, reverse=reverse)
    
    def _get_field_value(self, log: ReceiptProcessingLog, field: str) -> Any:
        """Get field value for sorting (same as LogFilter._get_field_value)."""
        # Direct fields
        if field == "id":
            return str(log.id)
        elif field == "original_filename":
            return log.original_filename
        elif field == "file_size":
            return log.file_size
        elif field == "current_status":
            return log.current_status.value
        elif field == "created_at":
            return log.created_at
        elif field == "processed_at":
            return log.processed_at
        elif field == "processing_time_seconds":
            return log.processing_time_seconds
        elif field == "confidence_score":
            return log.confidence_score
        
        # Receipt data fields
        elif field == "vendor_name" and log.receipt_data:
            return log.receipt_data.vendor_name
        elif field == "transaction_date" and log.receipt_data:
            return log.receipt_data.transaction_date
        elif field == "total_amount" and log.receipt_data:
            return log.receipt_data.total_amount
        elif field == "currency" and log.receipt_data:
            return log.receipt_data.currency.value
        elif field == "extraction_confidence" and log.receipt_data:
            return log.receipt_data.extraction_confidence
        
        # Status transition fields
        elif field == "status_count":
            return len(log.status_history)
        elif field == "last_status_change":
            if log.status_history:
                return log.status_history[-1].timestamp
            return None
        
        # Payment fields
        elif field == "payment_received_at":
            return log.payment_received_at
        elif field == "payment_amount":
            return log.payment_amount
        elif field == "payment_reference":
            return log.payment_reference
        
        # Tags and notes
        elif field == "tags":
            return log.tags
        elif field == "notes":
            return log.notes
        
        return None


class LogQueryEngine:
    """Advanced query engine for receipt processing logs."""
    
    def __init__(self, storage_manager: JSONStorageManager):
        self.storage = storage_manager
        self.filter = LogFilter(storage_manager)
        self.sorter = LogSorter()
    
    def query(self, options: QueryOptions) -> List[ReceiptProcessingLog]:
        """Execute a query with filters, sorting, and pagination."""
        # Get all logs
        all_logs = self.storage.get_all_logs()
        
        # Apply filters
        filtered_logs = self.filter.apply_filters(all_logs, options.filters or [])
        
        # Apply sorting
        sorted_logs = self.sorter.sort_logs(filtered_logs, options.sort_by or [])
        
        # Apply pagination
        start_idx = options.offset
        end_idx = start_idx + options.limit if options.limit else len(sorted_logs)
        
        return sorted_logs[start_idx:end_idx]
    
    def count(self, filters: List[FilterCondition] = None) -> int:
        """Count logs matching the given filters."""
        all_logs = self.storage.get_all_logs()
        filtered_logs = self.filter.apply_filters(all_logs, filters or [])
        return len(filtered_logs)
    
    def get_distinct_values(self, field: str, 
                           filters: List[FilterCondition] = None) -> List[Any]:
        """Get distinct values for a field."""
        all_logs = self.storage.get_all_logs()
        filtered_logs = self.filter.apply_filters(all_logs, filters or [])
        
        values = set()
        for log in filtered_logs:
            value = self.filter._get_field_value(log, field)
            if value is not None:
                values.add(value)
        
        return sorted(list(values))


class ReportGenerator:
    """Generate various types of reports."""
    
    def __init__(self, storage_manager: JSONStorageManager):
        self.storage = storage_manager
        self.query_engine = LogQueryEngine(storage_manager)
    
    def generate_summary_report(self, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               vendor_filter: Optional[str] = None) -> ReportSummary:
        """Generate a summary report."""
        # Build filters
        filters = []
        if start_date:
            filters.append(FilterCondition("created_at", FilterOperator.GREATER_EQUAL, start_date))
        if end_date:
            filters.append(FilterCondition("created_at", FilterOperator.LESS_EQUAL, end_date))
        if vendor_filter:
            filters.append(FilterCondition("vendor_name", FilterOperator.CONTAINS, vendor_filter))
        
        # Get logs
        logs = self.query_engine.query(QueryOptions(filters=filters))
        
        # Calculate statistics
        total_receipts = len(logs)
        status_counts = {}
        total_amount = Decimal('0')
        unique_vendors = set()
        processing_times = []
        
        for log in logs:
            # Count by status
            status = log.current_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Sum amounts
            if log.receipt_data and log.receipt_data.total_amount:
                total_amount += log.receipt_data.total_amount
                unique_vendors.add(log.receipt_data.vendor_name)
            
            # Collect processing times
            if log.processing_time_seconds:
                processing_times.append(log.processing_time_seconds)
        
        # Calculate rates
        processed_count = status_counts.get('processed', 0)
        error_count = status_counts.get('error', 0)
        success_rate = processed_count / total_receipts if total_receipts > 0 else 0
        error_rate = error_count / total_receipts if total_receipts > 0 else 0
        
        # Calculate average processing time
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None
        
        # Get date range
        date_range = (None, None)
        if logs:
            dates = [log.created_at for log in logs if log.created_at]
            if dates:
                date_range = (min(dates), max(dates))
        
        return ReportSummary(
            total_receipts=total_receipts,
            processed_count=processed_count,
            error_count=error_count,
            pending_count=status_counts.get('pending', 0),
            retry_count=status_counts.get('retry', 0),
            no_data_count=status_counts.get('no_data_extracted', 0),
            emailed_count=status_counts.get('emailed', 0),
            submitted_count=status_counts.get('submitted', 0),
            payment_received_count=status_counts.get('payment_received', 0),
            success_rate=success_rate,
            error_rate=error_rate,
            avg_processing_time=avg_processing_time,
            total_amount=total_amount if total_amount > 0 else None,
            unique_vendors=len(unique_vendors),
            date_range=date_range
        )
    
    def generate_vendor_analysis(self, 
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[VendorAnalysis]:
        """Generate vendor analysis report."""
        # Build filters
        filters = []
        if start_date:
            filters.append(FilterCondition("created_at", FilterOperator.GREATER_EQUAL, start_date))
        if end_date:
            filters.append(FilterCondition("created_at", FilterOperator.LESS_EQUAL, end_date))
        
        # Get logs with receipt data
        logs = self.query_engine.query(QueryOptions(filters=filters))
        logs_with_data = [log for log in logs if log.receipt_data and log.receipt_data.vendor_name]
        
        # Group by vendor
        vendor_data = {}
        for log in logs_with_data:
            vendor_name = log.receipt_data.vendor_name
            if vendor_name not in vendor_data:
                vendor_data[vendor_name] = {
                    'logs': [],
                    'amounts': [],
                    'dates': [],
                    'errors': 0
                }
            
            vendor_data[vendor_name]['logs'].append(log)
            if log.receipt_data.total_amount:
                vendor_data[vendor_name]['amounts'].append(log.receipt_data.total_amount)
            if log.receipt_data.transaction_date:
                vendor_data[vendor_name]['dates'].append(log.receipt_data.transaction_date)
            if log.current_status == ProcessingStatus.ERROR:
                vendor_data[vendor_name]['errors'] += 1
        
        # Generate analysis for each vendor
        analyses = []
        for vendor_name, data in vendor_data.items():
            receipt_count = len(data['logs'])
            total_amount = sum(data['amounts']) if data['amounts'] else Decimal('0')
            avg_amount = total_amount / len(data['amounts']) if data['amounts'] else Decimal('0')
            
            first_receipt = min(data['dates']) if data['dates'] else None
            last_receipt = max(data['dates']) if data['dates'] else None
            
            success_count = sum(1 for log in data['logs'] if log.current_status == ProcessingStatus.PROCESSED)
            success_rate = success_count / receipt_count if receipt_count > 0 else 0
            
            # Analyze common issues
            common_issues = []
            error_logs = [log for log in data['logs'] if log.current_status == ProcessingStatus.ERROR]
            if error_logs:
                # This would need more sophisticated analysis in a real implementation
                common_issues.append(f"{len(error_logs)} processing errors")
            
            analyses.append(VendorAnalysis(
                vendor_name=vendor_name,
                receipt_count=receipt_count,
                total_amount=total_amount,
                avg_amount=avg_amount,
                first_receipt=first_receipt,
                last_receipt=last_receipt,
                success_rate=success_rate,
                error_count=data['errors'],
                common_issues=common_issues
            ))
        
        # Sort by total amount descending
        analyses.sort(key=lambda x: x.total_amount, reverse=True)
        return analyses
    
    def generate_workflow_metrics(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> WorkflowMetrics:
        """Generate workflow performance metrics."""
        # Build filters
        filters = []
        if start_date:
            filters.append(FilterCondition("created_at", FilterOperator.GREATER_EQUAL, start_date))
        if end_date:
            filters.append(FilterCondition("created_at", FilterOperator.LESS_EQUAL, end_date))
        
        # Get logs
        logs = self.query_engine.query(QueryOptions(filters=filters))
        
        # Calculate metrics
        processing_times = [log.processing_time_seconds for log in logs if log.processing_time_seconds]
        retry_counts = [len([t for t in log.status_history if t.to_status == ProcessingStatus.RETRY]) for log in logs]
        
        if not processing_times:
            return WorkflowMetrics(
                avg_processing_time=0.0,
                median_processing_time=0.0,
                p95_processing_time=0.0,
                p99_processing_time=0.0,
                total_processing_time=0.0,
                avg_retries_per_receipt=0.0,
                max_retries=0,
                error_recovery_rate=0.0,
                workflow_efficiency=0.0
            )
        
        # Calculate percentiles
        sorted_times = sorted(processing_times)
        n = len(sorted_times)
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        median_processing_time = sorted_times[n // 2] if n > 0 else 0
        p95_processing_time = sorted_times[int(n * 0.95)] if n > 0 else 0
        p99_processing_time = sorted_times[int(n * 0.99)] if n > 0 else 0
        total_processing_time = sum(processing_times)
        
        # Calculate retry metrics
        avg_retries = sum(retry_counts) / len(retry_counts) if retry_counts else 0
        max_retries = max(retry_counts) if retry_counts else 0
        
        # Calculate error recovery rate
        error_logs = [log for log in logs if log.current_status == ProcessingStatus.ERROR]
        retry_logs = [log for log in logs if ProcessingStatus.RETRY in [t.to_status for t in log.status_history]]
        error_recovery_rate = len(retry_logs) / len(error_logs) if error_logs else 0
        
        # Calculate workflow efficiency (successful processing rate)
        successful_logs = [log for log in logs if log.current_status == ProcessingStatus.PROCESSED]
        workflow_efficiency = len(successful_logs) / len(logs) if logs else 0
        
        return WorkflowMetrics(
            avg_processing_time=avg_processing_time,
            median_processing_time=median_processing_time,
            p95_processing_time=p95_processing_time,
            p99_processing_time=p99_processing_time,
            total_processing_time=total_processing_time,
            avg_retries_per_receipt=avg_retries,
            max_retries=max_retries,
            error_recovery_rate=error_recovery_rate,
            workflow_efficiency=workflow_efficiency
        )
    
    def generate_payment_report(self, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate payment reconciliation report."""
        # Build filters
        filters = []
        if start_date:
            filters.append(FilterCondition("created_at", FilterOperator.GREATER_EQUAL, start_date))
        if end_date:
            filters.append(FilterCondition("created_at", FilterOperator.LESS_EQUAL, end_date))
        
        # Get logs
        logs = self.query_engine.query(QueryOptions(filters=filters))
        
        # Analyze payment status
        payment_data = {
            'total_receipts': len(logs),
            'submitted_receipts': 0,
            'payment_received': 0,
            'outstanding_payments': 0,
            'total_submitted_amount': Decimal('0'),
            'total_paid_amount': Decimal('0'),
            'outstanding_amount': Decimal('0'),
            'payment_summary': [],
            'outstanding_receipts': []
        }
        
        for log in logs:
            if log.current_status in [ProcessingStatus.SUBMITTED, ProcessingStatus.PAYMENT_RECEIVED]:
                payment_data['submitted_receipts'] += 1
                
                if log.receipt_data and log.receipt_data.total_amount:
                    amount = log.receipt_data.total_amount
                    payment_data['total_submitted_amount'] += amount
                    
                    if log.current_status == ProcessingStatus.PAYMENT_RECEIVED:
                        payment_data['payment_received'] += 1
                        payment_data['total_paid_amount'] += amount
                        
                        payment_data['payment_summary'].append({
                            'receipt_id': str(log.id),
                            'vendor': log.receipt_data.vendor_name,
                            'amount': float(amount),
                            'currency': log.receipt_data.currency.value,
                            'submitted_at': log.processed_at,
                            'paid_at': log.payment_received_at,
                            'payment_reference': log.payment_reference
                        })
                    else:
                        payment_data['outstanding_payments'] += 1
                        payment_data['outstanding_amount'] += amount
                        
                        payment_data['outstanding_receipts'].append({
                            'receipt_id': str(log.id),
                            'vendor': log.receipt_data.vendor_name,
                            'amount': float(amount),
                            'currency': log.receipt_data.currency.value,
                            'submitted_at': log.processed_at,
                            'days_outstanding': (datetime.now() - log.processed_at).days if log.processed_at else None
                        })
        
        return payment_data
    
    def generate_audit_report(self, 
                             log_id: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate audit report with complete status change history."""
        if log_id:
            # Single log audit
            try:
                from uuid import UUID
                log_uuid = UUID(log_id)
                log = self.storage.get_log_entry(log_uuid)
            except ValueError:
                return {'error': 'Invalid log ID format'}
            
            if not log:
                return {'error': 'Log not found'}
            
            return {
                'log_id': str(log.id),
                'original_filename': log.original_filename,
                'created_at': log.created_at,
                'current_status': log.current_status.value,
                'status_history': [
                    {
                        'from_status': t.from_status.value if t.from_status else None,
                        'to_status': t.to_status.value,
                        'timestamp': t.timestamp,
                        'reason': t.reason,
                        'user': t.user,
                        'metadata': t.metadata
                    }
                    for t in log.status_history
                ],
                'receipt_data': log.receipt_data.model_dump() if log.receipt_data else None,
                'processing_metrics': {
                    'processing_time_seconds': log.processing_time_seconds,
                    'confidence_score': log.confidence_score
                }
            }
        else:
            # Multiple logs audit
            filters = []
            if start_date:
                filters.append(FilterCondition("created_at", FilterOperator.GREATER_EQUAL, start_date))
            if end_date:
                filters.append(FilterCondition("created_at", FilterOperator.LESS_EQUAL, end_date))
            
            logs = self.query_engine.query(QueryOptions(filters=filters))
            
            audit_data = []
            for log in logs:
                audit_data.append({
                    'log_id': str(log.id),
                    'original_filename': log.original_filename,
                    'created_at': log.created_at,
                    'current_status': log.current_status.value,
                    'status_count': len(log.status_history),
                    'last_status_change': log.status_history[-1].timestamp if log.status_history else None,
                    'processing_time_seconds': log.processing_time_seconds
                })
            
            return {
                'total_logs': len(audit_data),
                'date_range': {
                    'start': min(log.created_at for log in logs) if logs else None,
                    'end': max(log.created_at for log in logs) if logs else None
                },
                'logs': audit_data
            }


class ExportManager:
    """Export data in various formats."""
    
    def __init__(self, storage_manager: JSONStorageManager):
        self.storage = storage_manager
        self.query_engine = LogQueryEngine(storage_manager)
    
    def export_to_json(self, output_path: Path, 
                       filters: List[FilterCondition] = None,
                       include_metadata: bool = True) -> bool:
        """Export logs to JSON format."""
        try:
            logs = self.query_engine.query(QueryOptions(
                filters=filters,
                include_metadata=include_metadata
            ))
            
            export_data = []
            for log in logs:
                log_data = {
                    'id': str(log.id),
                    'original_filename': log.original_filename,
                    'file_size': log.file_size,
                    'current_status': log.current_status.value,
                    'created_at': log.created_at.isoformat() if log.created_at else None,
                    'processed_at': log.processed_at.isoformat() if log.processed_at else None,
                    'processing_time_seconds': log.processing_time_seconds,
                    'confidence_score': log.confidence_score
                }
                
                if log.receipt_data:
                    log_data['receipt_data'] = {
                        'vendor_name': log.receipt_data.vendor_name,
                        'transaction_date': log.receipt_data.transaction_date.isoformat() if log.receipt_data.transaction_date else None,
                        'total_amount': float(log.receipt_data.total_amount) if log.receipt_data.total_amount else None,
                        'currency': log.receipt_data.currency.value,
                        'extraction_confidence': log.receipt_data.extraction_confidence
                    }
                
                if include_metadata:
                    log_data['status_history'] = [
                        {
                            'from_status': t.from_status.value if t.from_status else None,
                            'to_status': t.to_status.value,
                            'timestamp': t.timestamp.isoformat(),
                            'reason': t.reason,
                            'user': t.user,
                            'metadata': t.metadata
                        }
                        for t in log.status_history
                    ]
                
                export_data.append(log_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(export_data)} logs to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False
    
    def export_to_csv(self, output_path: Path,
                      filters: List[FilterCondition] = None) -> bool:
        """Export logs to CSV format."""
        try:
            logs = self.query_engine.query(QueryOptions(filters=filters))
            
            if not logs:
                logger.warning("No logs to export")
                return False
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                header = [
                    'ID', 'Original Filename', 'File Size', 'Current Status',
                    'Created At', 'Processed At', 'Processing Time (s)',
                    'Vendor Name', 'Transaction Date', 'Total Amount', 'Currency',
                    'Confidence Score', 'Status Count', 'Last Status Change'
                ]
                writer.writerow(header)
                
                # Write data
                for log in logs:
                    row = [
                        str(log.id),
                        log.original_filename,
                        log.file_size,
                        log.current_status.value,
                        log.created_at.isoformat() if log.created_at else '',
                        log.processed_at.isoformat() if log.processed_at else '',
                        log.processing_time_seconds or '',
                        log.receipt_data.vendor_name if log.receipt_data else '',
                        log.receipt_data.transaction_date.isoformat() if log.receipt_data and log.receipt_data.transaction_date else '',
                        float(log.receipt_data.total_amount) if log.receipt_data and log.receipt_data.total_amount else '',
                        log.receipt_data.currency.value if log.receipt_data else '',
                        log.confidence_score or '',
                        len(log.status_history),
                        log.status_history[-1].timestamp.isoformat() if log.status_history else ''
                    ]
                    writer.writerow(row)
            
            logger.info(f"Exported {len(logs)} logs to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False


class AnalyticsEngine:
    """Comprehensive analytics engine for receipt processing."""
    
    def __init__(self, storage_manager: JSONStorageManager):
        self.storage = storage_manager
        self.query_engine = LogQueryEngine(storage_manager)
        self.report_generator = ReportGenerator(storage_manager)
        self.export_manager = ExportManager(storage_manager)
    
    def get_daily_summary(self, target_date: date) -> Dict[str, Any]:
        """Get daily summary for a specific date."""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        summary = self.report_generator.generate_summary_report(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return {
            'date': target_date.isoformat(),
            'summary': summary.__dict__,
            'workflow_metrics': self.report_generator.generate_workflow_metrics(
                start_date=start_datetime,
                end_date=end_datetime
            ).__dict__
        }
    
    def get_weekly_summary(self, start_date: date) -> Dict[str, Any]:
        """Get weekly summary starting from a specific date."""
        end_date = start_date + timedelta(days=6)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        summary = self.report_generator.generate_summary_report(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        vendor_analysis = self.report_generator.generate_vendor_analysis(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return {
            'week_start': start_date.isoformat(),
            'week_end': end_date.isoformat(),
            'summary': summary.__dict__,
            'top_vendors': [v.__dict__ for v in vendor_analysis[:10]],  # Top 10 vendors
            'workflow_metrics': self.report_generator.generate_workflow_metrics(
                start_date=start_datetime,
                end_date=end_datetime
            ).__dict__
        }
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly summary for a specific year and month."""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        summary = self.report_generator.generate_summary_report(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        vendor_analysis = self.report_generator.generate_vendor_analysis(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        payment_report = self.report_generator.generate_payment_report(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return {
            'year': year,
            'month': month,
            'summary': summary.__dict__,
            'vendor_analysis': [v.__dict__ for v in vendor_analysis],
            'payment_report': payment_report,
            'workflow_metrics': self.report_generator.generate_workflow_metrics(
                start_date=start_datetime,
                end_date=end_datetime
            ).__dict__
        }
