"""
Ozon scraper implementation for the ru_search module.

This module implements a scraper for Ozon marketplace that collects
product listings, prices, ratings, reviews count, brand, and product URLs.
It supports both API-based and web scraping approaches with proper rate limiting.
"""

import time
import random
import threading
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from .base import DataSource, Product


class OzonSearch(DataSource):
    """
    Ozon data source implementation.
    
    This class implements a scraper for Ozon marketplace with support for:
    - Public API (if available)
    - Web scraping fallback using requests and BeautifulSoup
    - Rate limiting: 1 request per 2 seconds, max 30 requests per minute
    - Error handling and retry logic
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Ozon data source.
        
        Args:
            api_key: Optional API key for authentication
            **kwargs: Additional configuration parameters
        """
        super().__init__("ozon", api_key, **kwargs)
        
        # Ozon specific configuration
        self.base_api_url = "https://api-seller.ozon.ru/v1/product/info"
        self.base_search_url = "https://www.ozon.ru/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
        # Rate limiting for Ozon
        # Max 1 request per 2 seconds, max 30 requests per minute
        self._request_timestamp = 0
        self._minute_request_count = 0
        self._minute_lock = threading.Lock()
        self._last_minute = 0
        
        # Override base rate limiting settings
        self.max_concurrent_requests = 1  # More restrictive for Ozon
        self.request_timeout = 30  # Ozon can be slow
        self.max_retries = 5  # More retries for rate limiting
        
        # Track if API is available
        self._api_available = True
    
    def _ozon_rate_limit(self) -> None:
        """
        Implement Ozon-specific rate limiting.
        
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
        Get headers for Ozon requests.
        
        Returns:
            Dictionary of HTTP headers with User-Agent rotation
        """
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.ozon.ru/',
            'Origin': 'https://www.ozon.ru'
        }
    
    def _try_api_search(self, query: str) -> Optional[List[Product]]:
        """
        Attempt to use Ozon public API for search.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects if API is available, None otherwise
        """
        try:
            # Check if API is available by making a test request
            test_url = f"{self.base_api_url}"
            test_params = {'query': query, 'limit': 1}
            
            response = requests.get(
                test_url,
                params=test_params,
                headers=self._get_headers(),
                timeout=10
            )
            
            # If we get a successful response, API is available
            if response.status_code == 200:
                self._api_available = True
                return self._api_search(query)
            else:
                # API not available or requires authentication
                self._api_available = False
                return None
                
        except RequestException:
            # API request failed, fall back to web scraping
            self._api_available = False
            return None
    
    def _api_search(self, query: str) -> List[Product]:
        """
        Search for products using Ozon API.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
        """
        # Apply Ozon-specific rate limiting
        self._ozon_rate_limit()
        
        # Prepare search parameters
        params = {
            'query': query,
            'limit': 100,
            'sort': 'popular',  # Sort by popularity
            'currency': 'RUB',
        }
        
        try:
            # Make the API request
            response_data = self._make_request(
                url=self.base_api_url,
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
            # If API fails, mark as unavailable and fall back to web scraping
            self._api_available = False
            raise Exception(f"Ozon API search failed: {str(e)}")
    
    def _web_scrape_search(self, query: str) -> List[Product]:
        """
        Search for products using web scraping (fallback method).
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
        """
        # Apply Ozon-specific rate limiting
        self._ozon_rate_limit()
        
        # Prepare search URL
        search_url = f"{self.base_search_url}?text={quote(query)}"
        
        try:
            # Make the web request
            response = requests.get(
                search_url,
                headers=self._get_headers(),
                timeout=self.request_timeout
            )
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse HTML to extract JSON data
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the NEXT_DATA script tag
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if not next_data_script:
                raise Exception("Could not find __NEXT_DATA__ script tag")
            
            # Extract and parse JSON data
            json_data = json.loads(next_data_script.string)
            
            # Extract products from the JSON structure
            products = []
            search_results = json_data.get('props', {}).get('pageProps', {}).get('searchResults', {})
            
            if not search_results:
                # Try alternative path for search results
                search_results = json_data.get('props', {}).get('initialState', {}).get('search', {})
            
            raw_products = search_results.get('items', [])
            
            for product_data in raw_products:
                try:
                    product = self._parse_web_product_data(product_data)
                    products.append(product)
                except (KeyError, TypeError, ValueError) as e:
                    # Skip malformed product entries
                    continue
            
            return products
            
        except Exception as e:
            raise Exception(f"Ozon web scraping failed: {str(e)}")
    
    def _parse_product_data(self, product_data: Dict[str, Any]) -> Product:
        """
        Parse raw product data from Ozon API response.
        
        Args:
            product_data: Raw product data dictionary
            
        Returns:
            Product object with extracted information
        """
        # Extract basic product information
        product_id = str(product_data.get('id', product_data.get('productId', '')))
        title = product_data.get('name', product_data.get('title', '')).strip()
        
        # Extract price information
        price = product_data.get('price', {}).get('price', 0) / 100  # Convert from kopecks to rubles
        old_price = product_data.get('price', {}).get('oldPrice', 0) / 100  # Convert from kopecks to rubles
        
        # Extract rating and reviews
        rating = product_data.get('rating', {}).get('rating', 0)
        reviews_count = product_data.get('rating', {}).get('count', 0)
        
        # Extract brand information
        brand = product_data.get('brand', {}).get('name', '').strip()
        
        # Construct product URL
        product_url = f"https://www.ozon.ru/product/{product_id}/"
        
        # Extract additional metadata
        metadata = {
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'brand': brand,
            'is_available': product_data.get('isAvailable', False),
            'is_new': product_data.get('isNew', False),
            'is_sale': product_data.get('isSale', False)
        }
        
        return Product(
            id=product_id,
            title=title,
            price=price,
            url=product_url,
            **metadata
        )
    
    def _parse_web_product_data(self, product_data: Dict[str, Any]) -> Product:
        """
        Parse raw product data from Ozon web scraping (NEXT_DATA JSON).
        
        Args:
            product_data: Raw product data dictionary from web scraping
            
        Returns:
            Product object with extracted information
        """
        # Extract basic product information
        product_id = str(product_data.get('id', product_data.get('productId', '')))
        title = product_data.get('title', product_data.get('name', '')).strip()
        
        # Extract price information
        price_info = product_data.get('price', {})
        if isinstance(price_info, dict):
            price = price_info.get('price', 0) / 100  # Convert from kopecks to rubles
            old_price = price_info.get('oldPrice', 0) / 100  # Convert from kopecks to rubles
        else:
            price = price_info / 100 if price_info else 0
            old_price = 0
        
        # Extract rating and reviews
        rating_info = product_data.get('rating', {})
        if isinstance(rating_info, dict):
            rating = rating_info.get('rating', 0)
            reviews_count = rating_info.get('count', 0)
        else:
            rating = rating_info if rating_info else 0
            reviews_count = 0
        
        # Extract brand information
        brand_info = product_data.get('brand', {})
        brand = brand_info.get('name', '') if isinstance(brand_info, dict) else brand_info
        brand = str(brand).strip()
        
        # Construct product URL
        product_url = f"https://www.ozon.ru/product/{product_id}/"
        
        # Extract additional metadata
        metadata = {
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'brand': brand,
            'is_available': product_data.get('available', False),
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
        Search for products on Ozon based on the given query.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
            
        Raises:
            Exception: If search fails after maximum retries
        """
        try:
            # First try API if available
            if self._api_available:
                try:
                    products = self._try_api_search(query)
                    if products is not None:
                        return products
                except Exception:
                    pass  # Fall through to web scraping
            
            # Fall back to web scraping
            return self._web_scrape_search(query)
            
        except Exception as e:
            # Handle specific rate limiting errors
            if "429" in str(e):
                # Exponential backoff for rate limiting
                retry_after = min(60, 2 ** self.max_retries)  # Max 60 seconds
                time.sleep(retry_after)
                # Try one more time
                return self.search(query)
            else:
                raise Exception(f"Ozon search failed: {str(e)}")
    
    def get_trends(self, query: str) -> 'TrendData':
        """
        Get trend data for a specific query.
        
        Note: Ozon doesn't provide a public trends API, so this method
        returns a basic TrendData object with limited information.
        
        Args:
            query: Query string to get trends for
            
        Returns:
            TrendData object containing trend information
        """
        from .base import TrendData
        
        # For Ozon, we'll return a basic trend object
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
        Make an HTTP request with Ozon-specific handling.
        
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
        # Apply both base and Ozon rate limiting
        super()._rate_limit()
        self._ozon_rate_limit()
        
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
                response = super()._make_request(
                    url=url,
                    method=method,
                    params=params,
                    data=data,
                    headers=headers
                )
                
                return response
                
            except Exception as e:
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
        raise Exception(f"Ozon request failed after {self.max_retries} attempts: {str(last_exception)}")