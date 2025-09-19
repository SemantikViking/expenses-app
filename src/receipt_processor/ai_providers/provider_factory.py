"""
AI Provider Factory for Receipt Processing Application.

This module provides a factory for creating AI providers based on configuration.
"""

from typing import Dict, Type, Optional
from loguru import logger

from .base import BaseAIProvider, AIProviderConfig, AIProviderType
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .local_provider import LocalModelProvider


class AIProviderFactory:
    """Factory for creating AI providers."""
    
    _providers: Dict[AIProviderType, Type[BaseAIProvider]] = {
        AIProviderType.OPENAI: OpenAIProvider,
        AIProviderType.ANTHROPIC: AnthropicProvider,
        AIProviderType.LOCAL: LocalModelProvider,
    }
    
    @classmethod
    def create_provider(cls, config: AIProviderConfig) -> BaseAIProvider:
        """
        Create an AI provider based on configuration.
        
        Args:
            config: Provider configuration
            
        Returns:
            Configured AI provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_class = cls._providers.get(config.provider_type)
        
        if not provider_class:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")
        
        try:
            provider = provider_class(config)
            logger.info(f"Created {config.provider_type} provider with model: {config.model_name}")
            return provider
        except Exception as e:
            logger.error(f"Failed to create {config.provider_type} provider: {e}")
            raise
    
    @classmethod
    def register_provider(
        cls, 
        provider_type: AIProviderType, 
        provider_class: Type[BaseAIProvider]
    ) -> None:
        """
        Register a new provider type.
        
        Args:
            provider_type: Type of provider
            provider_class: Provider class implementation
        """
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered provider type: {provider_type}")
    
    @classmethod
    def get_supported_providers(cls) -> list[AIProviderType]:
        """Get list of supported provider types."""
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_supported(cls, provider_type: AIProviderType) -> bool:
        """Check if a provider type is supported."""
        return provider_type in cls._providers
    
    @classmethod
    def get_provider_class(cls, provider_type: AIProviderType) -> Optional[Type[BaseAIProvider]]:
        """Get provider class for a given type."""
        return cls._providers.get(provider_type)
