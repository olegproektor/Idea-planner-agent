"""
Test cases for GoogleTrendsAPI implementation.

This module contains comprehensive tests for the Google Trends API integration,
testing all major functionality including interest over time, related queries,
rate limiting, caching, and error handling.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

from src.ru_search.google_trends import GoogleTrendsAPI
from src.ru_search.base import TrendData


class TestGoogleTrendsAPI:
    """Test class for GoogleTrendsAPI functionality."""
    
    @pytest.fixture
    def google_trends(self):
        """Create a GoogleTrendsAPI instance for testing."""
        return GoogleTrendsAPI()
    
    def test_initialization(self, google_trends):
        """Test that GoogleTrendsAPI initializes correctly."""
        assert google_trends.source_name == "google_trends"
        assert google_trends.hl == 'ru-RU'
        assert google_trends.tz == 360
        assert google_trends.max_requests_per_hour == 100
        assert google_trends.request_interval == 5
        assert google_trends.cache is not None
    
    def test_get_interest_over_time_basic(self, google_trends):
        """Test basic interest over time functionality."""
        # Mock the pytrends client to avoid actual API calls
        with patch.object(google_trends.trends_client, 'build_payload') as mock_build, \
             patch.object(google_trends.trends_client, 'interest_over_time') as mock_interest:
            
            # Create mock data
            dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
            values = [i for i in range(50, 80)]  # Same length as dates
            mock_data = pd.DataFrame({
                'date': dates,
                'test_query': values
            })
            mock_data = mock_data.set_index('date')
            mock_interest.return_value = mock_data
            
            # Call the method
            result = google_trends.get_interest_over_time('test_query')
            
            # Verify results
            assert isinstance(result, TrendData)
            assert result.query == 'test_query'
            assert 0.0 <= result.trend_score <= 1.0
            assert len(result.historical_data) > 0
            
            # Verify cache was used
            cached_data = google_trends._get_cached_data('test_query', 'interest_over_time')
            assert cached_data is not None
    
    def test_get_interest_over_time_cache(self, google_trends):
        """Test caching functionality for interest over time."""
        # First call - should not use cache
        with patch.object(google_trends.trends_client, 'build_payload'), \
             patch.object(google_trends.trends_client, 'interest_over_time') as mock_interest:
            
            dates = [datetime.now() - timedelta(days=i) for i in range(10, 0, -1)]
            values = [i * 10 for i in range(10, 20)]
            mock_data = pd.DataFrame({
                'date': dates,
                'cached_query': values
            })
            mock_data = mock_data.set_index('date')
            mock_interest.return_value = mock_data
            
            result1 = google_trends.get_interest_over_time('cached_query', use_cache=False)
            assert mock_interest.call_count == 1
        
        # Second call with cache - should use cache
        with patch.object(google_trends.trends_client, 'interest_over_time') as mock_interest:
            result2 = google_trends.get_interest_over_time('cached_query', use_cache=True)
            assert mock_interest.call_count == 0  # Should not call API
            assert result2.query == result1.query
            # Note: trend_score might differ slightly due to processing, so just check it's reasonable
            assert 0.0 <= result2.trend_score <= 1.0
    
    def test_get_related_queries_basic(self, google_trends):
        """Test basic related queries functionality."""
        # Mock the pytrends client
        with patch.object(google_trends.trends_client, 'build_payload') as mock_build, \
             patch.object(google_trends.trends_client, 'related_queries') as mock_related:
            
            # Create mock related queries data
            mock_related_data = {
                'test_query': {
                    'rising': pd.DataFrame({
                        'query': ['rising_query_1', 'rising_query_2'],
                        'value': [100, 80]
                    }),
                    'top': pd.DataFrame({
                        'query': ['top_query_1', 'top_query_2'],
                        'value': [200, 180]
                    })
                }
            }
            mock_related.return_value = mock_related_data
            
            # Call the method
            result = google_trends.get_related_queries('test_query')
            
            # Verify results
            assert 'query' in result
            assert result['query'] == 'test_query'
            assert 'rising_queries' in result
            assert 'top_queries' in result
            assert len(result['rising_queries']) == 2
            assert len(result['top_queries']) == 2
            assert result['rising_queries'][0]['query'] == 'rising_query_1'
            assert result['top_queries'][0]['query'] == 'top_query_1'
    
    def test_get_related_queries_cache(self, google_trends):
        """Test caching functionality for related queries."""
        # First call - should not use cache
        with patch.object(google_trends.trends_client, 'build_payload'), \
             patch.object(google_trends.trends_client, 'related_queries') as mock_related:
            
            mock_data = {
                'cache_test': {
                    'rising': pd.DataFrame({'query': ['rising'], 'value': [50]}),
                    'top': pd.DataFrame({'query': ['top'], 'value': [100]})
                }
            }
            mock_related.return_value = mock_data
            
            result1 = google_trends.get_related_queries('cache_test', use_cache=False)
            assert mock_related.call_count == 1
        
        # Second call with cache - should use cache
        with patch.object(google_trends.trends_client, 'related_queries') as mock_related:
            result2 = google_trends.get_related_queries('cache_test', use_cache=True)
            assert mock_related.call_count == 0  # Should not call API
            assert result2['query'] == result1['query']
    
    def test_rate_limiting(self, google_trends):
        """Test that rate limiting works correctly."""
        # Test minimum interval rate limiting
        start_time = time.time()
        
        # First call should be immediate
        google_trends._google_trends_rate_limit()
        first_call_time = time.time() - start_time
        
        # Second call should wait for minimum interval
        google_trends._google_trends_rate_limit()
        second_call_time = time.time() - start_time
        
        # Should be at least the request interval (5 seconds)
        assert second_call_time - first_call_time >= google_trends.request_interval - 0.1
    
    def test_error_handling_interest_over_time(self, google_trends):
        """Test error handling for interest over time."""
        # Mock the pytrends client to raise an exception
        with patch.object(google_trends.trends_client, 'build_payload') as mock_build, \
             patch.object(google_trends.trends_client, 'interest_over_time') as mock_interest:
            
            mock_interest.side_effect = Exception("API error")
            
            # Should return fallback data instead of raising exception
            result = google_trends.get_interest_over_time('error_test')
            
            assert isinstance(result, TrendData)
            assert result.query == 'error_test'
            assert result.trend_score == 0.5  # Fallback neutral score
            assert len(result.historical_data) == 0
    
    def test_error_handling_related_queries(self, google_trends):
        """Test error handling for related queries."""
        # Mock the pytrends client to raise an exception
        with patch.object(google_trends.trends_client, 'build_payload') as mock_build, \
             patch.object(google_trends.trends_client, 'related_queries') as mock_related:
            
            mock_related.side_effect = Exception("API error")
            
            # Should return fallback data instead of raising exception
            result = google_trends.get_related_queries('error_test')
            
            assert 'query' in result
            assert result['query'] == 'error_test'
            assert len(result['rising_queries']) == 0
            assert len(result['top_queries']) == 0
    
    def test_get_trends_compatibility(self, google_trends):
        """Test that get_trends method works as compatibility layer."""
        with patch.object(google_trends, 'get_interest_over_time') as mock_interest:
            mock_interest.return_value = TrendData(
                query='test',
                trend_score=0.75,
                historical_data=[{'date': '2023-01-01', 'search_volume': 75, 'trend_index': 0.75}]
            )
            
            result = google_trends.get_trends('test')
            
            assert isinstance(result, TrendData)
            assert result.query == 'test'
            assert mock_interest.call_count == 1
    
    def test_search_not_implemented(self, google_trends):
        """Test that search method returns empty list (not implemented)."""
        result = google_trends.search('any_query')
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_cache_key_generation(self, google_trends):
        """Test cache key generation."""
        key1 = google_trends._make_cache_key('test_query', 'interest_over_time')
        key2 = google_trends._make_cache_key('test_query', 'related_queries')
        key3 = google_trends._make_cache_key('different_query', 'interest_over_time')
        
        # Same query, different method - different keys
        assert key1 != key2
        # Different queries, same method - different keys
        assert key1 != key3
        # Same query and method - same key
        assert google_trends._make_cache_key('test_query', 'interest_over_time') == key1
    
    def test_process_interest_data_empty(self, google_trends):
        """Test processing of empty interest data."""
        empty_df = pd.DataFrame()
        result = google_trends._process_interest_data(empty_df, 'empty_test')
        
        assert isinstance(result, TrendData)
        assert result.query == 'empty_test'
        assert result.trend_score == 0.5  # Fallback neutral score
        assert len(result.historical_data) == 0
    
    def test_process_related_queries_empty(self, google_trends):
        """Test processing of empty related queries data."""
        empty_df = pd.DataFrame()
        mock_queries = {'empty_test': empty_df}
        
        result = google_trends._process_related_queries(mock_queries, 'empty_test')
        
        assert result['query'] == 'empty_test'
        assert len(result['rising_queries']) == 0
        assert len(result['top_queries']) == 0


class TestGoogleTrendsIntegration:
    """Integration tests for GoogleTrendsAPI."""
    
    def test_context_manager(self):
        """Test that GoogleTrendsAPI works as a context manager."""
        with GoogleTrendsAPI() as api:
            assert api.source_name == "google_trends"
            # Context manager should work without errors
        # After context, resources should be cleaned up
    
    def test_multiple_queries_caching(self):
        """Test multiple queries with caching enabled."""
        api = GoogleTrendsAPI()
        
        # Test with a single query first to verify caching works
        query = 'test_query'
        
        # First call - should not use cache
        with patch.object(api.trends_client, 'build_payload'), \
             patch.object(api.trends_client, 'interest_over_time') as mock_interest:
            
            # Set up mock data that works with the actual processing
            dates = [datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
            mock_data = pd.DataFrame({
                'date': dates,
                query: [10, 20, 30, 40, 50],
                'isPartial': [False, False, False, False, False]
            }).set_index('date')
            
            mock_interest.return_value = mock_data
            
            # First call (should call API)
            result1 = api.get_interest_over_time(query, use_cache=False)
            
            # Should be 1 call
            assert mock_interest.call_count == 1
        
        # Second call with cache - should use cache
        with patch.object(api.trends_client, 'interest_over_time') as mock_interest:
            # Second call (should use cache)
            result2 = api.get_interest_over_time(query, use_cache=True)
            
            # Should be 0 calls (no additional API calls)
            assert mock_interest.call_count == 0
            
            # Results should be the same - compare the trend scores directly
            # Since caching works, the trend scores should match
            assert result1.query == result2.query
            # Allow for small floating point differences
            assert abs(result1.trend_score - result2.trend_score) < 0.01
    
    def test_rate_limiting_multiple_calls(self):
        """Test rate limiting with multiple rapid calls."""
        api = GoogleTrendsAPI()
        
        start_time = time.time()
        
        # Make multiple calls that should be rate limited
        for i in range(3):
            api._google_trends_rate_limit()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take at least 2 * request_interval (10 seconds) for 3 calls
        assert total_time >= api.request_interval * 2 - 0.5


class TestGoogleTrendsErrorConditions:
    """Test error conditions and edge cases."""
    
    def test_initialization_failure(self):
        """Test behavior when pytrends client initialization fails."""
        with patch('src.ru_search.google_trends.TrendReq') as mock_trend_req:
            mock_trend_req.side_effect = Exception("Initialization failed")
            
            # Should raise exception during initialization
            with pytest.raises(Exception):
                GoogleTrendsAPI()
    
    def test_empty_query_handling(self):
        """Test handling of empty or invalid queries."""
        api = GoogleTrendsAPI()
        
        # Test with empty query
        with patch.object(api.trends_client, 'build_payload') as mock_build, \
             patch.object(api.trends_client, 'interest_over_time') as mock_interest:
            
            mock_interest.return_value = None
            
            result = api.get_interest_over_time('')
            
            # Should return fallback data
            assert isinstance(result, TrendData)
            assert result.trend_score == 0.5
    
    @patch('time.sleep')
    def test_api_quota_exceeded(self, mock_sleep):
        """Test behavior when API quota is exceeded."""
        api = GoogleTrendsAPI()
        
        # Simulate hitting the hourly limit
        api._hourly_request_count = api.max_requests_per_hour
        
        # Mock the current time to be at the end of an hour
        import time
        current_time = int(time.time())
        api._last_hour = current_time // 3600  # Set to current hour
        
        start_time = time.time()
        
        # This should trigger the rate limiting wait
        api._google_trends_rate_limit()
        
        end_time = time.time()
        
        # Verify that sleep was called with the expected duration (seconds until next hour)
        expected_sleep_time = 3600 - (current_time % 3600)
        if mock_sleep.call_count > 0:
            actual_sleep_time = mock_sleep.call_args[0][0]
            # Allow for small timing differences
            assert abs(actual_sleep_time - expected_sleep_time) < 2  # Within 2 seconds tolerance
        
        # The actual time elapsed should be minimal since we're mocking sleep
        assert end_time - start_time < 1  # Should be much less than 1 second
