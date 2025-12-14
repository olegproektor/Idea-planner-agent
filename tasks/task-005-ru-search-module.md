# Task 005: ru_search Module

**Phase**: 2 - Core Features  
**Estimated Hours**: 10  
**Priority**: P1  
**Status**: Not Started

---

## Description

Implement the ru_search module for gathering data from Russian market sources (Wildberries, Ozon, Yandex). This module provides the core data collection functionality for the idea-planner-agent.

---

## Acceptance Criteria

- [ ] Clean API implemented: `search(query, sources=["wb", "ozon", "yandex"])` (FR-010)
- [ ] Wildberries scraper with rate limiting and error handling (FR-011)
- [ ] Ozon scraper with proper authentication and data extraction (FR-012)
- [ ] Yandex Wordstat/Market integration with trend data (FR-013)
- [ ] Caching layer using `cachetools.TTLCache` (6-hour TTL) (FR-010)
- [ ] Data validation and normalization implemented
- [ ] Unit tests for search functionality (>80% coverage) (Engineering Quality VI)
- [ ] All sources respect ToS and ethical guidelines (Ethics VIII)

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 5.1 Design API interface | 1.0 | Create clean, documented API design |
| 5.2 Implement WB scraper | 3.0 | Wildberries data collection with rate limiting |
| 5.3 Implement Ozon scraper | 2.0 | Ozon API integration with error handling |
| 5.4 Implement Yandex integration | 2.0 | Yandex Wordstat and Market data |
| 5.5 Add caching layer | 1.0 | Implement cachetools.TTLCache integration |
| 5.6 Data validation | 0.5 | Normalize and validate collected data |
| 5.7 Write unit tests | 0.5 | Create tests with >80% coverage |

---

## Dependencies

**Depends on**: 
- Task 001 (Project Structure Setup) - for module structure
- Task 002 (Database Implementation) - for data storage
- Task 003 (Configuration System) - for API keys and settings

**Required for**: 
- Task 006 (Telegram Bot Logic) - uses this module for data
- Task 008 (Mode Analysis) - depends on data quality

---

## Testing Requirements

- [ ] Verify API interface works as documented
- [ ] Test WB scraper handles rate limits gracefully
- [ ] Confirm Ozon scraper handles authentication errors
- [ ] Validate Yandex integration returns proper trend data
- [ ] Test caching layer respects TTL settings
- [ ] Verify data validation catches invalid responses
- [ ] Confirm unit test coverage >80%

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| API design | Reality-First (III) | FR-010 |
| WB scraper | Russia-First (V) | FR-011, US-1 |
| Ozon scraper | Citations (IV) | FR-012, AC-1 |
| Yandex integration | Traceability (II) | FR-013, AC-2 |
| Caching layer | Engineering Quality (VI) | FR-010..FR-013 |
| Data validation | Ethics (VIII) | AC-3..AC-4 |
| Unit tests | Resilience (VII) | NFR-003 |

---

## Implementation Notes

### API Design

```python
# ru_search/__init__.py
from .search import search
from .models import SearchResult, SourceData

__all__ = ['search', 'SearchResult', 'SourceData']
```

```python
# ru_search/search.py
from typing import List, Optional
from dataclasses import dataclass
from cachetools import TTLCache
import time

# Cache configuration
cache = TTLCache(maxsize=1000, ttl=21600)  # 6 hours

@dataclass
class SourceData:
    """Data from a single source"""
    source: str  # 'wb', 'ozon', 'yandex'
    products: list
    price_range: Optional[str] = None
    citation: Optional[str] = None
    timestamp: Optional[str] = None

@dataclass
class SearchResult:
    """Complete search result"""
    query: str
    sources: List[SourceData]
    timestamp: str
    cache_hit: bool

def search(
    query: str,
    sources: List[str] = ["wb", "ozon", "yandex"],
    max_results: int = 20,
    cache_ttl: int = 21600
) -> SearchResult:
    """
    Search Russian market sources for product data
    
    Args:
        query: Search query (e.g., "деревянная посуда")
        sources: List of sources to search ('wb', 'ozon', 'yandex')
        max_results: Maximum number of results per source
        cache_ttl: Cache time-to-live in seconds
    
    Returns:
        SearchResult with data from all requested sources
    
    Acceptance Criteria:
        - FR-010: Caching with TTL
        - FR-011: WB data collection
        - FR-012: Ozon data collection
        - FR-013: Yandex data collection
        - AC-1..AC-4: Proper citations
    """
    # Create cache key
    cache_key = f"{query}:{','.join(sources)}"
    
    # Check cache first
    if cache_key in cache:
        cached_result = cache[cache_key]
        return SearchResult(
            query=query,
            sources=cached_result['sources'],
            timestamp=cached_result['timestamp'],
            cache_hit=True
        )
    
    # Collect data from sources
    source_data = []
    
    if "wb" in sources:
        wb_data = _search_wildberries(query, max_results)
        source_data.append(wb_data)
    
    if "ozon" in sources:
        ozon_data = _search_ozon(query, max_results)
        source_data.append(ozon_data)
    
    if "yandex" in sources:
        yandex_data = _search_yandex(query)
        source_data.append(yandex_data)
    
    # Create result and cache it
    result = {
        'query': query,
        'sources': source_data,
        'timestamp': _current_msk_time()
    }
    
    cache[cache_key] = result
    
    return SearchResult(
        query=query,
        sources=source_data,
        timestamp=result['timestamp'],
        cache_hit=False
    )
```

### Wildberries Scraper

```python
# ru_search/wb.py
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
from typing import List, Dict

WB_BASE_URL = "https://www.wildberries.ru"

class WildberriesScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'
        })
        self.rate_limit_delay = 2  # seconds between requests
    
    def search(self, query: str, max_results: int = 20) -> Dict:
        """
        Search Wildberries for products
        
        Acceptance Criteria:
            - FR-011: WB data collection
            - Ethics VIII: Respect ToS and rate limits
            - AC-1: Proper citations
        """
        search_url = f"{WB_BASE_URL}/catalog/0/search.aspx?search={query}"
        
        try:
            # Respect rate limits
            time.sleep(self.rate_limit_delay)
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract product data
            products = []
            product_cards = soup.select('.product-card')[:max_results]
            
            for card in product_cards:
                product = {
                    'title': card.select_one('.product-card__name').text.strip(),
                    'price': card.select_one('.price__current').text.strip(),
                    'rating': card.select_one('.product-card__rating')['aria-label'] if card.select_one('.product-card__rating') else None,
                    'url': WB_BASE_URL + card.select_one('a')['href']
                }
                products.append(product)
            
            # Calculate price range
            prices = [int(p['price'].replace('₽', '').replace(' ', '')) for p in products if p['price']]
            price_range = f"{min(prices)}–{max(prices)} ₽" if prices else "Нет данных"
            
            return {
                'source': 'wb',
                'products': products,
                'price_range': price_range,
                'citation': self._create_citation(query),
                'timestamp': self._current_msk_time()
            }
            
        except Exception as e:
            # Graceful degradation
            return {
                'source': 'wb',
                'products': [],
                'price_range': None,
                'citation': None,
                'timestamp': self._current_msk_time(),
                'error': str(e)
            }
    
    def _create_citation(self, query: str) -> str:
        """Create proper citation according to constitution"""
        timestamp = self._current_msk_time()
        return f"[{WB_BASE_URL}, {timestamp}, 'WB search results for {query}']"
    
    def _current_msk_time(self) -> str:
        """Get current time in MSK format"""
        from datetime import datetime
        import pytz
        msk_tz = pytz.timezone('Europe/Moscow')
        return datetime.now(msk_tz).strftime('%d.%m.%Y %H:%M')
```

### Ozon Scraper

```python
# ru_search/ozon.py
import requests
from typing import Dict, List
import time

OZON_API_URL = "https://api.ozon.ru/composer-api.bx/page/json/v2"

class OzonScraper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IdeaPlannerAgent/1.0',
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 1
    
    def search(self, query: str, max_results: int = 20) -> Dict:
        """
        Search Ozon for products using API
        
        Acceptance Criteria:
            - FR-012: Ozon data collection
            - Ethics VIII: Proper API usage
            - AC-2: Data freshness indicators
        """
        params = {
            'text': query,
            'page': 1,
            'page_size': max_results
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(OZON_API_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            products = []
            
            for item in data.get('widgetStates', {}).get('catalog', {}).get('items', []):
                product = {
                    'title': item.get('name', ''),
                    'price': item.get('price', {}).get('price', ''),
                    'rating': item.get('rating', {}).get('value', None),
                    'url': f"https://www.ozon.ru{item.get('link', '')}"
                }
                products.append(product)
            
            # Calculate price range
            prices = []
            for p in products:
                if p['price']:
                    try:
                        prices.append(int(p['price'].replace('₽', '').replace(' ', '')))
                    except:
                        pass
            
            price_range = f"{min(prices)}–{max(prices)} ₽" if prices else "Нет данных"
            
            return {
                'source': 'ozon',
                'products': products,
                'price_range': price_range,
                'citation': self._create_citation(query),
                'timestamp': self._current_msk_time()
            }
            
        except Exception as e:
            return {
                'source': 'ozon',
                'products': [],
                'price_range': None,
                'citation': None,
                'timestamp': self._current_msk_time(),
                'error': str(e)
            }
    
    def _create_citation(self, query: str) -> str:
        """Create proper citation"""
        timestamp = self._current_msk_time()
        return f"[{OZON_API_URL}, {timestamp}, 'Ozon search results for {query}']"
    
    def _current_msk_time(self) -> str:
        """Get current time in MSK format"""
        from datetime import datetime
        import pytz
        msk_tz = pytz.timezone('Europe/Moscow')
        return datetime.now(msk_tz).strftime('%d.%m.%Y %H:%M')
```

### Yandex Integration

```python
# ru_search/yandex.py
import requests
from typing import Dict
import time

YANDEX_WORDSTAT_URL = "https://wordstat.yandex.ru"

class YandexScraper:
    def __init__(self, token: str = None):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IdeaPlannerAgent/1.0',
            'Accept': 'application/json'
        })
    
    def get_trends(self, query: str) -> Dict:
        """
        Get Yandex Wordstat trends for query
        
        Acceptance Criteria:
            - FR-013: Yandex data collection
            - Ethics VIII: Respect ToS
            - AC-3: Source validation
        """
        try:
            # Note: This is a simplified example
            # Real implementation would use proper Yandex API
            time.sleep(1)  # Rate limiting
            
            # Mock data for example
            trends = {
                'query': query,
                'monthly_searches': 10000,
                'trend': 'growing',
                'cpc': '50-100 ₽',
                'competition': 'medium'
            }
            
            return {
                'source': 'yandex',
                'trends': trends,
                'citation': self._create_citation(query),
                'timestamp': self._current_msk_time()
            }
            
        except Exception as e:
            return {
                'source': 'yandex',
                'trends': {},
                'citation': None,
                'timestamp': self._current_msk_time(),
                'error': str(e)
            }
    
    def _create_citation(self, query: str) -> str:
        """Create proper citation"""
        timestamp = self._current_msk_time()
        return f"[{YANDEX_WORDSTAT_URL}, {timestamp}, 'Yandex Wordstat data for {query}']"
    
    def _current_msk_time(self) -> str:
        """Get current time in MSK format"""
        from datetime import datetime
        import pytz
        msk_tz = pytz.timezone('Europe/Moscow')
        return datetime.now(msk_tz).strftime('%d.%m.%Y %H:%M')
```

### Data Validation and Normalization

```python
# ru_search/validation.py
from typing import Dict, List
from dataclasses import asdict

def validate_search_result(result: Dict) -> Dict:
    """
    Validate and normalize search results
    
    Acceptance Criteria:
        - AC-3: Source validation
        - AC-4: Data accuracy
        - Engineering Quality VI: Robust validation
    """
    validated = {}
    
    # Validate required fields
    if not result.get('source'):
        raise ValueError("Source is required")
    
    validated['source'] = result['source']
    
    # Normalize products
    if result.get('products'):
        validated['products'] = []
        for product in result['products']:
            normalized_product = {
                'title': product.get('title', '').strip() or 'Без названия',
                'price': product.get('price', '').strip() or 'Нет данных',
                'rating': product.get('rating') or None,
                'url': product.get('url', '').strip() or None
            }
            validated['products'].append(normalized_product)
    
    # Validate price range
    price_range = result.get('price_range', '').strip()
    if price_range and '₽' not in price_range:
        price_range = f"{price_range} ₽"
    validated['price_range'] = price_range or 'Нет данных'
    
    # Validate citation format
    citation = result.get('citation')
    if citation:
        # Check citation format: [URL, DD.MM.YYYY HH:MM, "description"]
        if not (citation.startswith('[') and ']' in citation):
            raise ValueError(f"Invalid citation format: {citation}")
    
    validated['citation'] = citation
    validated['timestamp'] = result.get('timestamp')
    
    return validated
```

### Unit Tests

```python
# tests/test_ru_search.py
import pytest
from ru_search import search, SearchResult
from ru_search.validation import validate_search_result

class TestRuSearch:
    """Test ru_search module functionality"""
    
    def test_search_api(self):
        """Test basic search API"""
        result = search("деревянная посуда", sources=["wb"])
        assert isinstance(result, SearchResult)
        assert result.query == "деревянная посуда"
        assert len(result.sources) == 1
        assert result.sources[0].source == "wb"
    
    def test_caching(self, monkeypatch):
        """Test caching functionality"""
        # First call - should not be cached
        result1 = search("test query", sources=["wb"])
        assert result1.cache_hit is False
        
        # Second call - should be cached
        result2 = search("test query", sources=["wb"])
        assert result2.cache_hit is True
        assert result2.query == result1.query
    
    def test_data_validation(self):
        """Test data validation"""
        test_data = {
            'source': 'wb',
            'products': [
                {'title': 'Product 1', 'price': '1000 ₽', 'rating': 4.5}
            ],
            'price_range': '800-1200',
            'citation': '[https://wb.ru, 14.12.2025 15:30, "test citation"]',
            'timestamp': '14.12.2025 15:30'
        }
        
        validated = validate_search_result(test_data)
        assert validated['source'] == 'wb'
        assert validated['price_range'] == '800-1200 ₽'
        assert validated['citation'] == test_data['citation']
    
    def test_error_handling(self, monkeypatch):
        """Test graceful error handling"""
        # Mock a failed request
        result = search("nonexistent product", sources=["wb"])
        assert result.sources[0].source == "wb"
        assert result.sources[0].products == []
        # Should not crash, should return empty results
```

---

## Success Criteria

- [ ] ru_search module API working as specified
- [ ] All three data sources (WB, Ozon, Yandex) implemented
- [ ] Caching layer properly integrated with 6-hour TTL
- [ ] Data validation and normalization working
- [ ] Unit test coverage >80%
- [ ] All ethical guidelines and ToS respected
- [ ] Module ready for integration with Telegram bot

---

## Next Tasks

- [ ] Task 006: Telegram Bot Logic (depends on this task)
- [ ] Task 008: Mode Analysis (depends on data quality)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1 (Ethics VIII, Reality-First III)
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (FR-010..FR-013, AC-1..AC-4)
- **Plan**: `plan.md` Phase 2.1
- **Architecture**: `architecture-decisions.md` ru_search section