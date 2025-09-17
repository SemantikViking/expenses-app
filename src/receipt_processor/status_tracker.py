"""
Enhanced Status Tracking System for Receipt Processing.

This module provides comprehensive status flow management, retry logic,
error categorization, timing measurement, and bulk operations for
the receipt processing workflow.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Set, Tuple
from uuid import UUID
from enum import Enum
import logging

from .models import (
    ReceiptProcessingLog, 
    ProcessingStatus, 
    StatusTransition,
    ReceiptData
)
from .storage import JSONStorageManager

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories for error classification."""
    AI_EXTRACTION_ERROR = "ai_extraction_error"
    IMAGE_PROCESSING_ERROR = "image_processing_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    FILE_ACCESS_ERROR = "file_access_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class RetryStrategy(str, Enum):
    """Retry strategies for failed operations."""
    IMMEDIATE = "immediate"  # Retry immediately
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Exponential backoff
    LINEAR_BACKOFF = "linear_backoff"  # Linear backoff
    FIXED_DELAY = "fixed_delay"  # Fixed delay between retries
    NO_RETRY = "no_retry"  # No retry


class ProcessingMetrics:
    """Tracks processing performance metrics."""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.ai_processing_time: Optional[float] = None
        self.data_validation_time: Optional[float] = None
        self.file_operations_time: Optional[float] = None
        self.total_retries: int = 0
        self.error_count: int = 0
        self.last_error: Optional[str] = None
        self.last_error_category: Optional[ErrorCategory] = None
    
    def start_processing(self):
        """Mark the start of processing."""
        self.start_time = datetime.now()
        logger.debug("Processing started")
    
    def end_processing(self):
        """Mark the end of processing."""
        self.end_time = datetime.now()
        logger.debug("Processing completed")
    
    def add_ai_processing_time(self, duration: float):
        """Record AI processing time."""
        self.ai_processing_time = duration
        logger.debug(f"AI processing took {duration:.2f} seconds")
    
    def add_validation_time(self, duration: float):
        """Record data validation time."""
        self.data_validation_time = duration
        logger.debug(f"Data validation took {duration:.2f} seconds")
    
    def add_file_operations_time(self, duration: float):
        """Record file operations time."""
        self.file_operations_time = duration
        logger.debug(f"File operations took {duration:.2f} seconds")
    
    def record_error(self, error_message: str, category: ErrorCategory):
        """Record an error occurrence."""
        self.error_count += 1
        self.last_error = error_message
        self.last_error_category = category
        logger.warning(f"Error recorded: {category.value} - {error_message}")
    
    def increment_retry(self):
        """Increment retry counter."""
        self.total_retries += 1
        logger.debug(f"Retry #{self.total_retries}")
    
    def get_total_processing_time(self) -> Optional[float]:
        """Get total processing time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "ai_processing_time": self.ai_processing_time,
            "data_validation_time": self.data_validation_time,
            "file_operations_time": self.file_operations_time,
            "total_processing_time": self.get_total_processing_time(),
            "total_retries": self.total_retries,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_error_category": self.last_error_category.value if self.last_error_category else None
        }


class StatusFlowValidator:
    """Validates status transitions according to business rules."""
    
    # Define valid status transitions
    VALID_TRANSITIONS: Dict[ProcessingStatus, Set[ProcessingStatus]] = {
        ProcessingStatus.PENDING: {
            ProcessingStatus.PROCESSING,
            ProcessingStatus.ERROR
        },
        ProcessingStatus.PROCESSING: {
            ProcessingStatus.PROCESSED,
            ProcessingStatus.ERROR,
            ProcessingStatus.NO_DATA_EXTRACTED,
            ProcessingStatus.RETRY
        },
        ProcessingStatus.RETRY: {
            ProcessingStatus.PROCESSING,
            ProcessingStatus.ERROR,
            ProcessingStatus.NO_DATA_EXTRACTED
        },
        ProcessingStatus.PROCESSED: {
            ProcessingStatus.EMAILED,
            ProcessingStatus.ERROR
        },
        ProcessingStatus.EMAILED: {
            ProcessingStatus.SUBMITTED,
            ProcessingStatus.ERROR
        },
        ProcessingStatus.SUBMITTED: {
            ProcessingStatus.PAYMENT_RECEIVED,
            ProcessingStatus.ERROR
        },
        ProcessingStatus.ERROR: {
            ProcessingStatus.RETRY,
            ProcessingStatus.PENDING
        },
        ProcessingStatus.NO_DATA_EXTRACTED: {
            ProcessingStatus.RETRY,
            ProcessingStatus.ERROR
        },
        ProcessingStatus.PAYMENT_RECEIVED: set()  # Terminal state
    }
    
    @classmethod
    def is_valid_transition(cls, from_status: ProcessingStatus, to_status: ProcessingStatus) -> bool:
        """Check if a status transition is valid."""
        if from_status not in cls.VALID_TRANSITIONS:
            return False
        
        return to_status in cls.VALID_TRANSITIONS[from_status]
    
    @classmethod
    def get_valid_next_statuses(cls, current_status: ProcessingStatus) -> Set[ProcessingStatus]:
        """Get all valid next statuses from current status."""
        return cls.VALID_TRANSITIONS.get(current_status, set())
    
    @classmethod
    def validate_transition(cls, from_status: ProcessingStatus, to_status: ProcessingStatus) -> Tuple[bool, Optional[str]]:
        """Validate a status transition and return result with error message."""
        if cls.is_valid_transition(from_status, to_status):
            return True, None
        
        valid_statuses = cls.get_valid_next_statuses(from_status)
        error_msg = f"Invalid transition from {from_status.value} to {to_status.value}. Valid next statuses: {[s.value for s in valid_statuses]}"
        return False, error_msg


class RetryManager:
    """Manages retry logic for failed operations."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_counts: Dict[UUID, int] = {}
        self.last_retry_times: Dict[UUID, datetime] = {}
    
    def should_retry(self, log_id: UUID, error_category: ErrorCategory) -> bool:
        """Determine if an operation should be retried."""
        # Some errors should never be retried
        no_retry_categories = {
            ErrorCategory.CONFIGURATION_ERROR,
            ErrorCategory.DATA_VALIDATION_ERROR
        }
        
        if error_category in no_retry_categories:
            return False
        
        current_retries = self.retry_counts.get(log_id, 0)
        return current_retries < self.max_retries
    
    def get_retry_delay(self, log_id: UUID, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF) -> float:
        """Calculate retry delay based on strategy."""
        current_retries = self.retry_counts.get(log_id, 0)
        
        if strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif strategy == RetryStrategy.FIXED_DELAY:
            return self.base_delay
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return self.base_delay * (current_retries + 1)
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return self.base_delay * (2 ** current_retries)
        else:
            return 0.0
    
    def record_retry(self, log_id: UUID):
        """Record a retry attempt."""
        self.retry_counts[log_id] = self.retry_counts.get(log_id, 0) + 1
        self.last_retry_times[log_id] = datetime.now()
        logger.info(f"Retry #{self.retry_counts[log_id]} recorded for log {log_id}")
    
    def can_retry_now(self, log_id: UUID, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF) -> bool:
        """Check if enough time has passed for the next retry."""
        if log_id not in self.last_retry_times:
            return True
        
        last_retry = self.last_retry_times[log_id]
        required_delay = self.get_retry_delay(log_id, strategy)
        time_since_last_retry = (datetime.now() - last_retry).total_seconds()
        
        return time_since_last_retry >= required_delay
    
    def reset_retry_count(self, log_id: UUID):
        """Reset retry count for successful operations."""
        if log_id in self.retry_counts:
            del self.retry_counts[log_id]
        if log_id in self.last_retry_times:
            del self.last_retry_times[log_id]
        logger.debug(f"Retry count reset for log {log_id}")


class ErrorCategorizer:
    """Categorizes errors for better handling and reporting."""
    
    ERROR_PATTERNS: Dict[ErrorCategory, List[str]] = {
        ErrorCategory.AI_EXTRACTION_ERROR: [
            "openai", "anthropic", "api", "model", "extraction", "vision",
            "token", "rate limit", "quota", "authentication"
        ],
        ErrorCategory.IMAGE_PROCESSING_ERROR: [
            "image", "corrupt", "decode", "pillow", "resize", "crop", "rotate"
        ],
        ErrorCategory.DATA_VALIDATION_ERROR: [
            "validation", "required", "parse", "convert", "type", "data format"
        ],
        ErrorCategory.FILE_ACCESS_ERROR: [
            "file", "permission", "not found", "access", "read", "write",
            "directory", "path", "exists"
        ],
        ErrorCategory.NETWORK_ERROR: [
            "network", "connection", "timeout", "dns", "http", "ssl",
            "socket", "unreachable"
        ],
        ErrorCategory.CONFIGURATION_ERROR: [
            "config", "setting", "environment", "variable", "missing config"
        ],
        ErrorCategory.TIMEOUT_ERROR: [
            "timeout", "timed out", "expired", "deadline"
        ]
    }
    
    @classmethod
    def categorize_error(cls, error_message: str) -> ErrorCategory:
        """Categorize an error based on its message."""
        error_lower = error_message.lower()
        
        for category, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in error_lower:
                    return category
        
        return ErrorCategory.UNKNOWN_ERROR
    
    @classmethod
    def get_error_priority(cls, category: ErrorCategory) -> int:
        """Get error priority (lower number = higher priority)."""
        priority_map = {
            ErrorCategory.CONFIGURATION_ERROR: 1,
            ErrorCategory.FILE_ACCESS_ERROR: 2,
            ErrorCategory.DATA_VALIDATION_ERROR: 3,
            ErrorCategory.AI_EXTRACTION_ERROR: 4,
            ErrorCategory.IMAGE_PROCESSING_ERROR: 5,
            ErrorCategory.NETWORK_ERROR: 6,
            ErrorCategory.TIMEOUT_ERROR: 7,
            ErrorCategory.UNKNOWN_ERROR: 8
        }
        return priority_map.get(category, 9)


class EnhancedStatusTracker:
    """Enhanced status tracking with comprehensive workflow management."""
    
    def __init__(self, storage_manager: JSONStorageManager):
        self.storage = storage_manager
        self.retry_manager = RetryManager()
        self.validator = StatusFlowValidator()
        self.categorizer = ErrorCategorizer()
        self.active_metrics: Dict[UUID, ProcessingMetrics] = {}
    
    def start_processing(self, log_id: UUID) -> bool:
        """Start processing a receipt and update status."""
        try:
            # Get current log entry
            log_entry = self.storage.get_log_entry(log_id)
            if not log_entry:
                logger.error(f"Log entry {log_id} not found")
                return False
            
            # Validate transition
            if not self.validator.is_valid_transition(log_entry.current_status, ProcessingStatus.PROCESSING):
                logger.error(f"Invalid transition to PROCESSING from {log_entry.current_status}")
                return False
            
            # Initialize metrics
            metrics = ProcessingMetrics()
            metrics.start_processing()
            self.active_metrics[log_id] = metrics
            
            # Update status
            success = self.storage.add_status_transition(
                log_id,
                ProcessingStatus.PROCESSING,
                reason="Processing started",
                user="system",
                metadata={"start_time": datetime.now().isoformat()}
            )
            
            if success:
                logger.info(f"Started processing for log {log_id}")
                return True
            else:
                logger.error(f"Failed to update status for log {log_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting processing for log {log_id}: {e}")
            return False
    
    def complete_processing(self, log_id: UUID, receipt_data: Optional[ReceiptData] = None) -> bool:
        """Complete processing and determine final status."""
        try:
            # Get current log entry
            log_entry = self.storage.get_log_entry(log_id)
            if not log_entry:
                logger.error(f"Log entry {log_id} not found")
                return False
            
            # Get metrics
            metrics = self.active_metrics.get(log_id)
            if metrics:
                metrics.end_processing()
            
            # Determine final status based on receipt data
            if receipt_data and receipt_data.has_required_data:
                final_status = ProcessingStatus.PROCESSED
                reason = "Processing completed successfully"
                metadata = {
                    "completion_time": datetime.now().isoformat(),
                    "extraction_confidence": receipt_data.extraction_confidence,
                    "processing_metrics": metrics.to_dict() if metrics else None
                }
            else:
                final_status = ProcessingStatus.NO_DATA_EXTRACTED
                reason = "No valid data extracted from receipt"
                metadata = {
                    "completion_time": datetime.now().isoformat(),
                    "processing_metrics": metrics.to_dict() if metrics else None
                }
            
            # Update status
            success = self.storage.add_status_transition(
                log_id,
                final_status,
                reason=reason,
                user="system",
                metadata=metadata
            )
            
            # Update log entry with receipt data
            if receipt_data and success:
                self.storage.update_log_entry(log_id, {
                    "receipt_data": receipt_data,
                    "processed_at": datetime.now(),
                    "processing_time_seconds": metrics.get_total_processing_time() if metrics else None
                })
            
            # Clean up metrics
            if log_id in self.active_metrics:
                del self.active_metrics[log_id]
            
            # Reset retry count on success
            self.retry_manager.reset_retry_count(log_id)
            
            if success:
                logger.info(f"Completed processing for log {log_id} with status {final_status}")
                return True
            else:
                logger.error(f"Failed to complete processing for log {log_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error completing processing for log {log_id}: {e}")
            return False
    
    def record_error(self, log_id: UUID, error_message: str, should_retry: bool = True) -> bool:
        """Record an error and determine if retry is needed."""
        try:
            # Categorize error
            error_category = self.categorizer.categorize_error(error_message)
            
            # Get metrics and record error
            metrics = self.active_metrics.get(log_id)
            if metrics:
                metrics.record_error(error_message, error_category)
            
            # Determine if we should retry
            if should_retry and self.retry_manager.should_retry(log_id, error_category):
                # Record retry
                self.retry_manager.record_retry(log_id)
                
                # Update to retry status
                success = self.storage.add_status_transition(
                    log_id,
                    ProcessingStatus.RETRY,
                    reason=f"Error occurred, scheduling retry: {error_message}",
                    user="system",
                    metadata={
                        "error_category": error_category.value,
                        "error_priority": self.categorizer.get_error_priority(error_category),
                        "retry_count": self.retry_manager.retry_counts.get(log_id, 0),
                        "error_time": datetime.now().isoformat()
                    }
                )
                
                if success:
                    logger.warning(f"Error recorded for log {log_id}, scheduled for retry: {error_message}")
                    return True
            else:
                # No retry, mark as error
                success = self.storage.add_status_transition(
                    log_id,
                    ProcessingStatus.ERROR,
                    reason=f"Error occurred, no retry: {error_message}",
                    user="system",
                    metadata={
                        "error_category": error_category.value,
                        "error_priority": self.categorizer.get_error_priority(error_category),
                        "final_error": True,
                        "error_time": datetime.now().isoformat()
                    }
                )
                
                if success:
                    logger.error(f"Error recorded for log {log_id}, no retry: {error_message}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error recording error for log {log_id}: {e}")
            return False
    
    def update_status(self, log_id: UUID, new_status: ProcessingStatus, 
                     reason: Optional[str] = None, user: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update status with validation."""
        try:
            # Get current log entry
            log_entry = self.storage.get_log_entry(log_id)
            if not log_entry:
                logger.error(f"Log entry {log_id} not found")
                return False
            
            # Validate transition
            is_valid, error_msg = self.validator.validate_transition(
                log_entry.current_status, new_status
            )
            
            if not is_valid:
                logger.error(f"Invalid status transition: {error_msg}")
                return False
            
            # Update status
            success = self.storage.add_status_transition(
                log_id,
                new_status,
                reason=reason,
                user=user,
                metadata=metadata
            )
            
            if success:
                logger.info(f"Status updated for log {log_id}: {log_entry.current_status} → {new_status}")
                return True
            else:
                logger.error(f"Failed to update status for log {log_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating status for log {log_id}: {e}")
            return False
    
    def bulk_update_status(self, log_ids: List[UUID], new_status: ProcessingStatus,
                          reason: Optional[str] = None, user: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[UUID, bool]:
        """Update status for multiple log entries."""
        results = {}
        
        for log_id in log_ids:
            try:
                success = self.update_status(log_id, new_status, reason, user, metadata)
                results[log_id] = success
            except Exception as e:
                logger.error(f"Error in bulk update for log {log_id}: {e}")
                results[log_id] = False
        
        successful_updates = sum(1 for success in results.values() if success)
        logger.info(f"Bulk status update completed: {successful_updates}/{len(log_ids)} successful")
        
        return results
    
    def get_retry_candidates(self) -> List[UUID]:
        """Get log entries that are candidates for retry."""
        retry_logs = self.storage.get_logs_by_status(ProcessingStatus.RETRY)
        candidates = []
        
        for log_entry in retry_logs:
            if self.retry_manager.can_retry_now(log_entry.id):
                candidates.append(log_entry.id)
        
        return candidates
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors by category."""
        error_logs = self.storage.get_logs_by_status(ProcessingStatus.ERROR)
        retry_logs = self.storage.get_logs_by_status(ProcessingStatus.RETRY)
        
        error_summary = {
            "total_errors": len(error_logs),
            "total_retries": len(retry_logs),
            "by_category": {},
            "by_priority": {}
        }
        
        # Categorize errors
        for log_entry in error_logs + retry_logs:
            latest_transition = log_entry.get_latest_transition()
            if latest_transition and latest_transition.metadata:
                category = latest_transition.metadata.get("error_category")
                if category:
                    error_summary["by_category"][category] = error_summary["by_category"].get(category, 0) + 1
                    
                    priority = latest_transition.metadata.get("error_priority", 9)
                    error_summary["by_priority"][priority] = error_summary["by_priority"].get(priority, 0) + 1
        
        return error_summary
    
    def cleanup_old_metrics(self, max_age_hours: int = 24):
        """Clean up old processing metrics."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for log_id, metrics in self.active_metrics.items():
            if metrics.start_time and metrics.start_time < cutoff_time:
                to_remove.append(log_id)
        
        for log_id in to_remove:
            del self.active_metrics[log_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old processing metrics")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        all_logs = self.storage.get_all_logs()
        
        stats = {
            "total_receipts": len(all_logs),
            "by_status": {},
            "processing_times": [],
            "error_rates": {},
            "retry_rates": {}
        }
        
        # Count by status
        for log_entry in all_logs:
            status = log_entry.current_status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Collect processing times
            if log_entry.processing_time_seconds:
                stats["processing_times"].append(log_entry.processing_time_seconds)
        
        # Calculate averages
        if stats["processing_times"]:
            stats["avg_processing_time"] = sum(stats["processing_times"]) / len(stats["processing_times"])
            stats["min_processing_time"] = min(stats["processing_times"])
            stats["max_processing_time"] = max(stats["processing_times"])
        
        # Error and retry rates
        total_processed = stats["by_status"].get("processed", 0) + stats["by_status"].get("error", 0) + stats["by_status"].get("no_data_extracted", 0)
        if total_processed > 0:
            stats["error_rate"] = stats["by_status"].get("error", 0) / total_processed
            stats["retry_rate"] = stats["by_status"].get("retry", 0) / total_processed
        
        return stats
