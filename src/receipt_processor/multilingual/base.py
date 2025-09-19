"""
Base multi-language support classes for Receipt Processing Application.

This module defines the base classes and types for multi-language processing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from ..models import ReceiptData, Currency


class LanguageCode(str, Enum):
    """Supported language codes."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    DUTCH = "nl"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh-cn"
    CHINESE_TRADITIONAL = "zh-tw"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    UNKNOWN = "unknown"


class LanguageConfig(BaseModel):
    """Configuration for language processing."""
    # Supported languages
    supported_languages: List[LanguageCode] = Field(default_factory=lambda: [
        LanguageCode.ENGLISH,
        LanguageCode.SPANISH,
        LanguageCode.FRENCH,
        LanguageCode.GERMAN
    ])
    
    # Default language
    default_language: LanguageCode = LanguageCode.ENGLISH
    
    # Language detection settings
    auto_detect_language: bool = True
    detection_confidence_threshold: float = 0.7
    
    # Text processing settings
    normalize_text: bool = True
    remove_accents: bool = True
    case_sensitive: bool = False
    
    # Currency handling
    auto_detect_currency: bool = True
    currency_by_language: Dict[LanguageCode, str] = Field(default_factory=lambda: {
        LanguageCode.ENGLISH: "USD",
        LanguageCode.SPANISH: "EUR",
        LanguageCode.FRENCH: "EUR",
        LanguageCode.GERMAN: "EUR",
        LanguageCode.ITALIAN: "EUR",
        LanguageCode.PORTUGUESE: "EUR",
        LanguageCode.DUTCH: "EUR",
        LanguageCode.RUSSIAN: "RUB",
        LanguageCode.CHINESE_SIMPLIFIED: "CNY",
        LanguageCode.CHINESE_TRADITIONAL: "TWD",
        LanguageCode.JAPANESE: "JPY",
        LanguageCode.KOREAN: "KRW",
        LanguageCode.ARABIC: "SAR",
        LanguageCode.HINDI: "INR"
    })
    
    # Date parsing settings
    date_formats_by_language: Dict[LanguageCode, List[str]] = Field(default_factory=lambda: {
        LanguageCode.ENGLISH: ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%B %d, %Y"],
        LanguageCode.SPANISH: ["%d/%m/%Y", "%d de %B de %Y", "%Y-%m-%d"],
        LanguageCode.FRENCH: ["%d/%m/%Y", "%d %B %Y", "%Y-%m-%d"],
        LanguageCode.GERMAN: ["%d.%m.%Y", "%d. %B %Y", "%Y-%m-%d"],
        LanguageCode.ITALIAN: ["%d/%m/%Y", "%d %B %Y", "%Y-%m-%d"],
        LanguageCode.PORTUGUESE: ["%d/%m/%Y", "%d de %B de %Y", "%Y-%m-%d"],
        LanguageCode.DUTCH: ["%d-%m-%Y", "%d %B %Y", "%Y-%m-%d"],
        LanguageCode.RUSSIAN: ["%d.%m.%Y", "%d %B %Y", "%Y-%m-%d"],
        LanguageCode.CHINESE_SIMPLIFIED: ["%Y年%m月%d日", "%Y-%m-%d"],
        LanguageCode.CHINESE_TRADITIONAL: ["%Y年%m月%d日", "%Y-%m-%d"],
        LanguageCode.JAPANESE: ["%Y年%m月%d日", "%Y-%m-%d"],
        LanguageCode.KOREAN: ["%Y년 %m월 %d일", "%Y-%m-%d"],
        LanguageCode.ARABIC: ["%d/%m/%Y", "%Y-%m-%d"],
        LanguageCode.HINDI: ["%d/%m/%Y", "%Y-%m-%d"]
    })
    
    # Number formatting
    decimal_separator_by_language: Dict[LanguageCode, str] = Field(default_factory=lambda: {
        LanguageCode.ENGLISH: ".",
        LanguageCode.SPANISH: ",",
        LanguageCode.FRENCH: ",",
        LanguageCode.GERMAN: ",",
        LanguageCode.ITALIAN: ",",
        LanguageCode.PORTUGUESE: ",",
        LanguageCode.DUTCH: ",",
        LanguageCode.RUSSIAN: ",",
        LanguageCode.CHINESE_SIMPLIFIED: ".",
        LanguageCode.CHINESE_TRADITIONAL: ".",
        LanguageCode.JAPANESE: ".",
        LanguageCode.KOREAN: ".",
        LanguageCode.ARABIC: ".",
        LanguageCode.HINDI: "."
    })
    
    thousand_separator_by_language: Dict[LanguageCode, str] = Field(default_factory=lambda: {
        LanguageCode.ENGLISH: ",",
        LanguageCode.SPANISH: ".",
        LanguageCode.FRENCH: " ",
        LanguageCode.GERMAN: ".",
        LanguageCode.ITALIAN: ".",
        LanguageCode.PORTUGUESE: ".",
        LanguageCode.DUTCH: ".",
        LanguageCode.RUSSIAN: " ",
        LanguageCode.CHINESE_SIMPLIFIED: ",",
        LanguageCode.CHINESE_TRADITIONAL: ",",
        LanguageCode.JAPANESE: ",",
        LanguageCode.KOREAN: ",",
        LanguageCode.ARABIC: ",",
        LanguageCode.HINDI: ","
    })


class LanguageDetectionResult(BaseModel):
    """Result of language detection."""
    detected_language: LanguageCode
    confidence: float = Field(ge=0.0, le=1.0)
    alternative_languages: List[Dict[str, Any]] = Field(default_factory=list)
    detection_method: str = ""
    processing_time: float = 0.0


class TextProcessingResult(BaseModel):
    """Result of text processing."""
    original_text: str
    processed_text: str
    language: LanguageCode
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CurrencyDetectionResult(BaseModel):
    """Result of currency detection."""
    detected_currency: Optional[str] = None
    currency_symbol: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    detection_method: str = ""
    language_hint: Optional[LanguageCode] = None


class DateParsingResult(BaseModel):
    """Result of date parsing."""
    parsed_date: Optional[datetime] = None
    original_text: str
    language: LanguageCode
    confidence: float = Field(ge=0.0, le=1.0)
    format_used: Optional[str] = None
    parsing_time: float = 0.0


class BaseLanguageProcessor(ABC):
    """Abstract base class for language processors."""
    
    def __init__(self, config: Optional[LanguageConfig] = None):
        self.config = config or LanguageConfig()
    
    @abstractmethod
    async def detect_language(self, text: str) -> LanguageDetectionResult:
        """Detect the language of the given text."""
        pass
    
    @abstractmethod
    async def process_text(self, text: str, language: Optional[LanguageCode] = None) -> TextProcessingResult:
        """Process text for the given language."""
        pass
    
    @abstractmethod
    async def detect_currency(self, text: str, language: Optional[LanguageCode] = None) -> CurrencyDetectionResult:
        """Detect currency from text."""
        pass
    
    @abstractmethod
    async def parse_date(self, text: str, language: Optional[LanguageCode] = None) -> DateParsingResult:
        """Parse date from text."""
        pass
    
    def normalize_text(self, text: str, language: LanguageCode) -> str:
        """Normalize text for the given language."""
        if not text:
            return text
        
        normalized = text.strip()
        
        if self.config.normalize_text:
            # Remove extra whitespace
            normalized = " ".join(normalized.split())
        
        if self.config.remove_accents and language in [LanguageCode.SPANISH, LanguageCode.FRENCH, LanguageCode.PORTUGUESE]:
            try:
                import unicodedata
                normalized = unicodedata.normalize('NFD', normalized)
                normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
            except ImportError:
                pass  # Fallback if unicodedata not available
        
        if not self.config.case_sensitive:
            normalized = normalized.lower()
        
        return normalized
    
    def get_currency_for_language(self, language: LanguageCode) -> str:
        """Get default currency for a language."""
        return self.config.currency_by_language.get(language, "USD")
    
    def get_date_formats_for_language(self, language: LanguageCode) -> List[str]:
        """Get date formats for a language."""
        return self.config.date_formats_by_language.get(language, ["%Y-%m-%d"])
    
    def get_decimal_separator_for_language(self, language: LanguageCode) -> str:
        """Get decimal separator for a language."""
        return self.config.decimal_separator_by_language.get(language, ".")
    
    def get_thousand_separator_for_language(self, language: LanguageCode) -> str:
        """Get thousand separator for a language."""
        return self.config.thousand_separator_by_language.get(language, ",")
    
    def is_language_supported(self, language: LanguageCode) -> bool:
        """Check if a language is supported."""
        return language in self.config.supported_languages
    
    def get_supported_languages(self) -> List[LanguageCode]:
        """Get list of supported languages."""
        return self.config.supported_languages.copy()
