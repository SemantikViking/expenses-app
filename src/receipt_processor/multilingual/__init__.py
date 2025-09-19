"""
Multi-language support module for Receipt Processing Application.

This module provides functionality for processing receipts in multiple languages
and handling language-specific text extraction and processing.
"""

from .base import BaseLanguageProcessor, LanguageConfig, LanguageDetectionResult
from .language_detector import LanguageDetector
from .text_processor import TextProcessor
from .currency_handler import CurrencyHandler
from .date_parser import DateParser
from .multilingual_engine import MultilingualEngine

__all__ = [
    "BaseLanguageProcessor",
    "LanguageConfig",
    "LanguageDetectionResult",
    "LanguageDetector", 
    "TextProcessor",
    "CurrencyHandler",
    "DateParser",
    "MultilingualEngine"
]
