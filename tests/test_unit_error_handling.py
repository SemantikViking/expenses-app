"""
Unit Tests for Error Handling Module

This module contains comprehensive unit tests for the error handling
and recovery system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.receipt_processor.error_handling import (
    ErrorSeverity, ErrorCategory, RetryStrategy, ErrorContext, ErrorInfo,
    ReceiptProcessorError, ValidationError, ProcessingError, StorageError,
    NetworkError, AIServiceError, FileSystemError, ConfigurationError,
    PermissionError, ResourceError, TimeoutError, ErrorCategorizer,
    RetryManager, ErrorRecoveryManager, ErrorReporter, ErrorHandler,
    handle_errors
)

class TestErrorEnums:
    """Test cases for error enums."""
    
    def test_error_severity_enum(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"
    
    def test_error_category_enum(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.VALIDATION_ERROR == "validation_error"
        assert ErrorCategory.PROCESSING_ERROR == "processing_error"
        assert ErrorCategory.STORAGE_ERROR == "storage_error"
        assert ErrorCategory.NETWORK_ERROR == "network_error"
        assert ErrorCategory.AI_SERVICE_ERROR == "ai_service_error"
    
    def test_retry_strategy_enum(self):
        """Test RetryStrategy enum values."""
        assert RetryStrategy.NONE == "none"
        assert RetryStrategy.IMMEDIATE == "immediate"
        assert RetryStrategy.EXPONENTIAL_BACKOFF == "exponential_backoff"
        assert RetryStrategy.LINEAR_BACKOFF == "linear_backoff"
        assert RetryStrategy.FIXED_DELAY == "fixed_delay"

class TestErrorContext:
    """Test cases for ErrorContext."""
    
    def test_error_context_creation(self):
        """Test ErrorContext creation with defaults."""
        context = ErrorContext()
        assert context.timestamp is not None
        assert context.user_id is None
        assert context.session_id is None
        assert context.request_id is None
        assert context.file_path is None
        assert context.operation is None
        assert context.metadata == {}
    
    def test_error_context_with_values(self):
        """Test ErrorContext creation with specific values."""
        context = ErrorContext(
            user_id="user123",
            session_id="session456",
            request_id="req789",
            file_path="/test/receipt.jpg",
            operation="process_receipt",
            metadata={"test": True}
        )
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.request_id == "req789"
        assert context.file_path == "/test/receipt.jpg"
        assert context.operation == "process_receipt"
        assert context.metadata == {"test": True}

class TestErrorInfo:
    """Test cases for ErrorInfo."""
    
    def test_error_info_creation(self, sample_error_info):
        """Test ErrorInfo creation."""
        error_info = sample_error_info
        assert error_info.error_id == "ERR_001"
        assert error_info.exception_type == "ValidationError"
        assert error_info.error_message == "Invalid data format"
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.category == ErrorCategory.VALIDATION_ERROR
        assert error_info.retry_count == 0
        assert error_info.max_retries == 3
        assert error_info.recovery_attempted is False
        assert error_info.resolved is False
    
    def test_error_info_serialization(self, sample_error_info):
        """Test ErrorInfo serialization."""
        error_info = sample_error_info
        data = error_info.model_dump()
        
        assert isinstance(data, dict)
        assert data["error_id"] == "ERR_001"
        assert data["severity"] == "medium"
        assert data["category"] == "validation_error"

class TestCustomExceptions:
    """Test cases for custom exception classes."""
    
    def test_receipt_processor_error_creation(self):
        """Test ReceiptProcessorError creation."""
        error = ReceiptProcessorError(
            message="Test error",
            category=ErrorCategory.PROCESSING_ERROR,
            severity=ErrorSeverity.HIGH
        )
        assert str(error) == "Test error"
        assert error.category == ErrorCategory.PROCESSING_ERROR
        assert error.severity == ErrorSeverity.HIGH
        assert error.context is not None
        assert error.timestamp is not None
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError(
            message="Invalid data",
            field="vendor_name"
        )
        assert str(error) == "Invalid data"
        assert error.field == "vendor_name"
        assert error.category == ErrorCategory.VALIDATION_ERROR
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_processing_error_creation(self):
        """Test ProcessingError creation."""
        error = ProcessingError(
            message="Processing failed",
            stage="extraction"
        )
        assert str(error) == "Processing failed"
        assert error.stage == "extraction"
        assert error.category == ErrorCategory.PROCESSING_ERROR
        assert error.severity == ErrorSeverity.HIGH
    
    def test_storage_error_creation(self):
        """Test StorageError creation."""
        error = StorageError(
            message="Storage failed",
            operation="save_log"
        )
        assert str(error) == "Storage failed"
        assert error.operation == "save_log"
        assert error.category == ErrorCategory.STORAGE_ERROR
        assert error.severity == ErrorSeverity.HIGH
    
    def test_network_error_creation(self):
        """Test NetworkError creation."""
        error = NetworkError(
            message="Connection failed",
            endpoint="https://api.example.com"
        )
        assert str(error) == "Connection failed"
        assert error.endpoint == "https://api.example.com"
        assert error.category == ErrorCategory.NETWORK_ERROR
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_ai_service_error_creation(self):
        """Test AIServiceError creation."""
        error = AIServiceError(
            message="AI service failed",
            service="openai"
        )
        assert str(error) == "AI service failed"
        assert error.service == "openai"
        assert error.category == ErrorCategory.AI_SERVICE_ERROR
        assert error.severity == ErrorSeverity.HIGH
    
    def test_file_system_error_creation(self):
        """Test FileSystemError creation."""
        error = FileSystemError(
            message="File not found",
            path="/test/receipt.jpg"
        )
        assert str(error) == "File not found"
        assert error.path == "/test/receipt.jpg"
        assert error.category == ErrorCategory.FILE_SYSTEM_ERROR
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_configuration_error_creation(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError(
            message="Invalid config",
            config_key="api_key"
        )
        assert str(error) == "Invalid config"
        assert error.config_key == "api_key"
        assert error.category == ErrorCategory.CONFIGURATION_ERROR
        assert error.severity == ErrorSeverity.HIGH
    
    def test_permission_error_creation(self):
        """Test PermissionError creation."""
        error = PermissionError(
            message="Access denied",
            resource="/test/file"
        )
        assert str(error) == "Access denied"
        assert error.resource == "/test/file"
        assert error.category == ErrorCategory.PERMISSION_ERROR
        assert error.severity == ErrorSeverity.HIGH
    
    def test_resource_error_creation(self):
        """Test ResourceError creation."""
        error = ResourceError(
            message="Insufficient memory",
            resource_type="RAM"
        )
        assert str(error) == "Insufficient memory"
        assert error.resource_type == "RAM"
        assert error.category == ErrorCategory.RESOURCE_ERROR
        assert error.severity == ErrorSeverity.HIGH
    
    def test_timeout_error_creation(self):
        """Test TimeoutError creation."""
        error = TimeoutError(
            message="Operation timed out",
            timeout_duration=30.0
        )
        assert str(error) == "Operation timed out"
        assert error.timeout_duration == 30.0
        assert error.category == ErrorCategory.TIMEOUT_ERROR
        assert error.severity == ErrorSeverity.MEDIUM

class TestErrorCategorizer:
    """Test cases for ErrorCategorizer."""
    
    def test_categorize_receipt_processor_error(self):
        """Test categorization of ReceiptProcessorError."""
        error = ValidationError("Invalid data")
        categorizer = ErrorCategorizer()
        category = categorizer.categorize_error(error)
        assert category == ErrorCategory.VALIDATION_ERROR
    
    def test_categorize_by_message_patterns(self):
        """Test categorization by message patterns."""
        categorizer = ErrorCategorizer()
        
        # Test validation error pattern
        error = Exception("Invalid data format")
        category = categorizer.categorize_error(error)
        assert category == ErrorCategory.VALIDATION_ERROR
        
        # Test network error pattern
        error = Exception("Connection timeout")
        category = categorizer.categorize_error(error)
        assert category == ErrorCategory.NETWORK_ERROR
        
        # Test storage error pattern
        error = Exception("Database connection failed")
        category = categorizer.categorize_error(error)
        assert category == ErrorCategory.STORAGE_ERROR
        
        # Test AI service error pattern
        error = Exception("OpenAI API rate limit exceeded")
        category = categorizer.categorize_error(error)
        assert category == ErrorCategory.AI_SERVICE_ERROR
    
    def test_determine_severity(self):
        """Test severity determination."""
        categorizer = ErrorCategorizer()
        
        # Test ReceiptProcessorError severity
        error = ValidationError("Invalid data")
        severity = categorizer.determine_severity(error, ErrorCategory.VALIDATION_ERROR)
        assert severity == ErrorSeverity.MEDIUM
        
        # Test critical error severity
        error = Exception("Critical system failure")
        severity = categorizer.determine_severity(error, ErrorCategory.CRITICAL_ERROR)
        assert severity == ErrorSeverity.CRITICAL

class TestRetryManager:
    """Test cases for RetryManager."""
    
    def test_retry_manager_creation(self):
        """Test RetryManager creation."""
        manager = RetryManager()
        assert manager.retry_strategies is not None
        assert manager.max_retries is not None
    
    def test_should_retry(self):
        """Test retry decision logic."""
        manager = RetryManager()
        
        # Test should retry
        error_info = ErrorInfo(
            error_id="ERR_001",
            exception_type="NetworkError",
            error_message="Connection failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK_ERROR,
            context=ErrorContext(),
            stack_trace="",
            retry_count=0,
            max_retries=5
        )
        assert manager.should_retry(error_info) is True
        
        # Test should not retry (max retries reached)
        error_info.retry_count = 5
        assert manager.should_retry(error_info) is False
        
        # Test should not retry (no retry strategy)
        error_info.retry_count = 0
        error_info.category = ErrorCategory.VALIDATION_ERROR
        assert manager.should_retry(error_info) is False
    
    def test_get_retry_delay(self):
        """Test retry delay calculation."""
        manager = RetryManager()
        
        # Test exponential backoff
        error_info = ErrorInfo(
            error_id="ERR_001",
            exception_type="NetworkError",
            error_message="Connection failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK_ERROR,
            context=ErrorContext(),
            stack_trace="",
            retry_count=0,
            max_retries=5,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        
        delay_0 = manager.get_retry_delay(error_info)
        error_info.retry_count = 1
        delay_1 = manager.get_retry_delay(error_info)
        error_info.retry_count = 2
        delay_2 = manager.get_retry_delay(error_info)
        
        assert delay_0 == 1.0
        assert delay_1 == 2.0
        assert delay_2 == 4.0
        
        # Test linear backoff
        error_info.retry_strategy = RetryStrategy.LINEAR_BACKOFF
        error_info.retry_count = 0
        delay_0 = manager.get_retry_delay(error_info)
        error_info.retry_count = 1
        delay_1 = manager.get_retry_delay(error_info)
        
        assert delay_0 == 1.0
        assert delay_1 == 2.0
        
        # Test fixed delay
        error_info.retry_strategy = RetryStrategy.FIXED_DELAY
        error_info.retry_count = 0
        delay_0 = manager.get_retry_delay(error_info)
        error_info.retry_count = 1
        delay_1 = manager.get_retry_delay(error_info)
        
        assert delay_0 == 1.0
        assert delay_1 == 1.0
        
        # Test immediate
        error_info.retry_strategy = RetryStrategy.IMMEDIATE
        delay = manager.get_retry_delay(error_info)
        assert delay == 0.0
    
    def test_get_max_retries(self):
        """Test max retries retrieval."""
        manager = RetryManager()
        
        assert manager.get_max_retries(ErrorCategory.NETWORK_ERROR) == 5
        assert manager.get_max_retries(ErrorCategory.VALIDATION_ERROR) == 0
        assert manager.get_max_retries(ErrorCategory.UNKNOWN_ERROR) == 2

class TestErrorRecoveryManager:
    """Test cases for ErrorRecoveryManager."""
    
    def test_recovery_manager_creation(self):
        """Test ErrorRecoveryManager creation."""
        manager = ErrorRecoveryManager()
        assert manager.recovery_strategies is not None
    
    def test_attempt_recovery(self):
        """Test recovery attempt logic."""
        manager = ErrorRecoveryManager()
        
        error_info = ErrorInfo(
            error_id="ERR_001",
            exception_type="StorageError",
            error_message="Storage failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.STORAGE_ERROR,
            context=ErrorContext(),
            stack_trace="",
            retry_count=0,
            max_retries=3
        )
        
        # Test recovery attempt (will fail in mock)
        result = manager.attempt_recovery(error_info)
        assert result is False  # Mock strategies return False
        assert error_info.recovery_attempted is True
    
    def test_recovery_strategies(self):
        """Test individual recovery strategies."""
        manager = ErrorRecoveryManager()
        
        error_info = ErrorInfo(
            error_id="ERR_001",
            exception_type="StorageError",
            error_message="Storage failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.STORAGE_ERROR,
            context=ErrorContext(),
            stack_trace="",
            retry_count=0,
            max_retries=3
        )
        
        # Test storage recovery strategy
        result = manager._recover_storage_error(error_info)
        assert result is False  # Mock implementation
        
        # Test network recovery strategy
        error_info.category = ErrorCategory.NETWORK_ERROR
        result = manager._recover_network_error(error_info)
        assert result is False  # Mock implementation

class TestErrorReporter:
    """Test cases for ErrorReporter."""
    
    def test_reporter_creation(self):
        """Test ErrorReporter creation."""
        reporter = ErrorReporter()
        assert reporter.user_messages is not None
        assert len(reporter.user_messages) > 0
    
    def test_get_user_message(self, sample_error_info):
        """Test user message generation."""
        reporter = ErrorReporter()
        message = reporter.get_user_message(sample_error_info)
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert "data format" in message.lower()
    
    def test_get_user_message_with_retry(self):
        """Test user message with retry count."""
        reporter = ErrorReporter()
        error_info = ErrorInfo(
            error_id="ERR_001",
            exception_type="NetworkError",
            error_message="Connection failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK_ERROR,
            context=ErrorContext(),
            stack_trace="",
            retry_count=2,
            max_retries=3
        )
        
        message = reporter.get_user_message(error_info)
        assert "Attempt 3" in message
    
    def test_get_technical_message(self, sample_error_info):
        """Test technical message generation."""
        reporter = ErrorReporter()
        message = reporter.get_technical_message(sample_error_info)
        
        assert isinstance(message, str)
        assert sample_error_info.error_id in message
        assert sample_error_info.category.value in message
        assert sample_error_info.error_message in message

class TestErrorHandler:
    """Test cases for ErrorHandler."""
    
    def test_error_handler_creation(self, temp_dir):
        """Test ErrorHandler creation."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        assert handler.log_file == log_file
        assert handler.categorizer is not None
        assert handler.retry_manager is not None
        assert handler.recovery_manager is not None
        assert handler.reporter is not None
        assert handler.error_history == []
    
    def test_handle_error(self, temp_dir):
        """Test error handling."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        error = ValidationError("Invalid data", field="vendor_name")
        context = ErrorContext(operation="process_receipt")
        
        error_info = handler.handle_error(error, context)
        
        assert error_info.error_id is not None
        assert error_info.exception_type == "ValidationError"
        assert error_info.error_message == "Invalid data"
        assert error_info.category == ErrorCategory.VALIDATION_ERROR
        assert error_info.context.operation == "process_receipt"
        assert len(handler.error_history) == 1
    
    def test_handle_error_without_context(self, temp_dir):
        """Test error handling without context."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        error = Exception("Generic error")
        error_info = handler.handle_error(error)
        
        assert error_info.error_id is not None
        assert error_info.exception_type == "Exception"
        assert error_info.error_message == "Generic error"
        assert error_info.context is not None
    
    def test_error_logging(self, temp_dir):
        """Test error logging to file."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        error = ValidationError("Invalid data")
        handler.handle_error(error)
        
        # Check if log file was created
        assert log_file.exists()
        
        # Check log file content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            log_data = json.loads(lines[0])
            assert log_data["exception_type"] == "ValidationError"
            assert log_data["error_message"] == "Invalid data"
            assert log_data["category"] == "validation_error"
    
    def test_retry_with_backoff(self, temp_dir):
        """Test retry with backoff functionality."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        # Mock function that fails first two times, then succeeds
        call_count = 0
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = handler.retry_with_backoff(mock_function)
        assert result == "success"
        assert call_count == 3
    
    def test_retry_with_backoff_max_retries(self, temp_dir):
        """Test retry with backoff when max retries exceeded."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        # Mock function that always fails
        def mock_function():
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception, match="Function failed after 3 retries"):
            handler.retry_with_backoff(mock_function)
    
    def test_get_error_summary(self, temp_dir):
        """Test error summary generation."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        # Add some errors to history
        error1 = ValidationError("Invalid data 1")
        error2 = ProcessingError("Processing failed")
        error3 = NetworkError("Connection failed")
        
        handler.handle_error(error1)
        handler.handle_error(error2)
        handler.handle_error(error3)
        
        summary = handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["resolved_errors"] == 0
        assert summary["unresolved_errors"] == 3
        assert "validation_error" in summary["by_category"]
        assert "processing_error" in summary["by_category"]
        assert "network_error" in summary["by_category"]

class TestErrorHandlingDecorator:
    """Test cases for error handling decorator."""
    
    def test_handle_errors_decorator(self, temp_dir):
        """Test @handle_errors decorator."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        @handle_errors(handler)
        def test_function():
            raise ValidationError("Test error")
        
        with pytest.raises(ReceiptProcessorError):
            test_function()
        
        # Check that error was logged
        assert len(handler.error_history) == 1
        assert handler.error_history[0].exception_type == "ValidationError"
    
    def test_handle_errors_decorator_success(self, temp_dir):
        """Test @handle_errors decorator with successful function."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        @handle_errors(handler)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
        assert len(handler.error_history) == 0

class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""
    
    def test_full_error_handling_workflow(self, temp_dir):
        """Test complete error handling workflow."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        # Simulate a processing error
        try:
            raise ProcessingError("AI service unavailable", stage="extraction")
        except Exception as e:
            error_info = handler.handle_error(e)
            
            # Verify error was categorized correctly
            assert error_info.category == ErrorCategory.PROCESSING_ERROR
            assert error_info.severity == ErrorSeverity.HIGH
            assert error_info.stage == "extraction"
            
            # Verify error was logged
            assert log_file.exists()
            
            # Verify error is in history
            assert len(handler.error_history) == 1
            
            # Verify retry logic
            assert handler.retry_manager.should_retry(error_info) is True
            assert handler.retry_manager.get_retry_delay(error_info) > 0
    
    def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery workflow."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        # Create a storage error
        error = StorageError("Database connection failed", operation="save_log")
        error_info = handler.handle_error(error)
        
        # Attempt recovery
        recovery_manager = ErrorRecoveryManager()
        result = recovery_manager.attempt_recovery(error_info)
        
        # Verify recovery was attempted
        assert error_info.recovery_attempted is True
        # Note: Mock strategies return False, so recovery won't succeed
    
    def test_error_reporting_workflow(self, temp_dir):
        """Test error reporting workflow."""
        log_file = temp_dir / "error_log.json"
        handler = ErrorHandler(log_file=log_file)
        
        # Create different types of errors
        errors = [
            ValidationError("Invalid data format"),
            NetworkError("Connection timeout"),
            AIServiceError("API rate limit exceeded")
        ]
        
        for error in errors:
            handler.handle_error(error)
        
        # Test error summary
        summary = handler.get_error_summary()
        assert summary["total_errors"] == 3
        assert summary["unresolved_errors"] == 3
        
        # Test user messages
        reporter = ErrorReporter()
        for error_info in handler.error_history:
            user_message = reporter.get_user_message(error_info)
            technical_message = reporter.get_technical_message(error_info)
            
            assert isinstance(user_message, str)
            assert isinstance(technical_message, str)
            assert len(user_message) > 0
            assert len(technical_message) > 0
