"""
End-to-End Tests for Receipt Processing

This module contains comprehensive end-to-end tests that verify the complete
receipt processing workflow from image input to final output.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner

from src.receipt_processor.cli import cli
from src.receipt_processor.models import ProcessingStatus, ProcessingLog
from src.receipt_processor.payment_models import PaymentStatus, PaymentType, PaymentMethod
from src.receipt_processor.error_handling import ErrorSeverity, ErrorCategory

class TestEndToEndProcessing:
    """End-to-end tests for receipt processing workflow."""
    
    @patch('src.receipt_processor.cli.AIVisionService')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_complete_receipt_processing_workflow(self, mock_storage, mock_file, mock_ai):
        """Test complete receipt processing workflow from image to final output."""
        # Setup mocks
        mock_ai.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [
                {"name": "Burger", "price": 15.99, "quantity": 1},
                {"name": "Fries", "price": 4.99, "quantity": 1},
                {"name": "Drink", "price": 2.99, "quantity": 1}
            ],
            "tax_amount": 1.53,
            "tip_amount": 0.00,
            "payment_method": "Credit Card",
            "receipt_number": "R123456",
            "confidence_score": 0.95
        }
        
        mock_file.return_value.rename_file.return_value = True
        mock_file.return_value.create_backup.return_value = True
        mock_storage.return_value.save_log.return_value = True
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image file
            test_image = Path(temp_dir) / "receipt.jpg"
            test_image.write_bytes(b"fake image data")
            
            # Step 1: Process the image
            result = runner.invoke(cli, ['process', str(temp_dir)])
            assert result.exit_code == 0
            assert "Processing completed" in result.output or "Processed" in result.output
            
            # Step 2: Check status
            result = runner.invoke(cli, ['status'])
            assert result.exit_code == 0
            
            # Step 3: Generate summary report
            result = runner.invoke(cli, ['report', '--type', 'summary'])
            assert result.exit_code == 0
            
            # Step 4: Check logs
            result = runner.invoke(cli, ['logs', '--format', 'json'])
            assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.AIVisionService')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_processing_with_error_recovery(self, mock_storage, mock_file, mock_ai):
        """Test processing workflow with error recovery."""
        # Setup mocks to simulate error and recovery
        call_count = 0
        def mock_extract_data(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("AI service temporarily unavailable")
            else:
                return {
                    "vendor_name": "Test Restaurant",
                    "date": "2024-01-15",
                    "total_amount": 25.50,
                    "currency": "USD",
                    "items": [],
                    "confidence_score": 0.90
                }
        
        mock_ai.return_value.extract_receipt_data.side_effect = mock_extract_data
        mock_file.return_value.rename_file.return_value = True
        mock_storage.return_value.save_log.return_value = True
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image file
            test_image = Path(temp_dir) / "receipt.jpg"
            test_image.write_bytes(b"fake image data")
            
            # Process with retry
            result = runner.invoke(cli, ['process', str(temp_dir)])
            # Should succeed after retry
            assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.AIVisionService')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_batch_processing_workflow(self, mock_storage, mock_file, mock_ai):
        """Test batch processing of multiple images."""
        # Setup mocks
        mock_ai.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [],
            "confidence_score": 0.95
        }
        
        mock_file.return_value.rename_file.return_value = True
        mock_storage.return_value.save_log.return_value = True
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test image files
            for i in range(5):
                test_image = Path(temp_dir) / f"receipt_{i}.jpg"
                test_image.write_bytes(b"fake image data")
            
            # Process all images
            result = runner.invoke(cli, ['process', str(temp_dir), '--batch-size', '3'])
            assert result.exit_code == 0
            
            # Check that all files were processed
            result = runner.invoke(cli, ['status'])
            assert result.exit_code == 0

class TestEndToEndPaymentWorkflow:
    """End-to-end tests for payment processing workflow."""
    
    @patch('src.receipt_processor.cli.PaymentWorkflowEngine')
    @patch('src.receipt_processor.cli.PaymentStorageManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_complete_payment_workflow(self, mock_storage, mock_payment_storage, mock_payment_workflow):
        """Test complete payment processing workflow."""
        # Setup mocks
        mock_storage.return_value.load_logs.return_value = [
            ProcessingLog(
                log_id="LOG_001",
                file_path="/test/receipt.jpg",
                original_filename="receipt.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                confidence_score=0.95
            )
        ]
        
        mock_payment_workflow.return_value.submit_payment.return_value = {
            "payment_id": "PAY_001",
            "status": "submitted"
        }
        
        mock_payment_storage.return_value.save_payment.return_value = True
        mock_payment_storage.return_value.load_payments.return_value = []
        
        runner = CliRunner()
        
        # Step 1: Submit payment
        result = runner.invoke(cli, ['submit', 'LOG_001'])
        assert result.exit_code == 0
        
        # Step 2: Check payment status
        result = runner.invoke(cli, ['payment-status', 'PAY_001'])
        assert result.exit_code == 0
        
        # Step 3: Mark payment as received
        result = runner.invoke(cli, ['payment-received', 'PAY_001'])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.PaymentWorkflowEngine')
    @patch('src.receipt_processor.cli.PaymentStorageManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_bulk_payment_processing(self, mock_storage, mock_payment_storage, mock_payment_workflow):
        """Test bulk payment processing workflow."""
        # Setup mocks
        mock_logs = [
            ProcessingLog(
                log_id=f"LOG_{i:03d}",
                file_path=f"/test/receipt_{i}.jpg",
                original_filename=f"receipt_{i}.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name=f"Restaurant {i}",
                date=datetime(2024, 1, 15),
                total_amount=25.50 + i,
                currency="USD",
                confidence_score=0.95
            )
            for i in range(10)
        ]
        
        mock_storage.return_value.load_logs.return_value = mock_logs
        mock_payment_workflow.return_value.submit_bulk_payments.return_value = {
            "success": 8,
            "failed": 2,
            "errors": ["LOG_003: Invalid data", "LOG_007: Duplicate payment"]
        }
        
        mock_payment_storage.return_value.save_payment.return_value = True
        mock_payment_storage.return_value.load_payments.return_value = []
        
        runner = CliRunner()
        
        # Process bulk payments
        result = runner.invoke(cli, ['bulk-submit', '--batch-size', '5'], input='y\n')
        assert result.exit_code == 0
        assert "Success: 8" in result.output
        assert "Failed: 2" in result.output

class TestEndToEndEmailWorkflow:
    """End-to-end tests for email workflow."""
    
    @patch('src.receipt_processor.cli.EmailWorkflowIntegrator')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_complete_email_workflow(self, mock_storage, mock_email):
        """Test complete email workflow."""
        # Setup mocks
        mock_storage.return_value.load_logs.return_value = [
            ProcessingLog(
                log_id="LOG_001",
                file_path="/test/receipt.jpg",
                original_filename="receipt.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                confidence_score=0.95
            )
        ]
        
        mock_email.return_value.send_email.return_value = {
            "message_id": "MSG_001",
            "status": "sent"
        }
        
        runner = CliRunner()
        
        # Step 1: Send email
        result = runner.invoke(cli, ['email', 'LOG_001'])
        assert result.exit_code == 0
        
        # Step 2: Send bulk emails
        result = runner.invoke(cli, ['bulk-email', '--batch-size', '5'], input='y\n')
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.EmailWorkflowIntegrator')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_email_with_attachments(self, mock_storage, mock_email):
        """Test email workflow with attachments."""
        # Setup mocks
        mock_storage.return_value.load_logs.return_value = [
            ProcessingLog(
                log_id="LOG_001",
                file_path="/test/receipt.jpg",
                original_filename="receipt.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                confidence_score=0.95
            )
        ]
        
        mock_email.return_value.send_email.return_value = {
            "message_id": "MSG_001",
            "status": "sent"
        }
        
        runner = CliRunner()
        
        # Send email with attachment
        result = runner.invoke(cli, ['email', 'LOG_001', '--include-attachment'])
        assert result.exit_code == 0

class TestEndToEndMonitoringWorkflow:
    """End-to-end tests for monitoring workflow."""
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_complete_monitoring_workflow(self, mock_monitor):
        """Test complete monitoring workflow."""
        # Setup mocks
        mock_status = {
            "overall_health": "healthy",
            "timestamp": "2024-01-15T10:00:00Z",
            "health_checks": [
                {
                    "name": "cpu_check",
                    "status": "healthy",
                    "message": "CPU usage OK",
                    "response_time_ms": 50.0
                },
                {
                    "name": "memory_check",
                    "status": "healthy",
                    "message": "Memory usage OK",
                    "response_time_ms": 30.0
                }
            ],
            "resource_metrics": {
                "cpu_percent": 45.0,
                "memory_percent": 60.0,
                "memory_used_mb": 2048.0,
                "disk_usage_percent": 25.0,
                "disk_free_gb": 75.0
            },
            "performance_metrics": {
                "requests_per_second": 10.0,
                "average_response_time": 0.5,
                "error_rate": 2.0
            },
            "active_alerts": 0,
            "alerts": []
        }
        
        mock_monitor.return_value.get_system_status.return_value = mock_status
        mock_monitor.return_value.resource_monitor.get_metrics_history.return_value = []
        mock_monitor.return_value.performance_monitor.get_metrics_history.return_value = []
        mock_monitor.return_value.alert_manager.alerts = []
        
        runner = CliRunner()
        
        # Step 1: Check system health
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert "Overall Health: HEALTHY" in result.output
        
        # Step 2: Check metrics
        result = runner.invoke(cli, ['metrics', '--duration', '60'])
        assert result.exit_code == 0
        
        # Step 3: Check alerts
        result = runner.invoke(cli, ['alerts'])
        assert result.exit_code == 0
        
        # Step 4: Check error log
        result = runner.invoke(cli, ['error-log'])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_monitoring_with_alerts(self, mock_monitor):
        """Test monitoring workflow with alerts."""
        from src.receipt_processor.system_monitoring import Alert, AlertLevel
        
        # Setup mocks with alerts
        mock_status = {
            "overall_health": "warning",
            "timestamp": "2024-01-15T10:00:00Z",
            "health_checks": [
                {
                    "name": "cpu_check",
                    "status": "warning",
                    "message": "High CPU usage",
                    "response_time_ms": 50.0
                }
            ],
            "resource_metrics": {
                "cpu_percent": 85.0,
                "memory_percent": 60.0,
                "memory_used_mb": 2048.0,
                "disk_usage_percent": 25.0,
                "disk_free_gb": 75.0
            },
            "performance_metrics": {
                "requests_per_second": 10.0,
                "average_response_time": 0.5,
                "error_rate": 2.0
            },
            "active_alerts": 1,
            "alerts": [
                {
                    "alert_id": "ALERT_001",
                    "level": "warning",
                    "title": "High CPU Usage",
                    "message": "CPU usage is 85%",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
        
        mock_alerts = [
            Alert(
                alert_id="ALERT_001",
                level=AlertLevel.WARNING,
                title="High CPU Usage",
                message="CPU usage is 85%"
            )
        ]
        
        mock_monitor.return_value.get_system_status.return_value = mock_status
        mock_monitor.return_value.alert_manager.alerts = mock_alerts
        mock_monitor.return_value.alert_manager.get_active_alerts.return_value = mock_alerts
        mock_monitor.return_value.alert_manager.resolve_alert.return_value = None
        
        runner = CliRunner()
        
        # Check health with alerts
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert "Overall Health: WARNING" in result.output
        assert "High CPU Usage" in result.output
        
        # Check alerts
        result = runner.invoke(cli, ['alerts'])
        assert result.exit_code == 0
        assert "High CPU Usage" in result.output
        
        # Resolve alerts
        result = runner.invoke(cli, ['resolve-alerts', '--all'])
        assert result.exit_code == 0
        assert "Resolved 1 alerts" in result.output

class TestEndToEndErrorHandling:
    """End-to-end tests for error handling workflow."""
    
    @patch('src.receipt_processor.cli.ErrorHandler')
    def test_error_handling_workflow(self, mock_error_handler):
        """Test error handling workflow."""
        # Setup mocks
        mock_summary = {
            "total_errors": 5,
            "by_severity": {"high": 1, "medium": 3, "low": 1},
            "by_category": {"validation_error": 2, "processing_error": 2, "network_error": 1},
            "resolved_errors": 3,
            "unresolved_errors": 2
        }
        
        mock_error_handler.return_value.get_error_summary.return_value = mock_summary
        
        runner = CliRunner()
        
        # Check error log
        result = runner.invoke(cli, ['error-log'])
        assert result.exit_code == 0
        assert "Total Errors: 5" in result.output
        assert "Resolved: 3" in result.output
        assert "Unresolved: 2" in result.output
        
        # Check error log with filters
        result = runner.invoke(cli, [
            'error-log',
            '--category', 'validation_error',
            '--severity', 'high'
        ])
        assert result.exit_code == 0

class TestEndToEndConcurrentProcessing:
    """End-to-end tests for concurrent processing workflow."""
    
    @patch('src.receipt_processor.cli.ConcurrentProcessor')
    def test_concurrent_processing_workflow(self, mock_processor):
        """Test concurrent processing workflow."""
        # Setup mocks
        mock_processor.return_value.start.return_value = None
        mock_processor.return_value.stop.return_value = None
        mock_processor.return_value.submit_job.return_value = True
        mock_processor.return_value.priority_queue.size.return_value = 0
        mock_processor.return_value.active_jobs = []
        mock_processor.return_value.get_metrics.return_value = Mock(
            total_jobs=10,
            completed_jobs=10,
            failed_jobs=0,
            average_processing_time=2.5
        )
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test image files
            for i in range(10):
                test_image = Path(temp_dir) / f"receipt_{i}.jpg"
                test_image.write_bytes(b"fake image data")
            
            # Process concurrently
            result = runner.invoke(cli, [
                'process-concurrent',
                '--input-dir', temp_dir,
                '--max-workers', '4',
                '--memory-limit', '512',
                '--cpu-limit', '80.0',
                '--priority', 'normal'
            ])
            assert result.exit_code == 0
            assert "Concurrent processing completed" in result.output
            assert "Total jobs: 10" in result.output
            assert "Completed: 10" in result.output

class TestEndToEndDaemonWorkflow:
    """End-to-end tests for daemon workflow."""
    
    @patch('src.receipt_processor.cli.ServiceManager')
    def test_daemon_workflow(self, mock_service_manager):
        """Test daemon workflow."""
        # Setup mocks
        mock_service_manager.return_value.start_service.return_value = True
        mock_service_manager.return_value.stop_service.return_value = True
        mock_service_manager.return_value.get_status.return_value = {
            "status": "running",
            "pid": 12345,
            "uptime": "1h 30m",
            "memory_usage": "256MB",
            "cpu_usage": "15%"
        }
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Start daemon
            result = runner.invoke(cli, [
                'daemon-start',
                '--watch-dir', temp_dir,
                '--max-workers', '4',
                '--memory-limit', '512',
                '--cpu-limit', '80.0'
            ])
            assert result.exit_code == 0
            assert "Daemon service started successfully" in result.output
            
            # Check daemon status
            result = runner.invoke(cli, ['daemon-status'])
            assert result.exit_code == 0
            assert "Status: running" in result.output
            assert "PID: 12345" in result.output
            
            # Stop daemon
            result = runner.invoke(cli, ['daemon-stop'])
            assert result.exit_code == 0
            assert "Daemon service stopped" in result.output

class TestEndToEndReportGeneration:
    """End-to-end tests for report generation workflow."""
    
    @patch('src.receipt_processor.cli.PaymentReporter')
    def test_report_generation_workflow(self, mock_reporter):
        """Test report generation workflow."""
        # Setup mocks
        mock_reporter.return_value.generate_report.return_value = {
            "total_receipts": 100,
            "total_amount": 2500.0,
            "success_rate": 0.95,
            "average_amount": 25.0,
            "top_vendors": [
                {"name": "Test Restaurant", "count": 20, "total": 500.0}
            ]
        }
        
        runner = CliRunner()
        
        # Generate summary report
        result = runner.invoke(cli, ['report', '--type', 'summary'])
        assert result.exit_code == 0
        
        # Generate vendor report
        result = runner.invoke(cli, ['report', '--type', 'vendor'])
        assert result.exit_code == 0
        
        # Generate workflow report
        result = runner.invoke(cli, ['report', '--type', 'workflow'])
        assert result.exit_code == 0
        
        # Generate payment report
        result = runner.invoke(cli, ['report', '--type', 'payment'])
        assert result.exit_code == 0
        
        # Generate audit report
        result = runner.invoke(cli, ['report', '--type', 'audit'])
        assert result.exit_code == 0
        
        # Generate report with filters
        result = runner.invoke(cli, [
            'report',
            '--type', 'summary',
            '--date-from', '2024-01-01',
            '--date-to', '2024-01-31',
            '--vendor', 'Test Restaurant'
        ])
        assert result.exit_code == 0
        
        # Generate report in JSON format
        result = runner.invoke(cli, ['report', '--type', 'summary', '--format', 'json'])
        assert result.exit_code == 0
        
        # Try to parse JSON output
        try:
            json_data = json.loads(result.output)
            assert isinstance(json_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Report command should return valid JSON when --format json is used")

class TestEndToEndConfiguration:
    """End-to-end tests for configuration management."""
    
    def test_configuration_workflow(self):
        """Test configuration management workflow."""
        runner = CliRunner()
        
        # Show current configuration
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
        
        # Validate configuration
        result = runner.invoke(cli, ['config', 'validate'])
        assert result.exit_code == 0
        
        # Reset configuration
        result = runner.invoke(cli, ['config', 'reset'], input='y\n')
        assert result.exit_code == 0

class TestEndToEndDataExport:
    """End-to-end tests for data export workflow."""
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_data_export_workflow(self, mock_storage):
        """Test data export workflow."""
        # Setup mock data
        mock_logs = [
            ProcessingLog(
                log_id="LOG_001",
                file_path="/test/receipt1.jpg",
                original_filename="receipt1.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name="Test Restaurant 1",
                date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                confidence_score=0.95
            ),
            ProcessingLog(
                log_id="LOG_002",
                file_path="/test/receipt2.jpg",
                original_filename="receipt2.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name="Test Restaurant 2",
                date=datetime(2024, 1, 15),
                total_amount=15.75,
                currency="USD",
                confidence_score=0.90
            )
        ]
        
        mock_storage.return_value.load_logs.return_value = mock_logs
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export to JSON
            result = runner.invoke(cli, [
                'export',
                '--format', 'json',
                '--output', str(Path(temp_dir) / 'export.json')
            ])
            assert result.exit_code == 0
            
            # Export to CSV
            result = runner.invoke(cli, [
                'export',
                '--format', 'csv',
                '--output', str(Path(temp_dir) / 'export.csv')
            ])
            assert result.exit_code == 0
            
            # Export with filters
            result = runner.invoke(cli, [
                'export',
                '--format', 'json',
                '--output', str(Path(temp_dir) / 'filtered_export.json'),
                '--status', 'completed',
                '--vendor', 'Test Restaurant 1'
            ])
            assert result.exit_code == 0
