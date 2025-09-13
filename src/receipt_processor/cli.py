"""
Command-line interface for Receipt Processing Application.

This module provides CLI commands for managing configuration, processing receipts,
and monitoring the application status.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from .config_manager import ConfigManager, validate_config, show_config_status
from .config_loader import ConfigurationError


@click.group()
@click.version_option(version="0.1.0", prog_name="receipt-processor")
@click.option(
    "--config", 
    "-c", 
    default=".env", 
    help="Path to configuration file (default: .env)"
)
@click.pass_context
def cli(ctx, config):
    """Receipt Processing Application - AI-powered receipt management."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.group(name="config")
@click.pass_context
def config_group(ctx):
    """Configuration management commands."""
    pass


@config_group.command(name="init")
@click.option(
    "--output", 
    "-o", 
    default=".env", 
    help="Output path for configuration file (default: .env)"
)
@click.option(
    "--template", 
    "-t", 
    default="default", 
    help="Template to use: default, example, or custom path (default: default)"
)
@click.option(
    "--force", 
    is_flag=True, 
    help="Overwrite existing configuration file"
)
@click.option(
    "--email", 
    is_flag=True, 
    help="Enable email integration in template"
)
@click.option(
    "--payment", 
    is_flag=True, 
    help="Enable payment tracking in template"
)
@click.option(
    "--provider", 
    default="openai", 
    type=click.Choice(["openai", "anthropic", "local"]),
    help="AI provider to configure (default: openai)"
)
def init_config(output, template, force, email, payment, provider):
    """Initialize a new configuration file from template."""
    
    config_manager = ConfigManager()
    output_path = Path(output)
    
    # Check if file exists and --force not specified
    if output_path.exists() and not force:
        click.echo(f"❌ Configuration file already exists: {output}")
        click.echo("Use --force to overwrite or choose a different output path")
        sys.exit(1)
    
    # Handle custom template creation
    if email or payment or provider != "openai":
        click.echo("Creating custom template...")
        custom_template = f"{output}.template"
        
        if config_manager.create_custom_template(
            custom_template, 
            enable_email=email,
            enable_payment=payment,
            ai_provider=provider
        ):
            template = custom_template
        else:
            click.echo("❌ Failed to create custom template")
            sys.exit(1)
    
    # Initialize configuration
    if force and output_path.exists():
        output_path.unlink()  # Remove existing file
    
    if config_manager.init_config(output, template):
        click.echo(f"✅ Configuration file created: {output}")
        
        # Show available templates
        templates = config_manager.list_templates()
        if templates:
            click.echo("\n📋 Available templates:")
            for tmpl in templates:
                click.echo(f"  • {tmpl['name']}: {tmpl['description']}")
        
        # Clean up custom template
        if template.endswith(".template"):
            Path(template).unlink()
            
        click.echo(f"\n🔧 Next steps:")
        click.echo("1. Edit the configuration file and set your API keys")
        click.echo("2. Update the MONITORING__WATCH_FOLDER path")
        click.echo("3. Configure email/payment settings if needed")
        click.echo(f"4. Run 'receipt-processor config validate' to verify settings")
        
    else:
        click.echo("❌ Failed to initialize configuration")
        sys.exit(1)


@config_group.command(name="validate")
@click.pass_context
def validate_config_cmd(ctx):
    """Validate the current configuration file."""
    
    config_path = ctx.obj['config_path']
    click.echo(f"🔍 Validating configuration: {config_path}")
    
    results = validate_config(config_path)
    
    if results["valid"]:
        click.echo("✅ Configuration is valid!")
        
        # Show any warnings
        if "warnings" in results and results["warnings"]:
            click.echo("\n⚠️  Warnings:")
            for warning in results["warnings"]:
                click.echo(f"  • {warning}")
    else:
        click.echo("❌ Configuration validation failed:")
        click.echo(f"  Error: {results['error']}")
        
        if "suggestions" in results:
            click.echo("\n💡 Suggestions:")
            for suggestion in results["suggestions"]:
                click.echo(f"  • {suggestion}")
        
        sys.exit(1)


@config_group.command(name="show")
@click.option(
    "--detailed", 
    is_flag=True, 
    help="Show detailed configuration information"
)
@click.pass_context
def show_config_cmd(ctx, detailed):
    """Show current configuration status."""
    
    config_path = ctx.obj['config_path']
    status = show_config_status(config_path)
    
    click.echo(f"📋 Configuration Status: {config_path}")
    click.echo("=" * 50)
    
    # Basic status
    if status["exists"]:
        click.echo("✅ Configuration file exists")
        
        if status["valid"]:
            click.echo("✅ Configuration is valid")
            
            if "settings_summary" in status:
                summary = status["settings_summary"]
                click.echo(f"\n🔧 Settings Summary:")
                click.echo(f"  • AI Provider: {summary['ai_provider']}")
                click.echo(f"  • Watch Folder: {summary['watch_folder']}")
                click.echo(f"  • Email Enabled: {summary['email_enabled']}")
                click.echo(f"  • Payment Tracking: {summary['payment_tracking']}")
                click.echo(f"  • Log File: {summary['log_file']}")
                
        else:
            click.echo("❌ Configuration has errors")
            if "error" in status:
                click.echo(f"  Error: {status['error']}")
    else:
        click.echo("❌ Configuration file not found")
        if "suggestions" in status:
            click.echo("\n💡 Suggestions:")
            for suggestion in status["suggestions"]:
                click.echo(f"  • {suggestion}")
    
    # Detailed information
    if detailed and status.get("valid"):
        if "loaded_files" in status:
            click.echo(f"\n📁 Loaded Files:")
            for file in status["loaded_files"]:
                click.echo(f"  • {file}")
        
        if "warnings" in status and status["warnings"]:
            click.echo(f"\n⚠️  Warnings:")
            for warning in status["warnings"]:
                click.echo(f"  • {warning}")


@config_group.command(name="templates")
def list_templates():
    """List available configuration templates."""
    
    config_manager = ConfigManager()
    templates = config_manager.list_templates()
    
    if templates:
        click.echo("📋 Available Configuration Templates:")
        click.echo("=" * 40)
        
        for template in templates:
            click.echo(f"\n🔧 {template['name']}")
            click.echo(f"   Path: {template['path']}")
            click.echo(f"   Description: {template['description']}")
    else:
        click.echo("❌ No configuration templates found")
        click.echo("Templates should be located in the 'config/' directory")


@cli.command(name="status")
@click.pass_context
def app_status(ctx):
    """Show application status and health check."""
    
    config_path = ctx.obj['config_path']
    
    click.echo("🚀 Receipt Processor - Application Status")
    click.echo("=" * 45)
    
    # Configuration status
    config_status = show_config_status(config_path)
    
    if config_status["exists"] and config_status["valid"]:
        click.echo("✅ Configuration: Valid")
    else:
        click.echo("❌ Configuration: Invalid or missing")
        return
    
    # Check dependencies
    click.echo("\n📦 Dependencies:")
    
    try:
        import pydantic_ai
        click.echo("✅ Pydantic AI: Available")
    except ImportError:
        click.echo("❌ Pydantic AI: Not installed")
    
    try:
        import watchdog
        click.echo("✅ Watchdog: Available") 
    except ImportError:
        click.echo("❌ Watchdog: Not installed")
    
    try:
        from PIL import Image
        click.echo("✅ Pillow: Available")
    except ImportError:
        click.echo("❌ Pillow: Not installed")
    
    # Check directories
    if "settings_summary" in config_status:
        summary = config_status["settings_summary"]
        watch_folder = Path(summary["watch_folder"])
        log_file = Path(summary["log_file"])
        
        click.echo(f"\n📁 Directories:")
        
        if watch_folder.exists():
            click.echo(f"✅ Watch Folder: {watch_folder}")
        else:
            click.echo(f"❌ Watch Folder: {watch_folder} (not found)")
        
        if log_file.parent.exists():
            click.echo(f"✅ Log Directory: {log_file.parent}")
        else:
            click.echo(f"❌ Log Directory: {log_file.parent} (not found)")


@cli.command(name="version")
def version():
    """Show version information."""
    click.echo("Receipt Processor v0.1.0")
    click.echo("AI-powered receipt processing application")
    click.echo("https://github.com/username/receipt-processor")


if __name__ == "__main__":
    cli()
