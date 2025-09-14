"""
Data models for Receipt Processing Application.

This module defines Pydantic models for receipt data, processing status,
logging, and all structured data used throughout the application.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """Status values for receipt processing workflow."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"
    NO_DATA_EXTRACTED = "no_data_extracted"
    EMAILED = "emailed"
    SUBMITTED = "submitted"
    PAYMENT_RECEIVED = "payment_received"
    RETRY = "retry"


class Currency(str, Enum):
    """Supported currency codes."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    CHF = "CHF"
    CNY = "CNY"


class ReceiptData(BaseModel):
    """Core receipt data extracted from images."""
    
    # Primary extracted data
    vendor_name: Optional[str] = Field(None, description="Name of the vendor/merchant")
    transaction_date: Optional[datetime] = Field(None, description="Date of the transaction")
    total_amount: Optional[Decimal] = Field(None, description="Total amount of the transaction", ge=0)
    currency: Optional[Currency] = Field(None, description="Currency of the transaction")
    
    # Additional extracted details
    receipt_number: Optional[str] = Field(None, description="Receipt or invoice number")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount if available", ge=0)
    subtotal: Optional[Decimal] = Field(None, description="Subtotal before tax", ge=0)
    
    # Line items (optional detailed extraction)
    line_items: List[Dict[str, Union[str, Decimal, int]]] = Field(
        default_factory=list,
        description="Individual line items from receipt"
    )
    
    # Metadata
    extraction_confidence: float = Field(0.0, description="Confidence score of extraction (0.0-1.0)", ge=0.0, le=1.0)
    extracted_text: Optional[str] = Field(None, description="Raw text extracted from image")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="When extraction was performed")
    
    # Validation flags
    has_required_data: bool = Field(False, description="Whether minimum required data was extracted")
    validation_errors: List[str] = Field(default_factory=list, description="Any validation errors found")
    
    @field_validator('total_amount', 'tax_amount', 'subtotal', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal for precision."""
        if v is None:
            return v
        if isinstance(v, (int, float, str)):
            try:
                return Decimal(str(v))
            except:
                return None
        return v
    
    @model_validator(mode='after')
    def validate_receipt_data(self):
        """Validate receipt data consistency."""
        total = self.total_amount
        subtotal = self.subtotal
        tax = self.tax_amount
        
        # Check if we have minimum required data
        vendor = self.vendor_name
        date = self.transaction_date
        
        has_required = bool(vendor and date and total)
        self.has_required_data = has_required
        
        # Validate amount relationships
        errors = []
        if subtotal and tax and total:
            calculated_total = subtotal + tax
            if abs(calculated_total - total) > Decimal('0.01'):
                errors.append(f"Total amount ({total}) doesn't match subtotal + tax ({calculated_total})")
        
        if total and total <= 0:
            errors.append("Total amount must be greater than zero")
        
        self.validation_errors = errors
        return self
    
    def to_filename_format(self) -> str:
        """Generate a standardized filename based on extracted data."""
        parts = []
        
        # Date component
        if self.transaction_date:
            parts.append(self.transaction_date.strftime("%Y%m%d"))
        else:
            parts.append("NODATE")
        
        # Vendor component (clean for filename)
        if self.vendor_name:
            vendor_clean = "".join(c for c in self.vendor_name if c.isalnum() or c in (' ', '-', '_')).strip()
            vendor_clean = vendor_clean.replace(' ', '_')[:20]  # Limit length
            parts.append(vendor_clean)
        else:
            parts.append("UNKNOWN_VENDOR")
        
        # Amount component
        if self.total_amount:
            currency_symbol = self.currency.value if self.currency else "USD"
            parts.append(f"{currency_symbol}{self.total_amount:.2f}")
        else:
            parts.append("AMOUNT_UNKNOWN")
        
        return "_".join(parts)


class StatusTransition(BaseModel):
    """Represents a status change in the processing workflow."""
    from_status: Optional[ProcessingStatus] = Field(None, description="Previous status")
    to_status: ProcessingStatus = Field(..., description="New status")
    timestamp: datetime = Field(default_factory=datetime.now, description="When transition occurred")
    reason: Optional[str] = Field(None, description="Reason for status change")
    user: Optional[str] = Field(None, description="User who initiated the change")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional transition metadata")


class ReceiptProcessingLog(BaseModel):
    """Complete processing log for a single receipt."""
    
    # Unique identifier
    id: UUID = Field(default_factory=uuid4, description="Unique log entry ID")
    
    # File information
    original_filename: str = Field(..., description="Original filename of the receipt image")
    file_path: Path = Field(..., description="Current path to the receipt file")
    processed_filename: Optional[str] = Field(None, description="Renamed filename after processing")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: Optional[str] = Field(None, description="SHA-256 hash of the file for integrity")
    
    # Processing status and workflow
    current_status: ProcessingStatus = Field(ProcessingStatus.PENDING, description="Current processing status")
    status_history: List[StatusTransition] = Field(default_factory=list, description="History of status changes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="When log entry was created")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    processed_at: Optional[datetime] = Field(None, description="When processing completed")
    
    # Extracted receipt data
    receipt_data: Optional[ReceiptData] = Field(None, description="Extracted receipt information")
    
    # Processing metadata
    processing_attempts: int = Field(0, description="Number of processing attempts")
    last_error: Optional[str] = Field(None, description="Last error message if any")
    ai_model_used: Optional[str] = Field(None, description="AI model used for extraction")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken for processing")
    
    # Email and payment tracking
    email_sent_at: Optional[datetime] = Field(None, description="When receipt was emailed")
    email_recipient: Optional[str] = Field(None, description="Email recipient")
    submitted_for_payment_at: Optional[datetime] = Field(None, description="When submitted for payment")
    payment_received_at: Optional[datetime] = Field(None, description="When payment was received")
    payment_amount: Optional[Decimal] = Field(None, description="Payment amount received")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    
    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    notes: Optional[str] = Field(None, description="User notes")
    confidence_score: Optional[float] = Field(None, description="Overall processing confidence")
    
    def add_status_transition(
        self, 
        new_status: ProcessingStatus, 
        reason: Optional[str] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a new status transition to the log."""
        transition = StatusTransition(
            from_status=self.current_status,
            to_status=new_status,
            reason=reason,
            user=user,
            metadata=metadata or {}
        )
        
        self.status_history.append(transition)
        self.current_status = new_status
        self.last_updated = datetime.now()
        
        # Update specific timestamps based on status
        if new_status == ProcessingStatus.PROCESSED:
            self.processed_at = datetime.now()
        elif new_status == ProcessingStatus.EMAILED:
            self.email_sent_at = datetime.now()
        elif new_status == ProcessingStatus.SUBMITTED:
            self.submitted_for_payment_at = datetime.now()
        elif new_status == ProcessingStatus.PAYMENT_RECEIVED:
            self.payment_received_at = datetime.now()
    
    def get_processing_duration(self) -> Optional[float]:
        """Calculate total processing duration in seconds."""
        if self.processed_at:
            return (self.processed_at - self.created_at).total_seconds()
        return None
    
    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return self.current_status in [
            ProcessingStatus.PROCESSED,
            ProcessingStatus.EMAILED,
            ProcessingStatus.SUBMITTED,
            ProcessingStatus.PAYMENT_RECEIVED
        ]
    
    def get_latest_transition(self) -> Optional[StatusTransition]:
        """Get the most recent status transition."""
        return self.status_history[-1] if self.status_history else None


class ReceiptProcessingLogFile(BaseModel):
    """Container for the entire processing log file."""
    
    version: str = Field("1.0", description="Log file format version")
    created_at: datetime = Field(default_factory=datetime.now, description="When log file was created")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update to log file")
    
    # Processing logs
    logs: List[ReceiptProcessingLog] = Field(default_factory=list, description="All processing logs")
    
    # Statistics
    total_receipts: int = Field(0, description="Total number of receipts processed")
    successful_extractions: int = Field(0, description="Number of successful extractions")
    failed_extractions: int = Field(0, description="Number of failed extractions")
    
    def add_log(self, log: ReceiptProcessingLog):
        """Add a new processing log entry."""
        self.logs.append(log)
        self.total_receipts = len(self.logs)
        self.last_updated = datetime.now()
        self._update_statistics()
    
    def get_log_by_id(self, log_id: UUID) -> Optional[ReceiptProcessingLog]:
        """Get a log entry by its ID."""
        for log in self.logs:
            if log.id == log_id:
                return log
        return None
    
    def get_logs_by_status(self, status: ProcessingStatus) -> List[ReceiptProcessingLog]:
        """Get all logs with a specific status."""
        return [log for log in self.logs if log.current_status == status]
    
    def get_recent_logs(self, limit: int = 10) -> List[ReceiptProcessingLog]:
        """Get the most recent log entries."""
        sorted_logs = sorted(self.logs, key=lambda x: x.created_at, reverse=True)
        return sorted_logs[:limit]
    
    def _update_statistics(self):
        """Update internal statistics."""
        self.successful_extractions = len([
            log for log in self.logs 
            if log.current_status in [
                ProcessingStatus.PROCESSED,
                ProcessingStatus.EMAILED,
                ProcessingStatus.SUBMITTED,
                ProcessingStatus.PAYMENT_RECEIVED
            ]
        ])
        
        self.failed_extractions = len([
            log for log in self.logs 
            if log.current_status in [ProcessingStatus.ERROR, ProcessingStatus.NO_DATA_EXTRACTED]
        ])
    
    def cleanup_old_logs(self, max_age_days: int = 180):
        """Remove logs older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        original_count = len(self.logs)
        self.logs = [log for log in self.logs if log.created_at > cutoff_date]
        
        removed_count = original_count - len(self.logs)
        if removed_count > 0:
            self.total_receipts = len(self.logs)
            self.last_updated = datetime.now()
            self._update_statistics()
            
        return removed_count


class AIExtractionRequest(BaseModel):
    """Request model for AI vision extraction."""
    
    image_path: Path = Field(..., description="Path to the image file")
    image_data: Optional[bytes] = Field(None, description="Raw image data if not using file path")
    
    # Processing options
    model: str = Field("gpt-4-vision-preview", description="AI model to use")
    max_tokens: int = Field(1000, description="Maximum tokens for response")
    temperature: float = Field(0.1, description="Temperature for AI response")
    
    # Extraction preferences
    extract_line_items: bool = Field(False, description="Whether to extract individual line items")
    preferred_currency: Optional[Currency] = Field(None, description="Preferred currency for extraction")
    
    # Metadata
    request_id: UUID = Field(default_factory=uuid4, description="Unique request ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Request timestamp")


class AIExtractionResponse(BaseModel):
    """Response model from AI vision extraction."""
    
    request_id: UUID = Field(..., description="Original request ID")
    success: bool = Field(..., description="Whether extraction was successful")
    
    # Extracted data
    receipt_data: Optional[ReceiptData] = Field(None, description="Extracted receipt data")
    
    # Response metadata
    model_used: str = Field(..., description="AI model that processed the request")
    processing_time: float = Field(..., description="Processing time in seconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    confidence_score: float = Field(0.0, description="Overall confidence in extraction")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    error_code: Optional[str] = Field(None, description="Error code for categorization")
    
    # Raw response data
    raw_response: Optional[str] = Field(None, description="Raw response from AI model")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Response timestamp")


# Type aliases for convenience
ReceiptLogDict = Dict[str, Any]
StatusDict = Dict[str, Union[str, int, float, datetime]]
