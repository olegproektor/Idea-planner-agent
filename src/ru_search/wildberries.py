"""
Wildberries scraper implementation for the ru_search module.

This module implements a scraper for Wildberries public search API that collects
product listings, prices, ratings, reviews count, sales count, brand, and product URLs.
"""

import time
import random
import threading
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from .base import DataSource, Product


class WildberriesSearch(DataSource):
    """
    Wildberries data source implementation.
    
    This class implements a scraper for the Wildberries public search API with
    rate limiting, error handling, and data normalization.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Wildberries data source.
        
        Args:
            api_key: Optional API key for authentication
            **kwargs: Additional configuration parameters
        """
        super().__init__("wildberries", api_key, **kwargs)
        
        # Wildberries specific configuration
        self.base_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
        # Rate limiting for Wildberries API
        # Max 1 request per 2 seconds, max 30 requests per minute
        self._request_timestamp = 0
        self._minute_request_count = 0
        self._minute_lock = threading.Lock()
        self._last_minute = 0
        
        # Override base rate limiting settings
        self.max_concurrent_requests = 1  # More restrictive for Wildberries
        self.request_timeout = 30  # Wildberries can be slow
        self.max_retries = 5  # More retries for rate limiting
    
    def _wildberries_rate_limit(self) -> None:
        """
        Implement Wildberries-specific rate limiting.
        
        Ensures:
        - Max 1 request per 2 seconds
        - Max 30 requests per minute
        """
        current_time = time.time()
        
        # Check 2-second rule
        time_since_last = current_time - self._request_timestamp
        if time_since_last < 2.0:
            sleep_time = 2.0 - time_since_last
            time.sleep(sleep_time)
        
        # Check 30 requests per minute rule
        with self._minute_lock:
            current_minute = int(current_time // 60)
            if current_minute != self._last_minute:
                # New minute, reset counter
                self._minute_request_count = 0
                self._last_minute = current_minute
            
            if self._minute_request_count >= 30:
                # Wait until next minute
                seconds_until_next_minute = 60 - (current_time % 60)
                time.sleep(seconds_until_next_minute)
                # Reset counter for new minute
                self._minute_request_count = 0
                self._last_minute = int(time.time() // 60)
            
            self._minute_request_count += 1
        
        # Update last request timestamp
        self._request_timestamp = time.time()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Wildberries API requests.
        
        Returns:
            Dictionary of HTTP headers with User-Agent rotation
        """
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.wildberries.ru/',
            'Origin': 'https://www.wildberries.ru'
        }
    
    def _parse_product_data(self, product_data: Dict[str, Any]) -> Product:
        """
        Parse raw product data from Wildberries API response.
        
        Args:
            product_data: Raw product data dictionary
            
        Returns:
            Product object with extracted information
        """
        # Extract basic product information
        product_id = str(product_data.get('id', ''))
        title = product_data.get('name', '').strip()
        
        # Extract price information
        price = product_data.get('salePriceU', 0) / 100  # Convert from kopecks to rubles
        old_price = product_data.get('priceU', 0) / 100  # Convert from kopecks to rubles
        
        # Extract rating and reviews
        rating = product_data.get('rating', 0)
        reviews_count = product_data.get('feedback', 0)
        
        # Extract brand information
        brand = product_data.get('brand', '').strip()
        
        # Construct product URL
        product_url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
        
        # Extract additional metadata
        metadata = {
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'brand': brand,
            'sales_count': product_data.get('volume', 0),  # Sales volume
            'is_available': product_data.get('selling', False),
            'is_new': product_data.get('new', False),
            'is_sale': product_data.get('sale', False)
        }
        
        return Product(
            id=product_id,
            title=title,
            price=price,
            url=product_url,
            **metadata
        )
    
    def search(self, query: str) -> List[Product]:
        """
        Search for products on Wildberries based on the given query.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
            
        Raises:
            Exception: If search fails after maximum retries
        """
        # Prepare search parameters
        params = {
            'query': query,
            'resultset': 'catalog',
            'limit': 100,
            'sort': 'popular',  # Sort by popularity
            'currency': 'RUB',
            'dest': '-1216603',  # Moscow region by default
            'spp': 0  # Don't filter by price
        }
        
        try:
            # Make the API request
            response_data = self._make_request(
                url=self.base_url,
                method='GET',
                params=params,
                headers=self._get_headers()
            )
            
            # Extract products from response
            products = []
            raw_products = response_data.get('data', {}).get('products', [])
            
            for product_data in raw_products:
                try:
                    product = self._parse_product_data(product_data)
                    products.append(product)
                except (KeyError, TypeError, ValueError) as e:
                    # Skip malformed product entries
                    continue
            
            return products
            
        except Exception as e:
            # Handle specific rate limiting errors
            if "429" in str(e):
                # Exponential backoff for rate limiting
                retry_after = min(60, 2 ** self.max_retries)  # Max 60 seconds
                time.sleep(retry_after)
                # Try one more time
                return self.search(query)
            else:
                raise Exception(f"Wildberries search failed: {str(e)}")
    
    def get_trends(self, query: str) -> 'TrendData':
        """
        Get trend data for a specific query.
        
        Note: Wildberries doesn't provide a public trends API, so this method
        returns a basic TrendData object with limited information.
        
        Args:
            query: Query string to get trends for
            
        Returns:
            TrendData object containing trend information
        """
        from .base import TrendData
        
        # For Wildberries, we'll return a basic trend object
        # since they don't have a public trends API
        return TrendData(
            query=query,
            trend_score=0.5,  # Neutral score
            historical_data=[]  # No historical data available
        )
    
    def _make_request(self, url: str, method: str = 'GET',
                      params: Optional[Dict] = None,
                      data: Optional[Dict] = None,
                      headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request with Wildberries-specific handling.
        
        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            headers: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails after maximum retries
        """
        import requests
        from requests.exceptions import RequestException
        
        # Apply both base and Wildberries rate limiting
        super()._rate_limit()
        self._wildberries_rate_limit()
        
        # Set default headers if not provided
        if headers is None:
            headers = self._get_headers()
        else:
            # Merge with default headers
            default_headers = self._get_headers()
            for key, value in default_headers.items():
                if key not in headers:
                    headers[key] = value
        
        # Retry logic with exponential backoff for 429 errors
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Use requests.request directly to match test mocking
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
                
            except (RequestException, ValueError) as e:
                last_exception = e
                error_message = str(e)
                
                # Special handling for 429 Too Many Requests
                if "429" in error_message or "too many requests" in error_message.lower():
                    if attempt < self.max_retries - 1:
                        # Exponential backoff specifically for rate limiting
                        wait_time = min(60, (2 ** attempt) * 5)  # Max 60 seconds
                        time.sleep(wait_time)
                        continue
                
                # For other errors, use regular backoff
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 0.1
                    time.sleep(wait_time)
                
        # If we get here, all retries failed
        raise Exception(f"Request failed after {self.max_retries} attempts: {str(last_exception)}")