"""
Anthropic Provider for Receipt Processing Application.

This module provides integration with Anthropic's Claude models for receipt extraction.
"""

import asyncio
import base64
import io
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import anthropic
from PIL import Image
from loguru import logger

from .base import BaseAIProvider, AIProviderConfig, AIProviderCapabilities, AIProviderResult
from ..models import ReceiptData, Currency


class AnthropicProvider(BaseAIProvider):
    """Anthropic provider for receipt data extraction."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            timeout=config.timeout
        )
        logger.info(f"Anthropic provider initialized with model: {config.model_name}")
    
    def _get_capabilities(self) -> AIProviderCapabilities:
        """Get Anthropic provider capabilities."""
        return AIProviderCapabilities(
            supports_vision=True,
            supports_streaming=False,
            supports_function_calling=True,
            max_tokens=200000,  # Claude 3.5 Sonnet
            max_image_size=2048,
            supported_formats=["jpeg", "png", "gif", "webp"],
            cost_per_token=0.000003,  # Approximate cost per token
            cost_per_image=0.00001    # Approximate cost per image
        )
    
    async def extract_receipt_data(
        self,
        image_data: bytes,
        image_format: str = "jpeg",
        extract_line_items: bool = False,
        preferred_currency: Optional[Currency] = None,
        **kwargs
    ) -> AIProviderResult:
        """Extract receipt data using Anthropic Claude model."""
        start_time = time.time()
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create message for the API
            message = self._create_message(
                image_base64,
                image_format,
                extract_line_items,
                preferred_currency
            )
            
            # Call Anthropic API
            response = await self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[message],
                **self.config.model_parameters
            )
            
            processing_time = time.time() - start_time
            
            # Parse response
            receipt_data = self._parse_response(
                response.content[0].text,
                preferred_currency
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(receipt_data)
            
            return self._create_success_result(
                receipt_data=receipt_data,
                raw_response=response.content[0].text,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                processing_time=processing_time,
                confidence_score=confidence,
                provider_metadata={
                    "model": self.config.model_name,
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    }
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Anthropic extraction failed: {e}")
            
            return self._create_error_result(
                error_message=str(e),
                error_code="ANTHROPIC_ERROR",
                processing_time=processing_time
            )
    
    def _create_message(
        self,
        image_base64: str,
        image_format: str,
        extract_line_items: bool,
        preferred_currency: Optional[Currency]
    ) -> Dict[str, Any]:
        """Create message for Anthropic API."""
        system_prompt = self._get_system_prompt(extract_line_items, preferred_currency)
        user_prompt = self._get_user_prompt()
        
        message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{system_prompt}\n\n{user_prompt}"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{image_format}",
                        "data": image_base64
                    }
                }
            ]
        }
        
        return message
    
    def _get_system_prompt(
        self,
        extract_line_items: bool,
        preferred_currency: Optional[Currency]
    ) -> str:
        """Get system prompt for Anthropic."""
        prompt_parts = [
            "You are a specialized AI assistant for extracting structured data from receipt images.",
            "Your task is to analyze receipt images and extract key information in JSON format.",
            "",
            "Extract the following information:",
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
            "IMPORTANT INSTRUCTIONS:",
            "1. Only extract information that is clearly visible and readable",
            "2. Use null for missing or unclear information",
            "3. Return valid JSON only, no additional text or explanations",
            "4. For dates, convert to YYYY-MM-DD format",
            "5. For amounts, use decimal numbers without currency symbols",
            "6. Be accurate and conservative - better to extract less information confidently"
        ]
        
        if extract_line_items:
            prompt_parts.append("7. Include individual line items in the 'items' array if clearly visible")
        
        if preferred_currency:
            prompt_parts.append(f"8. If no currency is visible, use {preferred_currency.value}")
        
        return "\n".join(prompt_parts)
    
    def _get_user_prompt(self) -> str:
        """Get user prompt for Anthropic."""
        return "Please analyze this receipt image and extract the structured data in JSON format."
    
    def _parse_response(self, response_content: str, preferred_currency: Optional[Currency]) -> ReceiptData:
        """Parse Anthropic response into ReceiptData."""
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
            logger.error(f"Failed to parse Anthropic response: {e}")
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
        """Test connection to Anthropic API."""
        try:
            # Simple test with a minimal request
            response = await self.client.messages.create(
                model=self.config.model_name,
                max_tokens=5,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {e}")
            return False
