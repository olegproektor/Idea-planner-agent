"""
LLM (Large Language Model) module for Idea Planner Agent.

This module provides integration with various LLM providers including Groq, 
with a focus on fast, reliable inference for idea analysis and market research.

Modules:
- groq_provider: Groq API client implementation
- base: Base LLM provider interface (future)
- analysis: Idea analysis utilities (future)

Usage:
    from src.llm.groq_provider import GroqProvider
    
    client = GroqProvider(api_key="your_api_key")
    result = client.generate("Analyze this idea: ...")
"""

# Module version
__version__ = "0.1.0"

# Import main classes for easy access
from .groq_provider import GroqProvider

__all__ = ["GroqProvider"]