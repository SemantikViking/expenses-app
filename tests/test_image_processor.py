"""
Tests for the image processing module.
"""

import pytest
import tempfile
import io
from pathlib import Path
from PIL import Image

from receipt_processor.image_processor import (
    ImageProcessor, ImageMetadata, ProcessingOptions, ImageFormat,
    load_and_validate_image, preprocess_receipt_image, extract_image_metadata
)
from receipt_processor.config import (
    AppSettings, MonitoringSettings, ExtractionSettings, 
    AIVisionSettings, EmailSettings, PaymentSettings, 
    StorageSettings, LoggingSettings
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_settings():
    """Create test settings."""
    return AppSettings(
        monitoring=MonitoringSettings(
            watch_folder=Path("/tmp"),
            file_extensions=[".jpg", ".png", ".heic"],
            processing_interval=1,
            max_concurrent_processing=1
        ),
        ai_vision=AIVisionSettings(
            provider="openai",
            model="gpt-4-vision-preview",
            api_key="test-key",
            max_retries=3,
            confidence_threshold=0.8,
            timeout_seconds=30
        ),
        extraction=ExtractionSettings(
            extract_vendor=True,
            extract_date=True,
            extract_amount=True,
            extract_currency=True,
            date_formats=["%Y-%m-%d"],
            default_currency="USD"
        ),
        email=EmailSettings(
            enable_email=False,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="test-password",
            default_recipient="test@example.com"
        ),
        payment=PaymentSettings(
            enable_payment_tracking=False,
            payment_systems=["manual"],
            default_payment_system="manual",
            auto_reconcile=False
        ),
        storage=StorageSettings(
            log_file_path=Path("/tmp/test.json"),
            backup_enabled=False,
            backup_interval_hours=24,
            max_log_entries=1000
        ),
        logging=LoggingSettings(
            log_level="INFO",
            log_file=Path("/tmp/test.log"),
            max_log_size_mb=10,
            backup_count=3,
            enable_logfire=False
        )
    )


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    img = Image.new('RGB', (800, 600), color='white')
    return img


@pytest.fixture
def sample_image_bytes():
    """Create sample image as bytes."""
    img = Image.new('RGB', (800, 600), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    return img_bytes.getvalue()


def test_image_processor_creation(test_settings):
    """Test ImageProcessor creation."""
    processor = ImageProcessor(test_settings)
    
    assert processor.settings == test_settings
    assert len(processor.supported_formats) > 0
    assert '.jpg' in processor.supported_formats


def test_load_image_valid(temp_dir, sample_image_bytes, test_settings):
    """Test loading a valid image."""
    processor = ImageProcessor(test_settings)
    
    # Save sample image
    image_path = temp_dir / "test.jpg"
    image_path.write_bytes(sample_image_bytes)
    
    # Load image
    loaded_image = processor.load_image(image_path)
    
    assert loaded_image is not None
    assert loaded_image.size == (800, 600)
    assert loaded_image.mode == 'RGB'


def test_load_image_nonexistent(test_settings):
    """Test loading a non-existent image."""
    processor = ImageProcessor(test_settings)
    
    loaded_image = processor.load_image("/nonexistent/path.jpg")
    
    assert loaded_image is None


def test_validate_image_valid(sample_image, test_settings):
    """Test validating a valid image."""
    processor = ImageProcessor(test_settings)
    
    is_valid = processor.validate_image(sample_image)
    
    assert is_valid is True


def test_validate_image_none(test_settings):
    """Test validating None image."""
    processor = ImageProcessor(test_settings)
    
    is_valid = processor.validate_image(None)
    
    assert is_valid is False


def test_validate_image_too_small(test_settings):
    """Test validating an image that's too small."""
    processor = ImageProcessor(test_settings)
    
    # Create very small image
    small_image = Image.new('RGB', (50, 50), color='white')
    
    is_valid = processor.validate_image(small_image)
    
    assert is_valid is False


def test_extract_metadata(temp_dir, sample_image_bytes, test_settings):
    """Test metadata extraction."""
    processor = ImageProcessor(test_settings)
    
    # Save sample image
    image_path = temp_dir / "test.jpg"
    image_path.write_bytes(sample_image_bytes)
    
    # Extract metadata
    metadata = processor.extract_metadata(image_path)
    
    assert metadata.file_path == image_path
    assert metadata.format == "JPEG"
    assert metadata.size == (800, 600)
    assert metadata.mode == "RGB"
    assert metadata.file_size > 0


def test_extract_metadata_invalid_file(temp_dir, test_settings):
    """Test metadata extraction from invalid file."""
    processor = ImageProcessor(test_settings)
    
    # Create invalid image file
    invalid_path = temp_dir / "invalid.jpg"
    invalid_path.write_text("This is not an image")
    
    metadata = processor.extract_metadata(invalid_path)
    
    assert metadata.format == "UNKNOWN"
    assert metadata.size == (0, 0)


def test_preprocess_image_basic(sample_image, test_settings):
    """Test basic image preprocessing."""
    processor = ImageProcessor(test_settings)
    options = ProcessingOptions()
    
    processed_image = processor.preprocess_image(sample_image, options)
    
    assert processed_image is not None
    assert processed_image.mode == 'RGB'
    # Should maintain size since it's already within limits
    assert processed_image.size == sample_image.size


def test_preprocess_image_resize(test_settings):
    """Test image resizing during preprocessing."""
    processor = ImageProcessor(test_settings)
    
    # Create large image
    large_image = Image.new('RGB', (4000, 3000), color='white')
    
    options = ProcessingOptions(max_width=2000, max_height=1500)
    processed_image = processor.preprocess_image(large_image, options)
    
    assert processed_image.size[0] <= 2000
    assert processed_image.size[1] <= 1500


def test_preprocess_image_transparency(test_settings):
    """Test handling transparency in preprocessing."""
    processor = ImageProcessor(test_settings)
    
    # Create RGBA image with transparency
    rgba_image = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
    
    options = ProcessingOptions(convert_to_rgb=True, remove_transparency=True)
    processed_image = processor.preprocess_image(rgba_image, options)
    
    assert processed_image.mode == 'RGB'


def test_convert_format(sample_image, test_settings):
    """Test format conversion."""
    processor = ImageProcessor(test_settings)
    
    # Convert to JPEG bytes
    jpeg_bytes = processor.convert_format(sample_image, ImageFormat.JPEG, quality=90)
    
    assert isinstance(jpeg_bytes, bytes)
    assert len(jpeg_bytes) > 0
    
    # Verify it's a valid JPEG
    jpeg_image = Image.open(io.BytesIO(jpeg_bytes))
    assert jpeg_image.format == 'JPEG'


def test_save_processed_image(temp_dir, sample_image, test_settings):
    """Test saving processed image."""
    processor = ImageProcessor(test_settings)
    
    output_path = temp_dir / "output.jpg"
    success = processor.save_processed_image(sample_image, output_path)
    
    assert success is True
    assert output_path.exists()
    
    # Verify saved image
    saved_image = Image.open(output_path)
    assert saved_image.size == sample_image.size


def test_get_optimal_processing_options(temp_dir, sample_image_bytes, test_settings):
    """Test getting optimal processing options."""
    processor = ImageProcessor(test_settings)
    
    # Create metadata
    image_path = temp_dir / "test.jpg"
    image_path.write_bytes(sample_image_bytes)
    metadata = processor.extract_metadata(image_path)
    
    options = processor.get_optimal_processing_options(metadata)
    
    assert isinstance(options, ProcessingOptions)
    assert options.max_width > 0
    assert options.max_height > 0


def test_processing_options_defaults():
    """Test ProcessingOptions default values."""
    options = ProcessingOptions()
    
    assert options.max_width == 2048
    assert options.max_height == 2048
    assert options.maintain_aspect_ratio is True
    assert options.enhance_contrast is True
    assert options.jpeg_quality == 95


def test_convenience_functions(temp_dir, sample_image_bytes, test_settings):
    """Test convenience functions."""
    # Save sample image
    image_path = temp_dir / "test.jpg"
    image_path.write_bytes(sample_image_bytes)
    
    # Test load_and_validate_image
    image = load_and_validate_image(image_path, test_settings)
    assert image is not None
    
    # Test preprocess_receipt_image
    processed = preprocess_receipt_image(image, test_settings)
    assert processed is not None
    
    # Test extract_image_metadata
    metadata = extract_image_metadata(image_path, test_settings)
    assert metadata.format == "JPEG"


if __name__ == "__main__":
    pytest.main([__file__])
