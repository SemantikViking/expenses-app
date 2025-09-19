"""
Error Handling Module

This module provides comprehensive error handling, categorization, retry mechanisms,
recovery strategies, and user-friendly error reporting for the receipt processing system.
"""

import logging
import time
import traceback
from typing import Optional, Dict, Any, List, Callable, Union, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import functools
import asyncio
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    """Error categories for better handling and reporting."""
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    STORAGE_ERROR = "storage_error"
    NETWORK_ERROR = "network_error"
    AI_SERVICE_ERROR = "ai_service_error"
    FILE_SYSTEM_ERROR = "file_system_error"
    CONFIGURATION_ERROR = "configuration_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

class RetryStrategy(str, Enum):
    """Retry strategies for different error types."""
    NONE = "none"
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"

@dataclass
class ErrorContext:
    """Context information for error tracking."""
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    file_path: Optional[str] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    error_id: str
    exception_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: str
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    recovery_attempted: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class ReceiptProcessorError(Exception):
    """Base exception for all receipt processor errors."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.timestamp = datetime.now()

class ValidationError(ReceiptProcessorError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.VALIDATION_ERROR, ErrorSeverity.MEDIUM, context)
        self.field = field

class ProcessingError(ReceiptProcessorError):
    """Raised when receipt processing fails."""
    
    def __init__(self, message: str, stage: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.PROCESSING_ERROR, ErrorSeverity.HIGH, context)
        self.stage = stage

class StorageError(ReceiptProcessorError):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.STORAGE_ERROR, ErrorSeverity.HIGH, context)
        self.operation = operation

class NetworkError(ReceiptProcessorError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.NETWORK_ERROR, ErrorSeverity.MEDIUM, context)
        self.endpoint = endpoint

class AIServiceError(ReceiptProcessorError):
    """Raised when AI service operations fail."""
    
    def __init__(self, message: str, service: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.AI_SERVICE_ERROR, ErrorSeverity.HIGH, context)
        self.service = service

class FileSystemError(ReceiptProcessorError):
    """Raised when file system operations fail."""
    
    def __init__(self, message: str, path: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.FILE_SYSTEM_ERROR, ErrorSeverity.MEDIUM, context)
        self.path = path

class ConfigurationError(ReceiptProcessorError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.CONFIGURATION_ERROR, ErrorSeverity.HIGH, context)
        self.config_key = config_key

class PermissionError(ReceiptProcessorError):
    """Raised when permission is denied."""
    
    def __init__(self, message: str, resource: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.PERMISSION_ERROR, ErrorSeverity.HIGH, context)
        self.resource = resource

class ResourceError(ReceiptProcessorError):
    """Raised when system resources are insufficient."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.RESOURCE_ERROR, ErrorSeverity.HIGH, context)
        self.resource_type = resource_type

class TimeoutError(ReceiptProcessorError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM, context)
        self.timeout_duration = timeout_duration

class ErrorCategorizer:
    """Categorizes errors based on exception type and message patterns."""
    
    ERROR_PATTERNS: Dict[ErrorCategory, List[str]] = {
        ErrorCategory.VALIDATION_ERROR: [
            "validation", "invalid", "required", "missing", "format", "type", "constraint"
        ],
        ErrorCategory.PROCESSING_ERROR: [
            "processing", "extract", "parse", "convert", "transform", "process"
        ],
        ErrorCategory.STORAGE_ERROR: [
            "storage", "database", "file", "save", "load", "persist", "json", "sqlite"
        ],
        ErrorCategory.NETWORK_ERROR: [
            "network", "connection", "timeout", "dns", "http", "ssl", "socket", "unreachable"
        ],
        ErrorCategory.AI_SERVICE_ERROR: [
            "openai", "anthropic", "api", "model", "extraction", "vision", "token", "rate limit"
        ],
        ErrorCategory.FILE_SYSTEM_ERROR: [
            "file", "directory", "path", "permission", "access", "not found", "exists"
        ],
        ErrorCategory.CONFIGURATION_ERROR: [
            "config", "setting", "environment", "variable", "missing config"
        ],
        ErrorCategory.PERMISSION_ERROR: [
            "permission", "access denied", "unauthorized", "forbidden"
        ],
        ErrorCategory.RESOURCE_ERROR: [
            "memory", "cpu", "disk", "resource", "limit", "quota", "insufficient"
        ],
        ErrorCategory.TIMEOUT_ERROR: [
            "timeout", "timed out", "expired", "deadline"
        ]
    }
    
    @classmethod
    def categorize_error(cls, exception: Exception) -> ErrorCategory:
        """Categorize an error based on exception type and message."""
        # Check exception type first
        if isinstance(exception, ReceiptProcessorError):
            return exception.category
        
        # Check message patterns
        error_message = str(exception).lower()
        for category, patterns in cls.ERROR_PATTERNS.items():
            if any(pattern in error_message for pattern in patterns):
                return category
        
        return ErrorCategory.UNKNOWN_ERROR
    
    @classmethod
    def determine_severity(cls, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on category and context."""
        if isinstance(exception, ReceiptProcessorError):
            return exception.severity
        
        severity_map = {
            ErrorCategory.CRITICAL_ERROR: ErrorSeverity.CRITICAL,
            ErrorCategory.CONFIGURATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.STORAGE_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.AI_SERVICE_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.PROCESSING_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.PERMISSION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.RESOURCE_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.FILE_SYSTEM_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        
        return severity_map.get(category, ErrorSeverity.MEDIUM)

class RetryManager:
    """Manages retry logic for different error types."""
    
    def __init__(self):
        self.retry_strategies: Dict[ErrorCategory, RetryStrategy] = {
            ErrorCategory.NETWORK_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.AI_SERVICE_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.TIMEOUT_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.STORAGE_ERROR: RetryStrategy.LINEAR_BACKOFF,
            ErrorCategory.PROCESSING_ERROR: RetryStrategy.LINEAR_BACKOFF,
            ErrorCategory.VALIDATION_ERROR: RetryStrategy.NONE,
            ErrorCategory.CONFIGURATION_ERROR: RetryStrategy.NONE,
            ErrorCategory.PERMISSION_ERROR: RetryStrategy.NONE,
            ErrorCategory.RESOURCE_ERROR: RetryStrategy.FIXED_DELAY,
            ErrorCategory.FILE_SYSTEM_ERROR: RetryStrategy.FIXED_DELAY,
            ErrorCategory.UNKNOWN_ERROR: RetryStrategy.EXPONENTIAL_BACKOFF
        }
        
        self.max_retries: Dict[ErrorCategory, int] = {
            ErrorCategory.NETWORK_ERROR: 5,
            ErrorCategory.AI_SERVICE_ERROR: 3,
            ErrorCategory.TIMEOUT_ERROR: 3,
            ErrorCategory.STORAGE_ERROR: 3,
            ErrorCategory.PROCESSING_ERROR: 2,
            ErrorCategory.VALIDATION_ERROR: 0,
            ErrorCategory.CONFIGURATION_ERROR: 0,
            ErrorCategory.PERMISSION_ERROR: 0,
            ErrorCategory.RESOURCE_ERROR: 2,
            ErrorCategory.FILE_SYSTEM_ERROR: 2,
            ErrorCategory.UNKNOWN_ERROR: 2
        }
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if an error should be retried."""
        if error_info.retry_count >= error_info.max_retries:
            return False
        
        strategy = self.retry_strategies.get(error_info.category, RetryStrategy.NONE)
        return strategy != RetryStrategy.NONE
    
    def get_retry_delay(self, error_info: ErrorInfo) -> float:
        """Calculate retry delay based on strategy and retry count."""
        strategy = self.retry_strategies.get(error_info.category, RetryStrategy.NONE)
        
        if strategy == RetryStrategy.NONE:
            return 0.0
        
        base_delay = 1.0  # Base delay in seconds
        
        if strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif strategy == RetryStrategy.FIXED_DELAY:
            return base_delay
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return base_delay * (error_info.retry_count + 1)
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return base_delay * (2 ** error_info.retry_count)
        
        return base_delay
    
    def get_max_retries(self, category: ErrorCategory) -> int:
        """Get maximum retries for a category."""
        return self.max_retries.get(category, 3)

class ErrorRecoveryManager:
    """Manages error recovery strategies."""
    
    def __init__(self):
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default recovery strategies."""
        self.recovery_strategies[ErrorCategory.STORAGE_ERROR] = [
            self._recover_storage_error,
            self._fallback_to_backup_storage
        ]
        self.recovery_strategies[ErrorCategory.NETWORK_ERROR] = [
            self._recover_network_error,
            self._use_cached_data
        ]
        self.recovery_strategies[ErrorCategory.AI_SERVICE_ERROR] = [
            self._recover_ai_service_error,
            self._use_fallback_ai_service
        ]
        self.recovery_strategies[ErrorCategory.FILE_SYSTEM_ERROR] = [
            self._recover_file_system_error,
            self._create_alternative_path
        ]
        self.recovery_strategies[ErrorCategory.RESOURCE_ERROR] = [
            self._recover_resource_error,
            self._reduce_resource_usage
        ]
    
    def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from an error."""
        strategies = self.recovery_strategies.get(error_info.category, [])
        
        for strategy in strategies:
            try:
                if strategy(error_info):
                    error_info.recovery_attempted = True
                    error_info.resolved = True
                    error_info.resolution_time = datetime.now()
                    logger.info(f"Error {error_info.error_id} recovered using strategy {strategy.__name__}")
                    return True
            except Exception as e:
                logger.warning(f"Recovery strategy {strategy.__name__} failed: {e}")
        
        return False
    
    def _recover_storage_error(self, error_info: ErrorInfo) -> bool:
        """Recover from storage errors."""
        # Implementation would depend on specific storage system
        logger.info("Attempting storage error recovery...")
        return False
    
    def _fallback_to_backup_storage(self, error_info: ErrorInfo) -> bool:
        """Fallback to backup storage."""
        logger.info("Attempting fallback to backup storage...")
        return False
    
    def _recover_network_error(self, error_info: ErrorInfo) -> bool:
        """Recover from network errors."""
        logger.info("Attempting network error recovery...")
        return False
    
    def _use_cached_data(self, error_info: ErrorInfo) -> bool:
        """Use cached data as fallback."""
        logger.info("Attempting to use cached data...")
        return False
    
    def _recover_ai_service_error(self, error_info: ErrorInfo) -> bool:
        """Recover from AI service errors."""
        logger.info("Attempting AI service error recovery...")
        return False
    
    def _use_fallback_ai_service(self, error_info: ErrorInfo) -> bool:
        """Use fallback AI service."""
        logger.info("Attempting to use fallback AI service...")
        return False
    
    def _recover_file_system_error(self, error_info: ErrorInfo) -> bool:
        """Recover from file system errors."""
        logger.info("Attempting file system error recovery...")
        return False
    
    def _create_alternative_path(self, error_info: ErrorInfo) -> bool:
        """Create alternative file path."""
        logger.info("Attempting to create alternative path...")
        return False
    
    def _recover_resource_error(self, error_info: ErrorInfo) -> bool:
        """Recover from resource errors."""
        logger.info("Attempting resource error recovery...")
        return False
    
    def _reduce_resource_usage(self, error_info: ErrorInfo) -> bool:
        """Reduce resource usage."""
        logger.info("Attempting to reduce resource usage...")
        return False

class ErrorReporter:
    """Provides user-friendly error reporting."""
    
    def __init__(self):
        self.user_messages: Dict[ErrorCategory, str] = {
            ErrorCategory.VALIDATION_ERROR: "There was a problem with the data format. Please check your input and try again.",
            ErrorCategory.PROCESSING_ERROR: "We encountered an issue while processing your receipt. Please try again or contact support.",
            ErrorCategory.STORAGE_ERROR: "We're having trouble saving your data. Please try again in a few moments.",
            ErrorCategory.NETWORK_ERROR: "We're experiencing network issues. Please check your connection and try again.",
            ErrorCategory.AI_SERVICE_ERROR: "Our AI service is temporarily unavailable. Please try again later.",
            ErrorCategory.FILE_SYSTEM_ERROR: "There was a problem accessing files. Please check permissions and try again.",
            ErrorCategory.CONFIGURATION_ERROR: "There's a configuration issue. Please contact support.",
            ErrorCategory.PERMISSION_ERROR: "You don't have permission to perform this action. Please contact your administrator.",
            ErrorCategory.RESOURCE_ERROR: "The system is currently under heavy load. Please try again later.",
            ErrorCategory.TIMEOUT_ERROR: "The operation took too long to complete. Please try again.",
            ErrorCategory.UNKNOWN_ERROR: "An unexpected error occurred. Please try again or contact support."
        }
    
    def get_user_message(self, error_info: ErrorInfo) -> str:
        """Get user-friendly error message."""
        base_message = self.user_messages.get(error_info.category, self.user_messages[ErrorCategory.UNKNOWN_ERROR])
        
        if error_info.retry_count > 0:
            base_message += f" (Attempt {error_info.retry_count + 1})"
        
        return base_message
    
    def get_technical_message(self, error_info: ErrorInfo) -> str:
        """Get technical error message for logging."""
        return f"[{error_info.error_id}] {error_info.category.value}: {error_info.error_message}"

class ErrorHandler:
    """Main error handling orchestrator."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path("error_log.json")
        self.categorizer = ErrorCategorizer()
        self.retry_manager = RetryManager()
        self.recovery_manager = ErrorRecoveryManager()
        self.reporter = ErrorReporter()
        self.error_history: List[ErrorInfo] = []
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup error logging."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create error logger
        error_logger = logging.getLogger("error_handler")
        error_logger.setLevel(logging.ERROR)
        
        # File handler for errors
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        error_logger.addHandler(file_handler)
    
    def handle_error(self, exception: Exception, context: Optional[ErrorContext] = None) -> ErrorInfo:
        """Handle an error and return error information."""
        # Generate error ID
        error_id = f"ERR_{int(time.time() * 1000)}"
        
        # Categorize error
        category = self.categorizer.categorize_error(exception)
        severity = self.categorizer.determine_severity(exception, category)
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            exception_type=type(exception).__name__,
            error_message=str(exception),
            severity=severity,
            category=category,
            context=context or ErrorContext(),
            stack_trace=traceback.format_exc(),
            max_retries=self.retry_manager.get_max_retries(category)
        )
        
        # Log error
        self._log_error(error_info)
        
        # Add to history
        self.error_history.append(error_info)
        
        # Attempt recovery if appropriate
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.recovery_manager.attempt_recovery(error_info)
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error information."""
        error_logger = logging.getLogger("error_handler")
        
        # Log based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            error_logger.critical(self.reporter.get_technical_message(error_info))
        elif error_info.severity == ErrorSeverity.HIGH:
            error_logger.error(self.reporter.get_technical_message(error_info))
        else:
            error_logger.warning(self.reporter.get_technical_message(error_info))
        
        # Log to file
        self._save_error_to_file(error_info)
    
    def _save_error_to_file(self, error_info: ErrorInfo):
        """Save error information to file."""
        try:
            error_data = {
                "error_id": error_info.error_id,
                "timestamp": error_info.context.timestamp.isoformat(),
                "exception_type": error_info.exception_type,
                "error_message": error_info.error_message,
                "severity": error_info.severity.value,
                "category": error_info.category.value,
                "context": {
                    "user_id": error_info.context.user_id,
                    "session_id": error_info.context.session_id,
                    "request_id": error_info.context.request_id,
                    "file_path": error_info.context.file_path,
                    "operation": error_info.context.operation,
                    "metadata": error_info.context.metadata
                },
                "retry_count": error_info.retry_count,
                "max_retries": error_info.max_retries,
                "retry_strategy": error_info.retry_strategy.value,
                "recovery_attempted": error_info.recovery_attempted,
                "resolved": error_info.resolved,
                "resolution_time": error_info.resolution_time.isoformat() if error_info.resolution_time else None,
                "stack_trace": error_info.stack_trace
            }
            
            # Append to error log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(error_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save error to file: {e}")
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Retry a function with exponential backoff."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retry_count += 1
                
                # Create error info
                error_info = self.handle_error(e)
                error_info.retry_count = retry_count
                
                if not self.retry_manager.should_retry(error_info):
                    raise
                
                # Calculate delay
                delay = self.retry_manager.get_retry_delay(error_info)
                logger.info(f"Retrying in {delay} seconds (attempt {retry_count}/{max_retries})")
                time.sleep(delay)
        
        raise Exception(f"Function failed after {max_retries} retries")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        recent_errors = [e for e in self.error_history if e.context.timestamp > datetime.now() - timedelta(hours=24)]
        
        summary = {
            "total_errors": len(recent_errors),
            "by_severity": {},
            "by_category": {},
            "resolved_errors": len([e for e in recent_errors if e.resolved]),
            "unresolved_errors": len([e for e in recent_errors if not e.resolved])
        }
        
        for error in recent_errors:
            severity = error.severity.value
            category = error.category.value
            
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
        
        return summary

# Decorator for automatic error handling
def handle_errors(error_handler: Optional[ErrorHandler] = None):
    """Decorator for automatic error handling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = handler.handle_error(e)
                raise ReceiptProcessorError(
                    handler.reporter.get_user_message(error_info),
                    error_info.category,
                    error_info.severity,
                    error_info.context
                )
        return wrapper
    return decorator

# Context manager for error handling
class ErrorContext:
    """Context manager for error handling."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None, operation: Optional[str] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.operation = operation
        self.context = ErrorContext(operation=operation)
    
    def __enter__(self):
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_handler.handle_error(exc_val, self.context)
        return False  # Don't suppress exceptions
