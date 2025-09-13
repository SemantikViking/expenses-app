"""
Configuration management utilities for Receipt Processing Application.

This module provides tools for initializing, validating, and managing
application configuration files.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from .config_loader import ConfigLoader, ConfigurationError


class ConfigManager:
    """Manages configuration files and templates."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / "config"
        self.default_template = self.config_dir / "default.env"
        self.env_example = self.project_root / "env.example"
    
    def init_config(self, output_path: str = ".env", template: str = "default") -> bool:
        """
        Initialize configuration file from template.
        
        Args:
            output_path: Where to create the .env file
            template: Template to use ('default', 'example', or custom path)
        
        Returns:
            True if successful, False otherwise
        """
        output_file = Path(output_path)
        
        # Check if file already exists
        if output_file.exists():
            logger.error(f"Configuration file already exists: {output_path}")
            logger.info("Use --force to overwrite or choose a different path")
            return False
        
        # Determine template source
        if template == "default" and self.default_template.exists():
            template_file = self.default_template
        elif template == "example" and self.env_example.exists():
            template_file = self.env_example
        elif Path(template).exists():
            template_file = Path(template)
        else:
            logger.error(f"Template not found: {template}")
            return False
        
        try:
            # Copy template to output location
            shutil.copy2(template_file, output_file)
            logger.success(f"Created configuration file: {output_path}")
            logger.info(f"Template used: {template_file}")
            
            # Provide next steps
            logger.info("Next steps:")
            logger.info("1. Edit the configuration file and set your API keys")
            logger.info("2. Update the MONITORING__WATCH_FOLDER path")
            logger.info("3. Configure email settings if needed")
            logger.info("4. Run 'receipt-processor validate-config' to verify settings")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create configuration file: {e}")
            return False
    
    def validate_config(self, config_path: str = ".env") -> Dict[str, any]:
        """
        Validate a configuration file.
        
        Args:
            config_path: Path to the configuration file
        
        Returns:
            Validation results dictionary
        """
        if not Path(config_path).exists():
            return {
                "valid": False,
                "error": f"Configuration file not found: {config_path}",
                "suggestions": [
                    "Run 'receipt-processor init' to create a configuration file",
                    "Check that the file path is correct"
                ]
            }
        
        try:
            loader = ConfigLoader()
            settings = loader.load_config(validate=True)
            
            results = {
                "valid": True,
                "config_path": config_path,
                "settings_loaded": True
            }
            
            logger.success("✅ Configuration is valid!")
            return results
            
        except ConfigurationError as e:
            results = {
                "valid": False,
                "error": str(e),
                "suggestions": [
                    "Check that all required settings are provided",
                    "Verify API keys are set correctly",
                    "Ensure file paths exist and are accessible"
                ]
            }
            logger.error("❌ Configuration validation failed:")
            logger.error(str(e))
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to validate configuration: {e}"
            }
    
    def show_config_status(self, config_path: str = ".env") -> Dict[str, any]:
        """
        Show detailed configuration status.
        
        Args:
            config_path: Path to the configuration file
        
        Returns:
            Configuration status information
        """
        loader = ConfigLoader()
        
        try:
            if Path(config_path).exists():
                settings = loader.load_config(validate=True)
                status = loader.get_status()
                
                return {
                    "config_file": config_path,
                    "exists": True,
                    "valid": True,
                    "loaded_files": status["loaded_env_files"],
                    "settings_summary": {
                        "ai_provider": settings.ai_vision.provider,
                        "watch_folder": str(settings.monitoring.watch_folder),
                        "email_enabled": settings.email.enable_email,
                        "payment_tracking": settings.payment.enable_payment_tracking,
                        "log_file": str(settings.storage.log_file_path)
                    }
                }
            else:
                return {
                    "config_file": config_path,
                    "exists": False,
                    "valid": False,
                    "suggestions": [
                        "Run 'receipt-processor init' to create a configuration file"
                    ]
                }
                
        except ConfigurationError as e:
            return {
                "config_file": config_path,
                "exists": Path(config_path).exists(),
                "valid": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "config_file": config_path,
                "exists": Path(config_path).exists(),
                "valid": False,
                "error": str(e)
            }
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        List available configuration templates.
        
        Returns:
            List of available templates with descriptions
        """
        templates = []
        
        if self.default_template.exists():
            templates.append({
                "name": "default",
                "path": str(self.default_template),
                "description": "Comprehensive template with all options and documentation"
            })
        
        if self.env_example.exists():
            templates.append({
                "name": "example",
                "path": str(self.env_example),
                "description": "Simple example template with basic settings"
            })
        
        return templates
    
    def create_custom_template(
        self, 
        template_path: str,
        enable_email: bool = False,
        enable_payment: bool = False,
        ai_provider: str = "openai"
    ) -> bool:
        """
        Create a custom configuration template.
        
        Args:
            template_path: Where to save the custom template
            enable_email: Include email settings
            enable_payment: Include payment settings
            ai_provider: AI provider to configure
        
        Returns:
            True if successful, False otherwise
        """
        try:
            template_content = self._generate_custom_template(
                enable_email=enable_email,
                enable_payment=enable_payment,
                ai_provider=ai_provider
            )
            
            Path(template_path).write_text(template_content)
            logger.success(f"Created custom template: {template_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom template: {e}")
            return False
    
    def _generate_custom_template(
        self,
        enable_email: bool = False,
        enable_payment: bool = False,
        ai_provider: str = "openai"
    ) -> str:
        """Generate custom template content based on options."""
        
        template = f"""# Receipt Processing Application - Custom Configuration
# Generated configuration template

# AI Vision Settings
AI_VISION__PROVIDER={ai_provider}
AI_VISION__MODEL={"gpt-4-vision-preview" if ai_provider == "openai" else "claude-3-vision"}
AI_VISION__API_KEY=your_api_key_here
AI_VISION__CONFIDENCE_THRESHOLD=0.8

# File Monitoring Settings
MONITORING__WATCH_FOLDER=/Users/username/Desktop/Receipts
MONITORING__PROCESSING_INTERVAL=5

# Data Extraction Settings
EXTRACTION__EXTRACT_VENDOR=true
EXTRACTION__EXTRACT_DATE=true
EXTRACTION__EXTRACT_AMOUNT=true
EXTRACTION__DEFAULT_CURRENCY=GBP

"""
        
        if enable_email:
            template += """
# Email Integration Settings
EMAIL__ENABLE_EMAIL=true
EMAIL__SMTP_SERVER=smtp.gmail.com
EMAIL__SMTP_PORT=587
EMAIL__SMTP_USERNAME=your_email@gmail.com
EMAIL__SMTP_PASSWORD=your_app_password_here
EMAIL__DEFAULT_RECIPIENT=accounting@company.com
"""
        
        if enable_payment:
            template += """
# Payment Tracking Settings
PAYMENT__ENABLE_PAYMENT_TRACKING=true
PAYMENT__DEFAULT_PAYMENT_SYSTEM=manual
PAYMENT__AUTO_RECONCILE=false
"""
        
        template += """
# Storage and Logging Settings
STORAGE__LOG_FILE_PATH=./receipt_processing_log.json
LOGGING__LOG_LEVEL=INFO
LOGGING__LOG_FILE=./logs/receipt-processor.log
"""
        
        return template


# Convenience functions
def init_config(output_path: str = ".env", template: str = "default") -> bool:
    """Initialize configuration file from template."""
    manager = ConfigManager()
    return manager.init_config(output_path, template)


def validate_config(config_path: str = ".env") -> Dict[str, any]:
    """Validate configuration file."""
    manager = ConfigManager()
    return manager.validate_config(config_path)


def show_config_status(config_path: str = ".env") -> Dict[str, any]:
    """Show configuration status."""
    manager = ConfigManager()
    return manager.show_config_status(config_path)
