("""
Comprehensive tests for MarketDataAggregator functionality.

This module tests the MarketDataAggregator class including:
- Multi-source search
- Caching integration
- Parallel execution
- Error handling
- Summary statistics
- Trend aggregation
""")

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from src.ru_search.aggregator import MarketDataAggregator
from src.ru_search.base import Product


class TestMarketDataAggregator:
    """Test suite for MarketDataAggregator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.aggregator = MarketDataAggregator(cache_ttl=2)  # Short TTL for testing
        self.test_query = "телефон"
        
    def teardown_method(self):
        """Clean up after tests."""
        self.aggregator.close()

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_all_sources_success(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test successful search across all sources."""
        # Mock product data
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1"),
            Product(id="wb2", title="Телефон Wildberries 2", price=15000.0, url="https://wb.ru/p2")
        ]
        
        ozon_products = [
            Product(id="oz1", title="Телефон Ozon 1", price=12000.0, url="https://ozon.ru/p1"),
            Product(id="oz2", title="Телефон Ozon 2", price=18000.0, url="https://ozon.ru/p2")
        ]
        
        yandex_products = [
            Product(id="ya1", title="Телефон Yandex 1", price=11000.0, url="https://market.yandex.ru/p1"),
            Product(id="ya2", title="Телефон Yandex 2", price=16000.0, url="https://market.yandex.ru/p2")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.return_value = yandex_products
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Assertions
        assert 'query' in results
        assert results['query'] == self.test_query
        assert 'results' in results
        assert 'summary' in results
        assert 'source_results' in results
        assert 'errors' in results
        assert 'timestamp' in results
        
        # Check all products are present
        all_products = results['results']
        assert len(all_products) == 6
        
        # Check source results
        source_results = results['source_results']
        assert 'wildberries' in source_results
        assert 'ozon' in source_results
        assert 'yandex' in source_results
        
        assert source_results['wildberries']['count'] == 2
        assert source_results['ozon']['count'] == 2
        assert source_results['yandex']['count'] == 2
        
        # Check summary statistics
        summary = results['summary']
        assert summary['total_products'] == 6
        assert summary['unique_products'] == 6  # All IDs are unique
        assert summary['total_sources'] == 3
        assert summary['successful_sources'] == 3
        assert summary['failed_sources'] == 0
        assert summary['error_rate'] == 0.0
        
        # Check price statistics
        assert summary['average_price'] > 0
        assert summary['min_price'] == 10000.0
        assert summary['max_price'] == 18000.0
        assert 'price_range' in summary
        
        # Check execution time
        assert 'execution_time' in summary
        assert summary['execution_time'] > 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_partial_failure(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with partial source failures."""
        # Mock successful responses
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        ozon_products = [
            Product(id="oz1", title="Телефон Ozon 1", price=12000.0, url="https://ozon.ru/p1")
        ]
        
        # Mock Yandex failure
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.side_effect = Exception("Yandex API unavailable")
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should still succeed with partial results
        assert len(results['results']) == 2
        assert results['summary']['total_products'] == 2
        assert results['summary']['successful_sources'] == 2
        assert results['summary']['failed_sources'] == 1
        assert results['summary']['error_rate'] == pytest.approx(1/3, 0.01)
        
        # Check errors
        assert len(results['errors']) == 1
        assert results['errors'][0]['source'] == 'yandex'
        assert "Yandex API unavailable" in results['errors'][0]['error']

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_all_sources_failure(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with all sources failing."""
        # Mock all failures
        mock_wb_search.side_effect = Exception("Wildberries unavailable")
        mock_ozon_search.side_effect = Exception("Ozon unavailable")
        mock_yandex_search.side_effect = Exception("Yandex unavailable")
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should return empty results with errors
        assert len(results['results']) == 0
        assert results['summary']['total_products'] == 0
        assert results['summary']['successful_sources'] == 0
        assert results['summary']['failed_sources'] == 3
        assert results['summary']['error_rate'] == 1.0
        
        # Check all errors are present
        assert len(results['errors']) == 3
        error_sources = [error['source'] for error in results['errors']]
        assert 'wildberries' in error_sources
        assert 'ozon' in error_sources
        assert 'yandex' in error_sources

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_empty_results(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with empty results from all sources."""
        # Mock empty responses
        mock_wb_search.return_value = []
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should return empty results
        assert len(results['results']) == 0
        assert results['summary']['total_products'] == 0
        assert results['summary']['unique_products'] == 0
        assert results['summary']['successful_sources'] == 3
        assert results['summary']['failed_sources'] == 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_duplicate_products(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with duplicate products across sources."""
        # Mock products with same ID (should be treated as duplicates)
        wb_products = [
            Product(id="dup1", title="Телефон 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        ozon_products = [
            Product(id="dup1", title="Телефон 1", price=10500.0, url="https://ozon.ru/p1")  # Same ID
        ]
        
        yandex_products = [
            Product(id="dup2", title="Телефон 2", price=12000.0, url="https://market.yandex.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.return_value = yandex_products
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should have 3 products total but only 2 unique
        assert len(results['results']) == 3
        assert results['summary']['total_products'] == 3
        assert results['summary']['unique_products'] == 2  # dup1 and dup2

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_cache_hit(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with cache hit."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        
        # First search - should call the actual search
        results1 = await self.aggregator.search(self.test_query, use_cache=True)
        assert len(results1['results']) == 1
        assert results1['source_results']['wildberries']['cache_hit'] is False
        
        # Second search - should hit cache
        results2 = await self.aggregator.search(self.test_query, use_cache=True)
        assert len(results2['results']) == 1
        assert results2['source_results']['wildberries']['cache_hit'] is True
        
        # Verify mock was only called once
        assert mock_wb_search.call_count == 1

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_cache_disabled(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with cache disabled."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        
        # First search with cache disabled
        results1 = await self.aggregator.search(self.test_query, use_cache=False)
        assert len(results1['results']) == 1
        
        # Second search with cache disabled - should call search again
        results2 = await self.aggregator.search(self.test_query, use_cache=False)
        assert len(results2['results']) == 1
        
        # Verify mock was called twice
        assert mock_wb_search.call_count == 2

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_cache_expiration(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with cache expiration."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        
        # First search
        results1 = await self.aggregator.search(self.test_query, use_cache=True)
        assert results1['source_results']['wildberries']['cache_hit'] is False
        
        # Wait for cache to expire (TTL is 2 seconds)
        time.sleep(3)
        
        # Second search - should miss cache due to expiration
        results2 = await self.aggregator.search(self.test_query, use_cache=True)
        assert results2['source_results']['wildberries']['cache_hit'] is False
        
        # Verify mock was called twice
        assert mock_wb_search.call_count == 2

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_selected_sources(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with selected sources only."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        ozon_products = [
            Product(id="oz1", title="Телефон Ozon 1", price=12000.0, url="https://ozon.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.return_value = []
        
        # Search with only Wildberries
        results = await self.aggregator.search(self.test_query, sources=['wildberries'])
        
        assert len(results['results']) == 1
        assert results['summary']['total_products'] == 1
        assert results['summary']['total_sources'] == 1
        assert 'wildberries' in results['source_results']
        assert 'ozon' not in results['source_results']
        assert 'yandex' not in results['source_results']
        
        # Verify only Wildberries was called
        assert mock_wb_search.call_count == 1
        assert mock_ozon_search.call_count == 0
        assert mock_yandex_search.call_count == 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_timeout(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with timeout."""
        # Mock slow responses
        def slow_search(*args, **kwargs):
            time.sleep(2)
            return []
        
        # Configure mocks to be slow
        mock_wb_search.side_effect = slow_search
        mock_ozon_search.side_effect = slow_search
        mock_yandex_search.side_effect = slow_search
        
        # Execute search with short timeout
        with pytest.raises(Exception) as exc_info:
            await self.aggregator.search(self.test_query, timeout=1)
        
        assert "timed out after 1 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.get_trends')
    @patch('src.ru_search.ozon.OzonSearch.get_trends')
    @patch('src.ru_search.yandex.YandexSearch.get_trends')
    async def test_get_trends_success(self, mock_yandex_trends, mock_ozon_trends, mock_wb_trends):
        """Test successful trends aggregation."""
        from src.ru_search.base import TrendData
        
        # Mock trend data
        wb_trend = TrendData(
            query=self.test_query,
            trend_score=0.7,
            historical_data=[{'month': '2023-01', 'search_volume': 1000}]
        )
        
        ozon_trend = TrendData(
            query=self.test_query,
            trend_score=0.6,
            historical_data=[{'month': '2023-01', 'search_volume': 800}]
        )
        
        yandex_trend = TrendData(
            query=self.test_query,
            trend_score=0.8,
            historical_data=[{'month': '2023-01', 'search_volume': 1200}]
        )
        
        # Configure mocks
        mock_wb_trends.return_value = wb_trend
        mock_ozon_trends.return_value = ozon_trend
        mock_yandex_trends.return_value = yandex_trend
        
        # Execute trends search
        results = await self.aggregator.get_trends(self.test_query)
        
        # Assertions
        assert 'query' in results
        assert results['query'] == self.test_query
        assert 'trend_results' in results
        assert 'average_trend_score' in results
        assert 'errors' in results
        assert 'execution_time' in results
        assert 'timestamp' in results
        
        # Check trend results
        trend_results = results['trend_results']
        assert 'wildberries' in trend_results
        assert 'ozon' in trend_results
        assert 'yandex' in trend_results
        
        assert trend_results['wildberries']['trend_score'] == 0.7
        assert trend_results['ozon']['trend_score'] == 0.6
        assert trend_results['yandex']['trend_score'] == 0.8
        
        # Check average trend score
        assert results['average_trend_score'] == pytest.approx((0.7 + 0.6 + 0.8) / 3, 0.01)
        assert len(results['errors']) == 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.get_trends')
    @patch('src.ru_search.ozon.OzonSearch.get_trends')
    @patch('src.ru_search.yandex.YandexSearch.get_trends')
    async def test_get_trends_partial_failure(self, mock_yandex_trends, mock_ozon_trends, mock_wb_trends):
        """Test trends aggregation with partial failures."""
        from src.ru_search.base import TrendData
        
        # Mock trend data
        wb_trend = TrendData(
            query=self.test_query,
            trend_score=0.7,
            historical_data=[{'month': '2023-01', 'search_volume': 1000}]
        )
        
        # Mock failures
        mock_wb_trends.return_value = wb_trend
        mock_ozon_trends.side_effect = Exception("Ozon trends unavailable")
        mock_yandex_trends.side_effect = Exception("Yandex trends unavailable")
        
        # Execute trends search
        results = await self.aggregator.get_trends(self.test_query)
        
        # Should succeed with partial results
        assert results['average_trend_score'] == 0.7
        assert len(results['errors']) == 2
        
        error_sources = [error['source'] for error in results['errors']]
        assert 'ozon' in error_sources
        assert 'yandex' in error_sources

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_brand_distribution(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test brand distribution in summary."""
        # Mock products with different brands
        products = [
            Product(id="1", title="Телефон Xiaomi 1", price=10000.0, url="https://wb.ru/p1", brand="Xiaomi"),
            Product(id="2", title="Телефон Xiaomi 2", price=12000.0, url="https://wb.ru/p2", brand="Xiaomi"),
            Product(id="3", title="Телефон Samsung 1", price=15000.0, url="https://wb.ru/p3", brand="Samsung"),
            Product(id="4", title="Телефон Apple 1", price=50000.0, url="https://wb.ru/p4", brand="Apple"),
            Product(id="5", title="Телефон Unknown", price=8000.0, url="https://wb.ru/p5")  # No brand
        ]
        
        # Configure mocks
        mock_wb_search.return_value = products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Check brand distribution
        summary = results['summary']
        assert 'top_brands' in summary
        assert 'brand_diversity' in summary
        
        top_brands = summary['top_brands']
        assert len(top_brands) == 4  # Xiaomi, Samsung, Apple, Unknown
        
        # Xiaomi should be first (2 products)
        assert top_brands[0]['brand'] == "Xiaomi"
        assert top_brands[0]['count'] == 2
        
        # Check brand diversity
        assert summary['brand_diversity'] == 4  # Xiaomi, Samsung, Apple, Unknown

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_price_statistics(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test price statistics calculation."""
        # Mock products with various prices
        products = [
            Product(id="1", title="Телефон 1", price=5000.0, url="https://wb.ru/p1"),
            Product(id="2", title="Телефон 2", price=10000.0, url="https://wb.ru/p2"),
            Product(id="3", title="Телефон 3", price=15000.0, url="https://wb.ru/p3"),
            Product(id="4", title="Телефон 4", price=20000.0, url="https://wb.ru/p4"),
            Product(id="5", title="Телефон 5", price=25000.0, url="https://wb.ru/p5")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Check price statistics
        summary = results['summary']
        assert summary['total_products'] == 5
        assert summary['average_price'] == 15000.0
        assert summary['min_price'] == 5000.0
        assert summary['max_price'] == 25000.0
        assert summary['price_range'] == "5000.00 - 25000.00"

    def test_clear_cache(self):
        """Test cache clearing."""
        # Add some cache entries
        self.aggregator.cache.set("wildberries", "телефон", {"test": "data1"})
        self.aggregator.cache.set("ozon", "телефон", {"test": "data2"})
        
        assert len(self.aggregator.cache._cache) == 2
        
        # Clear cache
        self.aggregator.clear_cache()
        
        assert len(self.aggregator.cache._cache) == 0

    def test_context_manager(self):
        """Test context manager functionality."""
        with MarketDataAggregator() as aggregator:
            assert aggregator.cache_ttl == 21600
            assert aggregator.max_workers == 3
            # Context manager should work
        
        # Should be able to create and use normally after context
        aggregator2 = MarketDataAggregator()
        assert aggregator2.cache_ttl == 21600
        aggregator2.close()

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_with_metadata(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with product metadata preservation."""
        # Mock products with rich metadata
        products = [
            Product(
                id="1", 
                title="Телефон Xiaomi", 
                price=15000.0, 
                url="https://wb.ru/p1",
                brand="Xiaomi",
                rating=4.5,
                reviews_count=125,
                sales_count=500,
                is_available=True,
                is_new=False,
                is_sale=True
            )
        ]
        
        # Configure mocks
        mock_wb_search.return_value = products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Check metadata preservation
        result_product = results['results'][0]
        assert result_product.metadata['brand'] == "Xiaomi"
        assert result_product.metadata['rating'] == 4.5
        assert result_product.metadata['reviews_count'] == 125
        assert result_product.metadata['sales_count'] == 500
        assert result_product.metadata['is_available'] is True
        assert result_product.metadata['is_new'] is False
        assert result_product.metadata['is_sale'] is True

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_error_handling_graceful(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test graceful error handling in search."""
        # Mock some products and some errors
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Mock mixed results
        mock_wb_search.return_value = wb_products
        mock_ozon_search.side_effect = Exception("Ozon timeout")
        mock_yandex_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should return partial results gracefully
        assert len(results['results']) == 1
        assert results['summary']['successful_sources'] == 2  # Wildberries and Yandex
        assert results['summary']['failed_sources'] == 1  # Ozon
        assert len(results['errors']) == 1
        assert results['errors'][0]['source'] == 'ozon'

    @pytest.mark.asyncio
    async def test_search_concurrent_execution(self):
        """Test that searches execute concurrently."""
        import time
        
        # Mock slow searches
        def slow_search(query):
            time.sleep(1)
            return []
        
        with patch('src.ru_search.wildberries.WildberriesSearch.search', side_effect=slow_search):
            with patch('src.ru_search.ozon.OzonSearch.search', side_effect=slow_search):
                with patch('src.ru_search.yandex.YandexSearch.search', side_effect=slow_search):
                    start_time = time.time()
                    
                    # Execute search
                    results = await self.aggregator.search(self.test_query)
                    
                    execution_time = time.time() - start_time
                    
                    # Should be much faster than 3 seconds (sequential) due to parallel execution
                    assert execution_time < 2.0  # Allow some overhead

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    async def test_search_large_result_set(self, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with large result sets."""
        # Mock large number of products
        large_products = []
        for i in range(100):
            large_products.append(
                Product(id=f"prod{i}", title=f"Телефон {i}", price=10000.0 + i * 100, url=f"https://wb.ru/p{i}")
            )
        
        # Configure mocks
        mock_wb_search.return_value = large_products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should handle large result set
        assert len(results['results']) == 100
        assert results['summary']['total_products'] == 100
        assert results['summary']['unique_products'] == 100
        
        # Check that summary statistics are calculated correctly
        summary = results['summary']
        assert summary['average_price'] == pytest.approx(15000.0, 100)  # Average of 10000 to 109900
        assert summary['min_price'] == 10000.0
        assert summary['max_price'] == 109900.0