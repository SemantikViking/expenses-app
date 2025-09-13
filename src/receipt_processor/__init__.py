"""
Receipt Processing Application

A macOS command-line application that automatically processes receipt images using AI vision
to extract vendor information, dates, and amounts, with comprehensive workflow tracking
from processing through payment reconciliation.
"""

__version__ = "0.1.0"
__author__ = "Receipt Processor Team"
__email__ = "support@receipt-processor.com"

from .config import AppSettings
from .models import ReceiptData, ProcessingStatus, ReceiptProcessingLog

__all__ = [
    "AppSettings",
    "ReceiptData", 
    "ProcessingStatus",
    "ReceiptProcessingLog",
    "__version__",
]

