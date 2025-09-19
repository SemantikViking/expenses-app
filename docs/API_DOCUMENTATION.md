# API Documentation

This document provides comprehensive API documentation for the Receipt Processor system, including Python API, REST API, and webhook integrations.

## Table of Contents

- [Python API](#python-api)
- [REST API](#rest-api)
- [Webhook API](#webhook-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Python API

### Core Classes

#### ReceiptProcessor

The main class for processing receipts.

```python
from receipt_processor import ReceiptProcessor, ProcessingConfig

# Initialize processor
config = ProcessingConfig(
    ai_provider="openai",
    confidence_threshold=0.8,
    max_workers=4
)
processor = ReceiptProcessor(config)
```

**Methods:**

##### `process_image(image_path: str) -> ReceiptData`

Process a single receipt image.

```python
result = processor.process_image("/path/to/receipt.jpg")
print(f"Vendor: {result.vendor_name}")
print(f"Amount: {result.total_amount}")
print(f"Date: {result.transaction_date}")
```

**Parameters:**
- `image_path` (str): Path to the receipt image

**Returns:**
- `ReceiptData`: Extracted receipt data

**Raises:**
- `FileNotFoundError`: If image file doesn't exist
- `ProcessingError`: If processing fails
- `ValidationError`: If extracted data is invalid

##### `process_directory(directory_path: str, **kwargs) -> List[ReceiptData]`

Process all images in a directory.

```python
results = processor.process_directory(
    "/path/to/receipts/",
    batch_size=10,
    confidence_threshold=0.9
)
```

**Parameters:**
- `directory_path` (str): Path to directory containing images
- `batch_size` (int, optional): Number of images to process at once
- `confidence_threshold` (float, optional): Minimum confidence threshold
- `recursive` (bool, optional): Process subdirectories recursively

**Returns:**
- `List[ReceiptData]`: List of extracted receipt data

##### `process_batch(image_paths: List[str], **kwargs) -> List[ReceiptData]`

Process a batch of images.

```python
image_paths = ["/path/to/receipt1.jpg", "/path/to/receipt2.jpg"]
results = processor.process_batch(image_paths)
```

**Parameters:**
- `image_paths` (List[str]): List of image file paths
- `confidence_threshold` (float, optional): Minimum confidence threshold

**Returns:**
- `List[ReceiptData]`: List of extracted receipt data

#### ProcessingConfig

Configuration class for the processor.

```python
from receipt_processor import ProcessingConfig

config = ProcessingConfig(
    ai_provider="openai",
    model="gpt-4-vision-preview",
    api_key="your_api_key",
    confidence_threshold=0.8,
    max_workers=4,
    timeout=30,
    max_retries=3
)
```

**Parameters:**
- `ai_provider` (str): AI provider ("openai", "anthropic", "google")
- `model` (str): AI model to use
- `api_key` (str): API key for the AI provider
- `confidence_threshold` (float): Minimum confidence threshold (0.0-1.0)
- `max_workers` (int): Maximum number of concurrent workers
- `timeout` (int): Request timeout in seconds
- `max_retries` (int): Maximum number of retry attempts

#### StorageManager

Class for managing data storage.

```python
from receipt_processor import StorageManager

storage = StorageManager(log_file="receipt_log.json")

# Save processing log
log_entry = ProcessingLog(
    log_id="LOG_001",
    file_path="/path/to/receipt.jpg",
    status=ProcessingStatus.COMPLETED,
    vendor_name="Test Restaurant",
    total_amount=25.50
)
storage.save_log(log_entry)

# Load logs
logs = storage.load_logs()
```

**Methods:**

##### `save_log(log_entry: ProcessingLog) -> bool`

Save a processing log entry.

##### `load_logs(filters: Optional[Dict] = None) -> List[ProcessingLog]`

Load processing logs with optional filters.

##### `update_log(log_id: str, updates: Dict) -> bool`

Update an existing log entry.

##### `delete_log(log_id: str) -> bool`

Delete a log entry.

#### ReportGenerator

Class for generating reports.

```python
from receipt_processor import ReportGenerator

reporter = ReportGenerator(storage)

# Generate summary report
summary = reporter.generate_summary_report(
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 1, 31)
)

# Generate vendor report
vendor_report = reporter.generate_vendor_report()
```

**Methods:**

##### `generate_summary_report(**filters) -> Dict`

Generate a summary report.

##### `generate_vendor_report(**filters) -> Dict`

Generate a vendor analysis report.

##### `generate_workflow_report(**filters) -> Dict`

Generate a workflow statistics report.

### Data Models

#### ReceiptData

Core data model for extracted receipt information.

```python
from receipt_processor import ReceiptData
from datetime import datetime
from decimal import Decimal

receipt = ReceiptData(
    vendor_name="Test Restaurant",
    transaction_date=datetime(2024, 1, 15),
    total_amount=Decimal("25.50"),
    currency="USD",
    items=[
        {"name": "Burger", "price": 15.99, "quantity": 1},
        {"name": "Fries", "price": 4.99, "quantity": 1}
    ],
    tax_amount=Decimal("1.53"),
    tip_amount=Decimal("0.00"),
    payment_method="Credit Card",
    receipt_number="R123456",
    confidence_score=0.95
)
```

**Fields:**
- `vendor_name` (Optional[str]): Name of the vendor/merchant
- `transaction_date` (Optional[datetime]): Date of the transaction
- `total_amount` (Optional[Decimal]): Total amount of the transaction
- `currency` (Optional[str]): Currency code (USD, EUR, etc.)
- `items` (List[Dict]): List of items with name, price, and quantity
- `tax_amount` (Optional[Decimal]): Tax amount
- `tip_amount` (Optional[Decimal]): Tip amount
- `payment_method` (Optional[str]): Payment method used
- `receipt_number` (Optional[str]): Receipt or transaction number
- `confidence_score` (float): AI confidence score (0.0-1.0)

#### ProcessingLog

Data model for processing log entries.

```python
from receipt_processor import ProcessingLog, ProcessingStatus

log = ProcessingLog(
    log_id="LOG_001",
    file_path="/path/to/receipt.jpg",
    original_filename="receipt.jpg",
    status=ProcessingStatus.COMPLETED,
    vendor_name="Test Restaurant",
    transaction_date=datetime(2024, 1, 15),
    total_amount=Decimal("25.50"),
    currency="USD",
    confidence_score=0.95,
    processing_time=2.5,
    error_message=None,
    retry_count=0,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    metadata={"test": True}
)
```

**Fields:**
- `log_id` (str): Unique identifier for the log entry
- `file_path` (str): Path to the processed file
- `original_filename` (str): Original filename
- `status` (ProcessingStatus): Processing status
- `vendor_name` (Optional[str]): Extracted vendor name
- `transaction_date` (Optional[datetime]): Extracted transaction date
- `total_amount` (Optional[Decimal]): Extracted total amount
- `currency` (Optional[str]): Extracted currency
- `confidence_score` (float): AI confidence score
- `processing_time` (float): Processing time in seconds
- `error_message` (Optional[str]): Error message if processing failed
- `retry_count` (int): Number of retry attempts
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp
- `metadata` (Dict): Additional metadata

#### Payment

Data model for payment tracking.

```python
from receipt_processor import Payment, PaymentStatus, PaymentType

payment = Payment(
    payment_id="PAY_001",
    receipt_log_id="LOG_001",
    amount=Decimal("25.50"),
    currency="USD",
    payment_type=PaymentType.EXPENSE,
    status=PaymentStatus.PENDING,
    recipient=PaymentRecipient(
        name="Test Restaurant",
        email="test@restaurant.com"
    ),
    due_date=datetime(2024, 2, 15),
    created_at=datetime.now()
)
```

## REST API

The Receipt Processor provides a REST API for integration with external systems.

### Base URL

```
https://api.receipt-processor.com/v1
```

### Authentication

All API requests require authentication using an API key.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.receipt-processor.com/v1/health
```

### Endpoints

#### Health Check

**GET** `/health`

Check API health and status.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.receipt-processor.com/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.0.0",
  "uptime": 3600
}
```

#### Process Image

**POST** `/process`

Process a single receipt image.

```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -F "image=@receipt.jpg" \
     -F "confidence_threshold=0.8" \
     https://api.receipt-processor.com/v1/process
```

**Request Parameters:**
- `image` (file): Receipt image file
- `confidence_threshold` (float, optional): Minimum confidence threshold

**Response:**
```json
{
  "success": true,
  "data": {
    "vendor_name": "Test Restaurant",
    "transaction_date": "2024-01-15T00:00:00Z",
    "total_amount": 25.50,
    "currency": "USD",
    "items": [
      {"name": "Burger", "price": 15.99, "quantity": 1}
    ],
    "confidence_score": 0.95
  },
  "processing_time": 2.5
}
```

#### Process Batch

**POST** `/process/batch`

Process multiple receipt images.

```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -F "images=@receipt1.jpg" \
     -F "images=@receipt2.jpg" \
     -F "batch_size=10" \
     https://api.receipt-processor.com/v1/process/batch
```

**Request Parameters:**
- `images` (file[]): Array of receipt image files
- `batch_size` (int, optional): Number of images to process at once
- `confidence_threshold` (float, optional): Minimum confidence threshold

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "file_name": "receipt1.jpg",
      "data": {
        "vendor_name": "Test Restaurant",
        "total_amount": 25.50
      },
      "confidence_score": 0.95
    }
  ],
  "total_processed": 2,
  "successful": 2,
  "failed": 0
}
```

#### Get Processing Status

**GET** `/status`

Get processing status and statistics.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.receipt-processor.com/v1/status?limit=10&status=completed"
```

**Query Parameters:**
- `limit` (int, optional): Maximum number of results
- `status` (string, optional): Filter by status
- `vendor` (string, optional): Filter by vendor
- `date_from` (string, optional): Start date filter
- `date_to` (string, optional): End date filter

**Response:**
```json
{
  "total_processed": 100,
  "successful": 95,
  "failed": 5,
  "recent_logs": [
    {
      "log_id": "LOG_001",
      "file_path": "/path/to/receipt.jpg",
      "status": "completed",
      "vendor_name": "Test Restaurant",
      "total_amount": 25.50,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Generate Report

**GET** `/reports/{type}`

Generate various types of reports.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.receipt-processor.com/v1/reports/summary?format=json&date_from=2024-01-01"
```

**Path Parameters:**
- `type` (string): Report type (summary, vendor, workflow, payment, audit)

**Query Parameters:**
- `format` (string, optional): Output format (json, csv, pdf)
- `date_from` (string, optional): Start date filter
- `date_to` (string, optional): End date filter
- `vendor` (string, optional): Filter by vendor

**Response:**
```json
{
  "report_type": "summary",
  "generated_at": "2024-01-15T10:00:00Z",
  "data": {
    "total_receipts": 100,
    "total_amount": 2500.00,
    "average_amount": 25.00,
    "success_rate": 0.95,
    "top_vendors": [
      {"name": "Test Restaurant", "count": 20, "total": 500.00}
    ]
  }
}
```

#### Get System Metrics

**GET** `/metrics`

Get system performance metrics.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.receipt-processor.com/v1/metrics?duration=3600"
```

**Query Parameters:**
- `duration` (int, optional): Duration in seconds

**Response:**
```json
{
  "timestamp": "2024-01-15T10:00:00Z",
  "metrics": {
    "requests_per_second": 10.5,
    "average_response_time": 0.5,
    "error_rate": 0.02,
    "active_connections": 25,
    "cpu_usage": 45.0,
    "memory_usage": 60.0
  }
}
```

## Webhook API

The Receipt Processor can send webhooks for real-time notifications.

### Webhook Configuration

Configure webhooks in your account settings:

```json
{
  "webhook_url": "https://your-app.com/webhooks/receipt-processor",
  "events": ["processing.completed", "processing.failed", "payment.submitted"],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

#### Processing Completed

Sent when a receipt is successfully processed.

```json
{
  "event": "processing.completed",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "log_id": "LOG_001",
    "file_path": "/path/to/receipt.jpg",
    "vendor_name": "Test Restaurant",
    "total_amount": 25.50,
    "confidence_score": 0.95,
    "processing_time": 2.5
  }
}
```

#### Processing Failed

Sent when processing fails.

```json
{
  "event": "processing.failed",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "log_id": "LOG_001",
    "file_path": "/path/to/receipt.jpg",
    "error_message": "AI service unavailable",
    "retry_count": 3
  }
}
```

#### Payment Submitted

Sent when a payment is submitted.

```json
{
  "event": "payment.submitted",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "payment_id": "PAY_001",
    "receipt_log_id": "LOG_001",
    "amount": 25.50,
    "status": "pending"
  }
}
```

### Webhook Security

Webhooks are signed using HMAC-SHA256 for security verification.

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Failed to process image",
    "details": {
      "file_path": "/path/to/receipt.jpg",
      "error_type": "AI_SERVICE_ERROR",
      "retry_after": 30
    },
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_REQUEST` | Invalid request parameters | 400 |
| `UNAUTHORIZED` | Missing or invalid API key | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `PROCESSING_ERROR` | Image processing failed | 422 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

### Retry Logic

The API implements automatic retry logic for transient errors:

- **Retryable errors**: 5xx status codes, rate limiting
- **Retry delay**: Exponential backoff starting at 1 second
- **Max retries**: 3 attempts
- **Retry-After header**: Indicates when to retry

## Rate Limiting

API requests are rate limited to ensure fair usage:

- **Free tier**: 100 requests per hour
- **Pro tier**: 1,000 requests per hour
- **Enterprise**: Custom limits

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## Examples

### Python Integration

```python
import requests
from receipt_processor import ReceiptProcessor

# Using Python API
processor = ReceiptProcessor()
result = processor.process_image("receipt.jpg")

# Using REST API
response = requests.post(
    "https://api.receipt-processor.com/v1/process",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    files={"image": open("receipt.jpg", "rb")}
)
data = response.json()
```

### JavaScript Integration

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('https://api.receipt-processor.com/v1/process', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Webhook Handler

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhooks/receipt-processor', methods=['POST'])
def handle_webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Webhook-Signature')
    
    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        return jsonify({'error': 'Invalid signature'}), 401
    
    event = request.json
    if event['event'] == 'processing.completed':
        # Handle processing completed
        process_completed_receipt(event['data'])
    
    return jsonify({'status': 'success'})

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

For more detailed information, please refer to the [User Manual](USER_MANUAL.md) or [Configuration Reference](CONFIGURATION_REFERENCE.md).
