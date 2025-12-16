"""
ru_search module - Russian market data search and aggregation.

This module provides comprehensive search capabilities for Russian e-commerce
platforms including Wildberries, Ozon, and Yandex Market. It includes:

- Data source implementations for major Russian marketplaces
- Caching system for improved performance
- Market data aggregator for combining results from multiple sources
- Trend analysis using available APIs

Main components:
- DataSource: Abstract base class for all data sources
- Product: Data class representing products
- TrendData: Data class representing trend information
- WildberriesSearch: Wildberries marketplace data source
- OzonSearch: Ozon marketplace data source
- YandexSearch: Yandex Market data source
- SearchCache: TTL-based caching system
- MarketDataAggregator: Aggregates data from multiple sources
"""

# Import base classes and data structures
from .base import Product, TrendData, DataSource

# Import data source implementations
from .wildberries import WildberriesSearch
from .ozon import OzonSearch
from .yandex import YandexSearch

# Import caching system
from .cache import SearchCache

# Import aggregator
from .aggregator import MarketDataAggregator

# Module-level initialization
__all__ = [
    'Product',
    'TrendData', 
    'DataSource',
    'WildberriesSearch',
    'OzonSearch',
    'YandexSearch',
    'SearchCache',
    'MarketDataAggregator'
]

# Initialize module-level components
def _initialize_module():
    """Initialize module-level components and perform any setup."""
    # Module is ready for use
    pass

# Perform module initialization
_initialize_module()