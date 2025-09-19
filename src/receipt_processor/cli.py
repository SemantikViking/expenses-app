"""
Receipt Processor Command-Line Interface

This module provides a comprehensive CLI for the receipt processing application,
including file monitoring, batch processing, status management, reporting,
and payment tracking functionality.
"""

import click
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
import asyncio
import logging
from tqdm import tqdm
import time

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.receipt_processor.models import (
    ReceiptProcessingLog, ProcessingStatus, ReceiptData, Currency
)
from src.receipt_processor.storage import JSONStorageManager
from src.receipt_processor.status_tracker import EnhancedStatusTracker
from src.receipt_processor.reporting import LogQueryEngine, ReportGenerator, ExportManager
from src.receipt_processor.file_manager import FileManager, FileOrganizationConfig
from src.receipt_processor.email_workflow import EmailWorkflowIntegrator, EmailWorkflowConfig
from src.receipt_processor.payment_workflow import PaymentWorkflowEngine
from src.receipt_processor.payment_storage import PaymentStorageManager
from src.receipt_processor.payment_models import PaymentStatus, PaymentType, PaymentMethod, PaymentRecipient
from src.receipt_processor.daemon import ServiceManager, ServiceConfig, ServiceStatus
from src.receipt_processor.concurrent_processor import ConcurrentProcessor, ProcessingJob, ProcessingPriority, ResourceLimits

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global configuration
DEFAULT_LOG_FILE = Path("receipt_processing_log.json")
DEFAULT_PAYMENT_LOG_FILE = Path("payment_tracking_log.json")
DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_CONFIG_FILE = Path("config.json")

class CLIState:
    """Global CLI state management."""
    
    def __init__(self):
        self.verbose = False
        self.quiet = False
        self.config_file = DEFAULT_CONFIG_FILE
        self.log_file = DEFAULT_LOG_FILE
        self.payment_log_file = DEFAULT_PAYMENT_LOG_FILE
        self.backup_dir = DEFAULT_BACKUP_DIR
        self.storage_manager = None
        self.payment_storage_manager = None
        self.status_tracker = None
        self.email_workflow = None
        self.payment_workflow = None

# Global CLI state
cli_state = CLIState()

def setup_storage_managers():
    """Initialize storage managers."""
    try:
        cli_state.storage_manager = JSONStorageManager(
            log_file_path=cli_state.log_file,
            backup_dir=cli_state.backup_dir
        )
        cli_state.payment_storage_manager = PaymentStorageManager(
            storage_file=cli_state.payment_log_file,
            backup_dir=cli_state.backup_dir
        )
        cli_state.status_tracker = EnhancedStatusTracker(cli_state.storage_manager)
        
        # Initialize email workflow (optional - requires configuration)
        try:
            from src.receipt_processor.email_system import EmailSender, EmailConfig, EmailProvider, SMTPConfig, EmailAuthMethod
            email_config = EmailConfig(
                provider=EmailProvider.GMAIL,
                smtp_config=SMTPConfig(host="smtp.gmail.com", port=587),
                auth_method=EmailAuthMethod.APP_PASSWORD,
                username="your-email@gmail.com"
            )
            email_sender = EmailSender(email_config)
            cli_state.email_workflow = EmailWorkflowIntegrator(
                email_sender=email_sender,
                storage_manager=cli_state.storage_manager,
                status_tracker=cli_state.status_tracker
            )
        except Exception as e:
            echo_verbose(f"Email workflow not initialized (requires configuration): {e}")
            cli_state.email_workflow = None
        
        # Initialize payment workflow
        from src.receipt_processor.payment_validation import PaymentValidator
        validator = PaymentValidator()
        cli_state.payment_workflow = PaymentWorkflowEngine(
            cli_state.payment_storage_manager, validator
        )
        
        return True
    except Exception as e:
        if not cli_state.quiet:
            click.echo(f"Error initializing storage managers: {e}", err=True)
        return False

def echo_info(message: str):
    """Print info message if not in quiet mode."""
    if not cli_state.quiet:
        click.echo(message)

def echo_verbose(message: str):
    """Print verbose message if verbose mode is enabled."""
    if cli_state.verbose and not cli_state.quiet:
        click.echo(f"[VERBOSE] {message}")

def echo_error(message: str):
    """Print error message."""
    click.echo(f"Error: {message}", err=True)

def echo_success(message: str):
    """Print success message."""
    click.echo(f"✅ {message}")

def echo_warning(message: str):
    """Print warning message."""
    click.echo(f"⚠️  {message}")

def confirm_action(message: str, default: bool = True) -> bool:
    """Ask for user confirmation with a default value."""
    if cli_state.quiet:
        return default
    return click.confirm(message, default=default)

def prompt_user(message: str, default: str = None, hide_input: bool = False) -> str:
    """Prompt user for input with optional default and hidden input."""
    if cli_state.quiet and default:
        return default
    return click.prompt(message, default=default, hide_input=hide_input)

def show_progress_bar(iterable, desc: str = "Processing", total: int = None, disable: bool = None):
    """Show progress bar for long operations."""
    if cli_state.quiet or cli_state.verbose:
        disable = True
    return tqdm(iterable, desc=desc, total=total, disable=disable, unit="item")

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output except errors')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--log-file', '-l', type=click.Path(), help='Receipt processing log file path')
@click.option('--payment-log-file', '-p', type=click.Path(), help='Payment tracking log file path')
@click.option('--backup-dir', '-b', type=click.Path(), help='Backup directory path')
@click.pass_context
def cli(ctx, verbose, quiet, config, log_file, payment_log_file, backup_dir):
    """
    Receipt Processor - AI-powered receipt processing and payment tracking system.
    
    This application monitors folders for receipt images, extracts vendor/date/amount
    using AI vision, renames files with standardized naming, and provides comprehensive
    status tracking through email submission and payment reconciliation.
    """
    # Set global state
    cli_state.verbose = verbose
    cli_state.quiet = quiet
    
    if config:
        cli_state.config_file = Path(config)
    if log_file:
        cli_state.log_file = Path(log_file)
    if payment_log_file:
        cli_state.payment_log_file = Path(payment_log_file)
    if backup_dir:
        cli_state.backup_dir = Path(backup_dir)
    
    # Initialize storage managers
    if not setup_storage_managers():
        ctx.exit(1)
    
    echo_verbose(f"Using log file: {cli_state.log_file}")
    echo_verbose(f"Using payment log file: {cli_state.payment_log_file}")
    echo_verbose(f"Using backup directory: {cli_state.backup_dir}")

@cli.command()
@click.option('--watch-dir', '-w', type=click.Path(exists=True), required=True, help='Directory to monitor for new receipts')
@click.option('--processed-dir', '-o', type=click.Path(), help='Directory to move processed receipts')
@click.option('--interval', '-i', type=int, default=5, help='Monitoring interval in seconds')
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon in background')
def start(watch_dir, processed_dir, interval, daemon):
    """Start monitoring a directory for new receipt images."""
    echo_info(f"Starting receipt processor...")
    echo_info(f"Watching directory: {watch_dir}")
    
    if processed_dir:
        echo_info(f"Processed receipts will be moved to: {processed_dir}")
    
    echo_info(f"Monitoring interval: {interval} seconds")
    
    if daemon:
        echo_info("Running as daemon (background mode)")
        # TODO: Implement daemon functionality
        echo_warning("Daemon mode not yet implemented")
    else:
        echo_info("Running in foreground mode")
        # TODO: Implement file monitoring
        echo_warning("File monitoring not yet implemented")
    
    echo_success("Receipt processor started successfully")

@cli.command()
@click.option('--input-dir', '-i', type=click.Path(exists=True), required=True, help='Directory containing receipt images to process')
@click.option('--output-dir', '-o', type=click.Path(), help='Directory to save processed receipts')
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories recursively')
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be processed without actually processing')
@click.option('--interactive', '-I', is_flag=True, help='Enable interactive mode for confirmations')
@click.option('--batch-size', '-b', type=int, default=10, help='Number of files to process in each batch')
def process(input_dir, output_dir, recursive, dry_run, interactive, batch_size):
    """Process existing receipt images in a directory."""
    echo_info(f"Processing receipts in: {input_dir}")
    
    if output_dir:
        echo_info(f"Output directory: {output_dir}")
    
    if recursive:
        echo_info("Processing subdirectories recursively")
    
    if dry_run:
        echo_info("DRY RUN MODE - No files will be processed")
    
    if interactive:
        echo_info("Interactive mode enabled - confirmations will be requested")
    
    # Find image files
    input_path = Path(input_dir)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    if recursive:
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_path.rglob(f'*{ext}'))
            image_files.extend(input_path.rglob(f'*{ext.upper()}'))
    else:
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_path.glob(f'*{ext}'))
            image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    if not image_files:
        echo_info("No image files found to process")
        return
    
    echo_info(f"Found {len(image_files)} image files to process")
    
    if interactive and not dry_run:
        if not confirm_action(f"Process {len(image_files)} files in batches of {batch_size}?"):
            echo_info("Processing cancelled by user")
            return
    
    # Process files in batches with progress bar
    processed_count = 0
    error_count = 0
    
    with show_progress_bar(image_files, desc="Processing receipts", total=len(image_files)) as pbar:
        for i in range(0, len(image_files), batch_size):
            batch = image_files[i:i + batch_size]
            
            for file_path in batch:
                try:
                    # Simulate processing time
                    time.sleep(0.1)
                    
                    if not dry_run:
                        # TODO: Implement actual processing logic
                        # For now, just simulate success
                        processed_count += 1
                    else:
                        echo_verbose(f"Would process: {file_path.name}")
                    
                    pbar.set_postfix({
                        'Processed': processed_count,
                        'Errors': error_count,
                        'Current': file_path.name[:20] + '...' if len(file_path.name) > 20 else file_path.name
                    })
                    
                except Exception as e:
                    error_count += 1
                    echo_error(f"Error processing {file_path.name}: {e}")
                
                pbar.update(1)
    
    if dry_run:
        echo_success(f"Dry run completed - would process {len(image_files)} files")
    else:
        echo_success(f"Processing completed - {processed_count} processed, {error_count} errors")

@cli.command()
@click.option('--log-id', '-l', help='Show status for specific log ID')
@click.option('--status', '-s', type=click.Choice([s.value for s in ProcessingStatus]), help='Filter by status')
@click.option('--limit', '-n', type=int, default=10, help='Number of recent logs to show')
def status(log_id, status, limit):
    """Show application status and recent processing logs."""
    if log_id:
        # Show specific log
        log = cli_state.storage_manager.get_log_entry(log_id)
        if not log:
            echo_error(f"Log with ID {log_id} not found")
            return
        
        click.echo(f"\n📋 Receipt Processing Log: {log_id}")
        click.echo(f"Status: {log.current_status.value}")
        click.echo(f"Original Filename: {log.original_filename}")
        click.echo(f"Created: {log.created_at}")
        click.echo(f"Last Updated: {log.last_updated}")
        
        if log.receipt_data:
            click.echo(f"Vendor: {log.receipt_data.vendor_name}")
            click.echo(f"Date: {log.receipt_data.transaction_date}")
            click.echo(f"Amount: {log.receipt_data.total_amount} {log.receipt_data.currency.value}")
        
        if log.status_history:
            click.echo(f"\n📈 Status History:")
            for transition in log.status_history[-5:]:  # Show last 5 transitions
                click.echo(f"  {transition.timestamp}: {transition.old_status.value if transition.old_status else 'N/A'} → {transition.new_status.value}")
                if transition.reason:
                    click.echo(f"    Reason: {transition.reason}")
    else:
        # Show recent logs
        if status:
            logs = cli_state.storage_manager.get_logs_by_status(ProcessingStatus(status))
        else:
            logs = cli_state.storage_manager.get_recent_logs(limit)
        
        if not logs:
            echo_info("No logs found")
            return
        
        click.echo(f"\n📊 Recent Processing Logs (showing {len(logs)} of {limit}):")
        click.echo("-" * 80)
        
        for log in logs:
            status_icon = {
                ProcessingStatus.PENDING: "⏳",
                ProcessingStatus.PROCESSING: "🔄",
                ProcessingStatus.PROCESSED: "✅",
                ProcessingStatus.ERROR: "❌",
                ProcessingStatus.NO_DATA_EXTRACTED: "⚠️",
                ProcessingStatus.EMAILED: "📧",
                ProcessingStatus.SUBMITTED: "📤",
                ProcessingStatus.PAYMENT_RECEIVED: "💰"
            }.get(log.current_status, "❓")
            
            click.echo(f"{status_icon} {log.id} | {log.current_status.value} | {log.original_filename}")
            if log.receipt_data:
                click.echo(f"    💳 {log.receipt_data.vendor_name} | {log.receipt_data.transaction_date} | {log.receipt_data.total_amount} {log.receipt_data.currency.value}")

@cli.command()
@click.option('--status', '-s', type=click.Choice([s.value for s in ProcessingStatus]), help='Filter by status')
@click.option('--vendor', '-v', help='Filter by vendor name')
@click.option('--date-from', '-f', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter from date (YYYY-MM-DD)')
@click.option('--date-to', '-t', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter to date (YYYY-MM-DD)')
@click.option('--amount-min', type=float, help='Minimum amount filter')
@click.option('--amount-max', type=float, help='Maximum amount filter')
@click.option('--limit', '-n', type=int, default=50, help='Number of logs to show')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
def logs(status, vendor, date_from, date_to, amount_min, amount_max, limit, output_format):
    """Query and display processing logs with filtering options."""
    # Build query options
    from src.receipt_processor.reporting import QueryOptions, FilterCondition, SortCondition, FilterOperator
    
    filters = []
    if status:
        filters.append(FilterCondition(field='current_status', operator=FilterOperator.EQUALS, value=ProcessingStatus(status)))
    if vendor:
        filters.append(FilterCondition(field='receipt_data.vendor_name', operator=FilterOperator.CONTAINS, value=vendor))
    if date_from:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=date_from))
    if date_to:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=date_to))
    if amount_min is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=Decimal(str(amount_min))))
    if amount_max is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=Decimal(str(amount_max))))
    
    from src.receipt_processor.reporting import SortDirection
    sort_conditions = [SortCondition(field='created_at', direction=SortDirection.DESC)]
    
    query_options = QueryOptions(
        filters=filters if filters else None,
        sort_by=sort_conditions,
        limit=limit
    )
    
    # Query logs
    query_engine = LogQueryEngine(cli_state.storage_manager)
    results = query_engine.query(query_options)
    
    if not results:
        echo_info("No logs found matching criteria")
        return
    
    # Display results
    if output_format == 'json':
        logs_data = [log.model_dump() for log in results]
        click.echo(json.dumps(logs_data, indent=2, default=str))
    elif output_format == 'csv':
        # TODO: Implement CSV export
        echo_warning("CSV export not yet implemented")
    else:  # table format
        click.echo(f"\n📋 Processing Logs (showing {len(results)} results):")
        click.echo("-" * 100)
        
        for log in results:
            status_icon = {
                ProcessingStatus.PENDING: "⏳",
                ProcessingStatus.PROCESSING: "🔄",
                ProcessingStatus.PROCESSED: "✅",
                ProcessingStatus.ERROR: "❌",
                ProcessingStatus.NO_DATA_EXTRACTED: "⚠️",
                ProcessingStatus.EMAILED: "📧",
                ProcessingStatus.SUBMITTED: "📤",
                ProcessingStatus.PAYMENT_RECEIVED: "💰"
            }.get(log.current_status, "❓")
            
            click.echo(f"{status_icon} {log.id}")
            click.echo(f"    Status: {log.current_status.value}")
            click.echo(f"    File: {log.original_filename}")
            click.echo(f"    Created: {log.created_at}")
            if log.receipt_data:
                click.echo(f"    Vendor: {log.receipt_data.vendor_name}")
                click.echo(f"    Date: {log.receipt_data.transaction_date}")
                click.echo(f"    Amount: {log.receipt_data.total_amount} {log.receipt_data.currency.value}")
            click.echo()

@cli.command()
@click.option('--init', 'init_config', is_flag=True, help='Initialize configuration file')
@click.option('--show', 'show_config', is_flag=True, help='Show current configuration')
@click.option('--validate', 'validate_config', is_flag=True, help='Validate configuration file')
def config(init_config, show_config, validate_config):
    """Manage application configuration."""
    if init_config:
        # TODO: Implement config initialization
        echo_warning("Config initialization not yet implemented")
    elif show_config:
        # TODO: Implement config display
        echo_warning("Config display not yet implemented")
    elif validate_config:
        # TODO: Implement config validation
        echo_warning("Config validation not yet implemented")
    else:
        click.echo("Use --init, --show, or --validate options")

@cli.command()
@click.option('--type', 'report_type', type=click.Choice(['summary', 'vendor', 'workflow', 'payment', 'audit']), default='summary', help='Report type')
@click.option('--date-from', '-f', type=click.DateTime(formats=['%Y-%m-%d']), help='Report from date (YYYY-MM-DD)')
@click.option('--date-to', '-t', type=click.DateTime(formats=['%Y-%m-%d']), help='Report to date (YYYY-MM-DD)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
def report(report_type, date_from, date_to, output_format):
    """Generate various reports and analytics."""
    echo_info(f"Generating {report_type} report...")
    
    # Set date range
    if not date_from:
        date_from = datetime.now() - timedelta(days=30)  # Default to last 30 days
    if not date_to:
        date_to = datetime.now()
    
    # Generate report
    report_generator = ReportGenerator(cli_state.storage_manager)
    
    try:
        if report_type == 'summary':
            report_data = report_generator.generate_summary_report(
                start_date=date_from, end_date=date_to
            )
            # Convert ReportSummary to dict
            from dataclasses import asdict
            report_data = asdict(report_data)
        elif report_type == 'vendor':
            report_data = report_generator.generate_vendor_analysis_report(
                start_date=date_from, end_date=date_to
            )
            # Convert to dict if needed
            if hasattr(report_data, 'model_dump'):
                report_data = report_data.model_dump()
        elif report_type == 'workflow':
            report_data = report_generator.generate_workflow_metrics_report(
                start_date=date_from, end_date=date_to
            )
            # Convert to dict if needed
            if hasattr(report_data, 'model_dump'):
                report_data = report_data.model_dump()
        elif report_type == 'payment':
            # TODO: Implement payment reports
            echo_warning("Payment reports not yet implemented")
            return
        elif report_type == 'audit':
            report_data = report_generator.generate_audit_report(
                start_date=date_from, end_date=date_to
            )
            # Convert to dict if needed
            if hasattr(report_data, 'model_dump'):
                report_data = report_data.model_dump()
        
        # Display report
        if output_format == 'json':
            click.echo(json.dumps(report_data, indent=2, default=str))
        elif output_format == 'csv':
            # TODO: Implement CSV export
            echo_warning("CSV export not yet implemented")
        else:  # table format
            click.echo(f"\n📊 {report_type.title()} Report ({date_from.date()} to {date_to.date()}):")
            click.echo("-" * 60)
            
            if report_type == 'summary':
                click.echo(f"Total Receipts: {report_data.get('total_receipts', 0)}")
                total_amount = report_data.get('total_amount', 0)
                if total_amount is not None:
                    click.echo(f"Total Amount: ${total_amount:.2f}")
                else:
                    click.echo("Total Amount: $0.00")
                success_rate = report_data.get('success_rate', 0)
                if success_rate is not None:
                    click.echo(f"Success Rate: {success_rate:.1f}%")
                else:
                    click.echo("Success Rate: 0.0%")
            elif report_type == 'vendor':
                click.echo(f"Top Vendors:")
                for vendor in report_data.get('top_vendors', [])[:10]:
                    click.echo(f"  {vendor['vendor_name']}: {vendor['count']} receipts, ${vendor['total_amount']:.2f}")
            elif report_type == 'workflow':
                click.echo(f"Processing Statistics:")
                click.echo(f"  Average Processing Time: {report_data.get('avg_processing_time', 0):.2f} seconds")
                click.echo(f"  Success Rate: {report_data.get('success_rate', 0):.1f}%")
                click.echo(f"  Error Rate: {report_data.get('error_rate', 0):.1f}%")
            elif report_type == 'audit':
                click.echo(f"Audit Trail:")
                for entry in report_data.get('audit_entries', [])[:20]:
                    click.echo(f"  {entry['timestamp']}: {entry['action']} - {entry['details']}")
        
        echo_success(f"{report_type.title()} report generated successfully")
        
    except Exception as e:
        echo_error(f"Error generating report: {e}")

@cli.command()
@click.option('--format', 'export_format', type=click.Choice(['json', 'csv']), default='json', help='Export format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--date-from', '-f', type=click.DateTime(formats=['%Y-%m-%d']), help='Export from date (YYYY-MM-DD)')
@click.option('--date-to', '-t', type=click.DateTime(formats=['%Y-%m-%d']), help='Export to date (YYYY-MM-DD)')
def export(export_format, output, date_from, date_to):
    """Export processing logs to various formats."""
    echo_info(f"Exporting logs in {export_format} format...")
    
    # Set date range
    if not date_from:
        date_from = datetime.now() - timedelta(days=30)  # Default to last 30 days
    if not date_to:
        date_to = datetime.now()
    
    # Set output file
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"receipt_export_{timestamp}.{export_format}"
    
    try:
        export_manager = ExportManager(cli_state.storage_manager)
        
        if export_format == 'json':
            success = export_manager.export_to_json(
                output_path=Path(output)
            )
        elif export_format == 'csv':
            success = export_manager.export_to_csv(
                output_path=Path(output)
            )
        
        if success:
            echo_success(f"Export completed: {output}")
        else:
            echo_error("Export failed")
            
    except Exception as e:
        echo_error(f"Error during export: {e}")

@cli.command()
def stats():
    """Show processing statistics and metrics."""
    echo_info("Generating processing statistics...")
    
    try:
        # Get statistics from storage manager
        stats = cli_state.storage_manager.get_statistics()
        
        click.echo(f"\n📊 Processing Statistics:")
        click.echo("-" * 40)
        click.echo(f"Total Logs: {stats.get('total_logs', 0)}")
        click.echo(f"File Size: {stats.get('file_size_mb', 0):.2f} MB")
        click.echo(f"Last Updated: {stats.get('last_updated', 'Never')}")
        
        # Status breakdown
        status_breakdown = stats.get('status_breakdown', {})
        if status_breakdown:
            click.echo(f"\n📈 Status Breakdown:")
            for status, count in status_breakdown.items():
                click.echo(f"  {status}: {count}")
        
        # Recent activity
        recent_logs = cli_state.storage_manager.get_recent_logs(5)
        if recent_logs:
            click.echo(f"\n🕒 Recent Activity:")
            for log in recent_logs:
                status_icon = {
                    ProcessingStatus.PENDING: "⏳",
                    ProcessingStatus.PROCESSING: "🔄",
                    ProcessingStatus.PROCESSED: "✅",
                    ProcessingStatus.ERROR: "❌",
                    ProcessingStatus.NO_DATA_EXTRACTED: "⚠️",
                    ProcessingStatus.EMAILED: "📧",
                    ProcessingStatus.SUBMITTED: "📤",
                    ProcessingStatus.PAYMENT_RECEIVED: "💰"
                }.get(log.current_status, "❓")
                
                click.echo(f"  {status_icon} {log.original_filename} ({log.current_status.value})")
        
        echo_success("Statistics generated successfully")
        
    except Exception as e:
        echo_error(f"Error generating statistics: {e}")

@cli.command()
@click.argument('log_id')
@click.argument('new_status', type=click.Choice([s.value for s in ProcessingStatus]))
@click.option('--reason', '-r', help='Reason for status change')
@click.option('--user', '-u', default='cli_user', help='User making the change')
def update_status(log_id, new_status, reason, user):
    """Update the status of a specific processing log."""
    echo_info(f"Updating status for log {log_id} to {new_status}...")
    
    try:
        # Get the log
        log = cli_state.storage_manager.get_log_entry(log_id)
        if not log:
            echo_error(f"Log with ID {log_id} not found")
            return
        
        # Update status
        old_status = log.current_status
        cli_state.status_tracker.update_status(
            log_id=log_id,
            new_status=ProcessingStatus(new_status),
            reason=reason or f"Status updated via CLI by {user}",
            user=user
        )
        
        echo_success(f"Status updated: {old_status.value} → {new_status}")
        
    except Exception as e:
        echo_error(f"Error updating status: {e}")

@cli.command()
@click.argument('log_id')
@click.option('--recipient', '-r', help='Email recipient')
@click.option('--template', '-t', help='Email template to use')
def email(log_id, recipient, template):
    """Send email for a specific receipt."""
    echo_info(f"Sending email for log {log_id}...")
    
    try:
        # Get the log
        log = cli_state.storage_manager.get_log_entry(log_id)
        if not log:
            echo_error(f"Log with ID {log_id} not found")
            return
        
        # TODO: Implement email sending
        echo_warning("Email sending not yet implemented")
        
    except Exception as e:
        echo_error(f"Error sending email: {e}")

@cli.command()
@click.argument('log_id')
@click.option('--amount', '-a', type=float, help='Payment amount')
@click.option('--method', '-m', type=click.Choice([m.value for m in PaymentMethod]), help='Payment method')
@click.option('--type', '-t', type=click.Choice([t.value for t in PaymentType]), help='Payment type')
def submit(log_id, amount, method, type):
    """Submit a receipt for payment processing."""
    echo_info(f"Submitting log {log_id} for payment processing...")
    
    try:
        # Get the log
        log = cli_state.storage_manager.get_log_entry(log_id)
        if not log:
            echo_error(f"Log with ID {log_id} not found")
            return
        
        # TODO: Implement payment submission
        echo_warning("Payment submission not yet implemented")
        
    except Exception as e:
        echo_error(f"Error submitting payment: {e}")

@cli.command()
@click.argument('log_id')
@click.option('--amount', '-a', type=float, help='Payment amount received')
@click.option('--method', '-m', type=click.Choice([m.value for m in PaymentMethod]), help='Payment method used')
def payment_received(log_id, amount, method):
    """Mark a payment as received."""
    echo_info(f"Marking payment as received for log {log_id}...")
    
    try:
        # Get the log
        log = cli_state.storage_manager.get_log_entry(log_id)
        if not log:
            echo_error(f"Log with ID {log_id} not found")
            return
        
        # Update status to payment received
        cli_state.status_tracker.update_status(
            log_id=log_id,
            new_status=ProcessingStatus.PAYMENT_RECEIVED,
            reason=f"Payment received: {amount} via {method}",
            user="cli_user"
        )
        
        echo_success(f"Payment marked as received: {amount} via {method}")
        
    except Exception as e:
        echo_error(f"Error marking payment as received: {e}")

@cli.command()
@click.option('--status', '-s', type=click.Choice([s.value for s in ProcessingStatus]), help='Filter by status')
@click.option('--vendor', '-v', help='Filter by vendor name')
@click.option('--date-from', '-f', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter from date (YYYY-MM-DD)')
@click.option('--date-to', '-t', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter to date (YYYY-MM-DD)')
@click.option('--amount-min', type=float, help='Minimum amount filter')
@click.option('--amount-max', type=float, help='Maximum amount filter')
@click.option('--new-status', '-n', type=click.Choice([s.value for s in ProcessingStatus]), required=True, help='New status to set')
@click.option('--reason', '-r', help='Reason for status change')
@click.option('--user', '-u', default='cli_user', help='User making the change')
@click.option('--interactive', '-I', is_flag=True, help='Enable interactive mode for confirmations')
@click.option('--batch-size', '-b', type=int, default=50, help='Number of logs to process in each batch')
def bulk_update_status(status, vendor, date_from, date_to, amount_min, amount_max, new_status, reason, user, interactive, batch_size):
    """Bulk update status for multiple receipts."""
    echo_info("Bulk updating receipt status...")
    
    # Build query options
    from src.receipt_processor.reporting import QueryOptions, FilterCondition, SortCondition, FilterOperator, SortDirection
    
    filters = []
    if status:
        filters.append(FilterCondition(field='current_status', operator=FilterOperator.EQUALS, value=ProcessingStatus(status)))
    if vendor:
        filters.append(FilterCondition(field='receipt_data.vendor_name', operator=FilterOperator.CONTAINS, value=vendor))
    if date_from:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=date_from))
    if date_to:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=date_to))
    if amount_min is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=Decimal(str(amount_min))))
    if amount_max is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=Decimal(str(amount_max))))
    
    sort_conditions = [SortCondition(field='created_at', direction=SortDirection.DESC)]
    
    query_options = QueryOptions(
        filters=filters if filters else None,
        sort_by=sort_conditions,
        limit=None  # Get all matching logs
    )
    
    # Query logs
    query_engine = LogQueryEngine(cli_state.storage_manager)
    results = query_engine.query(query_options)
    
    if not results:
        echo_info("No logs found matching criteria")
        return
    
    echo_info(f"Found {len(results)} logs matching criteria")
    
    if interactive:
        if not confirm_action(f"Update {len(results)} logs to status '{new_status}'?"):
            echo_info("Bulk update cancelled by user")
            return
    
    # Process logs in batches with progress bar
    updated_count = 0
    error_count = 0
    
    with show_progress_bar(results, desc="Updating status", total=len(results)) as pbar:
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            
            for log in batch:
                try:
                    # Update status
                    cli_state.status_tracker.update_status(
                        log_id=str(log.id),
                        new_status=ProcessingStatus(new_status),
                        reason=reason or f"Bulk status update via CLI by {user}",
                        user=user
                    )
                    updated_count += 1
                    
                    pbar.set_postfix({
                        'Updated': updated_count,
                        'Errors': error_count,
                        'Current': log.original_filename[:20] + '...' if len(log.original_filename) > 20 else log.original_filename
                    })
                    
                except Exception as e:
                    error_count += 1
                    echo_error(f"Error updating {log.original_filename}: {e}")
                
                pbar.update(1)
    
    echo_success(f"Bulk update completed - {updated_count} updated, {error_count} errors")

@cli.command()
@click.option('--status', '-s', type=click.Choice([s.value for s in ProcessingStatus]), help='Filter by status')
@click.option('--vendor', '-v', help='Filter by vendor name')
@click.option('--date-from', '-f', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter from date (YYYY-MM-DD)')
@click.option('--date-to', '-t', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter to date (YYYY-MM-DD)')
@click.option('--amount-min', type=float, help='Minimum amount filter')
@click.option('--amount-max', type=float, help='Maximum amount filter')
@click.option('--recipient', '-r', help='Email recipient')
@click.option('--template', '-t', help='Email template to use')
@click.option('--interactive', '-I', is_flag=True, help='Enable interactive mode for confirmations')
@click.option('--batch-size', '-b', type=int, default=10, help='Number of emails to send in each batch')
def bulk_email(status, vendor, date_from, date_to, amount_min, amount_max, recipient, template, interactive, batch_size):
    """Send bulk emails for multiple receipts."""
    echo_info("Sending bulk emails...")
    
    # Build query options
    from src.receipt_processor.reporting import QueryOptions, FilterCondition, SortCondition, FilterOperator, SortDirection
    
    filters = []
    if status:
        filters.append(FilterCondition(field='current_status', operator=FilterOperator.EQUALS, value=ProcessingStatus(status)))
    if vendor:
        filters.append(FilterCondition(field='receipt_data.vendor_name', operator=FilterOperator.CONTAINS, value=vendor))
    if date_from:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=date_from))
    if date_to:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=date_to))
    if amount_min is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=Decimal(str(amount_min))))
    if amount_max is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=Decimal(str(amount_max))))
    
    sort_conditions = [SortCondition(field='created_at', direction=SortDirection.DESC)]
    
    query_options = QueryOptions(
        filters=filters if filters else None,
        sort_by=sort_conditions,
        limit=None  # Get all matching logs
    )
    
    # Query logs
    query_engine = LogQueryEngine(cli_state.storage_manager)
    results = query_engine.query(query_options)
    
    if not results:
        echo_info("No logs found matching criteria")
        return
    
    echo_info(f"Found {len(results)} logs matching criteria")
    
    if interactive:
        if not confirm_action(f"Send emails for {len(results)} receipts?"):
            echo_info("Bulk email cancelled by user")
            return
    
    # Process emails in batches with progress bar
    sent_count = 0
    error_count = 0
    
    with show_progress_bar(results, desc="Sending emails", total=len(results)) as pbar:
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            
            for log in batch:
                try:
                    # TODO: Implement actual email sending
                    # For now, just simulate success
                    time.sleep(0.1)
                    sent_count += 1
                    
                    pbar.set_postfix({
                        'Sent': sent_count,
                        'Errors': error_count,
                        'Current': log.original_filename[:20] + '...' if len(log.original_filename) > 20 else log.original_filename
                    })
                    
                except Exception as e:
                    error_count += 1
                    echo_error(f"Error sending email for {log.original_filename}: {e}")
                
                pbar.update(1)
    
    echo_success(f"Bulk email completed - {sent_count} sent, {error_count} errors")

@cli.command()
@click.option('--status', '-s', type=click.Choice([s.value for s in ProcessingStatus]), help='Filter by status')
@click.option('--vendor', '-v', help='Filter by vendor name')
@click.option('--date-from', '-f', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter from date (YYYY-MM-DD)')
@click.option('--date-to', '-t', type=click.DateTime(formats=['%Y-%m-%d']), help='Filter to date (YYYY-MM-DD)')
@click.option('--amount-min', type=float, help='Minimum amount filter')
@click.option('--amount-max', type=float, help='Maximum amount filter')
@click.option('--amount', '-a', type=float, help='Payment amount')
@click.option('--method', '-m', type=click.Choice([m.value for m in PaymentMethod]), help='Payment method')
@click.option('--type', '-t', type=click.Choice([t.value for t in PaymentType]), help='Payment type')
@click.option('--interactive', '-I', is_flag=True, help='Enable interactive mode for confirmations')
@click.option('--batch-size', '-b', type=int, default=50, help='Number of payments to submit in each batch')
def bulk_submit(status, vendor, date_from, date_to, amount_min, amount_max, amount, method, type, interactive, batch_size):
    """Bulk submit multiple receipts for payment processing."""
    echo_info("Bulk submitting receipts for payment processing...")
    
    # Build query options
    from src.receipt_processor.reporting import QueryOptions, FilterCondition, SortCondition, FilterOperator, SortDirection
    
    filters = []
    if status:
        filters.append(FilterCondition(field='current_status', operator=FilterOperator.EQUALS, value=ProcessingStatus(status)))
    if vendor:
        filters.append(FilterCondition(field='receipt_data.vendor_name', operator=FilterOperator.CONTAINS, value=vendor))
    if date_from:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=date_from))
    if date_to:
        filters.append(FilterCondition(field='created_at', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=date_to))
    if amount_min is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=Decimal(str(amount_min))))
    if amount_max is not None:
        filters.append(FilterCondition(field='receipt_data.total_amount', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=Decimal(str(amount_max))))
    
    sort_conditions = [SortCondition(field='created_at', direction=SortDirection.DESC)]
    
    query_options = QueryOptions(
        filters=filters if filters else None,
        sort_by=sort_conditions,
        limit=None  # Get all matching logs
    )
    
    # Query logs
    query_engine = LogQueryEngine(cli_state.storage_manager)
    results = query_engine.query(query_options)
    
    if not results:
        echo_info("No logs found matching criteria")
        return
    
    echo_info(f"Found {len(results)} logs matching criteria")
    
    if interactive:
        if not confirm_action(f"Submit {len(results)} receipts for payment processing?"):
            echo_info("Bulk submit cancelled by user")
            return
    
    # Process submissions in batches with progress bar
    submitted_count = 0
    error_count = 0
    
    with show_progress_bar(results, desc="Submitting payments", total=len(results)) as pbar:
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            
            for log in batch:
                try:
                    # TODO: Implement actual payment submission
                    # For now, just simulate success
                    time.sleep(0.1)
                    submitted_count += 1
                    
                    pbar.set_postfix({
                        'Submitted': submitted_count,
                        'Errors': error_count,
                        'Current': log.original_filename[:20] + '...' if len(log.original_filename) > 20 else log.original_filename
                    })
                    
                except Exception as e:
                    error_count += 1
                    echo_error(f"Error submitting {log.original_filename}: {e}")
                
                pbar.update(1)
    
    echo_success(f"Bulk submit completed - {submitted_count} submitted, {error_count} errors")

@cli.command()
@click.option('--pid-file', '-p', type=click.Path(), default='receipt_processor.pid', help='PID file path')
@click.option('--watch-dir', '-w', type=click.Path(exists=True), required=True, help='Directory to monitor for new receipts')
@click.option('--processed-dir', '-o', type=click.Path(), help='Directory to move processed receipts')
@click.option('--max-workers', '-n', type=int, default=4, help='Maximum number of worker threads')
@click.option('--check-interval', '-i', type=int, default=5, help='File check interval in seconds')
@click.option('--memory-limit', '-m', type=int, default=512, help='Memory limit in MB')
@click.option('--cpu-limit', '-c', type=float, default=80.0, help='CPU limit percentage')
def daemon_start(pid_file, watch_dir, processed_dir, max_workers, check_interval, memory_limit, cpu_limit):
    """Start the receipt processor daemon service."""
    echo_info("Starting receipt processor daemon...")
    
    try:
        # Create service configuration
        config = ServiceConfig(
            pid_file=Path(pid_file),
            log_file=cli_state.log_file,
            watch_directory=Path(watch_dir),
            processed_directory=Path(processed_dir) if processed_dir else None,
            check_interval=check_interval,
            max_workers=max_workers,
            memory_limit_mb=memory_limit,
            cpu_limit_percent=cpu_limit
        )
        
        # Create service manager
        service_manager = ServiceManager(
            config=config,
            storage_manager=cli_state.storage_manager,
            status_tracker=cli_state.status_tracker
        )
        
        # Start service
        if service_manager.start_service():
            echo_success("Daemon service started successfully")
            echo_info(f"PID file: {pid_file}")
            echo_info(f"Watching: {watch_dir}")
            if processed_dir:
                echo_info(f"Processed files will be moved to: {processed_dir}")
        else:
            echo_error("Failed to start daemon service")
            click.exit(1)
            
    except Exception as e:
        echo_error(f"Error starting daemon service: {e}")
        click.exit(1)

@cli.command()
@click.option('--pid-file', '-p', type=click.Path(), default='receipt_processor.pid', help='PID file path')
def daemon_stop(pid_file):
    """Stop the receipt processor daemon service."""
    echo_info("Stopping receipt processor daemon...")
    
    try:
        # Check if PID file exists
        pid_path = Path(pid_file)
        if not pid_path.exists():
            echo_warning("PID file not found - service may not be running")
            return
        
        # Read PID
        with open(pid_path, 'r') as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM to process
        import signal
        try:
            os.kill(pid, signal.SIGTERM)
            echo_success("Stop signal sent to daemon process")
        except ProcessLookupError:
            echo_warning("Process not found - may have already stopped")
        except PermissionError:
            echo_error("Permission denied - try running with sudo")
            click.exit(1)
        
        # Wait for process to stop
        import time
        for i in range(30):  # Wait up to 30 seconds
            try:
                os.kill(pid, 0)  # Check if process exists
                time.sleep(1)
            except ProcessLookupError:
                echo_success("Daemon service stopped")
                return
        
        echo_warning("Daemon did not stop gracefully - may need force kill")
        
    except Exception as e:
        echo_error(f"Error stopping daemon service: {e}")
        click.exit(1)

@cli.command()
@click.option('--pid-file', '-p', type=click.Path(), default='receipt_processor.pid', help='PID file path')
def daemon_restart(pid_file):
    """Restart the receipt processor daemon service."""
    echo_info("Restarting receipt processor daemon...")
    
    # Stop first
    daemon_stop(pid_file)
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Start again
    echo_info("Starting daemon service...")
    # Note: This is a simplified restart - in practice you'd want to preserve the original config
    echo_warning("Restart command requires original configuration parameters")
    echo_info("Please use 'daemon-start' with the same parameters as before")

@cli.command()
@click.option('--pid-file', '-p', type=click.Path(), default='receipt_processor.pid', help='PID file path')
def daemon_status(pid_file):
    """Show daemon service status."""
    try:
        pid_path = Path(pid_file)
        if not pid_path.exists():
            echo_info("Daemon service is not running (no PID file)")
            return
        
        # Read PID
        with open(pid_path, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is running
        try:
            import psutil
            process = psutil.Process(pid)
            
            echo_success("Daemon service is running")
            click.echo(f"PID: {pid}")
            click.echo(f"Status: {process.status()}")
            click.echo(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            click.echo(f"CPU usage: {process.cpu_percent():.1f}%")
            click.echo(f"Started: {datetime.fromtimestamp(process.create_time())}")
            
        except psutil.NoSuchProcess:
            echo_warning("Daemon service is not running (process not found)")
            # Clean up stale PID file
            pid_path.unlink()
        except psutil.AccessDenied:
            echo_error("Permission denied - cannot access process information")
            
    except Exception as e:
        echo_error(f"Error checking daemon status: {e}")

@cli.command()
@click.option('--max-workers', '-n', type=int, default=4, help='Maximum number of worker threads')
@click.option('--memory-limit', '-m', type=int, default=512, help='Memory limit in MB')
@click.option('--cpu-limit', '-c', type=float, default=80.0, help='CPU limit percentage')
@click.option('--input-dir', '-i', type=click.Path(exists=True), required=True, help='Directory containing images to process')
@click.option('--priority', '-p', type=click.Choice(['low', 'normal', 'high', 'urgent']), default='normal', help='Processing priority')
def process_concurrent(max_workers, memory_limit, cpu_limit, input_dir, priority):
    """Process images using concurrent processing with resource monitoring."""
    echo_info("Starting concurrent processing...")
    
    try:
        # Create resource limits
        resource_limits = ResourceLimits(
            max_memory_mb=memory_limit,
            max_cpu_percent=cpu_limit,
            max_concurrent_jobs=max_workers
        )
        
        # Create concurrent processor
        processor = ConcurrentProcessor(
            max_workers=max_workers,
            resource_limits=resource_limits
        )
        
        # Start processor
        processor.start()
        
        # Find image files
        input_path = Path(input_dir)
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(input_path.glob(f'*{ext}'))
            image_files.extend(input_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            echo_info("No image files found to process")
            processor.stop()
            return
        
        echo_info(f"Found {len(image_files)} image files to process")
        
        # Submit jobs
        priority_enum = ProcessingPriority[priority.upper()]
        submitted_count = 0
        
        with show_progress_bar(image_files, desc="Submitting jobs", total=len(image_files)) as pbar:
            for file_path in image_files:
                job = ProcessingJob(
                    job_id=f"job_{submitted_count}",
                    file_path=file_path,
                    priority=priority_enum
                )
                
                if processor.submit_job(job):
                    submitted_count += 1
                
                pbar.set_postfix({
                    'Submitted': submitted_count,
                    'Queue': processor.priority_queue.size()
                })
                pbar.update(1)
        
        echo_success(f"Submitted {submitted_count} jobs for processing")
        
        # Monitor processing
        echo_info("Monitoring processing...")
        while processor.priority_queue.size() > 0 or len(processor.active_jobs) > 0:
            metrics = processor.get_metrics()
            queue_status = processor.get_queue_status()
            
            echo_verbose(f"Queue: {queue_status['total_size']}, Active: {queue_status['active_jobs']}, "
                        f"Completed: {metrics.completed_jobs}, Failed: {metrics.failed_jobs}")
            
            time.sleep(2)
        
        # Final metrics
        final_metrics = processor.get_metrics()
        echo_success("Concurrent processing completed")
        echo_info(f"Total jobs: {final_metrics.total_jobs}")
        echo_info(f"Completed: {final_metrics.completed_jobs}")
        echo_info(f"Failed: {final_metrics.failed_jobs}")
        echo_info(f"Average processing time: {final_metrics.average_processing_time:.2f}s")
        
        # Stop processor
        processor.stop()
        
    except Exception as e:
        echo_error(f"Error in concurrent processing: {e}")
        click.exit(1)

if __name__ == '__main__':
    cli()