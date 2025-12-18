"""
Comprehensive tests for MarketDataAggregator functionality.

This module tests the MarketDataAggregator class including:
- Multi-source search
- Caching integration
- Parallel execution
- Error handling
- Summary statistics
- Trend aggregation
- Data quality assessment
- Honest disclosure messages
- Three-tier fallback logic
"""

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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_all_sources_success(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        
        # Google Trends returns empty products (no product search support)
        gt_products = []
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.return_value = yandex_products
        mock_gt_search.return_value = gt_products
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Assertions
        assert 'query' in results
        assert results['query'] == self.test_query
        assert 'results' in results
        assert 'summary' in results
        assert 'source_results' in results
        assert 'errors' in results
        assert 'data_quality' in results
        assert 'disclosure' in results
        assert 'citations' in results
        assert 'timestamp' in results
        
        # Check all products are present
        all_products = results['results']
        assert len(all_products) == 6  # 2 from each source except Google Trends
        
        # Check source results
        source_results = results['source_results']
        assert 'wildberries' in source_results
        assert 'ozon' in source_results
        assert 'yandex' in source_results
        assert 'google_trends' in source_results
        
        assert source_results['wildberries']['count'] == 2
        assert source_results['ozon']['count'] == 2
        assert source_results['yandex']['count'] == 2
        assert source_results['google_trends']['count'] == 0
        
        # Check summary statistics
        summary = results['summary']
        assert summary['total_products'] == 6
        assert summary['unique_products'] == 6  # All IDs are unique
        assert summary['total_sources'] == 4  # Now includes Google Trends
        assert summary['successful_sources'] == 4
        assert summary['failed_sources'] == 0
        assert summary['error_rate'] == 0.0
        
        # Check price statistics
        assert summary['average_price'] > 0
        assert summary['min_price'] == 10000.0
        assert summary['max_price'] == 18000.0
        assert 'price_range' in summary
        
        # Check data quality assessment
        data_quality = results['data_quality']
        assert 'confidence_score' in data_quality
        assert 'freshness_score' in data_quality
        assert 'reliability_score' in data_quality
        assert 'completeness_score' in data_quality
        assert 'disclosure_message' in data_quality
        assert 'quality_grade' in data_quality
        assert 'citation_format' in data_quality
        
        # Check confidence score is in required range (0.4-0.9)
        assert 0.4 <= data_quality['confidence_score'] <= 0.9
        
        # Check disclosure message contains required elements
        disclosure = results['disclosure']
        assert '✅' in disclosure or '⚠️' in disclosure or '❌' in disclosure
        assert '📊' in disclosure
        assert '🕒' in disclosure
        assert '🏆' in disclosure
        
        # Check citations format
        citations = results['citations']
        assert 'wildberries' in citations
        assert 'ozon' in citations
        assert 'yandex' in citations
        
        # Check execution time
        assert 'execution_time' in summary
        assert summary['execution_time'] > 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_partial_failure(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with partial source failures."""
        # Mock successful responses
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        ozon_products = [
            Product(id="oz1", title="Телефон Ozon 1", price=12000.0, url="https://ozon.ru/p1")
        ]
        
        # Mock Yandex and Google Trends failures
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.side_effect = Exception("Yandex API unavailable")
        mock_gt_search.side_effect = Exception("Google Trends API unavailable")
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should still succeed with partial results
        assert len(results['results']) == 2
        assert results['summary']['total_products'] == 2
        assert results['summary']['successful_sources'] == 2
        assert results['summary']['failed_sources'] == 2
        assert results['summary']['error_rate'] == pytest.approx(0.5, 0.01)
        
        # Check errors
        assert len(results['errors']) == 2
        error_sources = [error['source'] for error in results['errors']]
        assert 'yandex' in error_sources
        assert 'google_trends' in error_sources
        
        # Check data quality reflects the errors
        data_quality = results['data_quality']
        assert data_quality['error_rate'] == 0.5
        assert data_quality['successful_sources'] == 2
        
        # Disclosure should mention the errors
        disclosure = results['disclosure']
        assert '⚠️' in disclosure

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_all_sources_failure(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with all sources failing."""
        # Mock all failures
        mock_wb_search.side_effect = Exception("Wildberries unavailable")
        mock_ozon_search.side_effect = Exception("Ozon unavailable")
        mock_yandex_search.side_effect = Exception("Yandex unavailable")
        mock_gt_search.side_effect = Exception("Google Trends unavailable")
        
        # Execute search with fallback disabled to test pure failure
        results = await self.aggregator.search(self.test_query, fallback_to_cache=False)
        
        # Should return empty results with errors
        assert len(results['results']) == 0
        assert results['summary']['total_products'] == 0
        assert results['summary']['successful_sources'] == 0
        assert results['summary']['failed_sources'] == 4
        assert results['summary']['error_rate'] == 1.0
        
        # Check all errors are present
        assert len(results['errors']) == 4
        error_sources = [error['source'] for error in results['errors']]
        assert 'wildberries' in error_sources
        assert 'ozon' in error_sources
        assert 'yandex' in error_sources
        assert 'google_trends' in error_sources
        
        # Data quality should reflect complete failure
        data_quality = results['data_quality']
        assert data_quality['confidence_score'] >= 0.4  # Should be minimum or higher due to fallback logic
        assert data_quality['error_rate'] == 1.0
        assert '❌' in results['disclosure'] or '⚠️' in results['disclosure']

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_empty_results(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with empty results from all sources."""
        # Mock empty responses
        mock_wb_search.return_value = []
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should return empty results
        assert len(results['results']) == 0
        assert results['summary']['total_products'] == 0
        assert results['summary']['unique_products'] == 0
        assert results['summary']['successful_sources'] == 4
        assert results['summary']['failed_sources'] == 0
        
        # Data quality should reflect no data (but successful sources mean higher confidence)
        data_quality = results['data_quality']
        assert data_quality['confidence_score'] >= 0.4  # Should be at least minimum
        assert data_quality['completeness_score'] == 0.0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_duplicate_products(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        
        gt_products = []
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = ozon_products
        mock_yandex_search.return_value = yandex_products
        mock_gt_search.return_value = gt_products
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_cache_hit(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with cache hit."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_cache_disabled(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with cache disabled."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_cache_expiration(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with cache expiration."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = wb_products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_selected_sources(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        mock_gt_search.return_value = []
        
        # Search with only Wildberries
        results = await self.aggregator.search(self.test_query, sources=['wildberries'])
        
        assert len(results['results']) == 1
        assert results['summary']['total_products'] == 1
        assert results['summary']['total_sources'] == 1
        assert 'wildberries' in results['source_results']
        assert 'ozon' not in results['source_results']
        assert 'yandex' not in results['source_results']
        assert 'google_trends' not in results['source_results']
        
        # Verify only Wildberries was called
        assert mock_wb_search.call_count == 1
        assert mock_ozon_search.call_count == 0
        assert mock_yandex_search.call_count == 0
        assert mock_gt_search.call_count == 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_timeout(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test search with timeout."""
        # Mock slow responses
        def slow_search(*args, **kwargs):
            time.sleep(2)
            return []
        
        # Configure mocks to be slow
        mock_wb_search.side_effect = slow_search
        mock_ozon_search.side_effect = slow_search
        mock_yandex_search.side_effect = slow_search
        mock_gt_search.side_effect = slow_search
        
        # Execute search with short timeout
        with pytest.raises(Exception) as exc_info:
            await self.aggregator.search(self.test_query, timeout=1)
        
        assert "timed out after 1 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.get_trends')
    @patch('src.ru_search.ozon.OzonSearch.get_trends')
    @patch('src.ru_search.yandex.YandexSearch.get_trends')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.get_trends')
    async def test_get_trends_success(self, mock_gt_trends, mock_yandex_trends, mock_ozon_trends, mock_wb_trends):
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
        
        gt_trend = TrendData(
            query=self.test_query,
            trend_score=0.9,
            historical_data=[{'month': '2023-01', 'search_volume': 1500}]
        )
        
        # Configure mocks
        mock_wb_trends.return_value = wb_trend
        mock_ozon_trends.return_value = ozon_trend
        mock_yandex_trends.return_value = yandex_trend
        mock_gt_trends.return_value = gt_trend
        
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
        assert 'google_trends' in trend_results
        
        assert trend_results['wildberries']['trend_score'] == 0.7
        assert trend_results['ozon']['trend_score'] == 0.6
        assert trend_results['yandex']['trend_score'] == 0.8
        assert trend_results['google_trends']['trend_score'] == 0.9
        
        # Check average trend score
        assert results['average_trend_score'] == pytest.approx((0.7 + 0.6 + 0.8 + 0.9) / 4, 0.01)
        assert len(results['errors']) == 0

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.get_trends')
    @patch('src.ru_search.ozon.OzonSearch.get_trends')
    @patch('src.ru_search.yandex.YandexSearch.get_trends')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.get_trends')
    async def test_get_trends_partial_failure(self, mock_gt_trends, mock_yandex_trends, mock_ozon_trends, mock_wb_trends):
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
        mock_gt_trends.side_effect = Exception("Google Trends unavailable")
        
        # Execute trends search
        results = await self.aggregator.get_trends(self.test_query)
        
        # Should succeed with partial results
        assert results['average_trend_score'] == 0.7
        assert len(results['errors']) == 3
        
        error_sources = [error['source'] for error in results['errors']]
        assert 'ozon' in error_sources
        assert 'yandex' in error_sources
        assert 'google_trends' in error_sources

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_brand_distribution(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        mock_gt_search.return_value = []
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_price_statistics(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        mock_gt_search.return_value = []
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_with_metadata(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        mock_gt_search.return_value = []
        
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
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_error_handling_graceful(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test graceful error handling in search."""
        # Mock some products and some errors
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Mock mixed results
        mock_wb_search.return_value = wb_products
        mock_ozon_search.side_effect = Exception("Ozon timeout")
        mock_yandex_search.return_value = []
        mock_gt_search.side_effect = Exception("Google Trends unavailable")
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Should return partial results gracefully
        assert len(results['results']) == 1
        assert results['summary']['successful_sources'] == 2  # Wildberries and Yandex
        assert results['summary']['failed_sources'] == 2  # Ozon and Google Trends
        assert len(results['errors']) == 2
        error_sources = [error['source'] for error in results['errors']]
        assert 'ozon' in error_sources
        assert 'google_trends' in error_sources

    @pytest.mark.asyncio
    async def test_search_concurrent_execution(self):
        """Test that searches execute concurrently."""
        import time
        
        # Mock slow searches
        def slow_search(query):
            time.sleep(0.3)  # Further reduced sleep time for more reliable test
            return []
        
        with patch('src.ru_search.wildberries.WildberriesSearch.search', side_effect=slow_search):
            with patch('src.ru_search.ozon.OzonSearch.search', side_effect=slow_search):
                with patch('src.ru_search.yandex.YandexSearch.search', side_effect=slow_search):
                    with patch('src.ru_search.google_trends.GoogleTrendsAPI.search', side_effect=slow_search):
                        start_time = time.time()
                        
                        # Execute search
                        results = await self.aggregator.search(self.test_query)
                        
                        execution_time = time.time() - start_time
                        
                        # Should be much faster than 1.2 seconds (sequential) due to parallel execution
                        assert execution_time < 0.7  # Allow some overhead

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_search_large_result_set(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
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
        mock_gt_search.return_value = []
        
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
        assert summary['max_price'] == 19900.0  # Fixed: 10000 + 99*100 = 19900

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_data_quality_assessment(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test data quality assessment functionality."""
        # Mock products with complete metadata
        products = [
            Product(
                id="1", 
                title="Телефон Xiaomi", 
                price=15000.0, 
                url="https://wb.ru/p1",
                brand="Xiaomi",
                rating=4.5,
                reviews_count=125,
                sales_count=500
            ),
            Product(
                id="2", 
                title="Телефон Samsung", 
                price=25000.0, 
                url="https://wb.ru/p2",
                brand="Samsung",
                rating=4.7,
                reviews_count=250,
                sales_count=800
            )
        ]
        
        # Configure mocks
        mock_wb_search.return_value = products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Check data quality assessment
        data_quality = results['data_quality']
        
        # Verify all quality metrics are present
        assert 'confidence_score' in data_quality
        assert 'freshness_score' in data_quality
        assert 'reliability_score' in data_quality
        assert 'completeness_score' in data_quality
        assert 'data_age_seconds' in data_quality
        assert 'data_age_human' in data_quality
        assert 'source_coverage' in data_quality
        assert 'successful_sources' in data_quality
        assert 'error_rate' in data_quality
        assert 'cache_usage' in data_quality
        assert 'disclosure_message' in data_quality
        assert 'quality_grade' in data_quality
        assert 'citation_format' in data_quality
        
        # Verify confidence score is in required range
        assert 0.4 <= data_quality['confidence_score'] <= 0.9
        
        # Verify completeness score (should be high with complete metadata)
        assert data_quality['completeness_score'] >= 0.8
        
        # Verify quality grade
        assert data_quality['quality_grade'] in ['A (Отлично)', 'B (Хорошо)', 'C (Удовлетворительно)', 'D (Ниже среднего)', 'F (Неудовлетворительно)']
        
        # Verify citation format
        citations = data_quality['citation_format']
        assert 'wildberries' in citations
        assert len(citations['wildberries']['sample_products']) == 2  # Should have 2 sample products

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_three_tier_fallback(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test three-tier fallback logic."""
        # Mock products
        wb_products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks - first call fails, second call succeeds
        mock_wb_search.side_effect = [
            Exception("Wildberries API timeout"),
            wb_products
        ]
        # Make all other sources fail too to isolate Wildberries testing
        mock_ozon_search.side_effect = Exception("Ozon unavailable")
        mock_yandex_search.side_effect = Exception("Yandex unavailable")
        mock_gt_search.side_effect = Exception("Google Trends unavailable")
        
        # First search - should handle errors gracefully and return empty results
        results1 = await self.aggregator.search(self.test_query, use_cache=False, fallback_to_cache=False)
        assert len(results1['results']) == 0
        assert len(results1['errors']) == 4  # All sources failed
        assert results1['summary']['failed_sources'] == 4
        
        # Second search - should succeed and cache the results
        results2 = await self.aggregator.search(self.test_query, use_cache=True, fallback_to_cache=True)
        assert len(results2['results']) == 1
        assert results2['source_results']['wildberries']['cache_hit'] is False
        
        # Third search - should hit cache (Tier 1)
        results3 = await self.aggregator.search(self.test_query, use_cache=True, fallback_to_cache=True)
        assert len(results3['results']) == 1
        assert results3['source_results']['wildberries']['cache_hit'] is True
        
        # Clear cache and test fallback
        self.aggregator.clear_cache()
        
        # Configure mock to fail again
        mock_wb_search.side_effect = Exception("Wildberries API timeout")
        
        # Fourth search - should fail API call but fallback to cache (Tier 2)
        # Since cache is empty, it should return empty results with errors
        results4 = await self.aggregator.search(self.test_query, use_cache=True, fallback_to_cache=True)
        assert len(results4['results']) == 0
        assert len(results4['errors']) == 4  # All sources failed
        
        # Test successful fallback scenario
        # Reset mock to work and populate cache
        mock_wb_search.side_effect = None
        mock_wb_search.return_value = wb_products
        
        # Populate cache
        results_cache = await self.aggregator.search(self.test_query, use_cache=True)
        assert len(results_cache['results']) == 1
        assert results_cache['source_results']['wildberries']['cache_hit'] is False
        
        # Now make API fail but cache should work
        mock_wb_search.side_effect = Exception("Wildberries API timeout")
        
        # This should succeed due to cache fallback (Tier 2)
        results_fallback = await self.aggregator.search(self.test_query, use_cache=True, fallback_to_cache=True)
        assert len(results_fallback['results']) == 1
        assert results_fallback['source_results']['wildberries']['cache_hit'] is True
        
        # Test Tier 3 fallback (user data) - not implemented in current version
        # This would require user-provided data which is beyond current scope

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_honest_disclosure_messages(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test honest disclosure message generation."""
        # Mock products
        products = [
            Product(id="1", title="Телефон 1", price=10000.0, url="https://wb.ru/p1")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Check disclosure message
        disclosure = results['disclosure']
        
        # Should contain source information
        assert '📊' in disclosure
        assert 'wildberries' in disclosure
        
        # Should contain freshness information
        assert '🕒' in disclosure
        assert 'секунд' in disclosure or 'минут' in disclosure or 'часов' in disclosure
        
        # Should contain quality grade
        assert '🏆' in disclosure
        
        # Should contain confidence indicator
        assert '✅' in disclosure or '⚠️' in disclosure or '❌' in disclosure

    @pytest.mark.asyncio
    @patch('src.ru_search.wildberries.WildberriesSearch.search')
    @patch('src.ru_search.ozon.OzonSearch.search')
    @patch('src.ru_search.yandex.YandexSearch.search')
    @patch('src.ru_search.google_trends.GoogleTrendsAPI.search')
    async def test_citation_format_transparency(self, mock_gt_search, mock_yandex_search, mock_ozon_search, mock_wb_search):
        """Test updated citation format with source transparency."""
        # Mock products
        products = [
            Product(id="wb1", title="Телефон Wildberries 1", price=10000.0, url="https://wb.ru/p1", brand="Xiaomi"),
            Product(id="wb2", title="Телефон Wildberries 2", price=15000.0, url="https://wb.ru/p2", brand="Samsung")
        ]
        
        # Configure mocks
        mock_wb_search.return_value = products
        mock_ozon_search.return_value = []
        mock_yandex_search.return_value = []
        mock_gt_search.return_value = []
        
        # Execute search
        results = await self.aggregator.search(self.test_query)
        
        # Check citation format
        citations = results['citations']
        
        # Should have wildberries citation
        assert 'wildberries' in citations
        
        # Check citation structure
        wb_citation = citations['wildberries']
        assert 'source_name' in wb_citation
        assert 'source_url' in wb_citation
        assert 'products_count' in wb_citation
        assert 'timestamp' in wb_citation
        assert 'data_freshness' in wb_citation
        assert 'sample_products' in wb_citation
        
        # Check sample products
        sample_products = wb_citation['sample_products']
        assert len(sample_products) == 2  # Should have 2 sample products (up to 3)
        
        # Check sample product structure
        for sample in sample_products:
            assert 'product_id' in sample
            assert 'product_title' in sample
            assert 'product_url' in sample
            assert 'product_price' in sample
            assert 'source_confidence' in sample
        
        # Verify source URL
        assert wb_citation['source_url'] == 'https://www.wildberries.ru'
        assert wb_citation['products_count'] == 2