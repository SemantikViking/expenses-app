#!/usr/bin/env python3
"""
Example usage of the Enhanced Reporting & Analytics System.

This script demonstrates comprehensive filtering, search, reporting, analytics,
and export capabilities for the receipt processing workflow.
"""

import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta, date
from decimal import Decimal

# Import the reporting system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.receipt_processor.reporting import (
    FilterOperator, SortDirection, FilterCondition, SortCondition, QueryOptions,
    ReportSummary, VendorAnalysis, WorkflowMetrics, LogFilter, LogSorter,
    LogQueryEngine, ReportGenerator, ExportManager, AnalyticsEngine
)
from src.receipt_processor.storage import JSONStorageManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency, StatusTransition
)


def main():
    """Demonstrate the enhanced reporting and analytics functionality."""
    print("📊 Enhanced Reporting & Analytics System Demo")
    print("=" * 60)
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        log_file = temp_path / "reporting_demo_log.json"
        
        print(f"📁 Using temporary directory: {temp_path}")
        print(f"📄 Log file: {log_file}")
        print()
        
        # Initialize storage and analytics engine
        print("🔧 Initializing reporting system...")
        storage = JSONStorageManager(log_file)
        analytics = AnalyticsEngine(storage)
        print("✅ Reporting system initialized")
        print()
        
        # Create sample data
        print("📋 Creating sample receipt data...")
        sample_data = create_sample_data(storage)
        print(f"✅ Created {len(sample_data)} sample receipt entries")
        print()
        
        # Demonstrate filtering capabilities
        print("🔍 Demonstrating advanced filtering...")
        demonstrate_filtering(analytics)
        print()
        
        # Demonstrate search and query capabilities
        print("🔎 Demonstrating search and query capabilities...")
        demonstrate_search_and_query(analytics)
        print()
        
        # Demonstrate report generation
        print("📈 Demonstrating report generation...")
        demonstrate_report_generation(analytics)
        print()
        
        # Demonstrate payment reports
        print("💰 Demonstrating payment reports...")
        demonstrate_payment_reports(analytics, storage)
        print()
        
        # Demonstrate audit reports
        print("📜 Demonstrating audit reports...")
        demonstrate_audit_reports(analytics)
        print()
        
        # Demonstrate export functionality
        print("📤 Demonstrating export functionality...")
        demonstrate_export_functionality(analytics, temp_path)
        print()
        
        # Demonstrate analytics and statistics
        print("📊 Demonstrating analytics and statistics...")
        demonstrate_analytics(analytics)
        print()
        
        print("🎉 Enhanced reporting and analytics demo completed successfully!")
        print(f"📁 Final log file: {log_file}")
        print(f"📊 Final log file size: {log_file.stat().st_size} bytes")


def create_sample_data(storage):
    """Create comprehensive sample data for demonstration."""
    sample_data = []
    
    # Create diverse sample data
    vendors = [
        "Apple Store", "Amazon", "Starbucks", "Target", "Walmart",
        "McDonald's", "Subway", "CVS Pharmacy", "Home Depot", "Best Buy"
    ]
    
    statuses = [
        ProcessingStatus.PROCESSED,
        ProcessingStatus.PROCESSED,
        ProcessingStatus.PROCESSED,
        ProcessingStatus.ERROR,
        ProcessingStatus.PENDING,
        ProcessingStatus.RETRY,
        ProcessingStatus.EMAILED,
        ProcessingStatus.SUBMITTED,
        ProcessingStatus.PAYMENT_RECEIVED,
        ProcessingStatus.NO_DATA_EXTRACTED
    ]
    
    for i in range(20):
        # Create receipt data
        vendor = vendors[i % len(vendors)]
        amount = Decimal(f"{15.99 + i * 2.50}")
        transaction_date = datetime.now() - timedelta(days=i % 30)
        
        receipt_data = ReceiptData(
            vendor_name=vendor,
            transaction_date=transaction_date,
            total_amount=amount,
            currency=Currency.USD,
            extraction_confidence=0.85 + (i % 15) * 0.01,
            has_required_data=True
        )
        
        # Create log entry
        log = ReceiptProcessingLog(
            original_filename=f"receipt_{i+1:03d}.jpg",
            file_path=Path(f"/receipts/receipt_{i+1:03d}.jpg"),
            file_size=1024 * (500 + i * 100),
            current_status=statuses[i % len(statuses)],
            receipt_data=receipt_data,
            processing_time_seconds=0.5 + i * 0.1,
            confidence_score=0.85 + (i % 15) * 0.01
        )
        
        # Add some status transitions
        if i % 3 == 0:  # Every third receipt has transitions
            log.status_history = [
                StatusTransition(
                    from_status=ProcessingStatus.PENDING,
                    to_status=ProcessingStatus.PROCESSING,
                    timestamp=datetime.now() - timedelta(hours=2),
                    reason="Processing started",
                    user="system"
                ),
                StatusTransition(
                    from_status=ProcessingStatus.PROCESSING,
                    to_status=log.current_status,
                    timestamp=datetime.now() - timedelta(hours=1),
                    reason="Processing completed",
                    user="system"
                )
            ]
        
        storage.add_log_entry(log)
        sample_data.append(log)
    
    return sample_data


def demonstrate_filtering(analytics):
    """Demonstrate advanced filtering capabilities."""
    query_engine = analytics.query_engine
    
    # Filter by status
    print("  📊 Filtering by status (PROCESSED)...")
    filters = [FilterCondition("current_status", FilterOperator.EQUALS, "processed")]
    processed_logs = query_engine.query(QueryOptions(filters=filters))
    print(f"    Found {len(processed_logs)} processed receipts")
    
    # Filter by vendor
    print("  🏪 Filtering by vendor (Apple Store)...")
    filters = [FilterCondition("vendor_name", FilterOperator.CONTAINS, "Apple")]
    apple_logs = query_engine.query(QueryOptions(filters=filters))
    print(f"    Found {len(apple_logs)} Apple Store receipts")
    
    # Filter by amount range
    print("  💵 Filtering by amount range ($20-$50)...")
    filters = [FilterCondition("total_amount", FilterOperator.BETWEEN, [20, 50])]
    amount_logs = query_engine.query(QueryOptions(filters=filters))
    print(f"    Found {len(amount_logs)} receipts in amount range")
    
    # Filter by date range
    print("  📅 Filtering by date range (last 7 days)...")
    start_date = datetime.now() - timedelta(days=7)
    filters = [
        FilterCondition("transaction_date", FilterOperator.GREATER_EQUAL, start_date)
    ]
    recent_logs = query_engine.query(QueryOptions(filters=filters))
    print(f"    Found {len(recent_logs)} receipts from last 7 days")
    
    # Complex filtering
    print("  🔍 Complex filtering (processed + high confidence)...")
    filters = [
        FilterCondition("current_status", FilterOperator.EQUALS, "processed"),
        FilterCondition("extraction_confidence", FilterOperator.GREATER_THAN, 0.9)
    ]
    complex_logs = query_engine.query(QueryOptions(filters=filters))
    print(f"    Found {len(complex_logs)} high-confidence processed receipts")


def demonstrate_search_and_query(analytics):
    """Demonstrate search and query capabilities."""
    query_engine = analytics.query_engine
    
    # Sorting
    print("  📈 Sorting by amount (descending)...")
    sort_conditions = [SortCondition("total_amount", SortDirection.DESC)]
    sorted_logs = query_engine.query(QueryOptions(sort_by=sort_conditions))
    print(f"    Top 3 amounts: {[float(log.receipt_data.total_amount) for log in sorted_logs[:3]]}")
    
    # Pagination
    print("  📄 Pagination (page 2, 5 items per page)...")
    paginated_logs = query_engine.query(QueryOptions(limit=5, offset=5))
    print(f"    Retrieved {len(paginated_logs)} logs for page 2")
    
    # Distinct values
    print("  🏷️  Getting distinct vendors...")
    vendors = query_engine.get_distinct_values("vendor_name")
    print(f"    Found {len(vendors)} unique vendors: {vendors[:5]}...")
    
    # Counting
    print("  🔢 Counting by status...")
    for status in ["processed", "error", "pending"]:
        filters = [FilterCondition("current_status", FilterOperator.EQUALS, status)]
        count = query_engine.count(filters)
        print(f"    {status.capitalize()}: {count} receipts")


def demonstrate_report_generation(analytics):
    """Demonstrate report generation capabilities."""
    report_generator = analytics.report_generator
    
    # Summary report
    print("  📊 Generating summary report...")
    summary = report_generator.generate_summary_report()
    print(f"    Total receipts: {summary.total_receipts}")
    print(f"    Success rate: {summary.success_rate:.1%}")
    print(f"    Error rate: {summary.error_rate:.1%}")
    print(f"    Total amount: ${summary.total_amount}")
    print(f"    Unique vendors: {summary.unique_vendors}")
    
    # Vendor analysis
    print("  🏪 Generating vendor analysis...")
    vendor_analysis = report_generator.generate_vendor_analysis()
    print(f"    Top 3 vendors by amount:")
    for i, vendor in enumerate(vendor_analysis[:3]):
        print(f"      {i+1}. {vendor.vendor_name}: ${vendor.total_amount} ({vendor.receipt_count} receipts)")
    
    # Workflow metrics
    print("  ⚙️  Generating workflow metrics...")
    workflow_metrics = report_generator.generate_workflow_metrics()
    print(f"    Average processing time: {workflow_metrics.avg_processing_time:.2f}s")
    print(f"    Median processing time: {workflow_metrics.median_processing_time:.2f}s")
    print(f"    P95 processing time: {workflow_metrics.p95_processing_time:.2f}s")
    print(f"    Workflow efficiency: {workflow_metrics.workflow_efficiency:.1%}")


def demonstrate_payment_reports(analytics, storage):
    """Demonstrate payment reporting capabilities."""
    report_generator = analytics.report_generator
    
    # Update some logs to have payment status
    all_logs = storage.get_all_logs()
    for i, log in enumerate(all_logs[:5]):  # First 5 logs
        if i < 3:  # First 3 submitted
            log.current_status = ProcessingStatus.SUBMITTED
            storage.update_log_entry(log.id, {"current_status": ProcessingStatus.SUBMITTED})
            
            if i == 0:  # First one paid
                log.current_status = ProcessingStatus.PAYMENT_RECEIVED
                log.payment_received_at = datetime.now()
                log.payment_reference = f"PAY-{i+1:03d}"
                storage.update_log_entry(log.id, {
                    "current_status": ProcessingStatus.PAYMENT_RECEIVED,
                    "payment_received_at": log.payment_received_at,
                    "payment_reference": log.payment_reference
                })
    
    print("  💰 Generating payment report...")
    payment_report = report_generator.generate_payment_report()
    print(f"    Total receipts: {payment_report['total_receipts']}")
    print(f"    Submitted receipts: {payment_report['submitted_receipts']}")
    print(f"    Payment received: {payment_report['payment_received']}")
    print(f"    Outstanding payments: {payment_report['outstanding_payments']}")
    print(f"    Total submitted amount: ${payment_report['total_submitted_amount']}")
    print(f"    Total paid amount: ${payment_report['total_paid_amount']}")
    print(f"    Outstanding amount: ${payment_report['outstanding_amount']}")


def demonstrate_audit_reports(analytics):
    """Demonstrate audit reporting capabilities."""
    report_generator = analytics.report_generator
    
    # Single log audit
    all_logs = analytics.storage.get_all_logs()
    if all_logs:
        log_id = str(all_logs[0].id)
        print(f"  📜 Generating single log audit for {log_id}...")
        single_audit = report_generator.generate_audit_report(log_id=log_id)
        if 'error' not in single_audit:
            print(f"    Log ID: {single_audit['log_id']}")
            print(f"    Filename: {single_audit['original_filename']}")
            print(f"    Status: {single_audit['current_status']}")
            print(f"    Status transitions: {len(single_audit['status_history'])}")
        else:
            print(f"    Error: {single_audit['error']}")
    
    # Multiple logs audit
    print("  📜 Generating multiple logs audit...")
    multi_audit = report_generator.generate_audit_report()
    print(f"    Total logs: {multi_audit['total_logs']}")
    print(f"    Date range: {multi_audit['date_range']['start']} to {multi_audit['date_range']['end']}")


def demonstrate_export_functionality(analytics, temp_path):
    """Demonstrate export functionality."""
    export_manager = analytics.export_manager
    
    # Export to JSON
    json_path = temp_path / "receipts_export.json"
    print(f"  📤 Exporting to JSON: {json_path}")
    success = export_manager.export_to_json(json_path)
    if success:
        print(f"    ✅ JSON export successful")
        with open(json_path, 'r') as f:
            data = json.load(f)
        print(f"    📊 Exported {len(data)} receipts")
    
    # Export to CSV
    csv_path = temp_path / "receipts_export.csv"
    print(f"  📤 Exporting to CSV: {csv_path}")
    success = export_manager.export_to_csv(csv_path)
    if success:
        print(f"    ✅ CSV export successful")
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        print(f"    📊 Exported {len(lines)-1} data rows (plus header)")
    
    # Export with filters
    filtered_json_path = temp_path / "filtered_receipts.json"
    print(f"  📤 Exporting filtered data (processed only)...")
    filters = [FilterCondition("current_status", FilterOperator.EQUALS, "processed")]
    success = export_manager.export_to_json(filtered_json_path, filters=filters)
    if success:
        print(f"    ✅ Filtered export successful")
        with open(filtered_json_path, 'r') as f:
            data = json.load(f)
        print(f"    📊 Exported {len(data)} processed receipts")


def demonstrate_analytics(analytics):
    """Demonstrate analytics and statistics capabilities."""
    # Daily summary
    print("  📅 Generating daily summary...")
    today = date.today()
    daily_summary = analytics.get_daily_summary(today)
    print(f"    Date: {daily_summary['date']}")
    print(f"    Total receipts: {daily_summary['summary']['total_receipts']}")
    print(f"    Success rate: {daily_summary['summary']['success_rate']:.1%}")
    
    # Weekly summary
    print("  📅 Generating weekly summary...")
    week_start = today - timedelta(days=6)
    weekly_summary = analytics.get_weekly_summary(week_start)
    print(f"    Week: {weekly_summary['week_start']} to {weekly_summary['week_end']}")
    print(f"    Total receipts: {weekly_summary['summary']['total_receipts']}")
    print(f"    Top vendors: {len(weekly_summary['top_vendors'])}")
    
    # Monthly summary
    print("  📅 Generating monthly summary...")
    monthly_summary = analytics.get_monthly_summary(today.year, today.month)
    print(f"    Month: {monthly_summary['year']}-{monthly_summary['month']:02d}")
    print(f"    Total receipts: {monthly_summary['summary']['total_receipts']}")
    print(f"    Vendor analysis: {len(monthly_summary['vendor_analysis'])} vendors")
    print(f"    Payment report: {monthly_summary['payment_report']['total_receipts']} receipts")


if __name__ == "__main__":
    main()
