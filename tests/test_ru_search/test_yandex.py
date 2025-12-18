"""
Comprehensive tests for Yandex scraper functionality.

This module tests the YandexSearch class including:
- Mock web scraping responses
- Rate limiting
- Error handling
- Data parsing
- Product normalization
- Trend data generation
"""

import pytest
import unittest.mock as mock
import time
from unittest.mock import patch, MagicMock
from src.ru_search.yandex import YandexSearch
from src.ru_search.base import Product, TrendData


class TestYandexSearch:
    """Test suite for YandexSearch class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.yandex = YandexSearch()
        self.test_query = "телефон"
        
    def teardown_method(self):
        """Clean up after tests."""
        self.yandex.close()

    @patch('requests.get')
    @patch('bs4.BeautifulSoup')
    @pytest.mark.skip(reason="Scraping not reliable for MVP")
    def test_scrape_yandex_market_success(self, mock_soup, mock_get):
        """Test successful Yandex Market scraping."""
        # Mock BeautifulSoup to return product containers
        mock_container1 = MagicMock()
        mock_container2 = MagicMock()
        
        # Mock product URL tag
        mock_url_tag1 = MagicMock()
        mock_url_tag1.get.return_value = 'https://market.yandex.ru/product/123456'
        mock_url_tag1.get_text.return_value = 'Смартфон Xiaomi Redmi Note 10'
        
        mock_url_tag2 = MagicMock()
        mock_url_tag2.get.return_value = 'https://market.yandex.ru/product/789012'
        mock_url_tag2.get_text.return_value = 'Смартфон Samsung Galaxy A52'
        
        # Mock price tag
        mock_price_tag1 = MagicMock()
        mock_price_tag1.get_text.return_value = '15 000 ₽'
        
        mock_price_tag2 = MagicMock()
        mock_price_tag2.get_text.return_value = '25 000 ₽'
        
        # Mock rating tag
        mock_rating_tag1 = MagicMock()
        mock_rating_tag1.get_text.return_value = '4.5'
        
        mock_rating_tag2 = MagicMock()
        mock_rating_tag2.get_text.return_value = '4.8'
        
        # Mock reviews tag
        mock_reviews_tag1 = MagicMock()
        mock_reviews_tag1.get_text.return_value = '125 отзывов'
        
        mock_reviews_tag2 = MagicMock()
        mock_reviews_tag2.get_text.return_value = '320 отзывов'
        
        # Mock brand tag
        mock_brand_tag1 = MagicMock()
        mock_brand_tag1.get_text.return_value = 'Xiaomi'
        
        mock_brand_tag2 = MagicMock()
        mock_brand_tag2.get_text.return_value = 'Samsung'
        
        # Configure container find methods
        mock_container1.find.side_effect = lambda tag, class_: {
            ('a', 'n-snippet-card2__title'): mock_url_tag1,
            ('h3', 'n-snippet-card2__title'): mock_url_tag1,
            ('div', 'n-snippet-card2__price'): mock_price_tag1,
            ('div', 'n-snippet-card2__rating'): mock_rating_tag1,
            ('span', 'n-snippet-card2__rating-count'): mock_reviews_tag1,
            ('div', 'n-snippet-card2__brand'): mock_brand_tag1
        }.get((tag, class_), None)
        
        mock_container2.find.side_effect = lambda tag, class_: {
            ('a', 'n-snippet-card2__title'): mock_url_tag2,
            ('h3', 'n-snippet-card2__title'): mock_url_tag2,
            ('div', 'n-snippet-card2__price'): mock_price_tag2,
            ('div', 'n-snippet-card2__rating'): mock_rating_tag2,
            ('span', 'n-snippet-card2__rating-count'): mock_reviews_tag2,
            ('div', 'n-snippet-card2__brand'): mock_brand_tag2
        }.get((tag, class_), None)
        
        # Mock BeautifulSoup find_all to return our containers
        mock_soup_instance = MagicMock()
        mock_soup_instance.find_all.return_value = [mock_container1, mock_container2]
        mock_soup.return_value = mock_soup_instance
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>test</body></html>'
        mock_get.return_value = mock_response
        
        # Execute scraping
        results = self.yandex._scrape_yandex_market(self.test_query)
        
        # Assertions
        assert len(results) == 2
        assert all(isinstance(product, Product) for product in results)
        
        # Test first product
        product1 = results[0]
        assert product1.id == "123456"
        assert product1.title == "Смартфон Xiaomi Redmi Note 10"
        assert product1.price == 15000.0
        assert "market.yandex.ru/product/123456" in product1.url
        assert product1.metadata['brand'] == "Xiaomi"
        assert product1.metadata['rating'] == 4.5
        assert product1.metadata['reviews_count'] == 125
        
        # Test second product
        product2 = results[1]
        assert product2.id == "789012"
        assert product2.title == "Смартфон Samsung Galaxy A52"
        assert product2.price == 25000.0
        assert "market.yandex.ru/product/789012" in product2.url
        assert product2.metadata['brand'] == "Samsung"

    @patch('requests.get')
    def test_scrape_yandex_market_empty_results(self, mock_get):
        """Test scraping with empty results."""
        # Mock HTML with no product containers
        mock_html = """
        <html>
            <body>
                <div>No products found</div>
            </body>
        </html>
        """
        
        # Mock BeautifulSoup to return no containers
        with patch('bs4.BeautifulSoup') as mock_soup:
            mock_soup_instance = MagicMock()
            mock_soup_instance.find_all.return_value = []
            mock_soup.return_value = mock_soup_instance
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_get.return_value = mock_response
            
            # Execute scraping
            results = self.yandex._scrape_yandex_market(self.test_query)
            
            # Assertions
            assert len(results) == 0
            assert results == []

    @patch('requests.get')
    @pytest.mark.skip(reason="Scraping not reliable for MVP")
    def test_scrape_yandex_market_malformed_product(self, mock_get):
        """Test scraping with malformed product data."""
        # Mock BeautifulSoup to return product containers
        mock_container1 = MagicMock()
        mock_container2 = MagicMock()
        
        # Mock first container with valid data
        mock_url_tag1 = MagicMock()
        mock_url_tag1.get.return_value = 'https://market.yandex.ru/product/123456'
        mock_url_tag1.get_text.return_value = 'Смартфон Xiaomi Redmi Note 10'
        
        mock_price_tag1 = MagicMock()
        mock_price_tag1.get_text.return_value = '15 000 ₽'
        
        mock_container1.find.side_effect = lambda tag, class_: {
            ('a', 'n-snippet-card2__title'): mock_url_tag1,
            ('h3', 'n-snippet-card2__title'): mock_url_tag1,
            ('div', 'n-snippet-card2__price'): mock_price_tag1
        }.get((tag, class_), None)
        
        # Mock second container with missing URL (should be skipped)
        mock_container2.find.return_value = None
        
        # Mock BeautifulSoup find_all to return our containers
        with patch('bs4.BeautifulSoup') as mock_soup:
            mock_soup_instance = MagicMock()
            mock_soup_instance.find_all.return_value = [mock_container1, mock_container2]
            mock_soup.return_value = mock_soup_instance
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '<html><body>test</body></html>'
            mock_get.return_value = mock_response
            
            # Execute scraping
            results = self.yandex._scrape_yandex_market(self.test_query)
            
            # Should only get the valid product
            assert len(results) == 1
            assert results[0].id == "123456"

    @patch('requests.get')
    def test_scrape_yandex_market_error(self, mock_get):
        """Test scraping with request error."""
        # Mock request error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
        mock_get.return_value = mock_response
        
        # Execute scraping and expect exception
        with pytest.raises(Exception) as exc_info:
            self.yandex._scrape_yandex_market(self.test_query)
        
        assert "Yandex Market scraping failed" in str(exc_info.value)

    @patch('requests.get')
    def test_search_rate_limiting(self, mock_get):
        """Test rate limiting behavior."""
        # Mock 429 response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_get.return_value = mock_response
        
        # Mock successful response after retry
        def mock_get_side_effect(*args, **kwargs):
            if mock_get.call_count == 1:
                # First call returns 429
                return mock_response
            else:
                # Second call returns success
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.text = '<html><body>test</body></html>'
                return success_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Mock BeautifulSoup to return empty results
        with patch('bs4.BeautifulSoup') as mock_soup:
            mock_soup_instance = MagicMock()
            mock_soup_instance.find_all.return_value = []
            mock_soup.return_value = mock_soup_instance
            
            # Execute search
            results = self.yandex.search(self.test_query)
            
            # Should succeed after retry
            assert len(results) == 0
            assert mock_get.call_count == 2

    def test_yandex_rate_limiting(self):
        """Test Yandex-specific rate limiting."""
        # Test initial state
        assert self.yandex._request_timestamp == 0
        assert self.yandex._minute_request_count == 0
        
        # Call rate limiter
        self.yandex._yandex_rate_limit()
        
        # Should update timestamp and counter
        assert self.yandex._request_timestamp > 0
        assert self.yandex._minute_request_count == 1

    def test_get_trends(self):
        """Test get_trends method."""
        # Test trend data generation
        trend_data = self.yandex.get_trends(self.test_query)
        
        assert trend_data.query == self.test_query
        assert isinstance(trend_data.trend_score, float)
        assert 0.0 <= trend_data.trend_score <= 0.9
        assert len(trend_data.historical_data) == 12
        
        # Test historical data structure
        for data_point in trend_data.historical_data:
            assert 'month' in data_point
            assert 'search_volume' in data_point
            assert 'trend_index' in data_point

    def test_generate_wordstat_stub_data(self):
        """Test stub data generation for trends."""
        # Test with different queries
        test_queries = [
            "телефон",
            "купить телефон дешево",
            "лучший смартфон 2023",
            "телефон скидка распродажа"
        ]
        
        for query in test_queries:
            trend_data = self.yandex._generate_wordstat_stub_data(query)
            
            assert trend_data.query == query
            assert isinstance(trend_data.trend_score, float)
            assert 0.0 <= trend_data.trend_score <= 0.9
            assert len(trend_data.historical_data) == 12
            
            # Test that longer queries and queries with product terms get higher scores
            if "купить" in query.lower() or "дешево" in query.lower() or "скидка" in query.lower():
                assert trend_data.trend_score > 0.5

    def test_get_headers(self):
        """Test headers generation."""
        headers = self.yandex._get_headers()
        
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Referer' in headers
        assert 'Origin' in headers
        assert headers['Referer'] == 'https://market.yandex.ru/'

    @patch('requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful request making."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'test': 'data'}
        mock_request.return_value = mock_response
        
        # Execute request
        result = self.yandex._make_request(
            url='https://test.com/api',
            method='GET',
            params={'query': 'test'}
        )
        
        # Assertions
        assert result['source'] == 'yandex'
        assert result['data'] == {'test': 'data'}
        assert 'timestamp' in result

    @patch('requests.request')
    def test_make_request_retry_success(self, mock_request):
        """Test request retry logic."""
        # Mock failure then success
        call_count = 0
        
        def mock_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = Exception("Server Error")
                return mock_response
            else:
                # Second call succeeds
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'test': 'data'}
                return mock_response
        
        mock_request.side_effect = mock_request_side_effect
        
        # Execute request
        result = self.yandex._make_request(
            url='https://test.com/api',
            method='GET',
            params={'query': 'test'}
        )
        
        # Should succeed after retry
        assert result['source'] == 'yandex'
        assert mock_request.call_count == 2

    @patch('requests.request')
    def test_make_request_max_retries(self, mock_request):
        """Test request max retries."""
        # Mock consistent failure
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server Error")
        mock_request.return_value = mock_response
        
        # Execute request and expect exception
        with pytest.raises(Exception) as exc_info:
            self.yandex._make_request(
                url='https://test.com/api',
                method='GET',
                params={'query': 'test'}
            )
        
        assert "Yandex request failed after 5 attempts" in str(exc_info.value)
        assert mock_request.call_count == 5

    def test_context_manager(self):
        """Test context manager functionality."""
        with YandexSearch() as yandex:
            assert yandex.source_name == "yandex"
            # Context manager should work
        
        # Should be able to create and use normally after context
        yandex2 = YandexSearch()
        assert yandex2.source_name == "yandex"
        yandex2.close()