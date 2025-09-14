"""
Tests for the file monitoring module.
"""

import pytest
import tempfile
import time
from pathlib import Path
from PIL import Image
import io

from receipt_processor.file_monitor import FileSystemMonitor, FileEvent, validate_image_file
from receipt_processor.config import AppSettings, MonitoringSettings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings with temporary directory."""
    monitoring_settings = MonitoringSettings(
        watch_folder=temp_dir,
        file_extensions=[".jpg", ".png", ".heic"],
        processing_interval=1,
        max_concurrent_processing=2
    )
    
    # Create minimal settings for testing
    settings = AppSettings()
    settings.monitoring = monitoring_settings
    return settings


@pytest.fixture
def sample_image():
    """Create a sample valid image for testing."""
    # Create a small test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


def test_validate_image_file_valid(temp_dir, sample_image):
    """Test image validation with valid image."""
    image_path = temp_dir / "test.jpg"
    image_path.write_bytes(sample_image)
    
    assert validate_image_file(image_path) is True


def test_validate_image_file_invalid(temp_dir):
    """Test image validation with invalid file."""
    invalid_path = temp_dir / "invalid.jpg"
    invalid_path.write_text("This is not an image")
    
    assert validate_image_file(invalid_path) is False


def test_validate_image_file_nonexistent(temp_dir):
    """Test image validation with non-existent file."""
    nonexistent_path = temp_dir / "nonexistent.jpg"
    
    assert validate_image_file(nonexistent_path) is False


def test_file_system_monitor_creation(test_settings):
    """Test FileSystemMonitor creation."""
    monitor = FileSystemMonitor(test_settings)
    
    assert monitor.settings == test_settings
    assert monitor.is_running is False
    assert len(monitor.event_callbacks) == 0


def test_file_system_monitor_callback_registration(test_settings):
    """Test callback registration."""
    monitor = FileSystemMonitor(test_settings)
    
    def test_callback(event):
        pass
    
    monitor.add_event_callback(test_callback)
    
    assert len(monitor.event_callbacks) == 1
    assert test_callback in monitor.event_callbacks


def test_file_system_monitor_start_stop(test_settings):
    """Test monitor start and stop."""
    monitor = FileSystemMonitor(test_settings)
    
    # Test start
    success = monitor.start()
    assert success is True
    assert monitor.is_running is True
    
    # Test stop
    monitor.stop()
    assert monitor.is_running is False


def test_file_system_monitor_invalid_directory():
    """Test monitor with invalid directory."""
    # Create settings with non-existent directory
    monitoring_settings = MonitoringSettings(
        watch_folder=Path("/nonexistent/directory"),
        file_extensions=[".jpg"],
        processing_interval=1,
        max_concurrent_processing=1
    )
    
    settings = AppSettings()
    settings.monitoring = monitoring_settings
    
    monitor = FileSystemMonitor(settings)
    
    # Should fail to start
    success = monitor.start()
    assert success is False
    assert monitor.is_running is False


def test_file_event_creation():
    """Test FileEvent creation."""
    test_path = Path("/test/path.jpg")
    event = FileEvent(
        file_path=test_path,
        event_type="created",
        timestamp=time.time(),
        file_size=1024
    )
    
    assert event.file_path == test_path
    assert event.event_type == "created"
    assert event.file_size == 1024
    assert event.is_valid_image is False
    assert event.processing_status == "pending"


@pytest.mark.integration
def test_file_monitor_integration(test_settings, temp_dir, sample_image):
    """Integration test for file monitoring."""
    events_received = []
    
    def capture_event(event):
        events_received.append(event)
    
    monitor = FileSystemMonitor(test_settings)
    monitor.add_event_callback(capture_event)
    
    # Start monitoring
    assert monitor.start() is True
    
    try:
        # Create a test image file
        image_path = temp_dir / "test_receipt.jpg"
        image_path.write_bytes(sample_image)
        
        # Wait for event processing
        time.sleep(2)
        
        # Check that event was captured
        assert len(events_received) > 0
        event = events_received[0]
        assert event.file_path == image_path
        assert event.is_valid_image is True
        
    finally:
        monitor.stop()


if __name__ == "__main__":
    pytest.main([__file__])
