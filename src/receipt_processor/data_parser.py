"""
Data parsing and validation module for Receipt Processing Application.

This module provides functionality for parsing, cleaning, and validating
extracted receipt data to ensure consistency and accuracy.
"""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import json

from dateutil.parser import parse as dateutil_parse
from loguru import logger

from .config import AppSettings
from .models import ReceiptData, Currency, ProcessingStatus


class VendorNameCleaner:
    """Handles vendor name cleaning and standardization."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        
        # Common business suffixes to normalize
        self.business_suffixes = [
            'LLC', 'INC', 'CORP', 'LTD', 'LP', 'LLP', 'CO', 'COMPANY',
            'INCORPORATED', 'LIMITED', 'CORPORATION', '&', 'AND'
        ]
        
        # Common words to remove or standardize
        self.noise_words = [
            'THE', 'A', 'AN', 'OF', 'FOR', 'AT', 'IN', 'ON', 'WITH',
            'STORE', 'SHOP', 'MARKET', 'OUTLET', 'CENTER', 'CENTRE'
        ]
        
        # Load custom vendor mappings if available
        self.vendor_mappings = self._load_vendor_mappings()
        
        logger.info("VendorNameCleaner initialized")
    
    def clean_vendor_name(self, raw_vendor: str) -> str:
        """
        Clean and standardize a vendor name.
        
        Args:
            raw_vendor: Raw vendor name from extraction
            
        Returns:
            Cleaned and standardized vendor name
        """
        if not raw_vendor:
            return ""
        
        # Start with the raw name
        cleaned = raw_vendor.strip()
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Convert to title case for consistency
        cleaned = cleaned.title()
        
        # Remove common OCR artifacts
        cleaned = self._remove_ocr_artifacts(cleaned)
        
        # Handle business suffixes
        cleaned = self._normalize_business_suffixes(cleaned)
        
        # Remove noise words if they don't seem essential
        cleaned = self._remove_noise_words(cleaned)
        
        # Apply custom mappings
        cleaned = self._apply_vendor_mappings(cleaned)
        
        # Final cleanup
        cleaned = cleaned.strip()
        
        logger.debug(f"Vendor name cleaned: '{raw_vendor}' -> '{cleaned}'")
        return cleaned
    
    def _remove_ocr_artifacts(self, name: str) -> str:
        """Remove common OCR reading artifacts."""
        # Remove phone numbers
        name = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', name)
        
        # Remove addresses (basic patterns)
        name = re.sub(r'\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive)', '', name)
        
        # Remove zip codes
        name = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', name)
        
        # Remove website URLs
        name = re.sub(r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', name)
        name = re.sub(r'[a-zA-Z0-9.-]+\.com', '', name)
        
        # Remove email addresses
        name = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', name)
        
        # Remove store numbers
        name = re.sub(r'#\d+', '', name)
        name = re.sub(r'Store\s+\d+', '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def _normalize_business_suffixes(self, name: str) -> str:
        """Normalize business suffixes."""
        # Create pattern for business suffixes
        suffix_pattern = r'\b(' + '|'.join(self.business_suffixes) + r')\.?\b'
        
        # Find and standardize suffixes
        def replace_suffix(match):
            suffix = match.group(1).upper()
            # Standardize common variations
            suffix_map = {
                'INCORPORATED': 'INC',
                'CORPORATION': 'CORP',
                'LIMITED': 'LTD',
                'COMPANY': 'CO',
                '&': 'AND'
            }
            return suffix_map.get(suffix, suffix)
        
        name = re.sub(suffix_pattern, replace_suffix, name, flags=re.IGNORECASE)
        return name
    
    def _remove_noise_words(self, name: str) -> str:
        """Remove noise words if they don't seem essential."""
        words = name.split()
        
        # Only remove noise words if we have more than 2 words
        if len(words) <= 2:
            return name
        
        # Don't remove if it's the first word and seems important
        filtered_words = []
        for i, word in enumerate(words):
            if word.upper() in self.noise_words:
                # Keep if it's the first word or if removing would make name too short
                if i == 0 or len([w for w in words if w.upper() not in self.noise_words]) < 2:
                    filtered_words.append(word)
            else:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def _apply_vendor_mappings(self, name: str) -> str:
        """Apply custom vendor name mappings."""
        # Check exact matches first
        if name.upper() in self.vendor_mappings:
            return self.vendor_mappings[name.upper()]
        
        # Check partial matches
        for pattern, replacement in self.vendor_mappings.items():
            if pattern in name.upper():
                return replacement
        
        return name
    
    def _load_vendor_mappings(self) -> Dict[str, str]:
        """Load vendor name mappings from configuration or file."""
        mappings = {}
        
        # Try to load from a mappings file
        mappings_file = Path("config/vendor_mappings.json")
        if mappings_file.exists():
            try:
                with open(mappings_file, 'r') as f:
                    mappings = json.load(f)
                logger.info(f"Loaded {len(mappings)} vendor mappings")
            except Exception as e:
                logger.warning(f"Failed to load vendor mappings: {e}")
        
        # Add some common default mappings
        default_mappings = {
            "MCDONALD'S": "McDonald's",
            "MCDONALDS": "McDonald's",
            "STARBUCKS": "Starbucks",
            "WALMART": "Walmart",
            "TARGET": "Target",
            "AMAZON": "Amazon",
            "COSTCO": "Costco",
            "HOME DEPOT": "Home Depot",
            "HOMEDEPOT": "Home Depot",
        }
        
        # Merge with defaults
        for key, value in default_mappings.items():
            if key not in mappings:
                mappings[key] = value
        
        return mappings


class DateParser:
    """Handles date parsing with multiple format support."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.date_formats = settings.extraction.date_formats
        
        # Common date patterns to try
        self.additional_formats = [
            "%Y-%m-%d",       # 2024-12-25
            "%m/%d/%Y",       # 12/25/2024
            "%d/%m/%Y",       # 25/12/2024
            "%m-%d-%Y",       # 12-25-2024
            "%d-%m-%Y",       # 25-12-2024
            "%Y/%m/%d",       # 2024/12/25
            "%m/%d/%y",       # 12/25/24
            "%d/%m/%y",       # 25/12/24
            "%B %d, %Y",      # December 25, 2024
            "%b %d, %Y",      # Dec 25, 2024
            "%d %B %Y",       # 25 December 2024
            "%d %b %Y",       # 25 Dec 2024
            "%Y%m%d",         # 20241225
        ]
        
        logger.info(f"DateParser initialized with {len(self.date_formats)} configured formats")
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse a date string using multiple format attempts.
        
        Args:
            date_string: Raw date string from extraction
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_string:
            return None
        
        # Clean the date string
        cleaned_date = self._clean_date_string(date_string)
        
        # Try configured formats first
        for fmt in self.date_formats:
            result = self._try_parse_format(cleaned_date, fmt)
            if result:
                logger.debug(f"Date parsed with format {fmt}: '{date_string}' -> {result}")
                return result
        
        # Try additional common formats
        for fmt in self.additional_formats:
            result = self._try_parse_format(cleaned_date, fmt)
            if result:
                logger.debug(f"Date parsed with additional format {fmt}: '{date_string}' -> {result}")
                return result
        
        # Try dateutil parser as last resort
        try:
            result = dateutil_parse(cleaned_date, fuzzy=True)
            logger.debug(f"Date parsed with dateutil: '{date_string}' -> {result}")
            return result
        except Exception:
            pass
        
        logger.warning(f"Failed to parse date: '{date_string}'")
        return None
    
    def _clean_date_string(self, date_string: str) -> str:
        """Clean and normalize date string."""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', date_string.strip())
        
        # Remove common prefixes
        cleaned = re.sub(r'^(date|transaction|trans):\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Remove time components if present
        cleaned = re.sub(r'\s+\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)?', '', cleaned, flags=re.IGNORECASE)
        
        # Handle ordinal indicators (1st, 2nd, 3rd, 4th, etc.)
        cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', cleaned)
        
        return cleaned.strip()
    
    def _try_parse_format(self, date_string: str, format_str: str) -> Optional[datetime]:
        """Try to parse date with a specific format."""
        try:
            return datetime.strptime(date_string, format_str)
        except ValueError:
            return None


class AmountExtractor:
    """Handles amount extraction with currency detection."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.default_currency = Currency(settings.extraction.default_currency)
        
        # Currency symbols and their codes
        self.currency_symbols = {
            '$': Currency.USD,
            '€': Currency.EUR,
            '£': Currency.GBP,
            '¥': Currency.JPY,
            '₹': Currency.CNY,  # Simplified mapping
            'C$': Currency.CAD,
            'A$': Currency.AUD,
            'CHF': Currency.CHF,
        }
        
        # Currency codes
        self.currency_codes = {code.value: code for code in Currency}
        
        logger.info("AmountExtractor initialized")
    
    def extract_amount(self, amount_string: str) -> Tuple[Optional[Decimal], Optional[Currency]]:
        """
        Extract amount and currency from a string.
        
        Args:
            amount_string: Raw amount string from extraction
            
        Returns:
            Tuple of (amount, currency) or (None, None) if extraction fails
        """
        if not amount_string:
            return None, None
        
        # Clean the amount string
        cleaned = self._clean_amount_string(amount_string)
        
        # Extract currency
        currency = self._extract_currency(cleaned)
        
        # Extract numeric amount
        amount = self._extract_numeric_amount(cleaned)
        
        if amount is not None:
            logger.debug(f"Amount extracted: '{amount_string}' -> {amount} {currency}")
            return amount, currency or self.default_currency
        
        logger.warning(f"Failed to extract amount: '{amount_string}'")
        return None, None
    
    def _clean_amount_string(self, amount_string: str) -> str:
        """Clean and normalize amount string."""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', amount_string.strip())
        
        # Remove common prefixes
        cleaned = re.sub(r'^(total|amount|sum|price):\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Handle parentheses (sometimes used for negative amounts)
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        return cleaned.strip()
    
    def _extract_currency(self, amount_string: str) -> Optional[Currency]:
        """Extract currency from amount string."""
        # Check for currency symbols
        for symbol, currency in self.currency_symbols.items():
            if symbol in amount_string:
                return currency
        
        # Check for currency codes
        for code, currency in self.currency_codes.items():
            if code in amount_string.upper():
                return currency
        
        return None
    
    def _extract_numeric_amount(self, amount_string: str) -> Optional[Decimal]:
        """Extract numeric amount from string."""
        # Remove currency symbols and codes
        numeric_string = amount_string
        
        # Remove currency symbols
        for symbol in self.currency_symbols.keys():
            numeric_string = numeric_string.replace(symbol, '')
        
        # Remove currency codes
        for code in self.currency_codes.keys():
            numeric_string = re.sub(rf'\b{code}\b', '', numeric_string, flags=re.IGNORECASE)
        
        # Remove non-numeric characters except decimal points, commas, and minus signs
        numeric_string = re.sub(r'[^\d.,\-]', '', numeric_string)
        
        # Handle different decimal separators
        # If there are multiple commas or periods, assume the last one is decimal separator
        if ',' in numeric_string and '.' in numeric_string:
            # Determine which is the decimal separator based on position
            last_comma = numeric_string.rfind(',')
            last_period = numeric_string.rfind('.')
            
            if last_period > last_comma:
                # Period is decimal separator
                numeric_string = numeric_string.replace(',', '')
            else:
                # Comma is decimal separator
                numeric_string = numeric_string.replace('.', '').replace(',', '.')
        elif ',' in numeric_string:
            # Check if comma is thousands separator or decimal separator
            comma_parts = numeric_string.split(',')
            if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                # Likely decimal separator
                numeric_string = numeric_string.replace(',', '.')
            else:
                # Likely thousands separator
                numeric_string = numeric_string.replace(',', '')
        
        # Try to convert to Decimal
        try:
            return Decimal(numeric_string)
        except (InvalidOperation, ValueError):
            return None


class DataValidator:
    """Validates and enhances extracted receipt data."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.vendor_cleaner = VendorNameCleaner(settings)
        self.date_parser = DateParser(settings)
        self.amount_extractor = AmountExtractor(settings)
        
        logger.info("DataValidator initialized")
    
    def validate_and_enhance(self, receipt_data: ReceiptData) -> ReceiptData:
        """
        Validate and enhance receipt data with cleaning and parsing.
        
        Args:
            receipt_data: Raw receipt data from AI extraction
            
        Returns:
            Enhanced and validated receipt data
        """
        enhanced = receipt_data.model_copy()
        
        # Clean vendor name
        if enhanced.vendor_name:
            enhanced.vendor_name = self.vendor_cleaner.clean_vendor_name(enhanced.vendor_name)
        
        # Parse and validate date
        if enhanced.transaction_date and isinstance(enhanced.transaction_date, str):
            parsed_date = self.date_parser.parse_date(enhanced.transaction_date)
            if parsed_date:
                enhanced.transaction_date = parsed_date
            else:
                enhanced.transaction_date = None
        
        # Extract and validate amounts
        if enhanced.total_amount and isinstance(enhanced.total_amount, str):
            amount, currency = self.amount_extractor.extract_amount(enhanced.total_amount)
            if amount:
                enhanced.total_amount = amount
                if currency and not enhanced.currency:
                    enhanced.currency = currency
        
        # Validate data consistency
        enhanced = self._validate_data_consistency(enhanced)
        
        # Update confidence based on validation
        enhanced.extraction_confidence = self._calculate_enhanced_confidence(enhanced)
        
        logger.debug(f"Data validation completed with confidence: {enhanced.extraction_confidence}")
        return enhanced
    
    def _validate_data_consistency(self, receipt_data: ReceiptData) -> ReceiptData:
        """Validate data consistency and add validation errors."""
        errors = []
        
        # Check date reasonableness
        if receipt_data.transaction_date:
            today = datetime.now()
            if receipt_data.transaction_date > today:
                errors.append("Transaction date is in the future")
            elif (today - receipt_data.transaction_date).days > 365 * 5:
                errors.append("Transaction date is more than 5 years old")
        
        # Check amount reasonableness
        if receipt_data.total_amount:
            if receipt_data.total_amount <= 0:
                errors.append("Total amount must be positive")
            elif receipt_data.total_amount > Decimal('10000'):
                errors.append("Total amount seems unusually high")
        
        # Check vendor name
        if receipt_data.vendor_name:
            if len(receipt_data.vendor_name) < 2:
                errors.append("Vendor name is too short")
            elif len(receipt_data.vendor_name) > 100:
                errors.append("Vendor name is too long")
        
        # Update validation errors
        receipt_data.validation_errors.extend(errors)
        
        return receipt_data
    
    def _calculate_enhanced_confidence(self, receipt_data: ReceiptData) -> float:
        """Calculate enhanced confidence score based on validation."""
        base_confidence = receipt_data.extraction_confidence
        
        # Boost confidence for clean data
        if receipt_data.vendor_name and len(receipt_data.vendor_name) > 2:
            base_confidence += 0.1
        
        if receipt_data.transaction_date:
            base_confidence += 0.1
        
        if receipt_data.total_amount and receipt_data.total_amount > 0:
            base_confidence += 0.1
        
        if receipt_data.currency:
            base_confidence += 0.05
        
        # Reduce confidence for validation errors
        if receipt_data.validation_errors:
            penalty = min(0.3, len(receipt_data.validation_errors) * 0.1)
            base_confidence -= penalty
        
        return max(0.0, min(1.0, base_confidence))
    
    def meets_confidence_threshold(self, receipt_data: ReceiptData) -> bool:
        """Check if receipt data meets the confidence threshold."""
        threshold = self.settings.ai_vision.confidence_threshold
        return receipt_data.extraction_confidence >= threshold


# Convenience functions
def clean_vendor_name(vendor_name: str, settings: AppSettings) -> str:
    """Clean a vendor name using the configured settings."""
    cleaner = VendorNameCleaner(settings)
    return cleaner.clean_vendor_name(vendor_name)


def parse_date(date_string: str, settings: AppSettings) -> Optional[datetime]:
    """Parse a date string using the configured formats."""
    parser = DateParser(settings)
    return parser.parse_date(date_string)


def extract_amount(amount_string: str, settings: AppSettings) -> Tuple[Optional[Decimal], Optional[Currency]]:
    """Extract amount and currency from a string."""
    extractor = AmountExtractor(settings)
    return extractor.extract_amount(amount_string)


def validate_receipt_data(receipt_data: ReceiptData, settings: AppSettings) -> ReceiptData:
    """Validate and enhance receipt data."""
    validator = DataValidator(settings)
    return validator.validate_and_enhance(receipt_data)
