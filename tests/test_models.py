"""
Tests for the data models module.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from receipt_processor.models import (
    ReceiptData, ProcessingStatus, ReceiptProcessingLog, 
    ReceiptProcessingLogFile, StatusTransition, Currency,
    AIExtractionRequest, AIExtractionResponse
)


def test_receipt_data_creation():
    """Test ReceiptData model creation."""
    receipt = ReceiptData(
        vendor_name="Test Store",
        transaction_date=datetime(2025, 6, 15),
        total_amount=Decimal("25.99"),
        currency=Currency.USD
    )
    
    assert receipt.vendor_name == "Test Store"
    assert receipt.total_amount == Decimal("25.99")
    assert receipt.currency == Currency.USD
    assert receipt.has_required_data is True


def test_receipt_data_validation():
    """Test ReceiptData validation logic."""
    # Test with inconsistent amounts
    receipt = ReceiptData(
        vendor_name="Test Store",
        transaction_date=datetime(2025, 6, 15),
        total_amount=Decimal("25.99"),
        subtotal=Decimal("20.00"),
        tax_amount=Decimal("4.00")  # Should be 5.99 to match total
    )
    
    assert len(receipt.validation_errors) > 0
    assert "doesn't match subtotal + tax" in receipt.validation_errors[0]


def test_receipt_data_filename_format():
    """Test filename generation from receipt data."""
    receipt = ReceiptData(
        vendor_name="Test Store & Co.",
        transaction_date=datetime(2025, 6, 15),
        total_amount=Decimal("25.99"),
        currency=Currency.USD
    )
    
    filename = receipt.to_filename_format()
    assert filename.startswith("20250615")
    assert "Test_Store___Co" in filename
    assert "USD25.99" in filename


def test_receipt_data_missing_data():
    """Test receipt data with missing required fields."""
    receipt = ReceiptData(
        total_amount=Decimal("25.99")
        # Missing vendor_name and transaction_date
    )
    
    assert receipt.has_required_data is False


def test_processing_status_enum():
    """Test ProcessingStatus enum values."""
    assert ProcessingStatus.PENDING == "pending"
    assert ProcessingStatus.PROCESSED == "processed"
    assert ProcessingStatus.ERROR == "error"


def test_status_transition():
    """Test StatusTransition model."""
    transition = StatusTransition(
        from_status=ProcessingStatus.PENDING,
        to_status=ProcessingStatus.PROCESSING,
        reason="Starting AI extraction"
    )
    
    assert transition.from_status == ProcessingStatus.PENDING
    assert transition.to_status == ProcessingStatus.PROCESSING
    assert transition.reason == "Starting AI extraction"
    assert isinstance(transition.timestamp, datetime)


def test_receipt_processing_log():
    """Test ReceiptProcessingLog model."""
    log = ReceiptProcessingLog(
        original_filename="receipt.jpg",
        file_path=Path("/test/receipt.jpg"),
        file_size=1024
    )
    
    assert log.original_filename == "receipt.jpg"
    assert log.current_status == ProcessingStatus.PENDING
    assert len(log.status_history) == 0
    assert isinstance(log.id, type(uuid4()))


def test_receipt_processing_log_status_transition():
    """Test adding status transitions to processing log."""
    log = ReceiptProcessingLog(
        original_filename="receipt.jpg",
        file_path=Path("/test/receipt.jpg"),
        file_size=1024
    )
    
    # Add status transition
    log.add_status_transition(
        ProcessingStatus.PROCESSING,
        reason="Starting extraction",
        user="system"
    )
    
    assert log.current_status == ProcessingStatus.PROCESSING
    assert len(log.status_history) == 1
    assert log.status_history[0].from_status == ProcessingStatus.PENDING
    assert log.status_history[0].to_status == ProcessingStatus.PROCESSING


def test_receipt_processing_log_success_check():
    """Test success status checking."""
    log = ReceiptProcessingLog(
        original_filename="receipt.jpg",
        file_path=Path("/test/receipt.jpg"),
        file_size=1024
    )
    
    assert log.is_successful() is False
    
    log.add_status_transition(ProcessingStatus.PROCESSED)
    assert log.is_successful() is True


def test_receipt_processing_log_file():
    """Test ReceiptProcessingLogFile container."""
    log_file = ReceiptProcessingLogFile()
    
    assert log_file.version == "1.0"
    assert len(log_file.logs) == 0
    assert log_file.total_receipts == 0
    
    # Add a log entry
    log = ReceiptProcessingLog(
        original_filename="receipt.jpg",
        file_path=Path("/test/receipt.jpg"),
        file_size=1024
    )
    
    log_file.add_log(log)
    
    assert len(log_file.logs) == 1
    assert log_file.total_receipts == 1


def test_receipt_processing_log_file_queries():
    """Test querying log file."""
    log_file = ReceiptProcessingLogFile()
    
    # Add logs with different statuses
    log1 = ReceiptProcessingLog(
        original_filename="receipt1.jpg",
        file_path=Path("/test/receipt1.jpg"),
        file_size=1024
    )
    log1.add_status_transition(ProcessingStatus.PROCESSED)
    
    log2 = ReceiptProcessingLog(
        original_filename="receipt2.jpg",
        file_path=Path("/test/receipt2.jpg"),
        file_size=2048
    )
    log2.add_status_transition(ProcessingStatus.ERROR)
    
    log_file.add_log(log1)
    log_file.add_log(log2)
    
    # Test queries
    processed_logs = log_file.get_logs_by_status(ProcessingStatus.PROCESSED)
    assert len(processed_logs) == 1
    assert processed_logs[0].original_filename == "receipt1.jpg"
    
    error_logs = log_file.get_logs_by_status(ProcessingStatus.ERROR)
    assert len(error_logs) == 1
    assert error_logs[0].original_filename == "receipt2.jpg"
    
    # Test get by ID
    found_log = log_file.get_log_by_id(log1.id)
    assert found_log is not None
    assert found_log.original_filename == "receipt1.jpg"


def test_ai_extraction_request():
    """Test AIExtractionRequest model."""
    request = AIExtractionRequest(
        image_path=Path("/test/receipt.jpg"),
        model="gpt-4-vision-preview",
        extract_line_items=True
    )
    
    assert request.image_path == Path("/test/receipt.jpg")
    assert request.model == "gpt-4-vision-preview"
    assert request.extract_line_items is True
    assert isinstance(request.request_id, type(uuid4()))


def test_ai_extraction_response():
    """Test AIExtractionResponse model."""
    receipt_data = ReceiptData(
        vendor_name="Test Store",
        total_amount=Decimal("25.99")
    )
    
    response = AIExtractionResponse(
        request_id=uuid4(),
        success=True,
        receipt_data=receipt_data,
        model_used="gpt-4-vision-preview",
        processing_time=2.5,
        confidence_score=0.85
    )
    
    assert response.success is True
    assert response.receipt_data.vendor_name == "Test Store"
    assert response.processing_time == 2.5
    assert response.confidence_score == 0.85


def test_currency_enum():
    """Test Currency enum."""
    assert Currency.USD == "USD"
    assert Currency.EUR == "EUR"
    assert Currency.GBP == "GBP"


def test_decimal_conversion():
    """Test decimal conversion in ReceiptData."""
    # Test with string input
    receipt = ReceiptData(total_amount="25.99")
    assert receipt.total_amount == Decimal("25.99")
    
    # Test with float input
    receipt = ReceiptData(total_amount=25.99)
    assert receipt.total_amount == Decimal("25.99")
    
    # Test with int input
    receipt = ReceiptData(total_amount=26)
    assert receipt.total_amount == Decimal("26")


if __name__ == "__main__":
    pytest.main([__file__])
