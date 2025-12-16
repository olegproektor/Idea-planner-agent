"""
Yandex integration for the ru_search module.

This module implements Yandex Wordstat for trends and Yandex Market for product listings.
For Wordstat, it uses stub data with realistic numbers since the API requires a paid key.
For Yandex Market, it implements a scraper similar to Wildberries and Ozon.
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

from .base import DataSource, Product, TrendData


class YandexSearch(DataSource):
    """
    Yandex data source implementation.
    
    This class implements:
    - Yandex Wordstat for trend analysis (using stub data)
    - Yandex Market scraper for product listings and prices
    - Rate limiting: 1 request per 2 seconds, max 30 requests per minute
    - Error handling and retry logic
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Yandex data source.
        
        Args:
            api_key: Optional API key for authentication
            **kwargs: Additional configuration parameters
        """
        super().__init__("yandex", api_key, **kwargs)
        
        # Yandex specific configuration
        self.wordstat_base_url = "https://wordstat.yandex.com"
        self.market_base_url = "https://market.yandex.ru"
        self.search_url = "https://market.yandex.ru/search"
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
        # Rate limiting for Yandex
        # Max 1 request per 2 seconds, max 30 requests per minute
        self._request_timestamp = 0
        self._minute_request_count = 0
        self._minute_lock = threading.Lock()
        self._last_minute = 0
        
        # Override base rate limiting settings
        self.max_concurrent_requests = 1  # More restrictive for Yandex
        self.request_timeout = 30  # Yandex can be slow
        self.max_retries = 5  # More retries for rate limiting

    def _yandex_rate_limit(self) -> None:
        """
        Implement Yandex-specific rate limiting.
        
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
        Get headers for Yandex requests.
        
        Returns:
            Dictionary of HTTP headers with User-Agent rotation
        """
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://market.yandex.ru/',
            'Origin': 'https://market.yandex.ru'
        }

    def _generate_wordstat_stub_data(self, query: str) -> TrendData:
        """
        Generate realistic stub data for Yandex Wordstat trends.
        
        Since the Wordstat API requires a paid key, this method generates
        realistic-looking trend data based on the query.
        
        Args:
            query: Search query string
            
        Returns:
            TrendData object with realistic stub data
        """
        # Generate a realistic trend score based on query length and content
        # Longer queries and queries with common product terms get higher scores
        base_score = 0.3
        
        # Add score based on query length
        query_length_factor = min(len(query) / 20, 0.4)  # Max 0.4 for long queries
        base_score += query_length_factor
        
        # Add score for common product-related terms
        product_terms = ['купить', 'цена', 'дешево', 'скидка', 'распродажа', 
                        'новый', 'лучший', 'отзывы', 'рейтинг', 'топ']
        for term in product_terms:
            if term in query.lower():
                base_score += 0.1
                break
        
        # Cap the score at 0.9 (realistic maximum)
        trend_score = min(base_score, 0.9)
        
        # Generate historical data for the past 12 months
        historical_data = []
        current_month = time.strftime('%Y-%m')
        
        for i in range(12):
            # Generate month in format YYYY-MM
            month = f"{int(current_month[:4]) - (i // 12)}-{str(12 - i % 12).zfill(2)}"
            
            # Generate realistic search volume with some seasonality
            # Higher volumes in recent months, with some random variation
            base_volume = 1000 + (i * 50)  # Increasing trend
            seasonal_factor = 1.0 + (random.random() * 0.3 - 0.15)  # ±15% randomness
            volume = int(base_volume * seasonal_factor * trend_score * 10)  # Scale by trend score
            
            historical_data.append({
                'month': month,
                'search_volume': volume,
                'trend_index': trend_score * (0.8 + random.random() * 0.4)  # Some variation
            })
        
        # Reverse to show chronological order (oldest first)
        historical_data.reverse()
        
        return TrendData(
            query=query,
            trend_score=trend_score,
            historical_data=historical_data
        )

    def get_trends(self, query: str) -> TrendData:
        """
        Get trend data for a specific query using Yandex Wordstat.
        
        Since the Wordstat API requires a paid key, this implementation
        uses realistic stub data generation.
        
        Args:
            query: Query string to get trends for
            
        Returns:
            TrendData object containing trend information
        """
        # Apply Yandex-specific rate limiting
        self._yandex_rate_limit()
        
        try:
            # For now, use stub data since Wordstat API requires paid key
            # In a production environment, you would implement actual API calls
            # or use a free proxy/scraper if available
            return self._generate_wordstat_stub_data(query)
            
        except Exception as e:
            # Fallback to basic trend data if stub generation fails
            return TrendData(
                query=query,
                trend_score=0.5,  # Neutral score
                historical_data=[]  # No historical data
            )

    def _scrape_yandex_market(self, query: str) -> List[Product]:
        """
        Scrape Yandex Market for product listings.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
        """
        # Apply Yandex-specific rate limiting
        self._yandex_rate_limit()
        
        # Prepare search URL
        search_url = f"{self.search_url}?text={quote(query)}"
        
        try:
            # Make the web request
            response = requests.get(
                search_url,
                headers=self._get_headers(),
                timeout=self.request_timeout
            )
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse HTML to extract product data
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for product containers - Yandex Market uses specific classes
            product_containers = soup.find_all('div', class_='n-snippet-card2')
            
            products = []
            
            for container in product_containers:
                try:
                    product = self._parse_yandex_product(container)
                    if product:
                        products.append(product)
                except (KeyError, TypeError, ValueError, AttributeError) as e:
                    # Skip malformed product entries
                    continue
            
            return products
            
        except Exception as e:
            raise Exception(f"Yandex Market scraping failed: {str(e)}")

    def _parse_yandex_product(self, product_container) -> Optional[Product]:
        """
        Parse a Yandex Market product container to extract product data.
        
        Args:
            product_container: BeautifulSoup container with product data
            
        Returns:
            Product object with extracted information, or None if parsing fails
        """
        try:
            # Extract product ID - try to find from URL or data attributes
            product_url_tag = product_container.find('a', class_='n-snippet-card2__title')
            if not product_url_tag or not product_url_tag.get('href'):
                return None
            
            product_url = product_url_tag['href']
            if not product_url.startswith('http'):
                product_url = f"https://market.yandex.ru{product_url}"
            
            # Extract product ID from URL
            product_id = product_url.split('/')[-1].split('?')[0]
            
            # Extract title
            title_tag = product_container.find('h3', class_='n-snippet-card2__title')
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Extract price
            price_tag = product_container.find('div', class_='n-snippet-card2__price')
            price_text = price_tag.get_text(strip=True) if price_tag else "0"
            
            # Clean price text and convert to float
            price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
            try:
                price = float(price_clean) if price_clean else 0.0
            except ValueError:
                price = 0.0
            
            # Extract rating
            rating_tag = product_container.find('div', class_='n-snippet-card2__rating')
            rating_text = rating_tag.get_text(strip=True) if rating_tag else "0"
            try:
                rating = float(rating_text.replace(',', '.')) if rating_text else 0.0
            except ValueError:
                rating = 0.0
            
            # Extract reviews count
            reviews_tag = product_container.find('span', class_='n-snippet-card2__rating-count')
            reviews_text = reviews_tag.get_text(strip=True) if reviews_tag else "0"
            try:
                reviews_count = int(''.join(c for c in reviews_text if c.isdigit()))
            except ValueError:
                reviews_count = 0
            
            # Extract brand
            brand_tag = product_container.find('div', class_='n-snippet-card2__brand')
            brand = brand_tag.get_text(strip=True) if brand_tag else ""
            
            # Extract additional metadata
            metadata = {
                'rating': rating,
                'reviews_count': reviews_count,
                'brand': brand,
                'is_available': True,  # Assume available if listed
                'source': 'yandex_market'
            }
            
            return Product(
                id=product_id,
                title=title,
                price=price,
                url=product_url,
                **metadata
            )
            
        except Exception as e:
            # If any parsing fails, return None
            return None

    def search(self, query: str) -> List[Product]:
        """
        Search for products on Yandex Market based on the given query.
        
        Args:
            query: Search query string
            
        Returns:
            List of Product objects matching the search query
            
        Raises:
            Exception: If search fails after maximum retries
        """
        try:
            # Use Yandex Market scraper
            return self._scrape_yandex_market(query)
            
        except Exception as e:
            # Handle specific rate limiting errors
            if "429" in str(e):
                # Exponential backoff for rate limiting
                retry_after = min(60, 2 ** self.max_retries)  # Max 60 seconds
                time.sleep(retry_after)
                # Try one more time
                return self.search(query)
            else:
                raise Exception(f"Yandex search failed: {str(e)}")

    def _make_request(self, url: str, method: str = 'GET',
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request with Yandex-specific handling.
        
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
        # Apply both base and Yandex rate limiting
        super()._rate_limit()
        self._yandex_rate_limit()
        
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
        raise Exception(f"Yandex request failed after {self.max_retries} attempts: {str(last_exception)}")