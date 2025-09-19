"""
Base categorization classes for Receipt Processing Application.

This module defines the base classes and types for receipt categorization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from ..models import ReceiptData


class CategoryType(str, Enum):
    """Types of receipt categories."""
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    RETAIL_SHOPPING = "retail_shopping"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    PROFESSIONAL_SERVICES = "professional_services"
    TRAVEL = "travel"
    EDUCATION = "education"
    INSURANCE = "insurance"
    TAXES = "taxes"
    OTHER = "other"


class CategoryRule(BaseModel):
    """Rule for categorizing receipts."""
    rule_id: str
    name: str
    description: str
    category: CategoryType
    priority: int = Field(default=100, ge=1, le=1000)
    enabled: bool = True
    
    # Matching criteria
    vendor_patterns: List[str] = Field(default_factory=list)
    amount_ranges: List[Dict[str, float]] = Field(default_factory=list)
    date_ranges: List[Dict[str, datetime]] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    payment_methods: List[str] = Field(default_factory=list)
    
    # Rule conditions
    require_all: bool = False  # If True, all conditions must match
    case_sensitive: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ReceiptCategory(BaseModel):
    """Categorized receipt information."""
    category: CategoryType
    confidence: float = Field(ge=0.0, le=1.0)
    matched_rules: List[str] = Field(default_factory=list)
    reasoning: str = ""
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    categorized_at: datetime = Field(default_factory=datetime.now)


class CategorizationResult(BaseModel):
    """Result of receipt categorization."""
    success: bool
    category: Optional[ReceiptCategory] = None
    processing_time: float = 0.0
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseCategorizer(ABC):
    """Abstract base class for receipt categorizers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._rules: List[CategoryRule] = []
        self._load_default_rules()
    
    @abstractmethod
    async def categorize(
        self, 
        receipt_data: ReceiptData,
        rules: Optional[List[CategoryRule]] = None
    ) -> CategorizationResult:
        """
        Categorize a receipt based on its data.
        
        Args:
            receipt_data: Extracted receipt data
            rules: Optional list of rules to use (uses default if None)
            
        Returns:
            Categorization result
        """
        pass
    
    @abstractmethod
    def add_rule(self, rule: CategoryRule) -> None:
        """Add a categorization rule."""
        pass
    
    @abstractmethod
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a categorization rule by ID."""
        pass
    
    @abstractmethod
    def get_rules(self) -> List[CategoryRule]:
        """Get all categorization rules."""
        pass
    
    def _load_default_rules(self) -> None:
        """Load default categorization rules."""
        default_rules = [
            # Food & Dining
            CategoryRule(
                rule_id="food_restaurants",
                name="Restaurants",
                description="Restaurant and food service establishments",
                category=CategoryType.FOOD_DINING,
                priority=100,
                vendor_patterns=["restaurant", "cafe", "diner", "bistro", "grill", "pizza", "burger"],
                keywords=["food", "meal", "dining", "restaurant", "cafe"]
            ),
            CategoryRule(
                rule_id="food_groceries",
                name="Grocery Stores",
                description="Grocery and supermarket purchases",
                category=CategoryType.FOOD_DINING,
                priority=90,
                vendor_patterns=["grocery", "supermarket", "market", "food", "fresh", "organic"],
                keywords=["grocery", "food", "supermarket", "produce"]
            ),
            
            # Transportation
            CategoryRule(
                rule_id="transport_gas",
                name="Gas Stations",
                description="Gas station and fuel purchases",
                category=CategoryType.TRANSPORTATION,
                priority=100,
                vendor_patterns=["gas", "fuel", "station", "shell", "exxon", "chevron", "bp"],
                keywords=["gas", "fuel", "gasoline", "diesel"]
            ),
            CategoryRule(
                rule_id="transport_public",
                name="Public Transportation",
                description="Public transit and rideshare services",
                category=CategoryType.TRANSPORTATION,
                priority=90,
                vendor_patterns=["uber", "lyft", "taxi", "metro", "bus", "train", "subway"],
                keywords=["transportation", "ride", "transit", "metro"]
            ),
            
            # Retail Shopping
            CategoryRule(
                rule_id="retail_general",
                name="General Retail",
                description="General retail and shopping",
                category=CategoryType.RETAIL_SHOPPING,
                priority=50,
                vendor_patterns=["store", "shop", "retail", "mall", "department"],
                keywords=["shopping", "retail", "store", "purchase"]
            ),
            CategoryRule(
                rule_id="retail_online",
                name="Online Shopping",
                description="Online retail purchases",
                category=CategoryType.RETAIL_SHOPPING,
                priority=80,
                vendor_patterns=["amazon", "ebay", "shopify", "etsy"],
                keywords=["online", "shipping", "order"]
            ),
            
            # Healthcare
            CategoryRule(
                rule_id="health_pharmacy",
                name="Pharmacy",
                description="Pharmacy and medical supplies",
                category=CategoryType.HEALTHCARE,
                priority=100,
                vendor_patterns=["pharmacy", "drug", "cvs", "walgreens", "rite aid"],
                keywords=["pharmacy", "medicine", "prescription", "medical"]
            ),
            CategoryRule(
                rule_id="health_medical",
                name="Medical Services",
                description="Medical and healthcare services",
                category=CategoryType.HEALTHCARE,
                priority=90,
                vendor_patterns=["hospital", "clinic", "doctor", "medical", "health"],
                keywords=["medical", "health", "doctor", "hospital", "clinic"]
            ),
            
            # Entertainment
            CategoryRule(
                rule_id="entertainment_movies",
                name="Movies & Entertainment",
                description="Movie theaters and entertainment venues",
                category=CategoryType.ENTERTAINMENT,
                priority=90,
                vendor_patterns=["theater", "cinema", "movie", "amc", "regal", "netflix", "spotify"],
                keywords=["movie", "entertainment", "theater", "cinema"]
            ),
            CategoryRule(
                rule_id="entertainment_dining",
                name="Entertainment Dining",
                description="Entertainment and recreational dining",
                category=CategoryType.ENTERTAINMENT,
                priority=70,
                vendor_patterns=["bar", "pub", "club", "lounge", "brewery"],
                keywords=["bar", "pub", "entertainment", "recreation"]
            ),
            
            # Utilities
            CategoryRule(
                rule_id="utilities_electric",
                name="Electric Utilities",
                description="Electric and power utilities",
                category=CategoryType.UTILITIES,
                priority=100,
                vendor_patterns=["electric", "power", "energy", "utility"],
                keywords=["electric", "power", "utility", "energy"]
            ),
            CategoryRule(
                rule_id="utilities_water",
                name="Water Utilities",
                description="Water and sewer utilities",
                category=CategoryType.UTILITIES,
                priority=100,
                vendor_patterns=["water", "sewer", "utility"],
                keywords=["water", "sewer", "utility"]
            ),
            CategoryRule(
                rule_id="utilities_internet",
                name="Internet & Telecom",
                description="Internet and telecommunications",
                category=CategoryType.UTILITIES,
                priority=90,
                vendor_patterns=["internet", "cable", "phone", "verizon", "att", "comcast"],
                keywords=["internet", "cable", "phone", "telecom"]
            ),
            
            # Professional Services
            CategoryRule(
                rule_id="professional_legal",
                name="Legal Services",
                description="Legal and professional services",
                category=CategoryType.PROFESSIONAL_SERVICES,
                priority=90,
                vendor_patterns=["law", "legal", "attorney", "lawyer"],
                keywords=["legal", "law", "attorney", "lawyer"]
            ),
            CategoryRule(
                rule_id="professional_accounting",
                name="Accounting Services",
                description="Accounting and financial services",
                category=CategoryType.PROFESSIONAL_SERVICES,
                priority=90,
                vendor_patterns=["accounting", "tax", "cpa", "financial"],
                keywords=["accounting", "tax", "cpa", "financial"]
            ),
            
            # Travel
            CategoryRule(
                rule_id="travel_hotel",
                name="Hotels & Accommodation",
                description="Hotels and travel accommodation",
                category=CategoryType.TRAVEL,
                priority=100,
                vendor_patterns=["hotel", "inn", "resort", "marriott", "hilton", "hyatt"],
                keywords=["hotel", "travel", "accommodation", "lodging"]
            ),
            CategoryRule(
                rule_id="travel_airline",
                name="Airlines",
                description="Airline and flight services",
                category=CategoryType.TRAVEL,
                priority=100,
                vendor_patterns=["airline", "airport", "delta", "united", "american", "southwest"],
                keywords=["airline", "flight", "travel", "airport"]
            ),
            
            # Education
            CategoryRule(
                rule_id="education_school",
                name="Education",
                description="Educational services and supplies",
                category=CategoryType.EDUCATION,
                priority=90,
                vendor_patterns=["school", "university", "college", "education", "learning"],
                keywords=["education", "school", "university", "learning"]
            ),
            
            # Insurance
            CategoryRule(
                rule_id="insurance_general",
                name="Insurance",
                description="Insurance services and payments",
                category=CategoryType.INSURANCE,
                priority=90,
                vendor_patterns=["insurance", "ins", "coverage", "policy"],
                keywords=["insurance", "coverage", "policy", "premium"]
            ),
            
            # Taxes
            CategoryRule(
                rule_id="taxes_general",
                name="Taxes",
                description="Tax payments and services",
                category=CategoryType.TAXES,
                priority=100,
                vendor_patterns=["tax", "irs", "revenue", "treasury"],
                keywords=["tax", "irs", "revenue", "treasury"]
            )
        ]
        
        self._rules.extend(default_rules)
    
    def _match_vendor_patterns(self, vendor_name: str, patterns: List[str], case_sensitive: bool = False) -> bool:
        """Check if vendor name matches any pattern."""
        if not vendor_name or not patterns:
            return False
        
        vendor = vendor_name if case_sensitive else vendor_name.lower()
        
        for pattern in patterns:
            pattern_lower = pattern if case_sensitive else pattern.lower()
            if pattern_lower in vendor:
                return True
        
        return False
    
    def _match_amount_ranges(self, amount: float, ranges: List[Dict[str, float]]) -> bool:
        """Check if amount falls within any range."""
        if not amount or not ranges:
            return False
        
        for range_def in ranges:
            min_amount = range_def.get('min', 0)
            max_amount = range_def.get('max', float('inf'))
            
            if min_amount <= amount <= max_amount:
                return True
        
        return False
    
    def _match_keywords(self, text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
        """Check if text contains any keywords."""
        if not text or not keywords:
            return False
        
        text_lower = text if case_sensitive else text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword if case_sensitive else keyword.lower()
            if keyword_lower in text_lower:
                return True
        
        return False
