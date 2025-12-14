# Task 009: Testing

**Phase**: 4 - Testing & Deployment  
**Estimated Hours**: 5  
**Priority**: P1  
**Status**: Not Started

---

## Description

Implement comprehensive testing for the idea-planner-agent MVP including unit tests, integration tests, and test coverage reporting. This task ensures the application meets the >80% test coverage requirement.

---

## Acceptance Criteria

- [ ] Unit tests written for all core modules (>80% coverage) (Engineering Quality VI)
- [ ] Integration tests created for Telegram bot flow (NFR-003)
- [ ] Mock testing implemented for external APIs
- [ ] Test coverage reporting set up and working
- [ ] Test data created for all analysis modes
- [ ] All tests passing before deployment
- [ ] Test documentation completed

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 9.1 Write unit tests | 2.0 | Core module unit tests (>80% coverage) |
| 9.2 Create integration tests | 1.5 | Telegram bot integration tests |
| 9.3 Implement mock testing | 0.5 | Mock external APIs for testing |
| 9.4 Set up coverage reporting | 0.5 | Test coverage measurement and reporting |
| 9.5 Create test data | 0.5 | Test data for all modes and scenarios |

---

## Dependencies

**Depends on**: 
- Task 001-008 (All implementation tasks)

**Required for**: 
- Task 010 (Deployment) - tests must pass before deployment

---

## Testing Requirements

- [ ] Verify unit tests cover >80% of codebase
- [ ] Confirm integration tests cover main user flows
- [ ] Test all 11 analysis modes
- [ ] Validate error handling in all scenarios
- [ ] Test edge cases and error conditions
- [ ] Verify test coverage reporting accuracy
- [ ] Ensure all tests pass before deployment

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| Unit tests | Engineering Quality (VI) | NFR-003 |
| Integration tests | Reality-First (III) | NFR-003 |
| Mock testing | Traceability (II) | FR-008 |
| Coverage reporting | Citations (IV) | Constitution v0.1.1 |
| Test data | Resilience (VII) | US-4 |

---

## Implementation Notes

### Testing Structure

```
tests/
├── unit/
│   ├── test_ru_search.py          # ru_search module tests
│   ├── test_llm_integration.py     # LLM integration tests
│   ├── test_mode_analysis.py       # Mode analysis tests
│   ├── test_bot_handlers.py        # Telegram bot handler tests
│   └── test_database.py            # Database tests
├── integration/
│   ├── test_telegram_flow.py       # Telegram bot flow tests
│   ├── test_api_integration.py     # API integration tests
│   └── test_error_handling.py      # Error handling tests
├── conftest.py                    # Pytest configuration
├── test_data/                     # Test data files
│   ├── sample_ideas.json           # Sample business ideas
│   ├── mock_api_responses.json     # Mock API responses
│   └── expected_outputs/           # Expected outputs for comparison
└── requirements-test.txt           # Test dependencies
```

### Unit Tests Implementation

```python
# tests/unit/test_ru_search.py
import pytest
from ru_search import search, SearchResult
from unittest.mock import patch, MagicMock

class TestRuSearch:
    """Unit tests for ru_search module"""
    
    @patch('ru_search.search._search_wildberries')
    @patch('ru_search.search._search_ozon')
    @patch('ru_search.search._search_yandex')
    def test_search_all_sources(self, mock_yandex, mock_ozon, mock_wb):
        """Test search with all sources"""
        # Mock responses
        mock_wb.return_value = {
            'source': 'wb',
            'products': [{'title': 'Product 1', 'price': '1000 ₽'}],
            'price_range': '800-1200 ₽',
            'citation': '[https://wb.ru, 14.12.2025 15:30, "WB test"]'
        }
        
        mock_ozon.return_value = {
            'source': 'ozon',
            'products': [{'title': 'Product 2', 'price': '1100 ₽'}],
            'price_range': '900-1300 ₽',
            'citation': '[https://ozon.ru, 14.12.2025 15:30, "Ozon test"]'
        }
        
        mock_yandex.return_value = {
            'source': 'yandex',
            'trends': {'monthly_searches': 1000},
            'citation': '[https://yandex.ru, 14.12.2025 15:30, "Yandex test"]'
        }
        
        result = search("test query", sources=["wb", "ozon", "yandex"])
        
        assert isinstance(result, SearchResult)
        assert result.query == "test query"
        assert len(result.sources) == 3
        assert result.sources[0].source == "wb"
        assert result.sources[1].source == "ozon"
        assert result.sources[2].source == "yandex"
    
    def test_caching(self):
        """Test caching functionality"""
        with patch('ru_search.search._search_wildberries') as mock_wb:
            mock_wb.return_value = {
                'source': 'wb',
                'products': [],
                'price_range': 'test',
                'citation': '[https://wb.ru, 14.12.2025 15:30, "test"]'
            }
            
            # First call - should not be cached
            result1 = search("test query", sources=["wb"])
            assert result1.cache_hit is False
            
            # Second call - should be cached
            result2 = search("test query", sources=["wb"])
            assert result2.cache_hit is True
            
            # Should only call mock once due to caching
            assert mock_wb.call_count == 1
```

### Integration Tests

```python
# tests/integration/test_telegram_flow.py
import pytest
from telegram import Update, Message
from telegram.ext import ContextTypes
from bot.handlers import IdeaHandler
from unittest.mock import AsyncMock, MagicMock

class TestTelegramFlow:
    """Integration tests for Telegram bot flow"""
    
    @pytest.mark.asyncio
    async def test_idea_flow(self):
        """Test complete idea analysis flow"""
        # Create mock update and context
        update = Update(1, Message(1, 1, text="Производство посуды"))
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock handler dependencies
        handler = IdeaHandler()
        handler.report_generator.generate_report = AsyncMock(return_value=["Test report"])
        
        # Mock message methods
        mock_reply = AsyncMock()
        update.message.reply_text = mock_reply
        
        # Test flow
        await handler.handle_idea(update, context)
        
        # Verify progress message shown
        assert mock_reply.call_count >= 2
        
        # Verify report generated
        handler.report_generator.generate_report.assert_called_once()
        
        # Verify final message sent
        final_call = mock_reply.call_args_list[-1]
        assert "Test report" in final_call[0][0]
    
    @pytest.mark.asyncio
    async def test_mode_detection(self):
        """Test mode detection in messages"""
        update = Update(1, Message(1, 1, text="РЕЖИМ: БИЗНЕС-ПЛАН Производство посуды"))
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        handler = IdeaHandler()
        handler.report_generator.generate_report = AsyncMock(return_value=["Business plan report"])
        
        mock_reply = AsyncMock()
        update.message.reply_text = mock_reply
        
        await handler.handle_idea(update, context)
        
        # Verify mode detected and passed
        call_args = handler.report_generator.generate_report.call_args
        assert call_args[0][1] == "БИЗНЕС-ПЛАН"  # Mode should be passed
        
        # Verify mode mentioned in response
        final_call = mock_reply.call_args_list[-1]
        assert "БИЗНЕС-ПЛАН" in final_call[0][0]
```

### Mock Testing for External APIs

```python
# tests/conftest.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_wildberries_api():
    """Mock Wildberries API responses"""
    with patch('ru_search.wb.WildberriesScraper.search') as mock:
        mock.return_value = {
            'source': 'wb',
            'products': [
                {'title': 'Деревянная тарелка', 'price': '800 ₽', 'rating': 4.5},
                {'title': 'Деревянная ложка', 'price': '300 ₽', 'rating': 4.7}
            ],
            'price_range': '300-1200 ₽',
            'citation': '[https://wb.ru/search, 14.12.2025 15:30, "WB search for деревянная посуда"]'
        }
        yield mock

@pytest.fixture
def mock_ozon_api():
    """Mock Ozon API responses"""
    with patch('ru_search.ozon.OzonScraper.search') as mock:
        mock.return_value = {
            'source': 'ozon',
            'products': [
                {'title': 'Набор деревянной посуды', 'price': '1500 ₽', 'rating': 4.8},
                {'title': 'Деревянная чашка', 'price': '500 ₽', 'rating': 4.6}
            ],
            'price_range': '500-2000 ₽',
            'citation': '[https://ozon.ru/search, 14.12.2025 15:30, "Ozon search for деревянная посуда"]'
        }
        yield mock

@pytest.fixture
def mock_yandex_api():
    """Mock Yandex API responses"""
    with patch('ru_search.yandex.YandexScraper.get_trends') as mock:
        mock.return_value = {
            'source': 'yandex',
            'trends': {
                'monthly_searches': 15000,
                'trend': 'growing',
                'cpc': '45-80 ₽',
                'competition': 'medium'
            },
            'citation': '[https://wordstat.yandex.ru, 14.12.2025 15:30, "Yandex trends for деревянная посуда"]'
        }
        yield mock

@pytest.fixture
def mock_llm():
    """Mock LLM responses"""
    with patch('bot.llm_integration.LLMIntegration.generate_analysis') as mock:
        mock.return_value = """
        📋 КАРТОЧКА ИДЕИ
        
        **Идея:** Производство деревянной посуды
        **Проблема:** Нехватка экологичной посуды на рынке
        **Решение:** Производство посуды из березы и дуба
        **Целевая аудитория:** Эко-сознательные потребители 25-45 лет
        **Размер рынка:** 10-15 млн ₽/месяц
        **Конкуренты:** [Конкурент 1], [Конкурент 2]
        **Монетизация:** Прямые продажи, маркетплейсы
        **Риски:** Высокая конкуренция, сезонность
        
        📊 ПОЧЕМУ СЕЙЧАС
        
        Текущие тренды показывают рост спроса на эко-продукты на 25% год к году.
        """
        yield mock
```

### Test Coverage Configuration

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage configuration
addopts = --cov=src --cov=bot --cov=ru_search --cov=llm --cov-report=term-missing --cov-fail-under=80

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Async support
asyncio_mode = auto
```

### Test Data

```json
# tests/test_data/sample_ideas.json
{
  "ideas": [
    {
      "id": "idea_001",
      "text": "Производство деревянной посуды",
      "category": "Эко-продукты",
      "expected_sections": 7,
      "test_modes": ["ОЦЕНКА", "БИЗНЕС-ПЛАН", "МАРКЕТИНГ"]
    },
    {
      "id": "idea_002",
      "text": "Онлайн-курсы по программированию для детей",
      "category": "Образование",
      "expected_sections": 7,
      "test_modes": ["ОЦЕНКА", "ИСПОЛНЕНИЕ", "САЙТ"]
    },
    {
      "id": "idea_003",
      "text": "Сервис доставки здоровых обедов",
      "category": "FoodTech",
      "expected_sections": 7,
      "test_modes": ["ОЦЕНКА", "ОТЧЁТ 1", "ОТЧЁТ 2"]
    }
  ]
}
```

### Test Execution and Reporting

```bash
# Run tests with coverage
pytest --cov=src --cov=bot --cov=ru_search --cov=llm --cov-report=html

# Generate HTML report
pytest --cov-report=html:coverage_report

# Run specific test group
pytest tests/unit/test_ru_search.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Continuous Integration Setup

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: pytest tests/unit/ --cov --cov-fail-under=80
    
    - name: Run integration tests
      run: pytest tests/integration/ --cov --cov-fail-under=60
    
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        files: ./coverage.xml
```

---

## Success Criteria

- [ ] Unit tests cover >80% of core modules
- [ ] Integration tests cover main user flows
- [ ] All 11 analysis modes tested
- [ ] Error handling validated in tests
- [ ] Test coverage reporting working
- [ ] All tests passing before deployment
- [ ] Test documentation completed

---

## Next Tasks

- [ ] Task 010: Deployment (depends on successful testing)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1 (Engineering Quality VI)
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (NFR-003)
- **Plan**: `plan.md` Phase 4.1
- **Architecture**: `architecture-decisions.md` Testing Strategy section