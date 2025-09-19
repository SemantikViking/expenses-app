"""
Unit Tests for Pydantic Models

This module contains comprehensive unit tests for all Pydantic models
used in the receipt processing system.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any

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

class TestReceiptData:
    """Test cases for ReceiptData model."""
    
    def test_receipt_data_creation(self, sample_receipt_data):
        """Test basic ReceiptData creation."""
        receipt = sample_receipt_data
        assert receipt.vendor_name == "Test Restaurant"
        assert receipt.total_amount == 25.50
        assert receipt.currency == "USD"
        assert len(receipt.items) == 3
        assert receipt.confidence_score == 0.95
    
    def test_receipt_data_validation(self):
        """Test ReceiptData validation rules."""
        # Test valid data
        valid_data = {
            "vendor_name": "Test Restaurant",
            "date": datetime(2024, 1, 15),
            "total_amount": 25.50,
            "currency": "USD",
            "items": [{"name": "Burger", "price": 15.99, "quantity": 1}],
            "confidence_score": 0.95
        }
        receipt = ReceiptData(**valid_data)
        assert receipt.vendor_name == "Test Restaurant"
        
        # Test invalid confidence score
        with pytest.raises(ValueError):
            ReceiptData(
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                items=[],
                confidence_score=1.5  # Invalid: > 1.0
            )
        
        # Test negative total amount
        with pytest.raises(ValueError):
            ReceiptData(
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=-25.50,  # Invalid: negative
                currency="USD",
                items=[],
                confidence_score=0.95
            )
    
    def test_receipt_data_serialization(self, sample_receipt_data):
        """Test ReceiptData serialization to dict."""
        receipt = sample_receipt_data
        data = receipt.model_dump()
        
        assert isinstance(data, dict)
        assert data["vendor_name"] == "Test Restaurant"
        assert data["total_amount"] == 25.50
        assert data["currency"] == "USD"
    
    def test_receipt_data_deserialization(self):
        """Test ReceiptData deserialization from dict."""
        data = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15T00:00:00",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [{"name": "Burger", "price": 15.99, "quantity": 1}],
            "confidence_score": 0.95
        }
        receipt = ReceiptData.model_validate(data)
        assert receipt.vendor_name == "Test Restaurant"
        assert receipt.total_amount == 25.50

class TestReceiptProcessingLog:
    """Test cases for ReceiptProcessingLog model."""
    
    def test_processing_log_creation(self, sample_processing_log):
        """Test basic ReceiptProcessingLog creation."""
        log = sample_processing_log
        assert log.log_id == "LOG_001"
        assert log.status == ProcessingStatus.PROCESSING
        assert log.vendor_name == "Test Restaurant"
        assert log.total_amount == 25.50
    
    def test_processing_log_status_transitions(self):
        """Test valid status transitions."""
        log = ReceiptProcessingLog(
            log_id="LOG_001",
            file_path="/test/receipt.jpg",
            original_filename="receipt.jpg",
            status=ProcessingStatus.PROCESSING,
            vendor_name="Test Restaurant",
            transaction_date=datetime(2024, 1, 15),
            total_amount=25.50,
            currency="USD",
            confidence_score=0.95
        )
        
        # Test valid transitions
        log.status = ProcessingStatus.PROCESSED
        assert log.status == ProcessingStatus.PROCESSED
        
        log.status = ProcessingStatus.ERROR
        assert log.status == ProcessingStatus.ERROR
    
    def test_processing_log_validation(self):
        """Test ReceiptProcessingLog validation rules."""
        # Test valid log
        valid_log = ReceiptProcessingLog(
            log_id="LOG_001",
            file_path="/test/receipt.jpg",
            original_filename="receipt.jpg",
            status=ProcessingStatus.PROCESSING,
            vendor_name="Test Restaurant",
            transaction_date=datetime(2024, 1, 15),
            total_amount=25.50,
            currency="USD",
            confidence_score=0.95
        )
        assert valid_log.log_id == "LOG_001"
        
        # Test invalid confidence score
        with pytest.raises(ValueError):
            ReceiptProcessingLog(
                log_id="LOG_001",
                file_path="/test/receipt.jpg",
                original_filename="receipt.jpg",
                status=ProcessingStatus.PROCESSING,
                vendor_name="Test Restaurant",
                transaction_date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                confidence_score=1.5  # Invalid: > 1.0
            )

class TestPayment:
    """Test cases for Payment model."""
    
    def test_payment_creation(self, sample_payment):
        """Test basic Payment creation."""
        payment = sample_payment
        assert payment.payment_id == "PAY_001"
        assert payment.amount == 25.50
        assert payment.currency == "USD"
        assert payment.payment_type == PaymentType.EXPENSE
        assert payment.status == PaymentStatus.PENDING
    
    def test_payment_validation(self):
        """Test Payment validation rules."""
        # Test valid payment
        valid_payment = Payment(
            payment_id="PAY_001",
            receipt_log_id="LOG_001",
            amount=25.50,
            currency="USD",
            payment_type=PaymentType.EXPENSE,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.PENDING,
            recipient=PaymentRecipient(
                name="Test Restaurant",
                email="test@restaurant.com"
            )
        )
        assert valid_payment.payment_id == "PAY_001"
        
        # Test negative amount
        with pytest.raises(ValueError):
            Payment(
                payment_id="PAY_001",
                receipt_log_id="LOG_001",
                amount=-25.50,  # Invalid: negative
                currency="USD",
                payment_type=PaymentType.EXPENSE,
                payment_method=PaymentMethod.CREDIT_CARD,
                status=PaymentStatus.PENDING,
                recipient=PaymentRecipient(
                    name="Test Restaurant",
                    email="test@restaurant.com"
                )
            )
    
    def test_payment_recipient_validation(self):
        """Test PaymentRecipient validation."""
        # Test valid recipient
        recipient = PaymentRecipient(
            name="Test Restaurant",
            email="test@restaurant.com",
            account_number="1234567890"
        )
        assert recipient.name == "Test Restaurant"
        assert recipient.email == "test@restaurant.com"
        
        # Test invalid email
        with pytest.raises(ValueError):
            PaymentRecipient(
                name="Test Restaurant",
                email="invalid-email",  # Invalid email format
                account_number="1234567890"
            )

class TestEmailModels:
    """Test cases for email models."""
    
    def test_email_config_creation(self, sample_email_config):
        """Test EmailConfig creation."""
        config = sample_email_config
        assert config.smtp_server == "smtp.test.com"
        assert config.smtp_port == 587
        assert config.username == "test@example.com"
        assert config.use_tls is True
    
    def test_email_message_creation(self, sample_email_message):
        """Test EmailMessage creation."""
        message = sample_email_message
        assert message.message_id == "MSG_001"
        assert message.subject == "Test Receipt Processing"
        assert message.status == EmailDeliveryStatus.PENDING
        assert len(message.to_recipients) == 1
    
    def test_email_recipient_validation(self):
        """Test EmailRecipient validation."""
        # Test valid recipient
        recipient = EmailRecipient(
            email="test@example.com",
            name="Test User"
        )
        assert recipient.email == "test@example.com"
        
        # Test invalid email
        with pytest.raises(ValueError):
            EmailRecipient(
                email="invalid-email",
                name="Test User"
            )

class TestWorkflowModels:
    """Test cases for workflow models."""
    
    def test_payment_workflow_rule_creation(self, sample_workflow_rules):
        """Test PaymentWorkflowRule creation."""
        rule = sample_workflow_rules[0]
        assert rule.rule_id == "rule_001"
        assert rule.name == "Auto-approve Small Payments"
        assert rule.priority == 1
        assert rule.enabled is True
    
    def test_workflow_condition_validation(self):
        """Test PaymentWorkflowCondition validation."""
        condition = PaymentWorkflowCondition(
            field="amount",
            operator="less_than",
            value=100.0
        )
        assert condition.field == "amount"
        assert condition.operator == "less_than"
        assert condition.value == 100.0
        
        # Test invalid operator
        with pytest.raises(ValueError):
            PaymentWorkflowCondition(
                field="amount",
                operator="invalid_operator",  # Invalid operator
                value=100.0
            )
    
    def test_workflow_action_validation(self):
        """Test PaymentWorkflowAction validation."""
        action = PaymentWorkflowAction(
            action_type="approve",
            parameters={"auto_approve": True}
        )
        assert action.action_type == "approve"
        assert action.parameters == {"auto_approve": True}
        
        # Test invalid action type
        with pytest.raises(ValueError):
            PaymentWorkflowAction(
                action_type="invalid_action",  # Invalid action type
                parameters={}
            )

class TestFileModels:
    """Test cases for file-related models."""
    
    def test_file_info_creation(self):
        """Test FileInfo creation."""
        file_info = FileInfo(
            file_path=Path("/test/receipt.jpg"),
            original_name="receipt.jpg",
            file_size=1024,
            file_type="image/jpeg",
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        assert file_info.file_path == Path("/test/receipt.jpg")
        assert file_info.file_size == 1024
        assert file_info.file_type == "image/jpeg"
    
    def test_file_organization_config(self):
        """Test FileOrganizationConfig creation."""
        config = FileOrganizationConfig(
            organize_by_date=True,
            organize_by_vendor=True,
            create_vendor_folders=True,
            date_format="%Y-%m-%d",
            max_files_per_folder=1000
        )
        assert config.organize_by_date is True
        assert config.organize_by_vendor is True
        assert config.max_files_per_folder == 1000

class TestReportModels:
    """Test cases for report models."""
    
    def test_report_filter_creation(self):
        """Test ReportFilter creation."""
        filter_obj = ReportFilter(
            status_filter=[ProcessingStatus.COMPLETED],
            date_range=(datetime(2024, 1, 1), datetime(2024, 1, 31)),
            vendor_filter=["Test Restaurant"],
            amount_range=(10.0, 100.0)
        )
        assert ProcessingStatus.COMPLETED in filter_obj.status_filter
        assert filter_obj.amount_range == (10.0, 100.0)
    
    def test_report_metrics_creation(self):
        """Test ReportMetrics creation."""
        metrics = ReportMetrics(
            total_receipts=100,
            total_amount=2500.0,
            average_amount=25.0,
            success_rate=0.95,
            processing_time_avg=2.5,
            error_count=5
        )
        assert metrics.total_receipts == 100
        assert metrics.total_amount == 2500.0
        assert metrics.success_rate == 0.95

class TestErrorModels:
    """Test cases for error models."""
    
    def test_error_log_creation(self):
        """Test ErrorLog creation."""
        error_log = ErrorLog(
            error_id="ERR_001",
            log_id="LOG_001",
            error_type="ValidationError",
            error_message="Invalid data format",
            stack_trace="Traceback...",
            timestamp=datetime.now(),
            resolved=False
        )
        assert error_log.error_id == "ERR_001"
        assert error_log.error_type == "ValidationError"
        assert error_log.resolved is False
    
    def test_processing_metrics_creation(self):
        """Test ProcessingMetrics creation."""
        metrics = ProcessingMetrics(
            total_processed=100,
            successful=95,
            failed=5,
            average_processing_time=2.5,
            total_processing_time=250.0,
            error_rate=0.05
        )
        assert metrics.total_processed == 100
        assert metrics.successful == 95
        assert metrics.failed == 5
        assert metrics.error_rate == 0.05

class TestModelSerialization:
    """Test cases for model serialization and deserialization."""
    
    def test_model_json_serialization(self, sample_receipt_data):
        """Test JSON serialization of models."""
        receipt = sample_receipt_data
        json_str = receipt.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "Test Restaurant" in json_str
        assert "25.50" in json_str
    
    def test_model_json_deserialization(self):
        """Test JSON deserialization of models."""
        json_data = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15T00:00:00",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [{"name": "Burger", "price": 15.99, "quantity": 1}],
            "confidence_score": 0.95
        }
        
        receipt = ReceiptData.model_validate_json(json.dumps(json_data))
        assert receipt.vendor_name == "Test Restaurant"
        assert receipt.total_amount == 25.50
    
    def test_model_dict_serialization(self, sample_processing_log):
        """Test dict serialization of models."""
        log = sample_processing_log
        data = log.model_dump()
        
        assert isinstance(data, dict)
        assert data["log_id"] == "LOG_001"
        assert data["status"] == "processing"
    
    def test_model_dict_deserialization(self):
        """Test dict deserialization of models."""
        data = {
            "log_id": "LOG_001",
            "file_path": "/test/receipt.jpg",
            "original_filename": "receipt.jpg",
            "status": "processing",
            "vendor_name": "Test Restaurant",
            "transaction_date": "2024-01-15T00:00:00",
            "total_amount": 25.50,
            "currency": "USD",
            "confidence_score": 0.95
        }
        
        log = ReceiptProcessingLog.model_validate(data)
        assert log.log_id == "LOG_001"
        assert log.status == ProcessingStatus.PROCESSING

class TestModelValidation:
    """Test cases for model validation edge cases."""
    
    def test_optional_fields(self):
        """Test optional fields in models."""
        # Test ReceiptData with minimal required fields
        receipt = ReceiptData(
            vendor_name="Test Restaurant",
            date=datetime(2024, 1, 15),
            total_amount=25.50,
            currency="USD",
            items=[],
            confidence_score=0.95
        )
        assert receipt.tax_amount is None
        assert receipt.tip_amount is None
        assert receipt.payment_method is None
    
    def test_default_values(self):
        """Test default values in models."""
        # Test ReceiptProcessingLog with defaults
        log = ReceiptProcessingLog(
            log_id="LOG_001",
            file_path="/test/receipt.jpg",
            original_filename="receipt.jpg",
            status=ProcessingStatus.PROCESSING,
            vendor_name="Test Restaurant",
            transaction_date=datetime(2024, 1, 15),
            total_amount=25.50,
            currency="USD",
            confidence_score=0.95
        )
        assert log.retry_count == 0
        assert log.error_message is None
        assert log.metadata == {}
    
    def test_field_constraints(self):
        """Test field constraints and validation."""
        # Test confidence score constraint
        with pytest.raises(ValueError):
            ReceiptData(
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                items=[],
                confidence_score=-0.1  # Invalid: < 0
            )
        
        # Test amount constraint
        with pytest.raises(ValueError):
            ReceiptData(
                vendor_name="Test Restaurant",
                date=datetime(2024, 1, 15),
                total_amount=0,  # Invalid: <= 0
                currency="USD",
                items=[],
                confidence_score=0.95
            )
    
    def test_enum_validation(self):
        """Test enum field validation."""
        # Test valid enum values
        log = ReceiptProcessingLog(
            log_id="LOG_001",
            file_path="/test/receipt.jpg",
            original_filename="receipt.jpg",
            status=ProcessingStatus.PROCESSING,
            vendor_name="Test Restaurant",
            transaction_date=datetime(2024, 1, 15),
            total_amount=25.50,
            currency="USD",
            confidence_score=0.95
        )
        assert log.status == ProcessingStatus.PROCESSING
        
        # Test invalid enum value
        with pytest.raises(ValueError):
            ReceiptProcessingLog(
                log_id="LOG_001",
                file_path="/test/receipt.jpg",
                original_filename="receipt.jpg",
                status="invalid_status",  # Invalid enum value
                vendor_name="Test Restaurant",
                transaction_date=datetime(2024, 1, 15),
                total_amount=25.50,
                currency="USD",
                confidence_score=0.95
            )
