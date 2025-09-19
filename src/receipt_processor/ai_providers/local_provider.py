"""
Local Model Provider for Receipt Processing Application.

This module provides integration with local AI models for receipt extraction,
including support for Ollama, Transformers, and other local model frameworks.
"""

import asyncio
import base64
import io
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image
from loguru import logger

from .base import BaseAIProvider, AIProviderConfig, AIProviderCapabilities, AIProviderResult
from ..models import ReceiptData, Currency


class LocalModelProvider(BaseAIProvider):
    """Local model provider for receipt data extraction."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.model_path = config.model_parameters.get('model_path')
        self.model_type = config.model_parameters.get('model_type', 'ollama')
        self.ollama_url = config.model_parameters.get('ollama_url', 'http://localhost:11434')
        self._model = None
        logger.info(f"Local model provider initialized: {self.model_type}")
    
    def _get_capabilities(self) -> AIProviderCapabilities:
        """Get local model provider capabilities."""
        return AIProviderCapabilities(
            supports_vision=True,
            supports_streaming=False,
            supports_function_calling=False,
            max_tokens=4096,
            max_image_size=1024,
            supported_formats=["jpeg", "png", "webp"],
            cost_per_token=0.0,  # Local models are free
            cost_per_image=0.0
        )
    
    async def extract_receipt_data(
        self,
        image_data: bytes,
        image_format: str = "jpeg",
        extract_line_items: bool = False,
        preferred_currency: Optional[Currency] = None,
        **kwargs
    ) -> AIProviderResult:
        """Extract receipt data using local model."""
        start_time = time.time()
        
        try:
            if self.model_type == 'ollama':
                return await self._extract_with_ollama(
                    image_data, image_format, extract_line_items, preferred_currency, start_time
                )
            elif self.model_type == 'transformers':
                return await self._extract_with_transformers(
                    image_data, image_format, extract_line_items, preferred_currency, start_time
                )
            else:
                raise ValueError(f"Unsupported local model type: {self.model_type}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Local model extraction failed: {e}")
            
            return self._create_error_result(
                error_message=str(e),
                error_code="LOCAL_MODEL_ERROR",
                processing_time=processing_time
            )
    
    async def _extract_with_ollama(
        self,
        image_data: bytes,
        image_format: str,
        extract_line_items: bool,
        preferred_currency: Optional[Currency],
        start_time: float
    ) -> AIProviderResult:
        """Extract using Ollama local model."""
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create prompt
            prompt = self._create_prompt(extract_line_items, preferred_currency)
            
            # Prepare request data
            request_data = {
                "model": self.config.model_name,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            processing_time = time.time() - start_time
            
            # Parse response
            receipt_data = self._parse_response(
                result.get('response', ''),
                preferred_currency
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(receipt_data)
            
            return self._create_success_result(
                receipt_data=receipt_data,
                raw_response=result.get('response', ''),
                tokens_used=result.get('eval_count', 0),
                processing_time=processing_time,
                confidence_score=confidence,
                provider_metadata={
                    "model": self.config.model_name,
                    "model_type": "ollama",
                    "eval_count": result.get('eval_count', 0),
                    "eval_duration": result.get('eval_duration', 0)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Ollama extraction failed: {e}")
    
    async def _extract_with_transformers(
        self,
        image_data: bytes,
        image_format: str,
        extract_line_items: bool,
        preferred_currency: Optional[Currency],
        start_time: float
    ) -> AIProviderResult:
        """Extract using Transformers local model."""
        try:
            # This is a placeholder for Transformers integration
            # In a real implementation, you would load a local vision-language model
            # like LLaVA, InstructBLIP, or similar
            
            # For now, we'll simulate the extraction
            await asyncio.sleep(0.1)  # Simulate processing time
            
            processing_time = time.time() - start_time
            
            # Create a basic receipt data structure
            receipt_data = ReceiptData(
                vendor_name="Local Model Extraction",
                transaction_date=datetime.now().date(),
                total_amount=0.0,
                currency=preferred_currency.value if preferred_currency else "USD",
                extraction_timestamp=datetime.now(),
                raw_extraction_text="Local model extraction not fully implemented"
            )
            
            return self._create_success_result(
                receipt_data=receipt_data,
                raw_response="Local model extraction placeholder",
                tokens_used=0,
                processing_time=processing_time,
                confidence_score=0.5,
                provider_metadata={
                    "model": self.config.model_name,
                    "model_type": "transformers",
                    "status": "placeholder"
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Transformers extraction failed: {e}")
    
    def _create_prompt(
        self,
        extract_line_items: bool,
        preferred_currency: Optional[Currency]
    ) -> str:
        """Create prompt for local model."""
        prompt_parts = [
            "Analyze this receipt image and extract the following information in JSON format:",
            "",
            "Required fields:",
            "- vendor_name: string (business name)",
            "- transaction_date: string (YYYY-MM-DD format)",
            "- total_amount: number (decimal without currency symbol)",
            "- currency: string (3-letter code like USD, EUR)",
            "",
            "Optional fields:",
            "- receipt_number: string",
            "- tax_amount: number",
            "- subtotal: number",
            "- payment_method: string",
            "- items: array of objects with name, quantity, price"
        ]
        
        if extract_line_items:
            prompt_parts.append("- Include individual line items in the items array")
        
        if preferred_currency:
            prompt_parts.append(f"- If no currency visible, use {preferred_currency.value}")
        
        prompt_parts.extend([
            "",
            "IMPORTANT:",
            "1. Return only valid JSON, no additional text",
            "2. Use null for missing information",
            "3. Be accurate and conservative"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_content: str, preferred_currency: Optional[Currency]) -> ReceiptData:
        """Parse local model response into ReceiptData."""
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
            logger.error(f"Failed to parse local model response: {e}")
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
        """Test connection to local model."""
        try:
            if self.model_type == 'ollama':
                # Test Ollama connection
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                return response.status_code == 200
            elif self.model_type == 'transformers':
                # Test if model is available locally
                return self.model_path and Path(self.model_path).exists()
            else:
                return False
        except Exception as e:
            logger.error(f"Local model connection test failed: {e}")
            return False
