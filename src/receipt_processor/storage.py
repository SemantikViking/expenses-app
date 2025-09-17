"""
JSON-based storage system for receipt processing logs.

This module provides atomic file operations, log management, and data persistence
for the receipt processing application using JSON files.
"""

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from uuid import UUID
import hashlib
import os
import logging

from .models import (
    ReceiptProcessingLog, 
    ReceiptProcessingLogFile, 
    ProcessingStatus,
    StatusTransition
)

logger = logging.getLogger(__name__)


class JSONStorageManager:
    """Manages JSON-based storage for receipt processing logs."""
    
    def __init__(self, log_file_path: Path, backup_dir: Optional[Path] = None):
        """
        Initialize the storage manager.
        
        Args:
            log_file_path: Path to the main log file
            backup_dir: Directory for log file backups (optional)
        """
        self.log_file_path = Path(log_file_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.log_file_path.parent / "backups"
        self.temp_dir = self.log_file_path.parent / "temp"
        
        # Ensure directories exist
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file if it doesn't exist
        if not self.log_file_path.exists():
            self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Create a new empty log file."""
        initial_log = ReceiptProcessingLogFile()
        self._write_log_file_atomic(initial_log)
        logger.info(f"Initialized new log file at {self.log_file_path}")
    
    def _write_log_file_atomic(self, log_file: ReceiptProcessingLogFile) -> bool:
        """
        Write log file atomically using temporary file and atomic move.
        
        Args:
            log_file: The log file object to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create temporary file in the same directory for atomic move
            temp_file = self.temp_dir / f"temp_{self.log_file_path.name}_{datetime.now().timestamp()}"
            
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(log_file.model_dump(), f, indent=2, default=str)
            
            # Atomic move
            shutil.move(str(temp_file), str(self.log_file_path))
            
            logger.debug(f"Successfully wrote log file atomically to {self.log_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write log file atomically: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def _read_log_file(self) -> Optional[ReceiptProcessingLogFile]:
        """
        Read the current log file.
        
        Returns:
            ReceiptProcessingLogFile or None if read failed
        """
        try:
            if not self.log_file_path.exists():
                logger.warning(f"Log file does not exist: {self.log_file_path}")
                return None
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ReceiptProcessingLogFile.model_validate(data)
            
        except Exception as e:
            logger.error(f"Failed to read log file {self.log_file_path}: {e}")
            return None
    
    def add_log_entry(self, log_entry: ReceiptProcessingLog) -> bool:
        """
        Add a new log entry to the storage.
        
        Args:
            log_entry: The log entry to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read current log file
            log_file = self._read_log_file()
            if log_file is None:
                logger.error("Failed to read current log file")
                return False
            
            # Add the new log entry
            log_file.add_log(log_entry)
            
            # Write back atomically
            success = self._write_log_file_atomic(log_file)
            if success:
                logger.info(f"Added log entry {log_entry.id} for file {log_entry.original_filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add log entry: {e}")
            return False
    
    def update_log_entry(self, log_id: UUID, updates: Dict[str, Any]) -> bool:
        """
        Update an existing log entry.
        
        Args:
            log_id: ID of the log entry to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read current log file
            log_file = self._read_log_file()
            if log_file is None:
                logger.error("Failed to read current log file")
                return False
            
            # Find the log entry
            log_entry = log_file.get_log_by_id(log_id)
            if log_entry is None:
                logger.warning(f"Log entry {log_id} not found")
                return False
            
            # Update the log entry
            for key, value in updates.items():
                if hasattr(log_entry, key):
                    setattr(log_entry, key, value)
            
            # Update timestamp
            log_entry.last_updated = datetime.now()
            log_file.last_updated = datetime.now()
            
            # Write back atomically
            success = self._write_log_file_atomic(log_file)
            if success:
                logger.info(f"Updated log entry {log_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update log entry {log_id}: {e}")
            return False
    
    def add_status_transition(
        self, 
        log_id: UUID, 
        new_status: ProcessingStatus,
        reason: Optional[str] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a status transition to an existing log entry.
        
        Args:
            log_id: ID of the log entry
            new_status: New status to transition to
            reason: Reason for the transition
            user: User who initiated the transition
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read current log file
            log_file = self._read_log_file()
            if log_file is None:
                logger.error("Failed to read current log file")
                return False
            
            # Find the log entry
            log_entry = log_file.get_log_by_id(log_id)
            if log_entry is None:
                logger.warning(f"Log entry {log_id} not found")
                return False
            
            # Add status transition
            log_entry.add_status_transition(new_status, reason, user, metadata)
            
            # Update log file timestamp
            log_file.last_updated = datetime.now()
            
            # Write back atomically
            success = self._write_log_file_atomic(log_file)
            if success:
                logger.info(f"Added status transition to {new_status} for log entry {log_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add status transition for log entry {log_id}: {e}")
            return False
    
    def get_log_entry(self, log_id: UUID) -> Optional[ReceiptProcessingLog]:
        """
        Get a specific log entry by ID.
        
        Args:
            log_id: ID of the log entry
            
        Returns:
            ReceiptProcessingLog or None if not found
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return None
            
            return log_file.get_log_by_id(log_id)
            
        except Exception as e:
            logger.error(f"Failed to get log entry {log_id}: {e}")
            return None
    
    def get_logs_by_status(self, status: ProcessingStatus) -> List[ReceiptProcessingLog]:
        """
        Get all log entries with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching log entries
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return []
            
            return log_file.get_logs_by_status(status)
            
        except Exception as e:
            logger.error(f"Failed to get logs by status {status}: {e}")
            return []
    
    def get_recent_logs(self, limit: int = 10) -> List[ReceiptProcessingLog]:
        """
        Get the most recent log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent log entries
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return []
            
            return log_file.get_recent_logs(limit)
            
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def get_all_logs(self) -> List[ReceiptProcessingLog]:
        """
        Get all log entries.
        
        Returns:
            List of all log entries
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return []
            
            return log_file.logs
            
        except Exception as e:
            logger.error(f"Failed to get all logs: {e}")
            return []
    
    def cleanup_old_logs(self, max_age_days: int = 180) -> int:
        """
        Remove logs older than specified days.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Number of logs removed
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return 0
            
            removed_count = log_file.cleanup_old_logs(max_age_days)
            
            if removed_count > 0:
                # Write back the cleaned log file
                success = self._write_log_file_atomic(log_file)
                if success:
                    logger.info(f"Cleaned up {removed_count} old log entries")
                else:
                    logger.error("Failed to save cleaned log file")
                    return 0
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0
    
    def create_backup(self) -> Optional[Path]:
        """
        Create a backup of the current log file.
        
        Returns:
            Path to backup file or None if failed
        """
        try:
            if not self.log_file_path.exists():
                logger.warning("No log file to backup")
                return None
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"receipt_log_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            # Copy the file
            shutil.copy2(self.log_file_path, backup_path)
            
            logger.info(f"Created backup at {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return {}
            
            return {
                "total_receipts": log_file.total_receipts,
                "successful_extractions": log_file.successful_extractions,
                "failed_extractions": log_file.failed_extractions,
                "last_updated": log_file.last_updated,
                "file_size_bytes": self.log_file_path.stat().st_size if self.log_file_path.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def verify_file_integrity(self) -> bool:
        """
        Verify the integrity of the log file.
        
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            log_file = self._read_log_file()
            if log_file is None:
                return False
            
            # Basic validation
            if not isinstance(log_file.logs, list):
                logger.error("Log file structure is invalid")
                return False
            
            # Check that all log entries have required fields
            for log_entry in log_file.logs:
                if not hasattr(log_entry, 'id') or not hasattr(log_entry, 'original_filename'):
                    logger.error("Log entry missing required fields")
                    return False
            
            logger.info("Log file integrity verified")
            return True
            
        except Exception as e:
            logger.error(f"Log file integrity check failed: {e}")
            return False


class LogRotationManager:
    """Manages log file rotation and archiving."""
    
    def __init__(self, storage_manager: JSONStorageManager, max_file_size_mb: int = 50):
        """
        Initialize log rotation manager.
        
        Args:
            storage_manager: The storage manager instance
            max_file_size_mb: Maximum file size before rotation (in MB)
        """
        self.storage_manager = storage_manager
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
    
    def should_rotate(self) -> bool:
        """
        Check if log file should be rotated.
        
        Returns:
            bool: True if rotation is needed
        """
        try:
            if not self.storage_manager.log_file_path.exists():
                return False
            
            file_size = self.storage_manager.log_file_path.stat().st_size
            return file_size > self.max_file_size_bytes
            
        except Exception as e:
            logger.error(f"Failed to check rotation condition: {e}")
            return False
    
    def rotate_logs(self) -> bool:
        """
        Rotate the current log file.
        
        Returns:
            bool: True if successful
        """
        try:
            # Create backup before rotation
            backup_path = self.storage_manager.create_backup()
            if backup_path is None:
                logger.error("Failed to create backup before rotation")
                return False
            
            # Read current log file
            current_log = self.storage_manager._read_log_file()
            if current_log is None:
                logger.error("Failed to read current log file for rotation")
                return False
            
            # Create new empty log file
            new_log = ReceiptProcessingLogFile()
            success = self.storage_manager._write_log_file_atomic(new_log)
            
            if success:
                logger.info(f"Rotated log file. Backup created at {backup_path}")
                return True
            else:
                logger.error("Failed to create new log file after rotation")
                return False
                
        except Exception as e:
            logger.error(f"Failed to rotate logs: {e}")
            return False
    
    def cleanup_old_backups(self, max_backups: int = 10) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            max_backups: Maximum number of backups to keep
            
        Returns:
            Number of backup files removed
        """
        try:
            if not self.storage_manager.backup_dir.exists():
                return 0
            
            # Get all backup files sorted by modification time
            backup_files = list(self.storage_manager.backup_dir.glob("receipt_log_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            removed_count = 0
            for backup_file in backup_files[max_backups:]:
                try:
                    backup_file.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old backup: {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove backup {backup_file}: {e}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backup files")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0
