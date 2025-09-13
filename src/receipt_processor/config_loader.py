"""
Configuration loading utilities for Receipt Processing Application.

This module provides enhanced configuration loading with validation,
error handling, and environment file management.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError
from loguru import logger

from .config import AppSettings


class ConfigurationError(Exception):
    """Raised when configuration loading fails."""
    pass


class ConfigLoader:
    """Enhanced configuration loader with validation and error handling."""
    
    DEFAULT_ENV_FILES = [".env", ".env.local", ".env.production"]
    
    def __init__(self):
        self.loaded_files: List[Path] = []
        self.missing_files: List[Path] = []
        self.validation_errors: List[str] = []
    
    def find_env_files(self, search_paths: Optional[List[Path]] = None) -> List[Path]:
        """Find available .env files in search paths."""
        if search_paths is None:
            search_paths = [Path.cwd()]
        
        found_files = []
        
        for search_path in search_paths:
            for env_file in self.DEFAULT_ENV_FILES:
                env_path = search_path / env_file
                if env_path.exists() and env_path.is_file():
                    found_files.append(env_path)
                    self.loaded_files.append(env_path)
                else:
                    self.missing_files.append(env_path)
        
        return found_files
    
    def validate_required_settings(self, settings: AppSettings) -> List[str]:
        """Validate that all required settings are present."""
        errors = []
        
        # Check AI Vision API key
        if not settings.ai_vision.api_key or settings.ai_vision.api_key == "your_api_key_here":
            errors.append("AI_VISION__API_KEY is required and must be set to a valid API key")
        
        # Check monitoring folder exists
        if not settings.monitoring.watch_folder.exists():
            errors.append(f"MONITORING__WATCH_FOLDER path does not exist: {settings.monitoring.watch_folder}")
        
        # Check email settings if email is enabled
        if settings.email.enable_email:
            if not settings.email.smtp_username or settings.email.smtp_username == "your_email@gmail.com":
                errors.append("EMAIL__SMTP_USERNAME is required when email is enabled")
            
            if not settings.email.smtp_password or settings.email.smtp_password == "your_app_password_here":
                errors.append("EMAIL__SMTP_PASSWORD is required when email is enabled")
        
        return errors
    
    def load_with_validation(
        self, 
        env_file: Optional[str] = None,
        create_missing_dirs: bool = True
    ) -> Tuple[AppSettings, List[str]]:
        """
        Load configuration with comprehensive validation.
        
        Returns:
            Tuple of (settings, warnings)
        """
        warnings = []
        
        try:
            # Load settings
            if env_file:
                if not Path(env_file).exists():
                    raise ConfigurationError(f"Specified env file does not exist: {env_file}")
                settings = AppSettings(_env_file=env_file)
                self.loaded_files.append(Path(env_file))
            else:
                # Try to find and load default env files
                found_files = self.find_env_files()
                if found_files:
                    settings = AppSettings(_env_file=str(found_files[0]))
                    logger.info(f"Loaded configuration from: {found_files[0]}")
                else:
                    settings = AppSettings()
                    warnings.append("No .env file found, using environment variables and defaults")
            
            # Validate required settings
            validation_errors = self.validate_required_settings(settings)
            if validation_errors:
                self.validation_errors.extend(validation_errors)
                raise ConfigurationError(f"Configuration validation failed:\n" + "\n".join(validation_errors))
            
            # Create necessary directories
            if create_missing_dirs:
                try:
                    settings.create_directories()
                    logger.info("Created necessary directories")
                except Exception as e:
                    warnings.append(f"Failed to create some directories: {e}")
            
            return settings, warnings
            
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                error_details.append(f"{field}: {error['msg']}")
            
            raise ConfigurationError(
                f"Configuration validation failed:\n" + "\n".join(error_details)
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def get_config_status(self) -> Dict[str, any]:
        """Get detailed status of configuration loading."""
        return {
            "loaded_files": [str(f) for f in self.loaded_files],
            "missing_files": [str(f) for f in self.missing_files],
            "validation_errors": self.validation_errors,
            "environment_variables": {
                key: "***" if "password" in key.lower() or "key" in key.lower() else value
                for key, value in os.environ.items()
                if key.upper().startswith(('MONITORING__', 'AI_VISION__', 'EMAIL__', 'PAYMENT__', 'STORAGE__', 'LOGGING__'))
            }
        }


def load_config(
    env_file: Optional[str] = None,
    validate: bool = True,
    create_dirs: bool = True
) -> AppSettings:
    """
    Load application configuration with optional validation.
    
    Args:
        env_file: Specific .env file to load (optional)
        validate: Whether to perform validation (default: True)
        create_dirs: Whether to create missing directories (default: True)
    
    Returns:
        AppSettings instance
    
    Raises:
        ConfigurationError: If loading or validation fails
    """
    loader = ConfigLoader()
    
    if validate:
        settings, warnings = loader.load_with_validation(env_file, create_dirs)
        
        for warning in warnings:
            logger.warning(warning)
        
        return settings
    else:
        # Simple loading without validation
        if env_file:
            return AppSettings(_env_file=env_file)
        else:
            return AppSettings()


def create_default_env_file(output_path: str = ".env") -> None:
    """
    Create a default .env file with placeholder values.
    
    Args:
        output_path: Path where to create the .env file
    """
    env_content = """# Receipt Processing Application - Environment Configuration
# Copy from env.example and fill in your actual values

# =============================================================================
# AI Vision Settings (REQUIRED)
# =============================================================================
AI_VISION__PROVIDER=openai
AI_VISION__MODEL=gpt-4-vision-preview
AI_VISION__API_KEY=your_openai_api_key_here
AI_VISION__CONFIDENCE_THRESHOLD=0.8

# =============================================================================
# Monitoring Settings (REQUIRED)
# =============================================================================
MONITORING__WATCH_FOLDER=/Users/username/Desktop/Receipts
MONITORING__PROCESSING_INTERVAL=5

# =============================================================================
# Email Settings (Optional - set EMAIL__ENABLE_EMAIL=true to activate)
# =============================================================================
EMAIL__ENABLE_EMAIL=false
EMAIL__SMTP_SERVER=smtp.gmail.com
EMAIL__SMTP_PORT=587
EMAIL__SMTP_USERNAME=your_email@gmail.com
EMAIL__SMTP_PASSWORD=your_app_password_here

# =============================================================================
# Payment Tracking (Optional)
# =============================================================================
PAYMENT__ENABLE_PAYMENT_TRACKING=false
PAYMENT__DEFAULT_PAYMENT_SYSTEM=manual

# =============================================================================
# Storage Settings
# =============================================================================
STORAGE__LOG_FILE_PATH=./receipt_processing_log.json
STORAGE__BACKUP_ENABLED=true

# =============================================================================
# Logging Settings
# =============================================================================
LOGGING__LOG_LEVEL=INFO
LOGGING__LOG_FILE=./logs/receipt-processor.log
"""
    
    output_file = Path(output_path)
    if output_file.exists():
        raise FileExistsError(f"File already exists: {output_path}")
    
    output_file.write_text(env_content)
    logger.info(f"Created default .env file: {output_path}")


def validate_config_file(env_file: str) -> Dict[str, any]:
    """
    Validate a configuration file and return detailed results.
    
    Args:
        env_file: Path to the .env file to validate
    
    Returns:
        Dictionary with validation results
    """
    loader = ConfigLoader()
    
    try:
        settings, warnings = loader.load_with_validation(env_file, create_missing_dirs=False)
        
        return {
            "valid": True,
            "settings": settings.dict(),
            "warnings": warnings,
            "status": loader.get_config_status()
        }
    
    except ConfigurationError as e:
        return {
            "valid": False,
            "error": str(e),
            "status": loader.get_config_status()
        }
