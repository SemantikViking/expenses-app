"""
Duplicate Detection module for Receipt Processing Application.

This module provides functionality for detecting duplicate receipts based on
various criteria including vendor, amount, date, and image similarity.
"""

from .base import BaseDuplicateDetector, DuplicateMatch, DuplicateDetectionResult
from .similarity_detector import SimilarityDetector
from .rule_based_detector import RuleBasedDetector
from .image_similarity import ImageSimilarityDetector
from .duplicate_manager import DuplicateManager

__all__ = [
    "BaseDuplicateDetector",
    "DuplicateMatch",
    "DuplicateDetectionResult", 
    "SimilarityDetector",
    "RuleBasedDetector",
    "ImageSimilarityDetector",
    "DuplicateManager"
]
