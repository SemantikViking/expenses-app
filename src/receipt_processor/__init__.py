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

# Note: Additional imports will be added as modules are implemented
# from .models import ReceiptData, ProcessingStatus, ReceiptProcessingLog
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
    "__version__",
]

