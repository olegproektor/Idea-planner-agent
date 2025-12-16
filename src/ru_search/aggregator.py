"""
Market Data Aggregator for the ru_search module.

This module implements the MarketDataAggregator class that combines data from all sources
(Wildberries, Ozon, Yandex) with caching support. The aggregator supports parallel
execution for speed and calculates summary metrics like average price, total products,
and search volume.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor

from .base import Product, TrendData, DataSource
from .wildberries import WildberriesSearch
from .ozon import OzonSearch
from .yandex import YandexSearch
from .cache import SearchCache


class MarketDataAggregator:
    """
    Market Data Aggregator that combines results from multiple sources.
    
    This class provides:
    - Parallel execution across multiple data sources
    - Caching support for individual source queries
    - Summary metrics calculation (average price, total products, etc.)
    - Graceful handling of partial failures
    - Configurable source selection
    """
    
    def __init__(self, cache_ttl: int = 21600, max_workers: int = 3):
        """
        Initialize the MarketDataAggregator.
        
        Args:
            cache_ttl: Time-to-live in seconds for cache entries (default: 21600 = 6 hours)
            max_workers: Maximum number of parallel workers for concurrent execution
        """
        self.cache_ttl = cache_ttl
        self.max_workers = max_workers
        
        # Initialize data sources
        self.wildberries = WildberriesSearch()
        self.ozon = OzonSearch()
        self.yandex = YandexSearch()
        
        # Initialize cache
        self.cache = SearchCache(ttl=cache_ttl)
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Available sources
        self.available_sources = {
            'wildberries': self.wildberries,
            'ozon': self.ozon,
            'yandex': self.yandex
        }
    
    async def search(
        self, 
        query: str, 
        sources: Optional[List[str]] = None,
        use_cache: bool = True,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Search for products across multiple sources with parallel execution.
        
        Args:
            query: Search query string
            sources: List of source names to use (None for all available)
            use_cache: Whether to use cached results when available
            timeout: Maximum timeout in seconds for the entire operation
            
        Returns:
            Dictionary containing:
            - 'results': List of all products from all sources
            - 'summary': Summary statistics
            - 'source_results': Results grouped by source
            - 'errors': Any errors encountered during search
        """
        start_time = time.time()
        
        # Determine which sources to use
        if sources is None:
            sources_to_use = list(self.available_sources.keys())
        else:
            sources_to_use = [source for source in sources if source in self.available_sources]
        
        # Prepare tasks for parallel execution
        tasks = []
        for source_name in sources_to_use:
            source = self.available_sources[source_name]
            task = asyncio.create_task(
                self._search_source(source_name, source, query, use_cache)
            )
            tasks.append(task)
        
        # Execute tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Cancel all tasks if timeout occurs
            for task in tasks:
                task.cancel()
            raise Exception(f"Search operation timed out after {timeout} seconds")
        
        # Process results
        all_products = []
        source_results = {}
        errors = []
        
        for i, source_name in enumerate(sources_to_use):
            result = results[i]
            
            if isinstance(result, Exception):
                # Handle errors gracefully
                errors.append({
                    'source': source_name,
                    'error': str(result)
                })
                source_results[source_name] = {
                    'products': [],
                    'error': str(result)
                }
            else:
                # Store successful results
                products, cache_hit = result
                all_products.extend(products)
                source_results[source_name] = {
                    'products': products,
                    'cache_hit': cache_hit,
                    'count': len(products)
                }
        
        # Calculate summary statistics
        summary = self._calculate_summary(all_products, sources_to_use, errors)
        
        # Add timing information
        summary['execution_time'] = time.time() - start_time
        
        return {
            'query': query,
            'results': all_products,
            'summary': summary,
            'source_results': source_results,
            'errors': errors,
            'timestamp': time.time()
        }
    
    async def _search_source(
        self, 
        source_name: str, 
        source: DataSource, 
        query: str, 
        use_cache: bool
    ) -> tuple:
        """
        Search a single source with caching support.
        
        Args:
            source_name: Name of the data source
            source: DataSource instance
            query: Search query string
            use_cache: Whether to use cached results
            
        Returns:
            Tuple of (products, cache_hit) where cache_hit is a boolean
        """
        cache_hit = False
        
        # Try to get cached results if caching is enabled
        if use_cache:
            cached_data = self.cache.get(source_name, query)
            if cached_data is not None:
                cache_hit = True
                products = cached_data.get('products', [])
                return (products, cache_hit)
        
        # If not in cache or caching disabled, perform actual search
        try:
            # Run the search in a thread to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            products = await loop.run_in_executor(
                self.executor,
                source.search,
                query
            )
            
            # Cache the results
            if use_cache:
                cache_data = {
                    'products': products,
                    'timestamp': time.time(),
                    'query': query,
                    'source': source_name
                }
                self.cache.set(source_name, query, cache_data)
            
            return (products, cache_hit)
            
        except Exception as e:
            # Wrap the exception to handle it in the main search method
            raise Exception(f"Search failed for {source_name}: {str(e)}")
    
    def _calculate_summary(
        self, 
        products: List[Product], 
        sources_used: List[str], 
        errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for the aggregated results.
        
        Args:
            products: List of all products from all sources
            sources_used: List of source names that were used
            errors: List of errors encountered during search
            
        Returns:
            Dictionary containing summary statistics
        """
        if not products:
            return {
                'total_products': 0,
                'average_price': 0.0,
                'min_price': 0.0,
                'max_price': 0.0,
                'total_sources': len(sources_used),
                'successful_sources': len(sources_used) - len(errors),
                'failed_sources': len(errors),
                'unique_products': 0,
                'price_range': '0 - 0',
                'error_rate': len(errors) / len(sources_used) if sources_used else 0.0
            }
        
        # Calculate basic statistics
        prices = [product.price for product in products]
        total_products = len(products)
        
        # Calculate unique products based on ID
        unique_product_ids = set()
        for product in products:
            if product.id:
                unique_product_ids.add(product.id)
        unique_products = len(unique_product_ids)
        
        # Calculate price statistics
        average_price = sum(prices) / len(prices) if prices else 0.0
        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        price_range = f"{min_price:.2f} - {max_price:.2f}"
        
        # Calculate source statistics
        successful_sources = len(sources_used) - len(errors)
        failed_sources = len(errors)
        error_rate = failed_sources / len(sources_used) if sources_used else 0.0
        
        # Calculate brand distribution
        brand_counts = {}
        for product in products:
            brand = product.metadata.get('brand', 'Unknown')
            if brand:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        # Get top brands
        top_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_products': total_products,
            'unique_products': unique_products,
            'average_price': round(average_price, 2),
            'min_price': round(min_price, 2),
            'max_price': round(max_price, 2),
            'price_range': price_range,
            'total_sources': len(sources_used),
            'successful_sources': successful_sources,
            'failed_sources': failed_sources,
            'error_rate': round(error_rate, 3),
            'top_brands': [{'brand': brand, 'count': count} for brand, count in top_brands],
            'brand_diversity': len(brand_counts)
        }
    
    async def get_trends(
        self, 
        query: str, 
        sources: Optional[List[str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Get trend data from multiple sources.
        
        Args:
            query: Search query string
            sources: List of source names to use (None for all available)
            timeout: Maximum timeout in seconds for the entire operation
            
        Returns:
            Dictionary containing trend data from all sources
        """
        start_time = time.time()
        
        # Determine which sources to use
        if sources is None:
            sources_to_use = list(self.available_sources.keys())
        else:
            sources_to_use = [source for source in sources if source in self.available_sources]
        
        # Prepare tasks for parallel execution
        tasks = []
        for source_name in sources_to_use:
            source = self.available_sources[source_name]
            task = asyncio.create_task(
                self._get_trends_source(source_name, source, query)
            )
            tasks.append(task)
        
        # Execute tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Cancel all tasks if timeout occurs
            for task in tasks:
                task.cancel()
            raise Exception(f"Trends operation timed out after {timeout} seconds")
        
        # Process results
        trend_results = {}
        errors = []
        
        for i, source_name in enumerate(sources_to_use):
            result = results[i]
            
            if isinstance(result, Exception):
                # Handle errors gracefully
                errors.append({
                    'source': source_name,
                    'error': str(result)
                })
                trend_results[source_name] = {
                    'error': str(result)
                }
            else:
                # Store successful results
                trend_data = result
                trend_results[source_name] = {
                    'trend_score': trend_data.trend_score,
                    'historical_data': trend_data.historical_data,
                    'query': trend_data.query
                }
        
        # Calculate average trend score
        valid_scores = [
            trend_results[source]['trend_score'] 
            for source in trend_results 
            if 'trend_score' in trend_results[source]
        ]
        average_trend_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        
        return {
            'query': query,
            'trend_results': trend_results,
            'average_trend_score': round(average_trend_score, 3),
            'errors': errors,
            'execution_time': time.time() - start_time,
            'timestamp': time.time()
        }
    
    async def _get_trends_source(
        self, 
        source_name: str, 
        source: DataSource, 
        query: str
    ) -> TrendData:
        """
        Get trends from a single source.
        
        Args:
            source_name: Name of the data source
            source: DataSource instance
            query: Search query string
            
        Returns:
            TrendData object
        """
        try:
            # Run the trends search in a thread to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            trend_data = await loop.run_in_executor(
                self.executor,
                source.get_trends,
                query
            )
            
            return trend_data
            
        except Exception as e:
            # Wrap the exception to handle it in the main get_trends method
            raise Exception(f"Trends search failed for {source_name}: {str(e)}")
    
    def clear_cache(self) -> None:
        """
        Clear all cached results.
        """
        self.cache.clear()
    
    def close(self) -> None:
        """
        Clean up resources.
        """
        self.executor.shutdown(wait=True)
        self.wildberries.close()
        self.ozon.close()
        self.yandex.close()
    
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