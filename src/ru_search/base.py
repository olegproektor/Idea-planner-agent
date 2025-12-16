"""
Abstract base class for data sources in the ru_search module.

This module defines the DataSource abstract base class that provides
the foundation for all data source implementations, including methods
for search, trend analysis, rate limiting, and response normalization.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError
import requests
from requests.exceptions import RequestException


class Product:
    """Data class representing a product from search results."""
    
    def __init__(self, id: str, title: str, price: float, url: str, **kwargs):
        self.id = id
        self.title = title
        self.price = price
        self.url = url
        self.metadata = kwargs
    
    def __repr__(self):
        return f"Product(id='{self.id}', title='{self.title}', price={self.price}, url='{self.url}')"


class TrendData:
    """Data class representing trend data."""
    
    def __init__(self, query: str, trend_score: float, historical_data: List[Dict[str, Any]]):
        self.query = query
        self.trend_score = trend_score
        self.historical_data = historical_data
    
    def __repr__(self):
        return f"TrendData(query='{self.query}', trend_score={self.trend_score}, historical_data={len(self.historical_data)} items)"


class DataSource(ABC):
    """
    Abstract base class for data sources.
    
    All concrete data source implementations must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, source_name: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the data source.
        
        Args:
            source_name: Name of the data source
            api_key: Optional API key for authentication
            **kwargs: Additional configuration parameters
        """
        self.source_name = source_name
        self.api_key = api_key
        self.config = kwargs
        
        # Rate limiting configuration
        self.max_concurrent_requests = 3
        self.request_timeout = 10  # seconds
        self.max_retries = 3
        
        # Thread pool for concurrent requests
        self._executor = ThreadPoolExecutor(max_workers=self.max_concurrent_requests)
        
        # Rate limiting tracking
        self._request_count = 0
        self._last_request_time = 0
        self._lock = threading.Lock()
    
    @abstractmethod
    def search(self, query: str) -> List[Product]:
        """
        Search for products based on the given query.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
            
        Raises:
            Exception: If search fails after maximum retries
        """
        pass
    
    @abstractmethod
    def get_trends(self, query: str) -> TrendData:
        """
        Get trend data for a specific query.
        
        Args:
            query: Query string to get trends for
            
        Returns:
            TrendData object containing trend information
            
        Raises:
            Exception: If trend data retrieval fails after maximum retries
        """
        pass
    
    def _rate_limit(self) -> None:
        """
        Implement rate limiting to ensure no more than max_concurrent_requests
        are active at the same time.
        
        This method uses a simple token bucket approach to limit the rate
        of requests.
        """
        with self._lock:
            current_time = time.time()
            
            # If this is the first request or enough time has passed, reset counter
            if self._last_request_time == 0 or (current_time - self._last_request_time) > 1.0:
                self._request_count = 0
                self._last_request_time = current_time
            
            # Increment request count
            self._request_count += 1
            
            # If we've hit the limit, wait
            if self._request_count > self.max_concurrent_requests:
                time.sleep(1.0)  # Wait 1 second before allowing more requests
                self._request_count = 0
                self._last_request_time = time.time()
    
    def _normalize_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the raw response data from the API to a consistent format.
        
        Args:
            raw_data: Raw data from the API response
            
        Returns:
            Normalized data dictionary with consistent structure
        """
        # Basic normalization - can be overridden by subclasses
        normalized = {
            'source': self.source_name,
            'timestamp': time.time(),
            'data': raw_data.get('data', raw_data),
            'metadata': raw_data.get('metadata', {})
        }
        return normalized
    
    def _make_request(self, url: str, method: str = 'GET', 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, 
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting, timeout, and retry logic.
        
        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            headers: Request headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails after maximum retries
        """
        # Apply rate limiting
        self._rate_limit()
        
        # Set default headers
        if headers is None:
            headers = {}
        
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        
        headers['User-Agent'] = f"ru_search/{self.source_name}"
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=self.request_timeout
                )
                
                # Check for successful response
                response.raise_for_status()
                
                # Parse and normalize response
                result = response.json()
                return self._normalize_response(result)
                
            except (RequestException, ConcurrentTimeoutError, ValueError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 0.1
                    time.sleep(wait_time)
                continue
        
        # If we get here, all retries failed
        raise Exception(f"Request failed after {self.max_retries} attempts: {str(last_exception)}")
    
    def close(self):
        """Clean up resources."""
        self._executor.shutdown(wait=True)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up resources."""
        self.close()