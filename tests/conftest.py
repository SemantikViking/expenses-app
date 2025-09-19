"""
Test Configuration and Fixtures

This module provides comprehensive test fixtures, mock data, and configuration
for the receipt processing system tests.
"""

import pytest
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, patch
import asyncio

# Import all models and classes for testing
from src.receipt_processor.models import (
    ReceiptData, ReceiptProcessingLog, ProcessingStatus, ErrorLog, ProcessingMetrics,
    ReportFilter, ReportMetrics, FileInfo, FileOrganizationConfig
)
from src.receipt_processor.payment_models import (
    Payment, PaymentStatus, PaymentType, PaymentMethod, PaymentRecipient,
    PaymentWorkflowRule, PaymentWorkflowAction, PaymentWorkflowCondition
)
from src.receipt_processor.email_models import (
    EmailConfig, EmailTemplate, EmailRecipient, EmailAttachment, EmailMessage,
    EmailDeliveryStatus, EmailWorkflowConfig
)
from src.receipt_processor.daemon import ServiceConfig, ServiceStatus, ServiceMetrics
from src.receipt_processor.concurrent_processor import (
    ProcessingPriority, JobStatus, ProcessingJob, ResourceLimits, ProcessingMetrics
)
from src.receipt_processor.error_handling import (
    ErrorSeverity, ErrorCategory, RetryStrategy, ErrorContext, ErrorInfo,
    ReceiptProcessorError, ValidationError, ProcessingError
)
from src.receipt_processor.system_monitoring import (
    HealthStatus, AlertLevel, ResourceMetrics, PerformanceMetrics,
    HealthCheck, Alert
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_receipt_data():
    """Sample receipt data for testing."""
    return ReceiptData(
        vendor_name="Test Restaurant",
        date=datetime(2024, 1, 15),
        total_amount=25.50,
        currency="USD",
        items=[
            {"name": "Burger", "price": 15.99, "quantity": 1},
            {"name": "Fries", "price": 4.99, "quantity": 1},
            {"name": "Drink", "price": 2.99, "quantity": 1}
        ],
        tax_amount=1.53,
        tip_amount=0.00,
        payment_method="Credit Card",
        receipt_number="R123456",
        confidence_score=0.95
    )

@pytest.fixture
def sample_processing_log():
    """Sample processing log for testing."""
    return ReceiptProcessingLog(
        log_id="LOG_001",
        file_path="/test/receipt.jpg",
        original_filename="receipt.jpg",
        status=ProcessingStatus.PROCESSING,
        vendor_name="Test Restaurant",
        transaction_date=datetime(2024, 1, 15),
        total_amount=25.50,
        currency="USD",
        confidence_score=0.95,
        processing_time=2.5,
        error_message=None,
        retry_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={"test": True}
    )

@pytest.fixture
def sample_payment():
    """Sample payment for testing."""
    return Payment(
        payment_id="PAY_001",
        receipt_log_id="LOG_001",
        amount=25.50,
        currency="USD",
        payment_type=PaymentType.EXPENSE,
        payment_method=PaymentMethod.CREDIT_CARD,
        status=PaymentStatus.PENDING,
        recipient=PaymentRecipient(
            name="Test Restaurant",
            email="test@restaurant.com",
            account_number="1234567890"
        ),
        due_date=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={"test": True}
    )

@pytest.fixture
def sample_email_config():
    """Sample email configuration for testing."""
    return EmailConfig(
        smtp_server="smtp.test.com",
        smtp_port=587,
        username="test@example.com",
        password="test_password",
        use_tls=True,
        use_ssl=False,
        timeout=30
    )

@pytest.fixture
def sample_email_message():
    """Sample email message for testing."""
    return EmailMessage(
        message_id="MSG_001",
        to_recipients=[EmailRecipient(email="test@example.com", name="Test User")],
        subject="Test Receipt Processing",
        body="This is a test email",
        html_body="<p>This is a test email</p>",
        attachments=[],
        status=EmailDeliveryStatus.PENDING,
        created_at=datetime.now(),
        sent_at=None,
        delivered_at=None,
        error_message=None
    )

@pytest.fixture
def sample_error_info():
    """Sample error information for testing."""
    return ErrorInfo(
        error_id="ERR_001",
        exception_type="ValidationError",
        error_message="Invalid data format",
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.VALIDATION_ERROR,
        context=ErrorContext(
            operation="process_receipt",
            file_path="/test/receipt.jpg",
            metadata={"test": True}
        ),
        stack_trace="Traceback (most recent call last)...",
        retry_count=0,
        max_retries=3,
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        recovery_attempted=False,
        resolved=False
    )

@pytest.fixture
def sample_health_check():
    """Sample health check for testing."""
    return HealthCheck(
        name="test_check",
        status=HealthStatus.HEALTHY,
        message="Test check passed",
        response_time_ms=50.0,
        details={"cpu_percent": 45.0, "memory_percent": 60.0}
    )

@pytest.fixture
def sample_alert():
    """Sample alert for testing."""
    return Alert(
        alert_id="ALERT_001",
        level=AlertLevel.WARNING,
        title="High CPU Usage",
        message="CPU usage is above 80%",
        metadata={"cpu_percent": 85.0}
    )

@pytest.fixture
def sample_resource_metrics():
    """Sample resource metrics for testing."""
    return ResourceMetrics(
        cpu_percent=45.0,
        memory_percent=60.0,
        memory_used_mb=2048.0,
        memory_available_mb=1365.0,
        disk_usage_percent=25.0,
        disk_free_gb=75.0,
        network_sent_mb=100.0,
        network_recv_mb=150.0,
        process_count=150,
        load_average=(1.2, 1.5, 1.8)
    )

@pytest.fixture
def sample_performance_metrics():
    """Sample performance metrics for testing."""
    return PerformanceMetrics(
        requests_per_second=10.5,
        average_response_time=0.5,
        error_rate=2.0,
        active_connections=25,
        queue_size=5,
        processing_time=0.3,
        throughput_mb_per_sec=5.2
    )

@pytest.fixture
def mock_ai_vision_service():
    """Mock AI vision service for testing."""
    mock_service = Mock()
    mock_service.extract_receipt_data.return_value = {
        "vendor_name": "Test Restaurant",
        "date": "2024-01-15",
        "total_amount": 25.50,
        "currency": "USD",
        "items": [
            {"name": "Burger", "price": 15.99, "quantity": 1},
            {"name": "Fries", "price": 4.99, "quantity": 1}
        ],
        "tax_amount": 1.53,
        "tip_amount": 0.00,
        "payment_method": "Credit Card",
        "receipt_number": "R123456",
        "confidence_score": 0.95
    }
    return mock_service

@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock_service = Mock()
    mock_service.send_email.return_value = True
    mock_service.send_bulk_email.return_value = {"success": 5, "failed": 0}
    return mock_service

@pytest.fixture
def mock_storage_manager():
    """Mock storage manager for testing."""
    mock_storage = Mock()
    mock_storage.save_log.return_value = True
    mock_storage.load_logs.return_value = []
    mock_storage.update_log.return_value = True
    mock_storage.delete_log.return_value = True
    return mock_storage

@pytest.fixture
def mock_file_manager():
    """Mock file manager for testing."""
    mock_manager = Mock()
    mock_manager.rename_file.return_value = True
    mock_manager.move_file.return_value = True
    mock_manager.create_backup.return_value = True
    mock_manager.cleanup_old_files.return_value = 5
    return mock_manager

@pytest.fixture
def sample_image_files(temp_dir):
    """Create sample image files for testing."""
    image_files = []
    for i in range(5):
        file_path = temp_dir / f"receipt_{i}.jpg"
        file_path.write_bytes(b"fake image data")
        image_files.append(file_path)
    return image_files

@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        "logs": [
            {
                "log_id": "LOG_001",
                "file_path": "/test/receipt1.jpg",
                "status": "processing",
                "vendor_name": "Test Restaurant 1",
                "total_amount": 25.50,
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "log_id": "LOG_002",
                "file_path": "/test/receipt2.jpg",
                "status": "completed",
                "vendor_name": "Test Restaurant 2",
                "total_amount": 15.75,
                "created_at": "2024-01-15T11:00:00Z"
            }
        ],
        "payments": [
            {
                "payment_id": "PAY_001",
                "receipt_log_id": "LOG_001",
                "amount": 25.50,
                "status": "pending",
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]
    }

@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "ai_vision": {
            "api_key": "test_api_key",
            "model": "gpt-4-vision-preview",
            "max_retries": 3,
            "timeout": 30
        },
        "email": {
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "test_password",
            "use_tls": True
        },
        "storage": {
            "log_file": "test_log.json",
            "backup_dir": "/test/backup",
            "max_file_size": 10485760,
            "retention_days": 30
        },
        "processing": {
            "max_workers": 4,
            "timeout": 60,
            "retry_attempts": 3,
            "confidence_threshold": 0.8
        }
    }

@pytest.fixture
def sample_workflow_rules():
    """Sample workflow rules for testing."""
    return [
        PaymentWorkflowRule(
            rule_id="rule_001",
            name="Auto-approve Small Payments",
            condition=PaymentWorkflowCondition(
                field="amount",
                operator="less_than",
                value=100.0
            ),
            action=PaymentWorkflowAction(
                action_type="approve",
                parameters={"auto_approve": True}
            ),
            priority=1,
            enabled=True
        ),
        PaymentWorkflowRule(
            rule_id="rule_002",
            name="Escalate Large Payments",
            condition=PaymentWorkflowCondition(
                field="amount",
                operator="greater_than",
                value=1000.0
            ),
            action=PaymentWorkflowAction(
                action_type="escalate",
                parameters={"escalate_to": "manager@example.com"}
            ),
            priority=2,
            enabled=True
        )
    ]

@pytest.fixture
def sample_error_scenarios():
    """Sample error scenarios for testing."""
    return [
        {
            "name": "validation_error",
            "exception": ValidationError("Invalid data format", field="vendor_name"),
            "expected_category": ErrorCategory.VALIDATION_ERROR,
            "expected_severity": ErrorSeverity.MEDIUM
        },
        {
            "name": "processing_error",
            "exception": ProcessingError("AI service unavailable", stage="extraction"),
            "expected_category": ErrorCategory.PROCESSING_ERROR,
            "expected_severity": ErrorSeverity.HIGH
        },
        {
            "name": "network_error",
            "exception": Exception("Connection timeout"),
            "expected_category": ErrorCategory.NETWORK_ERROR,
            "expected_severity": ErrorSeverity.MEDIUM
        }
    ]

@pytest.fixture
def sample_performance_data():
    """Sample performance data for testing."""
    return {
        "response_times": [0.1, 0.2, 0.15, 0.3, 0.25, 0.18, 0.22, 0.28, 0.19, 0.21],
        "memory_usage": [100, 120, 115, 130, 125, 118, 122, 128, 119, 121],
        "cpu_usage": [45, 50, 48, 55, 52, 47, 49, 53, 46, 48],
        "error_rates": [0.0, 0.0, 0.05, 0.0, 0.02, 0.0, 0.0, 0.01, 0.0, 0.0]
    }

@pytest.fixture
def sample_cli_commands():
    """Sample CLI commands for testing."""
    return [
        "process /test/images --verbose",
        "status --format json",
        "logs --status completed --limit 10",
        "report --type summary --format table",
        "health",
        "metrics --duration 60",
        "alerts --level warning",
        "daemon-start --watch-dir /test/watch --max-workers 4",
        "process-concurrent --input-dir /test/images --max-workers 2"
    ]

@pytest.fixture
def sample_file_operations():
    """Sample file operations for testing."""
    return [
        {
            "operation": "rename",
            "source": "/test/receipt.jpg",
            "destination": "/test/2024-01-15_Test_Restaurant_25.50.jpg",
            "expected_result": True
        },
        {
            "operation": "move",
            "source": "/test/processing/receipt.jpg",
            "destination": "/test/processed/receipt.jpg",
            "expected_result": True
        },
        {
            "operation": "backup",
            "source": "/test/receipt.jpg",
            "destination": "/test/backup/receipt.jpg",
            "expected_result": True
        }
    ]

@pytest.fixture
def sample_concurrent_jobs():
    """Sample concurrent processing jobs for testing."""
    jobs = []
    for i in range(10):
        job = ProcessingJob(
            job_id=f"job_{i}",
            file_path=Path(f"/test/receipt_{i}.jpg"),
            priority=ProcessingPriority.NORMAL
        )
        jobs.append(job)
    return jobs

@pytest.fixture
def sample_daemon_config():
    """Sample daemon configuration for testing."""
    return ServiceConfig(
        pid_file=Path("/test/receipt_processor.pid"),
        log_file=Path("/test/daemon.log"),
        watch_directory=Path("/test/watch"),
        processed_directory=Path("/test/processed"),
        check_interval=5,
        max_workers=4,
        memory_limit_mb=512,
        cpu_limit_percent=80.0
    )

@pytest.fixture
def sample_monitoring_data():
    """Sample monitoring data for testing."""
    return {
        "health_checks": [
            {"name": "cpu_check", "status": "healthy", "response_time": 50.0},
            {"name": "memory_check", "status": "warning", "response_time": 30.0},
            {"name": "disk_check", "status": "healthy", "response_time": 20.0}
        ],
        "resource_metrics": {
            "cpu_percent": 45.0,
            "memory_percent": 75.0,
            "disk_usage_percent": 25.0
        },
        "alerts": [
            {"level": "warning", "title": "High Memory Usage", "message": "Memory usage is 75%"}
        ]
    }

# Async fixtures for testing async functions
@pytest.fixture
def event_loop():
    """Create an event loop for async testing."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def async_mock():
    """Mock for async functions."""
    return AsyncMock()

class AsyncMock(Mock):
    """Mock class for async functions."""
    
    def __call__(self, *args, **kwargs):
        result = super().__call__(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return result
        return asyncio.coroutine(lambda: result)()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        elif "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker for tests that take more than 1 second
        if "slow" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)
