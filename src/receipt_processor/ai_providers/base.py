"""
Base AI Provider interface for Receipt Processing Application.

This module defines the abstract base class and common types for AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from ..models import ReceiptData, Currency


class AIProviderType(str, Enum):
    """Supported AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    AZURE_OPENAI = "azure_openai"
    GOOGLE_VERTEX = "google_vertex"
    AWS_BEDROCK = "aws_bedrock"


class AIProviderCapabilities(BaseModel):
    """Capabilities of an AI provider."""
    supports_vision: bool = True
    supports_streaming: bool = False
    supports_function_calling: bool = True
    max_tokens: int = 4096
    max_image_size: int = 2048
    supported_formats: List[str] = Field(default_factory=lambda: ["jpeg", "png", "webp"])
    cost_per_token: Optional[float] = None
    cost_per_image: Optional[float] = None


class AIProviderConfig(BaseModel):
    """Configuration for an AI provider."""
    provider_type: AIProviderType
    model_name: str
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    model_parameters: Dict[str, Any] = Field(default_factory=dict)


class AIProviderResult(BaseModel):
    """Result from an AI provider."""
    success: bool
    receipt_data: Optional[ReceiptData] = None
    raw_response: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time: float = 0.0
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.capabilities = self._get_capabilities()
        self._validate_config()
    
    @abstractmethod
    def _get_capabilities(self) -> AIProviderCapabilities:
        """Get the capabilities of this provider."""
        pass
    
    @abstractmethod
    async def extract_receipt_data(
        self,
        image_data: bytes,
        image_format: str = "jpeg",
        extract_line_items: bool = False,
        preferred_currency: Optional[Currency] = None,
        **kwargs
    ) -> AIProviderResult:
        """
        Extract receipt data from an image.
        
        Args:
            image_data: Raw image data
            image_format: Format of the image (jpeg, png, etc.)
            extract_line_items: Whether to extract individual line items
            preferred_currency: Preferred currency if none detected
            **kwargs: Additional provider-specific parameters
            
        Returns:
            AIProviderResult with extracted data
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the AI provider."""
        pass
    
    def _validate_config(self) -> None:
        """Validate provider configuration."""
        if not self.config.model_name:
            raise ValueError("Model name is required")
        
        if self.config.provider_type in [AIProviderType.OPENAI, AIProviderType.ANTHROPIC]:
            if not self.config.api_key:
                raise ValueError(f"API key is required for {self.config.provider_type}")
    
    def get_capabilities(self) -> AIProviderCapabilities:
        """Get provider capabilities."""
        return self.capabilities
    
    def get_config(self) -> AIProviderConfig:
        """Get provider configuration."""
        return self.config
    
    def estimate_cost(self, tokens_used: int, images_processed: int = 1) -> Optional[float]:
        """Estimate cost for the operation."""
        if not self.capabilities.cost_per_token:
            return None
        
        cost = 0.0
        if self.capabilities.cost_per_token:
            cost += tokens_used * self.capabilities.cost_per_token
        if self.capabilities.cost_per_image:
            cost += images_processed * self.capabilities.cost_per_image
        
        return cost
    
    def _create_error_result(
        self,
        error_message: str,
        error_code: str = "PROVIDER_ERROR",
        processing_time: float = 0.0
    ) -> AIProviderResult:
        """Create an error result."""
        return AIProviderResult(
            success=False,
            error_message=error_message,
            error_code=error_code,
            processing_time=processing_time
        )
    
    def _create_success_result(
        self,
        receipt_data: ReceiptData,
        raw_response: Optional[str] = None,
        tokens_used: Optional[int] = None,
        processing_time: float = 0.0,
        confidence_score: float = 0.0,
        provider_metadata: Optional[Dict[str, Any]] = None
    ) -> AIProviderResult:
        """Create a success result."""
        return AIProviderResult(
            success=True,
            receipt_data=receipt_data,
            raw_response=raw_response,
            tokens_used=tokens_used,
            processing_time=processing_time,
            confidence_score=confidence_score,
            provider_metadata=provider_metadata or {}
        )
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.config.provider_type}:{self.config.model_name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"
