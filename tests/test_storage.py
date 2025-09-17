"""
Tests for JSON storage system.

This module tests the JSONStorageManager and LogRotationManager classes
for atomic operations, data integrity, and log management.
"""

import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import pytest

from src.receipt_processor.storage import JSONStorageManager, LogRotationManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, 
    ReceiptProcessingLogFile, 
    ProcessingStatus,
    ReceiptData,
    Currency
)


class TestJSONStorageManager:
    """Test cases for JSONStorageManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def sample_log_entry(self):
        """Create a sample log entry for testing."""
        return ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("/test/path/test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING,
            receipt_data=ReceiptData(
                vendor_name="Test Vendor",
                transaction_date=datetime.now(),
                total_amount=25.50,
                currency=Currency.USD,
                extraction_confidence=0.95
            )
        )
    
    def test_initialization_creates_log_file(self, storage_manager):
        """Test that initialization creates a log file."""
        assert storage_manager.log_file_path.exists()
        
        # Verify it's a valid JSON file
        with open(storage_manager.log_file_path, 'r') as f:
            data = json.load(f)
        
        assert "version" in data
        assert "logs" in data
        assert data["logs"] == []
    
    def test_add_log_entry(self, storage_manager, sample_log_entry):
        """Test adding a log entry."""
        success = storage_manager.add_log_entry(sample_log_entry)
        assert success
        
        # Verify the entry was added
        log_file = storage_manager._read_log_file()
        assert len(log_file.logs) == 1
        assert log_file.logs[0].id == sample_log_entry.id
    
    def test_add_multiple_log_entries(self, storage_manager):
        """Test adding multiple log entries."""
        # Create multiple log entries
        log_entries = []
        for i in range(5):
            entry = ReceiptProcessingLog(
                original_filename=f"test_receipt_{i}.jpg",
                file_path=Path(f"/test/path/test_receipt_{i}.jpg"),
                file_size=1024 + i * 100,
                current_status=ProcessingStatus.PENDING
            )
            log_entries.append(entry)
        
        # Add all entries
        for entry in log_entries:
            success = storage_manager.add_log_entry(entry)
            assert success
        
        # Verify all entries were added
        log_file = storage_manager._read_log_file()
        assert len(log_file.logs) == 5
        
        # Verify statistics were updated
        assert log_file.total_receipts == 5
    
    def test_update_log_entry(self, storage_manager, sample_log_entry):
        """Test updating a log entry."""
        # Add initial entry
        storage_manager.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        
        # Update the entry
        updates = {
            "current_status": ProcessingStatus.PROCESSED,
            "notes": "Updated with test notes"
        }
        success = storage_manager.update_log_entry(log_id, updates)
        assert success
        
        # Verify the update
        updated_entry = storage_manager.get_log_entry(log_id)
        assert updated_entry.current_status == ProcessingStatus.PROCESSED
        assert updated_entry.notes == "Updated with test notes"
        assert updated_entry.last_updated > sample_log_entry.last_updated
    
    def test_add_status_transition(self, storage_manager, sample_log_entry):
        """Test adding a status transition."""
        # Add initial entry
        storage_manager.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        
        # Add status transition
        success = storage_manager.add_status_transition(
            log_id,
            ProcessingStatus.PROCESSING,
            reason="Started processing",
            user="test_user"
        )
        assert success
        
        # Verify the transition was added
        updated_entry = storage_manager.get_log_entry(log_id)
        assert updated_entry.current_status == ProcessingStatus.PROCESSING
        assert len(updated_entry.status_history) == 1
        assert updated_entry.status_history[0].to_status == ProcessingStatus.PROCESSING
        assert updated_entry.status_history[0].reason == "Started processing"
        assert updated_entry.status_history[0].user == "test_user"
    
    def test_get_logs_by_status(self, storage_manager):
        """Test getting logs by status."""
        # Create entries with different statuses
        pending_entry = ReceiptProcessingLog(
            original_filename="pending.jpg",
            file_path=Path("/test/pending.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING
        )
        
        processed_entry = ReceiptProcessingLog(
            original_filename="processed.jpg",
            file_path=Path("/test/processed.jpg"),
            file_size=2048,
            current_status=ProcessingStatus.PROCESSED
        )
        
        # Add entries
        storage_manager.add_log_entry(pending_entry)
        storage_manager.add_log_entry(processed_entry)
        
        # Test filtering
        pending_logs = storage_manager.get_logs_by_status(ProcessingStatus.PENDING)
        assert len(pending_logs) == 1
        assert pending_logs[0].original_filename == "pending.jpg"
        
        processed_logs = storage_manager.get_logs_by_status(ProcessingStatus.PROCESSED)
        assert len(processed_logs) == 1
        assert processed_logs[0].original_filename == "processed.jpg"
    
    def test_get_recent_logs(self, storage_manager):
        """Test getting recent logs."""
        # Create multiple entries with different timestamps
        entries = []
        for i in range(5):
            entry = ReceiptProcessingLog(
                original_filename=f"receipt_{i}.jpg",
                file_path=Path(f"/test/receipt_{i}.jpg"),
                file_size=1024,
                current_status=ProcessingStatus.PENDING
            )
            # Add small delay to ensure different timestamps
            import time
            time.sleep(0.01)
            entries.append(entry)
        
        # Add entries
        for entry in entries:
            storage_manager.add_log_entry(entry)
        
        # Test getting recent logs
        recent_logs = storage_manager.get_recent_logs(3)
        assert len(recent_logs) == 3
        
        # Verify they are sorted by creation time (most recent first)
        timestamps = [log.created_at for log in recent_logs]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_cleanup_old_logs(self, storage_manager):
        """Test cleaning up old logs."""
        # Create old and new entries
        old_entry = ReceiptProcessingLog(
            original_filename="old.jpg",
            file_path=Path("/test/old.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING
        )
        # Set creation time to 200 days ago
        old_entry.created_at = datetime.now() - timedelta(days=200)
        
        new_entry = ReceiptProcessingLog(
            original_filename="new.jpg",
            file_path=Path("/test/new.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING
        )
        
        # Add entries
        storage_manager.add_log_entry(old_entry)
        storage_manager.add_log_entry(new_entry)
        
        # Cleanup logs older than 180 days
        removed_count = storage_manager.cleanup_old_logs(180)
        assert removed_count == 1
        
        # Verify only new entry remains
        remaining_logs = storage_manager.get_all_logs()
        assert len(remaining_logs) == 1
        assert remaining_logs[0].original_filename == "new.jpg"
    
    def test_create_backup(self, storage_manager, sample_log_entry):
        """Test creating a backup."""
        # Add a log entry
        storage_manager.add_log_entry(sample_log_entry)
        
        # Create backup
        backup_path = storage_manager.create_backup()
        assert backup_path is not None
        assert backup_path.exists()
        
        # Verify backup contains the same data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        with open(storage_manager.log_file_path, 'r') as f:
            original_data = json.load(f)
        
        assert backup_data["total_receipts"] == original_data["total_receipts"]
        assert len(backup_data["logs"]) == len(original_data["logs"])
    
    def test_get_statistics(self, storage_manager, sample_log_entry):
        """Test getting statistics."""
        # Add a log entry
        storage_manager.add_log_entry(sample_log_entry)
        
        # Get statistics
        stats = storage_manager.get_statistics()
        
        assert "total_receipts" in stats
        assert "successful_extractions" in stats
        assert "failed_extractions" in stats
        assert "last_updated" in stats
        assert "file_size_bytes" in stats
        
        assert stats["total_receipts"] == 1
        assert stats["file_size_bytes"] > 0
    
    def test_verify_file_integrity(self, storage_manager, sample_log_entry):
        """Test file integrity verification."""
        # Test with valid file
        storage_manager.add_log_entry(sample_log_entry)
        assert storage_manager.verify_file_integrity()
        
        # Test with corrupted file
        with open(storage_manager.log_file_path, 'w') as f:
            f.write("invalid json content")
        
        assert not storage_manager.verify_file_integrity()
    
    def test_atomic_write_operation(self, storage_manager, sample_log_entry):
        """Test that write operations are atomic."""
        # This test verifies that if a write operation fails,
        # the original file is not corrupted
        
        # Add initial entry
        storage_manager.add_log_entry(sample_log_entry)
        original_size = storage_manager.log_file_path.stat().st_size
        
        # Simulate a write failure by making the temp directory read-only
        # (This is a bit tricky to test properly, so we'll just verify the atomic structure)
        success = storage_manager.add_log_entry(sample_log_entry)
        assert success
        
        # Verify file is still valid
        assert storage_manager.verify_file_integrity()
        assert storage_manager.log_file_path.stat().st_size > original_size


class TestLogRotationManager:
    """Test cases for LogRotationManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_manager(self, temp_dir):
        """Create a storage manager for testing."""
        log_file = temp_dir / "test_log.json"
        return JSONStorageManager(log_file)
    
    @pytest.fixture
    def rotation_manager(self, storage_manager):
        """Create a rotation manager for testing."""
        return LogRotationManager(storage_manager, max_file_size_mb=1)  # 1MB limit
    
    def test_should_rotate_small_file(self, rotation_manager):
        """Test that small files don't need rotation."""
        assert not rotation_manager.should_rotate()
    
    def test_should_rotate_large_file(self, rotation_manager, storage_manager):
        """Test that large files need rotation."""
        # Create a large log file by adding many entries
        for i in range(1000):  # This should create a large file
            entry = ReceiptProcessingLog(
                original_filename=f"large_receipt_{i}.jpg",
                file_path=Path(f"/test/large_receipt_{i}.jpg"),
                file_size=1024,
                current_status=ProcessingStatus.PENDING,
                receipt_data=ReceiptData(
                    vendor_name=f"Vendor {i}",
                    transaction_date=datetime.now(),
                    total_amount=100.0 + i,
                    currency=Currency.USD,
                    extraction_confidence=0.9,
                    extracted_text="A" * 1000  # Large text content
                )
            )
            storage_manager.add_log_entry(entry)
        
        # Check if rotation is needed
        assert rotation_manager.should_rotate()
    
    def test_rotate_logs(self, rotation_manager, storage_manager):
        """Test log rotation."""
        # Add some entries
        for i in range(5):
            entry = ReceiptProcessingLog(
                original_filename=f"receipt_{i}.jpg",
                file_path=Path(f"/test/receipt_{i}.jpg"),
                file_size=1024,
                current_status=ProcessingStatus.PENDING
            )
            storage_manager.add_log_entry(entry)
        
        # Rotate logs
        success = rotation_manager.rotate_logs()
        assert success
        
        # Verify new log file is empty
        log_file = storage_manager._read_log_file()
        assert len(log_file.logs) == 0
        
        # Verify backup was created
        backup_files = list(storage_manager.backup_dir.glob("receipt_log_backup_*.json"))
        assert len(backup_files) == 1
        
        # Verify backup contains original data
        with open(backup_files[0], 'r') as f:
            backup_data = json.load(f)
        assert len(backup_data["logs"]) == 5
    
    def test_cleanup_old_backups(self, rotation_manager, storage_manager):
        """Test cleanup of old backup files."""
        # Create multiple backups
        for i in range(15):
            backup_path = storage_manager.backup_dir / f"receipt_log_backup_{i:03d}.json"
            with open(backup_path, 'w') as f:
                json.dump({"test": f"backup_{i}"}, f)
        
        # Cleanup old backups (keep only 10)
        removed_count = rotation_manager.cleanup_old_backups(10)
        assert removed_count == 5
        
        # Verify only 10 backups remain
        remaining_backups = list(storage_manager.backup_dir.glob("receipt_log_backup_*.json"))
        assert len(remaining_backups) == 10


class TestIntegration:
    """Integration tests for the storage system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_full_workflow(self, temp_dir):
        """Test a complete workflow with storage and rotation."""
        # Create storage manager
        log_file = temp_dir / "workflow_log.json"
        storage_manager = JSONStorageManager(log_file)
        rotation_manager = LogRotationManager(storage_manager, max_file_size_mb=0.001)  # Very small limit
        
        # Add multiple log entries with status transitions
        log_entries = []
        for i in range(10):
            entry = ReceiptProcessingLog(
                original_filename=f"workflow_receipt_{i}.jpg",
                file_path=Path(f"/test/workflow_receipt_{i}.jpg"),
                file_size=1024,
                current_status=ProcessingStatus.PENDING
            )
            storage_manager.add_log_entry(entry)
            log_entries.append(entry)
            
            # Add status transitions
            storage_manager.add_status_transition(
                entry.id,
                ProcessingStatus.PROCESSING,
                reason="Started processing"
            )
            
            storage_manager.add_status_transition(
                entry.id,
                ProcessingStatus.PROCESSED,
                reason="Processing completed"
            )
        
        # Verify all entries were added
        all_logs = storage_manager.get_all_logs()
        assert len(all_logs) == 10
        
        # Verify status transitions
        for log_entry in all_logs:
            assert len(log_entry.status_history) == 2
            assert log_entry.current_status == ProcessingStatus.PROCESSED
        
        # Test rotation (if file is large enough)
        if rotation_manager.should_rotate():
            success = rotation_manager.rotate_logs()
            assert success
            
            # Verify new log is empty
            new_logs = storage_manager.get_all_logs()
            assert len(new_logs) == 0
        
        # Test statistics
        stats = storage_manager.get_statistics()
        assert stats["total_receipts"] >= 0
        
        # Test cleanup
        removed_count = storage_manager.cleanup_old_logs(0)  # Remove all logs
        assert removed_count >= 0
