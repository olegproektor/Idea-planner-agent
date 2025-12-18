"""
Wildberries Public API implementation for the ru_search module.

This module implements a client for Wildberries public search API that collects
product listings, prices, ratings, reviews count, sales count, brand, and product URLs.
"""

import time
import random
import threading
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from .base import DataSource, Product


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WildberriesPublicAPI(DataSource):
    """
    Wildberries data source implementation using the public API.
    
    This class implements a client for the Wildberries public search API with
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
        
        # Wildberries public API configuration
        self.base_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
        self.user_agent = "idea-planner-agent/0.1.0"
        
        # Rate limiting for Wildberries API - 1 request per second
        self._last_request_time = 0
        self._lock = threading.Lock()
        
        # Override base rate limiting settings for Wildberries
        self.max_concurrent_requests = 1  # Strict rate limiting
        self.request_timeout = 30  # Wildberries can be slow
        self.max_retries = 5  # More retries for rate limiting

    def _rate_limit(self) -> None:
        """
        Implement Wildberries-specific rate limiting.
        
        Ensures maximum 1 request per second as required by the API.
        """
        current_time = time.time()
        
        with self._lock:
            time_since_last = current_time - self._last_request_time
            if time_since_last < 1.0:
                sleep_time = 1.0 - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f} seconds")
                time.sleep(sleep_time)
            
            # Update last request timestamp
            self._last_request_time = time.time()

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Wildberries API requests.
        
        Returns:
            Dictionary of HTTP headers with required User-Agent
        """
        return {
            'User-Agent': self.user_agent,
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
        try:
            # Extract basic product information
            product_id = str(product_data.get('id', ''))
            title = product_data.get('name', '').strip()
            
            # Extract price information (convert from kopecks to rubles)
            price = product_data.get('salePriceU', 0) / 100
            old_price = product_data.get('priceU', 0) / 100
            
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
        except Exception as e:
            logger.error(f"Failed to parse product data: {e}")
            raise ValueError(f"Failed to parse product data: {e}")

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
                    logger.warning(f"Skipping malformed product: {e}")
                    continue
            
            logger.info(f"Found {len(products)} products for query: '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"Wildberries search failed: {e}")
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
            headers: Request headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails after maximum retries
        """
        import requests
        from requests.exceptions import RequestException
        
        # Apply both base and Wildberries rate limiting
        super()._rate_limit()
        self._rate_limit()
        
        # Set default headers if not provided
        if headers is None:
            headers = self._get_headers()
        else:
            # Merge with default headers
            default_headers = self._get_headers()
            for key, value in default_headers.items():
                if key not in headers:
                    headers[key] = value
        
        # Retry logic with exponential backoff for 403/429 errors
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
                
                # Special handling for 403 Forbidden and 429 Too Many Requests
                if "403" in error_message or "429" in error_message or \
                   "too many requests" in error_message.lower() or \
                   "forbidden" in error_message.lower():
                    if attempt < self.max_retries - 1:
                        # Exponential backoff specifically for rate limiting/forbidden errors
                        wait_time = min(60, (2 ** attempt) * 5)  # Max 60 seconds
                        logger.warning(f"Rate limited/forbidden (attempt {attempt + 1}/{self.max_retries}), retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                
                # For other errors, use regular backoff
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 0.1
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}), retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                
        # If we get here, all retries failed
        error_msg = f"Request failed after {self.max_retries} attempts: {str(last_exception)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# Maintain backward compatibility by aliasing the old class name
WildberriesSearch = WildberriesPublicAPI