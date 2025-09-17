"""
Tests for Enhanced Status Tracking System.

This module tests the status flow validation, retry logic, error categorization,
timing measurement, and bulk operations for the receipt processing workflow.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import pytest

from src.receipt_processor.status_tracker import (
    StatusFlowValidator, RetryManager, ErrorCategorizer, ProcessingMetrics,
    EnhancedStatusTracker, ErrorCategory, RetryStrategy
)
from src.receipt_processor.storage import JSONStorageManager
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)


class TestStatusFlowValidator:
    """Test cases for status flow validation."""
    
    def test_valid_transitions(self):
        """Test that valid transitions are accepted."""
        # PENDING -> PROCESSING
        assert StatusFlowValidator.is_valid_transition(
            ProcessingStatus.PENDING, ProcessingStatus.PROCESSING
        )
        
        # PROCESSING -> PROCESSED
        assert StatusFlowValidator.is_valid_transition(
            ProcessingStatus.PROCESSING, ProcessingStatus.PROCESSED
        )
        
        # PROCESSED -> EMAILED
        assert StatusFlowValidator.is_valid_transition(
            ProcessingStatus.PROCESSED, ProcessingStatus.EMAILED
        )
        
        # EMAILED -> SUBMITTED
        assert StatusFlowValidator.is_valid_transition(
            ProcessingStatus.EMAILED, ProcessingStatus.SUBMITTED
        )
        
        # SUBMITTED -> PAYMENT_RECEIVED
        assert StatusFlowValidator.is_valid_transition(
            ProcessingStatus.SUBMITTED, ProcessingStatus.PAYMENT_RECEIVED
        )
    
    def test_invalid_transitions(self):
        """Test that invalid transitions are rejected."""
        # PENDING -> PROCESSED (must go through PROCESSING)
        assert not StatusFlowValidator.is_valid_transition(
            ProcessingStatus.PENDING, ProcessingStatus.PROCESSED
        )
        
        # PROCESSED -> PENDING (can't go backwards)
        assert not StatusFlowValidator.is_valid_transition(
            ProcessingStatus.PROCESSED, ProcessingStatus.PENDING
        )
        
        # PAYMENT_RECEIVED -> any status (terminal state)
        assert not StatusFlowValidator.is_valid_transition(
            ProcessingStatus.PAYMENT_RECEIVED, ProcessingStatus.PROCESSED
        )
    
    def test_get_valid_next_statuses(self):
        """Test getting valid next statuses."""
        # PENDING can go to PROCESSING or ERROR
        next_statuses = StatusFlowValidator.get_valid_next_statuses(ProcessingStatus.PENDING)
        assert ProcessingStatus.PROCESSING in next_statuses
        assert ProcessingStatus.ERROR in next_statuses
        assert ProcessingStatus.PROCESSED not in next_statuses
        
        # PROCESSING can go to multiple statuses
        next_statuses = StatusFlowValidator.get_valid_next_statuses(ProcessingStatus.PROCESSING)
        assert ProcessingStatus.PROCESSED in next_statuses
        assert ProcessingStatus.ERROR in next_statuses
        assert ProcessingStatus.NO_DATA_EXTRACTED in next_statuses
        assert ProcessingStatus.RETRY in next_statuses
    
    def test_validate_transition_with_error_message(self):
        """Test validation with error message."""
        # Valid transition
        is_valid, error_msg = StatusFlowValidator.validate_transition(
            ProcessingStatus.PENDING, ProcessingStatus.PROCESSING
        )
        assert is_valid
        assert error_msg is None
        
        # Invalid transition
        is_valid, error_msg = StatusFlowValidator.validate_transition(
            ProcessingStatus.PENDING, ProcessingStatus.PROCESSED
        )
        assert not is_valid
        assert error_msg is not None
        assert "Invalid transition" in error_msg


class TestRetryManager:
    """Test cases for retry management."""
    
    @pytest.fixture
    def retry_manager(self):
        """Create a retry manager for testing."""
        return RetryManager(max_retries=3, base_delay=1.0)
    
    def test_should_retry_within_limits(self, retry_manager):
        """Test retry logic within limits."""
        log_id = uuid4()
        
        # Should retry for first few attempts
        assert retry_manager.should_retry(log_id, ErrorCategory.AI_EXTRACTION_ERROR)
        retry_manager.record_retry(log_id)
        assert retry_manager.should_retry(log_id, ErrorCategory.AI_EXTRACTION_ERROR)
        retry_manager.record_retry(log_id)
        assert retry_manager.should_retry(log_id, ErrorCategory.AI_EXTRACTION_ERROR)
        retry_manager.record_retry(log_id)
        
        # Should not retry after max retries
        assert not retry_manager.should_retry(log_id, ErrorCategory.AI_EXTRACTION_ERROR)
    
    def test_should_not_retry_certain_errors(self, retry_manager):
        """Test that certain errors are not retried."""
        log_id = uuid4()
        
        # Configuration errors should not be retried
        assert not retry_manager.should_retry(log_id, ErrorCategory.CONFIGURATION_ERROR)
        
        # Data validation errors should not be retried
        assert not retry_manager.should_retry(log_id, ErrorCategory.DATA_VALIDATION_ERROR)
    
    def test_retry_delay_calculations(self, retry_manager):
        """Test retry delay calculations."""
        log_id = uuid4()
        
        # Immediate retry
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.IMMEDIATE) == 0.0
        
        # Fixed delay
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.FIXED_DELAY) == 1.0
        
        # Linear backoff
        retry_manager.record_retry(log_id)  # 1 retry
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.LINEAR_BACKOFF) == 2.0
        
        retry_manager.record_retry(log_id)  # 2 retries
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.LINEAR_BACKOFF) == 3.0
        
        # Exponential backoff
        retry_manager.retry_counts[log_id] = 0  # Reset
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.EXPONENTIAL_BACKOFF) == 1.0
        
        retry_manager.retry_counts[log_id] = 1
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.EXPONENTIAL_BACKOFF) == 2.0
        
        retry_manager.retry_counts[log_id] = 2
        assert retry_manager.get_retry_delay(log_id, RetryStrategy.EXPONENTIAL_BACKOFF) == 4.0
    
    def test_can_retry_now_timing(self, retry_manager):
        """Test retry timing restrictions."""
        log_id = uuid4()
        
        # Can retry immediately if never retried
        assert retry_manager.can_retry_now(log_id)
        
        # Record a retry
        retry_manager.record_retry(log_id)
        
        # Should not be able to retry immediately
        assert not retry_manager.can_retry_now(log_id)
    
    def test_reset_retry_count(self, retry_manager):
        """Test resetting retry count."""
        log_id = uuid4()
        
        # Record some retries
        retry_manager.record_retry(log_id)
        retry_manager.record_retry(log_id)
        assert retry_manager.retry_counts[log_id] == 2
        
        # Reset
        retry_manager.reset_retry_count(log_id)
        assert log_id not in retry_manager.retry_counts
        assert log_id not in retry_manager.last_retry_times


class TestErrorCategorizer:
    """Test cases for error categorization."""
    
    def test_categorize_ai_errors(self):
        """Test categorization of AI-related errors."""
        assert ErrorCategorizer.categorize_error("OpenAI API error") == ErrorCategory.AI_EXTRACTION_ERROR
        assert ErrorCategorizer.categorize_error("Rate limit exceeded") == ErrorCategory.AI_EXTRACTION_ERROR
        assert ErrorCategorizer.categorize_error("Model not found") == ErrorCategory.AI_EXTRACTION_ERROR
    
    def test_categorize_image_errors(self):
        """Test categorization of image processing errors."""
        assert ErrorCategorizer.categorize_error("Invalid image format") == ErrorCategory.IMAGE_PROCESSING_ERROR
        assert ErrorCategorizer.categorize_error("Corrupt image file") == ErrorCategory.IMAGE_PROCESSING_ERROR
        assert ErrorCategorizer.categorize_error("Pillow decode error") == ErrorCategory.IMAGE_PROCESSING_ERROR
    
    def test_categorize_validation_errors(self):
        """Test categorization of validation errors."""
        assert ErrorCategorizer.categorize_error("Validation failed") == ErrorCategory.DATA_VALIDATION_ERROR
        assert ErrorCategorizer.categorize_error("Missing required field") == ErrorCategory.DATA_VALIDATION_ERROR
        assert ErrorCategorizer.categorize_error("Invalid data format") == ErrorCategory.DATA_VALIDATION_ERROR
    
    def test_categorize_file_errors(self):
        """Test categorization of file access errors."""
        assert ErrorCategorizer.categorize_error("File not found") == ErrorCategory.FILE_ACCESS_ERROR
        assert ErrorCategorizer.categorize_error("Permission denied") == ErrorCategory.FILE_ACCESS_ERROR
        assert ErrorCategorizer.categorize_error("Directory not found") == ErrorCategory.FILE_ACCESS_ERROR
    
    def test_categorize_network_errors(self):
        """Test categorization of network errors."""
        assert ErrorCategorizer.categorize_error("Connection timeout") == ErrorCategory.NETWORK_ERROR
        assert ErrorCategorizer.categorize_error("DNS resolution failed") == ErrorCategory.NETWORK_ERROR
        assert ErrorCategorizer.categorize_error("SSL handshake error") == ErrorCategory.NETWORK_ERROR
    
    def test_categorize_config_errors(self):
        """Test categorization of configuration errors."""
        assert ErrorCategorizer.categorize_error("Missing config setting") == ErrorCategory.CONFIGURATION_ERROR
        assert ErrorCategorizer.categorize_error("Invalid environment variable") == ErrorCategory.CONFIGURATION_ERROR
        assert ErrorCategorizer.categorize_error("Configuration error") == ErrorCategory.CONFIGURATION_ERROR
    
    def test_categorize_timeout_errors(self):
        """Test categorization of timeout errors."""
        assert ErrorCategorizer.categorize_error("Operation timed out") == ErrorCategory.TIMEOUT_ERROR
        assert ErrorCategorizer.categorize_error("Request timed out") == ErrorCategory.TIMEOUT_ERROR
        assert ErrorCategorizer.categorize_error("Deadline exceeded") == ErrorCategory.TIMEOUT_ERROR
    
    def test_categorize_unknown_errors(self):
        """Test categorization of unknown errors."""
        assert ErrorCategorizer.categorize_error("Some random error") == ErrorCategory.UNKNOWN_ERROR
        assert ErrorCategorizer.categorize_error("Unexpected error") == ErrorCategory.UNKNOWN_ERROR
    
    def test_error_priority(self):
        """Test error priority ordering."""
        assert ErrorCategorizer.get_error_priority(ErrorCategory.CONFIGURATION_ERROR) == 1
        assert ErrorCategorizer.get_error_priority(ErrorCategory.FILE_ACCESS_ERROR) == 2
        assert ErrorCategorizer.get_error_priority(ErrorCategory.AI_EXTRACTION_ERROR) == 4
        assert ErrorCategorizer.get_error_priority(ErrorCategory.UNKNOWN_ERROR) == 8


class TestProcessingMetrics:
    """Test cases for processing metrics."""
    
    def test_processing_timing(self):
        """Test processing time measurement."""
        metrics = ProcessingMetrics()
        
        # Start processing
        metrics.start_processing()
        assert metrics.start_time is not None
        assert metrics.end_time is None
        
        # Add component times
        metrics.add_ai_processing_time(2.5)
        metrics.add_validation_time(0.3)
        metrics.add_file_operations_time(0.2)
        
        # End processing
        metrics.end_processing()
        assert metrics.end_time is not None
        
        # Check total time
        total_time = metrics.get_total_processing_time()
        assert total_time is not None
        assert total_time >= 0
    
    def test_error_recording(self):
        """Test error recording."""
        metrics = ProcessingMetrics()
        
        # Record errors
        metrics.record_error("Test error", ErrorCategory.AI_EXTRACTION_ERROR)
        assert metrics.error_count == 1
        assert metrics.last_error == "Test error"
        assert metrics.last_error_category == ErrorCategory.AI_EXTRACTION_ERROR
        
        metrics.record_error("Another error", ErrorCategory.NETWORK_ERROR)
        assert metrics.error_count == 2
        assert metrics.last_error == "Another error"
        assert metrics.last_error_category == ErrorCategory.NETWORK_ERROR
    
    def test_retry_counting(self):
        """Test retry counting."""
        metrics = ProcessingMetrics()
        
        # Increment retries
        metrics.increment_retry()
        assert metrics.total_retries == 1
        
        metrics.increment_retry()
        assert metrics.total_retries == 2
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = ProcessingMetrics()
        metrics.start_processing()
        metrics.add_ai_processing_time(1.5)
        metrics.record_error("Test error", ErrorCategory.AI_EXTRACTION_ERROR)
        metrics.increment_retry()
        metrics.end_processing()
        
        metrics_dict = metrics.to_dict()
        
        assert "start_time" in metrics_dict
        assert "end_time" in metrics_dict
        assert "ai_processing_time" in metrics_dict
        assert "total_processing_time" in metrics_dict
        assert "error_count" in metrics_dict
        assert "total_retries" in metrics_dict
        assert "last_error" in metrics_dict
        assert "last_error_category" in metrics_dict


class TestEnhancedStatusTracker:
    """Test cases for enhanced status tracker."""
    
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
    def status_tracker(self, storage_manager):
        """Create a status tracker for testing."""
        return EnhancedStatusTracker(storage_manager)
    
    @pytest.fixture
    def sample_log_entry(self):
        """Create a sample log entry for testing."""
        return ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("/test/path/test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING
        )
    
    def test_start_processing(self, status_tracker, sample_log_entry):
        """Test starting processing."""
        # Add log entry to storage
        status_tracker.storage.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        
        # Start processing
        success = status_tracker.start_processing(log_id)
        assert success
        
        # Verify status was updated
        updated_log = status_tracker.storage.get_log_entry(log_id)
        assert updated_log.current_status == ProcessingStatus.PROCESSING
        
        # Verify metrics were initialized
        assert log_id in status_tracker.active_metrics
    
    def test_complete_processing_success(self, status_tracker, sample_log_entry):
        """Test completing processing successfully."""
        # Add log entry and start processing
        status_tracker.storage.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        status_tracker.start_processing(log_id)
        
        # Create successful receipt data
        receipt_data = ReceiptData(
            vendor_name="Test Vendor",
            transaction_date=datetime.now(),
            total_amount=25.50,
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        # Complete processing
        success = status_tracker.complete_processing(log_id, receipt_data)
        assert success
        
        # Verify status was updated
        updated_log = status_tracker.storage.get_log_entry(log_id)
        assert updated_log.current_status == ProcessingStatus.PROCESSED
        assert updated_log.receipt_data == receipt_data
    
    def test_complete_processing_no_data(self, status_tracker, sample_log_entry):
        """Test completing processing with no data extracted."""
        # Add log entry and start processing
        status_tracker.storage.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        status_tracker.start_processing(log_id)
        
        # Complete processing with no data
        success = status_tracker.complete_processing(log_id, None)
        assert success
        
        # Verify status was updated
        updated_log = status_tracker.storage.get_log_entry(log_id)
        assert updated_log.current_status == ProcessingStatus.NO_DATA_EXTRACTED
    
    def test_record_error_with_retry(self, status_tracker, sample_log_entry):
        """Test recording error with retry."""
        # Add log entry and start processing
        status_tracker.storage.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        status_tracker.start_processing(log_id)
        
        # Record error
        success = status_tracker.record_error(log_id, "Test error", should_retry=True)
        assert success
        
        # Verify status was updated to retry
        updated_log = status_tracker.storage.get_log_entry(log_id)
        assert updated_log.current_status == ProcessingStatus.RETRY
    
    def test_record_error_no_retry(self, status_tracker, sample_log_entry):
        """Test recording error without retry."""
        # Add log entry and start processing
        status_tracker.storage.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        status_tracker.start_processing(log_id)
        
        # Record configuration error (should not retry)
        success = status_tracker.record_error(
            log_id, "Configuration error", should_retry=True
        )
        assert success
        
        # Verify status was updated to error
        updated_log = status_tracker.storage.get_log_entry(log_id)
        assert updated_log.current_status == ProcessingStatus.ERROR
    
    def test_update_status_with_validation(self, status_tracker, sample_log_entry):
        """Test updating status with validation."""
        # Add log entry
        status_tracker.storage.add_log_entry(sample_log_entry)
        log_id = sample_log_entry.id
        
        # Valid transition
        success = status_tracker.update_status(
            log_id, ProcessingStatus.PROCESSING, "Starting processing"
        )
        assert success
        
        # Invalid transition (PROCESSING -> PENDING is not valid)
        success = status_tracker.update_status(
            log_id, ProcessingStatus.PENDING, "Invalid transition"
        )
        assert not success
    
    def test_bulk_update_status(self, status_tracker):
        """Test bulk status updates."""
        # Create multiple log entries
        log_entries = []
        for i in range(3):
            entry = ReceiptProcessingLog(
                original_filename=f"receipt_{i}.jpg",
                file_path=Path(f"/test/receipt_{i}.jpg"),
                file_size=1024,
                current_status=ProcessingStatus.PENDING
            )
            status_tracker.storage.add_log_entry(entry)
            log_entries.append(entry)
        
        # Bulk update
        log_ids = [entry.id for entry in log_entries]
        results = status_tracker.bulk_update_status(
            log_ids, ProcessingStatus.PROCESSING, "Bulk processing start"
        )
        
        # Verify all updates succeeded
        assert all(results.values())
        
        # Verify statuses were updated
        for log_id in log_ids:
            log_entry = status_tracker.storage.get_log_entry(log_id)
            assert log_entry.current_status == ProcessingStatus.PROCESSING
    
    def test_get_retry_candidates(self, status_tracker):
        """Test getting retry candidates."""
        # Create log entries in retry status
        retry_entry = ReceiptProcessingLog(
            original_filename="retry_receipt.jpg",
            file_path=Path("/test/retry_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.RETRY
        )
        status_tracker.storage.add_log_entry(retry_entry)
        
        # Get retry candidates
        candidates = status_tracker.get_retry_candidates()
        assert retry_entry.id in candidates
    
    def test_get_error_summary(self, status_tracker):
        """Test getting error summary."""
        # Create log entries with errors
        error_entry = ReceiptProcessingLog(
            original_filename="error_receipt.jpg",
            file_path=Path("/test/error_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.ERROR
        )
        status_tracker.storage.add_log_entry(error_entry)
        
        # Add error transition
        status_tracker.storage.add_status_transition(
            error_entry.id, ProcessingStatus.ERROR, "Test error",
            metadata={"error_category": "ai_extraction_error"}
        )
        
        # Get error summary
        summary = status_tracker.get_error_summary()
        assert summary["total_errors"] == 1
        assert "ai_extraction_error" in summary["by_category"]
    
    def test_get_processing_statistics(self, status_tracker):
        """Test getting processing statistics."""
        # Create log entries with different statuses
        for i, status in enumerate([ProcessingStatus.PROCESSED, ProcessingStatus.ERROR, ProcessingStatus.PENDING]):
            entry = ReceiptProcessingLog(
                original_filename=f"receipt_{i}.jpg",
                file_path=Path(f"/test/receipt_{i}.jpg"),
                file_size=1024,
                current_status=status,
                processing_time_seconds=1.0 + i
            )
            status_tracker.storage.add_log_entry(entry)
        
        # Get statistics
        stats = status_tracker.get_processing_statistics()
        
        assert stats["total_receipts"] == 3
        assert "processed" in stats["by_status"]
        assert "error" in stats["by_status"]
        assert "pending" in stats["by_status"]
        assert "avg_processing_time" in stats
        assert "min_processing_time" in stats
        assert "max_processing_time" in stats


class TestIntegration:
    """Integration tests for the status tracking system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_full_workflow(self, temp_dir):
        """Test a complete workflow with status tracking."""
        # Setup
        log_file = temp_dir / "workflow_log.json"
        storage = JSONStorageManager(log_file)
        tracker = EnhancedStatusTracker(storage)
        
        # Create log entry
        log_entry = ReceiptProcessingLog(
            original_filename="workflow_receipt.jpg",
            file_path=Path("/test/workflow_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING
        )
        storage.add_log_entry(log_entry)
        log_id = log_entry.id
        
        # Start processing
        assert tracker.start_processing(log_id)
        
        # Simulate processing with error and retry
        tracker.record_error(log_id, "Temporary network error", should_retry=True)
        
        # Verify retry status
        updated_log = storage.get_log_entry(log_id)
        assert updated_log.current_status == ProcessingStatus.RETRY
        
        # Complete processing successfully
        receipt_data = ReceiptData(
            vendor_name="Test Vendor",
            transaction_date=datetime.now(),
            total_amount=50.00,
            currency=Currency.USD,
            extraction_confidence=0.92,
            has_required_data=True
        )
        
        assert tracker.complete_processing(log_id, receipt_data)
        
        # Verify final status
        final_log = storage.get_log_entry(log_id)
        assert final_log.current_status == ProcessingStatus.PROCESSED
        assert final_log.receipt_data == receipt_data
        
        # Test statistics
        stats = tracker.get_processing_statistics()
        assert stats["total_receipts"] == 1
        assert stats["by_status"]["processed"] == 1
