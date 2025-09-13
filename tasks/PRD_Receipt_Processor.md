# Product Requirements Document (PRD)
## Receipt Processing Command-Line Application

**Version:** 1.0  
**Date:** September 2025  
**Author:** AI Assistant  
**Status:** Draft  

---

## 1. Executive Summary

### 1.1 Product Overview
A macOS command-line application that runs continuously in the background to automatically process receipt images. The application monitors a designated folder for new receipt screenshots, uses AI vision capabilities to extract key information (vendor, date, total cost), and renames files in a standardized format.

### 1.2 Business Objectives
- **Automate receipt processing** to reduce manual data entry
- **Standardize file naming** for better organization and searchability
- **Improve expense tracking efficiency** for individuals and small businesses
- **Minimize human intervention** in receipt management workflow

### 1.3 Success Metrics
- 95%+ accuracy in vendor name extraction
- 90%+ accuracy in date extraction
- 95%+ accuracy in total cost extraction
- < 5 seconds processing time per receipt
- 99%+ uptime for background monitoring

---

## 2. Product Requirements

### 2.1 Functional Requirements

#### 2.1.1 Core Functionality
- **FR-001**: Monitor designated folder for new image files
- **FR-002**: Detect supported image formats (PNG, JPEG, JPG, HEIC)
- **FR-003**: Process images using AI vision model to extract:
  - Vendor name
  - Transaction date
  - Total cost/amount
- **FR-004**: Rename files using standardized format: `YYYY-MM-DD_VendorName_Amount.ext`
- **FR-005**: Handle processing errors gracefully with logging
- **FR-006**: Support batch processing of existing files in monitored folder

#### 2.1.2 Configuration Management
- **FR-007**: Allow configuration of monitored folder path
- **FR-008**: Support configuration of AI model parameters
- **FR-009**: Enable/disable specific extraction fields
- **FR-010**: Set custom file naming patterns
- **FR-011**: Configure processing intervals and batch sizes

#### 2.1.3 Logging and Monitoring
- **FR-012**: Generate detailed processing logs with structured data
- **FR-013**: Track processing statistics (success/failure rates)
- **FR-014**: Log extraction confidence scores
- **FR-015**: Provide real-time status updates via console output
- **FR-016**: Maintain detailed receipt processing log with comprehensive status tracking
- **FR-017**: Store receipt extraction data in structured JSON file format
- **FR-018**: Enable log querying and filtering by date, vendor, status
- **FR-019**: Generate processing reports and analytics
- **FR-020**: Track receipt workflow from processing through payment completion
- **FR-021**: Support email integration for receipt submission to accounting systems
- **FR-022**: Monitor payment status and reconciliation tracking
- **FR-023**: Provide status transition logging with timestamps and user actions

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance
- **NFR-001**: Process individual receipts in < 5 seconds
- **NFR-002**: Support concurrent processing of up to 10 images
- **NFR-003**: Memory usage < 500MB during normal operation
- **NFR-004**: CPU usage < 20% during idle monitoring

#### 2.2.2 Reliability
- **NFR-005**: 99%+ uptime for background monitoring
- **NFR-006**: Automatic recovery from processing errors
- **NFR-007**: Graceful handling of corrupted or unsupported images
- **NFR-008**: Persistent configuration storage

#### 2.2.3 Security
- **NFR-009**: No storage of sensitive image data beyond processing
- **NFR-010**: Secure handling of AI model API keys
- **NFR-011**: Local processing option to avoid cloud dependencies

#### 2.2.4 Usability
- **NFR-012**: Simple command-line interface with clear help text
- **NFR-013**: Comprehensive configuration file documentation
- **NFR-014**: Clear error messages and troubleshooting guidance

---

## 3. Technical Specifications

### 3.1 System Architecture

#### 3.1.1 Core Components
- **File System Monitor**: Watches designated folder for new files
- **Image Processor**: Handles image loading and preprocessing
- **AI Vision Engine**: Extracts text and data from receipt images
- **Data Parser**: Processes extracted text to identify vendor, date, and amount
- **File Renamer**: Applies standardized naming convention
- **Configuration Manager**: Handles settings and preferences
- **Logging System**: Records processing activities and errors

#### 3.1.2 Technology Stack
- **Language**: Python 3.9+ (recommended for Pydantic AI integration)
- **AI Framework**: Pydantic AI for structured data extraction and type safety
- **File Monitoring**: `watchdog` for cross-platform file system monitoring
- **Image Processing**: `PIL/Pillow` for image handling and preprocessing
- **AI Vision**: OpenAI GPT-4 Vision API, Anthropic Claude Vision, or local models
- **Data Validation**: Pydantic for structured data models and validation
- **Data Storage**: JSON file for receipt processing logs and structured data storage
- **Text Processing**: `regex` and `dateutil` libraries for data parsing
- **Configuration**: `pydantic-settings` for type-safe configuration management
- **Observability**: Pydantic Logfire for AI model monitoring and debugging

### 3.2 Data Flow

```
1. File System Monitor detects new image
2. Image Processor validates and loads image
3. AI Vision Engine (Pydantic AI) extracts structured data from image
4. Data Parser validates extracted data using Pydantic models
5. JSON Logger stores receipt details and processing status to file
6. File Renamer applies standardized naming based on extracted data
7. Logging System records processing results and updates status
8. Process repeats for next image
```

### 3.3 Data Models (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal

class ReceiptData(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=100)
    transaction_date: datetime
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="GBP", max_length=3)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class ProcessingStatus(BaseModel):
    status: Literal[
        "pending",           # File detected, queued for processing
        "processing",        # Currently being processed by AI
        "error",            # Processing failed with error
        "no_data_extracted", # AI couldn't extract receipt details
        "processed",         # Successfully extracted and renamed
        "emailed",          # Receipt sent via email to target
        "submitted",        # Receipt submitted for payment processing
        "payment_received", # Payment has been received/reconciled
        "retry"             # Automatic retry in progress
    ]
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    retry_count: int = Field(default=0, ge=0)
    email_sent_at: Optional[datetime] = None
    email_recipient: Optional[str] = None
    submitted_at: Optional[datetime] = None
    payment_received_at: Optional[datetime] = None
    payment_amount: Optional[Decimal] = None
    notes: Optional[str] = None

class ReceiptProcessingLog(BaseModel):
    id: str = Field(..., description="Unique processing log ID (UUID)")
    timestamp: datetime = Field(default_factory=datetime.now)
    original_filename: str
    file_path: str
    file_size: int
    new_filename: Optional[str] = None
    receipt_data: Optional[ReceiptData] = None
    processing_status: ProcessingStatus
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StatusTransition(BaseModel):
    """Tracks status changes with timestamps and context"""
    from_status: str
    to_status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user_action: Optional[str] = None
    automated: bool = Field(default=True)
    notes: Optional[str] = None

class ReceiptProcessingLogFile(BaseModel):
    """Container for all receipt processing logs"""
    logs: List[ReceiptProcessingLog] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    status_transitions: List[StatusTransition] = Field(default_factory=list)
```

### 3.4 JSON File Structure

```json
{
  "logs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-09-15T10:30:00Z",
      "original_filename": "receipt_001.jpg",
      "file_path": "/Users/username/Desktop/Receipts/receipt_001.jpg",
      "file_size": 245760,
      "new_filename": "2025-09-15_Starbucks_12.50.jpg",
      "receipt_data": {
        "vendor_name": "Starbucks",
        "transaction_date": "2025-09-15T08:45:00Z",
        "total_amount": "12.50",
        "currency": "GBP",
        "confidence_score": 0.95
      },
      "processing_status": {
        "status": "processed",
        "error_message": null,
        "processing_time": 3.2,
        "retry_count": 0,
        "email_sent_at": null,
        "email_recipient": null,
        "submitted_at": null,
        "payment_received_at": null,
        "payment_amount": null,
        "notes": null
      },
      "created_at": "2025-09-15T10:30:00Z",
      "updated_at": "2025-09-15T10:30:03Z"
    }
  ],
  "metadata": {
    "total_processed": 1,
    "success_count": 1,
    "failed_count": 0,
    "avg_processing_time": 3.2,
    "status_counts": {
      "pending": 0,
      "processing": 0,
      "error": 0,
      "no_data_extracted": 0,
      "processed": 1,
      "emailed": 0,
      "submitted": 0,
      "payment_received": 0,
      "retry": 0
    }
  },
  "status_transitions": [
    {
      "from_status": "pending",
      "to_status": "processing",
      "timestamp": "2025-09-15T10:30:00Z",
      "user_action": null,
      "automated": true,
      "notes": "AI processing started"
    },
    {
      "from_status": "processing",
      "to_status": "processed",
      "timestamp": "2025-09-15T10:30:03Z",
      "user_action": null,
      "automated": true,
      "notes": "Successfully extracted receipt data"
    }
  ],
  "last_updated": "2025-09-15T10:30:03Z"
}
```

### 3.5 File Naming Convention

**Standard Format**: `YYYY-MM-DD_VendorName_Amount.ext`

**Examples**:
- `2025-09-15_Starbucks_12.50.jpg`
- `2025-08-22_Amazon_89.99.png`
- `2025-07-10_GasStation_45.67.heic`

**Fallback Format**: `YYYY-MM-DD_Unknown_0.00.ext` (when extraction fails)

---

## 4. User Interface Requirements

### 4.1 Command-Line Interface

#### 4.1.1 Basic Commands
```bash
# Start the application
receipt-processor start --config /path/to/config.ini

# Process existing files
receipt-processor process --folder /path/to/receipts

# Show status
receipt-processor status

# Show processing logs
receipt-processor logs --filter status=failed --limit 10

# Update receipt status manually
receipt-processor update-status --id 550e8400-e29b-41d4-a716-446655440000 --status emailed --notes "Sent to accounting@company.com"

# Send receipt via email
receipt-processor email --id 550e8400-e29b-41d4-a716-446655440000 --to accounting@company.com --template expense_report

# Mark receipt as submitted for payment
receipt-processor submit --id 550e8400-e29b-41d4-a716-446655440000 --payment-system quickbooks

# Record payment received
receipt-processor payment-received --id 550e8400-e29b-41d4-a716-446655440000 --amount 12.50

# Generate reports
receipt-processor report --from 2025-06-01 --to 2025-12-31

# Export data
receipt-processor export --format csv --output receipts_2025.csv

# Show help
receipt-processor --help
```

#### 4.1.2 Configuration Commands
```bash
# Initialize configuration
receipt-processor init

# Validate configuration
receipt-processor validate-config

# Show current settings
receipt-processor show-config
```

### 4.2 Configuration File Format (Pydantic Settings)

```python
# config.py - Type-safe configuration using Pydantic Settings
from pydantic import BaseSettings, Field
from typing import List, Literal
from pathlib import Path

class MonitoringSettings(BaseSettings):
    watch_folder: Path = Field(..., description="Folder to monitor for new receipts")
    file_extensions: List[str] = Field(default=[".jpg", ".jpeg", ".png", ".heic"])
    processing_interval: int = Field(default=5, description="Seconds between folder checks")
    max_concurrent_processing: int = Field(default=3)

class AIVisionSettings(BaseSettings):
    provider: Literal["openai", "anthropic", "local"] = Field(default="openai")
    model: str = Field(default="gpt-4-vision-preview")
    api_key: str = Field(..., description="API key for AI service")
    max_retries: int = Field(default=3)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    timeout_seconds: int = Field(default=30)

class ExtractionSettings(BaseSettings):
    extract_vendor: bool = Field(default=True)
    extract_date: bool = Field(default=True)
    extract_amount: bool = Field(default=True)
    extract_currency: bool = Field(default=True)
    date_formats: List[str] = Field(default=["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"])
    default_currency: str = Field(default="GBP")

class EmailSettings(BaseSettings):
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(..., description="SMTP username/email")
    smtp_password: str = Field(..., description="SMTP password or app password")
    default_recipient: Optional[str] = Field(default=None)
    email_templates_path: Path = Field(default="./templates")
    enable_email: bool = Field(default=False)

class PaymentSettings(BaseSettings):
    enable_payment_tracking: bool = Field(default=False)
    payment_systems: List[str] = Field(default=["manual", "quickbooks", "xero"])
    default_payment_system: str = Field(default="manual")
    auto_reconcile: bool = Field(default=False)

class StorageSettings(BaseSettings):
    log_file_path: Path = Field(default="./receipt_processing_log.json")
    backup_enabled: bool = Field(default=True)
    backup_interval_hours: int = Field(default=24)
    max_log_entries: int = Field(default=10000, description="Maximum log entries before rotation")

class LoggingSettings(BaseSettings):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: Path = Field(default="./logs/receipt-processor.log")
    max_log_size_mb: int = Field(default=10)
    backup_count: int = Field(default=5)
    enable_logfire: bool = Field(default=True)

class AppSettings(BaseSettings):
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
```

---

## 5. Receipt Processing Log System

### 5.1 Log Structure and Status Tracking

The application maintains a comprehensive log of all receipt processing activities with detailed status tracking:

#### 5.1.1 Enhanced Processing Status Flow
```
pending → processing → [error/no_data_extracted/processed] → emailed → submitted → payment_received
                    ↓
                   retry (if error/no_data_extracted)
```

**Detailed Status Flow:**
1. **pending**: File detected, queued for processing
2. **processing**: Currently being processed by AI vision model
3. **error**: Processing failed with technical error (network, API, etc.)
4. **no_data_extracted**: AI couldn't extract meaningful receipt data
5. **processed**: Successfully extracted data and renamed file
6. **emailed**: Receipt sent via email to accounting/target system
7. **submitted**: Receipt submitted for payment processing in accounting system
8. **payment_received**: Payment has been received and reconciled
9. **retry**: Automatic retry in progress after error or no data extracted

#### 5.1.2 Log Entry Components
Each receipt processing attempt creates a log entry containing:

- **File Information**: Original filename, file path, file size, timestamps
- **Extracted Data**: Vendor name, transaction date, amount, currency, confidence scores
- **Processing Status**: Current status, error messages, processing time, retry count
- **Email Tracking**: Email sent timestamp, recipient, delivery status
- **Payment Tracking**: Submission timestamp, payment system, payment received timestamp
- **Status Transitions**: Complete audit trail of status changes with timestamps
- **Metadata**: Processing timestamps, configuration used, AI model version, user actions

#### 5.1.3 Status Management Features
- **Automatic Transitions**: System automatically progresses through processing stages
- **Manual Status Updates**: Users can manually update status via CLI commands
- **Status Validation**: Prevents invalid status transitions (e.g., can't mark payment_received before submitted)
- **Audit Trail**: Complete history of all status changes with timestamps and reasons
- **Bulk Operations**: Update status for multiple receipts simultaneously
- **Conditional Logic**: Status transitions can trigger automated actions (e.g., auto-email after processing)

### 5.2 Log Querying and Reporting

#### 5.2.1 Query Capabilities
```bash
# View recent processing logs
receipt-processor logs --recent 24h

# Filter by status
receipt-processor logs --status failed --limit 20

# Search by vendor
receipt-processor logs --vendor "Starbucks" --from 2025-06-01

# Filter by multiple statuses
receipt-processor logs --status emailed,submitted --limit 50

# Show receipts pending email
receipt-processor logs --status processed --no-email

# Show payment reconciliation status
receipt-processor logs --status submitted --pending-payment

# Show processing statistics
receipt-processor stats --period monthly --include-payment-status

# Export processing data with workflow status
receipt-processor export --format json --include-logs --include-transitions
```

#### 5.2.2 Enhanced Report Generation
- **Daily Summary**: Processing counts, success rates, common errors, workflow status distribution
- **Vendor Analysis**: Spending by vendor, frequency analysis, payment status by vendor
- **Error Reports**: Failed processing attempts with error details and retry analysis
- **Performance Metrics**: Processing times, confidence scores, system resource usage
- **Workflow Reports**: Status transition analytics, time spent in each status, bottleneck identification
- **Payment Reports**: Outstanding payments, reconciliation status, payment timeline analysis
- **Email Reports**: Email delivery status, bounce rates, recipient engagement
- **Audit Reports**: Complete status change history with user actions and timestamps

### 5.3 Log Management

#### 5.3.1 Retention Policy
- Keep detailed logs for 180 days by default (configurable)
- Rotate log file when maximum entries reached (default: 10,000)
- Archive older logs with summary data only
- Configurable retention periods and file rotation

#### 5.3.2 Log File Management
- Automatic JSON file rotation and backup
- Configurable backup schedules with timestamp-based naming
- Log file compression for long-term storage
- Atomic file writes to prevent corruption during processing

---

## 6. Error Handling and Edge Cases

### 5.1 Error Scenarios
- **Invalid image format**: Skip file and log warning
- **Corrupted image**: Attempt recovery, skip if failed
- **AI extraction failure**: Use fallback naming with "Unknown"
- **File permission errors**: Log error and continue monitoring
- **Network connectivity issues**: Queue for retry when connection restored

### 5.2 Edge Cases
- **Multiple receipts in one image**: Process first detected receipt
- **Poor image quality**: Apply image enhancement before processing
- **Non-English receipts**: Support basic multilingual text extraction
- **Handwritten receipts**: Attempt processing with lower confidence threshold
- **Duplicate files**: Skip processing if file already exists with target name

---

## 6. Validation Criteria

### 7.1 Functional Validation
- [ ] Application starts and monitors designated folder
- [ ] Processes new image files within 5 seconds
- [ ] Extracts vendor name with 95%+ accuracy using Pydantic AI
- [ ] Extracts date with 90%+ accuracy with proper validation
- [ ] Extracts amount with 95%+ accuracy as Decimal type
- [ ] Renames files according to specified format
- [ ] Handles errors gracefully without crashing
- [ ] Logs all processing activities with structured data
- [ ] Maintains processing status tracking in JSON log file
- [ ] Provides accurate log querying and filtering capabilities
- [ ] Generates meaningful processing reports and analytics
- [ ] Validates extracted data using Pydantic models
- [ ] Supports comprehensive status tracking through complete workflow
- [ ] Enables manual status updates via CLI commands
- [ ] Provides email integration for receipt submission
- [ ] Tracks payment status and reconciliation
- [ ] Maintains complete audit trail of status transitions

### 7.2 Performance Validation
- [ ] Memory usage stays below 500MB
- [ ] CPU usage below 20% during idle
- [ ] Processes 10+ concurrent images without issues
- [ ] Maintains 99%+ uptime over 24-hour period

### 7.3 User Experience Validation
- [ ] Clear command-line help and documentation
- [ ] Intuitive configuration file format
- [ ] Meaningful error messages and troubleshooting info
- [ ] Easy installation and setup process

---

## 8. Future Enhancements

### 8.1 Phase 2 Features
- **Advanced Analytics**: Spending pattern analysis and trend visualization
- **Web Dashboard**: Simple web interface for monitoring and configuration
- **Export Capabilities**: Export data to CSV, Excel, QuickBooks, or accounting software
- **Receipt Categories**: Automatic categorization of expense types using AI
- **Duplicate Detection**: Identify and handle duplicate receipts
- **OCR Confidence Scoring**: Advanced confidence metrics and manual review workflows

### 8.2 Phase 3 Features
- **Multi-folder Monitoring**: Watch multiple folders simultaneously
- **Cloud Storage Integration**: Process files from Dropbox, Google Drive
- **Advanced Analytics**: Spending patterns and trend analysis
- **Mobile App**: Companion app for configuration and monitoring

---

## 9. Dependencies and Assumptions

### 9.1 External Dependencies
- macOS 12.0+ (Monterey or later)
- Python 3.9+ with Pydantic AI framework
- Internet connectivity for AI vision API (OpenAI, Anthropic)
- Sufficient disk space for image processing and JSON log file storage
- Pydantic Logfire account (optional, for advanced monitoring)

### 9.2 Assumptions
- Receipt images are clear and readable
- Receipts contain standard vendor, date, and amount information
- Users have basic command-line interface knowledge
- AI vision API has sufficient quota and reliability

---

## 10. Risks and Mitigation

### 10.1 Technical Risks
- **AI API reliability**: Implement local fallback models
- **Image processing performance**: Optimize with caching and batching
- **File system monitoring accuracy**: Use multiple monitoring strategies

### 10.2 Business Risks
- **Data privacy concerns**: Implement local processing options
- **API cost escalation**: Monitor usage and implement cost controls
- **User adoption**: Provide comprehensive documentation and examples

---

## 11. Conclusion

This PRD outlines a comprehensive solution for automated receipt processing that leverages Pydantic AI for structured data extraction and maintains detailed processing logs with status tracking. The application addresses the core need for efficient expense tracking while maintaining simplicity, reliability, and comprehensive auditability. 

Key enhancements in this version include:
- **Structured Data Validation**: Using Pydantic models for type-safe data extraction and validation
- **Comprehensive Logging**: JSON file storing detailed processing logs with enhanced status tracking
- **Advanced Monitoring**: Pydantic Logfire integration for AI model observability
- **Robust Error Handling**: Structured error tracking with automatic retry mechanisms
- **Rich Querying**: Advanced log filtering, reporting, and analytics capabilities
- **End-to-End Workflow**: Complete receipt lifecycle from processing through payment reconciliation
- **Email Integration**: Automated receipt submission to accounting systems
- **Payment Tracking**: Full payment status monitoring and reconciliation capabilities
- **Audit Trail**: Complete history of status changes with user actions and timestamps

The application will significantly reduce manual data entry while providing complete visibility into the processing workflow, from initial receipt capture through final payment reconciliation, creating a comprehensive expense management automation solution.
