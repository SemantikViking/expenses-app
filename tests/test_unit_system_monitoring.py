"""
Unit Tests for System Monitoring Module

This module contains comprehensive unit tests for the system monitoring
and health checking system.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.receipt_processor.system_monitoring import (
    HealthStatus, AlertLevel, ResourceMetrics, PerformanceMetrics,
    HealthCheck, Alert, ResourceMonitor, PerformanceMonitor,
    HealthChecker, AlertManager, SystemMonitor
)

class TestHealthStatus:
    """Test cases for HealthStatus enum."""
    
    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.WARNING == "warning"
        assert HealthStatus.CRITICAL == "critical"
        assert HealthStatus.UNKNOWN == "unknown"

class TestAlertLevel:
    """Test cases for AlertLevel enum."""
    
    def test_alert_level_values(self):
        """Test AlertLevel enum values."""
        assert AlertLevel.INFO == "info"
        assert AlertLevel.WARNING == "warning"
        assert AlertLevel.ERROR == "error"
        assert AlertLevel.CRITICAL == "critical"

class TestResourceMetrics:
    """Test cases for ResourceMetrics."""
    
    def test_resource_metrics_creation(self, sample_resource_metrics):
        """Test ResourceMetrics creation."""
        metrics = sample_resource_metrics
        assert metrics.cpu_percent == 45.0
        assert metrics.memory_percent == 60.0
        assert metrics.memory_used_mb == 2048.0
        assert metrics.memory_available_mb == 1365.0
        assert metrics.disk_usage_percent == 25.0
        assert metrics.disk_free_gb == 75.0
        assert metrics.network_sent_mb == 100.0
        assert metrics.network_recv_mb == 150.0
        assert metrics.process_count == 150
        assert metrics.load_average == (1.2, 1.5, 1.8)
    
    def test_resource_metrics_defaults(self):
        """Test ResourceMetrics with default values."""
        metrics = ResourceMetrics()
        assert metrics.cpu_percent == 0.0
        assert metrics.memory_percent == 0.0
        assert metrics.memory_used_mb == 0.0
        assert metrics.memory_available_mb == 0.0
        assert metrics.disk_usage_percent == 0.0
        assert metrics.disk_free_gb == 0.0
        assert metrics.network_sent_mb == 0.0
        assert metrics.network_recv_mb == 0.0
        assert metrics.process_count == 0
        assert metrics.load_average == (0.0, 0.0, 0.0)

class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics."""
    
    def test_performance_metrics_creation(self, sample_performance_metrics):
        """Test PerformanceMetrics creation."""
        metrics = sample_performance_metrics
        assert metrics.requests_per_second == 10.5
        assert metrics.average_response_time == 0.5
        assert metrics.error_rate == 2.0
        assert metrics.active_connections == 25
        assert metrics.queue_size == 5
        assert metrics.processing_time == 0.3
        assert metrics.throughput_mb_per_sec == 5.2
    
    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metrics = PerformanceMetrics()
        assert metrics.requests_per_second == 0.0
        assert metrics.average_response_time == 0.0
        assert metrics.error_rate == 0.0
        assert metrics.active_connections == 0
        assert metrics.queue_size == 0
        assert metrics.processing_time == 0.0
        assert metrics.throughput_mb_per_sec == 0.0

class TestHealthCheck:
    """Test cases for HealthCheck."""
    
    def test_health_check_creation(self, sample_health_check):
        """Test HealthCheck creation."""
        check = sample_health_check
        assert check.name == "test_check"
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "Test check passed"
        assert check.response_time_ms == 50.0
        assert check.details == {"cpu_percent": 45.0, "memory_percent": 60.0}
    
    def test_health_check_defaults(self):
        """Test HealthCheck with default values."""
        check = HealthCheck(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="Test check"
        )
        assert check.name == "test_check"
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "Test check"
        assert check.response_time_ms == 0.0
        assert check.details == {}

class TestAlert:
    """Test cases for Alert."""
    
    def test_alert_creation(self, sample_alert):
        """Test Alert creation."""
        alert = sample_alert
        assert alert.alert_id == "ALERT_001"
        assert alert.level == AlertLevel.WARNING
        assert alert.title == "High CPU Usage"
        assert alert.message == "CPU usage is above 80%"
        assert alert.metadata == {"cpu_percent": 85.0}
        assert alert.resolved is False
        assert alert.resolved_at is None
    
    def test_alert_defaults(self):
        """Test Alert with default values."""
        alert = Alert(
            alert_id="ALERT_001",
            level=AlertLevel.INFO,
            title="Test Alert",
            message="Test message"
        )
        assert alert.alert_id == "ALERT_001"
        assert alert.level == AlertLevel.INFO
        assert alert.title == "Test Alert"
        assert alert.message == "Test message"
        assert alert.resolved is False
        assert alert.resolved_at is None
        assert alert.metadata == {}

class TestResourceMonitor:
    """Test cases for ResourceMonitor."""
    
    def test_resource_monitor_creation(self):
        """Test ResourceMonitor creation."""
        monitor = ResourceMonitor(check_interval=1.0)
        assert monitor.check_interval == 1.0
        assert monitor.monitoring is False
        assert monitor.monitor_thread is None
        assert monitor.metrics_history.maxlen == 3600
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.pids')
    @patch('psutil.getloadavg')
    def test_collect_metrics(self, mock_loadavg, mock_pids, mock_net_io, 
                           mock_disk, mock_memory, mock_cpu):
        """Test metrics collection."""
        # Setup mocks
        mock_cpu.return_value = 45.0
        mock_memory.return_value = Mock(
            percent=60.0,
            used=2048 * 1024 * 1024,
            available=1365 * 1024 * 1024
        )
        mock_disk.return_value = Mock(
            used=25 * 1024 * 1024 * 1024,
            total=100 * 1024 * 1024 * 1024,
            free=75 * 1024 * 1024 * 1024
        )
        mock_net_io.return_value = Mock(
            bytes_sent=100 * 1024 * 1024,
            bytes_recv=150 * 1024 * 1024
        )
        mock_pids.return_value = list(range(150))
        mock_loadavg.return_value = (1.2, 1.5, 1.8)
        
        monitor = ResourceMonitor()
        metrics = monitor._collect_metrics()
        
        assert metrics.cpu_percent == 45.0
        assert metrics.memory_percent == 60.0
        assert metrics.memory_used_mb == 2048.0
        assert metrics.memory_available_mb == 1365.0
        assert metrics.disk_usage_percent == 25.0
        assert metrics.disk_free_gb == 75.0
        assert metrics.network_sent_mb == 100.0
        assert metrics.network_recv_mb == 150.0
        assert metrics.process_count == 150
        assert metrics.load_average == (1.2, 1.5, 1.8)
    
    def test_get_current_metrics_empty_history(self):
        """Test get_current_metrics with empty history."""
        monitor = ResourceMonitor()
        metrics = monitor.get_current_metrics()
        assert isinstance(metrics, ResourceMetrics)
    
    def test_get_metrics_history(self):
        """Test get_metrics_history filtering."""
        monitor = ResourceMonitor()
        
        # Add some metrics to history
        now = datetime.now()
        for i in range(10):
            metrics = ResourceMetrics(timestamp=now - timedelta(minutes=i))
            monitor.metrics_history.append(metrics)
        
        # Test filtering
        recent_metrics = monitor.get_metrics_history(duration_minutes=5)
        assert len(recent_metrics) == 6  # 0, 1, 2, 3, 4, 5 minutes ago
    
    def test_get_average_metrics(self):
        """Test get_average_metrics calculation."""
        monitor = ResourceMonitor()
        
        # Add some metrics to history
        for i in range(5):
            metrics = ResourceMetrics(
                cpu_percent=10.0 + i,
                memory_percent=20.0 + i,
                memory_used_mb=1000.0 + i * 100
            )
            monitor.metrics_history.append(metrics)
        
        avg_metrics = monitor.get_average_metrics(duration_minutes=10)
        assert avg_metrics.cpu_percent == 12.0  # (10+11+12+13+14)/5
        assert avg_metrics.memory_percent == 22.0  # (20+21+22+23+24)/5
        assert avg_metrics.memory_used_mb == 1200.0  # (1000+1100+1200+1300+1400)/5

class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor."""
    
    def test_performance_monitor_creation(self):
        """Test PerformanceMonitor creation."""
        monitor = PerformanceMonitor()
        assert monitor.metrics_history.maxlen == 3600
        assert monitor.request_times.maxlen == 1000
        assert monitor.error_count == 0
        assert monitor.request_count == 0
        assert monitor.start_time is not None
    
    def test_record_request(self):
        """Test request recording."""
        monitor = PerformanceMonitor()
        
        # Record some requests
        monitor.record_request(0.5, success=True)
        monitor.record_request(0.3, success=True)
        monitor.record_request(0.7, success=False)
        
        assert monitor.request_count == 3
        assert monitor.error_count == 1
        assert len(monitor.request_times) == 3
        assert len(monitor.metrics_history) == 3
    
    def test_get_current_metrics(self):
        """Test get_current_metrics."""
        monitor = PerformanceMonitor()
        
        # Record some requests
        for i in range(5):
            monitor.record_request(0.1 * (i + 1), success=True)
        
        metrics = monitor.get_current_metrics()
        assert metrics.requests_per_second > 0
        assert metrics.average_response_time > 0
        assert metrics.error_rate == 0.0
    
    def test_get_metrics_history(self):
        """Test get_metrics_history filtering."""
        monitor = PerformanceMonitor()
        
        # Add some metrics to history
        now = datetime.now()
        for i in range(10):
            metrics = PerformanceMetrics(timestamp=now - timedelta(minutes=i))
            monitor.metrics_history.append(metrics)
        
        # Test filtering
        recent_metrics = monitor.get_metrics_history(duration_minutes=5)
        assert len(recent_metrics) == 6  # 0, 1, 2, 3, 4, 5 minutes ago

class TestHealthChecker:
    """Test cases for HealthChecker."""
    
    def test_health_checker_creation(self):
        """Test HealthChecker creation."""
        checker = HealthChecker()
        assert len(checker.health_checks) > 0
        assert "system_resources" in checker.health_checks
        assert "disk_space" in checker.health_checks
        assert "memory_usage" in checker.health_checks
        assert "cpu_usage" in checker.health_checks
        assert "process_health" in checker.health_checks
    
    def test_add_health_check(self):
        """Test adding custom health check."""
        checker = HealthChecker()
        
        def custom_check():
            return HealthCheck(
                name="custom_check",
                status=HealthStatus.HEALTHY,
                message="Custom check passed"
            )
        
        checker.add_health_check("custom_check", custom_check)
        assert "custom_check" in checker.health_checks
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_check_system_resources_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test system resources check when healthy."""
        mock_cpu.return_value = 45.0
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=25.0)
        
        checker = HealthChecker()
        result = checker._check_system_resources()
        
        assert result.name == "system_resources"
        assert result.status == HealthStatus.HEALTHY
        assert "healthy" in result.message.lower()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_check_system_resources_critical(self, mock_disk, mock_memory, mock_cpu):
        """Test system resources check when critical."""
        mock_cpu.return_value = 95.0  # Critical CPU
        mock_memory.return_value = Mock(percent=98.0)  # Critical memory
        mock_disk.return_value = Mock(percent=25.0)
        
        checker = HealthChecker()
        result = checker._check_system_resources()
        
        assert result.name == "system_resources"
        assert result.status == HealthStatus.CRITICAL
        assert "critical" in result.message.lower()
    
    @patch('psutil.disk_usage')
    def test_check_disk_space_healthy(self, mock_disk):
        """Test disk space check when healthy."""
        mock_disk.return_value = Mock(
            free=50 * 1024 * 1024 * 1024,  # 50GB free
            total=100 * 1024 * 1024 * 1024  # 100GB total
        )
        
        checker = HealthChecker()
        result = checker._check_disk_space()
        
        assert result.name == "disk_space"
        assert result.status == HealthStatus.HEALTHY
        assert "ok" in result.message.lower()
    
    @patch('psutil.disk_usage')
    def test_check_disk_space_critical(self, mock_disk):
        """Test disk space check when critical."""
        mock_disk.return_value = Mock(
            free=0.5 * 1024 * 1024 * 1024,  # 0.5GB free
            total=100 * 1024 * 1024 * 1024  # 100GB total
        )
        
        checker = HealthChecker()
        result = checker._check_disk_space()
        
        assert result.name == "disk_space"
        assert result.status == HealthStatus.CRITICAL
        assert "critical" in result.message.lower()
    
    @patch('psutil.virtual_memory')
    def test_check_memory_usage_healthy(self, mock_memory):
        """Test memory usage check when healthy."""
        mock_memory.return_value = Mock(
            percent=60.0,
            available=4 * 1024 * 1024 * 1024  # 4GB available
        )
        
        checker = HealthChecker()
        result = checker._check_memory_usage()
        
        assert result.name == "memory_usage"
        assert result.status == HealthStatus.HEALTHY
        assert "ok" in result.message.lower()
    
    @patch('psutil.virtual_memory')
    def test_check_memory_usage_critical(self, mock_memory):
        """Test memory usage check when critical."""
        mock_memory.return_value = Mock(
            percent=98.0,
            available=0.1 * 1024 * 1024 * 1024  # 0.1GB available
        )
        
        checker = HealthChecker()
        result = checker._check_memory_usage()
        
        assert result.name == "memory_usage"
        assert result.status == HealthStatus.CRITICAL
        assert "critical" in result.message.lower()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.getloadavg')
    def test_check_cpu_usage_healthy(self, mock_loadavg, mock_cpu):
        """Test CPU usage check when healthy."""
        mock_cpu.return_value = 45.0
        mock_loadavg.return_value = (1.2, 1.5, 1.8)
        
        checker = HealthChecker()
        result = checker._check_cpu_usage()
        
        assert result.name == "cpu_usage"
        assert result.status == HealthStatus.HEALTHY
        assert "ok" in result.message.lower()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.getloadavg')
    def test_check_cpu_usage_critical(self, mock_loadavg, mock_cpu):
        """Test CPU usage check when critical."""
        mock_cpu.return_value = 98.0
        mock_loadavg.return_value = (1.2, 1.5, 1.8)
        
        checker = HealthChecker()
        result = checker._check_cpu_usage()
        
        assert result.name == "cpu_usage"
        assert result.status == HealthStatus.CRITICAL
        assert "critical" in result.message.lower()
    
    @patch('psutil.Process')
    def test_check_process_health_healthy(self, mock_process_class):
        """Test process health check when healthy."""
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 10.0
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
        mock_process.children.return_value = []
        mock_process_class.return_value = mock_process
        
        checker = HealthChecker()
        result = checker._check_process_health()
        
        assert result.name == "process_health"
        assert result.status == HealthStatus.HEALTHY
        assert "ok" in result.message.lower()
    
    def test_run_all_checks(self):
        """Test running all health checks."""
        checker = HealthChecker()
        
        # Mock all check methods to return healthy results
        with patch.object(checker, '_check_system_resources') as mock_sys, \
             patch.object(checker, '_check_disk_space') as mock_disk, \
             patch.object(checker, '_check_memory_usage') as mock_mem, \
             patch.object(checker, '_check_cpu_usage') as mock_cpu, \
             patch.object(checker, '_check_process_health') as mock_proc:
            
            mock_sys.return_value = HealthCheck("system_resources", HealthStatus.HEALTHY, "OK")
            mock_disk.return_value = HealthCheck("disk_space", HealthStatus.HEALTHY, "OK")
            mock_mem.return_value = HealthCheck("memory_usage", HealthStatus.HEALTHY, "OK")
            mock_cpu.return_value = HealthCheck("cpu_usage", HealthStatus.HEALTHY, "OK")
            mock_proc.return_value = HealthCheck("process_health", HealthStatus.HEALTHY, "OK")
            
            results = checker.run_all_checks()
            
            assert len(results) == 5
            for result in results:
                assert result.status == HealthStatus.HEALTHY
                assert result.response_time_ms >= 0

class TestAlertManager:
    """Test cases for AlertManager."""
    
    def test_alert_manager_creation(self):
        """Test AlertManager creation."""
        manager = AlertManager()
        assert len(manager.alerts) == 0
        assert len(manager.alert_handlers) == 0
        assert "cpu_percent" in manager.alert_thresholds
        assert "memory_percent" in manager.alert_thresholds
        assert "disk_percent" in manager.alert_thresholds
    
    def test_add_alert_handler(self):
        """Test adding alert handler."""
        manager = AlertManager()
        handler = Mock()
        manager.add_alert_handler(handler)
        assert handler in manager.alert_handlers
    
    def test_create_alert(self):
        """Test alert creation."""
        manager = AlertManager()
        alert = manager.create_alert(
            AlertLevel.WARNING,
            "Test Alert",
            "Test message",
            {"test": True}
        )
        
        assert alert.alert_id is not None
        assert alert.level == AlertLevel.WARNING
        assert alert.title == "Test Alert"
        assert alert.message == "Test message"
        assert alert.metadata == {"test": True}
        assert alert.resolved is False
        assert len(manager.alerts) == 1
    
    def test_check_thresholds_cpu_warning(self):
        """Test CPU threshold checking - warning."""
        manager = AlertManager()
        
        metrics = ResourceMetrics(cpu_percent=85.0)
        performance = PerformanceMetrics()
        
        manager.check_thresholds(metrics, performance)
        
        assert len(manager.alerts) == 1
        alert = manager.alerts[0]
        assert alert.level == AlertLevel.WARNING
        assert "CPU" in alert.title
    
    def test_check_thresholds_cpu_critical(self):
        """Test CPU threshold checking - critical."""
        manager = AlertManager()
        
        metrics = ResourceMetrics(cpu_percent=95.0)
        performance = PerformanceMetrics()
        
        manager.check_thresholds(metrics, performance)
        
        assert len(manager.alerts) == 1
        alert = manager.alerts[0]
        assert alert.level == AlertLevel.CRITICAL
        assert "CPU" in alert.title
    
    def test_check_thresholds_memory_critical(self):
        """Test memory threshold checking - critical."""
        manager = AlertManager()
        
        metrics = ResourceMetrics(memory_percent=98.0)
        performance = PerformanceMetrics()
        
        manager.check_thresholds(metrics, performance)
        
        assert len(manager.alerts) == 1
        alert = manager.alerts[0]
        assert alert.level == AlertLevel.CRITICAL
        assert "Memory" in alert.title
    
    def test_check_thresholds_disk_critical(self):
        """Test disk threshold checking - critical."""
        manager = AlertManager()
        
        metrics = ResourceMetrics(disk_usage_percent=98.0)
        performance = PerformanceMetrics()
        
        manager.check_thresholds(metrics, performance)
        
        assert len(manager.alerts) == 1
        alert = manager.alerts[0]
        assert alert.level == AlertLevel.CRITICAL
        assert "Disk" in alert.title
    
    def test_check_thresholds_error_rate_critical(self):
        """Test error rate threshold checking - critical."""
        manager = AlertManager()
        
        metrics = ResourceMetrics()
        performance = PerformanceMetrics(error_rate=15.0)
        
        manager.check_thresholds(metrics, performance)
        
        assert len(manager.alerts) == 1
        alert = manager.alerts[0]
        assert alert.level == AlertLevel.CRITICAL
        assert "Error Rate" in alert.title
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        manager = AlertManager()
        
        # Create some alerts
        alert1 = manager.create_alert(AlertLevel.WARNING, "Alert 1", "Message 1")
        alert2 = manager.create_alert(AlertLevel.ERROR, "Alert 2", "Message 2")
        alert3 = manager.create_alert(AlertLevel.INFO, "Alert 3", "Message 3")
        
        # Resolve one alert
        manager.resolve_alert(alert2.alert_id)
        
        active_alerts = manager.get_active_alerts()
        assert len(active_alerts) == 2
        assert alert1 in active_alerts
        assert alert3 in active_alerts
        assert alert2 not in active_alerts
    
    def test_resolve_alert(self):
        """Test alert resolution."""
        manager = AlertManager()
        
        alert = manager.create_alert(AlertLevel.WARNING, "Test Alert", "Test message")
        assert alert.resolved is False
        assert alert.resolved_at is None
        
        manager.resolve_alert(alert.alert_id)
        assert alert.resolved is True
        assert alert.resolved_at is not None

class TestSystemMonitor:
    """Test cases for SystemMonitor."""
    
    def test_system_monitor_creation(self):
        """Test SystemMonitor creation."""
        monitor = SystemMonitor(check_interval=30.0)
        assert monitor.check_interval == 30.0
        assert monitor.monitoring is False
        assert monitor.monitor_thread is None
        assert monitor.resource_monitor is not None
        assert monitor.performance_monitor is not None
        assert monitor.health_checker is not None
        assert monitor.alert_manager is not None
    
    def test_start_monitoring(self):
        """Test starting monitoring."""
        monitor = SystemMonitor()
        monitor.start_monitoring()
        
        assert monitor.monitoring is True
        assert monitor.resource_monitor.monitoring is True
        assert monitor.monitor_thread is not None
        assert monitor.monitor_thread.is_alive()
        
        monitor.stop_monitoring()
    
    def test_stop_monitoring(self):
        """Test stopping monitoring."""
        monitor = SystemMonitor()
        monitor.start_monitoring()
        monitor.stop_monitoring()
        
        assert monitor.monitoring is False
        assert monitor.resource_monitor.monitoring is False
    
    def test_get_system_status(self):
        """Test getting system status."""
        monitor = SystemMonitor()
        
        # Mock the health checker and resource monitor
        with patch.object(monitor.health_checker, 'run_all_checks') as mock_health, \
             patch.object(monitor.resource_monitor, 'get_current_metrics') as mock_resource, \
             patch.object(monitor.performance_monitor, 'get_current_metrics') as mock_perf, \
             patch.object(monitor.alert_manager, 'get_active_alerts') as mock_alerts:
            
            mock_health.return_value = [
                HealthCheck("test_check", HealthStatus.HEALTHY, "OK")
            ]
            mock_resource.return_value = ResourceMetrics(cpu_percent=45.0, memory_percent=60.0)
            mock_perf.return_value = PerformanceMetrics(requests_per_second=10.0)
            mock_alerts.return_value = []
            
            status = monitor.get_system_status()
            
            assert status["overall_health"] == "healthy"
            assert "timestamp" in status
            assert "health_checks" in status
            assert "resource_metrics" in status
            assert "performance_metrics" in status
            assert "active_alerts" in status
            assert "alerts" in status
    
    def test_get_system_status_with_critical_health(self):
        """Test system status with critical health checks."""
        monitor = SystemMonitor()
        
        with patch.object(monitor.health_checker, 'run_all_checks') as mock_health, \
             patch.object(monitor.resource_monitor, 'get_current_metrics') as mock_resource, \
             patch.object(monitor.performance_monitor, 'get_current_metrics') as mock_perf, \
             patch.object(monitor.alert_manager, 'get_active_alerts') as mock_alerts:
            
            mock_health.return_value = [
                HealthCheck("critical_check", HealthStatus.CRITICAL, "Critical error")
            ]
            mock_resource.return_value = ResourceMetrics()
            mock_perf.return_value = PerformanceMetrics()
            mock_alerts.return_value = []
            
            status = monitor.get_system_status()
            assert status["overall_health"] == "critical"
    
    def test_get_system_status_with_warning_health(self):
        """Test system status with warning health checks."""
        monitor = SystemMonitor()
        
        with patch.object(monitor.health_checker, 'run_all_checks') as mock_health, \
             patch.object(monitor.resource_monitor, 'get_current_metrics') as mock_resource, \
             patch.object(monitor.performance_monitor, 'get_current_metrics') as mock_perf, \
             patch.object(monitor.alert_manager, 'get_active_alerts') as mock_alerts:
            
            mock_health.return_value = [
                HealthCheck("warning_check", HealthStatus.WARNING, "Warning")
            ]
            mock_resource.return_value = ResourceMetrics()
            mock_perf.return_value = PerformanceMetrics()
            mock_alerts.return_value = []
            
            status = monitor.get_system_status()
            assert status["overall_health"] == "warning"
    
    def test_alert_handler_integration(self):
        """Test alert handler integration."""
        monitor = SystemMonitor()
        
        # Add a mock alert handler
        mock_handler = Mock()
        monitor.alert_manager.add_alert_handler(mock_handler)
        
        # Create an alert
        alert = monitor.alert_manager.create_alert(
            AlertLevel.WARNING,
            "Test Alert",
            "Test message"
        )
        
        # Verify handler was called
        mock_handler.assert_called_once_with(alert)

class TestSystemMonitoringIntegration:
    """Integration tests for system monitoring."""
    
    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        monitor = SystemMonitor(check_interval=0.1)  # Fast interval for testing
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Let it run for a short time
        time.sleep(0.2)
        
        # Get system status
        status = monitor.get_system_status()
        
        # Verify status structure
        assert "overall_health" in status
        assert "timestamp" in status
        assert "health_checks" in status
        assert "resource_metrics" in status
        assert "performance_metrics" in status
        assert "active_alerts" in status
        
        # Stop monitoring
        monitor.stop_monitoring()
    
    def test_monitoring_with_high_cpu_alert(self):
        """Test monitoring with high CPU alert."""
        monitor = SystemMonitor()
        
        # Create high CPU metrics
        metrics = ResourceMetrics(cpu_percent=95.0)
        performance = PerformanceMetrics()
        
        # Check thresholds
        monitor.alert_manager.check_thresholds(metrics, performance)
        
        # Verify alert was created
        assert len(monitor.alert_manager.alerts) == 1
        alert = monitor.alert_manager.alerts[0]
        assert alert.level == AlertLevel.CRITICAL
        assert "CPU" in alert.title
    
    def test_monitoring_with_multiple_alerts(self):
        """Test monitoring with multiple alerts."""
        monitor = SystemMonitor()
        
        # Create multiple alert conditions
        metrics = ResourceMetrics(
            cpu_percent=95.0,
            memory_percent=98.0,
            disk_usage_percent=98.0
        )
        performance = PerformanceMetrics(error_rate=15.0)
        
        # Check thresholds
        monitor.alert_manager.check_thresholds(metrics, performance)
        
        # Verify multiple alerts were created
        assert len(monitor.alert_manager.alerts) == 4  # CPU, Memory, Disk, Error Rate
        
        # Verify alert levels
        alert_levels = [alert.level for alert in monitor.alert_manager.alerts]
        assert AlertLevel.CRITICAL in alert_levels
    
    def test_alert_resolution_workflow(self):
        """Test alert resolution workflow."""
        monitor = SystemMonitor()
        
        # Create an alert
        alert = monitor.alert_manager.create_alert(
            AlertLevel.WARNING,
            "Test Alert",
            "Test message"
        )
        
        # Verify alert is active
        active_alerts = monitor.alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert alert in active_alerts
        
        # Resolve alert
        monitor.alert_manager.resolve_alert(alert.alert_id)
        
        # Verify alert is resolved
        active_alerts = monitor.alert_manager.get_active_alerts()
        assert len(active_alerts) == 0
        assert alert.resolved is True
        assert alert.resolved_at is not None
