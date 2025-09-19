"""
System Monitoring Module

This module provides comprehensive system monitoring including health checks,
performance monitoring, resource tracking, and alerting for critical errors.
"""

import psutil
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import asyncio
from collections import deque

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertLevel(str, Enum):
    """Alert levels for monitoring."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ResourceMetrics:
    """System resource metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_free_gb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    process_count: int = 0
    load_average: Tuple[float, float, float] = (0.0, 0.0, 0.0)

@dataclass
class PerformanceMetrics:
    """Application performance metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    requests_per_second: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    active_connections: int = 0
    queue_size: int = 0
    processing_time: float = 0.0
    throughput_mb_per_sec: float = 0.0

@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """System alert."""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceMonitor:
    """Monitors system resource usage."""
    
    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics_history: deque = deque(maxlen=3600)  # Keep 1 hour of data
        self.network_io_start = None
        self.network_io_previous = None
        
    def start_monitoring(self):
        """Start resource monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(self.check_interval)
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent_mb = network_io.bytes_sent / 1024 / 1024
            network_recv_mb = network_io.bytes_recv / 1024 / 1024
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix only)
            try:
                load_average = psutil.getloadavg()
            except AttributeError:
                load_average = (0.0, 0.0, 0.0)
            
            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")
            return ResourceMetrics()
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return self._collect_metrics()
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[ResourceMetrics]:
        """Get metrics history for specified duration."""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, duration_minutes: int = 5) -> ResourceMetrics:
        """Get average metrics over specified duration."""
        recent_metrics = self.get_metrics_history(duration_minutes)
        if not recent_metrics:
            return self.get_current_metrics()
        
        return ResourceMetrics(
            cpu_percent=sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            memory_percent=sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            memory_used_mb=sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics),
            memory_available_mb=sum(m.memory_available_mb for m in recent_metrics) / len(recent_metrics),
            disk_usage_percent=sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics),
            disk_free_gb=sum(m.disk_free_gb for m in recent_metrics) / len(recent_metrics),
            network_sent_mb=sum(m.network_sent_mb for m in recent_metrics) / len(recent_metrics),
            network_recv_mb=sum(m.network_recv_mb for m in recent_metrics) / len(recent_metrics),
            process_count=sum(m.process_count for m in recent_metrics) / len(recent_metrics),
            load_average=(
                sum(m.load_average[0] for m in recent_metrics) / len(recent_metrics),
                sum(m.load_average[1] for m in recent_metrics) / len(recent_metrics),
                sum(m.load_average[2] for m in recent_metrics) / len(recent_metrics)
            )
        )

class PerformanceMonitor:
    """Monitors application performance."""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=3600)  # Keep 1 hour of data
        self.request_times: deque = deque(maxlen=1000)
        self.error_count = 0
        self.request_count = 0
        self.start_time = datetime.now()
    
    def record_request(self, response_time: float, success: bool = True):
        """Record a request and its response time."""
        self.request_times.append(response_time)
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Update metrics
        self._update_metrics()
    
    def _update_metrics(self):
        """Update performance metrics."""
        current_time = datetime.now()
        uptime_seconds = (current_time - self.start_time).total_seconds()
        
        # Calculate requests per second
        requests_per_second = self.request_count / uptime_seconds if uptime_seconds > 0 else 0
        
        # Calculate average response time
        average_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        
        # Calculate error rate
        error_rate = (self.error_count / self.request_count) * 100 if self.request_count > 0 else 0
        
        metrics = PerformanceMetrics(
            requests_per_second=requests_per_second,
            average_response_time=average_response_time,
            error_rate=error_rate,
            active_connections=len(self.request_times),
            queue_size=0,  # Would be set by queue monitoring
            processing_time=average_response_time,
            throughput_mb_per_sec=0  # Would be calculated based on data processed
        )
        
        self.metrics_history.append(metrics)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return PerformanceMetrics()
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[PerformanceMetrics]:
        """Get performance metrics history."""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

class HealthChecker:
    """Performs health checks on various system components."""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.health_checks["system_resources"] = self._check_system_resources
        self.health_checks["disk_space"] = self._check_disk_space
        self.health_checks["memory_usage"] = self._check_memory_usage
        self.health_checks["cpu_usage"] = self._check_cpu_usage
        self.health_checks["process_health"] = self._check_process_health
    
    def add_health_check(self, name: str, check_func: Callable):
        """Add a custom health check."""
        self.health_checks[name] = check_func
    
    def run_all_checks(self) -> List[HealthCheck]:
        """Run all registered health checks."""
        results = []
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = check_func()
                response_time = (time.time() - start_time) * 1000
                
                if isinstance(result, HealthCheck):
                    result.response_time_ms = response_time
                    results.append(result)
                else:
                    # Convert simple result to HealthCheck
                    status = HealthStatus.HEALTHY if result else HealthStatus.CRITICAL
                    results.append(HealthCheck(
                        name=name,
                        status=status,
                        message="Check completed",
                        response_time_ms=response_time
                    ))
            except Exception as e:
                results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Check failed: {str(e)}",
                    response_time_ms=0
                ))
        
        return results
    
    def _check_system_resources(self) -> HealthCheck:
        """Check overall system resources."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            status = HealthStatus.HEALTHY
            
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif cpu_percent > 80:
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
                status = HealthStatus.WARNING
            
            if memory.percent > 95:
                issues.append(f"Critical memory usage: {memory.percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                status = HealthStatus.WARNING
            
            if disk.percent > 95:
                issues.append(f"Critical disk usage: {disk.percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif disk.percent > 85:
                issues.append(f"High disk usage: {disk.percent:.1f}%")
                status = HealthStatus.WARNING
            
            message = "System resources are healthy" if not issues else "; ".join(issues)
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                }
            )
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check system resources: {str(e)}"
            )
    
    def _check_disk_space(self) -> HealthCheck:
        """Check disk space availability."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / 1024 / 1024 / 1024
            usage_percent = (disk.used / disk.total) * 100
            
            if free_gb < 1:
                status = HealthStatus.CRITICAL
                message = f"Critical: Only {free_gb:.1f}GB free space remaining"
            elif free_gb < 5:
                status = HealthStatus.WARNING
                message = f"Warning: Only {free_gb:.1f}GB free space remaining"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space OK: {free_gb:.1f}GB free ({usage_percent:.1f}% used)"
            
            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                details={
                    "free_gb": free_gb,
                    "usage_percent": usage_percent,
                    "total_gb": disk.total / 1024 / 1024 / 1024
                }
            )
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check disk space: {str(e)}"
            )
    
    def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            available_gb = memory.available / 1024 / 1024 / 1024
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
                message = f"Critical memory usage: {usage_percent:.1f}%"
            elif usage_percent > 85:
                status = HealthStatus.WARNING
                message = f"High memory usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage OK: {usage_percent:.1f}% ({available_gb:.1f}GB available)"
            
            return HealthCheck(
                name="memory_usage",
                status=status,
                message=message,
                details={
                    "usage_percent": usage_percent,
                    "available_gb": available_gb,
                    "total_gb": memory.total / 1024 / 1024 / 1024
                }
            )
        except Exception as e:
            return HealthCheck(
                name="memory_usage",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check memory usage: {str(e)}"
            )
    
    def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            if cpu_percent > 95:
                status = HealthStatus.CRITICAL
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 80:
                status = HealthStatus.WARNING
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage OK: {cpu_percent:.1f}%"
            
            return HealthCheck(
                name="cpu_usage",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "load_average": load_avg
                }
            )
        except Exception as e:
            return HealthCheck(
                name="cpu_usage",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check CPU usage: {str(e)}"
            )
    
    def _check_process_health(self) -> HealthCheck:
        """Check process health."""
        try:
            current_process = psutil.Process()
            
            # Check if process is responsive
            cpu_percent = current_process.cpu_percent()
            memory_info = current_process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Check for zombie processes
            children = current_process.children(recursive=True)
            zombie_count = sum(1 for child in children if child.status() == psutil.STATUS_ZOMBIE)
            
            issues = []
            status = HealthStatus.HEALTHY
            
            if zombie_count > 0:
                issues.append(f"Zombie processes detected: {zombie_count}")
                status = HealthStatus.WARNING
            
            if memory_mb > 1000:  # More than 1GB
                issues.append(f"High memory usage: {memory_mb:.1f}MB")
                status = HealthStatus.WARNING
            
            message = "Process health OK" if not issues else "; ".join(issues)
            
            return HealthCheck(
                name="process_health",
                status=status,
                message=message,
                details={
                    "memory_mb": memory_mb,
                    "cpu_percent": cpu_percent,
                    "zombie_count": zombie_count,
                    "children_count": len(children)
                }
            )
        except Exception as e:
            return HealthCheck(
                name="process_health",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check process health: {str(e)}"
            )

class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_thresholds: Dict[str, Dict[str, float]] = {
            "cpu_percent": {"warning": 80.0, "critical": 90.0},
            "memory_percent": {"warning": 85.0, "critical": 95.0},
            "disk_percent": {"warning": 85.0, "critical": 95.0},
            "error_rate": {"warning": 5.0, "critical": 10.0},
            "response_time": {"warning": 2.0, "critical": 5.0}
        }
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    def create_alert(self, level: AlertLevel, title: str, message: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a new alert."""
        alert_id = f"ALERT_{int(time.time() * 1000)}"
        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        return alert
    
    def check_thresholds(self, metrics: ResourceMetrics, performance: PerformanceMetrics):
        """Check metrics against alert thresholds."""
        # CPU threshold
        if metrics.cpu_percent >= self.alert_thresholds["cpu_percent"]["critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                "High CPU Usage",
                f"CPU usage is {metrics.cpu_percent:.1f}%",
                {"metric": "cpu_percent", "value": metrics.cpu_percent}
            )
        elif metrics.cpu_percent >= self.alert_thresholds["cpu_percent"]["warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                "Elevated CPU Usage",
                f"CPU usage is {metrics.cpu_percent:.1f}%",
                {"metric": "cpu_percent", "value": metrics.cpu_percent}
            )
        
        # Memory threshold
        if metrics.memory_percent >= self.alert_thresholds["memory_percent"]["critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                "High Memory Usage",
                f"Memory usage is {metrics.memory_percent:.1f}%",
                {"metric": "memory_percent", "value": metrics.memory_percent}
            )
        elif metrics.memory_percent >= self.alert_thresholds["memory_percent"]["warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                "Elevated Memory Usage",
                f"Memory usage is {metrics.memory_percent:.1f}%",
                {"metric": "memory_percent", "value": metrics.memory_percent}
            )
        
        # Disk threshold
        if metrics.disk_usage_percent >= self.alert_thresholds["disk_percent"]["critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                "High Disk Usage",
                f"Disk usage is {metrics.disk_usage_percent:.1f}%",
                {"metric": "disk_percent", "value": metrics.disk_usage_percent}
            )
        elif metrics.disk_usage_percent >= self.alert_thresholds["disk_percent"]["warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                "Elevated Disk Usage",
                f"Disk usage is {metrics.disk_usage_percent:.1f}%",
                {"metric": "disk_percent", "value": metrics.disk_usage_percent}
            )
        
        # Error rate threshold
        if performance.error_rate >= self.alert_thresholds["error_rate"]["critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                "High Error Rate",
                f"Error rate is {performance.error_rate:.1f}%",
                {"metric": "error_rate", "value": performance.error_rate}
            )
        elif performance.error_rate >= self.alert_thresholds["error_rate"]["warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                "Elevated Error Rate",
                f"Error rate is {performance.error_rate:.1f}%",
                {"metric": "error_rate", "value": performance.error_rate}
            )
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                break

class SystemMonitor:
    """Main system monitoring orchestrator."""
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Initialize components
        self.resource_monitor = ResourceMonitor()
        self.performance_monitor = PerformanceMonitor()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        
        # Setup default alert handlers
        self.alert_manager.add_alert_handler(self._log_alert)
    
    def start_monitoring(self):
        """Start system monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.resource_monitor.start_monitoring()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        self.resource_monitor.stop_monitoring()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Run health checks
                health_checks = self.health_checker.run_all_checks()
                
                # Get current metrics
                resource_metrics = self.resource_monitor.get_current_metrics()
                performance_metrics = self.performance_monitor.get_current_metrics()
                
                # Check for alerts
                self.alert_manager.check_thresholds(resource_metrics, performance_metrics)
                
                # Log health status
                critical_checks = [h for h in health_checks if h.status == HealthStatus.CRITICAL]
                if critical_checks:
                    logger.error(f"Critical health checks failed: {[h.name for h in critical_checks]}")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _log_alert(self, alert: Alert):
        """Default alert handler that logs alerts."""
        level_map = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        
        logger.log(level_map[alert.level], f"[{alert.alert_id}] {alert.title}: {alert.message}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        health_checks = self.health_checker.run_all_checks()
        resource_metrics = self.resource_monitor.get_current_metrics()
        performance_metrics = self.performance_monitor.get_current_metrics()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Determine overall health
        critical_checks = [h for h in health_checks if h.status == HealthStatus.CRITICAL]
        warning_checks = [h for h in health_checks if h.status == HealthStatus.WARNING]
        
        if critical_checks:
            overall_health = HealthStatus.CRITICAL
        elif warning_checks:
            overall_health = HealthStatus.WARNING
        else:
            overall_health = HealthStatus.HEALTHY
        
        return {
            "overall_health": overall_health.value,
            "timestamp": datetime.now().isoformat(),
            "health_checks": [
                {
                    "name": h.name,
                    "status": h.status.value,
                    "message": h.message,
                    "response_time_ms": h.response_time_ms
                }
                for h in health_checks
            ],
            "resource_metrics": {
                "cpu_percent": resource_metrics.cpu_percent,
                "memory_percent": resource_metrics.memory_percent,
                "memory_used_mb": resource_metrics.memory_used_mb,
                "disk_usage_percent": resource_metrics.disk_usage_percent,
                "disk_free_gb": resource_metrics.disk_free_gb
            },
            "performance_metrics": {
                "requests_per_second": performance_metrics.requests_per_second,
                "average_response_time": performance_metrics.average_response_time,
                "error_rate": performance_metrics.error_rate
            },
            "active_alerts": len(active_alerts),
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ]
        }
