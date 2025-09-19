"""
Base duplicate detection classes for Receipt Processing Application.

This module defines the base classes and types for duplicate detection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

from ..models import ReceiptData


class DuplicateType(str, Enum):
    """Types of duplicate matches."""
    EXACT = "exact"  # Identical receipts
    SIMILAR = "similar"  # Similar receipts with minor differences
    SUSPICIOUS = "suspicious"  # Potentially duplicate but needs review
    PARTIAL = "partial"  # Partial match (e.g., same vendor, different amount)


class MatchCriteria(str, Enum):
    """Criteria used for duplicate matching."""
    VENDOR_NAME = "vendor_name"
    AMOUNT = "amount"
    DATE = "date"
    RECEIPT_NUMBER = "receipt_number"
    IMAGE_SIMILARITY = "image_similarity"
    TEXT_SIMILARITY = "text_similarity"
    LOCATION = "location"
    PAYMENT_METHOD = "payment_method"


class DuplicateMatch(BaseModel):
    """A duplicate match between two receipts."""
    match_id: str
    receipt_id_1: str
    receipt_id_2: str
    duplicate_type: DuplicateType
    confidence: float = Field(ge=0.0, le=1.0)
    match_criteria: List[MatchCriteria] = Field(default_factory=list)
    similarity_score: float = Field(ge=0.0, le=1.0)
    differences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    reviewed: bool = False
    is_duplicate: Optional[bool] = None  # User confirmation
    notes: Optional[str] = None


class DuplicateDetectionResult(BaseModel):
    """Result of duplicate detection."""
    success: bool
    duplicates_found: int = 0
    matches: List[DuplicateMatch] = Field(default_factory=list)
    processing_time: float = 0.0
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DuplicateDetectionConfig(BaseModel):
    """Configuration for duplicate detection."""
    # Similarity thresholds
    exact_match_threshold: float = 0.95
    similar_match_threshold: 0.8
    suspicious_match_threshold: 0.6
    
    # Criteria weights
    vendor_weight: float = 0.3
    amount_weight: float = 0.3
    date_weight: float = 0.2
    receipt_number_weight: float = 0.1
    image_similarity_weight: float = 0.1
    
    # Time windows for matching
    date_tolerance_days: int = 1
    amount_tolerance_percent: float = 0.05  # 5%
    
    # Image similarity settings
    image_similarity_threshold: float = 0.8
    use_image_similarity: bool = True
    
    # Text similarity settings
    text_similarity_threshold: float = 0.9
    use_text_similarity: bool = True
    
    # Vendor name matching
    vendor_fuzzy_threshold: float = 0.8
    vendor_ignore_case: bool = True
    vendor_ignore_punctuation: bool = True


class BaseDuplicateDetector(ABC):
    """Abstract base class for duplicate detectors."""
    
    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        self.config = config or DuplicateDetectionConfig()
    
    @abstractmethod
    async def detect_duplicates(
        self,
        receipts: List[ReceiptData],
        reference_receipts: Optional[List[ReceiptData]] = None
    ) -> DuplicateDetectionResult:
        """
        Detect duplicates in a list of receipts.
        
        Args:
            receipts: List of receipts to check for duplicates
            reference_receipts: Optional reference receipts to compare against
            
        Returns:
            Duplicate detection result
        """
        pass
    
    @abstractmethod
    async def check_duplicate(
        self,
        receipt: ReceiptData,
        reference_receipts: List[ReceiptData]
    ) -> List[DuplicateMatch]:
        """
        Check if a single receipt is a duplicate of any reference receipts.
        
        Args:
            receipt: Receipt to check
            reference_receipts: Reference receipts to compare against
            
        Returns:
            List of duplicate matches
        """
        pass
    
    def _calculate_vendor_similarity(self, vendor1: str, vendor2: str) -> float:
        """Calculate similarity between two vendor names."""
        if not vendor1 or not vendor2:
            return 0.0
        
        # Normalize vendor names
        v1 = self._normalize_vendor_name(vendor1)
        v2 = self._normalize_vendor_name(vendor2)
        
        if v1 == v2:
            return 1.0
        
        # Use fuzzy string matching
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, v1, v2).ratio()
        except ImportError:
            # Fallback to simple substring matching
            if v1 in v2 or v2 in v1:
                return 0.8
            return 0.0
    
    def _normalize_vendor_name(self, vendor_name: str) -> str:
        """Normalize vendor name for comparison."""
        if not vendor_name:
            return ""
        
        normalized = vendor_name.strip()
        
        if self.config.vendor_ignore_case:
            normalized = normalized.lower()
        
        if self.config.vendor_ignore_punctuation:
            import string
            normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        
        # Remove common business suffixes
        suffixes = ['inc', 'llc', 'corp', 'ltd', 'co', 'company', 'restaurant', 'cafe', 'store']
        for suffix in suffixes:
            if normalized.endswith(' ' + suffix):
                normalized = normalized[:-len(' ' + suffix)]
        
        return normalized.strip()
    
    def _calculate_amount_similarity(self, amount1: float, amount2: float) -> float:
        """Calculate similarity between two amounts."""
        if not amount1 or not amount2:
            return 0.0
        
        if amount1 == amount2:
            return 1.0
        
        # Calculate percentage difference
        diff = abs(amount1 - amount2)
        avg_amount = (amount1 + amount2) / 2
        percent_diff = diff / avg_amount if avg_amount > 0 else 1.0
        
        # Return similarity based on tolerance
        if percent_diff <= self.config.amount_tolerance_percent:
            return 1.0 - percent_diff
        else:
            return 0.0
    
    def _calculate_date_similarity(self, date1: datetime, date2: datetime) -> float:
        """Calculate similarity between two dates."""
        if not date1 or not date2:
            return 0.0
        
        if date1.date() == date2.date():
            return 1.0
        
        # Check if dates are within tolerance
        diff = abs((date1 - date2).days)
        if diff <= self.config.date_tolerance_days:
            return 1.0 - (diff / (self.config.date_tolerance_days + 1))
        else:
            return 0.0
    
    def _calculate_receipt_number_similarity(self, number1: str, number2: str) -> float:
        """Calculate similarity between two receipt numbers."""
        if not number1 or not number2:
            return 0.0
        
        if number1 == number2:
            return 1.0
        
        # Check if one is a substring of the other
        if number1 in number2 or number2 in number1:
            return 0.8
        
        # Use fuzzy string matching
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, number1, number2).ratio()
        except ImportError:
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        if text1 == text2:
            return 1.0
        
        # Use fuzzy string matching
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, text1, text2).ratio()
        except ImportError:
            return 0.0
    
    def _determine_duplicate_type(self, similarity_score: float) -> DuplicateType:
        """Determine duplicate type based on similarity score."""
        if similarity_score >= self.config.exact_match_threshold:
            return DuplicateType.EXACT
        elif similarity_score >= self.config.similar_match_threshold:
            return DuplicateType.SIMILAR
        elif similarity_score >= self.config.suspicious_match_threshold:
            return DuplicateType.SUSPICIOUS
        else:
            return DuplicateType.PARTIAL
    
    def _create_match_id(self, receipt_id_1: str, receipt_id_2: str) -> str:
        """Create a unique match ID."""
        # Sort IDs to ensure consistent match ID regardless of order
        sorted_ids = sorted([receipt_id_1, receipt_id_2])
        return f"match_{sorted_ids[0]}_{sorted_ids[1]}"
    
    def _find_differences(self, receipt1: ReceiptData, receipt2: ReceiptData) -> Dict[str, Any]:
        """Find differences between two receipts."""
        differences = {}
        
        # Compare vendor names
        if receipt1.vendor_name != receipt2.vendor_name:
            differences['vendor_name'] = {
                'receipt1': receipt1.vendor_name,
                'receipt2': receipt2.vendor_name
            }
        
        # Compare amounts
        if receipt1.total_amount != receipt2.total_amount:
            differences['total_amount'] = {
                'receipt1': receipt1.total_amount,
                'receipt2': receipt2.total_amount
            }
        
        # Compare dates
        if receipt1.transaction_date != receipt2.transaction_date:
            differences['transaction_date'] = {
                'receipt1': receipt1.transaction_date,
                'receipt2': receipt2.transaction_date
            }
        
        # Compare receipt numbers
        if receipt1.receipt_number != receipt2.receipt_number:
            differences['receipt_number'] = {
                'receipt1': receipt1.receipt_number,
                'receipt2': receipt2.receipt_number
            }
        
        # Compare currencies
        if receipt1.currency != receipt2.currency:
            differences['currency'] = {
                'receipt1': receipt1.currency,
                'receipt2': receipt2.currency
            }
        
        return differences
