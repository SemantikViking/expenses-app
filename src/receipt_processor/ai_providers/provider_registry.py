"""
AI Provider Registry for Receipt Processing Application.

This module provides a registry for managing multiple AI providers and
routing requests to the appropriate provider.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from .base import BaseAIProvider, AIProviderConfig, AIProviderType, AIProviderResult
from .provider_factory import AIProviderFactory
from ..models import ReceiptData, Currency


class AIProviderRegistry:
    """Registry for managing multiple AI providers."""
    
    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_provider: Optional[str] = None
        self._provider_weights: Dict[str, float] = {}
        self._usage_stats: Dict[str, Dict[str, Any]] = {}
        
        logger.info("AI Provider Registry initialized")
    
    def register_provider(
        self, 
        name: str, 
        config: AIProviderConfig,
        weight: float = 1.0
    ) -> None:
        """
        Register a new AI provider.
        
        Args:
            name: Unique name for the provider
            config: Provider configuration
            weight: Weight for load balancing (higher = more requests)
        """
        try:
            provider = AIProviderFactory.create_provider(config)
            self._providers[name] = provider
            self._provider_weights[name] = weight
            self._usage_stats[name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_processing_time": 0.0,
                "last_used": None
            }
            
            if not self._default_provider:
                self._default_provider = name
            
            logger.info(f"Registered provider '{name}' with weight {weight}")
            
        except Exception as e:
            logger.error(f"Failed to register provider '{name}': {e}")
            raise
    
    def unregister_provider(self, name: str) -> None:
        """
        Unregister an AI provider.
        
        Args:
            name: Name of the provider to unregister
        """
        if name in self._providers:
            del self._providers[name]
            del self._provider_weights[name]
            del self._usage_stats[name]
            
            if self._default_provider == name:
                self._default_provider = next(iter(self._providers.keys()), None)
            
            logger.info(f"Unregistered provider '{name}'")
        else:
            logger.warning(f"Provider '{name}' not found for unregistration")
    
    def set_default_provider(self, name: str) -> None:
        """
        Set the default provider.
        
        Args:
            name: Name of the provider to set as default
        """
        if name in self._providers:
            self._default_provider = name
            logger.info(f"Set default provider to '{name}'")
        else:
            raise ValueError(f"Provider '{name}' not found")
    
    def get_provider(self, name: Optional[str] = None) -> BaseAIProvider:
        """
        Get a provider by name or default provider.
        
        Args:
            name: Name of the provider (None for default)
            
        Returns:
            AI provider instance
            
        Raises:
            ValueError: If provider not found
        """
        provider_name = name or self._default_provider
        
        if not provider_name:
            raise ValueError("No providers registered and no default provider set")
        
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        
        return self._providers[provider_name]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())
    
    def get_provider_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific provider."""
        if name not in self._providers:
            return None
        
        provider = self._providers[name]
        stats = self._usage_stats[name]
        
        return {
            "name": name,
            "provider_type": provider.config.provider_type,
            "model_name": provider.config.model_name,
            "capabilities": provider.get_capabilities().dict(),
            "weight": self._provider_weights[name],
            "usage_stats": stats,
            "is_default": name == self._default_provider
        }
    
    async def extract_receipt_data(
        self,
        image_data: bytes,
        provider_name: Optional[str] = None,
        image_format: str = "jpeg",
        extract_line_items: bool = False,
        preferred_currency: Optional[Currency] = None,
        **kwargs
    ) -> AIProviderResult:
        """
        Extract receipt data using the specified or default provider.
        
        Args:
            image_data: Raw image data
            provider_name: Name of provider to use (None for default)
            image_format: Format of the image
            extract_line_items: Whether to extract line items
            preferred_currency: Preferred currency
            **kwargs: Additional parameters
            
        Returns:
            AI extraction result
        """
        provider = self.get_provider(provider_name)
        provider_name = provider_name or self._default_provider
        
        # Update usage stats
        self._usage_stats[provider_name]["total_requests"] += 1
        self._usage_stats[provider_name]["last_used"] = datetime.now()
        
        try:
            result = await provider.extract_receipt_data(
                image_data=image_data,
                image_format=image_format,
                extract_line_items=extract_line_items,
                preferred_currency=preferred_currency,
                **kwargs
            )
            
            # Update success stats
            if result.success:
                self._usage_stats[provider_name]["successful_requests"] += 1
            else:
                self._usage_stats[provider_name]["failed_requests"] += 1
            
            self._usage_stats[provider_name]["total_processing_time"] += result.processing_time
            
            return result
            
        except Exception as e:
            self._usage_stats[provider_name]["failed_requests"] += 1
            logger.error(f"Provider '{provider_name}' extraction failed: {e}")
            raise
    
    async def extract_with_fallback(
        self,
        image_data: bytes,
        preferred_providers: Optional[List[str]] = None,
        **kwargs
    ) -> AIProviderResult:
        """
        Extract receipt data with fallback to other providers on failure.
        
        Args:
            image_data: Raw image data
            preferred_providers: List of preferred providers in order
            **kwargs: Additional parameters
            
        Returns:
            AI extraction result from first successful provider
        """
        providers_to_try = preferred_providers or self.get_available_providers()
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                logger.info(f"Trying provider: {provider_name}")
                result = await self.extract_receipt_data(
                    image_data=image_data,
                    provider_name=provider_name,
                    **kwargs
                )
                
                if result.success:
                    logger.info(f"Success with provider: {provider_name}")
                    return result
                else:
                    logger.warning(f"Provider {provider_name} failed: {result.error_message}")
                    
            except Exception as e:
                logger.warning(f"Provider {provider_name} error: {e}")
                last_error = e
        
        # All providers failed
        logger.error("All providers failed")
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all registered providers."""
        results = {}
        
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.test_connection()
                logger.info(f"Provider '{name}' connection test: {'PASS' if results[name] else 'FAIL'}")
            except Exception as e:
                results[name] = False
                logger.error(f"Provider '{name}' connection test failed: {e}")
        
        return results
    
    def get_usage_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all providers."""
        return self._usage_stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset usage statistics for all providers."""
        for stats in self._usage_stats.values():
            stats.update({
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_processing_time": 0.0,
                "last_used": None
            })
        
        logger.info("Usage statistics reset")
    
    def get_load_balancing_weights(self) -> Dict[str, float]:
        """Get current load balancing weights."""
        return self._provider_weights.copy()
    
    def set_load_balancing_weights(self, weights: Dict[str, float]) -> None:
        """Set load balancing weights for providers."""
        for name, weight in weights.items():
            if name in self._providers:
                self._provider_weights[name] = weight
                logger.info(f"Set weight for provider '{name}': {weight}")
            else:
                logger.warning(f"Cannot set weight for unknown provider '{name}'")
    
    def __len__(self) -> int:
        """Get number of registered providers."""
        return len(self._providers)
    
    def __contains__(self, name: str) -> bool:
        """Check if provider is registered."""
        return name in self._providers
