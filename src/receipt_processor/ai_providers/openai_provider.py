"""
OpenAI Provider for Receipt Processing Application.

This module provides integration with OpenAI's vision models for receipt extraction.
"""

import asyncio
import base64
import io
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import openai
from PIL import Image
from loguru import logger

from .base import BaseAIProvider, AIProviderConfig, AIProviderCapabilities, AIProviderResult
from ..models import ReceiptData, Currency


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider for receipt data extraction."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            timeout=config.timeout
        )
        logger.info(f"OpenAI provider initialized with model: {config.model_name}")
    
    def _get_capabilities(self) -> AIProviderCapabilities:
        """Get OpenAI provider capabilities."""
        return AIProviderCapabilities(
            supports_vision=True,
            supports_streaming=False,
            supports_function_calling=True,
            max_tokens=128000,  # GPT-4 Vision
            max_image_size=2048,
            supported_formats=["jpeg", "png", "gif", "webp"],
            cost_per_token=0.00001,  # Approximate cost per token
            cost_per_image=0.00001   # Approximate cost per image
        )
    
    async def extract_receipt_data(
        self,
        image_data: bytes,
        image_format: str = "jpeg",
        extract_line_items: bool = False,
        preferred_currency: Optional[Currency] = None,
        **kwargs
    ) -> AIProviderResult:
        """Extract receipt data using OpenAI vision model."""
        start_time = time.time()
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create messages for the API
            messages = self._create_messages(
                image_base64,
                image_format,
                extract_line_items,
                preferred_currency
            )
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **self.config.model_parameters
            )
            
            processing_time = time.time() - start_time
            
            # Parse response
            receipt_data = self._parse_response(
                response.choices[0].message.content,
                preferred_currency
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(receipt_data)
            
            return self._create_success_result(
                receipt_data=receipt_data,
                raw_response=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens if response.usage else None,
                processing_time=processing_time,
                confidence_score=confidence,
                provider_metadata={
                    "model": self.config.model_name,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.dict() if response.usage else None
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"OpenAI extraction failed: {e}")
            
            return self._create_error_result(
                error_message=str(e),
                error_code="OPENAI_ERROR",
                processing_time=processing_time
            )
    
    def _create_messages(
        self,
        image_base64: str,
        image_format: str,
        extract_line_items: bool,
        preferred_currency: Optional[Currency]
    ) -> List[Dict[str, Any]]:
        """Create messages for OpenAI API."""
        system_prompt = self._get_system_prompt(extract_line_items, preferred_currency)
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this receipt image and extract the structured data in JSON format."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
        
        return messages
    
    def _get_system_prompt(
        self,
        extract_line_items: bool,
        preferred_currency: Optional[Currency]
    ) -> str:
        """Get system prompt for OpenAI."""
        prompt_parts = [
            "You are a specialized AI assistant for extracting structured data from receipt images.",
            "Extract the following information and return it as valid JSON:",
            "",
            "Required fields:",
            "- vendor_name: string (business/merchant name)",
            "- transaction_date: string (ISO 8601 format: YYYY-MM-DD)",
            "- total_amount: number (decimal value without currency symbol)",
            "- currency: string (3-letter currency code like USD, EUR, GBP)",
            "",
            "Optional fields:",
            "- receipt_number: string (receipt/invoice number)",
            "- tax_amount: number (tax amount if shown separately)",
            "- subtotal: number (subtotal before tax)",
            "- payment_method: string (cash, card, etc.)",
            "- items: array of objects with 'name', 'quantity', 'price' fields",
            "",
            "IMPORTANT:",
            "1. Only extract information that is clearly visible",
            "2. Use null for missing or unclear information",
            "3. Return valid JSON only, no additional text",
            "4. For dates, convert to YYYY-MM-DD format",
            "5. For amounts, use decimal numbers without currency symbols"
        ]
        
        if extract_line_items:
            prompt_parts.append("6. Include individual line items in the 'items' array")
        
        if preferred_currency:
            prompt_parts.append(f"7. If no currency is visible, use {preferred_currency.value}")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_content: str, preferred_currency: Optional[Currency]) -> ReceiptData:
        """Parse OpenAI response into ReceiptData."""
        import json
        
        try:
            # Try to extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_content[json_start:json_end]
            data = json.loads(json_str)
            
            # Convert to ReceiptData
            receipt_data = ReceiptData(
                vendor_name=data.get('vendor_name'),
                transaction_date=self._parse_date(data.get('transaction_date')),
                total_amount=self._parse_amount(data.get('total_amount')),
                currency=data.get('currency') or (preferred_currency.value if preferred_currency else None),
                receipt_number=data.get('receipt_number'),
                tax_amount=self._parse_amount(data.get('tax_amount')),
                subtotal=self._parse_amount(data.get('subtotal')),
                payment_method=data.get('payment_method'),
                items=data.get('items', []),
                extraction_timestamp=datetime.now()
            )
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            # Return minimal ReceiptData with raw response
            return ReceiptData(
                raw_extraction_text=response_content,
                extraction_timestamp=datetime.now()
            )
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except Exception:
            return None
    
    def _parse_amount(self, amount: Any) -> Optional[float]:
        """Parse amount to float."""
        if amount is None:
            return None
        
        try:
            if isinstance(amount, (int, float)):
                return float(amount)
            elif isinstance(amount, str):
                # Remove currency symbols and whitespace
                cleaned = amount.replace('$', '').replace('€', '').replace('£', '').strip()
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _calculate_confidence(self, receipt_data: ReceiptData) -> float:
        """Calculate confidence score for extraction."""
        confidence_factors = []
        
        # Base confidence on required fields
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
        
        return min(1.0, sum(confidence_factors))
    
    async def test_connection(self) -> bool:
        """Test connection to OpenAI API."""
        try:
            # Simple test with a minimal request
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
