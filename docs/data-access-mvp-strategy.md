# Data Access MVP Strategy (18.12.2025)

## Overview

This document outlines the data access strategy for the Idea Planner Agent MVP, addressing the current blocking issues with WB/Ozon scraping (403 Forbidden) while maintaining ethical standards and graceful degradation principles.

## Current Problem

- **WB/Ozon Scraping Blocked**: Both platforms return 403 Forbidden errors
- **No Paid API Access**: Cannot use Ozon Seller API or Yandex.XML (paid services)
- **LLM Integration Missing**: Groq API not yet implemented
- **Impact**: Market analysis functionality is broken, blocking MVP completion

## MVP Data Access Strategy

### Tier 1: Free Public APIs (Primary Source)

#### 1. Wildberries Public API
- **Endpoint**: `https://search.wb.ru/exactmatch/ru/common/v4/search`
- **Access**: Free, no authentication required
- **Limitations**: 
  - Rate limited (unknown exact limits)
  - Basic product data only
  - No historical pricing
- **Implementation**: 
  ```python
  # Example request
  import httpx
  
  async def fetch_wb_data(query: str):
      url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?query={query}&resultset=catalog"
      async with httpx.AsyncClient() as client:
          response = await client.get(url)
          return response.json()
  ```

#### 2. Google Trends API
- **Endpoint**: `https://trends.google.com/trends/api/explore`
- **Access**: Free, no authentication required
- **Data Available**:
  - Search volume trends
  - Regional interest
  - Related queries
  - Seasonality patterns
- **Implementation**: Use unofficial Python wrapper or direct HTTP requests

### Tier 2: User-Provided Data (Fallback)

#### CSV Upload Feature
- **Implementation**: Telegram bot command `/upload`
- **Format**: Standardized CSV template
- **Fields**: 
  ```
  product_name,price_rub,category,brand,rating,reviews_count,url
  ```
- **Validation**: Schema validation with Pydantic
- **Storage**: Temporary in-memory processing (no persistent storage for privacy)

#### Manual Data Entry
- **Implementation**: Interactive Telegram form
- **Fields**: Product name, price, category, estimated demand
- **Use Case**: Single product analysis when no API data available

### Tier 3: Cached Data (Graceful Degradation)

#### Cache Strategy
- **TTL**: 6 hours (adjustable via config)
- **Storage**: SQLite with JSON blobs
- **Key Structure**: `{query}_{source}_{timestamp}`
- **Fallback Logic**:
  1. Try Tier 1 (Public APIs)
  2. If 403/429 → Use cached data if < 6h old
  3. If no cache → Prompt user for Tier 2 data
  4. If no user data → Return partial analysis with data_quality warnings

#### Cache Implementation
```python
from datetime import datetime, timedelta
import json

class MarketDataCache:
    def __init__(self, ttl_hours=6):
        self.ttl = timedelta(hours=ttl_hours)
        self.cache = {}
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, key, data):
        self.cache[key] = (data, datetime.now())
```

## Data Quality Metrics

### Transparency Requirements

Each analysis response must include:

```json
{
  "data_quality": {
    "sources": [
      {
        "name": "wildberries",
        "type": "public_api",
        "freshness": "live",
        "coverage": "partial"
      },
      {
        "name": "user_upload",
        "type": "manual",
        "freshness": "static",
        "coverage": "complete"
      }
    ],
    "warnings": [
      "Ozon data unavailable due to API restrictions",
      "Yandex Market data unavailable due to paid access requirements",
      "Price data may be up to 6 hours old"
    ],
    "confidence_score": 0.65,
    "recommendation": "Consider supplementing with manual market research"
  }
}
```

### Quality Score Calculation

```python
def calculate_data_quality(sources):
    base_score = 0.4  # Minimum for cached/user data
    
    for source in sources:
        if source["type"] == "public_api":
            base_score += 0.2
        if source["freshness"] == "live":
            base_score += 0.15
        if source["coverage"] == "complete":
            base_score += 0.1
    
    return min(base_score, 0.9)  # Max 0.9 for MVP (not production-grade)
```

## Implementation Plan

### Phase 1: Tier 1 Implementation (18-19.12.2025)
- [ ] Refactor `ru_search/wildberries.py` to use Public API
- [ ] Add Google Trends integration
- [ ] Implement cache layer with 6h TTL
- [ ] Add data_quality metric calculation

### Phase 2: Tier 2 Implementation (20.12.2025)
- [ ] Add `/upload` command handler
- [ ] Implement CSV parsing with Pydantic validation
- [ ] Add interactive data entry form
- [ ] Integrate user data into analysis pipeline

### Phase 3: Graceful Degradation (21.12.2025)
- [ ] Implement fallback logic in `market_search_handler`
- [ ] Add data quality warnings to all responses
- [ ] Update error messages to guide users to Tier 2 options
- [ ] Add constitution compliance checks

## Constitution Compliance

### Principle VIII: Ethics
- **Honest Disclosure**: Clear labeling of data sources and limitations
- **No Misrepresentation**: Explicit warnings about data gaps
- **User Consent**: Optional data upload with clear privacy terms

### Principle VII: Graceful Degradation
- **Tiered Fallback**: Three-tier system ensures some data always available
- **Transparency**: Data quality metrics in every response
- **User Empowerment**: Multiple ways for users to provide data
- **No Silent Failures**: All limitations clearly communicated

## Risk Assessment

### Risks
1. **API Rate Limiting**: WB Public API may block frequent requests
   - Mitigation: Implement exponential backoff + cache
2. **Data Staleness**: 6h cache may be too old for some analyses
   - Mitigation: Allow user override with fresh data upload
3. **User Data Quality**: Manual entries may be inaccurate
   - Mitigation: Validation + confidence scoring
4. **Legal Compliance**: Scraping terms may change
   - Mitigation: Regular review + fallback to Tier 2/3

### Acceptance Criteria
- [ ] 80% of queries return Tier 1 data
- [ ] 100% of queries return some data (no empty responses)
- [ ] All responses include data_quality metrics
- [ ] No 403/429 errors in production logs
- [ ] User satisfaction > 3.5/5 in feedback

## References
- Constitution Principle VIII (Ethics)
- Constitution Principle VII (Graceful Degradation)
- MVP Status Report (docs/mvp-status.md)
- Task-005 Refactoring Plan