"""
Daemon Service Module

This module provides daemon functionality for running the receipt processor
as a background service with process management, signal handling, and monitoring.
"""

import os
import sys
import signal
import time
import threading
import psutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import atexit

from .models import ProcessingStatus
from .storage import JSONStorageManager
from .status_tracker import EnhancedStatusTracker

logger = logging.getLogger(__name__)

class ServiceStatus(str, Enum):
    """Service status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class ServiceConfig:
    """Configuration for the daemon service."""
    pid_file: Path
    log_file: Path
    watch_directory: Path
    processed_directory: Optional[Path] = None
    check_interval: int = 5  # seconds
    max_workers: int = 4
    memory_limit_mb: int = 512
    cpu_limit_percent: float = 80.0
    graceful_shutdown_timeout: int = 30  # seconds
    health_check_interval: int = 60  # seconds

@dataclass
class ServiceMetrics:
    """Service performance metrics."""
    start_time: datetime
    last_health_check: datetime
    processed_files: int = 0
    error_count: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_workers: int = 0
    queue_size: int = 0

class DaemonService:
    """Main daemon service class."""
    
    def __init__(self, config: ServiceConfig, storage_manager: JSONStorageManager, status_tracker: EnhancedStatusTracker):
        self.config = config
        self.storage_manager = storage_manager
        self.status_tracker = status_tracker
        self.status = ServiceStatus.STOPPED
        self.metrics = ServiceMetrics(start_time=datetime.now(), last_health_check=datetime.now())
        self.shutdown_event = threading.Event()
        self.workers: Dict[int, threading.Thread] = {}
        self.processing_queue = []
        self.queue_lock = threading.Lock()
        self.metrics_lock = threading.Lock()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Register cleanup function
        atexit.register(self._cleanup)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGHUP, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def _cleanup(self):
        """Cleanup resources on exit."""
        if self.status == ServiceStatus.RUNNING:
            self.stop()
        self._remove_pid_file()
    
    def _write_pid_file(self) -> bool:
        """Write PID file."""
        try:
            self.config.pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"PID file written: {self.config.pid_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")
            return False
    
    def _remove_pid_file(self):
        """Remove PID file."""
        try:
            if self.config.pid_file.exists():
                self.config.pid_file.unlink()
                logger.info(f"PID file removed: {self.config.pid_file}")
        except Exception as e:
            logger.error(f"Failed to remove PID file: {e}")
    
    def _is_running(self) -> bool:
        """Check if service is already running."""
        if not self.config.pid_file.exists():
            return False
        
        try:
            with open(self.config.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            if psutil.pid_exists(pid):
                try:
                    process = psutil.Process(pid)
                    # Check if it's our process
                    if 'python' in process.name().lower() and 'receipt_processor' in ' '.join(process.cmdline()):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # PID file exists but process is dead, remove it
            self.config.pid_file.unlink()
            return False
            
        except (ValueError, FileNotFoundError):
            return False
    
    def start(self) -> bool:
        """Start the daemon service."""
        if self.status != ServiceStatus.STOPPED:
            logger.warning(f"Service is already {self.status.value}")
            return False
        
        if self._is_running():
            logger.error("Service is already running (PID file exists)")
            return False
        
        try:
            logger.info("Starting daemon service...")
            self.status = ServiceStatus.STARTING
            
            # Write PID file
            if not self._write_pid_file():
                self.status = ServiceStatus.ERROR
                return False
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            # Start health check thread
            self.health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_thread.start()
            
            # Start worker threads
            for i in range(self.config.max_workers):
                worker = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
                worker.start()
                self.workers[i] = worker
            
            self.status = ServiceStatus.RUNNING
            logger.info("Daemon service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start daemon service: {e}")
            self.status = ServiceStatus.ERROR
            self._remove_pid_file()
            return False
    
    def stop(self) -> bool:
        """Stop the daemon service."""
        if self.status not in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            logger.warning(f"Service is not running (status: {self.status.value})")
            return False
        
        try:
            logger.info("Stopping daemon service...")
            self.status = ServiceStatus.STOPPING
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Wait for workers to finish gracefully
            timeout = self.config.graceful_shutdown_timeout
            start_time = time.time()
            
            for worker_id, worker in self.workers.items():
                if worker.is_alive():
                    worker.join(timeout=max(1, timeout - (time.time() - start_time)))
                    if worker.is_alive():
                        logger.warning(f"Worker {worker_id} did not stop gracefully")
            
            # Wait for monitor thread
            if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            # Wait for health check thread
            if hasattr(self, 'health_thread') and self.health_thread.is_alive():
                self.health_thread.join(timeout=5)
            
            self.status = ServiceStatus.STOPPED
            self._remove_pid_file()
            logger.info("Daemon service stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping daemon service: {e}")
            self.status = ServiceStatus.ERROR
            return False
    
    def restart(self) -> bool:
        """Restart the daemon service."""
        logger.info("Restarting daemon service...")
        if self.stop():
            time.sleep(1)  # Brief pause before restart
            return self.start()
        return False
    
    def status_info(self) -> Dict[str, Any]:
        """Get detailed status information."""
        with self.metrics_lock:
            return {
                'status': self.status.value,
                'pid': os.getpid() if self.status == ServiceStatus.RUNNING else None,
                'uptime_seconds': (datetime.now() - self.metrics.start_time).total_seconds(),
                'processed_files': self.metrics.processed_files,
                'error_count': self.metrics.error_count,
                'memory_usage_mb': self.metrics.memory_usage_mb,
                'cpu_usage_percent': self.metrics.cpu_usage_percent,
                'active_workers': self.metrics.active_workers,
                'queue_size': self.metrics.queue_size,
                'last_health_check': self.metrics.last_health_check.isoformat(),
                'config': {
                    'watch_directory': str(self.config.watch_directory),
                    'processed_directory': str(self.config.processed_directory) if self.config.processed_directory else None,
                    'check_interval': self.config.check_interval,
                    'max_workers': self.config.max_workers,
                    'memory_limit_mb': self.config.memory_limit_mb,
                    'cpu_limit_percent': self.config.cpu_limit_percent
                }
            }
    
    def _monitor_loop(self):
        """Main monitoring loop for file watching."""
        logger.info("File monitor started")
        
        while not self.shutdown_event.is_set():
            try:
                # Check for new files
                self._scan_for_new_files()
                
                # Update metrics
                self._update_metrics()
                
                # Sleep until next check
                self.shutdown_event.wait(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                with self.metrics_lock:
                    self.metrics.error_count += 1
        
        logger.info("File monitor stopped")
    
    def _scan_for_new_files(self):
        """Scan watch directory for new image files."""
        if not self.config.watch_directory.exists():
            logger.warning(f"Watch directory does not exist: {self.config.watch_directory}")
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        new_files = []
        
        for ext in image_extensions:
            new_files.extend(self.config.watch_directory.glob(f'*{ext}'))
            new_files.extend(self.config.watch_directory.glob(f'*{ext.upper()}'))
        
        for file_path in new_files:
            if file_path.is_file():
                # Add to processing queue
                with self.queue_lock:
                    if file_path not in self.processing_queue:
                        self.processing_queue.append(file_path)
                        logger.info(f"Added to queue: {file_path.name}")
    
    def _worker_loop(self, worker_id: int):
        """Worker thread loop for processing files."""
        logger.info(f"Worker {worker_id} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get next file from queue
                file_path = None
                with self.queue_lock:
                    if self.processing_queue:
                        file_path = self.processing_queue.pop(0)
                
                if file_path is None:
                    # No work to do, sleep briefly
                    self.shutdown_event.wait(1)
                    continue
                
                # Process the file
                self._process_file(file_path, worker_id)
                
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {e}")
                with self.metrics_lock:
                    self.metrics.error_count += 1
        
        logger.info(f"Worker {worker_id} stopped")
    
    def _process_file(self, file_path: Path, worker_id: int):
        """Process a single file."""
        try:
            logger.info(f"Worker {worker_id} processing: {file_path.name}")
            
            # TODO: Implement actual file processing logic
            # For now, just simulate processing
            time.sleep(0.5)  # Simulate processing time
            
            # Create processing log entry
            from .models import ReceiptProcessingLog, ReceiptData, Currency
            from uuid import uuid4
            
            log_entry = ReceiptProcessingLog(
                id=uuid4(),
                original_filename=file_path.name,
                current_status=ProcessingStatus.PROCESSED,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                receipt_data=ReceiptData(
                    vendor_name="Sample Vendor",
                    transaction_date=datetime.now(),
                    total_amount=100.00,
                    currency=Currency.USD
                )
            )
            
            # Store the log entry
            self.storage_manager.add_log_entry(log_entry)
            
            # Move file to processed directory if configured
            if self.config.processed_directory:
                self.config.processed_directory.mkdir(parents=True, exist_ok=True)
                new_path = self.config.processed_directory / file_path.name
                file_path.rename(new_path)
                logger.info(f"Moved to processed: {new_path}")
            
            # Update metrics
            with self.metrics_lock:
                self.metrics.processed_files += 1
            
            logger.info(f"Worker {worker_id} completed: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            with self.metrics_lock:
                self.metrics.error_count += 1
    
    def _health_check_loop(self):
        """Health check loop for monitoring service health."""
        logger.info("Health check monitor started")
        
        while not self.shutdown_event.is_set():
            try:
                self._perform_health_check()
                self.shutdown_event.wait(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
        
        logger.info("Health check monitor stopped")
    
    def _perform_health_check(self):
        """Perform health check and update metrics."""
        try:
            process = psutil.Process()
            
            # Update memory and CPU usage
            with self.metrics_lock:
                self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                self.metrics.cpu_usage_percent = process.cpu_percent()
                self.metrics.active_workers = sum(1 for w in self.workers.values() if w.is_alive())
                self.metrics.queue_size = len(self.processing_queue)
                self.metrics.last_health_check = datetime.now()
            
            # Check resource limits
            if self.metrics.memory_usage_mb > self.config.memory_limit_mb:
                logger.warning(f"Memory usage exceeds limit: {self.metrics.memory_usage_mb:.1f}MB > {self.config.memory_limit_mb}MB")
            
            if self.metrics.cpu_usage_percent > self.config.cpu_limit_percent:
                logger.warning(f"CPU usage exceeds limit: {self.metrics.cpu_usage_percent:.1f}% > {self.config.cpu_limit_percent}%")
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
    
    def _update_metrics(self):
        """Update service metrics."""
        with self.metrics_lock:
            self.metrics.active_workers = sum(1 for w in self.workers.values() if w.is_alive())
            self.metrics.queue_size = len(self.processing_queue)

class ServiceManager:
    """Service manager for controlling daemon operations."""
    
    def __init__(self, config: ServiceConfig, storage_manager: JSONStorageManager, status_tracker: EnhancedStatusTracker):
        self.config = config
        self.storage_manager = storage_manager
        self.status_tracker = status_tracker
        self.service: Optional[DaemonService] = None
    
    def start_service(self) -> bool:
        """Start the daemon service."""
        if self.service is None:
            self.service = DaemonService(self.config, self.storage_manager, self.status_tracker)
        
        return self.service.start()
    
    def stop_service(self) -> bool:
        """Stop the daemon service."""
        if self.service is None:
            logger.warning("No service instance to stop")
            return False
        
        return self.service.stop()
    
    def restart_service(self) -> bool:
        """Restart the daemon service."""
        if self.service is None:
            return self.start_service()
        
        return self.service.restart()
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        if self.service is None:
            return {'status': ServiceStatus.STOPPED.value, 'message': 'No service instance'}
        
        return self.service.status_info()
    
    def is_running(self) -> bool:
        """Check if service is running."""
        if self.service is None:
            return False
        
        return self.service.status == ServiceStatus.RUNNING
