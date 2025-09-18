"""
File Management & Naming System for Receipt Processing.

This module provides comprehensive file management capabilities including
standardized naming, organization, backup, validation, and cleanup utilities.
"""

import os
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
import logging
from dataclasses import dataclass
import hashlib

from .models import ReceiptProcessingLog, ReceiptData, ProcessingStatus, Currency

logger = logging.getLogger(__name__)


class FileOrganizationMode(str, Enum):
    """File organization modes."""
    FLAT = "flat"  # All files in one directory
    BY_DATE = "by_date"  # Organized by date (YYYY/MM/DD/)
    BY_VENDOR = "by_vendor"  # Organized by vendor name
    BY_STATUS = "by_status"  # Organized by processing status
    BY_MONTH = "by_month"  # Organized by month (YYYY/MM/)
    CUSTOM = "custom"  # Custom organization logic


class FileValidationResult(str, Enum):
    """File validation results."""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_SIZE = "invalid_size"
    INVALID_PERMISSIONS = "invalid_permissions"
    CORRUPTED = "corrupted"
    DUPLICATE = "duplicate"


@dataclass
class FileValidationReport:
    """File validation report."""
    is_valid: bool
    result: FileValidationResult
    issues: List[str]
    file_size: int
    file_hash: Optional[str] = None
    suggested_fixes: List[str] = None


@dataclass
class FileRenameResult:
    """Result of file rename operation."""
    success: bool
    original_path: Path
    new_path: Optional[Path] = None
    backup_path: Optional[Path] = None
    error_message: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class FileOrganizationConfig:
    """Configuration for file organization."""
    mode: FileOrganizationMode
    base_directory: Path
    create_backups: bool = True
    preserve_original_structure: bool = False
    custom_organization_func: Optional[callable] = None
    max_file_size_mb: int = 50
    allowed_extensions: List[str] = None
    duplicate_handling: str = "increment"  # increment, skip, overwrite


class FileNameSanitizer:
    """Sanitizes and validates file names."""
    
    # Characters that are not allowed in file names
    INVALID_CHARS = r'[<>:"/\\|?*]'
    # Characters that should be replaced with underscores
    REPLACE_CHARS = r'[^\w\-_\.]'
    # Maximum file name length (excluding extension)
    MAX_NAME_LENGTH = 200
    # Maximum extension length
    MAX_EXT_LENGTH = 10
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize a filename to be safe for filesystem use."""
        if not filename:
            return "unnamed_file"
        
        # Split filename and extension
        name, ext = os.path.splitext(filename)
        
        # Remove invalid characters
        name = re.sub(cls.INVALID_CHARS, '', name)
        
        # Replace problematic characters with underscores
        name = re.sub(cls.REPLACE_CHARS, '_', name)
        
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores and dots
        name = name.strip('_.')
        
        # Ensure name is not empty
        if not name:
            name = "unnamed_file"
        
        # Truncate if too long
        if len(name) > cls.MAX_NAME_LENGTH:
            name = name[:cls.MAX_NAME_LENGTH]
        
        # Sanitize extension
        if ext:
            ext = ext.lower()
            ext = re.sub(cls.INVALID_CHARS, '', ext)
            if len(ext) > cls.MAX_EXT_LENGTH:
                ext = ext[:cls.MAX_EXT_LENGTH]
        
        return name + ext
    
    @classmethod
    def validate_filename(cls, filename: str) -> Tuple[bool, List[str]]:
        """Validate a filename and return issues if any."""
        issues = []
        
        if not filename:
            issues.append("Filename is empty")
            return False, issues
        
        # Check for invalid characters
        if re.search(cls.INVALID_CHARS, filename):
            issues.append("Contains invalid characters")
        
        # Check length
        if len(filename) > cls.MAX_NAME_LENGTH + cls.MAX_EXT_LENGTH:
            issues.append("Filename too long")
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            issues.append("Uses reserved name")
        
        # Check for leading/trailing spaces or dots
        if filename.startswith((' ', '.')) or filename.endswith((' ', '.')):
            issues.append("Starts or ends with space or dot")
        
        return len(issues) == 0, issues


class FileNamingGenerator:
    """Generates standardized file names for receipts."""
    
    @classmethod
    def generate_filename(cls, receipt_data: ReceiptData, original_filename: str, 
                         config: Optional[Dict[str, Any]] = None) -> str:
        """Generate a standardized filename for a receipt."""
        if not receipt_data or not receipt_data.has_required_data:
            # Fallback to sanitized original filename
            return FileNameSanitizer.sanitize_filename(original_filename)
        
        # Extract components
        date_str = receipt_data.transaction_date.strftime("%Y-%m-%d")
        vendor_name = cls._sanitize_vendor_name(receipt_data.vendor_name)
        amount_str = cls._format_amount(receipt_data.total_amount, receipt_data.currency)
        
        # Get original extension
        original_ext = Path(original_filename).suffix.lower()
        if not original_ext:
            original_ext = ".jpg"  # Default extension
        
        # Generate filename
        filename = f"{date_str}_{vendor_name}_{amount_str}{original_ext}"
        
        # Sanitize the final filename
        filename = FileNameSanitizer.sanitize_filename(filename)
        
        return filename
    
    @classmethod
    def _sanitize_vendor_name(cls, vendor_name: str) -> str:
        """Sanitize vendor name for use in filename."""
        if not vendor_name:
            return "Unknown"
        
        # Remove common business suffixes
        vendor_name = re.sub(r'\s+(Inc|LLC|Corp|Corporation|Company|Co|Ltd|Limited)\.?$', '', vendor_name, flags=re.IGNORECASE)
        
        # Replace spaces and special characters with underscores
        vendor_name = re.sub(r'[^\w\-]', '_', vendor_name)
        
        # Remove multiple consecutive underscores
        vendor_name = re.sub(r'_+', '_', vendor_name)
        
        # Remove leading/trailing underscores
        vendor_name = vendor_name.strip('_')
        
        # Truncate if too long
        if len(vendor_name) > 50:
            vendor_name = vendor_name[:50]
        
        return vendor_name or "Unknown"
    
    @classmethod
    def _format_amount(cls, amount: float, currency: Currency) -> str:
        """Format amount for filename."""
        if amount is None:
            return "0_00"
        
        # Format as integer cents to avoid decimal issues
        cents = int(amount * 100)
        return f"{cents:06d}"  # 6 digits with leading zeros


class FileValidator:
    """Validates files before processing."""
    
    @classmethod
    def validate_file(cls, file_path: Path, config: FileOrganizationConfig) -> FileValidationReport:
        """Validate a file for processing."""
        issues = []
        suggested_fixes = []
        
        try:
            # Check if file exists
            if not file_path.exists():
                return FileValidationReport(
                    is_valid=False,
                    result=FileValidationResult.INVALID_FORMAT,
                    issues=["File does not exist"],
                    file_size=0
                )
            
            # Check file size
            file_size = file_path.stat().st_size
            max_size_bytes = config.max_file_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                issues.append(f"File too large ({file_size / 1024 / 1024:.1f}MB > {config.max_file_size_mb}MB)")
                suggested_fixes.append("Reduce file size or increase max_file_size_mb limit")
            
            # Check file extension
            if config.allowed_extensions:
                file_ext = file_path.suffix.lower()
                if file_ext not in config.allowed_extensions:
                    issues.append(f"Invalid file extension: {file_ext}")
                    suggested_fixes.append(f"Use one of: {', '.join(config.allowed_extensions)}")
            
            # Check file permissions
            if not os.access(file_path, os.R_OK):
                issues.append("File not readable")
                suggested_fixes.append("Check file permissions")
            
            # Check if file is corrupted (basic check)
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Try to read first 1KB
            except (IOError, OSError) as e:
                issues.append(f"File appears corrupted: {str(e)}")
                suggested_fixes.append("Check file integrity")
            
            # Generate file hash for duplicate detection
            file_hash = cls._calculate_file_hash(file_path)
            
            # Determine result
            if not issues:
                result = FileValidationResult.VALID
            elif any("corrupted" in issue.lower() for issue in issues):
                result = FileValidationResult.CORRUPTED
            elif any("too large" in issue.lower() for issue in issues):
                result = FileValidationResult.INVALID_SIZE
            elif any("extension" in issue.lower() for issue in issues):
                result = FileValidationResult.INVALID_FORMAT
            elif any("permission" in issue.lower() for issue in issues):
                result = FileValidationResult.INVALID_PERMISSIONS
            else:
                result = FileValidationResult.INVALID_FORMAT
            
            return FileValidationReport(
                is_valid=len(issues) == 0,
                result=result,
                issues=issues,
                file_size=file_size,
                file_hash=file_hash,
                suggested_fixes=suggested_fixes
            )
            
        except Exception as e:
            return FileValidationReport(
                is_valid=False,
                result=FileValidationResult.CORRUPTED,
                issues=[f"Validation error: {str(e)}"],
                file_size=0
            )
    
    @classmethod
    def _calculate_file_hash(cls, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for duplicate detection."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""


class DuplicateHandler:
    """Handles duplicate files during processing."""
    
    @classmethod
    def handle_duplicate(cls, file_path: Path, target_path: Path, 
                        handling_mode: str = "increment") -> Tuple[Path, bool]:
        """Handle duplicate file names."""
        if not target_path.exists():
            return target_path, True
        
        if handling_mode == "skip":
            return target_path, False
        
        elif handling_mode == "overwrite":
            return target_path, True
        
        elif handling_mode == "increment":
            return cls._increment_filename(target_path), True
        
        else:
            raise ValueError(f"Unknown duplicate handling mode: {handling_mode}")
    
    @classmethod
    def _increment_filename(cls, file_path: Path) -> Path:
        """Increment filename to avoid duplicates."""
        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter:03d}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
            
            # Prevent infinite loop
            if counter > 9999:
                # Use timestamp as fallback
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{stem}_{timestamp}{suffix}"
                return parent / new_name


class FileBackupManager:
    """Manages file backups before processing."""
    
    @classmethod
    def create_backup(cls, file_path: Path, backup_dir: Path) -> Optional[Path]:
        """Create a backup of a file."""
        try:
            # Ensure backup directory exists
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    @classmethod
    def restore_from_backup(cls, backup_path: Path, target_path: Path) -> bool:
        """Restore file from backup."""
        try:
            shutil.copy2(backup_path, target_path)
            logger.info(f"Restored from backup: {backup_path} -> {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False


class FileOrganizer:
    """Organizes files according to configuration."""
    
    @classmethod
    def organize_file(cls, file_path: Path, config: FileOrganizationConfig, 
                     receipt_data: Optional[ReceiptData] = None,
                     log_entry: Optional[ReceiptProcessingLog] = None) -> Path:
        """Organize a file according to the configuration."""
        if config.mode == FileOrganizationMode.FLAT:
            return file_path
        
        elif config.mode == FileOrganizationMode.BY_DATE:
            return cls._organize_by_date(file_path, config, receipt_data)
        
        elif config.mode == FileOrganizationMode.BY_VENDOR:
            return cls._organize_by_vendor(file_path, config, receipt_data)
        
        elif config.mode == FileOrganizationMode.BY_STATUS:
            return cls._organize_by_status(file_path, config, log_entry)
        
        elif config.mode == FileOrganizationMode.BY_MONTH:
            return cls._organize_by_month(file_path, config, receipt_data)
        
        elif config.mode == FileOrganizationMode.CUSTOM and config.custom_organization_func:
            return config.custom_organization_func(file_path, config, receipt_data, log_entry)
        
        else:
            return file_path
    
    @classmethod
    def _organize_by_date(cls, file_path: Path, config: FileOrganizationConfig, 
                         receipt_data: Optional[ReceiptData]) -> Path:
        """Organize files by date (YYYY/MM/DD/)."""
        if receipt_data and receipt_data.transaction_date:
            date = receipt_data.transaction_date
        else:
            date = datetime.now()
        
        date_dir = config.base_directory / date.strftime("%Y") / date.strftime("%m") / date.strftime("%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        return date_dir / file_path.name
    
    @classmethod
    def _organize_by_vendor(cls, file_path: Path, config: FileOrganizationConfig, 
                           receipt_data: Optional[ReceiptData]) -> Path:
        """Organize files by vendor name."""
        if receipt_data and receipt_data.vendor_name:
            vendor_name = FileNameSanitizer.sanitize_filename(receipt_data.vendor_name)
        else:
            vendor_name = "Unknown"
        
        vendor_dir = config.base_directory / vendor_name
        vendor_dir.mkdir(parents=True, exist_ok=True)
        
        return vendor_dir / file_path.name
    
    @classmethod
    def _organize_by_status(cls, file_path: Path, config: FileOrganizationConfig, 
                           log_entry: Optional[ReceiptProcessingLog]) -> Path:
        """Organize files by processing status."""
        if log_entry:
            status = log_entry.current_status.value
        else:
            status = "unknown"
        
        status_dir = config.base_directory / status
        status_dir.mkdir(parents=True, exist_ok=True)
        
        return status_dir / file_path.name
    
    @classmethod
    def _organize_by_month(cls, file_path: Path, config: FileOrganizationConfig, 
                          receipt_data: Optional[ReceiptData]) -> Path:
        """Organize files by month (YYYY/MM/)."""
        if receipt_data and receipt_data.transaction_date:
            date = receipt_data.transaction_date
        else:
            date = datetime.now()
        
        month_dir = config.base_directory / date.strftime("%Y") / date.strftime("%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        
        return month_dir / file_path.name


class FileManager:
    """Main file management class that coordinates all file operations."""
    
    def __init__(self, config: FileOrganizationConfig):
        self.config = config
        self.validator = FileValidator()
        self.backup_manager = FileBackupManager()
        self.organizer = FileOrganizer()
        self.duplicate_handler = DuplicateHandler()
        self.naming_generator = FileNamingGenerator()
    
    def process_file(self, file_path: Path, receipt_data: Optional[ReceiptData] = None,
                    log_entry: Optional[ReceiptProcessingLog] = None) -> FileRenameResult:
        """Process a file with renaming, organization, and backup."""
        try:
            # Validate file
            validation_report = self.validator.validate_file(file_path, self.config)
            if not validation_report.is_valid:
                return FileRenameResult(
                    success=False,
                    original_path=file_path,
                    error_message=f"File validation failed: {', '.join(validation_report.issues)}"
                )
            
            # Create backup if configured
            backup_path = None
            if self.config.create_backups:
                backup_dir = self.config.base_directory / "backups"
                backup_path = self.backup_manager.create_backup(file_path, backup_dir)
                if not backup_path:
                    logger.warning(f"Failed to create backup for {file_path}")
            
            # Generate new filename
            if receipt_data and receipt_data.has_required_data:
                new_filename = self.naming_generator.generate_filename(
                    receipt_data, file_path.name
                )
            else:
                new_filename = FileNameSanitizer.sanitize_filename(file_path.name)
            
            # Determine target directory
            if self.config.mode != FileOrganizationMode.FLAT:
                target_dir = self.organizer.organize_file(
                    file_path, self.config, receipt_data, log_entry
                ).parent
            else:
                target_dir = self.config.base_directory
            
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Create target path
            target_path = target_dir / new_filename
            
            # Handle duplicates
            final_path, should_proceed = self.duplicate_handler.handle_duplicate(
                file_path, target_path, self.config.duplicate_handling
            )
            
            if not should_proceed:
                return FileRenameResult(
                    success=False,
                    original_path=file_path,
                    error_message="Duplicate file skipped"
                )
            
            # Perform the rename/move
            if file_path != final_path:
                shutil.move(str(file_path), str(final_path))
                logger.info(f"Renamed file: {file_path} -> {final_path}")
            else:
                logger.info(f"File already in correct location: {file_path}")
            
            # Prepare rollback data
            rollback_data = {
                "original_path": str(file_path),
                "backup_path": str(backup_path) if backup_path else None,
                "file_hash": validation_report.file_hash
            }
            
            return FileRenameResult(
                success=True,
                original_path=file_path,
                new_path=final_path,
                backup_path=backup_path,
                rollback_data=rollback_data
            )
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return FileRenameResult(
                success=False,
                original_path=file_path,
                error_message=str(e)
            )
    
    def rollback_file(self, rollback_data: Dict[str, Any]) -> bool:
        """Rollback a file operation using rollback data."""
        try:
            original_path = Path(rollback_data["original_path"])
            backup_path = Path(rollback_data["backup_path"]) if rollback_data.get("backup_path") else None
            
            # If we have a backup, restore from it
            if backup_path and backup_path.exists():
                return self.backup_manager.restore_from_backup(backup_path, original_path)
            
            # Otherwise, try to move the file back
            current_path = Path(rollback_data.get("current_path", original_path))
            if current_path.exists() and current_path != original_path:
                shutil.move(str(current_path), str(original_path))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error rolling back file operation: {e}")
            return False
    
    def cleanup_old_files(self, max_age_days: int = 30, 
                         status_filter: Optional[ProcessingStatus] = None) -> int:
        """Clean up old files based on age and status."""
        cleaned_count = 0
        
        try:
            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            
            for file_path in self.config.base_directory.rglob("*"):
                if file_path.is_file():
                    # Check file age
                    if file_path.stat().st_mtime < cutoff_date:
                        # If status filter is provided, check log entry
                        if status_filter:
                            # This would require integration with storage system
                            # For now, we'll skip status-based filtering
                            pass
                        
                        # Move to trash or delete
                        trash_dir = self.config.base_directory / "trash"
                        trash_dir.mkdir(exist_ok=True)
                        
                        trash_path = trash_dir / file_path.name
                        shutil.move(str(file_path), str(trash_path))
                        cleaned_count += 1
                        logger.info(f"Moved old file to trash: {file_path}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleaned_count
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """Get statistics about managed files."""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "files_by_extension": {},
            "files_by_status": {},
            "oldest_file": None,
            "newest_file": None
        }
        
        try:
            for file_path in self.config.base_directory.rglob("*"):
                if file_path.is_file():
                    stats["total_files"] += 1
                    file_size = file_path.stat().st_size
                    stats["total_size_bytes"] += file_size
                    
                    # Count by extension
                    ext = file_path.suffix.lower()
                    stats["files_by_extension"][ext] = stats["files_by_extension"].get(ext, 0) + 1
                    
                    # Track oldest/newest files
                    file_time = file_path.stat().st_mtime
                    if not stats["oldest_file"] or file_time < stats["oldest_file"][1]:
                        stats["oldest_file"] = (str(file_path), file_time)
                    if not stats["newest_file"] or file_time > stats["newest_file"][1]:
                        stats["newest_file"] = (str(file_path), file_time)
            
            # Convert timestamps to readable format
            if stats["oldest_file"]:
                stats["oldest_file"] = (stats["oldest_file"][0], datetime.fromtimestamp(stats["oldest_file"][1]))
            if stats["newest_file"]:
                stats["newest_file"] = (stats["newest_file"][0], datetime.fromtimestamp(stats["newest_file"][1]))
            
        except Exception as e:
            logger.error(f"Error getting file statistics: {e}")
        
        return stats
