"""
Google Trends API integration for the ru_search module.

This module implements GoogleTrendsAPI class that replaces Yandex Wordstat functionality
using the pytrends library. It provides trend analysis for the Russian market with proper
rate limiting, error handling, and caching support.
"""

import time
import threading
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

import pandas as pd
from pytrends.request import TrendReq

from .base import DataSource, Product, TrendData
from .cache import SearchCache


class GoogleTrendsAPI(DataSource):
    """
    Google Trends API implementation for market trend analysis.
    
    This class replaces Yandex Wordstat functionality and provides:
    - Interest over time data for Russian market
    - Related queries (rising and top queries)
    - Rate limiting and quota handling
    - Caching to avoid repeated API calls
    - Comprehensive error handling and logging
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Google Trends API.
        
        Args:
            api_key: Optional API key (not used for Google Trends, but kept for interface compatibility)
            **kwargs: Additional configuration parameters
        """
        # Configure logging first
        self.logger = logging.getLogger('GoogleTrendsAPI')
        self.logger.setLevel(logging.INFO)
        
        super().__init__("google_trends", api_key, **kwargs)
        
        # Google Trends specific configuration
        self.hl = 'ru-RU'  # Russian language
        self.tz = 360      # Moscow timezone offset in minutes
        self.timeout = (10, 30)  # Connect and read timeout
        
        # Rate limiting configuration for Google Trends
        # Google has strict quotas, so we need to be conservative
        self.max_requests_per_hour = 100  # Conservative estimate
        self.max_concurrent_requests = 1  # Google Trends doesn't like parallel requests
        self.request_interval = 5  # Minimum 5 seconds between requests
        
        # Initialize pytrends client
        self._init_trends_client()
        
        # Rate limiting tracking
        self._last_request_time = 0
        self._hourly_request_count = 0
        self._hourly_lock = threading.Lock()
        self._last_hour = 0
        
        # Initialize cache for trends data
        self.cache = SearchCache(ttl=3600)  # 1 hour cache for trends data
        
        # Override base rate limiting settings
        self.max_concurrent_requests = 1
        self.request_timeout = 30
        self.max_retries = 3

    def _init_trends_client(self) -> None:
        """
        Initialize the pytrends client with Russian market settings.
        """
        try:
            # Initialize with Russian language and timezone settings
            self.trends_client = TrendReq(
                hl=self.hl,
                tz=self.tz,
                timeout=self.timeout,
                retries=2,
                backoff_factor=0.5
            )
            self.logger.info("Google Trends client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Trends client: {str(e)}")
            raise

    def _google_trends_rate_limit(self) -> None:
        """
        Implement Google Trends specific rate limiting.
        
        Ensures:
        - Minimum 5 seconds between requests
        - Maximum 100 requests per hour (conservative estimate)
        """
        current_time = time.time()
        
        # Check minimum interval between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Check hourly request limit
        with self._hourly_lock:
            current_hour = int(current_time // 3600)  # Current hour in Unix timestamp
            if current_hour != self._last_hour:
                # New hour, reset counter
                self._hourly_request_count = 0
                self._last_hour = current_hour
            
            if self._hourly_request_count >= self.max_requests_per_hour:
                # Wait until next hour
                seconds_until_next_hour = 3600 - (current_time % 3600)
                self.logger.warning(f"Hourly quota reached, waiting {seconds_until_next_hour:.2f} seconds")
                time.sleep(seconds_until_next_hour)
                # Reset counter for new hour
                self._hourly_request_count = 0
                self._last_hour = int(time.time() // 3600)
            
            self._hourly_request_count += 1
        
        # Update last request timestamp
        self._last_request_time = time.time()

    def _make_cache_key(self, query: str, method: str) -> str:
        """
        Create a cache key for trends data.
        
        Args:
            query: Search query string
            method: Method name (interest_over_time, related_queries)
            
        Returns:
            Cache key string
        """
        return f"google_trends:{method}:{query}"

    def _get_cached_data(self, query: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Get cached trends data if available.
        
        Args:
            query: Search query string
            method: Method name
            
        Returns:
            Cached data if available, None otherwise
        """
        cache_key = self._make_cache_key(query, method)
        return self.cache.get('google_trends', cache_key)

    def _set_cached_data(self, query: str, method: str, data: Dict[str, Any]) -> None:
        """
        Cache trends data.
        
        Args:
            query: Search query string
            method: Method name
            data: Data to cache
        """
        cache_key = self._make_cache_key(query, method)
        self.cache.set('google_trends', cache_key, data)

    def get_interest_over_time(
        self, 
        query: str, 
        timeframe: str = 'today 12-m',
        use_cache: bool = True
    ) -> TrendData:
        """
        Get interest over time data for a specific query.
        
        Args:
            query: Search query string
            timeframe: Timeframe for trends data (default: 'today 12-m' for 12 months)
            use_cache: Whether to use cached results when available
            
        Returns:
            TrendData object containing normalized interest data
            
        Raises:
            Exception: If trends data retrieval fails after maximum retries
        """
        # Apply rate limiting
        self._google_trends_rate_limit()
        
        # Try to get cached data first
        if use_cache:
            cached_data = self._get_cached_data(query, 'interest_over_time')
            if cached_data is not None:
                self.logger.info(f"Cache hit for interest_over_time: {query}")
                return TrendData(
                    query=cached_data['query'],
                    trend_score=cached_data['trend_score'],
                    historical_data=cached_data['historical_data']
                )
        
        try:
            # Build payload for Google Trends
            self.trends_client.build_payload([query], cat=0, timeframe=timeframe, geo='RU', gprop='')
            
            # Get interest over time data
            interest_df = self.trends_client.interest_over_time()
            
            if interest_df is None or interest_df.empty:
                raise Exception("No data returned from Google Trends")
            
            # Process the data
            trend_data = self._process_interest_data(interest_df, query)
            
            # Cache the results
            if use_cache:
                cache_data = {
                    'query': query,
                    'trend_score': trend_data.trend_score,
                    'historical_data': trend_data.historical_data,
                    'timestamp': time.time()
                }
                self._set_cached_data(query, 'interest_over_time', cache_data)
            
            return trend_data
            
        except Exception as e:
            self.logger.error(f"Failed to get interest over time for '{query}': {str(e)}")
            # Return fallback data with neutral trend score
            return TrendData(
                query=query,
                trend_score=0.5,  # Neutral score
                historical_data=[]  # No historical data
            )

    def _process_interest_data(self, interest_df: pd.DataFrame, query: str) -> TrendData:
        """
        Process raw Google Trends interest data into TrendData format.
        
        Args:
            interest_df: Pandas DataFrame with interest data
            query: Original query string
            
        Returns:
            TrendData object with processed data
        """
        try:
            # Reset index to get date as column
            interest_df = interest_df.reset_index()
            
            # Calculate overall trend score (average of all data points, normalized to 0-1)
            interest_values = interest_df[query].dropna()
            if len(interest_values) == 0:
                trend_score = 0.5  # Neutral score if no data
            else:
                # Normalize to 0-1 range based on max value in the series
                max_value = interest_values.max()
                if max_value > 0:
                    trend_score = min(interest_values.mean() / max_value, 1.0)
                else:
                    trend_score = 0.0
            
            # Convert to historical data format
            historical_data = []
            for _, row in interest_df.iterrows():
                date_str = row['date'].strftime('%Y-%m-%d')
                interest_value = row[query]
                
                # Handle NaN values
                if pd.isna(interest_value):
                    continue
                    
                historical_data.append({
                    'date': date_str,
                    'search_volume': int(interest_value),
                    'trend_index': float(interest_value) / 100.0  # Normalize to 0-1 range
                })
            
            return TrendData(
                query=query,
                trend_score=float(trend_score),
                historical_data=historical_data
            )
            
        except Exception as e:
            self.logger.error(f"Error processing interest data: {str(e)}")
            # Return fallback data
            return TrendData(
                query=query,
                trend_score=0.5,
                historical_data=[]
            )

    def get_related_queries(
        self, 
        query: str, 
        timeframe: str = 'today 12-m',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get related queries for a specific query.
        
        Args:
            query: Search query string
            timeframe: Timeframe for trends data (default: 'today 12-m')
            use_cache: Whether to use cached results when available
            
        Returns:
            Dictionary containing structured query data with rising and top queries
            
        Raises:
            Exception: If related queries retrieval fails after maximum retries
        """
        # Apply rate limiting
        self._google_trends_rate_limit()
        
        # Try to get cached data first
        if use_cache:
            cached_data = self._get_cached_data(query, 'related_queries')
            if cached_data is not None:
                self.logger.info(f"Cache hit for related_queries: {query}")
                return cached_data
        
        try:
            # Build payload for Google Trends
            self.trends_client.build_payload([query], cat=0, timeframe=timeframe, geo='RU', gprop='')
            
            # Get related queries data
            related_queries = self.trends_client.related_queries()
            
            if related_queries is None or query not in related_queries:
                raise Exception("No related queries data returned from Google Trends")
            
            # Process the data
            processed_data = self._process_related_queries(related_queries[query], query)
            
            # Cache the results
            if use_cache:
                self._set_cached_data(query, 'related_queries', processed_data)
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Failed to get related queries for '{query}': {str(e)}")
            # Return fallback data with empty results
            return {
                'query': query,
                'rising_queries': [],
                'top_queries': [],
                'timestamp': time.time()
            }

    def _process_related_queries(self, queries_df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Process raw Google Trends related queries data into structured format.
        
        Args:
            queries_df: Pandas DataFrame with related queries data
            query: Original query string
            
        Returns:
            Dictionary with structured query data
        """
        try:
            result = {
                'query': query,
                'rising_queries': [],
                'top_queries': [],
                'timestamp': time.time()
            }
            
            # Process rising queries
            if 'rising' in queries_df and not queries_df['rising'].empty:
                rising_df = queries_df['rising']
                for _, row in rising_df.iterrows():
                    result['rising_queries'].append({
                        'query': row['query'],
                        'value': int(row['value']) if pd.notna(row['value']) else 0
                    })
            
            # Process top queries
            if 'top' in queries_df and not queries_df['top'].empty:
                top_df = queries_df['top']
                for _, row in top_df.iterrows():
                    result['top_queries'].append({
                        'query': row['query'],
                        'value': int(row['value']) if pd.notna(row['value']) else 0
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing related queries: {str(e)}")
            # Return fallback data
            return {
                'query': query,
                'rising_queries': [],
                'top_queries': [],
                'timestamp': time.time()
            }

    def get_trends(self, query: str) -> TrendData:
        """
        Get trend data for a specific query (compatibility method).
        
        This method provides compatibility with the DataSource interface.
        It uses interest_over_time data as the primary trend indicator.
        
        Args:
            query: Query string to get trends for
            
        Returns:
            TrendData object containing trend information
        """
        return self.get_interest_over_time(query)

    def search(self, query: str) -> List[Product]:
        """
        Search for products (not implemented for Google Trends).
        
        Google Trends doesn't provide product search functionality,
        so this method returns an empty list.
        
        Args:
            query: Search query string
            
        Returns:
            Empty list of products
        """
        self.logger.warning("Google Trends does not support product search")
        return []

    def _make_request(self, url: str, method: str = 'GET',
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request with Google Trends specific handling.
        
        This method overrides the base implementation to handle
        Google Trends API specifics.
        
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
        # Apply both base and Google Trends rate limiting
        super()._rate_limit()
        self._google_trends_rate_limit()
        
        # For Google Trends, we use the pytrends library directly,
        # so this method is mostly for compatibility
        try:
            return super()._make_request(url, method, params, data, headers)
        except Exception as e:
            self.logger.error(f"Google Trends request failed: {str(e)}")
            raise

    def close(self):
        """
        Clean up resources.
        """
        super().close()
        # No specific cleanup needed for pytrends

    def __enter__(self):
        """
        Context manager entry.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - clean up resources.
        """
        self.close()