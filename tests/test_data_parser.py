"""
Tests for the data parsing module.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from receipt_processor.data_parser import (
    VendorNameCleaner, DateParser, AmountExtractor, DataValidator,
    clean_vendor_name, parse_date, extract_amount, validate_receipt_data
)
from receipt_processor.models import ReceiptData, Currency
from receipt_processor.config import (
    AppSettings, MonitoringSettings, ExtractionSettings, 
    AIVisionSettings, EmailSettings, PaymentSettings, 
    StorageSettings, LoggingSettings
)


@pytest.fixture
def test_settings():
    """Create test settings."""
    return AppSettings(
        monitoring=MonitoringSettings(
            watch_folder=Path("/tmp"),
            file_extensions=[".jpg", ".png"],
            processing_interval=1,
            max_concurrent_processing=1
        ),
        ai_vision=AIVisionSettings(
            provider="openai",
            model="gpt-4-vision-preview",
            api_key="test-key",
            max_retries=3,
            confidence_threshold=0.8,
            timeout_seconds=30
        ),
        extraction=ExtractionSettings(
            extract_vendor=True,
            extract_date=True,
            extract_amount=True,
            extract_currency=True,
            date_formats=["%Y-%m-%d", "%m/%d/%Y"],
            default_currency="USD"
        ),
        email=EmailSettings(
            enable_email=False,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="test-password",
            default_recipient="test@example.com"
        ),
        payment=PaymentSettings(
            enable_payment_tracking=False,
            payment_systems=["manual"],
            default_payment_system="manual",
            auto_reconcile=False
        ),
        storage=StorageSettings(
            log_file_path=Path("/tmp/test.json"),
            backup_enabled=False,
            backup_interval_hours=24,
            max_log_entries=1000
        ),
        logging=LoggingSettings(
            log_level="INFO",
            log_file=Path("/tmp/test.log"),
            max_log_size_mb=10,
            backup_count=3,
            enable_logfire=False
        )
    )


class TestVendorNameCleaner:
    """Test VendorNameCleaner functionality."""
    
    def test_basic_cleaning(self, test_settings):
        """Test basic vendor name cleaning."""
        cleaner = VendorNameCleaner(test_settings)
        
        # Test basic cleaning
        result = cleaner.clean_vendor_name("  mcdonald's restaurant  ")
        assert result == "McDonald's"  # Should apply vendor mapping
        
        # Test title case conversion
        result = cleaner.clean_vendor_name("STARBUCKS COFFEE")
        assert result == "Starbucks"  # Should apply mapping
    
    def test_ocr_artifact_removal(self, test_settings):
        """Test removal of OCR artifacts."""
        cleaner = VendorNameCleaner(test_settings)
        
        # Test phone number removal
        result = cleaner.clean_vendor_name("Target Store (555) 123-4567")
        assert "555" not in result
        assert "Target" in result
        
        # Test address removal
        result = cleaner.clean_vendor_name("Walmart 123 Main Street")
        assert "123 Main Street" not in result
        assert "Walmart" in result
    
    def test_business_suffix_normalization(self, test_settings):
        """Test business suffix normalization."""
        cleaner = VendorNameCleaner(test_settings)
        
        result = cleaner.clean_vendor_name("Tech Company Incorporated")
        assert "INC" in result
        
        result = cleaner.clean_vendor_name("Smith & Associates LLC")
        assert "AND" in result
    
    def test_vendor_mappings(self, test_settings):
        """Test vendor name mappings."""
        cleaner = VendorNameCleaner(test_settings)
        
        # Test known mapping
        result = cleaner.clean_vendor_name("MCDONALDS")
        assert result == "McDonald's"
        
        result = cleaner.clean_vendor_name("walmart")
        assert result == "Walmart"


class TestDateParser:
    """Test DateParser functionality."""
    
    def test_standard_formats(self, test_settings):
        """Test parsing standard date formats."""
        parser = DateParser(test_settings)
        
        # Test ISO format
        result = parser.parse_date("2024-12-25")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
        
        # Test US format
        result = parser.parse_date("12/25/2024")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
    
    def test_written_formats(self, test_settings):
        """Test parsing written date formats."""
        parser = DateParser(test_settings)
        
        # Test full month name
        result = parser.parse_date("December 25, 2024")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
        
        # Test abbreviated month
        result = parser.parse_date("Dec 25, 2024")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
    
    def test_date_cleaning(self, test_settings):
        """Test date string cleaning."""
        parser = DateParser(test_settings)
        
        # Test with time removal
        result = parser.parse_date("2024-12-25 14:30:00")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
        
        # Test with prefix removal
        result = parser.parse_date("Date: 12/25/2024")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
    
    def test_invalid_dates(self, test_settings):
        """Test handling of invalid dates."""
        parser = DateParser(test_settings)
        
        result = parser.parse_date("invalid date")
        assert result is None
        
        result = parser.parse_date("")
        assert result is None
        
        result = parser.parse_date(None)
        assert result is None


class TestAmountExtractor:
    """Test AmountExtractor functionality."""
    
    def test_basic_amount_extraction(self, test_settings):
        """Test basic amount extraction."""
        extractor = AmountExtractor(test_settings)
        
        # Test simple dollar amount
        amount, currency = extractor.extract_amount("$25.99")
        assert amount == Decimal("25.99")
        assert currency == Currency.USD
        
        # Test euro amount
        amount, currency = extractor.extract_amount("€15.50")
        assert amount == Decimal("15.50")
        assert currency == Currency.EUR
    
    def test_currency_detection(self, test_settings):
        """Test currency detection."""
        extractor = AmountExtractor(test_settings)
        
        # Test various currency symbols
        amount, currency = extractor.extract_amount("£8.75")
        assert currency == Currency.GBP
        
        # Test currency codes
        amount, currency = extractor.extract_amount("100.00 USD")
        assert amount == Decimal("100.00")
        assert currency == Currency.USD
    
    def test_amount_cleaning(self, test_settings):
        """Test amount string cleaning."""
        extractor = AmountExtractor(test_settings)
        
        # Test with prefix
        amount, currency = extractor.extract_amount("Total: $25.99")
        assert amount == Decimal("25.99")
        
        # Test with thousands separator
        amount, currency = extractor.extract_amount("$1,234.56")
        assert amount == Decimal("1234.56")
        
        # Test with parentheses (negative)
        amount, currency = extractor.extract_amount("($25.99)")
        assert amount == Decimal("-25.99")
    
    def test_decimal_separators(self, test_settings):
        """Test different decimal separators."""
        extractor = AmountExtractor(test_settings)
        
        # Test comma as decimal separator
        amount, currency = extractor.extract_amount("€25,99")
        assert amount == Decimal("25.99")
        
        # Test with both comma and period
        amount, currency = extractor.extract_amount("$1,234.56")
        assert amount == Decimal("1234.56")
    
    def test_invalid_amounts(self, test_settings):
        """Test handling of invalid amounts."""
        extractor = AmountExtractor(test_settings)
        
        amount, currency = extractor.extract_amount("invalid")
        assert amount is None
        
        amount, currency = extractor.extract_amount("")
        assert amount is None


class TestDataValidator:
    """Test DataValidator functionality."""
    
    def test_vendor_name_enhancement(self, test_settings):
        """Test vendor name enhancement."""
        validator = DataValidator(test_settings)
        
        receipt = ReceiptData(
            vendor_name="  mcdonald's restaurant  ",
            total_amount=Decimal("15.99")
        )
        
        enhanced = validator.validate_and_enhance(receipt)
        assert enhanced.vendor_name == "Mcdonald'S Restaurant"
    
    def test_date_parsing_enhancement(self, test_settings):
        """Test date parsing enhancement."""
        validator = DataValidator(test_settings)
        
        receipt = ReceiptData(
            vendor_name="Test Store",
            transaction_date="2024-12-25",  # String instead of datetime
            total_amount=Decimal("15.99")
        )
        
        enhanced = validator.validate_and_enhance(receipt)
        assert isinstance(enhanced.transaction_date, datetime)
        assert enhanced.transaction_date.year == 2024
    
    def test_amount_parsing_enhancement(self, test_settings):
        """Test amount parsing enhancement."""
        validator = DataValidator(test_settings)
        
        receipt = ReceiptData(
            vendor_name="Test Store",
            total_amount="$25.99",  # String instead of Decimal
        )
        
        enhanced = validator.validate_and_enhance(receipt)
        assert enhanced.total_amount == Decimal("25.99")
        assert enhanced.currency == Currency.USD
    
    def test_confidence_threshold(self, test_settings):
        """Test confidence threshold checking."""
        validator = DataValidator(test_settings)
        
        # High confidence receipt
        receipt = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime(2024, 12, 25),
            total_amount=Decimal("25.99"),
            extraction_confidence=0.9
        )
        
        assert validator.meets_confidence_threshold(receipt) is True
        
        # Low confidence receipt
        receipt.extraction_confidence = 0.5
        assert validator.meets_confidence_threshold(receipt) is False
    
    def test_data_consistency_validation(self, test_settings):
        """Test data consistency validation."""
        validator = DataValidator(test_settings)
        
        # Test future date validation
        receipt = ReceiptData(
            vendor_name="Test Store",
            transaction_date=datetime(2030, 12, 25),  # Future date
            total_amount=Decimal("25.99")
        )
        
        enhanced = validator.validate_and_enhance(receipt)
        assert "future" in enhanced.validation_errors[0].lower()
        
        # Test negative amount validation
        receipt = ReceiptData(
            vendor_name="Test Store",
            total_amount=Decimal("-25.99")  # Negative amount
        )
        
        enhanced = validator.validate_and_enhance(receipt)
        assert any("positive" in error.lower() for error in enhanced.validation_errors)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_clean_vendor_name_function(self, test_settings):
        """Test clean_vendor_name convenience function."""
        result = clean_vendor_name("  TEST STORE  ", test_settings)
        assert result == "Test Store"
    
    def test_parse_date_function(self, test_settings):
        """Test parse_date convenience function."""
        result = parse_date("2024-12-25", test_settings)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25
    
    def test_extract_amount_function(self, test_settings):
        """Test extract_amount convenience function."""
        amount, currency = extract_amount("$25.99", test_settings)
        assert amount == Decimal("25.99")
        assert currency == Currency.USD
    
    def test_validate_receipt_data_function(self, test_settings):
        """Test validate_receipt_data convenience function."""
        receipt = ReceiptData(
            vendor_name="  test store  ",
            total_amount=Decimal("25.99")
        )
        
        enhanced = validate_receipt_data(receipt, test_settings)
        assert enhanced.vendor_name == "Test Store"


if __name__ == "__main__":
    pytest.main([__file__])
