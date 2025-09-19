"""
Performance Tests for Receipt Processor

This module contains performance and load tests to ensure the system
can handle expected workloads efficiently.
"""

import pytest
import time
import tempfile
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

from src.receipt_processor.cli import cli
from src.receipt_processor.models import ProcessingStatus, ProcessingLog
from src.receipt_processor.concurrent_processor import ConcurrentProcessor, ProcessingJob, ProcessingPriority
from src.receipt_processor.system_monitoring import SystemMonitor, ResourceMonitor, PerformanceMonitor
from src.receipt_processor.error_handling import ErrorHandler

class TestProcessingPerformance:
    """Performance tests for receipt processing."""
    
    @pytest.mark.performance
    @patch('src.receipt_processor.cli.AIVisionService')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_single_image_processing_performance(self, mock_storage, mock_file, mock_ai):
        """Test performance of single image processing."""
        # Setup mocks
        mock_ai.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [],
            "confidence_score": 0.95
        }
        
        mock_file.return_value.rename_file.return_value = True
        mock_storage.return_value.save_log.return_value = True
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image file
            test_image = Path(temp_dir) / "receipt.jpg"
            test_image.write_bytes(b"fake image data")
            
            # Measure processing time
            start_time = time.time()
            result = runner.invoke(cli, ['process', str(temp_dir)])
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            assert result.exit_code == 0
            assert processing_time < 5.0  # Should complete within 5 seconds
            print(f"Single image processing time: {processing_time:.2f} seconds")
    
    @pytest.mark.performance
    @patch('src.receipt_processor.cli.AIVisionService')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_batch_processing_performance(self, mock_storage, mock_file, mock_ai):
        """Test performance of batch image processing."""
        # Setup mocks
        mock_ai.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [],
            "confidence_score": 0.95
        }
        
        mock_file.return_value.rename_file.return_value = True
        mock_storage.return_value.save_log.return_value = True
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test image files
            num_images = 50
            for i in range(num_images):
                test_image = Path(temp_dir) / f"receipt_{i}.jpg"
                test_image.write_bytes(b"fake image data")
            
            # Measure batch processing time
            start_time = time.time()
            result = runner.invoke(cli, ['process', str(temp_dir), '--batch-size', '10'])
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = num_images / processing_time
            
            assert result.exit_code == 0
            assert processing_time < 30.0  # Should complete within 30 seconds
            assert throughput > 1.0  # Should process at least 1 image per second
            print(f"Batch processing time: {processing_time:.2f} seconds")
            print(f"Throughput: {throughput:.2f} images/second")
    
    @pytest.mark.performance
    @patch('src.receipt_processor.cli.AIVisionService')
    @patch('src.receipt_processor.cli.FileManager')
    @patch('src.receipt_processor.cli.JSONStorageManager')
    def test_concurrent_processing_performance(self, mock_storage, mock_file, mock_ai):
        """Test performance of concurrent processing."""
        # Setup mocks
        mock_ai.return_value.extract_receipt_data.return_value = {
            "vendor_name": "Test Restaurant",
            "date": "2024-01-15",
            "total_amount": 25.50,
            "currency": "USD",
            "items": [],
            "confidence_score": 0.95
        }
        
        mock_file.return_value.rename_file.return_value = True
        mock_storage.return_value.save_log.return_value = True
        mock_storage.return_value.load_logs.return_value = []
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test image files
            num_images = 100
            for i in range(num_images):
                test_image = Path(temp_dir) / f"receipt_{i}.jpg"
                test_image.write_bytes(b"fake image data")
            
            # Measure concurrent processing time
            start_time = time.time()
            result = runner.invoke(cli, [
                'process-concurrent',
                '--input-dir', temp_dir,
                '--max-workers', '8',
                '--memory-limit', '1024',
                '--cpu-limit', '80.0'
            ])
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = num_images / processing_time
            
            assert result.exit_code == 0
            assert processing_time < 60.0  # Should complete within 60 seconds
            assert throughput > 2.0  # Should process at least 2 images per second
            print(f"Concurrent processing time: {processing_time:.2f} seconds")
            print(f"Throughput: {throughput:.2f} images/second")

class TestMemoryPerformance:
    """Memory performance tests."""
    
    @pytest.mark.performance
    def test_memory_usage_during_processing(self):
        """Test memory usage during processing."""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a large number of processing logs
        logs = []
        for i in range(1000):
            log = ProcessingLog(
                log_id=f"LOG_{i:06d}",
                file_path=f"/test/receipt_{i}.jpg",
                original_filename=f"receipt_{i}.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name=f"Restaurant {i % 10}",
                date=datetime(2024, 1, 15),
                total_amount=25.50 + i,
                currency="USD",
                confidence_score=0.95
            )
            logs.append(log)
        
        # Get memory usage after creating logs
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 1000 logs)
        assert memory_increase < 100.0
        print(f"Memory increase for 1000 logs: {memory_increase:.2f} MB")
    
    @pytest.mark.performance
    def test_memory_cleanup_after_processing(self):
        """Test memory cleanup after processing."""
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and process logs
        logs = []
        for i in range(500):
            log = ProcessingLog(
                log_id=f"LOG_{i:06d}",
                file_path=f"/test/receipt_{i}.jpg",
                original_filename=f"receipt_{i}.jpg",
                status=ProcessingStatus.COMPLETED,
                vendor_name=f"Restaurant {i % 10}",
                date=datetime(2024, 1, 15),
                total_amount=25.50 + i,
                currency="USD",
                confidence_score=0.95
            )
            logs.append(log)
        
        # Clear logs and force garbage collection
        del logs
        gc.collect()
        
        # Get memory usage after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_cleanup = initial_memory - final_memory
        
        # Memory should be cleaned up (allow for some variance)
        assert memory_cleanup > -10.0  # Allow 10MB variance
        print(f"Memory cleanup: {memory_cleanup:.2f} MB")

class TestConcurrentProcessingPerformance:
    """Performance tests for concurrent processing system."""
    
    @pytest.mark.performance
    def test_concurrent_processor_throughput(self):
        """Test concurrent processor throughput."""
        processor = ConcurrentProcessor(max_workers=4)
        processor.start()
        
        try:
            # Create test jobs
            num_jobs = 100
            jobs = []
            for i in range(num_jobs):
                job = ProcessingJob(
                    job_id=f"job_{i}",
                    file_path=Path(f"/test/receipt_{i}.jpg"),
                    priority=ProcessingPriority.NORMAL
                )
                jobs.append(job)
            
            # Submit jobs and measure time
            start_time = time.time()
            for job in jobs:
                processor.submit_job(job)
            
            # Wait for completion
            while processor.priority_queue.size() > 0 or len(processor.active_jobs) > 0:
                time.sleep(0.1)
            
            end_time = time.time()
            processing_time = end_time - start_time
            throughput = num_jobs / processing_time
            
            assert processing_time < 30.0  # Should complete within 30 seconds
            assert throughput > 3.0  # Should process at least 3 jobs per second
            print(f"Concurrent processor throughput: {throughput:.2f} jobs/second")
            
        finally:
            processor.stop()
    
    @pytest.mark.performance
    def test_concurrent_processor_resource_usage(self):
        """Test concurrent processor resource usage."""
        processor = ConcurrentProcessor(max_workers=8)
        processor.start()
        
        try:
            # Monitor resource usage during processing
            process = psutil.Process()
            initial_cpu = process.cpu_percent()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create and submit jobs
            num_jobs = 50
            for i in range(num_jobs):
                job = ProcessingJob(
                    job_id=f"job_{i}",
                    file_path=Path(f"/test/receipt_{i}.jpg"),
                    priority=ProcessingPriority.NORMAL
                )
                processor.submit_job(job)
            
            # Wait for completion
            while processor.priority_queue.size() > 0 or len(processor.active_jobs) > 0:
                time.sleep(0.1)
            
            # Check final resource usage
            final_cpu = process.cpu_percent()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_increase = final_memory - initial_memory
            
            # Resource usage should be reasonable
            assert memory_increase < 200.0  # Less than 200MB increase
            print(f"Memory increase: {memory_increase:.2f} MB")
            print(f"CPU usage: {final_cpu:.1f}%")
            
        finally:
            processor.stop()

class TestSystemMonitoringPerformance:
    """Performance tests for system monitoring."""
    
    @pytest.mark.performance
    def test_resource_monitor_performance(self):
        """Test resource monitor performance."""
        monitor = ResourceMonitor(check_interval=0.1)
        monitor.start_monitoring()
        
        try:
            # Let it run for a short time
            time.sleep(1.0)
            
            # Check that metrics are being collected
            metrics = monitor.get_current_metrics()
            assert metrics.cpu_percent >= 0.0
            assert metrics.memory_percent >= 0.0
            assert metrics.disk_usage_percent >= 0.0
            
            # Check metrics history
            history = monitor.get_metrics_history(duration_minutes=1)
            assert len(history) > 0
            
            print(f"Collected {len(history)} metrics in 1 second")
            
        finally:
            monitor.stop_monitoring()
    
    @pytest.mark.performance
    def test_performance_monitor_throughput(self):
        """Test performance monitor throughput."""
        monitor = PerformanceMonitor()
        
        # Simulate high request volume
        num_requests = 1000
        start_time = time.time()
        
        for i in range(num_requests):
            response_time = 0.1 + (i % 10) * 0.01  # Vary response time
            success = i % 20 != 0  # 95% success rate
            monitor.record_request(response_time, success)
        
        end_time = time.time()
        processing_time = end_time - start_time
        throughput = num_requests / processing_time
        
        # Check metrics
        metrics = monitor.get_current_metrics()
        assert metrics.requests_per_second > 0
        assert metrics.average_response_time > 0
        assert metrics.error_rate >= 0
        
        print(f"Performance monitor throughput: {throughput:.2f} requests/second")
        print(f"Average response time: {metrics.average_response_time:.3f} seconds")
        print(f"Error rate: {metrics.error_rate:.1f}%")
    
    @pytest.mark.performance
    def test_health_checker_performance(self):
        """Test health checker performance."""
        from src.receipt_processor.system_monitoring import HealthChecker
        
        checker = HealthChecker()
        
        # Measure health check execution time
        start_time = time.time()
        results = checker.run_all_checks()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Health checks should complete quickly
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(results) > 0  # Should have some results
        
        print(f"Health check execution time: {execution_time:.3f} seconds")
        print(f"Number of health checks: {len(results)}")

class TestErrorHandlingPerformance:
    """Performance tests for error handling system."""
    
    @pytest.mark.performance
    def test_error_handler_throughput(self):
        """Test error handler throughput."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = ErrorHandler(log_file=Path(temp_dir) / "error_log.json")
            
            # Simulate high error volume
            num_errors = 1000
            start_time = time.time()
            
            for i in range(num_errors):
                error = Exception(f"Test error {i}")
                handler.handle_error(error)
            
            end_time = time.time()
            processing_time = end_time - start_time
            throughput = num_errors / processing_time
            
            # Error handling should be fast
            assert processing_time < 10.0  # Should complete within 10 seconds
            assert throughput > 100.0  # Should handle at least 100 errors per second
            
            print(f"Error handler throughput: {throughput:.2f} errors/second")
            
            # Check error history
            assert len(handler.error_history) == num_errors
    
    @pytest.mark.performance
    def test_error_recovery_performance(self):
        """Test error recovery performance."""
        from src.receipt_processor.error_handling import ErrorRecoveryManager, ErrorInfo, ErrorCategory, ErrorSeverity
        
        recovery_manager = ErrorRecoveryManager()
        
        # Create test error info
        error_info = ErrorInfo(
            error_id="ERR_001",
            exception_type="StorageError",
            error_message="Storage failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.STORAGE_ERROR,
            context=None,
            stack_trace="",
            retry_count=0,
            max_retries=3
        )
        
        # Measure recovery attempt time
        start_time = time.time()
        result = recovery_manager.attempt_recovery(error_info)
        end_time = time.time()
        
        recovery_time = end_time - start_time
        
        # Recovery should be fast
        assert recovery_time < 1.0  # Should complete within 1 second
        print(f"Error recovery time: {recovery_time:.3f} seconds")

class TestLoadTesting:
    """Load testing for the system."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_high_load_processing(self):
        """Test system under high load."""
        # This test simulates high load conditions
        num_threads = 10
        requests_per_thread = 100
        
        def worker_thread(thread_id):
            """Worker thread for load testing."""
            results = []
            for i in range(requests_per_thread):
                start_time = time.time()
                
                # Simulate processing work
                time.sleep(0.01)  # 10ms processing time
                
                end_time = time.time()
                results.append(end_time - start_time)
            
            return results
        
        # Run load test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            all_results = []
            
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        total_requests = num_threads * requests_per_thread
        throughput = total_requests / total_time
        average_response_time = sum(all_results) / len(all_results)
        
        # System should handle load gracefully
        assert total_time < 30.0  # Should complete within 30 seconds
        assert throughput > 50.0  # Should handle at least 50 requests per second
        assert average_response_time < 0.1  # Average response time should be reasonable
        
        print(f"Load test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Average response time: {average_response_time:.3f} seconds")
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_under_load(self):
        """Test memory usage under load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of objects
        objects = []
        for i in range(10000):
            obj = {
                "id": i,
                "data": "x" * 1000,  # 1KB of data per object
                "timestamp": datetime.now()
            }
            objects.append(obj)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 500.0  # Less than 500MB increase
        print(f"Memory increase under load: {memory_increase:.2f} MB")
        
        # Clean up
        del objects
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_cleanup = peak_memory - final_memory
        print(f"Memory cleanup: {memory_cleanup:.2f} MB")

class TestScalability:
    """Scalability tests for the system."""
    
    @pytest.mark.performance
    def test_concurrent_worker_scalability(self):
        """Test scalability with different numbers of workers."""
        worker_counts = [1, 2, 4, 8]
        num_jobs = 100
        
        results = {}
        
        for worker_count in worker_counts:
            processor = ConcurrentProcessor(max_workers=worker_count)
            processor.start()
            
            try:
                # Create jobs
                jobs = []
                for i in range(num_jobs):
                    job = ProcessingJob(
                        job_id=f"job_{i}",
                        file_path=Path(f"/test/receipt_{i}.jpg"),
                        priority=ProcessingPriority.NORMAL
                    )
                    jobs.append(job)
                
                # Submit jobs and measure time
                start_time = time.time()
                for job in jobs:
                    processor.submit_job(job)
                
                # Wait for completion
                while processor.priority_queue.size() > 0 or len(processor.active_jobs) > 0:
                    time.sleep(0.1)
                
                end_time = time.time()
                processing_time = end_time - start_time
                throughput = num_jobs / processing_time
                
                results[worker_count] = {
                    "processing_time": processing_time,
                    "throughput": throughput
                }
                
                print(f"Workers: {worker_count}, Time: {processing_time:.2f}s, Throughput: {throughput:.2f} jobs/s")
                
            finally:
                processor.stop()
        
        # Throughput should generally increase with more workers (up to a point)
        assert results[2]["throughput"] > results[1]["throughput"]
        assert results[4]["throughput"] > results[2]["throughput"]
    
    @pytest.mark.performance
    def test_batch_size_scalability(self):
        """Test scalability with different batch sizes."""
        batch_sizes = [1, 5, 10, 20, 50]
        total_images = 100
        
        results = {}
        
        for batch_size in batch_sizes:
            # Simulate batch processing
            start_time = time.time()
            
            for i in range(0, total_images, batch_size):
                # Simulate processing batch
                time.sleep(0.01 * batch_size)  # Processing time proportional to batch size
            
            end_time = time.time()
            processing_time = end_time - start_time
            throughput = total_images / processing_time
            
            results[batch_size] = {
                "processing_time": processing_time,
                "throughput": throughput
            }
            
            print(f"Batch size: {batch_size}, Time: {processing_time:.2f}s, Throughput: {throughput:.2f} images/s")
        
        # Larger batch sizes should generally be more efficient
        assert results[10]["throughput"] > results[1]["throughput"]
        assert results[20]["throughput"] > results[5]["throughput"]
