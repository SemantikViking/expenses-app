# User Manual

This comprehensive user manual provides detailed instructions for using the Receipt Processor system effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Command Reference](#command-reference)
- [Configuration Guide](#configuration-guide)
- [Processing Workflows](#processing-workflows)
- [Reporting and Analytics](#reporting-and-analytics)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## Getting Started

### First Time Setup

1. **Install the system** (see [Installation Guide](INSTALLATION.md))
2. **Configure API keys** in your `.env` file
3. **Set up directories** for processing
4. **Test the installation**

```bash
# Test basic functionality
receipt-processor --version
receipt-processor config validate
receipt-processor test-ai --provider openai
```

### Quick Start Example

```bash
# Process a single receipt
receipt-processor process /path/to/receipt.jpg

# Process a directory of receipts
receipt-processor process /path/to/receipts/ --batch-size 5

# Check processing status
receipt-processor status

# Generate a summary report
receipt-processor report --type summary
```

## Command Reference

### Basic Commands

#### `process` - Process Receipt Images

Process one or more receipt images to extract data.

```bash
# Process single image
receipt-processor process /path/to/receipt.jpg

# Process directory
receipt-processor process /path/to/receipts/

# Process with options
receipt-processor process /path/to/receipts/ \
  --batch-size 10 \
  --confidence 0.9 \
  --output-dir /path/to/processed
```

**Options:**
- `--batch-size N`: Process N images at a time
- `--confidence FLOAT`: Minimum confidence threshold (0.0-1.0)
- `--output-dir PATH`: Directory for processed files
- `--interactive`: Interactive mode for confirmation
- `--verbose`: Verbose output
- `--dry-run`: Show what would be processed without actually processing

#### `status` - Check Processing Status

View current processing status and statistics.

```bash
# Basic status
receipt-processor status

# Detailed status with statistics
receipt-processor status --detailed

# Status in JSON format
receipt-processor status --format json

# Status with specific filters
receipt-processor status --status completed --limit 10
```

**Options:**
- `--format FORMAT`: Output format (table, json, csv)
- `--status STATUS`: Filter by status (pending, processing, completed, error)
- `--limit N`: Limit number of results
- `--detailed`: Show detailed information

#### `logs` - View Processing Logs

Display processing logs and history.

```bash
# View recent logs
receipt-processor logs

# View logs with filters
receipt-processor logs --status completed --limit 20

# View logs in JSON format
receipt-processor logs --format json

# Export logs
receipt-processor logs --export logs.json
```

**Options:**
- `--status STATUS`: Filter by processing status
- `--vendor VENDOR`: Filter by vendor name
- `--date-from DATE`: Start date filter (YYYY-MM-DD)
- `--date-to DATE`: End date filter (YYYY-MM-DD)
- `--amount-min FLOAT`: Minimum amount filter
- `--amount-max FLOAT`: Maximum amount filter
- `--format FORMAT`: Output format (table, json, csv)
- `--limit N`: Limit number of results
- `--export FILE`: Export logs to file

### Report Commands

#### `report` - Generate Reports

Create various types of reports and analytics.

```bash
# Summary report
receipt-processor report --type summary

# Vendor analysis
receipt-processor report --type vendor

# Workflow statistics
receipt-processor report --type workflow

# Payment tracking
receipt-processor report --type payment

# Audit trail
receipt-processor report --type audit
```

**Report Types:**
- `summary`: Overview of all processing activities
- `vendor`: Analysis grouped by vendor/merchant
- `workflow`: Processing workflow statistics
- `payment`: Payment tracking and status
- `audit`: Detailed audit trail

**Options:**
- `--type TYPE`: Report type
- `--format FORMAT`: Output format (table, json, csv, pdf)
- `--output FILE`: Save report to file
- `--date-from DATE`: Start date filter
- `--date-to DATE`: End date filter
- `--vendor VENDOR`: Filter by vendor
- `--status STATUS`: Filter by status

### Monitoring Commands

#### `health` - System Health Check

Check system health and performance.

```bash
# Basic health check
receipt-processor health

# Detailed health information
receipt-processor health --detailed

# Health check with resources
receipt-processor health --show-resources
```

#### `metrics` - Performance Metrics

View system performance metrics and statistics.

```bash
# Current metrics
receipt-processor metrics

# Metrics over time
receipt-processor metrics --duration 60

# Export metrics
receipt-processor metrics --format json --output metrics.json
```

#### `alerts` - System Alerts

View and manage system alerts.

```bash
# View active alerts
receipt-processor alerts

# View alerts by level
receipt-processor alerts --level warning

# Resolve alerts
receipt-processor resolve-alerts --all
```

### Daemon Commands

#### `daemon-start` - Start Background Service

Start the receipt processor as a background daemon.

```bash
# Start daemon with default settings
receipt-processor daemon-start

# Start with custom settings
receipt-processor daemon-start \
  --watch-dir /path/to/watch \
  --max-workers 4 \
  --memory-limit 1024 \
  --cpu-limit 80.0
```

#### `daemon-stop` - Stop Background Service

Stop the running daemon service.

```bash
receipt-processor daemon-stop
```

#### `daemon-status` - Check Daemon Status

Check the status of the daemon service.

```bash
receipt-processor daemon-status
```

### Utility Commands

#### `config` - Configuration Management

Manage system configuration.

```bash
# Show current configuration
receipt-processor config show

# Validate configuration
receipt-processor config validate

# Reset to defaults
receipt-processor config reset
```

#### `export` - Data Export

Export processing data in various formats.

```bash
# Export to JSON
receipt-processor export --format json --output data.json

# Export to CSV
receipt-processor export --format csv --output data.csv

# Export with filters
receipt-processor export --format json \
  --status completed \
  --date-from 2024-01-01 \
  --output completed_receipts.json
```

## Configuration Guide

### Environment Variables

The system uses environment variables for configuration. Create a `.env` file in your project directory:

```bash
# AI Service Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Processing Configuration
WATCH_DIRECTORY=/path/to/watch
PROCESSED_DIRECTORY=/path/to/processed
MAX_WORKERS=4
CONFIDENCE_THRESHOLD=0.8

# Storage Configuration
LOG_FILE=receipt_processing_log.json
BACKUP_DIRECTORY=/path/to/backup
```

### Configuration File

For more complex configurations, use a YAML configuration file:

```yaml
# AI Vision Configuration
ai_vision:
  provider: "openai"
  model: "gpt-4-vision-preview"
  api_key: "${OPENAI_API_KEY}"
  max_retries: 3
  timeout: 30
  confidence_threshold: 0.8

# Email Configuration
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "${EMAIL_USERNAME}"
  password: "${EMAIL_PASSWORD}"
  use_tls: true
  use_ssl: false
  timeout: 30

# Processing Configuration
processing:
  max_workers: 4
  batch_size: 10
  confidence_threshold: 0.8
  retry_attempts: 3
  timeout: 60

# Storage Configuration
storage:
  log_file: "receipt_processing_log.json"
  backup_directory: "./backup"
  retention_days: 30
  max_file_size: 10485760

# Monitoring Configuration
monitoring:
  enabled: true
  check_interval: 30
  alert_thresholds:
    cpu_percent: 80
    memory_percent: 85
    disk_percent: 90
```

### Advanced Configuration

#### Custom AI Prompts

Customize AI prompts for better extraction:

```yaml
ai_vision:
  custom_prompts:
    vendor_extraction: |
      Extract the vendor or merchant name from this receipt.
      Look for business names, store names, or company names.
    
    amount_extraction: |
      Extract the total amount from this receipt.
      Look for the final total, including tax and tip.
    
    date_extraction: |
      Extract the transaction date from this receipt.
      Look for date stamps, transaction dates, or receipt dates.
```

#### File Organization Rules

Configure how processed files are organized:

```yaml
file_management:
  organize_by_date: true
  organize_by_vendor: true
  create_vendor_folders: true
  date_format: "%Y-%m-%d"
  max_files_per_folder: 1000
  backup_original: true
  cleanup_old_files: true
  retention_days: 365
```

## Processing Workflows

### Basic Processing Workflow

1. **Prepare Images**: Ensure receipt images are clear and well-lit
2. **Run Processing**: Use the `process` command
3. **Review Results**: Check the status and logs
4. **Generate Reports**: Create reports for analysis

```bash
# Step 1: Process images
receipt-processor process /path/to/receipts/

# Step 2: Check status
receipt-processor status

# Step 3: Generate report
receipt-processor report --type summary
```

### Batch Processing Workflow

For processing large numbers of receipts:

```bash
# Process in batches
receipt-processor process /path/to/receipts/ --batch-size 10

# Monitor progress
receipt-processor status --detailed

# Check for errors
receipt-processor logs --status error
```

### Continuous Processing Workflow

For ongoing receipt processing:

```bash
# Start daemon service
receipt-processor daemon-start --watch-dir /path/to/watch

# Monitor system health
receipt-processor health

# Check processing status
receipt-processor daemon-status
```

### Error Handling Workflow

When processing errors occur:

```bash
# Check error logs
receipt-processor error-log

# Retry failed processing
receipt-processor retry --status error

# Check system health
receipt-processor health
```

## Reporting and Analytics

### Summary Reports

Get an overview of all processing activities:

```bash
# Basic summary
receipt-processor report --type summary

# Summary with date range
receipt-processor report --type summary \
  --date-from 2024-01-01 \
  --date-to 2024-01-31

# Export summary
receipt-processor report --type summary \
  --format csv \
  --output summary_2024_01.csv
```

### Vendor Analysis

Analyze spending by vendor:

```bash
# Vendor analysis
receipt-processor report --type vendor

# Top vendors
receipt-processor report --type vendor --limit 10

# Vendor analysis by date range
receipt-processor report --type vendor \
  --date-from 2024-01-01 \
  --date-to 2024-01-31
```

### Workflow Statistics

View processing workflow statistics:

```bash
# Workflow statistics
receipt-processor report --type workflow

# Processing times
receipt-processor report --type workflow --show-times

# Error rates
receipt-processor report --type workflow --show-errors
```

### Payment Tracking

Track payment processing:

```bash
# Payment status
receipt-processor report --type payment

# Pending payments
receipt-processor report --type payment --status pending

# Payment history
receipt-processor report --type payment --show-history
```

## Monitoring and Maintenance

### System Health Monitoring

Regular health checks ensure optimal performance:

```bash
# Daily health check
receipt-processor health

# Detailed health check
receipt-processor health --detailed --show-resources

# Health check with alerts
receipt-processor health --show-alerts
```

### Performance Monitoring

Monitor system performance:

```bash
# Current performance
receipt-processor metrics

# Performance over time
receipt-processor metrics --duration 3600

# Export performance data
receipt-processor metrics --format json --output performance.json
```

### Log Management

Regular log management prevents disk space issues:

```bash
# View log statistics
receipt-processor logs --stats

# Clean old logs
receipt-processor logs --cleanup --older-than 30

# Export logs for analysis
receipt-processor logs --export logs.json
```

### Backup and Recovery

Regular backups protect your data:

```bash
# Create backup
receipt-processor backup --output backup_2024_01_15.tar.gz

# Restore from backup
receipt-processor restore --input backup_2024_01_15.tar.gz

# List available backups
receipt-processor backup --list
```

## Advanced Features

### Concurrent Processing

Process multiple receipts simultaneously:

```bash
# Start concurrent processing
receipt-processor process-concurrent \
  --input-dir /path/to/receipts \
  --max-workers 8 \
  --memory-limit 2048 \
  --cpu-limit 80.0

# Monitor concurrent processing
receipt-processor status --concurrent
```

### Email Integration

Send notifications and reports via email:

```bash
# Send processing report
receipt-processor email --report summary

# Send to specific recipients
receipt-processor email --report summary \
  --to user1@example.com,user2@example.com

# Schedule regular emails
receipt-processor email --schedule daily --report summary
```

### Payment Processing

Track and manage payments:

```bash
# Submit payment
receipt-processor submit --log-id LOG_001

# Check payment status
receipt-processor payment-status --payment-id PAY_001

# Mark payment received
receipt-processor payment-received --payment-id PAY_001
```

### Data Export and Import

Export and import data for integration:

```bash
# Export all data
receipt-processor export --format json --output all_data.json

# Export specific data
receipt-processor export --format csv \
  --status completed \
  --output completed_receipts.csv

# Import data
receipt-processor import --input data.json
```

## Troubleshooting

### Common Issues

#### Processing Errors

**Problem**: Images not being processed
**Solution**:
```bash
# Check file permissions
receipt-processor check-files /path/to/images

# Test with single image
receipt-processor process /path/to/test.jpg --verbose

# Check error logs
receipt-processor error-log --recent 10
```

#### Performance Issues

**Problem**: Slow processing
**Solution**:
```bash
# Check system resources
receipt-processor health --show-resources

# Adjust worker count
receipt-processor daemon-start --max-workers 2

# Check for bottlenecks
receipt-processor metrics --duration 60
```

#### Configuration Issues

**Problem**: Configuration errors
**Solution**:
```bash
# Validate configuration
receipt-processor config validate

# Show current configuration
receipt-processor config show

# Reset to defaults
receipt-processor config reset
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Enable debug logging
export RECEIPT_PROCESSOR_DEBUG=1

# Run with debug output
receipt-processor process /path/to/images --verbose --debug

# Check debug logs
receipt-processor logs --level debug
```

### Getting Help

If you need additional help:

1. **Check the documentation**: [https://receipt-processor.readthedocs.io](https://receipt-processor.readthedocs.io)
2. **View command help**: `receipt-processor --help` or `receipt-processor COMMAND --help`
3. **Run diagnostics**: `receipt-processor diagnose`
4. **Check system requirements**: `receipt-processor check-requirements`
5. **Report issues**: [GitHub Issues](https://github.com/receipt-processor/receipt-processor/issues)

---

For more detailed information, please refer to the [API Documentation](API_DOCUMENTATION.md) or [Configuration Reference](CONFIGURATION_REFERENCE.md).
