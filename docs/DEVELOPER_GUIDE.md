# Developer Guide

This guide provides comprehensive information for developers who want to contribute to, extend, or integrate with the Receipt Processor system.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Code Structure](#code-structure)
- [API Development](#api-development)
- [Testing](#testing)
- [Contributing](#contributing)
- [Advanced Topics](#advanced-topics)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of Python, Pydantic, and async programming
- Familiarity with AI/ML concepts (helpful but not required)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test

# Start development server
make dev
```

## Architecture Overview

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │    │   REST API      │    │   Web Interface │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Core Processor │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI Vision      │    │  File Manager   │    │  Storage        │
│  Service        │    │                 │    │  Manager        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Data Models    │
                    │  (Pydantic)     │
                    └─────────────────┘
```

### Core Components

1. **CLI Interface**: Command-line interface for user interaction
2. **REST API**: HTTP API for external integrations
3. **Core Processor**: Main processing logic and orchestration
4. **AI Vision Service**: AI-powered data extraction
5. **File Manager**: File operations and organization
6. **Storage Manager**: Data persistence and retrieval
7. **Data Models**: Pydantic models for data validation

### Data Flow

```
Image Input → AI Processing → Data Extraction → Validation → Storage → Reporting
     │              │              │              │          │         │
     │              │              │              │          │         │
     ▼              ▼              ▼              ▼          ▼         ▼
File Manager → AI Service → ReceiptData → Validation → JSON Storage → Reports
```

## Development Setup

### Environment Setup

1. **Clone Repository:**
   ```bash
   git clone https://github.com/receipt-processor/receipt-processor.git
   cd receipt-processor
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   # Install package in development mode
   pip install -e .
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

4. **Configure Environment:**
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

### Development Tools

**Code Quality:**
```bash
# Run linting
make lint

# Format code
make format

# Type checking
make type-check

# Security scanning
make security
```

**Testing:**
```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage
make test-coverage
```

**Development Server:**
```bash
# Start development server
make dev

# Start with hot reload
make dev-watch
```

## Code Structure

### Directory Structure

```
receipt-processor/
├── src/receipt_processor/          # Main source code
│   ├── __init__.py
│   ├── cli.py                      # CLI interface
│   ├── models.py                   # Data models
│   ├── ai_vision.py               # AI service integration
│   ├── file_manager.py            # File operations
│   ├── storage.py                 # Data persistence
│   ├── reporting.py               # Report generation
│   ├── email_system.py            # Email integration
│   ├── payment_models.py          # Payment data models
│   ├── payment_workflow.py        # Payment processing
│   ├── daemon.py                  # Background service
│   ├── concurrent_processor.py    # Concurrent processing
│   ├── error_handling.py          # Error handling
│   └── system_monitoring.py       # System monitoring
├── tests/                         # Test suite
│   ├── conftest.py               # Test configuration
│   ├── test_unit_*.py            # Unit tests
│   ├── test_integration_*.py     # Integration tests
│   └── test_e2e_*.py             # End-to-end tests
├── docs/                         # Documentation
├── examples/                     # Example code
├── scripts/                      # Utility scripts
├── pyproject.toml               # Project configuration
├── pytest.ini                   # Test configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
└── Makefile                     # Development commands
```

### Key Modules

#### Core Modules

**`models.py`**: Pydantic data models
```python
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class ReceiptData(BaseModel):
    vendor_name: Optional[str] = Field(None, description="Vendor name")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    total_amount: Optional[Decimal] = Field(None, description="Total amount")
    currency: Optional[str] = Field(None, description="Currency code")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
```

**`ai_vision.py`**: AI service integration
```python
class AIVisionService:
    def __init__(self, config: AIVisionConfig):
        self.config = config
        self.client = self._create_client()
    
    async def extract_receipt_data(self, image_path: str) -> ReceiptData:
        # AI processing logic
        pass
```

**`storage.py`**: Data persistence
```python
class JSONStorageManager:
    def __init__(self, log_file: Path):
        self.log_file = log_file
    
    def save_log(self, log_entry: ProcessingLog) -> bool:
        # Save to JSON file
        pass
    
    def load_logs(self, filters: Optional[Dict] = None) -> List[ProcessingLog]:
        # Load from JSON file
        pass
```

#### Integration Modules

**`email_system.py`**: Email integration
```python
class EmailSystem:
    def __init__(self, config: EmailConfig):
        self.config = config
        self.smtp_client = self._create_smtp_client()
    
    async def send_email(self, message: EmailMessage) -> bool:
        # Send email
        pass
```

**`payment_workflow.py`**: Payment processing
```python
class PaymentWorkflowEngine:
    def __init__(self, config: PaymentWorkflowConfig):
        self.config = config
        self.rules = self._load_rules()
    
    def process_payment(self, payment: Payment) -> PaymentResult:
        # Process payment workflow
        pass
```

### Data Models

#### Core Models

**ReceiptData**: Extracted receipt information
```python
class ReceiptData(BaseModel):
    vendor_name: Optional[str] = None
    transaction_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    tax_amount: Optional[Decimal] = None
    tip_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
```

**ProcessingLog**: Processing log entry
```python
class ProcessingLog(BaseModel):
    log_id: str
    file_path: str
    original_filename: str
    status: ProcessingStatus
    vendor_name: Optional[str] = None
    transaction_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    processing_time: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### Payment Models

**Payment**: Payment tracking
```python
class Payment(BaseModel):
    payment_id: str
    receipt_log_id: str
    amount: Decimal = Field(gt=0)
    currency: str
    payment_type: PaymentType
    payment_method: PaymentMethod
    status: PaymentStatus
    recipient: PaymentRecipient
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### Error Models

**ErrorInfo**: Error information
```python
class ErrorInfo(BaseModel):
    error_id: str
    exception_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: str
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    recovery_attempted: bool = False
    resolved: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)
```

## API Development

### REST API

The system provides a REST API for external integrations.

#### API Endpoints

**Health Check:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": __version__
    }
```

**Process Image:**
```python
@app.post("/process")
async def process_image(
    image: UploadFile = File(...),
    confidence_threshold: float = 0.8
):
    # Process image
    result = await processor.process_image(image.file)
    return {"success": True, "data": result}
```

**Get Status:**
```python
@app.get("/status")
async def get_status(
    limit: int = 10,
    status: Optional[str] = None
):
    # Get processing status
    logs = storage.load_logs(limit=limit, status=status)
    return {"logs": logs}
```

#### API Documentation

The API includes automatic documentation:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`

### Webhook Integration

**Webhook Events:**
```python
class WebhookEvent(BaseModel):
    event: str
    timestamp: datetime
    data: Dict[str, Any]

# Send webhook
async def send_webhook(event: WebhookEvent):
    async with httpx.AsyncClient() as client:
        await client.post(
            webhook_url,
            json=event.dict(),
            headers={"X-Webhook-Signature": signature}
        )
```

### Python API

**Core Processor:**
```python
class ReceiptProcessor:
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.ai_service = AIVisionService(config.ai_vision)
        self.storage = JSONStorageManager(config.storage)
    
    async def process_image(self, image_path: str) -> ReceiptData:
        # Process single image
        pass
    
    async def process_directory(self, directory_path: str) -> List[ReceiptData]:
        # Process directory
        pass
```

## Testing

### Test Structure

**Unit Tests:**
```python
def test_receipt_data_creation():
    receipt = ReceiptData(
        vendor_name="Test Restaurant",
        total_amount=25.50,
        confidence_score=0.95
    )
    assert receipt.vendor_name == "Test Restaurant"
    assert receipt.total_amount == 25.50
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_ai_vision_integration():
    ai_service = AIVisionService(config)
    result = await ai_service.extract_receipt_data("test_image.jpg")
    assert result.vendor_name is not None
```

**End-to-End Tests:**
```python
def test_complete_processing_workflow():
    # Test complete workflow
    result = runner.invoke(cli, ['process', '/path/to/images'])
    assert result.exit_code == 0
```

### Test Configuration

**pytest.ini:**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=src/receipt_processor
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
```

**conftest.py:**
```python
@pytest.fixture
def sample_receipt_data():
    return ReceiptData(
        vendor_name="Test Restaurant",
        total_amount=25.50,
        confidence_score=0.95
    )

@pytest.fixture
def mock_ai_service():
    mock = Mock()
    mock.extract_receipt_data.return_value = sample_receipt_data()
    return mock
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage
make test-coverage

# Run specific test
pytest tests/test_models.py::TestReceiptData::test_creation
```

## Contributing

### Development Workflow

1. **Fork Repository:**
   ```bash
   # Fork on GitHub, then clone
   git clone https://github.com/your-username/receipt-processor.git
   cd receipt-processor
   ```

2. **Create Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes:**
   - Write code
   - Add tests
   - Update documentation

4. **Run Tests:**
   ```bash
   make test
   make lint
   make type-check
   ```

5. **Commit Changes:**
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

6. **Push and Create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Code Standards

**Python Style:**
- Follow PEP 8
- Use type hints
- Write docstrings
- Use meaningful variable names

**Code Formatting:**
```bash
# Format code
make format

# Check formatting
make lint
```

**Type Checking:**
```bash
# Run type checking
make type-check
```

### Pull Request Guidelines

1. **Clear Description**: Explain what the PR does
2. **Tests**: Include tests for new functionality
3. **Documentation**: Update relevant documentation
4. **Breaking Changes**: Clearly mark breaking changes
5. **Screenshots**: Include screenshots for UI changes

### Issue Reporting

**Bug Reports:**
- Use the bug report template
- Include system information
- Provide steps to reproduce
- Include error logs

**Feature Requests:**
- Use the feature request template
- Explain the use case
- Provide examples if possible

## Advanced Topics

### Custom AI Providers

**Implement Custom Provider:**
```python
class CustomAIProvider(AIProvider):
    def __init__(self, config: AIConfig):
        self.config = config
        self.client = self._create_client()
    
    async def extract_data(self, image_path: str) -> ReceiptData:
        # Custom extraction logic
        pass
```

**Register Provider:**
```python
# In ai_vision.py
PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "custom": CustomAIProvider
}
```

### Custom Data Models

**Extend Base Models:**
```python
class CustomReceiptData(ReceiptData):
    custom_field: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('custom_field')
    def validate_custom_field(cls, v):
        if v and len(v) < 3:
            raise ValueError('Custom field must be at least 3 characters')
        return v
```

### Custom Processing Steps

**Add Processing Step:**
```python
class CustomProcessingStep(ProcessingStep):
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    async def process(self, data: ReceiptData) -> ReceiptData:
        # Custom processing logic
        return data
```

**Register Step:**
```python
# In processing pipeline
PROCESSING_STEPS = [
    AIVisionStep,
    ValidationStep,
    CustomProcessingStep,  # Add custom step
    StorageStep
]
```

### Performance Optimization

**Async Processing:**
```python
async def process_batch_async(image_paths: List[str]) -> List[ReceiptData]:
    tasks = [process_image_async(path) for path in image_paths]
    results = await asyncio.gather(*tasks)
    return results
```

**Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_ai_call(image_hash: str) -> ReceiptData:
    # Cached AI processing
    pass
```

**Memory Optimization:**
```python
class MemoryEfficientProcessor:
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory = max_memory_mb * 1024 * 1024
        self.current_memory = 0
    
    def check_memory(self):
        if self.current_memory > self.max_memory:
            self.cleanup_memory()
```

### Monitoring and Observability

**Custom Metrics:**
```python
class CustomMetrics:
    def __init__(self):
        self.processing_time = Histogram('processing_time_seconds')
        self.error_count = Counter('errors_total')
        self.success_count = Counter('success_total')
    
    def record_processing_time(self, duration: float):
        self.processing_time.observe(duration)
    
    def record_error(self, error_type: str):
        self.error_count.labels(type=error_type).inc()
```

**Logging:**
```python
import structlog

logger = structlog.get_logger()

def process_image(image_path: str):
    logger.info("Processing image", image_path=image_path)
    try:
        result = ai_service.extract_data(image_path)
        logger.info("Processing successful", confidence=result.confidence_score)
        return result
    except Exception as e:
        logger.error("Processing failed", error=str(e), image_path=image_path)
        raise
```

---

For more information, please refer to the [User Manual](USER_MANUAL.md) or [API Documentation](API_DOCUMENTATION.md).
