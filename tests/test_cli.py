"""
Test suite for the Receipt Processor CLI.

This module tests all CLI commands and functionality.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from receipt_processor import cli
from src.receipt_processor.models import ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
from src.receipt_processor.storage import JSONStorageManager

class TestCLI:
    """Test cases for CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_log.json"
        self.payment_log_file = Path(self.temp_dir) / "test_payment_log.json"
        self.backup_dir = Path(self.temp_dir) / "backups"
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Receipt Processor" in result.output
        assert "start" in result.output
        assert "process" in result.output
        assert "status" in result.output
    
    def test_cli_verbose_quiet(self):
        """Test verbose and quiet modes."""
        # Test verbose mode
        result = self.runner.invoke(cli, ['--verbose', '--log-file', str(self.log_file), 'stats'])
        assert result.exit_code == 0
        assert "[VERBOSE]" in result.output
        
        # Test quiet mode
        result = self.runner.invoke(cli, ['--quiet', '--log-file', str(self.log_file), 'stats'])
        assert result.exit_code == 0
        assert "Generating processing statistics" not in result.output
    
    def test_start_command(self):
        """Test start command."""
        watch_dir = Path(self.temp_dir) / "watch"
        watch_dir.mkdir()
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'start', '--watch-dir', str(watch_dir)
        ])
        
        assert result.exit_code == 0
        assert "Starting receipt processor" in result.output
        assert "Watching directory" in result.output
        assert "File monitoring not yet implemented" in result.output
    
    def test_process_command(self):
        """Test process command."""
        input_dir = Path(self.temp_dir) / "input"
        input_dir.mkdir()
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'process', '--input-dir', str(input_dir)
        ])
        
        assert result.exit_code == 0
        assert "Processing receipts in" in result.output
        assert "Batch processing not yet implemented" in result.output
    
    def test_status_command_no_logs(self):
        """Test status command with no logs."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'status'
        ])
        
        assert result.exit_code == 0
        assert "No logs found" in result.output
    
    def test_status_command_with_logs(self):
        """Test status command with existing logs."""
        # Create a test log entry
        storage_manager = JSONStorageManager(
            log_file_path=self.log_file,
            backup_dir=self.backup_dir
        )
        
        test_log = ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=ReceiptData(
                vendor_name="Test Vendor",
                transaction_date=datetime.now(),
                total_amount=Decimal("25.50"),
                currency=Currency.USD
            )
        )
        
        storage_manager.add_log_entry(test_log)
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'status'
        ])
        
        assert result.exit_code == 0
        assert "Recent Processing Logs" in result.output
        assert "test_receipt.jpg" in result.output
        assert "Test Vendor" in result.output
    
    def test_status_command_specific_log(self):
        """Test status command with specific log ID."""
        # Create a test log entry
        storage_manager = JSONStorageManager(
            log_file_path=self.log_file,
            backup_dir=self.backup_dir
        )
        
        test_log = ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED,
            receipt_data=ReceiptData(
                vendor_name="Test Vendor",
                transaction_date=datetime.now(),
                total_amount=Decimal("25.50"),
                currency=Currency.USD
            )
        )
        
        storage_manager.add_log_entry(test_log)
        log_id = str(test_log.id)
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'status', '--log-id', log_id
        ])
        
        assert result.exit_code == 0
        assert f"Receipt Processing Log: {log_id}" in result.output
        assert "test_receipt.jpg" in result.output
        assert "Test Vendor" in result.output
    
    def test_logs_command(self):
        """Test logs command."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'logs'
        ])
        
        assert result.exit_code == 0
        assert "No logs found matching criteria" in result.output
    
    def test_logs_command_with_filters(self):
        """Test logs command with filters."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'logs', '--status', 'processed', '--limit', '5'
        ])
        
        assert result.exit_code == 0
        assert "No logs found matching criteria" in result.output
    
    def test_config_command(self):
        """Test config command."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'config', '--show'
        ])
        
        assert result.exit_code == 0
        assert "Config display not yet implemented" in result.output
    
    def test_report_command(self):
        """Test report command."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'report', '--type', 'summary'
        ])
        
        assert result.exit_code == 0
        assert "Generating summary report" in result.output
        assert "Summary report generated successfully" in result.output
    
    def test_export_command(self):
        """Test export command."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'export', '--format', 'json'
        ])
        
        assert result.exit_code == 0
        assert "Exporting logs in json format" in result.output
        assert "Export completed" in result.output
    
    def test_stats_command(self):
        """Test stats command."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'stats'
        ])
        
        assert result.exit_code == 0
        assert "Generating processing statistics" in result.output
        assert "Processing Statistics" in result.output
        assert "Statistics generated successfully" in result.output
    
    def test_update_status_command(self):
        """Test update-status command."""
        # Create a test log entry
        storage_manager = JSONStorageManager(
            log_file_path=self.log_file,
            backup_dir=self.backup_dir
        )
        
        test_log = ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PENDING
        )
        
        storage_manager.add_log_entry(test_log)
        log_id = str(test_log.id)
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'update-status', log_id, 'processed', '--reason', 'Test update'
        ])
        
        assert result.exit_code == 0
        assert f"Updating status for log {log_id}" in result.output
        assert "Status updated: pending → processed" in result.output
    
    def test_email_command(self):
        """Test email command."""
        # Create a test log entry
        storage_manager = JSONStorageManager(
            log_file_path=self.log_file,
            backup_dir=self.backup_dir
        )
        
        test_log = ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED
        )
        
        storage_manager.add_log_entry(test_log)
        log_id = str(test_log.id)
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'email', log_id
        ])
        
        assert result.exit_code == 0
        assert f"Sending email for log {log_id}" in result.output
        assert "Email sending not yet implemented" in result.output
    
    def test_submit_command(self):
        """Test submit command."""
        # Create a test log entry
        storage_manager = JSONStorageManager(
            log_file_path=self.log_file,
            backup_dir=self.backup_dir
        )
        
        test_log = ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.PROCESSED
        )
        
        storage_manager.add_log_entry(test_log)
        log_id = str(test_log.id)
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'submit', log_id, '--amount', '25.50', '--method', 'bank_transfer'
        ])
        
        assert result.exit_code == 0
        assert f"Submitting log {log_id} for payment processing" in result.output
        assert "Payment submission not yet implemented" in result.output
    
    def test_payment_received_command(self):
        """Test payment-received command."""
        # Create a test log entry
        storage_manager = JSONStorageManager(
            log_file_path=self.log_file,
            backup_dir=self.backup_dir
        )
        
        test_log = ReceiptProcessingLog(
            original_filename="test_receipt.jpg",
            file_path=Path("test_receipt.jpg"),
            file_size=1024,
            current_status=ProcessingStatus.SUBMITTED
        )
        
        storage_manager.add_log_entry(test_log)
        log_id = str(test_log.id)
        
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'payment-received', log_id, '--amount', '25.50', '--method', 'bank_transfer'
        ])
        
        assert result.exit_code == 0
        assert f"Marking payment as received for log {log_id}" in result.output
        assert "Payment marked as received: 25.5 via bank_transfer" in result.output
    
    def test_invalid_log_id(self):
        """Test commands with invalid log ID."""
        result = self.runner.invoke(cli, [
            '--log-file', str(self.log_file),
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'status', '--log-id', 'invalid-id'
        ])
        
        assert result.exit_code == 0
        assert "Log with ID invalid-id not found" in result.output
    
    def test_error_handling(self):
        """Test error handling in CLI."""
        # Test with invalid log file path
        result = self.runner.invoke(cli, [
            '--log-file', '/invalid/path/log.json',
            '--payment-log-file', str(self.payment_log_file),
            '--backup-dir', str(self.backup_dir),
            'stats'
        ])
        
        # Should still work as it creates the file
        assert result.exit_code == 0

if __name__ == '__main__':
    pytest.main([__file__])
