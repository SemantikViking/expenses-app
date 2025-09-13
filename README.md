# Receipt Processing Application

A macOS command-line application that automatically processes receipt images using AI vision to extract vendor information, dates, and amounts, with comprehensive workflow tracking from processing through payment reconciliation.

## 🚀 Features

- **Automated Receipt Processing**: Monitor folders for new receipt images and extract data using AI vision
- **Comprehensive Status Tracking**: Full workflow from processing through email submission and payment reconciliation
- **Email Integration**: Automated receipt submission to accounting systems via email
- **Payment Tracking**: Monitor payment status and reconciliation with accounting systems
- **Structured Data Storage**: JSON-based logging with complete audit trail
- **Advanced Reporting**: Analytics, vendor analysis, and workflow bottleneck identification
- **Command-Line Interface**: Full CLI with status management and bulk operations

## 📋 Status Workflow

```
pending → processing → [error/no_data_extracted/processed] → emailed → submitted → payment_received
                    ↓
                   retry (automatic recovery)
```

## 🛠️ Technology Stack

- **Language**: Python 3.9+
- **AI Framework**: Pydantic AI for structured data extraction
- **Computer Vision**: OpenAI GPT-4 Vision API, Anthropic Claude Vision
- **File Monitoring**: `watchdog` for cross-platform monitoring
- **Data Validation**: Pydantic for type-safe models
- **Email**: SMTP integration with template system
- **Storage**: JSON file-based logging with 180-day retention

## 📦 Installation

### Prerequisites

- macOS 12.0+ (Monterey or later)
- Python 3.9 or higher
- OpenAI API key (for AI vision processing)
- SMTP server access (for email integration)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/receipt-processor.git
cd receipt-processor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
receipt-processor init
```

## 🔧 Configuration

Create a `.env` file with your settings:

```env
# AI Vision Settings
AI_VISION__PROVIDER=openai
AI_VISION__API_KEY=your_openai_api_key_here
AI_VISION__MODEL=gpt-4-vision-preview

# Monitoring Settings
MONITORING__WATCH_FOLDER=/Users/username/Desktop/Receipts
MONITORING__FILE_EXTENSIONS=[".jpg", ".jpeg", ".png", ".heic"]

# Email Settings (Optional)
EMAIL__ENABLE_EMAIL=true
EMAIL__SMTP_SERVER=smtp.gmail.com
EMAIL__SMTP_PORT=587
EMAIL__SMTP_USERNAME=your_email@gmail.com
EMAIL__SMTP_PASSWORD=your_app_password

# Payment Settings (Optional)
PAYMENT__ENABLE_PAYMENT_TRACKING=true
PAYMENT__DEFAULT_PAYMENT_SYSTEM=manual
```

## 🚀 Usage

### Basic Commands

```bash
# Start background monitoring
receipt-processor start

# Process existing files
receipt-processor process --folder /path/to/receipts

# Check application status
receipt-processor status

# View processing logs
receipt-processor logs --recent 24h
```

### Status Management

```bash
# Update receipt status manually
receipt-processor update-status --id <receipt-id> --status emailed

# Send receipt via email
receipt-processor email --id <receipt-id> --to accounting@company.com

# Mark as submitted for payment
receipt-processor submit --id <receipt-id> --payment-system quickbooks

# Record payment received
receipt-processor payment-received --id <receipt-id> --amount 45.67
```

### Reporting & Analytics

```bash
# Generate reports
receipt-processor report --from 2025-06-01 --to 2025-12-31

# Export data
receipt-processor export --format csv --output receipts_2025.csv

# View statistics
receipt-processor stats --period monthly --include-payment-status
```

## 📊 File Naming Convention

Processed receipts are automatically renamed using the format:
```
YYYY-MM-DD_VendorName_Amount.ext
```

**Examples:**
- `2025-09-15_Starbucks_12.50.jpg`
- `2025-08-22_Amazon_89.99.png`
- `2025-07-10_GasStation_45.67.heic`

## 📁 Project Structure

```
receipt-processor/
├── src/receipt_processor/          # Main application package
│   ├── config.py                   # Configuration models
│   ├── monitor.py                  # File system monitoring
│   ├── vision.py                   # AI vision integration
│   ├── status.py                   # Status management
│   ├── email.py                    # Email integration
│   ├── payment.py                  # Payment tracking
│   ├── logger.py                   # JSON logging system
│   ├── reports.py                  # Analytics and reporting
│   └── cli.py                      # Command-line interface
├── tests/                          # Test suite
├── tasks/                          # Project documentation
│   ├── PRD_Receipt_Processor.md    # Product Requirements Document
│   └── Task_List_Receipt_Processor.md # Development task list
├── requirements.txt                # Python dependencies
├── .env.example                    # Configuration template
└── README.md                       # This file
```

## 🔍 Status Tracking

The application maintains comprehensive status tracking for each receipt:

- **pending**: File detected, queued for processing
- **processing**: Currently being processed by AI
- **error**: Processing failed with technical error
- **no_data_extracted**: AI couldn't extract meaningful data
- **processed**: Successfully extracted and renamed
- **emailed**: Receipt sent via email
- **submitted**: Receipt submitted for payment processing
- **payment_received**: Payment received and reconciled

## 📈 Reporting Features

- **Daily Summary**: Processing counts, success rates, error analysis
- **Vendor Analysis**: Spending by vendor, frequency analysis
- **Workflow Reports**: Status transition analytics, bottleneck identification
- **Payment Reports**: Outstanding payments, reconciliation status
- **Email Reports**: Delivery status and engagement tracking
- **Audit Reports**: Complete status change history

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/receipt_processor

# Run specific test category
pytest tests/test_vision.py
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 src/ tests/
black src/ tests/
mypy src/

# Pre-commit hooks
pre-commit install
```

## 📚 Documentation

- [Product Requirements Document](tasks/PRD_Receipt_Processor.md) - Comprehensive feature specification
- [Development Task List](tasks/Task_List_Receipt_Processor.md) - Implementation roadmap
- [API Documentation](docs/api.md) - Detailed API reference (coming soon)
- [Configuration Guide](docs/configuration.md) - Advanced configuration options (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

- API keys are stored securely in environment variables
- No sensitive receipt data is stored beyond processing
- Email credentials use secure authentication methods
- Local processing options available to avoid cloud dependencies

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/receipt-processor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/receipt-processor/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/receipt-processor/wiki)

## 🗺️ Roadmap

- **Phase 1**: Core processing and AI integration ✅
- **Phase 2**: Email and payment tracking ✅
- **Phase 3**: Advanced analytics and reporting 🚧
- **Phase 4**: Web dashboard interface 📋
- **Phase 5**: Mobile companion app 📋

---

**Built with ❤️ for automated expense management**
