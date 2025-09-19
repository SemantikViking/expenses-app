# Receipt Processor - AI-Powered Receipt Processing System

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/receipt-processor/receipt-processor)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](https://github.com/receipt-processor/receipt-processor)

An intelligent, AI-powered receipt processing system that automatically extracts data from receipt images, processes payments, and provides comprehensive reporting and analytics.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install receipt-processor

# Or install from source
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor
pip install -e .
```

### Basic Usage

```bash
# Process a single receipt image
receipt-processor process /path/to/receipt.jpg

# Process all images in a directory
receipt-processor process /path/to/receipts/ --batch-size 10

# Check processing status
receipt-processor status

# Generate reports
receipt-processor report --type summary
```

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Functionality
- **AI-Powered Data Extraction**: Automatically extracts vendor, date, amount, and items from receipt images
- **Intelligent File Management**: Renames and organizes files based on extracted data
- **Payment Processing**: Tracks payments, approvals, and disbursements
- **Email Integration**: Sends notifications and reports via email
- **Comprehensive Reporting**: Generates detailed analytics and reports

### Advanced Features
- **Background Processing**: Runs as a daemon service for continuous monitoring
- **Concurrent Processing**: Multi-threaded processing for high throughput
- **Error Handling**: Robust error recovery and retry mechanisms
- **System Monitoring**: Real-time health checks and performance metrics
- **Data Export**: Export data in multiple formats (JSON, CSV, Excel)

### Supported Formats
- **Image Formats**: JPEG, PNG, TIFF, WebP
- **AI Providers**: OpenAI GPT-4 Vision, Anthropic Claude, Google Vision
- **Email Providers**: Gmail, Outlook, SMTP
- **Export Formats**: JSON, CSV, Excel, PDF

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space
- Internet connection for AI services

### Option 1: PyPI Installation (Recommended)

```bash
pip install receipt-processor
```

### Option 2: Source Installation

```bash
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor
pip install -e .
```

### Option 3: Development Installation

```bash
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor
pip install -e ".[dev]"
```

### Verify Installation

```bash
receipt-processor --version
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in your project directory:

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

Create a `config.yaml` file:

```yaml
ai_vision:
  provider: "openai"  # openai, anthropic, google
  model: "gpt-4-vision-preview"
  max_retries: 3
  timeout: 30

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "your_email@gmail.com"
  password: "your_app_password"
  use_tls: true

processing:
  max_workers: 4
  batch_size: 10
  confidence_threshold: 0.8
  retry_attempts: 3

storage:
  log_file: "receipt_processing_log.json"
  backup_directory: "./backup"
  retention_days: 30
```

## 📖 Usage

### Command Line Interface

#### Basic Commands

```bash
# Process images
receipt-processor process /path/to/images

# Check status
receipt-processor status

# View logs
receipt-processor logs

# Generate reports
receipt-processor report --type summary

# Check system health
receipt-processor health
```

#### Advanced Commands

```bash
# Start background daemon
receipt-processor daemon-start --watch-dir /path/to/watch

# Process with specific settings
receipt-processor process /path/to/images --batch-size 5 --confidence 0.9

# Generate custom reports
receipt-processor report --type vendor --date-from 2024-01-01 --date-to 2024-01-31

# Monitor system performance
receipt-processor metrics --duration 60

# View error logs
receipt-processor error-log --severity high
```

### Python API

```python
from receipt_processor import ReceiptProcessor, ProcessingConfig

# Initialize processor
config = ProcessingConfig(
    ai_provider="openai",
    confidence_threshold=0.8,
    max_workers=4
)
processor = ReceiptProcessor(config)

# Process single image
result = processor.process_image("/path/to/receipt.jpg")
print(f"Vendor: {result.vendor_name}")
print(f"Amount: {result.total_amount}")

# Process directory
results = processor.process_directory("/path/to/receipts/")
for result in results:
    print(f"Processed: {result.file_path}")
```

### Background Processing

```bash
# Start daemon service
receipt-processor daemon-start \
  --watch-dir /path/to/watch \
  --max-workers 4 \
  --memory-limit 1024

# Check daemon status
receipt-processor daemon-status

# Stop daemon
receipt-processor daemon-stop
```

## 📊 Reports and Analytics

### Report Types

- **Summary**: Overview of all processing activities
- **Vendor**: Analysis by vendor/merchant
- **Workflow**: Processing workflow statistics
- **Payment**: Payment tracking and status
- **Audit**: Detailed audit trail

### Generating Reports

```bash
# Summary report
receipt-processor report --type summary

# Vendor analysis
receipt-processor report --type vendor --format json

# Custom date range
receipt-processor report --type summary \
  --date-from 2024-01-01 \
  --date-to 2024-01-31

# Export to file
receipt-processor report --type summary \
  --format csv \
  --output report.csv
```

## 🔍 Monitoring and Health Checks

### System Health

```bash
# Check overall health
receipt-processor health

# View detailed metrics
receipt-processor metrics --duration 60

# Check alerts
receipt-processor alerts

# View error logs
receipt-processor error-log
```

### Performance Monitoring

```bash
# Real-time metrics
receipt-processor metrics --format json

# Resource usage
receipt-processor health --show-resources

# Processing statistics
receipt-processor status --show-stats
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. AI Service Errors

**Problem**: "AI service unavailable" error
**Solution**: 
- Check API key configuration
- Verify internet connection
- Check API quota and limits

```bash
# Test AI service
receipt-processor test-ai --provider openai
```

#### 2. Email Delivery Issues

**Problem**: Emails not being sent
**Solution**:
- Verify SMTP credentials
- Check email provider settings
- Enable app passwords for Gmail

```bash
# Test email configuration
receipt-processor test-email
```

#### 3. File Processing Errors

**Problem**: Images not being processed
**Solution**:
- Check file permissions
- Verify image format support
- Check disk space

```bash
# Check file permissions
receipt-processor check-files /path/to/images
```

#### 4. Performance Issues

**Problem**: Slow processing
**Solution**:
- Increase max workers
- Check system resources
- Optimize image sizes

```bash
# Check system resources
receipt-processor health --show-resources
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Enable debug mode
export RECEIPT_PROCESSOR_DEBUG=1
receipt-processor process /path/to/images --verbose
```

### Log Files

Check log files for detailed error information:

```bash
# View processing logs
receipt-processor logs --level debug

# View error logs
receipt-processor error-log --recent 10

# Export logs
receipt-processor export --format json --output logs.json
```

## ❓ FAQ

### General Questions

**Q: What image formats are supported?**
A: JPEG, PNG, TIFF, and WebP formats are supported. Images should be clear and well-lit for best results.

**Q: How accurate is the data extraction?**
A: Accuracy depends on image quality and receipt clarity. Typical accuracy is 85-95% with good quality images.

**Q: Can I process receipts in different languages?**
A: Yes, the system supports receipts in multiple languages, though English receipts typically have higher accuracy.

**Q: Is my data secure?**
A: Yes, all data is processed locally and only sent to AI services for analysis. No data is stored on external servers.

### Technical Questions

**Q: What are the system requirements?**
A: Python 3.8+, 4GB RAM minimum, 1GB free disk space, and internet connection for AI services.

**Q: Can I run this on a server?**
A: Yes, the system can run as a daemon service on servers for continuous processing.

**Q: How do I backup my data?**
A: The system automatically creates backups of log files. You can also export data using the export command.

**Q: Can I customize the AI prompts?**
A: Yes, you can customize AI prompts and processing logic through configuration files.

### Integration Questions

**Q: Can I integrate this with my existing system?**
A: Yes, the system provides a Python API and can be integrated with existing workflows.

**Q: Does it support webhooks?**
A: Yes, webhooks are supported for real-time notifications of processing events.

**Q: Can I use my own AI models?**
A: Yes, the system supports custom AI models and local processing options.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor

# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run linting
make lint
```

### Reporting Issues

Please report issues on our [GitHub Issues](https://github.com/receipt-processor/receipt-processor/issues) page.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 Vision API
- Anthropic for Claude API
- The Python community for excellent libraries
- All contributors and users

## 📞 Support

- **Documentation**: [https://receipt-processor.readthedocs.io](https://receipt-processor.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/receipt-processor/receipt-processor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/receipt-processor/receipt-processor/discussions)
- **Email**: support@receipt-processor.com

---

**Made with ❤️ by the Receipt Processor Team**
