"""
Concurrent Processing Module

This module provides concurrent processing capabilities including thread pools,
queue management, resource monitoring, and priority-based processing.
"""

import threading
import queue
import time
import psutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import asyncio
from threading import Lock, Event

logger = logging.getLogger(__name__)

class ProcessingPriority(int, Enum):
    """Processing priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProcessingJob:
    """A processing job with priority and metadata."""
    job_id: str
    file_path: Path
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

@dataclass
class ResourceLimits:
    """Resource usage limits and thresholds."""
    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0
    max_disk_usage_percent: float = 90.0
    max_concurrent_jobs: int = 4
    memory_threshold_mb: int = 400  # Warning threshold
    cpu_threshold_percent: float = 70.0  # Warning threshold

@dataclass
class ProcessingMetrics:
    """Processing performance metrics."""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    peak_memory_usage: float = 0.0
    peak_cpu_usage: float = 0.0
    current_queue_size: int = 0
    active_workers: int = 0

class PriorityQueue:
    """Priority queue for processing jobs."""
    
    def __init__(self):
        self._queues: Dict[ProcessingPriority, queue.Queue] = {
            priority: queue.Queue() for priority in ProcessingPriority
        }
        self._lock = Lock()
        self._total_size = 0
    
    def put(self, job: ProcessingJob):
        """Add a job to the appropriate priority queue."""
        with self._lock:
            self._queues[job.priority].put(job)
            self._total_size += 1
    
    def get(self, timeout: Optional[float] = None) -> Optional[ProcessingJob]:
        """Get the highest priority job available."""
        with self._lock:
            # Check queues in priority order (URGENT -> HIGH -> NORMAL -> LOW)
            for priority in sorted(ProcessingPriority, reverse=True):
                try:
                    job = self._queues[priority].get(timeout=0.1 if timeout else None)
                    self._total_size -= 1
                    return job
                except queue.Empty:
                    continue
            
            if timeout:
                # If no job available and timeout specified, wait
                time.sleep(0.1)
                return self.get(timeout - 0.1 if timeout > 0.1 else None)
            
            return None
    
    def size(self) -> int:
        """Get total queue size."""
        with self._lock:
            return self._total_size
    
    def priority_sizes(self) -> Dict[ProcessingPriority, int]:
        """Get queue sizes by priority."""
        with self._lock:
            return {priority: q.qsize() for priority, q in self._queues.items()}

class ResourceMonitor:
    """Monitor system resource usage and enforce limits."""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self._lock = Lock()
        self._current_usage = {
            'memory_mb': 0.0,
            'cpu_percent': 0.0,
            'disk_percent': 0.0
        }
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """Start resource monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._update_usage()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
    
    def _update_usage(self):
        """Update current resource usage."""
        try:
            process = psutil.Process()
            
            with self._lock:
                self._current_usage['memory_mb'] = process.memory_info().rss / 1024 / 1024
                self._current_usage['cpu_percent'] = process.cpu_percent()
                
                # Get disk usage for the current working directory
                disk_usage = psutil.disk_usage('.')
                self._current_usage['disk_percent'] = (disk_usage.used / disk_usage.total) * 100
                
        except Exception as e:
            logger.error(f"Error updating resource usage: {e}")
    
    def can_process_job(self) -> Tuple[bool, str]:
        """Check if a new job can be processed based on resource limits."""
        with self._lock:
            if self._current_usage['memory_mb'] > self.limits.max_memory_mb:
                return False, f"Memory usage too high: {self._current_usage['memory_mb']:.1f}MB > {self.limits.max_memory_mb}MB"
            
            if self._current_usage['cpu_percent'] > self.limits.max_cpu_percent:
                return False, f"CPU usage too high: {self._current_usage['cpu_percent']:.1f}% > {self.limits.max_cpu_percent}%"
            
            if self._current_usage['disk_percent'] > self.limits.max_disk_usage_percent:
                return False, f"Disk usage too high: {self._current_usage['disk_percent']:.1f}% > {self.limits.max_disk_usage_percent}%"
            
            return True, "Resources available"
    
    def get_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        with self._lock:
            return self._current_usage.copy()
    
    def is_under_load(self) -> bool:
        """Check if system is under load (warning thresholds)."""
        with self._lock:
            return (self._current_usage['memory_mb'] > self.limits.memory_threshold_mb or
                    self._current_usage['cpu_percent'] > self.limits.cpu_threshold_percent)

class ConcurrentProcessor:
    """Main concurrent processing engine."""
    
    def __init__(self, 
                 max_workers: int = 4,
                 resource_limits: Optional[ResourceLimits] = None,
                 job_processor: Optional[Callable[[ProcessingJob], Any]] = None):
        self.max_workers = max_workers
        self.resource_limits = resource_limits or ResourceLimits()
        self.job_processor = job_processor or self._default_job_processor
        
        # Initialize components
        self.priority_queue = PriorityQueue()
        self.resource_monitor = ResourceMonitor(self.resource_limits)
        self.metrics = ProcessingMetrics()
        
        # Threading components
        self.executor: Optional[ThreadPoolExecutor] = None
        self.shutdown_event = Event()
        self._lock = Lock()
        
        # Job tracking
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.completed_jobs: List[ProcessingJob] = []
        self.failed_jobs: List[ProcessingJob] = []
    
    def start(self):
        """Start the concurrent processor."""
        if self.executor is not None:
            logger.warning("Processor is already running")
            return
        
        logger.info(f"Starting concurrent processor with {self.max_workers} workers")
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Start thread pool
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Start job processing loop
        self._process_jobs()
        
        logger.info("Concurrent processor started")
    
    def stop(self, timeout: float = 30.0):
        """Stop the concurrent processor."""
        if self.executor is None:
            logger.warning("Processor is not running")
            return
        
        logger.info("Stopping concurrent processor...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()
        
        # Shutdown executor
        self.executor.shutdown(wait=True, timeout=timeout)
        self.executor = None
        
        logger.info("Concurrent processor stopped")
    
    def submit_job(self, job: ProcessingJob) -> bool:
        """Submit a job for processing."""
        if self.executor is None:
            logger.error("Processor is not running")
            return False
        
        # Check resource limits
        can_process, reason = self.resource_monitor.can_process_job()
        if not can_process:
            logger.warning(f"Cannot process job {job.job_id}: {reason}")
            job.status = JobStatus.FAILED
            job.error_message = reason
            self.failed_jobs.append(job)
            return False
        
        # Add to priority queue
        self.priority_queue.put(job)
        
        with self._lock:
            self.metrics.total_jobs += 1
            self.metrics.current_queue_size = self.priority_queue.size()
        
        logger.info(f"Job {job.job_id} submitted with priority {job.priority.name}")
        return True
    
    def _process_jobs(self):
        """Main job processing loop."""
        while not self.shutdown_event.is_set():
            try:
                # Get next job
                job = self.priority_queue.get(timeout=1.0)
                if job is None:
                    continue
                
                # Check if we can process it
                can_process, reason = self.resource_monitor.can_process_job()
                if not can_process:
                    # Put job back in queue if resources not available
                    self.priority_queue.put(job)
                    time.sleep(1)
                    continue
                
                # Submit job to thread pool
                future = self.executor.submit(self._process_single_job, job)
                
                # Track active job
                with self._lock:
                    self.active_jobs[job.job_id] = job
                    self.metrics.active_workers = len(self.active_jobs)
                    self.metrics.current_queue_size = self.priority_queue.size()
                
            except Exception as e:
                logger.error(f"Error in job processing loop: {e}")
                time.sleep(1)
    
    def _process_single_job(self, job: ProcessingJob):
        """Process a single job."""
        try:
            logger.info(f"Processing job {job.job_id}: {job.file_path.name}")
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
            
            # Process the job
            start_time = time.time()
            result = self.job_processor(job)
            processing_time = time.time() - start_time
            
            # Update job status
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
            # Update metrics
            with self._lock:
                self.metrics.completed_jobs += 1
                self.metrics.total_processing_time += processing_time
                self.metrics.average_processing_time = (
                    self.metrics.total_processing_time / self.metrics.completed_jobs
                )
                self.completed_jobs.append(job)
                
                # Remove from active jobs
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
                    self.metrics.active_workers = len(self.active_jobs)
            
            logger.info(f"Job {job.job_id} completed in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            
            # Handle retry logic
            job.retry_count += 1
            if job.retry_count <= job.max_retries:
                logger.info(f"Retrying job {job.job_id} (attempt {job.retry_count})")
                job.status = JobStatus.PENDING
                self.priority_queue.put(job)
            else:
                # Max retries exceeded
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now()
                
                with self._lock:
                    self.metrics.failed_jobs += 1
                    self.failed_jobs.append(job)
                    
                    # Remove from active jobs
                    if job.job_id in self.active_jobs:
                        del self.active_jobs[job.job_id]
                        self.metrics.active_workers = len(self.active_jobs)
    
    def _default_job_processor(self, job: ProcessingJob) -> Any:
        """Default job processor (placeholder)."""
        # Simulate processing time based on file size
        file_size_mb = job.file_path.stat().st_size / (1024 * 1024)
        processing_time = min(5.0, max(0.1, file_size_mb * 0.1))  # 0.1s per MB, max 5s
        
        time.sleep(processing_time)
        
        # Simulate occasional failures
        if job.retry_count > 0 and job.retry_count % 3 == 0:
            raise Exception(f"Simulated processing error for {job.file_path.name}")
        
        return f"Processed {job.file_path.name}"
    
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics."""
        with self._lock:
            return ProcessingMetrics(
                total_jobs=self.metrics.total_jobs,
                completed_jobs=self.metrics.completed_jobs,
                failed_jobs=self.metrics.failed_jobs,
                cancelled_jobs=self.metrics.cancelled_jobs,
                total_processing_time=self.metrics.total_processing_time,
                average_processing_time=self.metrics.average_processing_time,
                peak_memory_usage=self.metrics.peak_memory_usage,
                peak_cpu_usage=self.metrics.peak_cpu_usage,
                current_queue_size=self.priority_queue.size(),
                active_workers=len(self.active_jobs)
            )
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get detailed queue status."""
        return {
            'total_size': self.priority_queue.size(),
            'priority_sizes': self.priority_queue.priority_sizes(),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
            'failed_jobs': len(self.failed_jobs),
            'resource_usage': self.resource_monitor.get_usage(),
            'under_load': self.resource_monitor.is_under_load()
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        # Note: This is a simplified implementation
        # In a real system, you'd need more sophisticated job cancellation
        logger.warning(f"Job cancellation not fully implemented for {job_id}")
        return False
    
    def graceful_degradation(self) -> bool:
        """Implement graceful degradation under load."""
        if not self.resource_monitor.is_under_load():
            return False
        
        logger.warning("System under load, implementing graceful degradation")
        
        # Reduce concurrent workers
        if self.max_workers > 1:
            self.max_workers = max(1, self.max_workers - 1)
            logger.info(f"Reduced workers to {self.max_workers}")
        
        # Increase processing delays
        time.sleep(0.5)
        
        return True
