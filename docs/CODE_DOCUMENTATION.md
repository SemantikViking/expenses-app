# Code Documentation Standards

This document outlines the code documentation standards and provides examples of how to document code in the Receipt Processor project.

## Table of Contents

- [Docstring Standards](#docstring-standards)
- [Code Comments](#code-comments)
- [Type Hints](#type-hints)
- [API Documentation](#api-documentation)
- [Examples](#examples)

## Docstring Standards

### Google Style Docstrings

We use Google-style docstrings throughout the project. Here's the format:

```python
def function_name(param1: str, param2: int = 10) -> bool:
    """Brief description of the function.
    
    Longer description if needed. This can span multiple lines and should
    provide more detailed information about what the function does.
    
    Args:
        param1: Description of the first parameter.
        param2: Description of the second parameter. Defaults to 10.
    
    Returns:
        Description of what the function returns.
    
    Raises:
        ValueError: Description of when this exception is raised.
        TypeError: Description of when this exception is raised.
    
    Example:
        >>> result = function_name("hello", 20)
        >>> print(result)
        True
    """
    pass
```

### Class Docstrings

```python
class ReceiptProcessor:
    """Main processor for handling receipt images and extracting data.
    
    This class orchestrates the entire receipt processing workflow, including
    AI vision processing, data validation, storage, and integration with
    external services.
    
    Attributes:
        config: Configuration object containing all settings.
        ai_service: AI vision service for data extraction.
        storage: Storage manager for persisting data.
        logger: Logger instance for this processor.
    
    Example:
        >>> config = ProcessingConfig()
        >>> processor = ReceiptProcessor(config)
        >>> result = await processor.process_image("receipt.jpg")
    """
    
    def __init__(self, config: ProcessingConfig):
        """Initialize the receipt processor.
        
        Args:
            config: Configuration object with all necessary settings.
        """
        self.config = config
        self.ai_service = AIVisionService(config.ai_vision)
        self.storage = JSONStorageManager(config.storage)
        self.logger = logging.getLogger(__name__)
```

### Method Docstrings

```python
async def process_image(self, image_path: str) -> ReceiptData:
    """Process a single receipt image and extract data.
    
    This method handles the complete workflow for processing a receipt image,
    including validation, AI processing, data extraction, and storage.
    
    Args:
        image_path: Path to the image file to process.
    
    Returns:
        ReceiptData object containing extracted information.
    
    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValidationError: If the extracted data is invalid.
        ProcessingError: If processing fails for any reason.
    
    Example:
        >>> processor = ReceiptProcessor(config)
        >>> data = await processor.process_image("/path/to/receipt.jpg")
        >>> print(f"Vendor: {data.vendor_name}")
        >>> print(f"Amount: {data.total_amount}")
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        # Process the image
        result = await self.ai_service.extract_receipt_data(image_path)
        return result
    except Exception as e:
        self.logger.error(f"Failed to process image {image_path}: {e}")
        raise ProcessingError(f"Image processing failed: {e}") from e
```

## Code Comments

### Inline Comments

Use inline comments to explain complex logic or non-obvious code:

```python
def calculate_confidence_score(ai_result: Dict[str, Any]) -> float:
    """Calculate confidence score based on AI extraction results."""
    # Base confidence from AI model
    base_confidence = ai_result.get('confidence', 0.0)
    
    # Boost confidence if all required fields are present
    required_fields = ['vendor_name', 'total_amount', 'transaction_date']
    field_completeness = sum(1 for field in required_fields 
                           if ai_result.get(field) is not None) / len(required_fields)
    
    # Apply field completeness multiplier (0.8 to 1.2 range)
    completeness_multiplier = 0.8 + (field_completeness * 0.4)
    
    # Final confidence score
    final_confidence = base_confidence * completeness_multiplier
    
    # Ensure confidence is within valid range [0.0, 1.0]
    return max(0.0, min(1.0, final_confidence))
```

### Block Comments

Use block comments for complex algorithms or business logic:

```python
def process_payment_workflow(payment: Payment) -> PaymentResult:
    """Process payment through the configured workflow."""
    
    # Step 1: Validate payment data
    # Check all required fields are present and valid
    if not payment.amount or payment.amount <= 0:
        return PaymentResult(success=False, error="Invalid payment amount")
    
    # Step 2: Apply business rules
    # Check if payment exceeds approval threshold
    if payment.amount > payment.recipient.approval_threshold:
        # Route to approval workflow
        return self._route_to_approval(payment)
    
    # Step 3: Process payment
    # Execute the actual payment processing
    try:
        result = self._execute_payment(payment)
        return PaymentResult(success=True, transaction_id=result.id)
    except PaymentError as e:
        # Log error and return failure result
        self.logger.error(f"Payment processing failed: {e}")
        return PaymentResult(success=False, error=str(e))
```

### TODO Comments

Use TODO comments for future improvements or known issues:

```python
def process_image_batch(image_paths: List[str]) -> List[ReceiptData]:
    """Process multiple images in batch.
    
    TODO: Implement parallel processing for better performance.
    TODO: Add progress tracking for long-running batches.
    TODO: Consider memory optimization for large batches.
    """
    results = []
    for image_path in image_paths:
        # Process each image sequentially
        result = await self.process_image(image_path)
        results.append(result)
    
    return results
```

## Type Hints

### Function Signatures

Always include type hints for function parameters and return values:

```python
from typing import List, Dict, Optional, Union, Any
from decimal import Decimal
from datetime import datetime

def extract_vendor_name(text: str, confidence_threshold: float = 0.8) -> Optional[str]:
    """Extract vendor name from text with confidence threshold."""
    pass

def process_receipts(
    image_paths: List[str],
    config: ProcessingConfig,
    callback: Optional[callable] = None
) -> Dict[str, ReceiptData]:
    """Process multiple receipts with optional callback."""
    pass

def calculate_total(
    items: List[Dict[str, Union[str, Decimal]]],
    tax_rate: Decimal = Decimal('0.0')
) -> Decimal:
    """Calculate total amount including tax."""
    pass
```

### Class Attributes

Document class attributes with type hints:

```python
class ReceiptProcessor:
    """Main receipt processor class."""
    
    def __init__(self, config: ProcessingConfig):
        self.config: ProcessingConfig = config
        self.ai_service: AIVisionService = AIVisionService(config.ai_vision)
        self.storage: StorageManager = JSONStorageManager(config.storage)
        self.logger: logging.Logger = logging.getLogger(__name__)
        self._processing_queue: List[str] = []
        self._results: Dict[str, ReceiptData] = {}
```

### Generic Types

Use generic types for reusable components:

```python
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class StorageManager(Generic[T]):
    """Generic storage manager for different data types."""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
    
    def save(self, data: T) -> bool:
        """Save data of type T to storage."""
        pass
    
    def load(self, identifier: str) -> Optional[T]:
        """Load data of type T from storage."""
        pass

# Usage
receipt_storage = StorageManager[ReceiptData]("/path/to/receipts")
payment_storage = StorageManager[Payment]("/path/to/payments")
```

## API Documentation

### REST API Endpoints

Document API endpoints with clear descriptions:

```python
from fastapi import FastAPI, HTTPException, UploadFile, File
from typing import List, Optional

app = FastAPI(
    title="Receipt Processor API",
    description="API for processing receipt images and extracting data",
    version="1.0.0"
)

@app.post(
    "/process",
    response_model=ProcessingResult,
    summary="Process receipt image",
    description="Upload and process a receipt image to extract vendor, date, and amount information."
)
async def process_receipt(
    image: UploadFile = File(..., description="Receipt image file"),
    confidence_threshold: float = 0.8,
    include_items: bool = False
) -> ProcessingResult:
    """Process a single receipt image.
    
    This endpoint accepts a receipt image file and returns extracted data
    including vendor name, transaction date, and total amount.
    
    Args:
        image: The receipt image file to process.
        confidence_threshold: Minimum confidence score for extracted data.
        include_items: Whether to include individual line items.
    
    Returns:
        ProcessingResult containing extracted data and metadata.
    
    Raises:
        HTTPException: If processing fails or image is invalid.
    """
    try:
        result = await processor.process_image(
            image.file,
            confidence_threshold=confidence_threshold,
            include_items=include_items
        )
        return ProcessingResult(success=True, data=result)
    except ProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### CLI Commands

Document CLI commands with help text and examples:

```python
import click

@click.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--confidence', '-c', default=0.8, help='Confidence threshold for extraction')
@click.option('--output', '-o', help='Output file path for results')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def process_image(image_path: str, confidence: float, output: Optional[str], verbose: bool):
    """Process a single receipt image.
    
    This command processes a receipt image and extracts vendor information,
    transaction date, and total amount. The results can be saved to a file
    or displayed in the terminal.
    
    Examples:
        # Process image with default settings
        receipt-processor process receipt.jpg
        
        # Process with custom confidence threshold
        receipt-processor process receipt.jpg --confidence 0.9
        
        # Save results to file
        receipt-processor process receipt.jpg --output results.json
        
        # Enable verbose output
        receipt-processor process receipt.jpg --verbose
    """
    if verbose:
        click.echo(f"Processing image: {image_path}")
        click.echo(f"Confidence threshold: {confidence}")
    
    try:
        result = processor.process_image(image_path, confidence_threshold=confidence)
        
        if output:
            with open(output, 'w') as f:
                json.dump(result.dict(), f, indent=2)
            click.echo(f"Results saved to: {output}")
        else:
            click.echo(json.dumps(result.dict(), indent=2))
            
    except Exception as e:
        click.echo(f"Error processing image: {e}", err=True)
        raise click.Abort()
```

## Examples

### Complete Class Documentation

```python
class AIVisionService:
    """Service for extracting data from receipt images using AI vision models.
    
    This service integrates with various AI providers to extract structured
    data from receipt images, including vendor information, transaction details,
    and line items.
    
    Attributes:
        config: Configuration object containing AI provider settings.
        client: AI provider client instance.
        logger: Logger instance for this service.
    
    Example:
        >>> config = AIVisionConfig(provider="openai", api_key="sk-...")
        >>> service = AIVisionService(config)
        >>> data = await service.extract_receipt_data("receipt.jpg")
        >>> print(f"Vendor: {data.vendor_name}")
    """
    
    def __init__(self, config: AIVisionConfig):
        """Initialize the AI vision service.
        
        Args:
            config: Configuration object with AI provider settings.
        
        Raises:
            ConfigurationError: If configuration is invalid.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = self._create_client()
    
    def _create_client(self) -> Any:
        """Create AI provider client based on configuration.
        
        Returns:
            AI provider client instance.
        
        Raises:
            ConfigurationError: If provider is not supported.
        """
        if self.config.provider == "openai":
            return self._create_openai_client()
        elif self.config.provider == "anthropic":
            return self._create_anthropic_client()
        else:
            raise ConfigurationError(f"Unsupported AI provider: {self.config.provider}")
    
    async def extract_receipt_data(
        self, 
        image_path: str, 
        include_items: bool = False
    ) -> ReceiptData:
        """Extract structured data from a receipt image.
        
        This method processes a receipt image and extracts vendor information,
        transaction date, total amount, and optionally line items.
        
        Args:
            image_path: Path to the receipt image file.
            include_items: Whether to extract individual line items.
        
        Returns:
            ReceiptData object containing extracted information.
        
        Raises:
            FileNotFoundError: If image file doesn't exist.
            ProcessingError: If AI processing fails.
            ValidationError: If extracted data is invalid.
        
        Example:
            >>> service = AIVisionService(config)
            >>> data = await service.extract_receipt_data("receipt.jpg")
            >>> print(f"Total: ${data.total_amount}")
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Load and validate image
            image_data = self._load_image(image_path)
            
            # Extract data using AI
            raw_data = await self._extract_with_ai(image_data, include_items)
            
            # Validate and structure data
            receipt_data = self._validate_and_structure(raw_data)
            
            return receipt_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract data from {image_path}: {e}")
            raise ProcessingError(f"AI extraction failed: {e}") from e
    
    def _load_image(self, image_path: str) -> bytes:
        """Load image file and return as bytes.
        
        Args:
            image_path: Path to the image file.
        
        Returns:
            Image data as bytes.
        
        Raises:
            FileNotFoundError: If image file doesn't exist.
            ValueError: If image format is not supported.
        """
        try:
            with open(image_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")
    
    async def _extract_with_ai(self, image_data: bytes, include_items: bool) -> Dict[str, Any]:
        """Extract data using AI provider.
        
        Args:
            image_data: Image data as bytes.
            include_items: Whether to extract line items.
        
        Returns:
            Raw extracted data from AI provider.
        
        Raises:
            ProcessingError: If AI processing fails.
        """
        # Implementation details...
        pass
    
    def _validate_and_structure(self, raw_data: Dict[str, Any]) -> ReceiptData:
        """Validate and structure raw AI data.
        
        Args:
            raw_data: Raw data from AI provider.
        
        Returns:
            Validated and structured ReceiptData object.
        
        Raises:
            ValidationError: If data validation fails.
        """
        # Implementation details...
        pass
```

### Function Documentation

```python
def calculate_processing_metrics(
    logs: List[ProcessingLog],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> ProcessingMetrics:
    """Calculate processing metrics from log entries.
    
    This function analyzes processing logs to calculate various metrics
    including success rate, average processing time, and error distribution.
    
    Args:
        logs: List of processing log entries to analyze.
        start_date: Optional start date for filtering logs.
        end_date: Optional end date for filtering logs.
    
    Returns:
        ProcessingMetrics object containing calculated metrics.
    
    Raises:
        ValueError: If start_date is after end_date.
        EmptyDataError: If no logs are provided for analysis.
    
    Example:
        >>> logs = load_processing_logs()
        >>> metrics = calculate_processing_metrics(logs)
        >>> print(f"Success rate: {metrics.success_rate:.2%}")
        >>> print(f"Average time: {metrics.avg_processing_time:.2f}s")
    """
    if not logs:
        raise EmptyDataError("No logs provided for analysis")
    
    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be before end_date")
    
    # Filter logs by date range if specified
    filtered_logs = logs
    if start_date:
        filtered_logs = [log for log in filtered_logs if log.created_at >= start_date]
    if end_date:
        filtered_logs = [log for log in filtered_logs if log.created_at <= end_date]
    
    if not filtered_logs:
        raise EmptyDataError("No logs found in specified date range")
    
    # Calculate metrics
    total_logs = len(filtered_logs)
    successful_logs = len([log for log in filtered_logs if log.status == ProcessingStatus.PROCESSED])
    error_logs = len([log for log in filtered_logs if log.status == ProcessingStatus.ERROR])
    
    success_rate = successful_logs / total_logs if total_logs > 0 else 0.0
    error_rate = error_logs / total_logs if total_logs > 0 else 0.0
    
    avg_processing_time = sum(log.processing_time for log in filtered_logs) / total_logs
    
    return ProcessingMetrics(
        total_processed=total_logs,
        successful=successful_logs,
        failed=error_logs,
        success_rate=success_rate,
        error_rate=error_rate,
        avg_processing_time=avg_processing_time
    )
```

## Documentation Best Practices

### 1. Be Clear and Concise

- Use simple, clear language
- Avoid jargon unless necessary
- Be specific about what functions do

### 2. Include Examples

- Provide practical examples
- Show both simple and complex use cases
- Include error handling examples

### 3. Document Edge Cases

- Mention what happens with invalid input
- Document error conditions
- Explain default behaviors

### 4. Keep Documentation Up to Date

- Update docstrings when code changes
- Review documentation during code reviews
- Remove outdated information

### 5. Use Consistent Formatting

- Follow the established docstring format
- Use consistent terminology
- Maintain consistent style across the codebase

This documentation standard ensures that all code in the Receipt Processor project is well-documented, maintainable, and easy to understand for both current and future developers.
