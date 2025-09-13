"""
Configuration management for Receipt Processing Application.

This module provides Pydantic Settings models for type-safe configuration
management with environment variable support and validation.
"""

from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class MonitoringSettings(BaseSettings):
    """Settings for file system monitoring."""
    
    watch_folder: Path = Field(
        ..., 
        description="Folder to monitor for new receipts"
    )
    file_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".heic"],
        description="Supported image file extensions"
    )
    processing_interval: int = Field(
        default=5, 
        description="Seconds between folder checks"
    )
    max_concurrent_processing: int = Field(
        default=3,
        description="Maximum number of receipts to process simultaneously"
    )

    class Config:
        env_prefix = "MONITORING__"


class AIVisionSettings(BaseSettings):
    """Settings for AI vision processing."""
    
    provider: Literal["openai", "anthropic", "local"] = Field(
        default="openai",
        description="AI provider to use for vision processing"
    )
    model: str = Field(
        default="gpt-4-vision-preview",
        description="AI model to use for vision processing"
    )
    api_key: str = Field(
        ..., 
        description="API key for AI service"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed API calls"
    )
    confidence_threshold: float = Field(
        default=0.8, 
        ge=0.0, 
        le=1.0,
        description="Minimum confidence score to accept extraction results"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for AI API calls in seconds"
    )

    class Config:
        env_prefix = "AI_VISION__"


class ExtractionSettings(BaseSettings):
    """Settings for data extraction configuration."""
    
    extract_vendor: bool = Field(
        default=True,
        description="Enable vendor name extraction"
    )
    extract_date: bool = Field(
        default=True,
        description="Enable transaction date extraction"
    )
    extract_amount: bool = Field(
        default=True,
        description="Enable amount extraction"
    )
    extract_currency: bool = Field(
        default=True,
        description="Enable currency extraction"
    )
    date_formats: List[str] = Field(
        default=["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"],
        description="Supported date formats for parsing"
    )
    default_currency: str = Field(
        default="GBP",
        max_length=3,
        description="Default currency code"
    )

    class Config:
        env_prefix = "EXTRACTION__"


class EmailSettings(BaseSettings):
    """Settings for email integration."""
    
    enable_email: bool = Field(
        default=False,
        description="Enable email functionality"
    )
    smtp_server: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port"
    )
    smtp_username: str = Field(
        ..., 
        description="SMTP username/email"
    )
    smtp_password: str = Field(
        ..., 
        description="SMTP password or app password"
    )
    default_recipient: Optional[str] = Field(
        default=None,
        description="Default email recipient for receipts"
    )
    email_templates_path: Path = Field(
        default=Path("./templates"),
        description="Path to email templates directory"
    )

    class Config:
        env_prefix = "EMAIL__"


class PaymentSettings(BaseSettings):
    """Settings for payment tracking."""
    
    enable_payment_tracking: bool = Field(
        default=False,
        description="Enable payment tracking functionality"
    )
    payment_systems: List[str] = Field(
        default=["manual", "quickbooks", "xero"],
        description="Supported payment systems"
    )
    default_payment_system: str = Field(
        default="manual",
        description="Default payment system to use"
    )
    auto_reconcile: bool = Field(
        default=False,
        description="Enable automatic payment reconciliation"
    )

    class Config:
        env_prefix = "PAYMENT__"


class StorageSettings(BaseSettings):
    """Settings for data storage."""
    
    log_file_path: Path = Field(
        default=Path("./receipt_processing_log.json"),
        description="Path to the main processing log file"
    )
    backup_enabled: bool = Field(
        default=True,
        description="Enable automatic backups"
    )
    backup_interval_hours: int = Field(
        default=24,
        description="Hours between automatic backups"
    )
    max_log_entries: int = Field(
        default=10000,
        description="Maximum log entries before rotation"
    )

    class Config:
        env_prefix = "STORAGE__"


class LoggingSettings(BaseSettings):
    """Settings for application logging."""
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: Path = Field(
        default=Path("./logs/receipt-processor.log"),
        description="Path to application log file"
    )
    max_log_size_mb: int = Field(
        default=10,
        description="Maximum log file size in MB before rotation"
    )
    backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )
    enable_logfire: bool = Field(
        default=True,
        description="Enable Pydantic Logfire integration"
    )

    class Config:
        env_prefix = "LOGGING__"


class AppSettings(BaseSettings):
    """Main application settings container."""
    
    monitoring: MonitoringSettings
    ai_vision: AIVisionSettings
    extraction: ExtractionSettings
    email: EmailSettings
    payment: PaymentSettings
    storage: StorageSettings
    logging: LoggingSettings

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.storage.log_file_path.parent,
            self.logging.log_file.parent,
            self.email.email_templates_path,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_config(cls, env_file: Optional[str] = None) -> "AppSettings":
        """Load configuration from environment variables and .env file."""
        if env_file:
            return cls(_env_file=env_file)
        return cls()


# Convenience function to load settings (kept for backwards compatibility)
def load_settings(env_file: Optional[str] = None) -> AppSettings:
    """Load application settings."""
    return AppSettings.load_config(env_file)


# Note: For enhanced configuration loading with validation, use config_loader.load_config()
