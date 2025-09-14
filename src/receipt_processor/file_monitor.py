"""
File system monitoring module for Receipt Processing Application.

This module provides functionality to monitor directories for new image files,
validate file types, and trigger processing events when receipts are detected.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
from loguru import logger
from PIL import Image

from .config import AppSettings


@dataclass
class FileEvent:
    """Represents a file system event for processing."""
    file_path: Path
    event_type: str  # 'created', 'modified'
    timestamp: datetime
    file_size: int
    is_valid_image: bool = False
    processing_status: str = "pending"  # pending, processing, completed, error


class ReceiptFileHandler(FileSystemEventHandler):
    """Handles file system events for receipt image files."""
    
    def __init__(
        self, 
        settings: AppSettings,
        callback: Optional[Callable[[FileEvent], None]] = None
    ):
        super().__init__()
        self.settings = settings
        self.callback = callback
        self.supported_extensions = set(
            ext.lower() for ext in settings.monitoring.file_extensions
        )
        self.recent_events: Dict[str, float] = {}
        self.processing_files: Set[str] = set()
        
        # Debounce settings to avoid duplicate processing
        self.debounce_seconds = 2.0
        
        logger.info(f"File handler initialized for extensions: {self.supported_extensions}")
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "created")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "modified")
    
    def _handle_file_event(self, file_path: str, event_type: str):
        """Process a file system event."""
        try:
            path = Path(file_path)
            
            # Check if file extension is supported
            if not self._is_supported_file(path):
                logger.debug(f"Ignoring unsupported file: {path}")
                return
            
            # Debounce rapid events for the same file
            if self._is_debounced(file_path):
                logger.debug(f"Debouncing event for: {path}")
                return
            
            # Check if file is already being processed
            if file_path in self.processing_files:
                logger.debug(f"File already being processed: {path}")
                return
            
            # Wait for file to be fully written
            if not self._wait_for_file_stable(path):
                logger.warning(f"File not stable after waiting: {path}")
                return
            
            # Create file event
            file_event = FileEvent(
                file_path=path,
                event_type=event_type,
                timestamp=datetime.now(),
                file_size=path.stat().st_size if path.exists() else 0
            )
            
            # Validate image file
            file_event.is_valid_image = self._validate_image_file(path)
            
            if file_event.is_valid_image:
                logger.info(f"Valid receipt image detected: {path} ({file_event.file_size} bytes)")
                
                # Mark as processing
                self.processing_files.add(file_path)
                
                # Trigger callback if provided
                if self.callback:
                    try:
                        self.callback(file_event)
                    except Exception as e:
                        logger.error(f"Callback error for {path}: {e}")
                    finally:
                        # Remove from processing set
                        self.processing_files.discard(file_path)
            else:
                logger.warning(f"Invalid or corrupted image file: {path}")
                
        except Exception as e:
            logger.error(f"Error handling file event for {file_path}: {e}")
            self.processing_files.discard(file_path)
    
    def _is_supported_file(self, path: Path) -> bool:
        """Check if file has a supported extension."""
        return path.suffix.lower() in self.supported_extensions
    
    def _is_debounced(self, file_path: str) -> bool:
        """Check if event should be debounced."""
        current_time = time.time()
        last_event_time = self.recent_events.get(file_path, 0)
        
        if current_time - last_event_time < self.debounce_seconds:
            return True
        
        self.recent_events[file_path] = current_time
        return False
    
    def _wait_for_file_stable(self, path: Path, max_wait: int = 10) -> bool:
        """Wait for file to be completely written."""
        if not path.exists():
            return False
        
        previous_size = -1
        stable_count = 0
        
        for _ in range(max_wait):
            try:
                current_size = path.stat().st_size
                if current_size == previous_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:  # File stable for 2 checks
                        return True
                else:
                    stable_count = 0
                
                previous_size = current_size
                time.sleep(0.5)
                
            except (OSError, IOError):
                time.sleep(0.5)
                continue
        
        return previous_size > 0
    
    def _validate_image_file(self, path: Path) -> bool:
        """Validate that the file is a valid image."""
        try:
            with Image.open(path) as img:
                # Try to load the image to verify it's valid
                img.verify()
                return True
        except Exception as e:
            logger.debug(f"Image validation failed for {path}: {e}")
            return False
    
    def cleanup_old_events(self, max_age_hours: int = 24):
        """Clean up old event records to prevent memory leaks."""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        old_events = [
            file_path for file_path, event_time in self.recent_events.items()
            if event_time < cutoff_time
        ]
        
        for file_path in old_events:
            del self.recent_events[file_path]
        
        if old_events:
            logger.debug(f"Cleaned up {len(old_events)} old event records")


class FileSystemMonitor:
    """Main file system monitor for receipt processing."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.observer: Optional[Observer] = None
        self.handler: Optional[ReceiptFileHandler] = None
        self.is_running = False
        self.processed_files: Set[str] = set()
        self.event_callbacks: List[Callable[[FileEvent], None]] = []
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(
            max_workers=settings.monitoring.max_concurrent_processing
        )
        
        logger.info(f"FileSystemMonitor initialized for: {settings.monitoring.watch_folder}")
    
    def add_event_callback(self, callback: Callable[[FileEvent], None]):
        """Add a callback function to be called when file events occur."""
        self.event_callbacks.append(callback)
        logger.debug(f"Added event callback: {callback.__name__}")
    
    def start(self) -> bool:
        """Start monitoring the configured directory."""
        try:
            watch_folder = self.settings.monitoring.watch_folder
            
            # Ensure watch folder exists
            if not watch_folder.exists():
                logger.error(f"Watch folder does not exist: {watch_folder}")
                return False
            
            if not watch_folder.is_dir():
                logger.error(f"Watch path is not a directory: {watch_folder}")
                return False
            
            # Create file handler with callback
            self.handler = ReceiptFileHandler(
                settings=self.settings,
                callback=self._handle_file_event
            )
            
            # Create and configure observer
            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(watch_folder),
                recursive=False  # Only monitor the specified directory
            )
            
            # Start observer
            self.observer.start()
            self.is_running = True
            
            logger.success(f"Started monitoring: {watch_folder}")
            
            # Process existing files if configured
            if hasattr(self.settings.monitoring, 'process_existing_files'):
                if self.settings.monitoring.process_existing_files:
                    self._process_existing_files()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file system monitor: {e}")
            return False
    
    def stop(self):
        """Stop monitoring."""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("File system monitor stopped")
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
    
    def _handle_file_event(self, file_event: FileEvent):
        """Handle file events from the file handler."""
        # Submit to thread pool for concurrent processing
        future = self.executor.submit(self._process_file_event, file_event)
        
        # Log submission
        logger.debug(f"Submitted file event for processing: {file_event.file_path}")
    
    def _process_file_event(self, file_event: FileEvent):
        """Process a file event (runs in thread pool)."""
        try:
            file_path_str = str(file_event.file_path)
            
            # Check if already processed
            if file_path_str in self.processed_files:
                logger.debug(f"File already processed: {file_event.file_path}")
                return
            
            # Mark as processed
            self.processed_files.add(file_path_str)
            
            # Call all registered callbacks
            for callback in self.event_callbacks:
                try:
                    callback(file_event)
                except Exception as e:
                    logger.error(f"Callback {callback.__name__} failed for {file_event.file_path}: {e}")
            
            logger.info(f"Processed file event: {file_event.file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file event {file_event.file_path}: {e}")
    
    def _process_existing_files(self):
        """Process files that already exist in the watch directory."""
        try:
            watch_folder = self.settings.monitoring.watch_folder
            logger.info(f"Processing existing files in: {watch_folder}")
            
            existing_files = []
            for ext in self.settings.monitoring.file_extensions:
                pattern = f"*{ext.lower()}"
                existing_files.extend(watch_folder.glob(pattern))
                pattern = f"*{ext.upper()}"
                existing_files.extend(watch_folder.glob(pattern))
            
            logger.info(f"Found {len(existing_files)} existing image files")
            
            for file_path in existing_files:
                if file_path.is_file():
                    # Create file event for existing file
                    file_event = FileEvent(
                        file_path=file_path,
                        event_type="existing",
                        timestamp=datetime.fromtimestamp(file_path.stat().st_mtime),
                        file_size=file_path.stat().st_size
                    )
                    
                    # Validate image
                    if self.handler:
                        file_event.is_valid_image = self.handler._validate_image_file(file_path)
                        
                        if file_event.is_valid_image:
                            self._handle_file_event(file_event)
            
        except Exception as e:
            logger.error(f"Error processing existing files: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        return {
            "is_running": self.is_running,
            "watch_folder": str(self.settings.monitoring.watch_folder),
            "supported_extensions": list(self.settings.monitoring.file_extensions),
            "processed_files_count": len(self.processed_files),
            "active_callbacks": len(self.event_callbacks),
            "recent_events_count": len(self.handler.recent_events) if self.handler else 0
        }
    
    def cleanup(self):
        """Perform cleanup operations."""
        if self.handler:
            self.handler.cleanup_old_events()
        
        # Clean up old processed files (keep only recent ones)
        # This could be enhanced to use timestamps if needed
        if len(self.processed_files) > 1000:
            # Keep only the most recent 500
            files_list = list(self.processed_files)
            self.processed_files = set(files_list[-500:])
            logger.debug("Cleaned up old processed files records")


# Convenience functions
def create_monitor(settings: AppSettings) -> FileSystemMonitor:
    """Create a new FileSystemMonitor instance."""
    return FileSystemMonitor(settings)


def validate_image_file(file_path: Path) -> bool:
    """Validate that a file is a readable image."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False
