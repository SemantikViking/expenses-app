"""
Payment Tracking Storage and Persistence System.

This module provides comprehensive storage management for payment tracking,
including CRUD operations, querying, reporting, and data integrity.
"""

import json
import hashlib
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from decimal import Decimal
import logging

from .payment_models import (
    PaymentTrackingLog, PaymentBatch, PaymentReport, PaymentStatus,
    PaymentMethod, PaymentType, ApprovalStatus, ReconciliationStatus
)
from .models import ReceiptProcessingLog

logger = logging.getLogger(__name__)


class PaymentStorageManager:
    """Manages payment tracking data storage and persistence."""
    
    def __init__(self, storage_file: Path, backup_dir: Path):
        self.storage_file = storage_file
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize payment storage file."""
        if not self.storage_file.exists():
            initial_data = {
                "payments": {},
                "batches": {},
                "reports": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "total_payments": 0,
                    "total_batches": 0,
                    "total_reports": 0
                }
            }
            self._save_data(initial_data)
            logger.info(f"Initialized payment storage: {self.storage_file}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load payment data from storage file."""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert payment data back to PaymentTrackingLog objects
            payments = {}
            for payment_id, payment_data in data.get("payments", {}).items():
                try:
                    # Convert datetime strings back to datetime objects
                    payment_data = self._deserialize_payment_data(payment_data)
                    payments[payment_id] = PaymentTrackingLog(**payment_data)
                except Exception as e:
                    logger.error(f"Error deserializing payment {payment_id}: {e}")
                    continue
            
            data["payments"] = payments
            return data
            
        except Exception as e:
            logger.error(f"Error loading payment data: {e}")
            return {"payments": {}, "batches": {}, "reports": {}, "metadata": {}}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save payment data to storage file."""
        try:
            # Create backup before saving
            self._create_backup()
            
            # Convert PaymentTrackingLog objects to serializable format
            serializable_data = data.copy()
            payments = {}
            
            for payment_id, payment in data.get("payments", {}).items():
                if isinstance(payment, PaymentTrackingLog):
                    payments[payment_id] = self._serialize_payment_data(payment)
                else:
                    payments[payment_id] = payment
            
            serializable_data["payments"] = payments
            
            # Update metadata
            serializable_data["metadata"]["last_updated"] = datetime.now().isoformat()
            serializable_data["metadata"]["total_payments"] = len(payments)
            serializable_data["metadata"]["total_batches"] = len(data.get("batches", {}))
            serializable_data["metadata"]["total_reports"] = len(data.get("reports", {}))
            
            # Write to temporary file first
            temp_file = self.storage_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, default=str)
            
            # Atomic move
            shutil.move(str(temp_file), str(self.storage_file))
            
            logger.debug(f"Payment data saved successfully: {self.storage_file}")
            
        except Exception as e:
            logger.error(f"Error saving payment data: {e}")
            raise
    
    def _serialize_payment_data(self, payment: PaymentTrackingLog) -> Dict[str, Any]:
        """Serialize PaymentTrackingLog to dictionary."""
        return payment.model_dump()
    
    def _deserialize_payment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize payment data from dictionary."""
        # Convert datetime strings back to datetime objects
        datetime_fields = [
            'created_at', 'submitted_at', 'approved_at', 'disbursed_at', 'received_at'
        ]
        
        for field in datetime_fields:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        # Convert date strings back to date objects
        date_fields = ['due_date', 'retention_date']
        for field in date_fields:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = date.fromisoformat(data[field])
        
        # Convert Decimal strings back to Decimal objects
        decimal_fields = [
            'amount', 'processing_fee', 'tax_amount', 'net_amount'
        ]
        for field in decimal_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], (str, float)):
                    data[field] = Decimal(str(data[field]))
        
        return data
    
    def _create_backup(self):
        """Create backup of current storage file."""
        if self.storage_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"payment_storage_backup_{timestamp}.json"
            shutil.copy2(self.storage_file, backup_file)
            logger.debug(f"Backup created: {backup_file}")
    
    def _verify_file_integrity(self) -> bool:
        """Verify file integrity using hash."""
        try:
            if not self.storage_file.exists():
                return True  # No file to verify
            
            # Calculate file hash
            with open(self.storage_file, 'rb') as f:
                file_hash = hashlib.sha224(f.read()).hexdigest()
            
            # Load data to check stored hash
            data = self._load_data()
            stored_hash = data.get("metadata", {}).get("file_hash")
            
            if stored_hash is None:
                # No stored hash, update it
                data["metadata"]["file_hash"] = file_hash
                self._save_data(data)
                return True
            
            # Compare hashes
            return file_hash == stored_hash
            
        except Exception as e:
            logger.error(f"File integrity verification failed: {e}")
            return False
    
    def add_payment(self, payment: PaymentTrackingLog) -> bool:
        """Add a new payment to storage."""
        try:
            data = self._load_data()
            data["payments"][payment.payment_id] = payment
            self._save_data(data)
            
            logger.info(f"Payment added: {payment.payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding payment {payment.payment_id}: {e}")
            return False
    
    def update_payment(self, payment: PaymentTrackingLog) -> bool:
        """Update an existing payment."""
        try:
            data = self._load_data()
            if payment.payment_id not in data["payments"]:
                logger.warning(f"Payment not found for update: {payment.payment_id}")
                return False
            
            data["payments"][payment.payment_id] = payment
            self._save_data(data)
            
            logger.info(f"Payment updated: {payment.payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating payment {payment.payment_id}: {e}")
            return False
    
    def get_payment(self, payment_id: str) -> Optional[PaymentTrackingLog]:
        """Get payment by ID."""
        try:
            data = self._load_data()
            return data["payments"].get(payment_id)
            
        except Exception as e:
            logger.error(f"Error getting payment {payment_id}: {e}")
            return None
    
    def delete_payment(self, payment_id: str) -> bool:
        """Delete a payment."""
        try:
            data = self._load_data()
            if payment_id not in data["payments"]:
                logger.warning(f"Payment not found for deletion: {payment_id}")
                return False
            
            del data["payments"][payment_id]
            self._save_data(data)
            
            logger.info(f"Payment deleted: {payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting payment {payment_id}: {e}")
            return False
    
    def get_payments_by_status(self, status: PaymentStatus) -> List[PaymentTrackingLog]:
        """Get payments by status."""
        try:
            data = self._load_data()
            return [
                payment for payment in data["payments"].values()
                if payment.current_status == status
            ]
            
        except Exception as e:
            logger.error(f"Error getting payments by status {status}: {e}")
            return []
    
    def get_payments_by_recipient(self, recipient_email: str) -> List[PaymentTrackingLog]:
        """Get payments by recipient email."""
        try:
            data = self._load_data()
            return [
                payment for payment in data["payments"].values()
                if payment.recipient.email == recipient_email
            ]
            
        except Exception as e:
            logger.error(f"Error getting payments by recipient {recipient_email}: {e}")
            return []
    
    def get_payments_by_date_range(self, start_date: date, end_date: date) -> List[PaymentTrackingLog]:
        """Get payments within date range."""
        try:
            data = self._load_data()
            payments = []
            
            for payment in data["payments"].values():
                payment_date = payment.created_at.date()
                if start_date <= payment_date <= end_date:
                    payments.append(payment)
            
            return payments
            
        except Exception as e:
            logger.error(f"Error getting payments by date range: {e}")
            return []
    
    def get_payments_by_amount_range(self, min_amount: Decimal, max_amount: Decimal) -> List[PaymentTrackingLog]:
        """Get payments within amount range."""
        try:
            data = self._load_data()
            return [
                payment for payment in data["payments"].values()
                if min_amount <= payment.amount <= max_amount
            ]
            
        except Exception as e:
            logger.error(f"Error getting payments by amount range: {e}")
            return []
    
    def get_overdue_payments(self) -> List[PaymentTrackingLog]:
        """Get overdue payments."""
        try:
            data = self._load_data()
            overdue_payments = []
            
            for payment in data["payments"].values():
                if payment.is_overdue():
                    overdue_payments.append(payment)
            
            return overdue_payments
            
        except Exception as e:
            logger.error(f"Error getting overdue payments: {e}")
            return []
    
    def get_payments_requiring_approval(self) -> List[PaymentTrackingLog]:
        """Get payments requiring approval."""
        try:
            data = self._load_data()
            return [
                payment for payment in data["payments"].values()
                if payment.requires_approval()
            ]
            
        except Exception as e:
            logger.error(f"Error getting payments requiring approval: {e}")
            return []
    
    def get_payments_ready_for_disbursement(self) -> List[PaymentTrackingLog]:
        """Get payments ready for disbursement."""
        try:
            data = self._load_data()
            return [
                payment for payment in data["payments"].values()
                if payment.is_ready_for_disbursement()
            ]
            
        except Exception as e:
            logger.error(f"Error getting payments ready for disbursement: {e}")
            return []
    
    def search_payments(self, query: str, fields: List[str] = None) -> List[PaymentTrackingLog]:
        """Search payments by query string."""
        try:
            data = self._load_data()
            results = []
            query_lower = query.lower()
            
            default_fields = [
                'payment_id', 'description', 'recipient.name', 'recipient.email',
                'business_purpose', 'reference_number', 'notes'
            ]
            search_fields = fields or default_fields
            
            for payment in data["payments"].values():
                for field in search_fields:
                    value = self._get_nested_value(payment, field)
                    if value and query_lower in str(value).lower():
                        results.append(payment)
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching payments: {e}")
            return []
    
    def _get_nested_value(self, obj: Any, field_path: str) -> Any:
        """Get nested value from object using dot notation."""
        try:
            for field in field_path.split('.'):
                if hasattr(obj, field):
                    obj = getattr(obj, field)
                elif isinstance(obj, dict) and field in obj:
                    obj = obj[field]
                else:
                    return None
            return obj
        except:
            return None
    
    def get_payment_statistics(self) -> Dict[str, Any]:
        """Get payment statistics."""
        try:
            data = self._load_data()
            payments = data["payments"]
            
            if not payments:
                return {
                    "total_payments": 0,
                    "total_amount": 0.0,
                    "status_breakdown": {},
                    "method_breakdown": {},
                    "type_breakdown": {},
                    "approval_breakdown": {}
                }
            
            # Calculate statistics
            total_amount = sum(payment.amount for payment in payments.values())
            
            status_breakdown = {}
            method_breakdown = {}
            type_breakdown = {}
            approval_breakdown = {}
            
            for payment in payments.values():
                # Status breakdown
                status = payment.current_status.value if hasattr(payment.current_status, 'value') else str(payment.current_status)
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Method breakdown
                method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
                method_breakdown[method] = method_breakdown.get(method, 0) + 1
                
                # Type breakdown
                payment_type = payment.payment_type.value if hasattr(payment.payment_type, 'value') else str(payment.payment_type)
                type_breakdown[payment_type] = type_breakdown.get(payment_type, 0) + 1
                
                # Approval breakdown
                approval = payment.approval_status.value if hasattr(payment.approval_status, 'value') else str(payment.approval_status)
                approval_breakdown[approval] = approval_breakdown.get(approval, 0) + 1
            
            return {
                "total_payments": len(payments),
                "total_amount": float(total_amount),
                "status_breakdown": status_breakdown,
                "method_breakdown": method_breakdown,
                "type_breakdown": type_breakdown,
                "approval_breakdown": approval_breakdown,
                "overdue_count": len(self.get_overdue_payments()),
                "pending_approval_count": len(self.get_payments_requiring_approval()),
                "ready_for_disbursement_count": len(self.get_payments_ready_for_disbursement())
            }
            
        except Exception as e:
            logger.error(f"Error calculating payment statistics: {e}")
            return {}
    
    def cleanup_old_payments(self, retention_days: int = 365) -> int:
        """Clean up old payments based on retention policy."""
        try:
            data = self._load_data()
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            payments_to_remove = []
            for payment_id, payment in data["payments"].items():
                if payment.created_at < cutoff_date:
                    payments_to_remove.append(payment_id)
            
            for payment_id in payments_to_remove:
                del data["payments"][payment_id]
            
            if payments_to_remove:
                self._save_data(data)
                logger.info(f"Cleaned up {len(payments_to_remove)} old payments")
            
            return len(payments_to_remove)
            
        except Exception as e:
            logger.error(f"Error cleaning up old payments: {e}")
            return 0
    
    def export_payments(self, file_path: Path, format: str = "json") -> bool:
        """Export payments to file."""
        try:
            data = self._load_data()
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            
            elif format.lower() == "csv":
                self._export_to_csv(data, file_path)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Payments exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting payments: {e}")
            return False
    
    def _export_to_csv(self, data: Dict[str, Any], file_path: Path):
        """Export payments to CSV format."""
        import csv
        
        payments = data.get("payments", {})
        if not payments:
            return
        
        # Get all field names from first payment
        first_payment = list(payments.values())[0]
        fieldnames = self._get_payment_fieldnames(first_payment)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for payment in payments.values():
                row = self._payment_to_csv_row(payment)
                writer.writerow(row)
    
    def _get_payment_fieldnames(self, payment: PaymentTrackingLog) -> List[str]:
        """Get field names for CSV export."""
        return [
            'payment_id', 'amount', 'currency', 'payment_type', 'payment_method',
            'current_status', 'approval_status', 'recipient_name', 'recipient_email',
            'created_at', 'submitted_at', 'approved_at', 'disbursed_at',
            'department', 'project_code', 'business_purpose', 'description'
        ]
    
    def _payment_to_csv_row(self, payment: PaymentTrackingLog) -> Dict[str, Any]:
        """Convert payment to CSV row."""
        return {
            'payment_id': payment.payment_id,
            'amount': float(payment.amount),
            'currency': payment.currency.value if hasattr(payment.currency, 'value') else str(payment.currency),
            'payment_type': payment.payment_type.value if hasattr(payment.payment_type, 'value') else str(payment.payment_type),
            'payment_method': payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method),
            'current_status': payment.current_status.value if hasattr(payment.current_status, 'value') else str(payment.current_status),
            'approval_status': payment.approval_status.value if hasattr(payment.approval_status, 'value') else str(payment.approval_status),
            'recipient_name': payment.recipient.name,
            'recipient_email': payment.recipient.email,
            'created_at': payment.created_at.isoformat() if payment.created_at else '',
            'submitted_at': payment.submitted_at.isoformat() if payment.submitted_at else '',
            'approved_at': payment.approved_at.isoformat() if payment.approved_at else '',
            'disbursed_at': payment.disbursed_at.isoformat() if payment.disbursed_at else '',
            'department': payment.department or '',
            'project_code': payment.project_code or '',
            'business_purpose': payment.business_purpose or '',
            'description': payment.description or ''
        }
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information and health status."""
        try:
            data = self._load_data()
            file_size = self.storage_file.stat().st_size if self.storage_file.exists() else 0
            
            return {
                "storage_file": str(self.storage_file),
                "backup_dir": str(self.backup_dir),
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "total_payments": len(data.get("payments", {})),
                "total_batches": len(data.get("batches", {})),
                "total_reports": len(data.get("reports", {})),
                "last_updated": data.get("metadata", {}).get("last_updated"),
                "version": data.get("metadata", {}).get("version"),
                "file_exists": self.storage_file.exists(),
                "backup_count": len(list(self.backup_dir.glob("*.json"))) if self.backup_dir.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {}


class PaymentBatchManager:
    """Manages payment batches for bulk operations."""
    
    def __init__(self, storage_manager: PaymentStorageManager):
        self.storage_manager = storage_manager
    
    def create_batch(self, batch_name: str, payment_ids: List[str], created_by: str) -> Optional[PaymentBatch]:
        """Create a new payment batch."""
        try:
            # Validate payment IDs exist
            valid_payment_ids = []
            total_amount = Decimal('0')
            
            for payment_id in payment_ids:
                payment = self.storage_manager.get_payment(payment_id)
                if payment:
                    valid_payment_ids.append(payment_id)
                    total_amount += payment.amount
                else:
                    logger.warning(f"Payment not found for batch: {payment_id}")
            
            if not valid_payment_ids:
                logger.error("No valid payments found for batch")
                return None
            
            # Create batch
            batch = PaymentBatch(
                batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                batch_name=batch_name,
                payment_ids=valid_payment_ids,
                total_amount=total_amount,
                created_by=created_by
            )
            
            # Save batch
            data = self.storage_manager._load_data()
            data["batches"][batch.batch_id] = batch.model_dump()
            self.storage_manager._save_data(data)
            
            logger.info(f"Payment batch created: {batch.batch_id}")
            return batch
            
        except Exception as e:
            logger.error(f"Error creating payment batch: {e}")
            return None
    
    def get_batch(self, batch_id: str) -> Optional[PaymentBatch]:
        """Get payment batch by ID."""
        try:
            data = self.storage_manager._load_data()
            batch_data = data.get("batches", {}).get(batch_id)
            if batch_data:
                return PaymentBatch(**batch_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting batch {batch_id}: {e}")
            return None
    
    def update_batch_status(self, batch_id: str, status: PaymentStatus, 
                           error_count: int = 0, success_count: int = 0) -> bool:
        """Update batch status and metrics."""
        try:
            data = self.storage_manager._load_data()
            batch_data = data.get("batches", {}).get(batch_id)
            
            if not batch_data:
                logger.warning(f"Batch not found: {batch_id}")
                return False
            
            batch = PaymentBatch(**batch_data)
            batch.batch_status = status
            batch.error_count = error_count
            batch.success_count = success_count
            
            if status in [PaymentStatus.DISBURSED, PaymentStatus.RECEIVED]:
                batch.processed_at = datetime.now()
            
            data["batches"][batch_id] = batch.model_dump()
            self.storage_manager._save_data(data)
            
            logger.info(f"Batch status updated: {batch_id} -> {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating batch status: {e}")
            return False
    
    def get_batch_payments(self, batch_id: str) -> List[PaymentTrackingLog]:
        """Get payments in a batch."""
        try:
            batch = self.get_batch(batch_id)
            if not batch:
                return []
            
            payments = []
            for payment_id in batch.payment_ids:
                payment = self.storage_manager.get_payment(payment_id)
                if payment:
                    payments.append(payment)
            
            return payments
            
        except Exception as e:
            logger.error(f"Error getting batch payments: {e}")
            return []
    
    def get_all_batches(self) -> List[PaymentBatch]:
        """Get all payment batches."""
        try:
            data = self.storage_manager._load_data()
            batches = []
            
            for batch_data in data.get("batches", {}).values():
                try:
                    batch = PaymentBatch(**batch_data)
                    batches.append(batch)
                except Exception as e:
                    logger.error(f"Error deserializing batch: {e}")
                    continue
            
            return batches
            
        except Exception as e:
            logger.error(f"Error getting all batches: {e}")
            return []
    
    def delete_batch(self, batch_id: str) -> bool:
        """Delete a payment batch."""
        try:
            data = self.storage_manager._load_data()
            if batch_id not in data.get("batches", {}):
                logger.warning(f"Batch not found for deletion: {batch_id}")
                return False
            
            del data["batches"][batch_id]
            self.storage_manager._save_data(data)
            
            logger.info(f"Batch deleted: {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting batch {batch_id}: {e}")
            return False
