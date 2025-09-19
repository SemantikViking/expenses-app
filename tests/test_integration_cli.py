"""
Integration Tests for CLI Commands

This module contains comprehensive integration tests for all CLI commands
including the new monitoring and error handling commands.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner
from datetime import datetime, timedelta

from src.receipt_processor.cli import cli
from src.receipt_processor.models import ProcessingStatus, ProcessingLog
from src.receipt_processor.payment_models import PaymentStatus, PaymentType, PaymentMethod
from src.receipt_processor.error_handling import ErrorSeverity, ErrorCategory
from src.receipt_processor.system_monitoring import HealthStatus, AlertLevel

class TestCLIBasicCommands:
    """Test cases for basic CLI commands."""
    
    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Receipt Processor" in result.output
        assert "Commands:" in result.output
    
    def test_cli_version(self):
        """Test CLI version display."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
    
    def test_verbose_option(self):
        """Test verbose option."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--verbose', '--help'])
        assert result.exit_code == 0
    
    def test_quiet_option(self):
        """Test quiet option."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--quiet', '--help'])
        assert result.exit_code == 0

class TestProcessCommand:
    """Test cases for process command."""
    
    def test_process_command_help(self):
        """Test process command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['process', '--help'])
        assert result.exit_code == 0
        assert "Process existing receipt images" in result.output
    
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.AIVisionService')
    def test_process_command_success(self, mock_ai_service, mock_file_manager):
        """Test successful process command."""
        # Setup mocks
        mock_ai_service.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [],
            "confidence_score": 0.95
        }
        mock_file_manager.return_value.rename_file.return_value = True
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test image file
            test_image = Path(temp_dir) / "receipt.jpg"
            test_image.write_bytes(b"fake image data")
            
            result = runner.invoke(cli, ['process', str(temp_dir)])
            assert result.exit_code == 0
    
    def test_process_command_invalid_directory(self):
        """Test process command with invalid directory."""
        runner = CliRunner()
        result = runner.invoke(cli, ['process', '/nonexistent/directory'])
        assert result.exit_code != 0
    
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.AIVisionService')
    def test_process_command_interactive(self, mock_ai_service, mock_file_manager):
        """Test process command with interactive mode."""
        # Setup mocks
        mock_ai_service.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [],
            "confidence_score": 0.95
        }
        mock_file_manager.return_value.rename_file.return_value = True
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test image file
            test_image = Path(temp_dir) / "receipt.jpg"
            test_image.write_bytes(b"fake image data")
            
            result = runner.invoke(cli, ['process', str(temp_dir), '--interactive'], input='y\n')
            assert result.exit_code == 0

class TestStatusCommand:
    """Test cases for status command."""
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_status_command_success(self, mock_storage):
        """Test successful status command."""
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
                status=ProcessingStatus.PROCESSING,
                vendor_name="Test Restaurant 2",
                date=datetime(2024, 1, 15),
                total_amount=15.75,
                currency="USD",
                confidence_score=0.90
            )
        ]
        mock_storage.return_value.load_logs.return_value = mock_logs
        
        runner = CliRunner()
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert "LOG_001" in result.output
        assert "LOG_002" in result.output
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_status_command_json_format(self, mock_storage):
        """Test status command with JSON format."""
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['status', '--format', 'json'])
        assert result.exit_code == 0
        
        # Try to parse JSON output
        try:
            json_data = json.loads(result.output)
            assert isinstance(json_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Status command should return valid JSON when --format json is used")
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_status_command_with_limit(self, mock_storage):
        """Test status command with limit."""
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['status', '--limit', '5'])
        assert result.exit_code == 0

class TestLogsCommand:
    """Test cases for logs command."""
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_logs_command_success(self, mock_storage):
        """Test successful logs command."""
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['logs'])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_logs_command_with_filters(self, mock_storage):
        """Test logs command with filters."""
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'logs',
            '--status', 'completed',
            '--vendor', 'Test Restaurant',
            '--date-from', '2024-01-01',
            '--date-to', '2024-01-31',
            '--amount-min', '10.0',
            '--amount-max', '100.0'
        ])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_logs_command_json_format(self, mock_storage):
        """Test logs command with JSON format."""
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['logs', '--format', 'json'])
        assert result.exit_code == 0

class TestReportCommand:
    """Test cases for report command."""
    
    @patch('src.receipt_processor.cli.PaymentReporter')
    def test_report_command_summary(self, mock_reporter):
        """Test report command with summary report."""
        mock_reporter.return_value.generate_report.return_value = {
            "total_receipts": 100,
            "total_amount": 2500.0,
            "success_rate": 0.95
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ['report', '--type', 'summary'])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.PaymentReporter')
    def test_report_command_vendor(self, mock_reporter):
        """Test report command with vendor report."""
        mock_reporter.return_value.generate_report.return_value = {
            "vendors": [
                {"name": "Test Restaurant", "count": 10, "total": 250.0}
            ]
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ['report', '--type', 'vendor'])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.PaymentReporter')
    def test_report_command_json_format(self, mock_reporter):
        """Test report command with JSON format."""
        mock_reporter.return_value.generate_report.return_value = {"test": "data"}
        
        runner = CliRunner()
        result = runner.invoke(cli, ['report', '--type', 'summary', '--format', 'json'])
        assert result.exit_code == 0

class TestHealthCommand:
    """Test cases for health command."""
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_health_command_success(self, mock_monitor):
        """Test successful health command."""
        mock_status = {
            "overall_health": "healthy",
            "timestamp": "2024-01-15T10:00:00Z",
            "health_checks": [
                {
                    "name": "cpu_check",
                    "status": "healthy",
                    "message": "CPU usage OK",
                    "response_time_ms": 50.0
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
        
        runner = CliRunner()
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert "Overall Health: HEALTHY" in result.output
        assert "CPU Usage: 45.0%" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_health_command_critical(self, mock_monitor):
        """Test health command with critical status."""
        mock_status = {
            "overall_health": "critical",
            "timestamp": "2024-01-15T10:00:00Z",
            "health_checks": [
                {
                    "name": "cpu_check",
                    "status": "critical",
                    "message": "CPU usage critical",
                    "response_time_ms": 50.0
                }
            ],
            "resource_metrics": {
                "cpu_percent": 95.0,
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
                    "level": "critical",
                    "title": "High CPU Usage",
                    "message": "CPU usage is 95%",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
        mock_monitor.return_value.get_system_status.return_value = mock_status
        
        runner = CliRunner()
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert "Overall Health: CRITICAL" in result.output
        assert "High CPU Usage" in result.output

class TestMetricsCommand:
    """Test cases for metrics command."""
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_metrics_command_table_format(self, mock_monitor):
        """Test metrics command with table format."""
        mock_metrics = [
            {
                "timestamp": datetime.now() - timedelta(minutes=i),
                "cpu_percent": 45.0 + i,
                "memory_percent": 60.0 + i,
                "memory_used_mb": 2048.0 + i * 100,
                "disk_usage_percent": 25.0,
                "disk_free_gb": 75.0
            }
            for i in range(5)
        ]
        mock_monitor.return_value.resource_monitor.get_metrics_history.return_value = mock_metrics
        mock_monitor.return_value.performance_monitor.get_metrics_history.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['metrics', '--duration', '60'])
        assert result.exit_code == 0
        assert "Resource Metrics" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_metrics_command_json_format(self, mock_monitor):
        """Test metrics command with JSON format."""
        mock_metrics = [
            {
                "timestamp": datetime.now() - timedelta(minutes=i),
                "cpu_percent": 45.0 + i,
                "memory_percent": 60.0 + i,
                "memory_used_mb": 2048.0 + i * 100,
                "disk_usage_percent": 25.0,
                "disk_free_gb": 75.0
            }
            for i in range(5)
        ]
        mock_monitor.return_value.resource_monitor.get_metrics_history.return_value = mock_metrics
        mock_monitor.return_value.performance_monitor.get_metrics_history.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['metrics', '--duration', '60', '--format', 'json'])
        assert result.exit_code == 0
        
        # Try to parse JSON output
        try:
            json_data = json.loads(result.output)
            assert isinstance(json_data, dict)
            assert "resource_metrics" in json_data
        except json.JSONDecodeError:
            pytest.fail("Metrics command should return valid JSON when --format json is used")

class TestAlertsCommand:
    """Test cases for alerts command."""
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_alerts_command_no_alerts(self, mock_monitor):
        """Test alerts command with no alerts."""
        mock_monitor.return_value.alert_manager.alerts = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['alerts'])
        assert result.exit_code == 0
        assert "No alerts found" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_alerts_command_with_alerts(self, mock_monitor):
        """Test alerts command with alerts."""
        from src.receipt_processor.system_monitoring import Alert, AlertLevel
        
        mock_alerts = [
            Alert(
                alert_id="ALERT_001",
                level=AlertLevel.WARNING,
                title="High CPU Usage",
                message="CPU usage is above 80%",
                metadata={"cpu_percent": 85.0}
            ),
            Alert(
                alert_id="ALERT_002",
                level=AlertLevel.CRITICAL,
                title="High Memory Usage",
                message="Memory usage is above 95%",
                metadata={"memory_percent": 98.0}
            )
        ]
        mock_monitor.return_value.alert_manager.alerts = mock_alerts
        
        runner = CliRunner()
        result = runner.invoke(cli, ['alerts'])
        assert result.exit_code == 0
        assert "High CPU Usage" in result.output
        assert "High Memory Usage" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_alerts_command_filter_by_level(self, mock_monitor):
        """Test alerts command with level filter."""
        from src.receipt_processor.system_monitoring import Alert, AlertLevel
        
        mock_alerts = [
            Alert(
                alert_id="ALERT_001",
                level=AlertLevel.WARNING,
                title="Warning Alert",
                message="Warning message"
            ),
            Alert(
                alert_id="ALERT_002",
                level=AlertLevel.CRITICAL,
                title="Critical Alert",
                message="Critical message"
            )
        ]
        mock_monitor.return_value.alert_manager.alerts = mock_alerts
        
        runner = CliRunner()
        result = runner.invoke(cli, ['alerts', '--level', 'warning'])
        assert result.exit_code == 0
        assert "Warning Alert" in result.output
        assert "Critical Alert" not in result.output

class TestResolveAlertsCommand:
    """Test cases for resolve-alerts command."""
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_resolve_alerts_command_specific_alert(self, mock_monitor):
        """Test resolve-alerts command with specific alert ID."""
        mock_monitor.return_value.alert_manager.resolve_alert.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ['resolve-alerts', '--error-id', 'ALERT_001'])
        assert result.exit_code == 0
        assert "Resolved alert ALERT_001" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_resolve_alerts_command_all_alerts(self, mock_monitor):
        """Test resolve-alerts command with all alerts."""
        from src.receipt_processor.system_monitoring import Alert, AlertLevel
        
        mock_alerts = [
            Alert(
                alert_id="ALERT_001",
                level=AlertLevel.WARNING,
                title="Alert 1",
                message="Message 1"
            ),
            Alert(
                alert_id="ALERT_002",
                level=AlertLevel.ERROR,
                title="Alert 2",
                message="Message 2"
            )
        ]
        mock_monitor.return_value.alert_manager.get_active_alerts.return_value = mock_alerts
        mock_monitor.return_value.alert_manager.resolve_alert.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ['resolve-alerts', '--all'])
        assert result.exit_code == 0
        assert "Resolved 2 alerts" in result.output
    
    def test_resolve_alerts_command_no_options(self):
        """Test resolve-alerts command with no options."""
        runner = CliRunner()
        result = runner.invoke(cli, ['resolve-alerts'])
        assert result.exit_code != 0
        assert "Please specify" in result.output

class TestErrorLogCommand:
    """Test cases for error-log command."""
    
    @patch('src.receipt_processor.cli.ErrorHandler')
    def test_error_log_command_success(self, mock_handler):
        """Test successful error-log command."""
        mock_summary = {
            "total_errors": 10,
            "by_severity": {"high": 2, "medium": 5, "low": 3},
            "by_category": {"validation_error": 3, "processing_error": 4, "network_error": 3},
            "resolved_errors": 8,
            "unresolved_errors": 2
        }
        mock_handler.return_value.get_error_summary.return_value = mock_summary
        
        runner = CliRunner()
        result = runner.invoke(cli, ['error-log'])
        assert result.exit_code == 0
        assert "Total Errors: 10" in result.output
        assert "Resolved: 8" in result.output
        assert "Unresolved: 2" in result.output
    
    @patch('src.receipt_processor.cli.ErrorHandler')
    def test_error_log_command_with_filters(self, mock_handler):
        """Test error-log command with filters."""
        mock_summary = {
            "total_errors": 5,
            "by_severity": {"high": 2, "medium": 3},
            "by_category": {"validation_error": 3, "processing_error": 2},
            "resolved_errors": 3,
            "unresolved_errors": 2
        }
        mock_handler.return_value.get_error_summary.return_value = mock_summary
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'error-log',
            '--hours', '12',
            '--category', 'validation_error',
            '--severity', 'high'
        ])
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.ErrorHandler')
    @patch('builtins.open', create=True)
    def test_error_log_command_with_log_file(self, mock_open, mock_handler):
        """Test error-log command with existing log file."""
        mock_summary = {
            "total_errors": 0,
            "by_severity": {},
            "by_category": {},
            "resolved_errors": 0,
            "unresolved_errors": 0
        }
        mock_handler.return_value.get_error_summary.return_value = mock_summary
        
        # Mock log file content
        mock_file_content = [
            '{"error_id": "ERR_001", "timestamp": "2024-01-15T10:00:00Z", "category": "validation_error", "error_message": "Invalid data", "severity": "medium"}\n',
            '{"error_id": "ERR_002", "timestamp": "2024-01-15T11:00:00Z", "category": "processing_error", "error_message": "Processing failed", "severity": "high"}\n'
        ]
        mock_open.return_value.__enter__.return_value.readlines.return_value = mock_file_content
        
        runner = CliRunner()
        result = runner.invoke(cli, ['error-log'])
        assert result.exit_code == 0

class TestMonitorCommand:
    """Test cases for monitor command."""
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_monitor_command_start(self, mock_monitor):
        """Test monitor command start."""
        mock_monitor.return_value.start_monitoring.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', '--start-monitoring'])
        assert result.exit_code == 0
        assert "System monitoring started" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_monitor_command_stop(self, mock_monitor):
        """Test monitor command stop."""
        mock_monitor.return_value.stop_monitoring.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', '--stop-monitoring'])
        assert result.exit_code == 0
        assert "System monitoring stopped" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_monitor_command_status_running(self, mock_monitor):
        """Test monitor command status when running."""
        mock_monitor.return_value.monitoring = True
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', '--status'])
        assert result.exit_code == 0
        assert "System monitoring is running" in result.output
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_monitor_command_status_stopped(self, mock_monitor):
        """Test monitor command status when stopped."""
        mock_monitor.return_value.monitoring = False
        
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', '--status'])
        assert result.exit_code == 0
        assert "System monitoring is not running" in result.output
    
    def test_monitor_command_no_options(self):
        """Test monitor command with no options."""
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor'])
        assert result.exit_code != 0
        assert "Please specify" in result.output

class TestDaemonCommands:
    """Test cases for daemon commands."""
    
    @patch('src.receipt_processor.cli.ServiceManager')
    def test_daemon_start_command(self, mock_service_manager):
        """Test daemon start command."""
        mock_service_manager.return_value.start_service.return_value = True
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli, [
                'daemon-start',
                '--watch-dir', temp_dir,
                '--max-workers', '4',
                '--memory-limit', '512',
                '--cpu-limit', '80.0'
            ])
            assert result.exit_code == 0
            assert "Daemon service started successfully" in result.output
    
    @patch('src.receipt_processor.cli.ServiceManager')
    def test_daemon_stop_command(self, mock_service_manager):
        """Test daemon stop command."""
        mock_service_manager.return_value.stop_service.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(cli, ['daemon-stop'])
        assert result.exit_code == 0
        assert "Daemon service stopped" in result.output
    
    @patch('src.receipt_processor.cli.ServiceManager')
    def test_daemon_status_command(self, mock_service_manager):
        """Test daemon status command."""
        mock_service_manager.return_value.get_status.return_value = {
            "status": "running",
            "pid": 12345,
            "uptime": "1h 30m",
            "memory_usage": "256MB",
            "cpu_usage": "15%"
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ['daemon-status'])
        assert result.exit_code == 0
        assert "Status: running" in result.output
        assert "PID: 12345" in result.output

class TestConcurrentProcessingCommand:
    """Test cases for concurrent processing command."""
    
    @patch('src.receipt_processor.cli.ConcurrentProcessor')
    def test_process_concurrent_command(self, mock_processor):
        """Test process-concurrent command."""
        mock_processor.return_value.start.return_value = None
        mock_processor.return_value.stop.return_value = None
        mock_processor.return_value.submit_job.return_value = True
        mock_processor.return_value.priority_queue.size.return_value = 0
        mock_processor.return_value.active_jobs = []
        mock_processor.return_value.get_metrics.return_value = Mock(
            total_jobs=5,
            completed_jobs=5,
            failed_jobs=0,
            average_processing_time=2.5
        )
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image files
            for i in range(3):
                test_image = Path(temp_dir) / f"receipt_{i}.jpg"
                test_image.write_bytes(b"fake image data")
            
            result = runner.invoke(cli, [
                'process-concurrent',
                '--input-dir', temp_dir,
                '--max-workers', '2',
                '--memory-limit', '512',
                '--cpu-limit', '80.0',
                '--priority', 'normal'
            ])
            assert result.exit_code == 0
            assert "Concurrent processing completed" in result.output

class TestBulkCommands:
    """Test cases for bulk commands."""
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_bulk_update_status_command(self, mock_storage):
        """Test bulk-update-status command."""
        mock_storage.return_value.load_logs.return_value = []
        mock_storage.return_value.update_log.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'bulk-update-status',
            '--status', 'completed',
            '--batch-size', '10'
        ], input='y\n')
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    @patch('src.receipt_processor.cli.EmailWorkflowIntegrator')
    def test_bulk_email_command(self, mock_email, mock_storage):
        """Test bulk-email command."""
        mock_storage.return_value.load_logs.return_value = []
        mock_email.return_value.send_bulk_emails.return_value = {"success": 5, "failed": 0}
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'bulk-email',
            '--batch-size', '10'
        ], input='y\n')
        assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    @patch('src.receipt_processor.cli.PaymentWorkflowEngine')
    def test_bulk_submit_command(self, mock_payment, mock_storage):
        """Test bulk-submit command."""
        mock_storage.return_value.load_logs.return_value = []
        mock_payment.return_value.submit_bulk_payments.return_value = {"success": 5, "failed": 0}
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'bulk-submit',
            '--batch-size', '10'
        ], input='y\n')
        assert result.exit_code == 0

class TestCLIErrorHandling:
    """Test cases for CLI error handling."""
    
    def test_cli_command_not_found(self):
        """Test CLI with non-existent command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['nonexistent-command'])
        assert result.exit_code != 0
    
    def test_cli_invalid_option(self):
        """Test CLI with invalid option."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--invalid-option'])
        assert result.exit_code != 0
    
    def test_cli_missing_required_argument(self):
        """Test CLI with missing required argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ['process'])
        assert result.exit_code != 0

class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    @patch('src.receipt_processor.cli.JSONStorageManager')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.AIVisionService')
    def test_full_processing_workflow(self, mock_ai, mock_file, mock_storage):
        """Test full processing workflow through CLI."""
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
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image file
            test_image = Path(temp_dir) / "receipt.jpg"
            test_image.write_bytes(b"fake image data")
            
            # Process the image
            result = runner.invoke(cli, ['process', str(temp_dir)])
            assert result.exit_code == 0
            
            # Check status
            result = runner.invoke(cli, ['status'])
            assert result.exit_code == 0
            
            # Generate report
            result = runner.invoke(cli, ['report', '--type', 'summary'])
            assert result.exit_code == 0
    
    @patch('src.receipt_processor.cli.SystemMonitor')
    def test_monitoring_workflow(self, mock_monitor):
        """Test monitoring workflow through CLI."""
        mock_status = {
            "overall_health": "healthy",
            "timestamp": "2024-01-15T10:00:00Z",
            "health_checks": [],
            "resource_metrics": {"cpu_percent": 45.0, "memory_percent": 60.0},
            "performance_metrics": {"requests_per_second": 10.0},
            "active_alerts": 0,
            "alerts": []
        }
        mock_monitor.return_value.get_system_status.return_value = mock_status
        mock_monitor.return_value.resource_monitor.get_metrics_history.return_value = []
        mock_monitor.return_value.performance_monitor.get_metrics_history.return_value = []
        
        runner = CliRunner()
        
        # Check health
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        
        # Check metrics
        result = runner.invoke(cli, ['metrics'])
        assert result.exit_code == 0
        
        # Check alerts
        result = runner.invoke(cli, ['alerts'])
        assert result.exit_code == 0
