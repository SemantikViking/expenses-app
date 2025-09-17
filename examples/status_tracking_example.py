#!/usr/bin/env python3
"""
Example usage of the Enhanced Status Tracking System.

This script demonstrates comprehensive status flow management, retry logic,
error categorization, timing measurement, and bulk operations for the
receipt processing workflow.
"""

import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Import the status tracking system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.receipt_processor.status_tracker import (
    EnhancedStatusTracker, StatusFlowValidator, RetryManager, 
    ErrorCategorizer, ProcessingMetrics, ErrorCategory, RetryStrategy
)
from src.receipt_processor.storage import JSONStorageManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)


def main():
    """Demonstrate the enhanced status tracking functionality."""
    print("🔄 Enhanced Status Tracking System Demo")
    print("=" * 50)
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        log_file = temp_path / "status_demo_log.json"
        
        print(f"📁 Using temporary directory: {temp_path}")
        print(f"📄 Log file: {log_file}")
        print()
        
        # Initialize storage and status tracker
        print("🔧 Initializing status tracking system...")
        storage = JSONStorageManager(log_file)
        tracker = EnhancedStatusTracker(storage)
        print("✅ Status tracking system initialized")
        print()
        
        # Demonstrate status flow validation
        print("🔍 Demonstrating status flow validation...")
        validator = StatusFlowValidator()
        
        # Valid transitions
        valid_transitions = [
            (ProcessingStatus.PENDING, ProcessingStatus.PROCESSING),
            (ProcessingStatus.PROCESSING, ProcessingStatus.PROCESSED),
            (ProcessingStatus.PROCESSED, ProcessingStatus.EMAILED),
            (ProcessingStatus.EMAILED, ProcessingStatus.SUBMITTED),
            (ProcessingStatus.SUBMITTED, ProcessingStatus.PAYMENT_RECEIVED)
        ]
        
        for from_status, to_status in valid_transitions:
            is_valid, error_msg = validator.validate_transition(from_status, to_status)
            print(f"  ✅ {from_status.value} → {to_status.value}: {'Valid' if is_valid else 'Invalid'}")
        
        # Invalid transitions
        invalid_transitions = [
            (ProcessingStatus.PENDING, ProcessingStatus.PROCESSED),  # Skip PROCESSING
            (ProcessingStatus.PROCESSED, ProcessingStatus.PENDING),  # Backwards
            (ProcessingStatus.PAYMENT_RECEIVED, ProcessingStatus.PROCESSED)  # Terminal state
        ]
        
        for from_status, to_status in invalid_transitions:
            is_valid, error_msg = validator.validate_transition(from_status, to_status)
            print(f"  ❌ {from_status.value} → {to_status.value}: {'Valid' if is_valid else 'Invalid'}")
        print()
        
        # Demonstrate error categorization
        print("🏷️  Demonstrating error categorization...")
        categorizer = ErrorCategorizer()
        
        test_errors = [
            "OpenAI API rate limit exceeded",
            "Invalid image format detected",
            "Validation failed: missing required field",
            "File not found: receipt.jpg",
            "Network connection timeout",
            "Missing configuration setting",
            "Operation timed out",
            "Some random error message"
        ]
        
        for error_msg in test_errors:
            category = categorizer.categorize_error(error_msg)
            priority = categorizer.get_error_priority(category)
            print(f"  📝 '{error_msg}' → {category.value} (priority: {priority})")
        print()
        
        # Demonstrate retry management
        print("🔄 Demonstrating retry management...")
        retry_manager = RetryManager(max_retries=3, base_delay=1.0)
        
        # Test retry logic
        log_id = "test-log-123"
        print(f"  📊 Testing retry logic for log: {log_id}")
        
        for attempt in range(5):
            should_retry = retry_manager.should_retry(log_id, ErrorCategory.AI_EXTRACTION_ERROR)
            delay = retry_manager.get_retry_delay(log_id, RetryStrategy.EXPONENTIAL_BACKOFF)
            can_retry_now = retry_manager.can_retry_now(log_id, RetryStrategy.EXPONENTIAL_BACKOFF)
            
            print(f"    Attempt {attempt + 1}: Should retry: {should_retry}, Delay: {delay:.1f}s, Can retry now: {can_retry_now}")
            
            if should_retry:
                retry_manager.record_retry(log_id)
            else:
                print(f"    ❌ Max retries ({retry_manager.max_retries}) exceeded")
                break
        print()
        
        # Create sample log entries
        print("📋 Creating sample log entries...")
        log_entries = []
        
        for i in range(5):
            entry = ReceiptProcessingLog(
                original_filename=f"demo_receipt_{i+1}.jpg",
                file_path=Path(f"/receipts/demo_receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,
                current_status=ProcessingStatus.PENDING
            )
            storage.add_log_entry(entry)
            log_entries.append(entry)
            print(f"  ✅ Created log entry {i+1}: {entry.original_filename}")
        print()
        
        # Demonstrate processing workflow
        print("⚙️  Demonstrating processing workflow...")
        
        for i, log_entry in enumerate(log_entries):
            log_id = log_entry.id
            print(f"  📄 Processing log {i+1}: {log_entry.original_filename}")
            
            # Start processing
            success = tracker.start_processing(log_id)
            if success:
                print(f"    ✅ Started processing")
                
                # Simulate processing time
                time.sleep(0.1)
                
                # Simulate different outcomes
                if i == 0:  # Success
                    receipt_data = ReceiptData(
                        vendor_name=f"Demo Vendor {i+1}",
                        transaction_date=datetime.now(),
                        total_amount=Decimal(f"{25.50 + i * 10}"),
                        currency=Currency.USD,
                        extraction_confidence=0.95,
                        has_required_data=True
                    )
                    success = tracker.complete_processing(log_id, receipt_data)
                    if success:
                        print(f"    ✅ Processing completed successfully")
                
                elif i == 1:  # No data extracted
                    success = tracker.complete_processing(log_id, None)
                    if success:
                        print(f"    ⚠️  Processing completed - no data extracted")
                
                elif i == 2:  # Error with retry
                    success = tracker.record_error(log_id, "Temporary network error", should_retry=True)
                    if success:
                        print(f"    🔄 Error recorded - scheduled for retry")
                
                elif i == 3:  # Error without retry
                    success = tracker.record_error(log_id, "Configuration error", should_retry=True)
                    if success:
                        print(f"    ❌ Error recorded - no retry (config error)")
                
                else:  # Success after retry
                    receipt_data = ReceiptData(
                        vendor_name=f"Demo Vendor {i+1}",
                        transaction_date=datetime.now(),
                        total_amount=Decimal(f"{25.50 + i * 10}"),
                        currency=Currency.USD,
                        extraction_confidence=0.88,
                        has_required_data=True
                    )
                    success = tracker.complete_processing(log_id, receipt_data)
                    if success:
                        print(f"    ✅ Processing completed after retry")
            else:
                print(f"    ❌ Failed to start processing")
        print()
        
        # Demonstrate bulk operations
        print("📦 Demonstrating bulk operations...")
        
        # Get all pending logs
        pending_logs = storage.get_logs_by_status(ProcessingStatus.PENDING)
        if pending_logs:
            log_ids = [log.id for log in pending_logs]
            print(f"  📊 Found {len(log_ids)} pending logs")
            
            # Bulk update to processing
            results = tracker.bulk_update_status(
                log_ids, ProcessingStatus.PROCESSING, "Bulk processing start"
            )
            successful = sum(1 for success in results.values() if success)
            print(f"  ✅ Bulk update completed: {successful}/{len(log_ids)} successful")
        else:
            print("  📊 No pending logs found")
        print()
        
        # Demonstrate status queries
        print("🔍 Demonstrating status queries...")
        
        for status in [ProcessingStatus.PROCESSED, ProcessingStatus.ERROR, ProcessingStatus.RETRY, ProcessingStatus.NO_DATA_EXTRACTED]:
            logs = storage.get_logs_by_status(status)
            print(f"  📊 {status.value}: {len(logs)} logs")
        print()
        
        # Demonstrate error summary
        print("📈 Demonstrating error summary...")
        error_summary = tracker.get_error_summary()
        print(f"  📊 Total errors: {error_summary['total_errors']}")
        print(f"  📊 Total retries: {error_summary['total_retries']}")
        print(f"  📊 By category: {error_summary['by_category']}")
        print(f"  📊 By priority: {error_summary['by_priority']}")
        print()
        
        # Demonstrate processing statistics
        print("📊 Demonstrating processing statistics...")
        stats = tracker.get_processing_statistics()
        print(f"  📊 Total receipts: {stats['total_receipts']}")
        print(f"  📊 By status: {stats['by_status']}")
        if 'avg_processing_time' in stats:
            print(f"  📊 Average processing time: {stats['avg_processing_time']:.2f}s")
            print(f"  📊 Min processing time: {stats['min_processing_time']:.2f}s")
            print(f"  📊 Max processing time: {stats['max_processing_time']:.2f}s")
        if 'error_rate' in stats:
            print(f"  📊 Error rate: {stats['error_rate']:.2%}")
            print(f"  📊 Retry rate: {stats['retry_rate']:.2%}")
        print()
        
        # Demonstrate retry candidates
        print("🔄 Demonstrating retry candidates...")
        retry_candidates = tracker.get_retry_candidates()
        print(f"  📊 Found {len(retry_candidates)} retry candidates")
        for candidate_id in retry_candidates:
            print(f"    🔄 {candidate_id}")
        print()
        
        # Demonstrate status transition history
        print("📜 Demonstrating status transition history...")
        all_logs = storage.get_all_logs()
        for i, log_entry in enumerate(all_logs[:3]):  # Show first 3 logs
            print(f"  📄 Log {i+1}: {log_entry.original_filename}")
            print(f"    Current status: {log_entry.current_status.value}")
            print(f"    Status history:")
            for j, transition in enumerate(log_entry.status_history):
                from_status = transition.from_status.value if transition.from_status else "None"
                print(f"      {j+1}. {from_status} → {transition.to_status.value} ({transition.timestamp.strftime('%H:%M:%S')})")
                if transition.reason:
                    print(f"         Reason: {transition.reason}")
            print()
        
        print("🎉 Enhanced status tracking demo completed successfully!")
        print(f"📁 Final log file: {log_file}")
        print(f"📊 Final log file size: {log_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
