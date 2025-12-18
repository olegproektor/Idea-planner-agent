"""
Market Data Aggregator for the ru_search module.

This module implements the MarketDataAggregator class that combines data from all sources
(Wildberries, Ozon, Yandex, Google Trends) with caching support. The aggregator supports parallel
execution for speed and calculates summary metrics like average price, total products,
and search volume. It includes data quality assessment, honest disclosure, and three-tier
fallback logic per Constitution Section 4.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor

from .base import Product, TrendData, DataSource
from .wildberries import WildberriesSearch
from .ozon import OzonSearch
from .yandex import YandexSearch
from .google_trends import GoogleTrendsAPI
from .cache import SearchCache


class DataQualityAssessor:
    """
    Data Quality Assessor for evaluating the quality and reliability of search results.
    
    This class provides:
    - Confidence scoring (0.4-0.9 range)
    - Data freshness tracking
    - Source reliability assessment
    - Comprehensive quality metrics
    """
    
    def __init__(self):
        """Initialize the DataQualityAssessor."""
        self.logger = logging.getLogger('DataQualityAssessor')
        self.logger.setLevel(logging.INFO)
        
    def assess_quality(
        self, 
        products: List[Product], 
        sources_used: List[str], 
        errors: List[Dict[str, Any]],
        cache_hits: Dict[str, bool],
        data_age: float,
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess data quality based on multiple factors.
        
        Args:
            products: List of products from search results
            sources_used: List of source names that were used
            errors: List of errors encountered during search
            cache_hits: Dictionary indicating cache hits per source
            data_age: Age of data in seconds
            source_data: Raw data from each source
            
        Returns:
            Dictionary containing comprehensive data quality metrics
        """
        # Calculate base confidence score
        base_score = self._calculate_base_confidence(products, sources_used, errors)
        
        # Adjust for data freshness
        freshness_score = self._calculate_freshness_score(data_age)
        
        # Adjust for source reliability
        reliability_score = self._calculate_reliability_score(sources_used, errors, cache_hits)
        
        # Calculate comprehensive confidence score (0.4-0.9 range)
        confidence_score = self._calculate_confidence_score(base_score, freshness_score, reliability_score)
        
        # Generate honest disclosure message
        disclosure_message = self._generate_disclosure_message(
            confidence_score, sources_used, errors, data_age, cache_hits
        )
        
        # Calculate data completeness
        completeness_score = self._calculate_completeness_score(products, source_data)
        
        return {
            'confidence_score': round(confidence_score, 2),
            'freshness_score': round(freshness_score, 2),
            'reliability_score': round(reliability_score, 2),
            'completeness_score': round(completeness_score, 2),
            'data_age_seconds': round(data_age, 2),
            'data_age_human': self._format_data_age(data_age),
            'source_coverage': len(sources_used),
            'successful_sources': len(sources_used) - len(errors),
            'error_rate': len(errors) / len(sources_used) if sources_used else 0.0,
            'cache_usage': sum(1 for hit in cache_hits.values() if hit) / len(cache_hits) if cache_hits else 0.0,
            'disclosure_message': disclosure_message,
            'quality_grade': self._get_quality_grade(confidence_score),
            'citation_format': self._generate_citation_format(sources_used, source_data)
        }
    
    def _calculate_base_confidence(
        self, 
        products: List[Product], 
        sources_used: List[str], 
        errors: List[Dict[str, Any]]
    ) -> float:
        """Calculate base confidence score based on data availability and errors."""
        if not products:
            return 0.4  # Minimum score for no data
            
        # Base score starts at 0.7 for successful data retrieval
        base_score = 0.7
        
        # Adjust for number of products
        if len(products) < 5:
            base_score -= 0.1
        elif len(products) >= 20:
            base_score += 0.1
            
        # Adjust for error rate
        error_rate = len(errors) / len(sources_used) if sources_used else 0.0
        if error_rate > 0.5:
            base_score -= 0.2
        elif error_rate > 0.2:
            base_score -= 0.1
            
        # Ensure score stays within bounds
        return max(0.4, min(0.9, base_score))
    
    def _calculate_freshness_score(self, data_age: float) -> float:
        """Calculate freshness score based on data age."""
        # Convert age to hours
        age_hours = data_age / 3600
        
        # Freshness score decreases as data gets older
        if age_hours <= 1:  # Very fresh (<1 hour)
            return 1.0
        elif age_hours <= 6:  # Fresh (<6 hours)
            return 0.9
        elif age_hours <= 24:  # Recent (<24 hours)
            return 0.7
        elif age_hours <= 168:  # Recent (<1 week)
            return 0.5
        else:  # Old (>1 week)
            return 0.3
    
    def _calculate_reliability_score(
        self, 
        sources_used: List[str], 
        errors: List[Dict[str, Any]],
        cache_hits: Dict[str, bool]
    ) -> float:
        """Calculate reliability score based on source performance."""
        if not sources_used:
            return 0.5
            
        # Start with base reliability
        reliability = 0.7
        
        # Adjust for error rate
        error_rate = len(errors) / len(sources_used)
        if error_rate > 0.5:
            reliability -= 0.3
        elif error_rate > 0.2:
            reliability -= 0.1
            
        # Adjust for cache usage (high cache usage may indicate stale data)
        cache_usage = sum(1 for hit in cache_hits.values() if hit) / len(cache_hits) if cache_hits else 0.0
        if cache_usage > 0.8:
            reliability -= 0.1  # Too much cached data
        elif cache_usage < 0.2:
            reliability += 0.1  # Fresh data from APIs
            
        return max(0.3, min(1.0, reliability))
    
    def _calculate_confidence_score(
        self, 
        base_score: float, 
        freshness_score: float,
        reliability_score: float
    ) -> float:
        """Calculate comprehensive confidence score (0.4-0.9 range)."""
        # Weighted average with base score being most important
        confidence = (
            base_score * 0.5 + 
            freshness_score * 0.3 + 
            reliability_score * 0.2
        )
        
        # Ensure score is within the required range
        return max(0.4, min(0.9, confidence))
    
    def _calculate_completeness_score(
        self, 
        products: List[Product], 
        source_data: Dict[str, Any]
    ) -> float:
        """Calculate data completeness score."""
        if not products:
            return 0.0
            
        # Check what percentage of products have complete metadata
        complete_products = 0
        for product in products:
            has_price = product.price is not None and product.price > 0
            has_title = product.title is not None and len(product.title.strip()) > 0
            has_url = product.url is not None and len(product.url.strip()) > 0
            has_metadata = len(product.metadata) >= 3  # At least 3 metadata fields
            
            if has_price and has_title and has_url and has_metadata:
                complete_products += 1
                
        completeness = complete_products / len(products) if products else 0.0
        return round(completeness, 2)
    
    def _generate_disclosure_message(
        self, 
        confidence_score: float,
        sources_used: List[str],
        errors: List[Dict[str, Any]],
        data_age: float,
        cache_hits: Dict[str, bool]
    ) -> str:
        """Generate honest disclosure message per Constitution Section 4."""
        disclosure_parts = []
        
        # Confidence disclosure
        if confidence_score >= 0.8:
            disclosure_parts.append("✅ Высокая уверенность в данных")
        elif confidence_score >= 0.6:
            disclosure_parts.append("⚠️ Умеренная уверенность в данных")
        elif confidence_score >= 0.4:
            disclosure_parts.append("⚠️ Низкая уверенность в данных")
        else:
            disclosure_parts.append("❌ Очень низкая уверенность в данных")
            
        # Source disclosure
        source_names = ", ".join(sources_used) if sources_used else "нет источников"
        disclosure_parts.append(f"📊 Источники данных: {source_names}")
        
        # Error disclosure
        if errors:
            error_sources = ", ".join([error['source'] for error in errors])
            disclosure_parts.append(f"⚠️ Ошибки при получении данных с: {error_sources}")
            
        # Freshness disclosure
        age_human = self._format_data_age(data_age)
        disclosure_parts.append(f"🕒 Актуальность данных: {age_human}")
        
        # Cache disclosure
        cache_count = sum(1 for hit in cache_hits.values() if hit)
        if cache_count > 0:
            disclosure_parts.append(f"💾 Использованы кешированные данные: {cache_count} из {len(cache_hits)} источников")
            
        # Quality grade disclosure
        quality_grade = self._get_quality_grade(confidence_score)
        disclosure_parts.append(f"🏆 Оценка качества: {quality_grade}")
        
        return " | ".join(disclosure_parts)
    
    def _format_data_age(self, data_age: float) -> str:
        """Format data age in human-readable format."""
        if data_age < 60:
            return f"{round(data_age)} секунд назад"
        elif data_age < 3600:
            minutes = round(data_age / 60)
            return f"{minutes} минут назад"
        elif data_age < 86400:
            hours = round(data_age / 3600)
            return f"{hours} часов назад"
        else:
            days = round(data_age / 86400)
            return f"{days} дней назад"
    
    def _get_quality_grade(self, confidence_score: float) -> str:
        """Get quality grade based on confidence score."""
        if confidence_score >= 0.8:
            return "A (Отлично)"
        elif confidence_score >= 0.7:
            return "B (Хорошо)"
        elif confidence_score >= 0.6:
            return "C (Удовлетворительно)"
        elif confidence_score >= 0.5:
            return "D (Ниже среднего)"
        else:
            return "F (Неудовлетворительно)"
    
    def _generate_citation_format(
        self, 
        sources_used: List[str], 
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate updated citation format with source transparency."""
        citations = {}
        
        for source_name in sources_used:
            if source_name in source_data:
                source_info = source_data[source_name]
                products = source_info.get('products', [])
                
                citations[source_name] = {
                    'source_name': source_name,
                    'source_url': self._get_source_url(source_name),
                    'products_count': len(products),
                    'timestamp': source_info.get('timestamp', time.time()),
                    'data_freshness': self._format_data_age(time.time() - source_info.get('timestamp', time.time())),
                    'sample_products': []
                }
                
                # Add sample product citations (up to 3)
                for i, product in enumerate(products[:3]):
                    citations[source_name]['sample_products'].append({
                        'product_id': product.id,
                        'product_title': product.title,
                        'product_url': product.url,
                        'product_price': product.price,
                        'source_confidence': self._get_source_confidence(source_name)
                    })
                    
        return citations
    
    def _get_source_url(self, source_name: str) -> str:
        """Get base URL for source."""
        source_urls = {
            'wildberries': 'https://www.wildberries.ru',
            'ozon': 'https://www.ozon.ru',
            'yandex': 'https://market.yandex.ru',
            'google_trends': 'https://trends.google.com'
        }
        return source_urls.get(source_name, 'unknown')
    
    def _get_source_confidence(self, source_name: str) -> float:
        """Get base confidence level for each source."""
        source_confidence = {
            'wildberries': 0.85,
            'ozon': 0.80,
            'yandex': 0.75,
            'google_trends': 0.90
        }
        return source_confidence.get(source_name, 0.70)


class MarketDataAggregator:
    """
    Market Data Aggregator that combines results from multiple sources.
     
    This class provides:
    - Parallel execution across multiple data sources
    - Caching support for individual source queries
    - Summary metrics calculation (average price, total products, etc.)
    - Graceful handling of partial failures
    - Configurable source selection
    - Data quality assessment and honest disclosure
    - Three-tier fallback logic (APIs → Cache → User data)
    - Confidence scoring (0.4-0.9 range)
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
        self.google_trends = GoogleTrendsAPI()
         
        # Initialize cache
        self.cache = SearchCache(ttl=cache_ttl)
         
        # Initialize data quality assessor
        self.quality_assessor = DataQualityAssessor()
         
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
         
        # Available sources with tier information
        self.available_sources = {
            'wildberries': {'instance': self.wildberries, 'tier': 1},
            'ozon': {'instance': self.ozon, 'tier': 1},
            'yandex': {'instance': self.yandex, 'tier': 1},
            'google_trends': {'instance': self.google_trends, 'tier': 2}
        }
        
        # Logger
        self.logger = logging.getLogger('MarketDataAggregator')
        self.logger.setLevel(logging.INFO)
     
    async def search(
        self, 
        query: str, 
        sources: Optional[List[str]] = None, 
        use_cache: bool = True, 
        timeout: int = 30,
        fallback_to_cache: bool = True,
        fallback_to_user_data: bool = False
    ) -> Dict[str, Any]:
        """
        Search for products across multiple sources with parallel execution.
        
        Args:
            query: Search query string
            sources: List of source names to use (None for all available)
            use_cache: Whether to use cached results when available
            timeout: Maximum timeout in seconds for the entire operation
            fallback_to_cache: Whether to use cached data if API fails
            fallback_to_user_data: Whether to use user-provided data as last resort
             
        Returns:
            Dictionary containing:
            - 'query': Original query
            - 'results': List of all products from all sources
            - 'summary': Summary statistics
            - 'source_results': Results grouped by source
            - 'errors': Any errors encountered during search
            - 'data_quality': Data quality assessment
            - 'disclosure': Honest disclosure message
            - 'citations': Source citations with transparency
            - 'timestamp': Execution timestamp
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
            source_info = self.available_sources[source_name]
            source = source_info['instance']
            task = asyncio.create_task(
                self._search_source(source_name, source, query, use_cache, fallback_to_cache)
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
        cache_hits = {}
        source_data = {}
         
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
                    'error': str(result),
                    'cache_hit': False,
                    'count': 0
                }
                cache_hits[source_name] = False
            else:
                # Store successful results
                products, cache_hit, source_info = result
                all_products.extend(products)
                source_results[source_name] = {
                    'products': products,
                    'cache_hit': cache_hit,
                    'count': len(products),
                    'timestamp': source_info.get('timestamp', time.time())
                }
                cache_hits[source_name] = cache_hit
                source_data[source_name] = source_info
         
        # Calculate summary statistics
        summary = self._calculate_summary(all_products, sources_to_use, errors)
         
        # Calculate data age (average age of all data)
        data_age = self._calculate_data_age(source_results)
         
        # Add data quality assessment
        data_quality = self.quality_assessor.assess_quality(
            all_products, sources_to_use, errors, cache_hits, data_age, source_data
        )
         
        # Add timing information
        summary['execution_time'] = time.time() - start_time
         
        return {
            'query': query,
            'results': all_products,
            'summary': summary,
            'source_results': source_results,
            'errors': errors,
            'data_quality': data_quality,
            'disclosure': data_quality['disclosure_message'],
            'citations': data_quality['citation_format'],
            'timestamp': time.time()
        }
     
    async def _search_source(
        self, 
        source_name: str, 
        source: DataSource, 
        query: str, 
        use_cache: bool,
        fallback_to_cache: bool
    ) -> tuple:
        """
        Search a single source with caching support and three-tier fallback.
        
        Args:
            source_name: Name of the data source
            source: DataSource instance
            query: Search query string
            use_cache: Whether to use cached results
            fallback_to_cache: Whether to use cached data if API fails
             
        Returns:
            Tuple of (products, cache_hit, source_info) where cache_hit is a boolean
        """
        cache_hit = False
        source_info = {}
         
        # Tier 1: Try to get cached results if caching is enabled
        if use_cache:
            cached_data = self.cache.get(source_name, query)
            if cached_data is not None:
                cache_hit = True
                products = cached_data.get('products', [])
                source_info = {
                    'products': products,
                    'timestamp': cached_data.get('timestamp', time.time()),
                    'source': source_name,
                    'cache_hit': True
                }
                self.logger.info(f"Cache hit for {source_name}: {query}")
                return (products, cache_hit, source_info)
         
        # Tier 2: If not in cache or caching disabled, perform actual search
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
                
            source_info = {
                'products': products,
                'timestamp': time.time(),
                'source': source_name,
                'cache_hit': False
            }
            
            return (products, cache_hit, source_info)
             
        except Exception as e:
            self.logger.error(f"Search failed for {source_name}: {str(e)}")
            
            # Tier 3: Fallback to cached data if available and allowed
            if fallback_to_cache:
                cached_data = self.cache.get(source_name, query)
                if cached_data is not None:
                    self.logger.info(f"Fallback to cache for {source_name}: {query}")
                    products = cached_data.get('products', [])
                    source_info = {
                        'products': products,
                        'timestamp': cached_data.get('timestamp', time.time()),
                        'source': source_name,
                        'cache_hit': True,
                        'fallback': True
                    }
                    return (products, True, source_info)
            
            # If no fallback available, raise the exception
            raise Exception(f"Search failed for {source_name}: {str(e)}")
     
    def _calculate_data_age(self, source_results: Dict[str, Any]) -> float:
        """Calculate average data age across all sources."""
        total_age = 0.0
        source_count = 0
        current_time = time.time()
        
        for source_name, result in source_results.items():
            if 'timestamp' in result:
                data_age = current_time - result['timestamp']
                total_age += data_age
                source_count += 1
                
        return total_age / source_count if source_count > 0 else 0.0
     
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
            source_info = self.available_sources[source_name]
            source = source_info['instance']
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
        self.google_trends.close()
     
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