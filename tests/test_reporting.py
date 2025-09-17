"""
Tests for Enhanced Reporting & Analytics System.

This module tests the filtering, search, reporting, analytics, and export
capabilities for the receipt processing workflow.
"""

import tempfile
import json
import csv
from datetime import datetime, timedelta, date
from pathlib import Path
from decimal import Decimal
import pytest

from src.receipt_processor.reporting import (
    FilterOperator, SortDirection, FilterCondition, SortCondition, QueryOptions,
    ReportSummary, VendorAnalysis, WorkflowMetrics, LogFilter, LogSorter,
    LogQueryEngine, ReportGenerator, ExportManager, AnalyticsEngine
)
from src.receipt_processor.storage import JSONStorageManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency, StatusTransition
)


class TestLogFilter:
    """Test cases for log filtering."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_logs(self, storage_manager):
        """Create sample log entries for testing."""
        logs = []
        
        # Create logs with different statuses and data
        for i in range(5):
            receipt_data = None
            if i < 3:  # First 3 have receipt data
                receipt_data = ReceiptData(
                    vendor_name=f"Vendor {i+1}",
                    transaction_date=datetime.now() - timedelta(days=i),
                    total_amount=Decimal(f"{25.50 + i * 10}"),
                    currency=Currency.USD,
                    extraction_confidence=0.9 - i * 0.1,
                    has_required_data=True
                )
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=ProcessingStatus.PROCESSED if i < 3 else ProcessingStatus.ERROR,
                receipt_data=receipt_data,
                processing_time_seconds=1.0 + i * 0.5,
                confidence_score=0.9 - i * 0.1
            )
            
            storage_manager.add_log_entry(log)
            logs.append(log)
        
        return logs
    
    @pytest.fixture
    def log_filter(self, storage_manager):
        """Create a log filter for testing."""
        return LogFilter(storage_manager)
    
    def test_filter_by_status(self, log_filter, sample_logs):
        """Test filtering by status."""
        filters = [FilterCondition("current_status", FilterOperator.EQUALS, "processed")]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 3
        assert all(log.current_status == ProcessingStatus.PROCESSED for log in filtered_logs)
    
    def test_filter_by_vendor_name(self, log_filter, sample_logs):
        """Test filtering by vendor name."""
        filters = [FilterCondition("vendor_name", FilterOperator.CONTAINS, "Vendor 1")]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 1
        assert filtered_logs[0].receipt_data.vendor_name == "Vendor 1"
    
    def test_filter_by_amount_range(self, log_filter, sample_logs):
        """Test filtering by amount range."""
        filters = [FilterCondition("total_amount", FilterOperator.BETWEEN, [30, 50])]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 2  # Vendor 2 and 3
        for log in filtered_logs:
            assert 30 <= log.receipt_data.total_amount <= 50
    
    def test_filter_by_date_range(self, log_filter, sample_logs):
        """Test filtering by date range."""
        start_date = datetime.now() - timedelta(days=2)
        end_date = datetime.now()
        
        filters = [
            FilterCondition("transaction_date", FilterOperator.GREATER_EQUAL, start_date),
            FilterCondition("transaction_date", FilterOperator.LESS_EQUAL, end_date)
        ]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        # Only logs 0 and 1 should be within the date range (0 days ago and 1 day ago)
        assert len(filtered_logs) == 2  # Vendor 1, 2
        for log in filtered_logs:
            assert start_date <= log.receipt_data.transaction_date <= end_date
    
    def test_filter_multiple_conditions(self, log_filter, sample_logs):
        """Test filtering with multiple conditions."""
        filters = [
            FilterCondition("current_status", FilterOperator.EQUALS, "processed"),
            FilterCondition("total_amount", FilterOperator.GREATER_THAN, 30)
        ]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 2  # Vendor 2 and 3
        for log in filtered_logs:
            assert log.current_status == ProcessingStatus.PROCESSED
            assert log.receipt_data.total_amount > 30
    
    def test_filter_case_insensitive(self, log_filter, sample_logs):
        """Test case-insensitive filtering."""
        filters = [FilterCondition("vendor_name", FilterOperator.CONTAINS, "vendor", case_sensitive=False)]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 3  # All vendors with data
    
    def test_filter_null_values(self, log_filter, sample_logs):
        """Test filtering for null values."""
        filters = [FilterCondition("vendor_name", FilterOperator.IS_NULL, None)]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 2  # Logs 4 and 5 (no receipt data)
    
    def test_filter_not_null_values(self, log_filter, sample_logs):
        """Test filtering for non-null values."""
        filters = [FilterCondition("vendor_name", FilterOperator.IS_NOT_NULL, None)]
        filtered_logs = log_filter.apply_filters(sample_logs, filters)
        
        assert len(filtered_logs) == 3  # Logs 1, 2, 3 (with receipt data)


class TestLogSorter:
    """Test cases for log sorting."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_logs(self, storage_manager):
        """Create sample log entries for testing."""
        logs = []
        
        for i in range(5):
            receipt_data = ReceiptData(
                vendor_name=f"Vendor {5-i}",  # Reverse order
                transaction_date=datetime.now() - timedelta(days=i),
                total_amount=Decimal(f"{25.50 + i * 10}"),
                currency=Currency.USD,
                extraction_confidence=0.9 - i * 0.1,
                has_required_data=True
            )
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=ProcessingStatus.PROCESSED,
                receipt_data=receipt_data,
                processing_time_seconds=1.0 + i * 0.5
            )
            
            storage_manager.add_log_entry(log)
            logs.append(log)
        
        return logs
    
    @pytest.fixture
    def log_sorter(self, storage_manager):
        """Create a log sorter for testing."""
        return LogSorter()
    
    def test_sort_by_vendor_name_asc(self, log_sorter, sample_logs):
        """Test sorting by vendor name ascending."""
        sort_conditions = [SortCondition("vendor_name", SortDirection.ASC)]
        sorted_logs = log_sorter.sort_logs(sample_logs, sort_conditions)
        
        vendor_names = [log.receipt_data.vendor_name for log in sorted_logs]
        assert vendor_names == ["Vendor 1", "Vendor 2", "Vendor 3", "Vendor 4", "Vendor 5"]
    
    def test_sort_by_vendor_name_desc(self, log_sorter, sample_logs):
        """Test sorting by vendor name descending."""
        sort_conditions = [SortCondition("vendor_name", SortDirection.DESC)]
        sorted_logs = log_sorter.sort_logs(sample_logs, sort_conditions)
        
        vendor_names = [log.receipt_data.vendor_name for log in sorted_logs]
        assert vendor_names == ["Vendor 5", "Vendor 4", "Vendor 3", "Vendor 2", "Vendor 1"]
    
    def test_sort_by_amount_desc(self, log_sorter, sample_logs):
        """Test sorting by amount descending."""
        sort_conditions = [SortCondition("total_amount", SortDirection.DESC)]
        sorted_logs = log_sorter.sort_logs(sample_logs, sort_conditions)
        
        amounts = [log.receipt_data.total_amount for log in sorted_logs]
        assert amounts == [Decimal('65.50'), Decimal('55.50'), Decimal('45.50'), Decimal('35.50'), Decimal('25.50')]
    
    def test_sort_by_processing_time_asc(self, log_sorter, sample_logs):
        """Test sorting by processing time ascending."""
        sort_conditions = [SortCondition("processing_time_seconds", SortDirection.ASC)]
        sorted_logs = log_sorter.sort_logs(sample_logs, sort_conditions)
        
        times = [log.processing_time_seconds for log in sorted_logs]
        assert times == [1.0, 1.5, 2.0, 2.5, 3.0]
    
    def test_sort_multiple_fields(self, log_sorter, sample_logs):
        """Test sorting by multiple fields."""
        # Sort by status first, then by amount
        sort_conditions = [
            SortCondition("current_status", SortDirection.ASC),
            SortCondition("total_amount", SortDirection.DESC)
        ]
        sorted_logs = log_sorter.sort_logs(sample_logs, sort_conditions)
        
        # All have same status, so should be sorted by amount desc
        amounts = [log.receipt_data.total_amount for log in sorted_logs]
        assert amounts == [Decimal('65.50'), Decimal('55.50'), Decimal('45.50'), Decimal('35.50'), Decimal('25.50')]


class TestLogQueryEngine:
    """Test cases for log query engine."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_logs(self, storage_manager):
        """Create sample log entries for testing."""
        logs = []
        
        for i in range(10):
            receipt_data = ReceiptData(
                vendor_name=f"Vendor {i % 3 + 1}",  # 3 different vendors
                transaction_date=datetime.now() - timedelta(days=i),
                total_amount=Decimal(f"{25.50 + i * 5}"),
                currency=Currency.USD,
                extraction_confidence=0.9 - i * 0.05,
                has_required_data=True
            )
            
            status = ProcessingStatus.PROCESSED if i < 7 else ProcessingStatus.ERROR
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=status,
                receipt_data=receipt_data,
                processing_time_seconds=1.0 + i * 0.2
            )
            
            storage_manager.add_log_entry(log)
            logs.append(log)
        
        return logs
    
    @pytest.fixture
    def query_engine(self, storage_manager):
        """Create a query engine for testing."""
        return LogQueryEngine(storage_manager)
    
    def test_query_with_filters(self, query_engine, sample_logs):
        """Test querying with filters."""
        filters = [FilterCondition("current_status", FilterOperator.EQUALS, "processed")]
        options = QueryOptions(filters=filters)
        
        results = query_engine.query(options)
        assert len(results) == 7
        assert all(log.current_status == ProcessingStatus.PROCESSED for log in results)
    
    def test_query_with_sorting(self, query_engine, sample_logs):
        """Test querying with sorting."""
        sort_conditions = [SortCondition("total_amount", SortDirection.DESC)]
        options = QueryOptions(sort_by=sort_conditions)
        
        results = query_engine.query(options)
        amounts = [log.receipt_data.total_amount for log in results]
        assert amounts == sorted(amounts, reverse=True)
    
    def test_query_with_pagination(self, query_engine, sample_logs):
        """Test querying with pagination."""
        options = QueryOptions(limit=3, offset=2)
        
        results = query_engine.query(options)
        assert len(results) == 3
        # Should get logs 3, 4, 5 (0-indexed)
    
    def test_query_count(self, query_engine, sample_logs):
        """Test counting results."""
        filters = [FilterCondition("current_status", FilterOperator.EQUALS, "processed")]
        count = query_engine.count(filters)
        assert count == 7
    
    def test_get_distinct_values(self, query_engine, sample_logs):
        """Test getting distinct values."""
        vendors = query_engine.get_distinct_values("vendor_name")
        assert set(vendors) == {"Vendor 1", "Vendor 2", "Vendor 3"}
        
        statuses = query_engine.get_distinct_values("current_status")
        assert set(statuses) == {"processed", "error"}


class TestReportGenerator:
    """Test cases for report generation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_logs(self, storage_manager):
        """Create sample log entries for testing."""
        logs = []
        
        # Create logs with different statuses and vendors
        vendors = ["Apple Store", "Amazon", "Starbucks", "Target", "Walmart"]
        statuses = [
            ProcessingStatus.PROCESSED,
            ProcessingStatus.PROCESSED,
            ProcessingStatus.ERROR,
            ProcessingStatus.PENDING,
            ProcessingStatus.RETRY
        ]
        
        for i in range(5):
            receipt_data = ReceiptData(
                vendor_name=vendors[i],
                transaction_date=datetime.now() - timedelta(days=i),
                total_amount=Decimal(f"{25.50 + i * 15}"),
                currency=Currency.USD,
                extraction_confidence=0.9 - i * 0.1,
                has_required_data=True
            )
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=statuses[i],
                receipt_data=receipt_data,
                processing_time_seconds=1.0 + i * 0.3
            )
            
            storage_manager.add_log_entry(log)
            logs.append(log)
        
        return logs
    
    @pytest.fixture
    def report_generator(self, storage_manager):
        """Create a report generator for testing."""
        return ReportGenerator(storage_manager)
    
    def test_generate_summary_report(self, report_generator, sample_logs):
        """Test generating summary report."""
        summary = report_generator.generate_summary_report()
        
        assert summary.total_receipts == 5
        assert summary.processed_count == 2
        assert summary.error_count == 1
        assert summary.pending_count == 1
        assert summary.retry_count == 1
        assert summary.success_rate == 0.4  # 2/5
        assert summary.error_rate == 0.2  # 1/5
        assert summary.unique_vendors == 5
        assert summary.total_amount == Decimal('277.50')  # Sum of all amounts (25.50 + 35.50 + 45.50 + 55.50 + 65.50)
    
    def test_generate_vendor_analysis(self, report_generator, sample_logs):
        """Test generating vendor analysis."""
        analysis = report_generator.generate_vendor_analysis()
        
        assert len(analysis) == 5
        assert all(isinstance(v, VendorAnalysis) for v in analysis)
        
        # Check that vendors are sorted by total amount
        amounts = [v.total_amount for v in analysis]
        assert amounts == sorted(amounts, reverse=True)
        
        # Check specific vendor data
        apple_vendor = next(v for v in analysis if v.vendor_name == "Apple Store")
        assert apple_vendor.receipt_count == 1
        assert apple_vendor.total_amount == Decimal('25.50')
        assert apple_vendor.success_rate == 1.0  # Only one receipt, processed
    
    def test_generate_workflow_metrics(self, report_generator, sample_logs):
        """Test generating workflow metrics."""
        metrics = report_generator.generate_workflow_metrics()
        
        assert metrics.avg_processing_time > 0
        assert metrics.median_processing_time > 0
        assert metrics.total_processing_time > 0
        assert metrics.workflow_efficiency == 0.4  # 2/5 processed
    
    def test_generate_payment_report(self, report_generator, sample_logs, storage_manager):
        """Test generating payment report."""
        # Add some submitted and paid receipts
        for log in sample_logs[:2]:  # First 2 logs
            log.current_status = ProcessingStatus.SUBMITTED
            storage_manager.update_log_entry(log.id, {"current_status": ProcessingStatus.SUBMITTED})
        
        # Make one paid
        log = sample_logs[0]
        log.current_status = ProcessingStatus.PAYMENT_RECEIVED
        log.payment_received_at = datetime.now()
        log.payment_reference = "PAY-123"
        storage_manager.update_log_entry(log.id, {
            "current_status": ProcessingStatus.PAYMENT_RECEIVED,
            "payment_received_at": log.payment_received_at,
            "payment_reference": log.payment_reference
        })
        
        payment_report = report_generator.generate_payment_report()
        
        assert payment_report['total_receipts'] == 5
        assert payment_report['submitted_receipts'] == 2
        assert payment_report['payment_received'] == 1
        assert payment_report['outstanding_payments'] == 1
        assert len(payment_report['payment_summary']) == 1
        assert len(payment_report['outstanding_receipts']) == 1
    
    def test_generate_audit_report_single_log(self, report_generator, sample_logs):
        """Test generating audit report for single log."""
        log_id = sample_logs[0].id  # Use UUID directly
        audit_report = report_generator.generate_audit_report(log_id=str(log_id))
        
        assert 'log_id' in audit_report
        assert audit_report['log_id'] == str(log_id)
        assert 'status_history' in audit_report
        assert 'receipt_data' in audit_report
    
    def test_generate_audit_report_multiple_logs(self, report_generator, sample_logs):
        """Test generating audit report for multiple logs."""
        audit_report = report_generator.generate_audit_report()
        
        assert 'total_logs' in audit_report
        assert audit_report['total_logs'] == 5
        assert 'logs' in audit_report
        assert len(audit_report['logs']) == 5


class TestExportManager:
    """Test cases for export functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_logs(self, storage_manager):
        """Create sample log entries for testing."""
        logs = []
        
        for i in range(3):
            receipt_data = ReceiptData(
                vendor_name=f"Vendor {i+1}",
                transaction_date=datetime.now() - timedelta(days=i),
                total_amount=Decimal(f"{25.50 + i * 10}"),
                currency=Currency.USD,
                extraction_confidence=0.9 - i * 0.1,
                has_required_data=True
            )
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=ProcessingStatus.PROCESSED,
                receipt_data=receipt_data,
                processing_time_seconds=1.0 + i * 0.5
            )
            
            storage_manager.add_log_entry(log)
            logs.append(log)
        
        return logs
    
    @pytest.fixture
    def export_manager(self, storage_manager):
        """Create an export manager for testing."""
        return ExportManager(storage_manager)
    
    def test_export_to_json(self, export_manager, sample_logs, temp_dir):
        """Test exporting to JSON format."""
        output_path = temp_dir / "export.json"
        success = export_manager.export_to_json(output_path)
        
        assert success
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 3
        assert all('id' in item for item in data)
        assert all('vendor_name' in item['receipt_data'] for item in data if 'receipt_data' in item)
    
    def test_export_to_csv(self, export_manager, sample_logs, temp_dir):
        """Test exporting to CSV format."""
        output_path = temp_dir / "export.csv"
        success = export_manager.export_to_csv(output_path)
        
        assert success
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert len(rows) == 4  # Header + 3 data rows
        assert rows[0][0] == 'ID'  # Header
        assert len(rows[1]) == 14  # Number of columns
    
    def test_export_with_filters(self, export_manager, sample_logs, temp_dir):
        """Test exporting with filters."""
        filters = [FilterCondition("vendor_name", FilterOperator.CONTAINS, "Vendor 1")]
        output_path = temp_dir / "filtered_export.json"
        success = export_manager.export_to_json(output_path, filters=filters)
        
        assert success
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['receipt_data']['vendor_name'] == 'Vendor 1'


class TestAnalyticsEngine:
    """Test cases for analytics engine."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_logs(self, storage_manager):
        """Create sample log entries for testing."""
        logs = []
        
        # Create logs for different days
        for i in range(7):  # 7 days
            receipt_data = ReceiptData(
                vendor_name=f"Vendor {i % 3 + 1}",
                transaction_date=datetime.now() - timedelta(days=i),
                total_amount=Decimal(f"{25.50 + i * 5}"),
                currency=Currency.USD,
                extraction_confidence=0.9 - i * 0.05,
                has_required_data=True
            )
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=ProcessingStatus.PROCESSED,
                receipt_data=receipt_data,
                processing_time_seconds=1.0 + i * 0.2
            )
            
            storage_manager.add_log_entry(log)
            logs.append(log)
        
        return logs
    
    @pytest.fixture
    def analytics_engine(self, storage_manager):
        """Create an analytics engine for testing."""
        return AnalyticsEngine(storage_manager)
    
    def test_get_daily_summary(self, analytics_engine, sample_logs):
        """Test getting daily summary."""
        today = date.today()
        summary = analytics_engine.get_daily_summary(today)
        
        assert 'date' in summary
        assert 'summary' in summary
        assert 'workflow_metrics' in summary
        assert summary['date'] == today.isoformat()
    
    def test_get_weekly_summary(self, analytics_engine, sample_logs):
        """Test getting weekly summary."""
        start_date = date.today() - timedelta(days=6)
        summary = analytics_engine.get_weekly_summary(start_date)
        
        assert 'week_start' in summary
        assert 'week_end' in summary
        assert 'summary' in summary
        assert 'top_vendors' in summary
        assert 'workflow_metrics' in summary
    
    def test_get_monthly_summary(self, analytics_engine, sample_logs):
        """Test getting monthly summary."""
        today = date.today()
        summary = analytics_engine.get_monthly_summary(today.year, today.month)
        
        assert 'year' in summary
        assert 'month' in summary
        assert 'summary' in summary
        assert 'vendor_analysis' in summary
        assert 'payment_report' in summary
        assert 'workflow_metrics' in summary


class TestIntegration:
    """Integration tests for the reporting system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_full_reporting_workflow(self, temp_dir):
        """Test a complete reporting workflow."""
        # Setup
        log_file = temp_dir / "reporting_log.json"
        storage = JSONStorageManager(log_file)
        analytics = AnalyticsEngine(storage)
        
        # Create sample data
        for i in range(10):
            receipt_data = ReceiptData(
                vendor_name=f"Vendor {i % 4 + 1}",
                transaction_date=datetime.now() - timedelta(days=i),
                total_amount=Decimal(f"{20.00 + i * 5}"),
                currency=Currency.USD,
                extraction_confidence=0.8 + i * 0.02,
                has_required_data=True
            )
            
            status = ProcessingStatus.PROCESSED if i < 8 else ProcessingStatus.ERROR
            
            log = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/test/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 50,
                current_status=status,
                receipt_data=receipt_data,
                processing_time_seconds=0.5 + i * 0.1
            )
            
            storage.add_log_entry(log)
        
        # Test filtering and querying
        query_engine = analytics.query_engine
        filters = [FilterCondition("current_status", FilterOperator.EQUALS, "processed")]
        results = query_engine.query(QueryOptions(filters=filters))
        assert len(results) == 8
        
        # Test report generation
        summary = analytics.report_generator.generate_summary_report()
        assert summary.total_receipts == 10
        assert summary.processed_count == 8
        assert summary.error_count == 2
        
        # Test vendor analysis
        vendor_analysis = analytics.report_generator.generate_vendor_analysis()
        assert len(vendor_analysis) == 4  # 4 unique vendors
        
        # Test export
        json_path = temp_dir / "export.json"
        csv_path = temp_dir / "export.csv"
        
        assert analytics.export_manager.export_to_json(json_path)
        assert analytics.export_manager.export_to_csv(csv_path)
        
        assert json_path.exists()
        assert csv_path.exists()
        
        # Test analytics
        daily_summary = analytics.get_daily_summary(date.today())
        assert 'summary' in daily_summary
        assert 'workflow_metrics' in daily_summary
