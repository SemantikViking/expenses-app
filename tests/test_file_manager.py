"""
Tests for File Management & Naming System.

This module tests file naming, organization, validation, backup,
and cleanup capabilities for the receipt processing workflow.
"""

import tempfile
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal
import pytest

from src.receipt_processor.file_manager import (
    FileOrganizationMode, FileValidationResult, FileValidationReport,
    FileRenameResult, FileOrganizationConfig, FileNameSanitizer,
    FileNamingGenerator, FileValidator, DuplicateHandler,
    FileBackupManager, FileOrganizer, FileManager
)
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)


class TestFileNameSanitizer:
    """Test cases for filename sanitization."""
    
    def test_sanitize_basic_filename(self):
        """Test basic filename sanitization."""
        assert FileNameSanitizer.sanitize_filename("receipt.jpg") == "receipt.jpg"
        assert FileNameSanitizer.sanitize_filename("Receipt 2023.jpg") == "Receipt_2023.jpg"
    
    def test_sanitize_invalid_characters(self):
        """Test sanitization of invalid characters."""
        assert FileNameSanitizer.sanitize_filename("file<name>.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("file:name.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("file/name.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("file\\name.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("file|name.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("file?name.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("file*name.jpg") == "filename.jpg"
    
    def test_sanitize_special_characters(self):
        """Test sanitization of special characters."""
        assert FileNameSanitizer.sanitize_filename("file@name.jpg") == "file_name.jpg"
        assert FileNameSanitizer.sanitize_filename("file#name.jpg") == "file_name.jpg"
        assert FileNameSanitizer.sanitize_filename("file$name.jpg") == "file_name.jpg"
        assert FileNameSanitizer.sanitize_filename("file%name.jpg") == "file_name.jpg"
        assert FileNameSanitizer.sanitize_filename("file&name.jpg") == "file_name.jpg"
    
    def test_sanitize_multiple_underscores(self):
        """Test removal of multiple consecutive underscores."""
        assert FileNameSanitizer.sanitize_filename("file___name.jpg") == "file_name.jpg"
        assert FileNameSanitizer.sanitize_filename("file____name.jpg") == "file_name.jpg"
    
    def test_sanitize_leading_trailing_underscores(self):
        """Test removal of leading and trailing underscores."""
        assert FileNameSanitizer.sanitize_filename("_filename_.jpg") == "filename.jpg"
        assert FileNameSanitizer.sanitize_filename("__filename__.jpg") == "filename.jpg"
    
    def test_sanitize_empty_filename(self):
        """Test handling of empty filename."""
        assert FileNameSanitizer.sanitize_filename("") == "unnamed_file"
        assert FileNameSanitizer.sanitize_filename(None) == "unnamed_file"
    
    def test_sanitize_long_filename(self):
        """Test truncation of long filenames."""
        long_name = "a" * 300
        result = FileNameSanitizer.sanitize_filename(long_name + ".jpg")
        assert len(result) <= 200 + 4  # Max name length + extension
    
    def test_sanitize_extension(self):
        """Test extension sanitization."""
        assert FileNameSanitizer.sanitize_filename("file.JPG") == "file.jpg"
        assert FileNameSanitizer.sanitize_filename("file.PnG") == "file.png"
        assert FileNameSanitizer.sanitize_filename("file<.jpg") == "file.jpg"
    
    def test_validate_filename(self):
        """Test filename validation."""
        # Valid filenames
        is_valid, issues = FileNameSanitizer.validate_filename("receipt.jpg")
        assert is_valid
        assert len(issues) == 0
        
        # Invalid filenames
        is_valid, issues = FileNameSanitizer.validate_filename("receipt<.jpg")
        assert not is_valid
        assert "invalid characters" in issues[0].lower()
        
        is_valid, issues = FileNameSanitizer.validate_filename("")
        assert not is_valid
        assert "empty" in issues[0].lower()


class TestFileNamingGenerator:
    """Test cases for file naming generation."""
    
    def test_generate_filename_with_receipt_data(self):
        """Test filename generation with complete receipt data."""
        receipt_data = ReceiptData(
            vendor_name="Apple Store",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("99.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        filename = FileNamingGenerator.generate_filename(receipt_data, "original.jpg")
        assert filename == "2023-12-25_Apple_Store_009999.jpg"
    
    def test_generate_filename_with_special_characters(self):
        """Test filename generation with special characters in vendor name."""
        receipt_data = ReceiptData(
            vendor_name="McDonald's & Co.",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("15.50"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        filename = FileNamingGenerator.generate_filename(receipt_data, "original.jpg")
        assert "McDonald_s" in filename
        assert "2023-12-25" in filename
        assert "001550" in filename
    
    def test_generate_filename_without_receipt_data(self):
        """Test filename generation without receipt data."""
        filename = FileNamingGenerator.generate_filename(None, "original.jpg")
        assert filename == "original.jpg"
    
    def test_generate_filename_with_incomplete_data(self):
        """Test filename generation with incomplete receipt data."""
        receipt_data = ReceiptData(
            vendor_name="Test Vendor",
            transaction_date=None,
            total_amount=None,
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=False
        )
        
        filename = FileNamingGenerator.generate_filename(receipt_data, "original.jpg")
        assert filename == "original.jpg"  # Should fallback to original
    
    def test_sanitize_vendor_name(self):
        """Test vendor name sanitization."""
        assert FileNamingGenerator._sanitize_vendor_name("Apple Inc.") == "Apple"
        assert FileNamingGenerator._sanitize_vendor_name("McDonald's LLC") == "McDonald_s"
        assert FileNamingGenerator._sanitize_vendor_name("") == "Unknown"
        assert FileNamingGenerator._sanitize_vendor_name(None) == "Unknown"
    
    def test_format_amount(self):
        """Test amount formatting."""
        assert FileNamingGenerator._format_amount(99.99, Currency.USD) == "009999"
        assert FileNamingGenerator._format_amount(0.01, Currency.USD) == "000001"
        assert FileNamingGenerator._format_amount(1234.56, Currency.USD) == "123456"
        assert FileNamingGenerator._format_amount(None, Currency.USD) == "0_00"


class TestFileValidator:
    """Test cases for file validation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return FileOrganizationConfig(
            mode=FileOrganizationMode.FLAT,
            base_directory=Path("/tmp"),
            max_file_size_mb=10,
            allowed_extensions=[".jpg", ".png", ".pdf"]
        )
    
    def test_validate_existing_file(self, temp_dir, config):
        """Test validation of existing file."""
        # Create a test file
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"test content")
        
        config.base_directory = temp_dir
        report = FileValidator.validate_file(test_file, config)
        
        assert report.is_valid
        assert report.result == FileValidationResult.VALID
        assert report.file_size > 0
        assert report.file_hash is not None
    
    def test_validate_nonexistent_file(self, temp_dir, config):
        """Test validation of non-existent file."""
        test_file = temp_dir / "nonexistent.jpg"
        
        report = FileValidator.validate_file(test_file, config)
        
        assert not report.is_valid
        assert report.result == FileValidationResult.INVALID_FORMAT
        assert "does not exist" in report.issues[0]
    
    def test_validate_file_too_large(self, temp_dir, config):
        """Test validation of file that's too large."""
        # Create a large file
        test_file = temp_dir / "large.jpg"
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        test_file.write_bytes(large_content)
        
        config.base_directory = temp_dir
        config.max_file_size_mb = 10
        
        report = FileValidator.validate_file(test_file, config)
        
        assert not report.is_valid
        assert report.result == FileValidationResult.INVALID_SIZE
        assert any("too large" in issue.lower() for issue in report.issues)
    
    def test_validate_invalid_extension(self, temp_dir, config):
        """Test validation of file with invalid extension."""
        test_file = temp_dir / "test.txt"
        test_file.write_bytes(b"test content")
        
        config.base_directory = temp_dir
        config.allowed_extensions = [".jpg", ".png"]
        
        report = FileValidator.validate_file(test_file, config)
        
        assert not report.is_valid
        assert report.result == FileValidationResult.INVALID_FORMAT
        assert any("extension" in issue.lower() for issue in report.issues)


class TestDuplicateHandler:
    """Test cases for duplicate file handling."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_handle_duplicate_increment(self, temp_dir):
        """Test duplicate handling with increment mode."""
        # Create existing file
        existing_file = temp_dir / "test.jpg"
        existing_file.write_bytes(b"existing content")
        
        # Test increment
        new_file = temp_dir / "test.jpg"
        final_path, should_proceed = DuplicateHandler.handle_duplicate(
            new_file, new_file, "increment"
        )
        
        assert should_proceed
        assert final_path.name == "test_001.jpg"
        assert not final_path.exists()
    
    def test_handle_duplicate_skip(self, temp_dir):
        """Test duplicate handling with skip mode."""
        # Create existing file
        existing_file = temp_dir / "test.jpg"
        existing_file.write_bytes(b"existing content")
        
        # Test skip
        new_file = temp_dir / "test.jpg"
        final_path, should_proceed = DuplicateHandler.handle_duplicate(
            new_file, new_file, "skip"
        )
        
        assert not should_proceed
        assert final_path == new_file
    
    def test_handle_duplicate_overwrite(self, temp_dir):
        """Test duplicate handling with overwrite mode."""
        # Create existing file
        existing_file = temp_dir / "test.jpg"
        existing_file.write_bytes(b"existing content")
        
        # Test overwrite
        new_file = temp_dir / "test.jpg"
        final_path, should_proceed = DuplicateHandler.handle_duplicate(
            new_file, new_file, "overwrite"
        )
        
        assert should_proceed
        assert final_path == new_file
    
    def test_increment_filename_multiple(self, temp_dir):
        """Test incrementing filename multiple times."""
        # Create multiple existing files
        for i in range(5):
            file_path = temp_dir / f"test_{i:03d}.jpg"
            file_path.write_bytes(b"content")
        
        # Test increment
        new_file = temp_dir / "test.jpg"
        final_path = DuplicateHandler._increment_filename(new_file)
        
        assert final_path.name == "test_005.jpg"
        assert not final_path.exists()


class TestFileBackupManager:
    """Test cases for file backup management."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_create_backup(self, temp_dir):
        """Test creating a file backup."""
        # Create source file
        source_file = temp_dir / "source.jpg"
        source_file.write_bytes(b"test content")
        
        # Create backup
        backup_dir = temp_dir / "backups"
        backup_path = FileBackupManager.create_backup(source_file, backup_dir)
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_bytes() == source_file.read_bytes()
        assert "source_" in backup_path.name
        assert backup_path.suffix == ".jpg"
    
    def test_restore_from_backup(self, temp_dir):
        """Test restoring from backup."""
        # Create backup file
        backup_file = temp_dir / "backup.jpg"
        backup_file.write_bytes(b"backup content")
        
        # Create target file
        target_file = temp_dir / "target.jpg"
        
        # Restore from backup
        success = FileBackupManager.restore_from_backup(backup_file, target_file)
        
        assert success
        assert target_file.exists()
        assert target_file.read_bytes() == backup_file.read_bytes()


class TestFileOrganizer:
    """Test cases for file organization."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def receipt_data(self):
        """Create sample receipt data."""
        return ReceiptData(
            vendor_name="Test Vendor",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("99.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
    
    @pytest.fixture
    def log_entry(self):
        """Create sample log entry."""
        return ReceiptProcessingLog(
            original_filename="test.jpg",
            file_path=Path("/test/test.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED
        )
    
    def test_organize_by_date(self, temp_dir, receipt_data):
        """Test organizing files by date."""
        config = FileOrganizationConfig(
            mode=FileOrganizationMode.BY_DATE,
            base_directory=temp_dir
        )
        
        file_path = temp_dir / "test.jpg"
        organized_path = FileOrganizer._organize_by_date(file_path, config, receipt_data)
        
        expected_path = temp_dir / "2023" / "12" / "25" / "test.jpg"
        assert organized_path == expected_path
    
    def test_organize_by_vendor(self, temp_dir, receipt_data):
        """Test organizing files by vendor."""
        config = FileOrganizationConfig(
            mode=FileOrganizationMode.BY_VENDOR,
            base_directory=temp_dir
        )
        
        file_path = temp_dir / "test.jpg"
        organized_path = FileOrganizer._organize_by_vendor(file_path, config, receipt_data)
        
        expected_path = temp_dir / "Test_Vendor" / "test.jpg"
        assert organized_path == expected_path
    
    def test_organize_by_status(self, temp_dir, log_entry):
        """Test organizing files by status."""
        config = FileOrganizationConfig(
            mode=FileOrganizationMode.BY_STATUS,
            base_directory=temp_dir
        )
        
        file_path = temp_dir / "test.jpg"
        organized_path = FileOrganizer._organize_by_status(file_path, config, log_entry)
        
        expected_path = temp_dir / "processed" / "test.jpg"
        assert organized_path == expected_path
    
    def test_organize_by_month(self, temp_dir, receipt_data):
        """Test organizing files by month."""
        config = FileOrganizationConfig(
            mode=FileOrganizationMode.BY_MONTH,
            base_directory=temp_dir
        )
        
        file_path = temp_dir / "test.jpg"
        organized_path = FileOrganizer._organize_by_month(file_path, config, receipt_data)
        
        expected_path = temp_dir / "2023" / "12" / "test.jpg"
        assert organized_path == expected_path


class TestFileManager:
    """Test cases for the main file manager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config(self, temp_dir):
        """Create a test configuration."""
        return FileOrganizationConfig(
            mode=FileOrganizationMode.FLAT,
            base_directory=temp_dir,
            create_backups=True,
            max_file_size_mb=10,
            allowed_extensions=[".jpg", ".png", ".pdf"]
        )
    
    @pytest.fixture
    def file_manager(self, config):
        """Create a file manager instance."""
        return FileManager(config)
    
    @pytest.fixture
    def receipt_data(self):
        """Create sample receipt data."""
        return ReceiptData(
            vendor_name="Test Vendor",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("99.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
    
    def test_process_file_success(self, file_manager, temp_dir, receipt_data):
        """Test successful file processing."""
        # Create test file
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"test content")
        
        # Process file
        result = file_manager.process_file(test_file, receipt_data)
        
        assert result.success
        assert result.new_path is not None
        assert result.new_path.name == "2023-12-25_Test_Vendor_009999.jpg"
        assert result.backup_path is not None
        assert result.rollback_data is not None
    
    def test_process_file_validation_failure(self, file_manager, temp_dir):
        """Test file processing with validation failure."""
        # Create file with invalid extension
        test_file = temp_dir / "test.txt"
        test_file.write_bytes(b"test content")
        
        # Process file
        result = file_manager.process_file(test_file)
        
        assert not result.success
        assert "validation failed" in result.error_message.lower()
    
    def test_process_file_duplicate_handling(self, file_manager, temp_dir, receipt_data):
        """Test file processing with duplicate handling."""
        # Create first file
        test_file1 = temp_dir / "test.jpg"
        test_file1.write_bytes(b"test content 1")
        
        # Process first file
        result1 = file_manager.process_file(test_file1, receipt_data)
        assert result1.success
        
        # Create second file with same name
        test_file2 = temp_dir / "test2.jpg"
        test_file2.write_bytes(b"test content 2")
        
        # Process second file (should increment)
        result2 = file_manager.process_file(test_file2, receipt_data)
        assert result2.success
        assert "001" in result2.new_path.name
    
    def test_rollback_file(self, file_manager, temp_dir, receipt_data):
        """Test file rollback functionality."""
        # Create test file
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"test content")
        
        # Process file
        result = file_manager.process_file(test_file, receipt_data)
        assert result.success
        
        # Rollback
        rollback_success = file_manager.rollback_file(result.rollback_data)
        assert rollback_success
    
    def test_cleanup_old_files(self, file_manager, temp_dir):
        """Test cleanup of old files."""
        # Create old file
        old_file = temp_dir / "old.jpg"
        old_file.write_bytes(b"old content")
        
        # Make file old by setting modification time
        old_time = datetime.now().timestamp() - (31 * 24 * 60 * 60)  # 31 days ago
        os.utime(old_file, (old_time, old_time))
        
        # Cleanup
        cleaned_count = file_manager.cleanup_old_files(max_age_days=30)
        
        assert cleaned_count >= 1  # At least one file should be cleaned
        assert not old_file.exists()
        assert (temp_dir / "trash" / "old.jpg").exists()
    
    def test_get_file_statistics(self, file_manager, temp_dir):
        """Test getting file statistics."""
        # Create some test files
        for i in range(3):
            test_file = temp_dir / f"test{i}.jpg"
            test_file.write_bytes(b"test content")
        
        # Get statistics
        stats = file_manager.get_file_statistics()
        
        assert stats["total_files"] == 3
        assert stats["total_size_bytes"] > 0
        assert ".jpg" in stats["files_by_extension"]
        assert stats["oldest_file"] is not None
        assert stats["newest_file"] is not None


class TestIntegration:
    """Integration tests for file management system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_complete_file_processing_workflow(self, temp_dir):
        """Test complete file processing workflow."""
        # Create configuration
        config = FileOrganizationConfig(
            mode=FileOrganizationMode.BY_VENDOR,
            base_directory=temp_dir,
            create_backups=True,
            max_file_size_mb=10,
            allowed_extensions=[".jpg", ".png", ".pdf"]
        )
        
        # Create file manager
        file_manager = FileManager(config)
        
        # Create receipt data
        receipt_data = ReceiptData(
            vendor_name="Apple Store Inc.",
            transaction_date=datetime(2023, 12, 25),
            total_amount=Decimal("299.99"),
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        
        # Create test file
        test_file = temp_dir / "receipt.jpg"
        test_file.write_bytes(b"receipt image content")
        
        # Process file
        result = file_manager.process_file(test_file, receipt_data)
        
        # Verify results
        assert result.success
        assert result.new_path is not None
        assert "Apple_Store" in result.new_path.name
        assert "2023-12-25" in result.new_path.name
        assert "029999" in result.new_path.name
        assert result.backup_path is not None
        assert result.rollback_data is not None
        
        # Verify file organization
        assert result.new_path.parent.name == "Apple_Store_Inc."
        
        # Test rollback
        rollback_success = file_manager.rollback_file(result.rollback_data)
        assert rollback_success
