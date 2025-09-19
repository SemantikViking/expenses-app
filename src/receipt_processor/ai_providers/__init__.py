"""
AI Providers module for Receipt Processing Application.

This module provides a unified interface for different AI vision providers,
allowing the application to work with multiple AI services and local models.
"""

from .base import BaseAIProvider, AIProviderConfig, AIProviderResult
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .local_provider import LocalModelProvider
from .provider_factory import AIProviderFactory
from .provider_registry import AIProviderRegistry

__all__ = [
    "BaseAIProvider",
    "AIProviderConfig", 
    "AIProviderResult",
    "OpenAIProvider",
    "AnthropicProvider",
    "LocalModelProvider",
    "AIProviderFactory",
    "AIProviderRegistry"
]
