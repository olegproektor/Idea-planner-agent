# Task-005: Refactor ru_search Module to Use Public APIs

## Overview
Refactor the ru_search module to replace scraping with public API access, addressing the 403 Forbidden issues while maintaining functionality and improving data quality transparency.

## Current Status
- **Blocking Issue**: WB/Ozon scraping returns 403 Forbidden
- **Impact**: Market analysis functionality broken
- **Solution**: Implement three-tier data access strategy (docs/data-access-mvp-strategy.md)

## Subtasks

### Subtask 2.1.1: Implement WildberriesPublicAPI
**Status**: Not Started
**Mode**: Code
**Objective**: Replace scraping with Wildberries public API endpoints

**Requirements**:
- Replace `src/ru_search/wildberries.py` scraping with public API
- Use endpoint: `https://search.wb.ru/exactmatch/ru/common/v4/search`
- Implement rate limiting: 1 request/second
- Set User-Agent: 'idea-planner-agent/0.1.0'
- Handle 403/429 errors with exponential backoff
- Return structured data matching existing schema

**Implementation**:
```python
class WildberriesPublicAPI:
    BASE_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    RATE_LIMIT = 1.0  # 1 request per second
    USER_AGENT = "idea-planner-agent/0.1.0"
    
    def __init__(self):
        self.last_request_time = 0
        self.session = httpx.AsyncClient()
    
    async def search(self, query: str, timeout: int = 30):
        # Implement rate limiting
        # Make API request with proper headers
        # Parse response into structured format
        # Handle errors gracefully
        pass
```

### Subtask 2.1.2: Add GoogleTrendsAPI
**Status**: Not Started
**Mode**: Code
**Objective**: Replace Yandex.Wordstat with Google Trends API

**Requirements**:
- Install pytrends library (`pip install pytrends`)
- Implement `get_interest_over_time()` method
- Implement `get_related_queries()` method
- Return data in format compatible with existing analysis
- Handle API rate limits and quotas

**Implementation**:
```python
from pytrends.request import TrendReq

class GoogleTrendsAPI:
    def __init__(self):
        self.trends = TrendReq(hl='ru-RU', tz=360)
    
    def get_interest_over_time(self, keywords: list, timeframe: str = 'today 12-m'):
        # Get interest over time data
        # Return normalized values
        pass
    
    def get_related_queries(self, keyword: str):
        # Get related queries and topics
        # Return structured data
        pass
```

### Subtask 2.1.3: Update MarketDataAggregator
**Status**: Not Started
**Mode**: Code
**Objective**: Add data quality assessment and honest disclosure

**Requirements**:
- Add `data_quality` assessment to all responses
- Implement honest disclosure messages per Constitution Section 4
- Update citation format to include source transparency
- Add data freshness tracking
- Implement confidence scoring (0.4-0.9 range)

**Implementation**:
```python
class MarketDataAggregator:
    def __init__(self, cache_ttl: int = 21600):  # 6 hours
        self.wb_api = WildberriesPublicAPI()
        self.trends_api = GoogleTrendsAPI()
        self.cache = MarketDataCache(ttl_hours=6)
        self.data_quality_assessor = DataQualityAssessor()
    
    async def search(self, query: str, sources: list, use_cache: bool = True):
        results = {}
        data_quality = {
            'sources': [],
            'warnings': [],
            'confidence_score': 0.4,
            'disclosure': ""
        }
        
        # Implement tiered data access
        # Add quality assessment
        # Generate honest disclosure
        
        return {
            'results': results,
            'data_quality': data_quality,
            'citations': []
        }
```

### Subtask 2.1.4: Fix Failing Tests
**Status**: Not Started
**Mode**: Code
**Objective**: Update test suite for new API structure

**Requirements**:
- Update mocks in `tests/test_ru_search/` to match new API responses
- Target: 100% test pass rate
- Verify coverage >80%
- Add integration tests for fallback logic
- Test rate limiting behavior

**Test Updates Needed**:
- `tests/test_ru_search/test_wildberries.py`
- `tests/test_ru_search/test_aggregator.py`
- Add new `tests/test_ru_search/test_google_trends.py`

## Success Criteria

### Functional
- [ ] WildberriesPublicAPI returns structured product data
- [ ] GoogleTrendsAPI provides interest and related query data
- [ ] MarketDataAggregator implements three-tier fallback
- [ ] All responses include data_quality metrics
- [ ] Honest disclosure messages included per Constitution

### Quality
- [ ] 100% test pass rate
- [ ] >80% code coverage
- [ ] No 403/429 errors in production
- [ ] Graceful degradation working
- [ ] Rate limiting properly implemented

### Compliance
- [ ] Constitution Principle VII (Graceful Degradation)
- [ ] Constitution Principle VIII (Ethics)
- [ ] Constitution Section 4 (Citation Format)
- [ ] Data quality transparency requirements

## Timeline
- **18.12**: Subtask 2.1.1 (WildberriesPublicAPI)
- **19.12**: Subtask 2.1.2 (GoogleTrendsAPI)
- **20.12**: Subtask 2.1.3 (MarketDataAggregator updates)
- **21.12**: Subtask 2.1.4 (Test fixes and coverage)

## Dependencies
- `httpx` for HTTP requests
- `pytrends` for Google Trends access
- Existing `src/ru_search/base.py` interfaces
- Constitution compliance requirements

## References
- docs/data-access-mvp-strategy.md
- docs/mvp-status.md
- .specify/constitution.md Section 4
- tests/test_ru_search/* (existing test suite)