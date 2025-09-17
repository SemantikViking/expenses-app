"""
Receipt Processing Application

A macOS command-line application that automatically processes receipt images using AI vision
to extract vendor information, dates, and amounts, with comprehensive workflow tracking
from processing through payment reconciliation.
"""

__version__ = "0.1.0"
__author__ = "Receipt Processor Team"
__email__ = "support@receipt-processor.com"

# Import available modules
from .config import AppSettings, load_settings
from .config_loader import load_config, ConfigLoader, ConfigurationError
from .config_manager import ConfigManager, init_config, validate_config, show_config_status

# Import file monitoring module
from .file_monitor import FileSystemMonitor, FileEvent, ReceiptFileHandler, create_monitor, validate_image_file

# Import image processing module  
from .image_processor import (
    ImageProcessor, ImageMetadata, ProcessingOptions, ImageFormat,
    load_and_validate_image, preprocess_receipt_image, extract_image_metadata
)

# Import data models
from .models import (
    ReceiptData, ProcessingStatus, ReceiptProcessingLog, ReceiptProcessingLogFile,
    StatusTransition, AIExtractionRequest, AIExtractionResponse, Currency
)

# Import AI vision module
from .ai_vision import (
    ReceiptExtractionAgent, VisionExtractionService, 
    extract_receipt_data, create_extraction_service
)

# Import data parsing module
from .data_parser import (
    VendorNameCleaner, DateParser, AmountExtractor, DataValidator,
    clean_vendor_name, parse_date, extract_amount, validate_receipt_data
)

# Import storage module
from .storage import (
    JSONStorageManager, LogRotationManager
)

# Import status tracking module
from .status_tracker import (
    EnhancedStatusTracker, StatusFlowValidator, RetryManager, 
    ErrorCategorizer, ProcessingMetrics, ErrorCategory, RetryStrategy
)

# Note: Additional imports will be added as modules are implemented
# from .cli import cli  # CLI is imported separately to avoid circular imports

__all__ = [
    "AppSettings",
    "load_settings", 
    "load_config",
    "ConfigLoader",
    "ConfigurationError",
    "ConfigManager",
    "init_config",
    "validate_config", 
    "show_config_status",
    "FileSystemMonitor",
    "FileEvent",
    "ReceiptFileHandler", 
    "create_monitor",
    "validate_image_file",
    "ImageProcessor",
    "ImageMetadata",
    "ProcessingOptions", 
    "ImageFormat",
    "load_and_validate_image",
    "preprocess_receipt_image",
    "extract_image_metadata",
    "ReceiptData",
    "ProcessingStatus",
    "ReceiptProcessingLog",
    "ReceiptProcessingLogFile",
    "StatusTransition",
    "AIExtractionRequest",
    "AIExtractionResponse",
    "Currency",
    "ReceiptExtractionAgent",
    "VisionExtractionService",
    "extract_receipt_data",
    "create_extraction_service",
    "VendorNameCleaner",
    "DateParser",
    "AmountExtractor",
    "DataValidator",
    "clean_vendor_name",
    "parse_date",
    "extract_amount",
    "validate_receipt_data",
    "JSONStorageManager",
    "LogRotationManager",
    "EnhancedStatusTracker",
    "StatusFlowValidator",
    "RetryManager",
    "ErrorCategorizer",
    "ProcessingMetrics",
    "ErrorCategory",
    "RetryStrategy",
    "__version__",
]

