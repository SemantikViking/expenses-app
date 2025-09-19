# Configuration Reference

This document provides a comprehensive reference for all configuration options available in the Receipt Processor system.

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Environment Variables](#environment-variables)
- [Configuration File](#configuration-file)
- [Command Line Options](#command-line-options)
- [Configuration Sections](#configuration-sections)
- [Validation and Testing](#validation-and-testing)
- [Examples](#examples)

## Configuration Methods

The Receipt Processor supports multiple configuration methods, listed in order of precedence:

1. **Command Line Arguments** (highest priority)
2. **Environment Variables**
3. **Configuration File** (YAML/JSON)
4. **Default Values** (lowest priority)

### Configuration File Locations

The system looks for configuration files in the following order:

1. `./config.yaml` (current directory)
2. `./config.json` (current directory)
3. `~/.receipt-processor/config.yaml` (user home directory)
4. `~/.receipt-processor/config.json` (user home directory)
5. `/etc/receipt-processor/config.yaml` (system-wide)
6. `/etc/receipt-processor/config.json` (system-wide)

## Environment Variables

### AI Service Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes (if using OpenAI) |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | Yes (if using Anthropic) |
| `GOOGLE_API_KEY` | Google Vision API key | - | Yes (if using Google) |
| `AI_PROVIDER` | AI provider to use | `openai` | No |
| `AI_MODEL` | AI model to use | `gpt-4-vision-preview` | No |
| `AI_CONFIDENCE_THRESHOLD` | Minimum confidence threshold | `0.8` | No |
| `AI_MAX_RETRIES` | Maximum retry attempts | `3` | No |
| `AI_TIMEOUT` | Request timeout in seconds | `30` | No |

### Email Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_SERVER` | SMTP server hostname | - | Yes |
| `SMTP_PORT` | SMTP server port | `587` | No |
| `EMAIL_USERNAME` | Email username | - | Yes |
| `EMAIL_PASSWORD` | Email password/app password | - | Yes |
| `EMAIL_FROM` | From email address | - | No |
| `EMAIL_USE_TLS` | Use TLS encryption | `true` | No |
| `EMAIL_USE_SSL` | Use SSL encryption | `false` | No |
| `EMAIL_TIMEOUT` | Email timeout in seconds | `30` | No |

### Processing Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WATCH_DIRECTORY` | Directory to watch for new files | - | No |
| `PROCESSED_DIRECTORY` | Directory for processed files | - | No |
| `MAX_WORKERS` | Maximum concurrent workers | `4` | No |
| `BATCH_SIZE` | Batch processing size | `10` | No |
| `CONFIDENCE_THRESHOLD` | Minimum confidence threshold | `0.8` | No |
| `RETRY_ATTEMPTS` | Maximum retry attempts | `3` | No |
| `PROCESSING_TIMEOUT` | Processing timeout in seconds | `60` | No |

### Storage Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_FILE` | Log file path | `receipt_processing_log.json` | No |
| `BACKUP_DIRECTORY` | Backup directory path | `./backup` | No |
| `RETENTION_DAYS` | Log retention in days | `30` | No |
| `MAX_FILE_SIZE` | Maximum log file size | `10485760` | No |
| `ENABLE_BACKUP` | Enable automatic backups | `true` | No |

### Monitoring Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONITORING_ENABLED` | Enable system monitoring | `true` | No |
| `CHECK_INTERVAL` | Health check interval in seconds | `30` | No |
| `CPU_THRESHOLD` | CPU usage alert threshold | `80` | No |
| `MEMORY_THRESHOLD` | Memory usage alert threshold | `85` | No |
| `DISK_THRESHOLD` | Disk usage alert threshold | `90` | No |

## Configuration File

### YAML Format

```yaml
# AI Vision Configuration
ai_vision:
  provider: "openai"  # openai, anthropic, google
  model: "gpt-4-vision-preview"
  api_key: "${OPENAI_API_KEY}"
  max_retries: 3
  timeout: 30
  confidence_threshold: 0.8
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

# Email Configuration
email:
  smtp_server: "${SMTP_SERVER}"
  smtp_port: 587
  username: "${EMAIL_USERNAME}"
  password: "${EMAIL_PASSWORD}"
  from_address: "${EMAIL_FROM}"
  use_tls: true
  use_ssl: false
  timeout: 30
  templates:
    processing_complete: |
      Receipt processing completed successfully.
      Vendor: {{ vendor_name }}
      Amount: {{ total_amount }}
      Date: {{ transaction_date }}
    processing_failed: |
      Receipt processing failed.
      Error: {{ error_message }}
      File: {{ file_path }}

# Processing Configuration
processing:
  max_workers: 4
  batch_size: 10
  confidence_threshold: 0.8
  retry_attempts: 3
  timeout: 60
  parallel_processing: true
  priority_queue: true
  resource_limits:
    memory_limit_mb: 1024
    cpu_limit_percent: 80.0
    disk_limit_gb: 10

# Storage Configuration
storage:
  log_file: "receipt_processing_log.json"
  backup_directory: "./backup"
  retention_days: 30
  max_file_size: 10485760  # 10MB
  enable_compression: true
  backup_schedule: "0 2 * * *"  # Daily at 2 AM
  cleanup_schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM

# File Management Configuration
file_management:
  organize_by_date: true
  organize_by_vendor: true
  create_vendor_folders: true
  date_format: "%Y-%m-%d"
  max_files_per_folder: 1000
  backup_original: true
  cleanup_old_files: true
  retention_days: 365
  allowed_extensions: [".jpg", ".jpeg", ".png", ".tiff", ".webp"]
  max_file_size: 52428800  # 50MB

# Payment Processing Configuration
payment_processing:
  enabled: true
  auto_submit: false
  approval_required: true
  workflow_rules:
    - name: "Auto-approve Small Payments"
      condition:
        field: "amount"
        operator: "less_than"
        value: 100.0
      action:
        type: "approve"
        parameters:
          auto_approve: true
    - name: "Escalate Large Payments"
      condition:
        field: "amount"
        operator: "greater_than"
        value: 1000.0
      action:
        type: "escalate"
        parameters:
          escalate_to: "manager@example.com"

# Monitoring Configuration
monitoring:
  enabled: true
  check_interval: 30
  alert_thresholds:
    cpu_percent: 80
    memory_percent: 85
    disk_percent: 90
    error_rate: 5.0
    response_time: 5.0
  alert_channels:
    email:
      enabled: true
      recipients: ["admin@example.com"]
    webhook:
      enabled: false
      url: "https://your-app.com/webhooks"
      secret: "your_webhook_secret"
  metrics:
    retention_days: 7
    export_format: "json"
    export_schedule: "0 1 * * *"  # Daily at 1 AM

# Error Handling Configuration
error_handling:
  enable_retry: true
  max_retries: 3
  retry_delay: 1.0
  retry_strategy: "exponential_backoff"
  enable_recovery: true
  recovery_strategies:
    - "restart_service"
    - "clear_cache"
    - "notify_admin"
  error_categories:
    validation_error:
      max_retries: 0
      severity: "medium"
    processing_error:
      max_retries: 3
      severity: "high"
    network_error:
      max_retries: 5
      severity: "medium"
    ai_service_error:
      max_retries: 3
      severity: "high"

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    console:
      enabled: true
      level: "INFO"
    file:
      enabled: true
      level: "DEBUG"
      filename: "receipt_processor.log"
      max_bytes: 10485760  # 10MB
      backup_count: 5
    syslog:
      enabled: false
      host: "localhost"
      port: 514
      facility: "local0"

# Security Configuration
security:
  enable_encryption: true
  encryption_key: "${ENCRYPTION_KEY}"
  enable_audit_log: true
  audit_log_file: "audit.log"
  enable_rate_limiting: true
  rate_limit_requests: 100
  rate_limit_window: 3600  # 1 hour
  allowed_ips: []  # Empty means all IPs allowed
  blocked_ips: []

# API Configuration
api:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  workers: 4
  timeout: 30
  max_request_size: 10485760  # 10MB
  enable_cors: true
  cors_origins: ["*"]
  enable_swagger: true
  swagger_url: "/docs"
  enable_metrics: true
  metrics_url: "/metrics"

# Webhook Configuration
webhooks:
  enabled: true
  secret: "${WEBHOOK_SECRET}"
  timeout: 30
  retry_attempts: 3
  retry_delay: 1.0
  events:
    - "processing.completed"
    - "processing.failed"
    - "payment.submitted"
    - "payment.approved"
    - "payment.rejected"
    - "error.occurred"
    - "system.alert"
```

### JSON Format

```json
{
  "ai_vision": {
    "provider": "openai",
    "model": "gpt-4-vision-preview",
    "api_key": "${OPENAI_API_KEY}",
    "max_retries": 3,
    "timeout": 30,
    "confidence_threshold": 0.8
  },
  "email": {
    "smtp_server": "${SMTP_SERVER}",
    "smtp_port": 587,
    "username": "${EMAIL_USERNAME}",
    "password": "${EMAIL_PASSWORD}",
    "use_tls": true,
    "use_ssl": false,
    "timeout": 30
  },
  "processing": {
    "max_workers": 4,
    "batch_size": 10,
    "confidence_threshold": 0.8,
    "retry_attempts": 3,
    "timeout": 60
  },
  "storage": {
    "log_file": "receipt_processing_log.json",
    "backup_directory": "./backup",
    "retention_days": 30,
    "max_file_size": 10485760
  },
  "monitoring": {
    "enabled": true,
    "check_interval": 30,
    "alert_thresholds": {
      "cpu_percent": 80,
      "memory_percent": 85,
      "disk_percent": 90
    }
  }
}
```

## Command Line Options

### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Path to configuration file | Auto-detect |
| `--verbose` | Enable verbose output | False |
| `--quiet` | Suppress output | False |
| `--debug` | Enable debug mode | False |
| `--log-level` | Set log level | INFO |
| `--log-file` | Log file path | - |

### Process Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--batch-size` | Batch processing size | 10 |
| `--confidence` | Confidence threshold | 0.8 |
| `--output-dir` | Output directory | - |
| `--interactive` | Interactive mode | False |
| `--dry-run` | Show what would be processed | False |
| `--recursive` | Process subdirectories | False |
| `--max-workers` | Maximum workers | 4 |

### Daemon Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--watch-dir` | Directory to watch | - |
| `--max-workers` | Maximum workers | 4 |
| `--memory-limit` | Memory limit in MB | 1024 |
| `--cpu-limit` | CPU limit percentage | 80.0 |
| `--pid-file` | PID file path | - |
| `--log-file` | Log file path | - |

### Report Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type` | Report type | summary |
| `--format` | Output format | table |
| `--output` | Output file | - |
| `--date-from` | Start date | - |
| `--date-to` | End date | - |
| `--vendor` | Filter by vendor | - |
| `--status` | Filter by status | - |

## Configuration Sections

### AI Vision Configuration

Controls AI service integration and data extraction.

```yaml
ai_vision:
  provider: "openai"  # openai, anthropic, google
  model: "gpt-4-vision-preview"
  api_key: "${OPENAI_API_KEY}"
  max_retries: 3
  timeout: 30
  confidence_threshold: 0.8
  custom_prompts:
    vendor_extraction: "Extract vendor name from receipt"
    amount_extraction: "Extract total amount from receipt"
    date_extraction: "Extract transaction date from receipt"
```

**Parameters:**
- `provider` (str): AI provider to use
- `model` (str): AI model to use
- `api_key` (str): API key for the provider
- `max_retries` (int): Maximum retry attempts
- `timeout` (int): Request timeout in seconds
- `confidence_threshold` (float): Minimum confidence threshold
- `custom_prompts` (dict): Custom prompts for extraction

### Email Configuration

Controls email notifications and delivery.

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "your_email@gmail.com"
  password: "your_app_password"
  from_address: "noreply@example.com"
  use_tls: true
  use_ssl: false
  timeout: 30
  templates:
    processing_complete: "Receipt processed: {{ vendor_name }}"
    processing_failed: "Processing failed: {{ error_message }}"
```

**Parameters:**
- `smtp_server` (str): SMTP server hostname
- `smtp_port` (int): SMTP server port
- `username` (str): Email username
- `password` (str): Email password
- `from_address` (str): From email address
- `use_tls` (bool): Use TLS encryption
- `use_ssl` (bool): Use SSL encryption
- `timeout` (int): Email timeout in seconds
- `templates` (dict): Email templates

### Processing Configuration

Controls processing behavior and performance.

```yaml
processing:
  max_workers: 4
  batch_size: 10
  confidence_threshold: 0.8
  retry_attempts: 3
  timeout: 60
  parallel_processing: true
  priority_queue: true
  resource_limits:
    memory_limit_mb: 1024
    cpu_limit_percent: 80.0
    disk_limit_gb: 10
```

**Parameters:**
- `max_workers` (int): Maximum concurrent workers
- `batch_size` (int): Batch processing size
- `confidence_threshold` (float): Minimum confidence threshold
- `retry_attempts` (int): Maximum retry attempts
- `timeout` (int): Processing timeout in seconds
- `parallel_processing` (bool): Enable parallel processing
- `priority_queue` (bool): Enable priority queue
- `resource_limits` (dict): Resource usage limits

### Storage Configuration

Controls data storage and backup.

```yaml
storage:
  log_file: "receipt_processing_log.json"
  backup_directory: "./backup"
  retention_days: 30
  max_file_size: 10485760
  enable_compression: true
  backup_schedule: "0 2 * * *"
  cleanup_schedule: "0 3 * * 0"
```

**Parameters:**
- `log_file` (str): Log file path
- `backup_directory` (str): Backup directory path
- `retention_days` (int): Log retention in days
- `max_file_size` (int): Maximum log file size
- `enable_compression` (bool): Enable log compression
- `backup_schedule` (str): Backup schedule (cron format)
- `cleanup_schedule` (str): Cleanup schedule (cron format)

### Monitoring Configuration

Controls system monitoring and alerting.

```yaml
monitoring:
  enabled: true
  check_interval: 30
  alert_thresholds:
    cpu_percent: 80
    memory_percent: 85
    disk_percent: 90
    error_rate: 5.0
    response_time: 5.0
  alert_channels:
    email:
      enabled: true
      recipients: ["admin@example.com"]
    webhook:
      enabled: false
      url: "https://your-app.com/webhooks"
      secret: "your_webhook_secret"
```

**Parameters:**
- `enabled` (bool): Enable monitoring
- `check_interval` (int): Health check interval in seconds
- `alert_thresholds` (dict): Alert thresholds
- `alert_channels` (dict): Alert delivery channels

## Validation and Testing

### Configuration Validation

```bash
# Validate configuration
receipt-processor config validate

# Show current configuration
receipt-processor config show

# Test configuration
receipt-processor config test
```

### Environment Testing

```bash
# Test AI service
receipt-processor test-ai --provider openai

# Test email service
receipt-processor test-email

# Test file system
receipt-processor test-files /path/to/test

# Test all services
receipt-processor test-all
```

### Configuration Examples

#### Development Configuration

```yaml
ai_vision:
  provider: "openai"
  model: "gpt-4-vision-preview"
  confidence_threshold: 0.7

processing:
  max_workers: 2
  batch_size: 5
  timeout: 30

logging:
  level: "DEBUG"
  handlers:
    console:
      enabled: true
      level: "DEBUG"
```

#### Production Configuration

```yaml
ai_vision:
  provider: "openai"
  model: "gpt-4-vision-preview"
  confidence_threshold: 0.8
  max_retries: 3
  timeout: 60

processing:
  max_workers: 8
  batch_size: 20
  timeout: 120
  resource_limits:
    memory_limit_mb: 2048
    cpu_limit_percent: 80.0

monitoring:
  enabled: true
  check_interval: 30
  alert_thresholds:
    cpu_percent: 80
    memory_percent: 85
    disk_percent: 90

logging:
  level: "INFO"
  handlers:
    file:
      enabled: true
      level: "INFO"
      filename: "/var/log/receipt-processor.log"
```

#### High-Volume Configuration

```yaml
processing:
  max_workers: 16
  batch_size: 50
  timeout: 300
  parallel_processing: true
  priority_queue: true
  resource_limits:
    memory_limit_mb: 4096
    cpu_limit_percent: 90.0
    disk_limit_gb: 50

storage:
  log_file: "/var/log/receipt_processing_log.json"
  backup_directory: "/var/backups/receipt-processor"
  retention_days: 90
  max_file_size: 104857600  # 100MB
  enable_compression: true

monitoring:
  enabled: true
  check_interval: 15
  alert_thresholds:
    cpu_percent: 85
    memory_percent: 90
    disk_percent: 95
    error_rate: 2.0
    response_time: 10.0
```

---

For more information, please refer to the [User Manual](USER_MANUAL.md) or [API Documentation](API_DOCUMENTATION.md).
