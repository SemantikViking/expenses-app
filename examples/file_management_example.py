#!/usr/bin/env python3
"""
Example usage of the File Management & Naming System.

This script demonstrates comprehensive file management capabilities including
standardized naming, organization, backup, validation, and cleanup utilities.
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Import the file management system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.receipt_processor.file_manager import (
    FileOrganizationMode, FileValidationResult, FileValidationReport,
    FileRenameResult, FileOrganizationConfig, FileNameSanitizer,
    FileNamingGenerator, FileValidator, DuplicateHandler,
    FileBackupManager, FileOrganizer, FileManager
)
from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)


def main():
    """Demonstrate the file management and naming functionality."""
    print("📁 File Management & Naming System Demo")
    print("=" * 60)
    
    # Create a temporary directory for this demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"📁 Using temporary directory: {temp_path}")
        print()
        
        # Demonstrate filename sanitization
        print("🧹 Demonstrating filename sanitization...")
        demonstrate_filename_sanitization()
        print()
        
        # Demonstrate file naming generation
        print("📝 Demonstrating file naming generation...")
        demonstrate_file_naming()
        print()
        
        # Demonstrate file validation
        print("✅ Demonstrating file validation...")
        demonstrate_file_validation(temp_path)
        print()
        
        # Demonstrate duplicate handling
        print("🔄 Demonstrating duplicate handling...")
        demonstrate_duplicate_handling(temp_path)
        print()
        
        # Demonstrate file backup
        print("💾 Demonstrating file backup...")
        demonstrate_file_backup(temp_path)
        print()
        
        # Demonstrate file organization
        print("📂 Demonstrating file organization...")
        demonstrate_file_organization(temp_path)
        print()
        
        # Demonstrate complete file management workflow
        print("🔄 Demonstrating complete file management workflow...")
        demonstrate_complete_workflow(temp_path)
        print()
        
        print("🎉 File management and naming demo completed successfully!")
        print(f"📁 Final directory: {temp_path}")


def demonstrate_filename_sanitization():
    """Demonstrate filename sanitization capabilities."""
    test_filenames = [
        "receipt.jpg",
        "Receipt 2023.jpg",
        "file<name>.jpg",
        "file:name.jpg",
        "file/name.jpg",
        "file\\name.jpg",
        "file|name.jpg",
        "file?name.jpg",
        "file*name.jpg",
        "file@name.jpg",
        "file#name.jpg",
        "file$name.jpg",
        "file%name.jpg",
        "file&name.jpg",
        "file___name.jpg",
        "_filename_.jpg",
        "",
        "a" * 300 + ".jpg"
    ]
    
    print("  📝 Original filenames and sanitized versions:")
    for filename in test_filenames:
        sanitized = FileNameSanitizer.sanitize_filename(filename)
        is_valid, issues = FileNameSanitizer.validate_filename(sanitized)
        status = "✅" if is_valid else "❌"
        print(f"    {status} '{filename}' → '{sanitized}'")
        if issues:
            print(f"      Issues: {', '.join(issues)}")


def demonstrate_file_naming():
    """Demonstrate file naming generation."""
    # Create sample receipt data
    receipt_data = ReceiptData(
        vendor_name="Apple Store Inc.",
        transaction_date=datetime(2023, 12, 25),
        total_amount=Decimal("299.99"),
        currency=Currency.USD,
        extraction_confidence=0.95,
        has_required_data=True
    )
    
    # Generate filename
    filename = FileNamingGenerator.generate_filename(receipt_data, "original.jpg")
    print(f"  📝 Generated filename: {filename}")
    
    # Test with different vendors and amounts
    test_cases = [
        ("McDonald's LLC", Decimal("15.50"), "receipt.jpg"),
        ("Amazon.com", Decimal("89.99"), "order.pdf"),
        ("Starbucks Coffee", Decimal("4.75"), "purchase.png"),
        ("Target Corporation", Decimal("156.78"), "shopping.jpg")
    ]
    
    print("  📝 Test cases with different vendors and amounts:")
    for vendor, amount, original in test_cases:
        test_receipt = ReceiptData(
            vendor_name=vendor,
            transaction_date=datetime(2023, 12, 25),
            total_amount=amount,
            currency=Currency.USD,
            extraction_confidence=0.95,
            has_required_data=True
        )
        filename = FileNamingGenerator.generate_filename(test_receipt, original)
        print(f"    {vendor} (${amount}) → {filename}")


def demonstrate_file_validation(temp_path):
    """Demonstrate file validation capabilities."""
    # Create test files
    valid_file = temp_path / "valid.jpg"
    valid_file.write_bytes(b"valid image content")
    
    large_file = temp_path / "large.jpg"
    large_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11MB
    
    invalid_ext_file = temp_path / "invalid.txt"
    invalid_ext_file.write_bytes(b"text content")
    
    # Create configuration
    config = FileOrganizationConfig(
        mode=FileOrganizationMode.FLAT,
        base_directory=temp_path,
        max_file_size_mb=10,
        allowed_extensions=[".jpg", ".png", ".pdf"]
    )
    
    # Test validation
    test_files = [
        (valid_file, "Valid file"),
        (large_file, "Large file"),
        (invalid_ext_file, "Invalid extension"),
        (temp_path / "nonexistent.jpg", "Non-existent file")
    ]
    
    print("  ✅ File validation results:")
    for file_path, description in test_files:
        report = FileValidator.validate_file(file_path, config)
        status = "✅" if report.is_valid else "❌"
        print(f"    {status} {description}: {report.result.value}")
        if report.issues:
            print(f"      Issues: {', '.join(report.issues)}")
        if report.suggested_fixes:
            print(f"      Suggestions: {', '.join(report.suggested_fixes)}")


def demonstrate_duplicate_handling(temp_path):
    """Demonstrate duplicate file handling."""
    # Create existing file
    existing_file = temp_path / "test.jpg"
    existing_file.write_bytes(b"existing content")
    
    print("  🔄 Duplicate handling modes:")
    
    # Test increment mode
    new_file = temp_path / "test.jpg"
    final_path, should_proceed = DuplicateHandler.handle_duplicate(
        new_file, new_file, "increment"
    )
    print(f"    Increment mode: {new_file} → {final_path} (proceed: {should_proceed})")
    
    # Test skip mode
    final_path, should_proceed = DuplicateHandler.handle_duplicate(
        new_file, new_file, "skip"
    )
    print(f"    Skip mode: {new_file} → {final_path} (proceed: {should_proceed})")
    
    # Test overwrite mode
    final_path, should_proceed = DuplicateHandler.handle_duplicate(
        new_file, new_file, "overwrite"
    )
    print(f"    Overwrite mode: {new_file} → {final_path} (proceed: {should_proceed})")


def demonstrate_file_backup(temp_path):
    """Demonstrate file backup capabilities."""
    # Create source file
    source_file = temp_path / "source.jpg"
    source_file.write_bytes(b"important content")
    
    # Create backup
    backup_dir = temp_path / "backups"
    backup_path = FileBackupManager.create_backup(source_file, backup_dir)
    
    if backup_path:
        print(f"  💾 Created backup: {backup_path}")
        print(f"    Source: {source_file}")
        print(f"    Backup size: {backup_path.stat().st_size} bytes")
        
        # Test restore
        target_file = temp_path / "restored.jpg"
        success = FileBackupManager.restore_from_backup(backup_path, target_file)
        print(f"  🔄 Restore test: {'✅ Success' if success else '❌ Failed'}")
    else:
        print("  ❌ Failed to create backup")


def demonstrate_file_organization(temp_path):
    """Demonstrate file organization capabilities."""
    # Create test file
    test_file = temp_path / "test.jpg"
    test_file.write_bytes(b"test content")
    
    # Create receipt data
    receipt_data = ReceiptData(
        vendor_name="Test Vendor",
        transaction_date=datetime(2023, 12, 25),
        total_amount=Decimal("99.99"),
        currency=Currency.USD,
        extraction_confidence=0.95,
        has_required_data=True
    )
    
    # Create log entry
    log_entry = ReceiptProcessingLog(
        original_filename="test.jpg",
        file_path=test_file,
        file_size=1024,
        current_status=ProcessingStatus.PROCESSED
    )
    
    # Test different organization modes
    config = FileOrganizationConfig(
        mode=FileOrganizationMode.FLAT,
        base_directory=temp_path
    )
    
    print("  📂 File organization modes:")
    
    # By date
    config.mode = FileOrganizationMode.BY_DATE
    organized_path = FileOrganizer.organize_file(test_file, config, receipt_data)
    print(f"    By date: {test_file} → {organized_path}")
    
    # By vendor
    config.mode = FileOrganizationMode.BY_VENDOR
    organized_path = FileOrganizer.organize_file(test_file, config, receipt_data)
    print(f"    By vendor: {test_file} → {organized_path}")
    
    # By status
    config.mode = FileOrganizationMode.BY_STATUS
    organized_path = FileOrganizer.organize_file(test_file, config, log_entry=log_entry)
    print(f"    By status: {test_file} → {organized_path}")
    
    # By month
    config.mode = FileOrganizationMode.BY_MONTH
    organized_path = FileOrganizer.organize_file(test_file, config, receipt_data)
    print(f"    By month: {test_file} → {organized_path}")


def demonstrate_complete_workflow(temp_path):
    """Demonstrate complete file management workflow."""
    # Create configuration
    config = FileOrganizationConfig(
        mode=FileOrganizationMode.BY_VENDOR,
        base_directory=temp_path,
        create_backups=True,
        max_file_size_mb=10,
        allowed_extensions=[".jpg", ".png", ".pdf"],
        duplicate_handling="increment"
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
    test_file = temp_path / "receipt.jpg"
    test_file.write_bytes(b"receipt image content")
    
    print(f"  🔄 Processing file: {test_file}")
    
    # Process file
    result = file_manager.process_file(test_file, receipt_data)
    
    if result.success:
        print(f"    ✅ Success!")
        print(f"    📁 New path: {result.new_path}")
        print(f"    💾 Backup: {result.backup_path}")
        print(f"    📊 File organized by vendor: {result.new_path.parent.name}")
        print(f"    📝 Standardized name: {result.new_path.name}")
        
        # Test rollback
        print("  🔄 Testing rollback...")
        rollback_success = file_manager.rollback_file(result.rollback_data)
        print(f"    Rollback: {'✅ Success' if rollback_success else '❌ Failed'}")
        
        # Get file statistics
        print("  📊 File statistics:")
        stats = file_manager.get_file_statistics()
        print(f"    Total files: {stats['total_files']}")
        print(f"    Total size: {stats['total_size_bytes']} bytes")
        print(f"    Files by extension: {stats['files_by_extension']}")
        
    else:
        print(f"    ❌ Failed: {result.error_message}")


if __name__ == "__main__":
    main()
