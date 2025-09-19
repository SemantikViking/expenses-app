# Frequently Asked Questions (FAQ)

This document answers the most common questions about the Receipt Processor system.

## Table of Contents

- [General Questions](#general-questions)
- [Installation Questions](#installation-questions)
- [Configuration Questions](#configuration-questions)
- [Usage Questions](#usage-questions)
- [Technical Questions](#technical-questions)
- [Troubleshooting Questions](#troubleshooting-questions)
- [Integration Questions](#integration-questions)
- [Performance Questions](#performance-questions)

## General Questions

### What is the Receipt Processor?

The Receipt Processor is an AI-powered system that automatically extracts data from receipt images, processes payments, and provides comprehensive reporting and analytics. It uses advanced computer vision and natural language processing to identify vendors, dates, amounts, and other key information from receipt images.

### What types of receipts can it process?

The system can process receipts from various sources including:
- Restaurants and cafes
- Retail stores
- Gas stations
- Hotels and travel
- Office supplies
- Medical expenses
- Transportation (taxis, rideshare, etc.)
- Online purchases
- And many more

### What image formats are supported?

Supported image formats include:
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- WebP (.webp)

### How accurate is the data extraction?

Accuracy depends on image quality and receipt clarity:
- **High-quality images**: 90-95% accuracy
- **Good-quality images**: 85-90% accuracy
- **Poor-quality images**: 70-85% accuracy

Factors affecting accuracy:
- Image resolution and clarity
- Receipt condition (wrinkled, torn, etc.)
- Lighting conditions
- Receipt format and layout
- Language and font readability

### Is my data secure?

Yes, data security is a top priority:
- All data is processed locally on your system
- Only image data is sent to AI services for analysis
- No personal or financial data is stored on external servers
- All communications are encrypted
- You can run the system completely offline (with local AI models)

### What languages are supported?

The system supports receipts in multiple languages:
- English (primary, highest accuracy)
- Spanish
- French
- German
- Italian
- Portuguese
- Chinese (Simplified and Traditional)
- Japanese
- Korean
- And many others

## Installation Questions

### What are the system requirements?

**Minimum Requirements:**
- Python 3.8 or higher
- 4GB RAM
- 1GB free disk space
- Internet connection for AI services

**Recommended Requirements:**
- Python 3.9 or higher
- 16GB RAM
- 10GB free disk space
- Stable broadband connection
- Multi-core processor

### How do I install the Receipt Processor?

**Option 1: PyPI Installation (Recommended)**
```bash
pip install receipt-processor
```

**Option 2: Source Installation**
```bash
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor
pip install -e .
```

**Option 3: Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install receipt-processor
```

### Do I need to install additional dependencies?

No, the installation includes all required dependencies. However, for development or specific features, you may want to install additional packages:

```bash
# Development dependencies
pip install receipt-processor[dev]

# All optional dependencies
pip install receipt-processor[all]
```

### Can I install it on Windows/Mac/Linux?

Yes, the Receipt Processor supports:
- **Windows**: 10, 11 (with Python 3.8+)
- **macOS**: 10.14+ (with Python 3.8+)
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+

### How do I verify the installation?

```bash
# Check version
receipt-processor --version

# Test basic functionality
receipt-processor --help

# Validate configuration
receipt-processor config validate
```

## Configuration Questions

### How do I configure API keys?

**Method 1: Environment Variables**
```bash
export OPENAI_API_KEY="your_api_key_here"
export ANTHROPIC_API_KEY="your_api_key_here"
```

**Method 2: Configuration File**
```yaml
ai_vision:
  provider: "openai"
  api_key: "your_api_key_here"
```

**Method 3: Command Line**
```bash
receipt-processor config set ai_vision.api_key "your_api_key_here"
```

### Which AI provider should I use?

**OpenAI (Recommended):**
- Highest accuracy
- Fastest processing
- Most reliable
- Requires API key

**Anthropic:**
- Good accuracy
- Alternative to OpenAI
- Requires API key

**Google Vision:**
- Good for specific use cases
- Requires API key
- May have different accuracy patterns

### How do I configure email notifications?

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "your_email@gmail.com"
  password: "your_app_password"
  use_tls: true
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an app password
3. Use the app password in configuration

### Can I customize the processing behavior?

Yes, you can customize many aspects:

```yaml
processing:
  max_workers: 4
  batch_size: 10
  confidence_threshold: 0.8
  timeout: 60
  retry_attempts: 3

ai_vision:
  custom_prompts:
    vendor_extraction: "Extract vendor name from receipt"
    amount_extraction: "Extract total amount from receipt"
```

## Usage Questions

### How do I process a single receipt?

```bash
# Basic processing
receipt-processor process /path/to/receipt.jpg

# With options
receipt-processor process /path/to/receipt.jpg \
  --confidence 0.9 \
  --output-dir /path/to/processed
```

### How do I process multiple receipts?

```bash
# Process directory
receipt-processor process /path/to/receipts/

# Process with batch size
receipt-processor process /path/to/receipts/ --batch-size 10

# Process recursively
receipt-processor process /path/to/receipts/ --recursive
```

### How do I run it as a background service?

```bash
# Start daemon
receipt-processor daemon-start --watch-dir /path/to/watch

# Check status
receipt-processor daemon-status

# Stop daemon
receipt-processor daemon-stop
```

### How do I generate reports?

```bash
# Summary report
receipt-processor report --type summary

# Vendor analysis
receipt-processor report --type vendor

# Export to file
receipt-processor report --type summary --format csv --output report.csv
```

### How do I check processing status?

```bash
# Basic status
receipt-processor status

# Detailed status
receipt-processor status --detailed

# Filter by status
receipt-processor status --status completed
```

## Technical Questions

### How does the AI processing work?

1. **Image Analysis**: The system analyzes the receipt image using computer vision
2. **Text Extraction**: OCR extracts text from the image
3. **AI Processing**: AI models analyze the text to identify key information
4. **Data Validation**: Extracted data is validated and structured
5. **Confidence Scoring**: Each extraction is given a confidence score

### Can I use my own AI models?

Yes, you can integrate custom AI models:

```yaml
ai_vision:
  provider: "custom"
  model_endpoint: "http://localhost:8000/predict"
  api_key: "your_custom_api_key"
```

### How does the payment processing work?

1. **Receipt Processing**: Extract payment information from receipts
2. **Payment Creation**: Create payment records with extracted data
3. **Workflow Rules**: Apply business rules for approval/disapproval
4. **Status Tracking**: Track payment status through workflow
5. **Notifications**: Send notifications for status changes

### Can I integrate with external systems?

Yes, the system provides multiple integration options:

**Python API:**
```python
from receipt_processor import ReceiptProcessor
processor = ReceiptProcessor()
result = processor.process_image("receipt.jpg")
```

**REST API:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@receipt.jpg" \
  https://api.receipt-processor.com/v1/process
```

**Webhooks:**
```yaml
webhooks:
  enabled: true
  url: "https://your-app.com/webhooks"
  events: ["processing.completed", "payment.submitted"]
```

### How does the file organization work?

The system can automatically organize processed files:

```yaml
file_management:
  organize_by_date: true
  organize_by_vendor: true
  create_vendor_folders: true
  date_format: "%Y-%m-%d"
  max_files_per_folder: 1000
```

**Example organization:**
```
processed/
├── 2024-01-15/
│   ├── Test_Restaurant/
│   │   ├── 2024-01-15_Test_Restaurant_25.50.jpg
│   │   └── 2024-01-15_Test_Restaurant_15.75.jpg
│   └── Coffee_Shop/
│       └── 2024-01-15_Coffee_Shop_8.50.jpg
```

## Troubleshooting Questions

### Why is my receipt not being processed?

**Common causes:**
1. **File format not supported**: Use JPEG, PNG, TIFF, or WebP
2. **File permissions**: Check file read permissions
3. **File size too large**: Reduce image size
4. **Poor image quality**: Improve lighting and resolution
5. **Configuration issues**: Check API keys and settings

**Solutions:**
```bash
# Check file format
file /path/to/receipt.jpg

# Check permissions
ls -la /path/to/receipt.jpg

# Test with verbose output
receipt-processor process /path/to/receipt.jpg --verbose
```

### Why am I getting low confidence scores?

**Common causes:**
1. **Poor image quality**: Blurry, dark, or distorted images
2. **Unusual receipt format**: Non-standard receipt layouts
3. **Language issues**: Receipts in unsupported languages
4. **Handwritten text**: Difficult to read handwriting

**Solutions:**
1. **Improve image quality**: Better lighting, higher resolution
2. **Lower confidence threshold**: `--confidence 0.7`
3. **Use custom prompts**: Customize AI prompts for your use case
4. **Preprocess images**: Clean up images before processing

### Why is processing slow?

**Common causes:**
1. **High batch size**: Processing too many images at once
2. **Low worker count**: Not enough concurrent workers
3. **Network issues**: Slow AI service responses
4. **System resources**: Insufficient CPU or memory

**Solutions:**
```bash
# Reduce batch size
receipt-processor process /path/to/images --batch-size 5

# Increase workers
receipt-processor daemon-start --max-workers 8

# Check system resources
receipt-processor health --show-resources
```

### Why are emails not being sent?

**Common causes:**
1. **SMTP configuration**: Incorrect server settings
2. **Authentication issues**: Wrong username/password
3. **Network issues**: Firewall or connectivity problems
4. **Email provider limits**: Rate limiting or blocking

**Solutions:**
```bash
# Test email configuration
receipt-processor test-email

# Check SMTP settings
receipt-processor config show | grep -i email

# Use app password for Gmail
# Enable 2-factor authentication first
```

## Integration Questions

### Can I integrate with my existing accounting system?

Yes, the system provides multiple integration options:

**Export Data:**
```bash
# Export to CSV
receipt-processor export --format csv --output receipts.csv

# Export to JSON
receipt-processor export --format json --output receipts.json
```

**API Integration:**
```python
# Get processed data
from receipt_processor import StorageManager
storage = StorageManager()
logs = storage.load_logs()

# Send to accounting system
for log in logs:
    send_to_accounting_system(log)
```

**Webhook Integration:**
```yaml
webhooks:
  enabled: true
  url: "https://your-accounting-system.com/webhooks"
  events: ["processing.completed"]
```

### Can I use it with my existing workflow?

Yes, the system is designed to integrate with existing workflows:

**Command Line Integration:**
```bash
# Process receipts and pipe to other tools
receipt-processor process /path/to/receipts/ | \
  jq '.vendor_name' | \
  sort | uniq -c
```

**Python Integration:**
```python
from receipt_processor import ReceiptProcessor

# Process in your existing Python code
processor = ReceiptProcessor()
result = processor.process_image("receipt.jpg")

# Use result in your workflow
if result.confidence_score > 0.8:
    process_payment(result)
else:
    send_for_manual_review(result)
```

### Can I customize the data extraction?

Yes, you can customize many aspects:

**Custom Prompts:**
```yaml
ai_vision:
  custom_prompts:
    vendor_extraction: |
      Extract the vendor name from this receipt.
      Look for business names, store names, or company names.
      Return only the vendor name, nothing else.
```

**Custom Validation:**
```python
from receipt_processor import ReceiptData

def custom_validation(receipt_data: ReceiptData) -> bool:
    # Custom validation logic
    if receipt_data.vendor_name and receipt_data.total_amount:
        return True
    return False
```

## Performance Questions

### How many receipts can I process per hour?

Performance depends on several factors:

**Typical Performance:**
- **Single-threaded**: 10-20 receipts per hour
- **Multi-threaded (4 workers)**: 40-80 receipts per hour
- **High-performance setup**: 100+ receipts per hour

**Factors affecting performance:**
- Image quality and size
- AI service response time
- System resources (CPU, memory)
- Network speed
- Batch size and worker count

### How can I improve processing speed?

**Optimize Configuration:**
```yaml
processing:
  max_workers: 8
  batch_size: 20
  timeout: 120
  parallel_processing: true
```

**System Optimization:**
- Use SSD storage
- Increase RAM
- Use faster CPU
- Optimize network connection

**Image Optimization:**
- Use appropriate image sizes
- Compress images before processing
- Use consistent image formats

### How much storage space do I need?

**Storage Requirements:**
- **Log files**: ~1MB per 1000 receipts
- **Backup files**: ~2MB per 1000 receipts
- **Temporary files**: ~10MB during processing
- **Total**: ~3MB per 1000 receipts

**Example for 10,000 receipts:**
- Log files: ~10MB
- Backup files: ~20MB
- Temporary files: ~100MB
- **Total**: ~130MB

### Can I run it on a server?

Yes, the system is designed for server deployment:

**Server Requirements:**
- Linux/Windows Server
- Python 3.8+
- 8GB+ RAM
- 50GB+ storage
- Stable internet connection

**Deployment Options:**
- **Docker**: Containerized deployment
- **Systemd**: Linux service
- **Windows Service**: Windows service
- **Cloud**: AWS, Azure, GCP

**Example Docker deployment:**
```bash
docker run -d \
  -v /path/to/receipts:/app/receipts \
  -v /path/to/processed:/app/processed \
  -e OPENAI_API_KEY="your_key" \
  receipt-processor:latest
```

---

For more detailed information, please refer to the [User Manual](USER_MANUAL.md), [API Documentation](API_DOCUMENTATION.md), or [Troubleshooting Guide](TROUBLESHOOTING.md).
