"""
AI Vision integration module for Receipt Processing Application.

This module provides integration with AI vision models for extracting
receipt data from images using Pydantic AI framework.
"""

import asyncio
import base64
import io
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from uuid import uuid4

from PIL import Image
from pydantic import BaseModel
from pydantic_ai import Agent
from loguru import logger

from .config import AppSettings
from .models import (
    ReceiptData, AIExtractionRequest, AIExtractionResponse, 
    Currency, ProcessingStatus
)
from .image_processor import ImageProcessor, ProcessingOptions


class ReceiptExtractionAgent:
    """AI agent specialized in receipt data extraction."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.image_processor = ImageProcessor(settings)
        
        # Initialize AI model based on configuration
        self.model = self._create_model()
        
        # Create Pydantic AI agent with structured output
        self.agent = Agent(
            model=self.model,
            result_type=ReceiptData,
            system_prompt=self._get_system_prompt()
        )
        
        logger.info(f"ReceiptExtractionAgent initialized with {settings.ai_vision.provider} model")
    
    def _create_model(self) -> str:
        """Create AI model identifier based on configuration."""
        provider = self.settings.ai_vision.provider.lower()
        
        if provider == "openai":
            return f"openai:{self.settings.ai_vision.model}"
        elif provider == "anthropic":
            return f"anthropic:{self.settings.ai_vision.model}"
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for receipt extraction."""
        return """
You are a specialized AI assistant for extracting structured data from receipt images.

Your task is to analyze receipt images and extract key information including:
- Vendor/merchant name
- Transaction date
- Total amount
- Currency
- Receipt/invoice number (if visible)
- Tax amount (if shown separately)
- Subtotal (if shown)

IMPORTANT INSTRUCTIONS:
1. Only extract information that is clearly visible and readable in the image
2. For dates, try to parse them into standard datetime format
3. For amounts, extract as precise decimal values without currency symbols
4. If you cannot clearly read a value, set it to null rather than guessing
5. Provide a confidence score based on image quality and text clarity
6. Extract the raw text you can see for reference

CURRENCY DETECTION:
- Look for currency symbols ($, €, £, ¥, etc.) or currency codes (USD, EUR, GBP)
- If no currency is visible, use the default from configuration
- Common patterns: $10.99, €15.50, £8.75, ¥1000

DATE PARSING:
- Look for dates in formats like: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
- Also check for written dates like "Jan 15, 2024" or "15 January 2024"
- Transaction date is usually near the top of the receipt

VENDOR IDENTIFICATION:
- Usually the largest text at the top of the receipt
- May be a business name, restaurant name, store name, etc.
- Avoid extracting addresses as vendor names

Be accurate and conservative - it's better to extract less information confidently 
than to make uncertain guesses.
"""
    
    async def extract_from_image(self, request: AIExtractionRequest) -> AIExtractionResponse:
        """
        Extract receipt data from an image using AI vision.
        
        Args:
            request: Extraction request with image and parameters
            
        Returns:
            AI extraction response with results
        """
        start_time = time.time()
        
        try:
            # Load and preprocess image
            image_data = await self._prepare_image(request)
            if not image_data:
                return AIExtractionResponse(
                    request_id=request.request_id,
                    success=False,
                    model_used=request.model,
                    processing_time=time.time() - start_time,
                    error_message="Failed to load or process image",
                    error_code="IMAGE_LOAD_ERROR"
                )
            
            # Create user prompt with image
            user_prompt = self._create_user_prompt(request)
            
            # Run AI extraction
            result = await self.agent.run(
                user_prompt,
                images=[image_data],
                model_settings={
                    'max_tokens': request.max_tokens,
                    'temperature': request.temperature,
                }
            )
            
            processing_time = time.time() - start_time
            
            # Validate and enhance extracted data
            receipt_data = result.data
            receipt_data.extraction_confidence = self._calculate_confidence(receipt_data)
            receipt_data.extraction_timestamp = datetime.now()
            
            # Apply preferred currency if none detected
            if not receipt_data.currency and request.preferred_currency:
                receipt_data.currency = request.preferred_currency
            
            logger.info(f"AI extraction completed in {processing_time:.2f}s")
            
            return AIExtractionResponse(
                request_id=request.request_id,
                success=True,
                receipt_data=receipt_data,
                model_used=request.model,
                processing_time=processing_time,
                tokens_used=getattr(result, 'usage', {}).get('total_tokens'),
                confidence_score=receipt_data.extraction_confidence,
                raw_response=str(result.data)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"AI extraction failed: {e}")
            
            return AIExtractionResponse(
                request_id=request.request_id,
                success=False,
                model_used=request.model,
                processing_time=processing_time,
                error_message=str(e),
                error_code="EXTRACTION_ERROR"
            )
    
    async def _prepare_image(self, request: AIExtractionRequest) -> Optional[bytes]:
        """Prepare image for AI processing."""
        try:
            # Load image
            if request.image_data:
                image = Image.open(io.BytesIO(request.image_data))
            elif request.image_path:
                image = self.image_processor.load_image(request.image_path)
            else:
                return None
            
            if not image:
                return None
            
            # Preprocess image for optimal AI processing
            processing_options = ProcessingOptions(
                max_width=2048,
                max_height=2048,
                enhance_contrast=True,
                enhance_sharpness=True,
                convert_to_rgb=True,
                jpeg_quality=95
            )
            
            processed_image = self.image_processor.preprocess_image(image, processing_options)
            
            # Convert to bytes for AI processing
            output = io.BytesIO()
            processed_image.save(output, format='JPEG', quality=95, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image preparation failed: {e}")
            return None
    
    def _create_user_prompt(self, request: AIExtractionRequest) -> str:
        """Create user prompt for the AI model."""
        prompt_parts = [
            "Please analyze this receipt image and extract the structured data.",
            "Focus on accuracy and only extract information you can clearly see."
        ]
        
        if request.extract_line_items:
            prompt_parts.append(
                "Also extract individual line items if they are clearly visible."
            )
        
        if request.preferred_currency:
            prompt_parts.append(
                f"If no currency is visible, assume {request.preferred_currency.value}."
            )
        
        return " ".join(prompt_parts)
    
    def _calculate_confidence(self, receipt_data: ReceiptData) -> float:
        """Calculate overall confidence score for extraction."""
        confidence_factors = []
        
        # Base confidence on data completeness
        if receipt_data.vendor_name:
            confidence_factors.append(0.3)
        if receipt_data.transaction_date:
            confidence_factors.append(0.3)
        if receipt_data.total_amount:
            confidence_factors.append(0.4)
        
        # Bonus for additional data
        if receipt_data.currency:
            confidence_factors.append(0.1)
        if receipt_data.receipt_number:
            confidence_factors.append(0.1)
        if receipt_data.tax_amount:
            confidence_factors.append(0.1)
        
        # Calculate base confidence
        base_confidence = sum(confidence_factors)
        
        # Apply validation penalties
        if receipt_data.validation_errors:
            penalty = min(0.2, len(receipt_data.validation_errors) * 0.1)
            base_confidence -= penalty
        
        return max(0.0, min(1.0, base_confidence))


class VisionExtractionService:
    """Main service for AI vision-based receipt extraction."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.agent = ReceiptExtractionAgent(settings)
        self.extraction_history: List[AIExtractionResponse] = []
        
        logger.info("VisionExtractionService initialized")
    
    async def extract_receipt_data(
        self, 
        image_path: Union[Path, str],
        extract_line_items: bool = False,
        preferred_currency: Optional[Currency] = None
    ) -> AIExtractionResponse:
        """
        Extract receipt data from an image file.
        
        Args:
            image_path: Path to the receipt image
            extract_line_items: Whether to extract individual line items
            preferred_currency: Preferred currency if none detected
            
        Returns:
            Extraction response with results
        """
        request = AIExtractionRequest(
            image_path=Path(image_path),
            model=self.settings.ai_vision.model,
            extract_line_items=extract_line_items,
            preferred_currency=preferred_currency or Currency(self.settings.extraction.default_currency)
        )
        
        response = await self.agent.extract_from_image(request)
        
        # Store in history
        self.extraction_history.append(response)
        
        # Keep only recent history to prevent memory bloat
        if len(self.extraction_history) > 100:
            self.extraction_history = self.extraction_history[-50:]
        
        return response
    
    async def extract_with_retry(
        self,
        image_path: Union[Path, str],
        max_retries: Optional[int] = None,
        **kwargs
    ) -> AIExtractionResponse:
        """
        Extract receipt data with automatic retry on failure.
        
        Args:
            image_path: Path to the receipt image
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for extraction
            
        Returns:
            Extraction response with results
        """
        max_retries = max_retries or self.settings.ai_vision.max_retries
        last_response = None
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.extract_receipt_data(image_path, **kwargs)
                
                if response.success:
                    if attempt > 0:
                        logger.info(f"Extraction succeeded on attempt {attempt + 1}")
                    return response
                
                last_response = response
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Extraction attempt {attempt + 1} failed, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Extraction attempt {attempt + 1} failed with exception: {e}")
                if attempt == max_retries:
                    # Create error response for final failure
                    last_response = AIExtractionResponse(
                        request_id=uuid4(),
                        success=False,
                        model_used=self.settings.ai_vision.model,
                        processing_time=0.0,
                        error_message=str(e),
                        error_code="MAX_RETRIES_EXCEEDED"
                    )
                    break
                
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        logger.error(f"All {max_retries + 1} extraction attempts failed")
        return last_response
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about recent extractions."""
        if not self.extraction_history:
            return {"total_extractions": 0}
        
        total = len(self.extraction_history)
        successful = len([r for r in self.extraction_history if r.success])
        failed = total - successful
        
        avg_processing_time = sum(r.processing_time for r in self.extraction_history) / total
        avg_confidence = sum(
            r.confidence_score for r in self.extraction_history if r.confidence_score > 0
        ) / max(1, len([r for r in self.extraction_history if r.confidence_score > 0]))
        
        return {
            "total_extractions": total,
            "successful_extractions": successful,
            "failed_extractions": failed,
            "success_rate": successful / total if total > 0 else 0,
            "average_processing_time": avg_processing_time,
            "average_confidence": avg_confidence,
            "model_used": self.settings.ai_vision.model
        }
    
    async def test_connection(self) -> bool:
        """Test connection to AI service."""
        try:
            # Create a simple test image
            test_image = Image.new('RGB', (100, 100), color='white')
            test_data = io.BytesIO()
            test_image.save(test_data, format='JPEG')
            
            request = AIExtractionRequest(
                image_data=test_data.getvalue(),
                model=self.settings.ai_vision.model,
                max_tokens=10
            )
            
            response = await self.agent.extract_from_image(request)
            
            # Even if extraction fails, a response indicates connection works
            return True
            
        except Exception as e:
            logger.error(f"AI service connection test failed: {e}")
            return False


# Convenience functions
async def extract_receipt_data(
    image_path: Union[Path, str], 
    settings: AppSettings,
    **kwargs
) -> AIExtractionResponse:
    """Convenience function to extract receipt data from an image."""
    service = VisionExtractionService(settings)
    return await service.extract_receipt_data(image_path, **kwargs)


def create_extraction_service(settings: AppSettings) -> VisionExtractionService:
    """Create a new VisionExtractionService instance."""
    return VisionExtractionService(settings)
