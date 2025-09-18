"""
Batch Email Templates for Receipt Processing Workflow.

This module provides additional email templates for batch operations,
workflow notifications, and scheduled reports.
"""

from pathlib import Path
from typing import Dict, Any


class BatchTemplateManager:
    """Manages batch email templates for workflow notifications."""
    
    BATCH_TEMPLATES = {
        # Batch processed receipts template
        "receipt_processed_batch.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Batch Receipt Processing Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .receipt-list { margin: 20px 0; }
        .receipt-item { border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .amount { font-weight: bold; color: #2e7d32; }
        .vendor { font-weight: bold; color: #1565c0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h2>📧 Batch Receipt Processing Summary</h2>
        <p>Processing completed for {{ batch_size }} receipts</p>
        <p><strong>Period:</strong> {{ period_start.strftime('%Y-%m-%d %H:%M') }} - {{ period_end.strftime('%Y-%m-%d %H:%M') }}</p>
        <p><strong>Batch Type:</strong> {{ batch_frequency|title }}</p>
    </div>
    
    <div class="summary">
        <h3>📊 Summary</h3>
        <ul>
            <li><strong>Total Receipts:</strong> {{ batch_size }}</li>
            <li><strong>Total Amount:</strong> ${{ "%.2f"|format(total_amount) }}</li>
            <li><strong>Batch Created:</strong> {{ batch_created_at.strftime('%Y-%m-%d %H:%M:%S') }}</li>
        </ul>
    </div>
    
    <div class="receipt-list">
        <h3>📋 Receipt Details</h3>
        {% for receipt in receipts %}
        <div class="receipt-item">
            <div class="vendor">{{ receipt.vendor_name or 'Unknown Vendor' }}</div>
            <div>
                <strong>Amount:</strong> <span class="amount">${{ receipt.total_amount or '0.00' }} {{ receipt.currency or 'USD' }}</span> |
                <strong>Date:</strong> {{ receipt.transaction_date or 'N/A' }} |
                <strong>File:</strong> {{ receipt.original_filename }}
            </div>
            <div>
                <strong>Status:</strong> {{ receipt.current_status|title }} |
                <strong>Confidence:</strong> {{ receipt.confidence_score or 0 }}%
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="footer">
        <p>This is an automated notification from the Receipt Processing System.</p>
        <p>Generated at {{ batch_created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
        """,
        
        # Batch processed receipts subject
        "receipt_processed_batch_subject.txt": "📧 {{ batch_size }} Receipts Processed - ${{ '%.2f'|format(total_amount) }} Total",
        
        # High value receipt template
        "high_value_receipt.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>High Value Receipt Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .alert { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .amount { font-size: 24px; font-weight: bold; color: #d32f2f; }
        .vendor { font-size: 18px; font-weight: bold; color: #1565c0; }
    </style>
</head>
<body>
    <div class="alert">
        <h2>🚨 High Value Receipt Alert</h2>
        <p>A high-value receipt has been processed and requires attention.</p>
    </div>
    
    <div class="details">
        <div class="vendor">{{ vendor_name }}</div>
        <div class="amount">${{ total_amount }} {{ currency }}</div>
        <p><strong>Transaction Date:</strong> {{ transaction_date }}</p>
        <p><strong>File:</strong> {{ original_filename }}</p>
        <p><strong>Processed At:</strong> {{ processed_at or created_at }}</p>
        <p><strong>Confidence Score:</strong> {{ confidence_score }}%</p>
    </div>
    
    <div>
        <h3>📋 Next Steps</h3>
        <ul>
            <li>Review receipt details for accuracy</li>
            <li>Verify vendor and amount information</li>
            <li>Approve for expense processing</li>
            <li>File receipt according to company policy</li>
        </ul>
    </div>
    
    <p>This receipt has been flagged due to its high value and may require additional approval.</p>
</body>
</html>
        """,
        
        # High value receipt subject
        "high_value_receipt_subject.txt": "🚨 High Value Receipt: {{ vendor_name }} - ${{ total_amount }}",
        
        # Daily summary template
        "daily_summary.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Daily Receipt Processing Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .metrics { display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }
        .metric { background-color: #f8f9fa; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #1565c0; }
        .metric-label { color: #666; margin-top: 5px; }
        .receipt-summary { margin: 20px 0; }
        .status-breakdown { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h2>📊 Daily Receipt Processing Summary</h2>
        <p><strong>Date:</strong> {{ batch_created_at.strftime('%Y-%m-%d') }}</p>
        <p>Your daily summary of receipt processing activities</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{{ batch_size }}</div>
            <div class="metric-label">Total Receipts</div>
        </div>
        <div class="metric">
            <div class="metric-value">${{ "%.2f"|format(total_amount) }}</div>
            <div class="metric-label">Total Amount</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ (receipts|selectattr('current_status', 'equalto', 'PROCESSED')|list|length / receipts|length * 100)|round(1) if receipts else 0 }}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
    </div>
    
    <div class="status-breakdown">
        <h3>📋 Status Breakdown</h3>
        <ul>
            <li><strong>Processed:</strong> {{ receipts|selectattr('current_status', 'equalto', 'PROCESSED')|list|length }} receipts</li>
            <li><strong>Errors:</strong> {{ receipts|selectattr('current_status', 'equalto', 'ERROR')|list|length }} receipts</li>
            <li><strong>Pending:</strong> {{ receipts|selectattr('current_status', 'equalto', 'PENDING')|list|length }} receipts</li>
        </ul>
    </div>
    
    {% if receipts|selectattr('current_status', 'equalto', 'PROCESSED')|list %}
    <div class="receipt-summary">
        <h3>✅ Successfully Processed Receipts</h3>
        {% for receipt in receipts|selectattr('current_status', 'equalto', 'PROCESSED')|list %}
        <div style="border-left: 4px solid #4caf50; padding-left: 15px; margin: 10px 0;">
            <strong>{{ receipt.vendor_name or 'Unknown Vendor' }}</strong> - 
            ${{ receipt.total_amount or '0.00' }} 
            ({{ receipt.transaction_date or 'N/A' }})
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    {% if receipts|selectattr('current_status', 'equalto', 'ERROR')|list %}
    <div class="receipt-summary">
        <h3>❌ Failed Receipts</h3>
        {% for receipt in receipts|selectattr('current_status', 'equalto', 'ERROR')|list %}
        <div style="border-left: 4px solid #f44336; padding-left: 15px; margin: 10px 0;">
            <strong>{{ receipt.original_filename }}</strong> - 
            Processing failed (Confidence: {{ receipt.confidence_score or 0 }}%)
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
        <p>📧 This is your automated daily summary from the Receipt Processing System.</p>
        <p>Generated at {{ batch_created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
        """,
        
        # Daily summary subject
        "daily_summary_subject.txt": "📊 Daily Summary: {{ batch_size }} Receipts - ${{ '%.2f'|format(total_amount) }}",
        
        # Bulk receipt summary template
        "bulk_receipt_summary.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bulk Receipt Processing Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #e8f5e9; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .bulk-stats { background-color: #f3e5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .receipt-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin: 20px 0; }
        .receipt-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #fafafa; }
        .receipt-header { font-weight: bold; color: #1565c0; margin-bottom: 10px; }
        .receipt-amount { font-size: 18px; font-weight: bold; color: #2e7d32; }
    </style>
</head>
<body>
    <div class="header">
        <h2>📦 Bulk Receipt Processing Complete</h2>
        <p>Bulk operation completed successfully</p>
        <p><strong>Processing Period:</strong> {{ period_start.strftime('%Y-%m-%d %H:%M') }} - {{ period_end.strftime('%Y-%m-%d %H:%M') }}</p>
    </div>
    
    <div class="bulk-stats">
        <h3>📊 Bulk Operation Statistics</h3>
        <div style="display: flex; gap: 30px; flex-wrap: wrap;">
            <div><strong>Total Receipts:</strong> {{ total_receipts }}</div>
            <div><strong>Total Amount:</strong> ${{ "%.2f"|format(total_amount) }}</div>
            <div><strong>Processing Time:</strong> {{ ((period_end - period_start).total_seconds() / 60)|round(1) }} minutes</div>
        </div>
    </div>
    
    <div class="receipt-grid">
        {% for receipt in receipts %}
        <div class="receipt-card">
            <div class="receipt-header">{{ receipt.vendor_name or 'Unknown Vendor' }}</div>
            <div class="receipt-amount">${{ receipt.total_amount or '0.00' }} {{ receipt.currency or 'USD' }}</div>
            <div><strong>Date:</strong> {{ receipt.transaction_date or 'N/A' }}</div>
            <div><strong>File:</strong> {{ receipt.original_filename }}</div>
            <div><strong>Status:</strong> {{ receipt.current_status|title }}</div>
            <div><strong>Confidence:</strong> {{ receipt.confidence_score or 0 }}%</div>
        </div>
        {% endfor %}
    </div>
    
    <div style="margin-top: 30px;">
        <h3>📋 Next Steps</h3>
        <ul>
            <li>Review processed receipts for accuracy</li>
            <li>Handle any failed receipts that need attention</li>
            <li>Update expense tracking systems</li>
            <li>Archive processed receipt files</li>
        </ul>
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
        <p>This bulk operation was completed automatically by the Receipt Processing System.</p>
        <p>Generated at {{ bulk_created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
        """,
        
        # Bulk summary subject
        "bulk_receipt_summary_subject.txt": "📦 Bulk Processing Complete: {{ total_receipts }} Receipts - ${{ '%.2f'|format(total_amount) }}",
        
        # Error escalation template
        "error_escalation.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Receipt Processing Error Escalation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .alert { background-color: #ffebee; border: 1px solid #f44336; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .error-details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .actions { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="alert">
        <h2>🚨 Receipt Processing Error Escalation</h2>
        <p>A receipt processing error requires immediate attention.</p>
    </div>
    
    <div class="error-details">
        <h3>❌ Error Details</h3>
        <p><strong>File:</strong> {{ original_filename }}</p>
        <p><strong>Error Time:</strong> {{ error_time or created_at }}</p>
        <p><strong>Status:</strong> {{ current_status|title }}</p>
        <p><strong>Error Message:</strong> {{ error_message or 'Unknown error occurred' }}</p>
        {% if confidence_score %}
        <p><strong>Confidence Score:</strong> {{ confidence_score }}%</p>
        {% endif %}
    </div>
    
    <div class="actions">
        <h3>🔧 Recommended Actions</h3>
        <ul>
            <li>Review the receipt image for quality issues</li>
            <li>Check if the receipt format is supported</li>
            <li>Verify the image is readable and not corrupted</li>
            <li>Consider manual data entry if automated processing fails</li>
            <li>Contact support if the issue persists</li>
        </ul>
    </div>
    
    <div>
        <h3>📊 Processing Context</h3>
        <p><strong>File Size:</strong> {{ file_size or 'Unknown' }} bytes</p>
        <p><strong>Processing Attempts:</strong> Multiple attempts failed</p>
        <p><strong>Escalation Threshold:</strong> 24 hours exceeded</p>
    </div>
    
    <p style="color: #d32f2f; font-weight: bold;">This error has been escalated due to processing delays. Please address immediately.</p>
</body>
</html>
        """,
        
        # Error escalation subject
        "error_escalation_subject.txt": "🚨 ESCALATED: Receipt Processing Error - {{ original_filename }}",
        
        # Workflow milestone template
        "workflow_milestone.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Workflow Milestone Reached</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .milestone { background-color: #e8f5e9; padding: 20px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
        .milestone-icon { font-size: 48px; margin-bottom: 10px; }
        .details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="milestone">
        <div class="milestone-icon">🎉</div>
        <h2>Workflow Milestone Reached</h2>
        <p>A significant milestone has been achieved in receipt processing.</p>
    </div>
    
    <div class="details">
        <h3>📋 Milestone Details</h3>
        <p><strong>Receipt:</strong> {{ vendor_name or 'Unknown Vendor' }}</p>
        <p><strong>Amount:</strong> ${{ total_amount or '0.00' }} {{ currency or 'USD' }}</p>
        <p><strong>Date:</strong> {{ transaction_date or 'N/A' }}</p>
        <p><strong>Status:</strong> {{ current_status|title }}</p>
        <p><strong>Milestone Time:</strong> {{ notification_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div>
        <h3>✅ Achievement</h3>
        <p>This receipt has met the criteria for workflow milestone notification:</p>
        <ul>
            <li>High-value transaction processed successfully</li>
            <li>Confidence score meets quality standards</li>
            <li>All validation checks passed</li>
            <li>Ready for final approval workflow</li>
        </ul>
    </div>
    
    <p>Congratulations on reaching this processing milestone!</p>
</body>
</html>
        """,
        
        # Workflow milestone subject
        "workflow_milestone_subject.txt": "🎉 Milestone: {{ vendor_name }} - ${{ total_amount }} Processed"
    }
    
    @classmethod
    def create_batch_templates(cls, template_dir: Path):
        """Create all batch email templates in the specified directory."""
        template_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in cls.BATCH_TEMPLATES.items():
            template_file = template_dir / filename
            template_file.write_text(content.strip())
        
        return len(cls.BATCH_TEMPLATES)
    
    @classmethod
    def get_template_list(cls) -> list:
        """Get list of available batch templates."""
        return list(cls.BATCH_TEMPLATES.keys())
    
    @classmethod
    def get_template_content(cls, template_name: str) -> str:
        """Get content of a specific template."""
        return cls.BATCH_TEMPLATES.get(template_name, "")


# Template variables reference for documentation
TEMPLATE_VARIABLES = {
    "batch_templates": {
        "batch_size": "Number of receipts in the batch",
        "total_amount": "Sum of all receipt amounts in the batch",
        "batch_frequency": "Frequency type (hourly, daily, etc.)",
        "batch_created_at": "Timestamp when batch was created",
        "period_start": "Start of the processing period",
        "period_end": "End of the processing period",
        "receipts": "List of receipt data objects",
        "total_receipts": "Total number of receipts processed"
    },
    "receipt_variables": {
        "vendor_name": "Name of the vendor/merchant",
        "total_amount": "Receipt total amount",
        "currency": "Currency code (USD, EUR, etc.)",
        "transaction_date": "Date of the transaction",
        "original_filename": "Original receipt file name",
        "current_status": "Processing status",
        "confidence_score": "AI extraction confidence percentage",
        "file_size": "Size of the receipt file in bytes",
        "created_at": "When the receipt was first processed",
        "processed_at": "When processing was completed"
    },
    "workflow_variables": {
        "event_id": "Unique identifier for the workflow event",
        "trigger_type": "Type of trigger that caused the email",
        "priority": "Email priority level",
        "notification_time": "When the notification was sent",
        "error_message": "Error description (for error notifications)",
        "error_time": "When the error occurred"
    }
}
