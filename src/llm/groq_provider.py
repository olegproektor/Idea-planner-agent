"""
Groq API provider for Idea Planner Agent.

This module implements a robust Groq API client with retry logic, rate limiting awareness,
and comprehensive error handling for reliable LLM inference.

Features:
- Automatic retry with exponential backoff (tenacity)
- Rate limiting awareness (30 req/min)
- Timeout handling (90s default)
- Context manager support
- Comprehensive logging
- Russian language support

Example:
    from src.llm.groq_provider import GroqProvider
    
    # Initialize client
    client = GroqProvider(api_key="your_api_key")
    
    # Generate text
    result = client.generate(
        prompt="Analyze this business idea:",
        max_tokens=500,
        temperature=0.7,
        system_prompt="You are a helpful business analyst."
    )
    
    # Use as context manager
    with GroqProvider(api_key="your_api_key") as client:
        result = client.generate("Hello!")
"""

import os
import time
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqProvider:
    """
    Groq API client for LLM inference.
    
    Provides reliable access to Groq's fast LLM API with built-in retry logic,
    rate limiting awareness, and comprehensive error handling.
    """
    
    # Default configuration
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_TIMEOUT = 90  # seconds
    MAX_RETRIES = 3
    RATE_LIMIT = 30  # requests per minute
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_retries: int = MAX_RETRIES,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize Groq API client.
        
        Args:
            api_key: Groq API key (uses GROQ_API_KEY env var if None)
            model: Model name (default: llama-3.3-70b-versatile)
            max_retries: Maximum retry attempts (default: 3)
            timeout: Request timeout in seconds (default: 90)
            
        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        # Set API key (env var takes precedence)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key not provided. "
                "Set GROQ_API_KEY environment variable or pass api_key parameter."
            )
        
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_url = "https://api.groq.com/openai/v1"
        
        # Rate limiting tracking
        self._last_request_time = 0
        self._minute_request_count = 0
        self._minute_lock = None  # Will be initialized in first request
        
        # Initialize headers
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "idea-planner-agent/0.1.0"
        }
        
        logger.info(f"GroqProvider initialized with model: {self.model}")
        logger.info(f"Rate limit: {self.RATE_LIMIT} req/min, Timeout: {self.timeout}s")
        
    def _rate_limit(self) -> None:
        """
        Implement rate limiting awareness.
        
        Tracks requests per minute to avoid hitting Groq's rate limits.
        Note: This is awareness only - actual rate limiting is handled by Groq.
        """
        current_time = time.time()
        current_minute = int(current_time // 60)
        
        # Initialize lock if needed
        if self._minute_lock is None:
            import threading
            self._minute_lock = threading.Lock()
        
        with self._minute_lock:
            # Reset counter if new minute
            if hasattr(self, '_last_minute') and current_minute != self._last_minute:
                self._minute_request_count = 0
                self._last_minute = current_minute
            elif not hasattr(self, '_last_minute'):
                self._last_minute = current_minute
            
            self._minute_request_count += 1
            
            # Log warning if approaching rate limit
            if self._minute_request_count >= self.RATE_LIMIT * 0.8:
                logger.warning(
                    f"Approaching Groq rate limit: {self._minute_request_count}/{self.RATE_LIMIT} "
                    f"requests this minute"
                )
            
            self._last_request_time = current_time
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            ConnectionError,
            TimeoutError
        )),
        reraise=True
    )
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated request to Groq API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "/chat/completions")
            data: Request payload
            
        Returns:
            API response as dictionary
            
        Raises:
            RetryError: If all retry attempts fail
            Exception: For other errors with context
        """
        url = f"{self.base_url}{endpoint}"
        
        # Apply rate limiting awareness
        self._rate_limit()
        
        try:
            response = requests.post(
                url,
                headers=self._headers,
                json=data,
                timeout=self.timeout
            )
            
            # Check for successful response
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Groq API request failed: {str(e)}"
            logger.error(error_msg)
            
            # Add context about rate limiting if applicable
            if "rate limit" in str(e).lower():
                error_msg += f" (Rate limit: {self.RATE_LIMIT} req/min)"
            
            raise Exception(error_msg) from e
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Groq API.
        
        Args:
            prompt: Input prompt for the model
            max_tokens: Maximum tokens to generate (default: 1000)
            temperature: Sampling temperature (0.0-1.0, default: 0.7)
            system_prompt: System message to guide model behavior
            **kwargs: Additional API parameters
            
        Returns:
            Dictionary containing:
            - 'text': Generated text
            - 'tokens_used': Total tokens used
            - 'model': Model used
            - 'timestamp': Request timestamp
            - 'raw_response': Full API response
            
        Raises:
            Exception: If generation fails after retries
        """
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request data
        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        logger.info(f"Generating with model: {self.model}, tokens: {max_tokens}")
        
        try:
            # Make API request
            start_time = time.time()
            response = self._make_request("/chat/completions", request_data)
            end_time = time.time()
            
            # Extract result
            choice = response["choices"][0]
            generated_text = choice["message"]["content"]
            
            # Calculate tokens used
            prompt_tokens = response["usage"]["prompt_tokens"]
            completion_tokens = response["usage"]["completion_tokens"]
            total_tokens = prompt_tokens + completion_tokens
            
            # Prepare result
            result = {
                "text": generated_text,
                "tokens_used": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat(),
                "latency": end_time - start_time,
                "raw_response": response
            }
            
            logger.info(
                f"Generated {len(generated_text)} chars in {result['latency']:.2f}s, "
                f"tokens: {total_tokens}"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Text generation failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Clean up resources if needed
        pass
    
    def __repr__(self):
        """String representation."""
        return f"GroqProvider(model={self.model}, timeout={self.timeout}s)"


if __name__ == "__main__":
    """Smoke test for GroqProvider."""
    import sys
    
    try:
        # Check if API key is available
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY environment variable not set")
            sys.exit(1)
        
        # Initialize client
        print("🔧 Initializing GroqProvider...")
        client = GroqProvider(api_key=api_key)
        
        # Test generation
        print("🤖 Testing generation...")
        result = client.generate(
            prompt="Скажи Привет!",
            max_tokens=50,
            temperature=0.7
        )
        
        # Print results
        print(f"✅ Success! Generated: {result['text'][:100]}...")
        print(f"📊 Tokens used: {result['tokens_used']}")
        print(f"⏱️  Latency: {result['latency']:.2f}s")
        print(f"🎯 Model: {result['model']}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)