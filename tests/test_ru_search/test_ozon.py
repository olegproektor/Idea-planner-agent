"""
Comprehensive tests for Ozon scraper functionality.

This module tests the OzonSearch class including:
- Mock API and web scraping responses
- Rate limiting
- Error handling
- Data parsing
- Product normalization
- API fallback to web scraping
"""

import pytest
import unittest.mock as mock
import time
from unittest.mock import patch, MagicMock
from src.ru_search.ozon import OzonSearch
from src.ru_search.base import Product


class TestOzonSearch:
    """Test suite for OzonSearch class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.ozon = OzonSearch()
        self.test_query = "телефон"
        
    def teardown_method(self):
        """Clean up after tests."""
        self.ozon.close()

    @patch('requests.get')
    def test_api_search_success(self, mock_get):
        """Test successful API search with mock response."""
        # Mock API response data
        mock_response_data = {
            'data': {
                'products': [
                    {
                        'id': 123456,
                        'name': 'Смартфон Xiaomi Redmi Note 10',
                        'price': {'price': 1500000, 'oldPrice': 1800000},  # in kopecks
                        'rating': {'rating': 4.5, 'count': 125},
                        'brand': {'name': 'Xiaomi'},
                        'isAvailable': True,
                        'isNew': False,
                        'isSale': True
                    },
                    {
                        'id': 789012,
                        'name': 'Смартфон Samsung Galaxy A52',
                        'price': {'price': 2500000, 'oldPrice': 2800000},  # in kopecks
                        'rating': {'rating': 4.8, 'count': 320},
                        'brand': {'name': 'Samsung'},
                        'isAvailable': True,
                        'isNew': True,
                        'isSale': False
                    }
                ]
            }
        }
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        # Execute API search
        results = self.ozon._api_search(self.test_query)
        
        # Assertions
        assert len(results) == 2
        assert all(isinstance(product, Product) for product in results)
        
        # Test first product
        product1 = results[0]
        assert product1.id == "123456"
        assert product1.title == "Смартфон Xiaomi Redmi Note 10"
        assert product1.price == 15000.0
        assert "xiaomi" in product1.url.lower()
        assert product1.metadata['brand'] == "Xiaomi"
        assert product1.metadata['rating'] == 4.5
        assert product1.metadata['reviews_count'] == 125
        
        # Test second product
        product2 = results[1]
        assert product2.id == "789012"
        assert product2.title == "Смартфон Samsung Galaxy A52"
        assert product2.price == 25000.0
        assert "samsung" in product2.url.lower()
        assert product2.metadata['brand'] == "Samsung"

    @patch('requests.get')
    def test_web_scrape_search_success(self, mock_get):
        """Test successful web scraping search."""
        # Mock HTML response with NEXT_DATA
        mock_html = """
        <html>
            <body>
                <script id="__NEXT_DATA__" type="application/json">
                    {
                        "props": {
                            "pageProps": {
                                "searchResults": {
                                    "items": [
                                        {
                                            "id": 123456,
                                            "title": "Смартфон Xiaomi Redmi Note 10",
                                            "price": {"price": 1500000, "oldPrice": 1800000},
                                            "rating": {"rating": 4.5, "count": 125},
                                            "brand": {"name": "Xiaomi"},
                                            "available": true,
                                            "new": false,
                                            "sale": true
                                        },
                                        {
                                            "id": 789012,
                                            "title": "Смартфон Samsung Galaxy A52",
                                            "price": {"price": 2500000, "oldPrice": 2800000},
                                            "rating": {"rating": 4.8, "count": 320},
                                            "brand": {"name": "Samsung"},
                                            "available": true,
                                            "new": true,
                                            "sale": false
                                        }
                                    ]
                                }
                            }
                        }
                    }
                </script>
            </body>
        </html>
        """
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # Execute web scrape search
        results = self.ozon._web_scrape_search(self.test_query)
        
        # Assertions
        assert len(results) == 2
        assert all(isinstance(product, Product) for product in results)
        
        # Test first product
        product1 = results[0]
        assert product1.id == "123456"
        assert product1.title == "Смартфон Xiaomi Redmi Note 10"
        assert product1.price == 15000.0
        assert product1.metadata['brand'] == "Xiaomi"

    @patch('requests.get')
    def test_search_api_fallback_to_web(self, mock_get):
        """Test search with API failure falling back to web scraping."""
        # Mock API failure then web scraping success
        def mock_get_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            
            if 'api-seller.ozon.ru' in url:
                # API call - return error
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = Exception("API Error")
                return mock_response
            elif 'www.ozon.ru/search' in url:
                # Web scraping call - return success
                mock_html = """
                <html>
                    <body>
                        <script id="__NEXT_DATA__" type="application/json">
                            {
                                "props": {
                                    "pageProps": {
                                        "searchResults": {
                                            "items": [
                                                {
                                                    "id": 123456,
                                                    "title": "Смартфон Xiaomi Redmi Note 10",
                                                    "price": {"price": 1500000},
                                                    "rating": {"rating": 4.5, "count": 125},
                                                    "brand": {"name": "Xiaomi"},
                                                    "available": true
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        </script>
                    </body>
                </html>
                """
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = mock_html
                return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Execute search
        results = self.ozon.search(self.test_query)
        
        # Should succeed with web scraping
        assert len(results) == 1
        assert results[0].id == "123456"

    @patch('requests.get')
    def test_search_empty_results(self, mock_get):
        """Test search with empty results."""
        # Mock empty API response
        mock_response_data = {'data': {'products': []}}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        # Execute API search
        results = self.ozon._api_search(self.test_query)
        
        # Assertions
        assert len(results) == 0
        assert results == []

    @patch('requests.get')
    def test_search_malformed_product(self, mock_get):
        """Test search with malformed product data."""
        # Mock response with malformed product
        mock_response_data = {
            'data': {
                'products': [
                    {
                        'id': 123456,
                        'name': 'Смартфон Xiaomi Redmi Note 10',
                        'price': {'price': 1500000},
                        'rating': {'rating': 4.5, 'count': 125},
                        'brand': {'name': 'Xiaomi'},
                        'isAvailable': True
                    },
                    {
                        # Missing required fields
                        'id': 789012,
                        # Missing name, price, etc.
                    }
                ]
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        # Execute API search
        results = self.ozon._api_search(self.test_query)
        
        # Should only get the valid product
        assert len(results) == 1
        assert results[0].id == "123456"

    @patch('requests.get')
    def test_search_api_error(self, mock_get):
        """Test search with API error."""
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
        mock_get.return_value = mock_response
        
        # Execute API search and expect exception
        with pytest.raises(Exception) as exc_info:
            self.ozon._api_search(self.test_query)
        
        assert "Ozon API search failed" in str(exc_info.value)

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
                success_response.json.return_value = {
                    'data': {
                        'products': [{
                            'id': 123456,
                            'name': 'Смартфон Xiaomi Redmi Note 10',
                            'price': {'price': 1500000},
                            'rating': {'rating': 4.5, 'count': 125},
                            'brand': {'name': 'Xiaomi'},
                            'isAvailable': True
                        }]
                    }
                }
                return success_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Execute search
        results = self.ozon.search(self.test_query)
        
        # Should succeed after retry
        assert len(results) == 1
        assert mock_get.call_count == 2

    def test_ozon_rate_limiting(self):
        """Test Ozon-specific rate limiting."""
        # Test initial state
        assert self.ozon._request_timestamp == 0
        assert self.ozon._minute_request_count == 0
        
        # Call rate limiter
        self.ozon._ozon_rate_limit()
        
        # Should update timestamp and counter
        assert self.ozon._request_timestamp > 0
        assert self.ozon._minute_request_count == 1

    def test_get_trends(self):
        """Test get_trends method."""
        # Test basic trend data
        trend_data = self.ozon.get_trends(self.test_query)
        
        assert trend_data.query == self.test_query
        assert trend_data.trend_score == 0.5  # Neutral score for Ozon
        assert trend_data.historical_data == []

    def test_parse_product_data(self):
        """Test API product data parsing."""
        # Test product data parsing
        product_data = {
            'id': 123456,
            'name': 'Смартфон Xiaomi Redmi Note 10',
            'price': {'price': 1500000, 'oldPrice': 1800000},
            'rating': {'rating': 4.5, 'count': 125},
            'brand': {'name': 'Xiaomi'},
            'isAvailable': True,
            'isNew': False,
            'isSale': True
        }
        
        product = self.ozon._parse_product_data(product_data)
        
        assert product.id == "123456"
        assert product.title == "Смартфон Xiaomi Redmi Note 10"
        assert product.price == 15000.0
        assert product.metadata['brand'] == "Xiaomi"
        assert product.metadata['rating'] == 4.5
        assert product.metadata['reviews_count'] == 125
        assert product.metadata['is_available'] is True

    def test_parse_web_product_data(self):
        """Test web scraping product data parsing."""
        # Test web product data parsing
        product_data = {
            'id': 123456,
            'title': 'Смартфон Xiaomi Redmi Note 10',
            'price': {'price': 1500000, 'oldPrice': 1800000},
            'rating': {'rating': 4.5, 'count': 125},
            'brand': {'name': 'Xiaomi'},
            'available': True,
            'new': False,
            'sale': True
        }
        
        product = self.ozon._parse_web_product_data(product_data)
        
        assert product.id == "123456"
        assert product.title == "Смартфон Xiaomi Redmi Note 10"
        assert product.price == 15000.0
        assert product.metadata['brand'] == "Xiaomi"
        assert product.metadata['rating'] == 4.5
        assert product.metadata['reviews_count'] == 125
        assert product.metadata['is_available'] is True

    def test_get_headers(self):
        """Test headers generation."""
        headers = self.ozon._get_headers()
        
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Referer' in headers
        assert 'Origin' in headers
        assert headers['Referer'] == 'https://www.ozon.ru/'

    @patch('requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful request making."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'test': 'data'}
        mock_request.return_value = mock_response
        
        # Execute request
        result = self.ozon._make_request(
            url='https://test.com/api',
            method='GET',
            params={'query': 'test'}
        )
        
        # Assertions
        assert result['source'] == 'ozon'
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
        result = self.ozon._make_request(
            url='https://test.com/api',
            method='GET',
            params={'query': 'test'}
        )
        
        # Should succeed after retry
        assert result['source'] == 'ozon'
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
            self.ozon._make_request(
                url='https://test.com/api',
                method='GET',
                params={'query': 'test'}
            )
        
        assert "Request failed after 5 attempts" in str(exc_info.value)
        assert mock_request.call_count == 5

    def test_context_manager(self):
        """Test context manager functionality."""
        with OzonSearch() as ozon:
            assert ozon.source_name == "ozon"
            # Context manager should work
        
        # Should be able to create and use normally after context
        ozon2 = OzonSearch()
        assert ozon2.source_name == "ozon"
        ozon2.close()