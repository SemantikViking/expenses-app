#!/usr/bin/env python3
"""
Example usage of the JSON storage system for receipt processing logs.

This script demonstrates how to use the JSONStorageManager and LogRotationManager
to manage receipt processing logs with atomic operations and data safety.
"""

import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Import the storage system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.receipt_processor.storage import JSONStorageManager, LogRotationManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, 
    ReceiptData, 
    ProcessingStatus, 
    Currency
)


def main():
    """Demonstrate the storage system functionality."""
    print("🗂️  Receipt Processing Storage System Demo")
    print("=" * 50)
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        log_file = temp_path / "receipt_log.json"
        
        print(f"📁 Using temporary directory: {temp_path}")
        print(f"📄 Log file: {log_file}")
        print()
        
        # Initialize storage manager
        print("🔧 Initializing storage manager...")
        storage = JSONStorageManager(log_file)
        print("✅ Storage manager initialized")
        print()
        
        # Create sample receipt data
        print("📝 Creating sample receipt data...")
        sample_receipts = [
            ReceiptData(
                vendor_name="Starbucks Coffee",
                transaction_date=datetime.now() - timedelta(days=1),
                total_amount=Decimal("12.50"),
                currency=Currency.USD,
                extraction_confidence=0.95,
                has_required_data=True
            ),
            ReceiptData(
                vendor_name="Whole Foods Market",
                transaction_date=datetime.now() - timedelta(days=2),
                total_amount=Decimal("89.99"),
                currency=Currency.USD,
                extraction_confidence=0.88,
                has_required_data=True
            ),
            ReceiptData(
                vendor_name="Uber",
                transaction_date=datetime.now() - timedelta(days=3),
                total_amount=Decimal("24.75"),
                currency=Currency.USD,
                extraction_confidence=0.92,
                has_required_data=True
            )
        ]
        
        # Create log entries
        print("📋 Creating log entries...")
        log_entries = []
        for i, receipt_data in enumerate(sample_receipts):
            log_entry = ReceiptProcessingLog(
                original_filename=f"receipt_{i+1}.jpg",
                file_path=Path(f"/receipts/receipt_{i+1}.jpg"),
                file_size=1024 * (i + 1) * 100,  # Varying file sizes
                current_status=ProcessingStatus.PENDING,
                receipt_data=receipt_data
            )
            log_entries.append(log_entry)
        
        print(f"✅ Created {len(log_entries)} log entries")
        print()
        
        # Add log entries to storage
        print("💾 Adding log entries to storage...")
        for i, log_entry in enumerate(log_entries):
            success = storage.add_log_entry(log_entry)
            if success:
                print(f"  ✅ Added entry {i+1}: {log_entry.original_filename}")
            else:
                print(f"  ❌ Failed to add entry {i+1}")
        print()
        
        # Demonstrate status transitions
        print("🔄 Demonstrating status transitions...")
        for i, log_entry in enumerate(log_entries):
            # Transition to processing
            storage.add_status_transition(
                log_entry.id,
                ProcessingStatus.PROCESSING,
                reason="Started AI processing",
                user="system"
            )
            print(f"  📊 Entry {i+1}: PENDING → PROCESSING")
            
            # Transition to processed
            storage.add_status_transition(
                log_entry.id,
                ProcessingStatus.PROCESSED,
                reason="AI processing completed successfully",
                user="system"
            )
            print(f"  ✅ Entry {i+1}: PROCESSING → PROCESSED")
        print()
        
        # Query logs by status
        print("🔍 Querying logs by status...")
        processed_logs = storage.get_logs_by_status(ProcessingStatus.PROCESSED)
        print(f"  📊 Found {len(processed_logs)} processed receipts")
        
        pending_logs = storage.get_logs_by_status(ProcessingStatus.PENDING)
        print(f"  ⏳ Found {len(pending_logs)} pending receipts")
        print()
        
        # Get recent logs
        print("📅 Getting recent logs...")
        recent_logs = storage.get_recent_logs(2)
        for i, log in enumerate(recent_logs):
            print(f"  {i+1}. {log.original_filename} - {log.current_status} - ${log.receipt_data.total_amount}")
        print()
        
        # Get statistics
        print("📈 Storage statistics...")
        stats = storage.get_statistics()
        print(f"  📊 Total receipts: {stats['total_receipts']}")
        print(f"  ✅ Successful extractions: {stats['successful_extractions']}")
        print(f"  ❌ Failed extractions: {stats['failed_extractions']}")
        print(f"  📁 File size: {stats['file_size_bytes']} bytes")
        print(f"  🕒 Last updated: {stats['last_updated']}")
        print()
        
        # Demonstrate log rotation
        print("🔄 Demonstrating log rotation...")
        rotation_manager = LogRotationManager(storage, max_file_size_mb=0.001)  # Very small limit
        
        if rotation_manager.should_rotate():
            print("  📊 Log file is large enough for rotation")
            backup_path = storage.create_backup()
            if backup_path:
                print(f"  💾 Backup created: {backup_path.name}")
            
            success = rotation_manager.rotate_logs()
            if success:
                print("  ✅ Log rotation completed")
            else:
                print("  ❌ Log rotation failed")
        else:
            print("  📊 Log file is not large enough for rotation")
        print()
        
        # Demonstrate cleanup
        print("🧹 Demonstrating log cleanup...")
        # Create an old log entry
        old_log = ReceiptProcessingLog(
            original_filename="old_receipt.jpg",
            file_path=Path("/receipts/old_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED
        )
        # Set creation time to 200 days ago
        old_log.created_at = datetime.now() - timedelta(days=200)
        storage.add_log_entry(old_log)
        
        print(f"  📊 Total logs before cleanup: {len(storage.get_all_logs())}")
        removed_count = storage.cleanup_old_logs(180)  # Remove logs older than 180 days
        print(f"  🗑️  Removed {removed_count} old log entries")
        print(f"  📊 Total logs after cleanup: {len(storage.get_all_logs())}")
        print()
        
        # Verify file integrity
        print("🔍 Verifying file integrity...")
        is_valid = storage.verify_file_integrity()
        if is_valid:
            print("  ✅ Log file integrity verified")
        else:
            print("  ❌ Log file integrity check failed")
        print()
        
        print("🎉 Storage system demo completed successfully!")
        print(f"📁 Final log file: {log_file}")
        print(f"📊 Final log file size: {log_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
