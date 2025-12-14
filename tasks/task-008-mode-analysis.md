# Task 008: Mode Analysis

**Phase**: 3 - Analysis Engine  
**Estimated Hours**: 15  
**Priority**: P2  
**Status**: Not Started

---

## Description

Implement mode-specific analysis logic for all 11 analysis modes. This task extends the basic functionality to provide specialized, mode-focused analysis that leverages the LLM integration and market data.

---

## Acceptance Criteria

- [ ] Mode-specific analysis logic implemented for all 11 modes (US-2)
- [ ] Mode-specific prompt engineering completed (Engineering Quality VI)
- [ ] Each mode produces distinguishable, focused results (SC-004)
- [ ] All modes maintain 7-section report structure (US-1)
- [ ] Mode-specific features working correctly
- [ ] Unit tests for each mode (>80% coverage)
- [ ] Integration with Telegram bot completed

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 8.1 Implement ОЦЕНКА mode | 1.0 | Default balanced analysis |
| 8.2 Implement БИЗНЕС-ПЛАН mode | 2.0 | Investor-focused financial analysis |
| 8.3 Implement МАРКЕТИНГ mode | 2.0 | Customer acquisition and branding |
| 8.4 Implement ИСПОЛНЕНИЕ mode | 2.0 | Operational implementation details |
| 8.5 Implement САЙТ mode | 1.5 | Website structure and content |
| 8.6 Implement ОТЧЁТ 1-3 modes | 3.0 | Deep dive report modes |
| 8.7 Implement section-specific modes | 2.0 | ПОЧЕМУ_СЕЙЧАС, РЫНОЧНЫЙ_РАЗРЫВ, ДОКАЗАТЕЛЬСТВА |
| 8.8 Write unit tests | 1.5 | Mode-specific tests (>80% coverage) |

---

## Dependencies

**Depends on**: 
- Task 006 (Telegram Bot Logic) - base report generation
- Task 007 (LLM Integration) - LLM functionality
- Task 005 (ru_search Module) - market data

**Required for**: Complete MVP functionality

---

## Testing Requirements

- [ ] Verify each mode produces distinct, focused results
- [ ] Test all modes maintain 7-section structure
- [ ] Confirm mode-specific features work correctly
- [ ] Validate prompt engineering produces quality outputs
- [ ] Test error handling for each mode
- [ ] Verify unit test coverage >80% for all modes

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| Mode implementation | Russia-First (V) | US-2, SC-004 |
| Prompt engineering | Reality-First (III) | Engineering Quality VI |
| Focused results | Citations (IV) | FR-004 |
| 7-section structure | Traceability (II) | US-1 |
| Unit tests | Engineering Quality (VI) | NFR-003 |

---

## Implementation Notes

### Mode Analysis Architecture

```python
# bot/mode_analysis.py
from typing import Dict, List
from bot.llm_integration import LLMIntegration
from ru_search import search

class ModeAnalyzer:
    """Mode-specific analysis engine"""
    
    def __init__(self):
        self.llm = LLMIntegration()
        self.mode_handlers = {
            "ОЦЕНКА": self._handle_default_mode,
            "БИЗНЕС-ПЛАН": self._handle_business_plan_mode,
            "МАРКЕТИНГ": self._handle_marketing_mode,
            "ИСПОЛНЕНИЕ": self._handle_execution_mode,
            "САЙТ": self._handle_website_mode,
            "ОТЧЁТ 1": self._handle_report_1_mode,
            "ОТЧЁТ 2": self._handle_report_2_mode,
            "ОТЧЁТ 3": self._handle_report_3_mode,
            "ПОЧЕМУ_СЕЙЧАС": self._handle_timing_mode,
            "РЫНОЧНЫЙ_РАЗРЫВ": self._handle_gap_mode,
            "ДОКАЗАТЕЛЬСТВА": self._handle_evidence_mode
        }
    
    async def analyze(
        self,
        idea: str,
        mode: str = "ОЦЕНКА",
        market_data: dict = None
    ) -> Dict:
        """
        Perform mode-specific analysis
        
        Args:
            idea: Business idea text
            mode: Analysis mode
            market_data: Pre-collected market data
            
        Returns:
            Dict with mode-specific analysis results
            
        Acceptance Criteria:
            - US-2: All modes supported
            - SC-004: Distinguishable results
        """
        # Get market data if not provided
        if not market_data:
            market_data = search(idea, sources=["wb", "ozon", "yandex"])
        
        # Get handler for mode
        handler = self.mode_handlers.get(mode, self._handle_default_mode)
        
        # Perform mode-specific analysis
        return await handler(idea, market_data)
    
    async def _handle_default_mode(self, idea: str, market_data: dict) -> Dict:
        """Default ОЦЕНКА mode - balanced analysis"""
        return await self._generate_balanced_analysis(idea, market_data)
    
    async def _handle_business_plan_mode(self, idea: str, market_data: dict) -> Dict:
        """БИЗНЕС-ПЛАН mode - investor-focused analysis"""
        return await self._generate_investor_analysis(idea, market_data)
    
    # ... other mode handlers
```

### Mode-Specific Analysis Implementations

#### 1. ОЦЕНКА Mode (Default)

```python
async def _generate_balanced_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate balanced analysis for ОЦЕНКА mode
    
    Acceptance Criteria:
        - US-1: 7-section report structure
        - SC-004: Balanced, comprehensive analysis
    """
    # Create LLM prompt for balanced analysis
    prompt = f"""
    Проанализируйте следующую бизнес-идею сбалансированно:
    
    Идея: {idea}
    
    Рыночные данные:
    {self._format_market_data(market_data)}
    
    Структура ответа (7 секций):
    1. КАРТОЧКА ИДЕИ: Problem, Solution, Target Audience, Market Size, Competitors, Monetization, Risks
    2. ПОЧЕМУ СЕЙЧАС: Timing factors, Policy/regulatory changes, Consumer behavior trends
    3. РЫНОЧНЫЙ РАЗРЫВ: What's missing in market, Why existing solutions fail, Your unique angle
    4. НЕДОСТАЮЩИЕ ДАННЫЕ: 10 critical questions for founder to validate
    5. ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ: Demand validation, Competitor signals, Price analysis
    6. ПЛАН ДЕЙСТВИЙ: 30-day week-by-week action breakdown
    7. ПЛАН РЕАЛИЗАЦИИ: 3-12 month roadmap with key stages
    
    Требования:
    - Ответ на русском языке
    - Используйте конкретные цифры из рыночных данных
    - Включите цитаты в формате [URL, DD.MM.YYYY HH:MM, "описание"]
    - Максимум 3 предложения на абзац
    - Используйте эмодзи для структуры
    """
    
    # Get LLM analysis
    llm_response = await self.llm.generate_analysis(idea, "ОЦЕНКА", {"market_data": market_data})
    
    # Parse and structure response
    return self._parse_llm_response(llm_response, idea, market_data)
```

#### 2. БИЗНЕС-ПЛАН Mode

```python
async def _generate_investor_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate investor-focused analysis for БИЗНЕС-ПЛАН mode
    
    Acceptance Criteria:
        - US-2: Investor-focused analysis
        - SC-004: Distinguishable from other modes
    """
    # Extract financial data from market research
    wb_data = next((s for s in market_data.sources if s.source == "wb"), None)
    ozon_data = next((s for s in market_data.sources if s.source == "ozon"), None)
    
    financial_context = ""
    if wb_data and wb_data.price_range:
        financial_context += f"WB price range: {wb_data.price_range}\n"
    if ozon_data and ozon_data.price_range:
        financial_context += f"Ozon price range: {ozon_data.price_range}\n"
    
    # Create investor-focused prompt
    prompt = f"""
    Вы - финансовый эксперт, анализирующий бизнес-идею для инвесторов:
    
    Идея: {idea}
    
    Финансовый контекст:
    {financial_context}
    
    Сфокусируйтесь на:
    1. Финансовых показателях и ROI
    2. Рыночном потенциале и размере
    3. Конкурентных преимуществах
    4. Рисках и митигации
    5. Требуемых инвестициях и сроках окупаемости
    
    Используйте структуру 7 секций, но уделите особое внимание:
    - КАРТОЧКА ИДЕИ: Финансовая модель, прогноз доходов
    - ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ: Рыночный спрос, ценовые бенчмарки
    - ПЛАН РЕАЛИЗАЦИИ: Финансовый roadmap, ключевые метрики
    
    Включите:
    - Прогноз выручки на 12 месяцев
    - Оценку начальных инвестиций
    - Сроки окупаемости
    - Ключевые финансовые риски
    """
    
    llm_response = await self.llm.generate_analysis(idea, "БИЗНЕС-ПЛАН", {
        "market_data": market_data,
        "financial_context": financial_context
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)
```

#### 3. МАРКЕТИНГ Mode

```python
async def _generate_marketing_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate marketing-focused analysis for МАРКЕТИНГ mode
    
    Acceptance Criteria:
        - US-2: Marketing-focused analysis
        - SC-004: Distinguishable from other modes
    """
    # Extract audience and trend data
    yandex_data = next((s for s in market_data.sources if s.source == "yandex"), None)
    
    marketing_context = ""
    if yandex_data and yandex_data.get('trends'):
        trends = yandex_data['trends']
        marketing_context += f"Monthly searches: {trends.get('monthly_searches', 'N/A')}\n"
        marketing_context += f"Trend: {trends.get('trend', 'N/A')}\n"
        marketing_context += f"CPC: {trends.get('cpc', 'N/A')}\n"
    
    prompt = f"""
    Вы - маркетинговый стратег, анализирующий бизнес-идею:
    
    Идея: {idea}
    
    Маркетинговый контекст:
    {marketing_context}
    
    Сфокусируйтесь на:
    1. Целевой аудитории (демография, поведение, боли)
    2. Каналах продвижения (маркетплейсы, соцсети, контент)
    3. Уникальном торговом предложении
    4. Конкурентных преимуществах в коммуникации
    5. Маркетинговой стратегии и бюджете
    
    Используйте структуру 7 секций, но уделите особое внимание:
    - КАРТОЧКА ИДЕИ: Целевая аудитория, каналы сбыта
    - ПОЧЕМУ СЕЙЧАС: Потребительские тренды, сезонность
    - РЫНОЧНЫЙ РАЗРЫВ: Пробелы в коммуникации конкурентов
    - ПЛАН ДЕЙСТВИЙ: Маркетинговый план на 30 дней
    
    Включите:
    - Портрет целевой аудитории
    - Рекомендации по каналам продвижения
    - Оценку маркетингового бюджета
    - Контент-стратегию
    """
    
    llm_response = await self.llm.generate_analysis(idea, "МАРКЕТИНГ", {
        "market_data": market_data,
        "marketing_context": marketing_context
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)
```

#### 4. ИСПОЛНЕНИЕ Mode

```python
async def _generate_execution_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate execution-focused analysis for ИСПОЛНЕНИЕ mode
    
    Acceptance Criteria:
        - US-2: Execution-focused analysis
        - SC-004: Distinguishable from other modes
    """
    prompt = f"""
    Вы - опытный проектный менеджер, анализирующий бизнес-идею с точки зрения реализации:
    
    Идея: {idea}
    
    Сфокусируйтесь на:
    1. Пошаговом плане реализации
    2. Необходимых ресурсах (команда, оборудование, партнеры)
    3. Ключевых этапах и вехах
    4. Потенциальных блокерах и решениях
    5. Операционных процессах
    
    Используйте структуру 7 секций, но уделите особое внимание:
    - КАРТОЧКА ИДЕИ: Требуемые ресурсы и компетенции
    - НЕДОСТАЮЩИЕ ДАННЫЕ: Вопросы по операционным деталям
    - ПЛАН ДЕЙСТВИЙ: Детальный план на 30 дней с задачами
    - ПЛАН РЕАЛИЗАЦИИ: Полный roadmap с вехами
    
    Включите:
    - Чеклист запуска проекта
    - Оценку необходимых инвестиций в инфраструктуру
    - Рекомендации по команде и ролям
    - План первых 30 дней с конкретными задачами
    """
    
    llm_response = await self.llm.generate_analysis(idea, "ИСПОЛНЕНИЕ", {
        "market_data": market_data
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)
```

#### 5. САЙТ Mode

```python
async def _generate_website_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate website-focused analysis for САЙТ mode
    
    Acceptance Criteria:
        - US-2: Website-focused analysis
        - SC-004: Distinguishable from other modes
    """
    prompt = f"""
    Вы - веб-стратег и UX-специалист, анализирующий бизнес-идею с точки зрения веб-присутствия:
    
    Идея: {idea}
    
    Сфокусируйтесь на:
    1. Структуре и контенте сайта
    2. Пользовательском опыте и конверсии
    3. Технических требованиях
    4. Интеграции с маркетплейсами
    5. SEO и цифровом маркетинге
    
    Используйте структуру 7 секций, но уделите особое внимание:
    - КАРТОЧКА ИДЕИ: Цели сайта и целевые действия
    - ПОЧЕМУ СЕЙЧАС: Тренды в веб-дизайне для ниши
    - ПЛАН ДЕЙСТВИЙ: План разработки сайта
    - ПЛАН РЕАЛИЗАЦИИ: Roadmap развития веб-присутствия
    
    Включите:
    - Рекомендации по структуре сайта
    - Ключевые страницы и их цели
    - Технический стек и хостинг
    - План контент-маркетинга
    """
    
    llm_response = await self.llm.generate_analysis(idea, "САЙТ", {
        "market_data": market_data
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)
```

#### 6. ОТЧЁТ 1-3 Modes

```python
async def _generate_report_1_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate deep data analysis for ОТЧЁТ 1 mode
    
    Acceptance Criteria:
        - US-2: Deep WB/Ozon data analysis
        - SC-004: Distinguishable from other modes
    """
    # Extract detailed market data
    wb_products = []
    ozon_products = []
    
    for source in market_data.sources:
        if source.source == "wb" and source.products:
            wb_products = source.products[:10]
        elif source.source == "ozon" and source.products:
            ozon_products = source.products[:10]
    
    detailed_data = ""
    if wb_products:
        detailed_data += "Wildberries Top Products:\n"
        for i, product in enumerate(wb_products[:5], 1):
            detailed_data += f"{i}. {product['title']} - {product['price']}\n"
    
    if ozon_products:
        detailed_data += "\nOzon Top Products:\n"
        for i, product in enumerate(ozon_products[:5], 1):
            detailed_data += f"{i}. {product['title']} - {product['price']}\n"
    
    prompt = f"""
    Вы - аналитик данных, специализирующийся на российских маркетплейсах.
    Проведите глубокий анализ данных для следующей идеи:
    
    Идея: {idea}
    
    Детальные рыночные данные:
    {detailed_data}
    
    Сфокусируйтесь на Section 5 (ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ):
    1. Глубокий анализ цен и позиционирования
    2. Конкурентный анализ топ-продуктов
    3. Рыночные тренды и паттерны
    4. Статистический анализ данных
    5. Рекомендации по ценообразованию
    
    Включите:
    - Сравнительные таблицы конкурентов
    - Анализ ценовых диапазонов
    - Выявление рыночных ниш
    - Рекомендации по ассортименту
    - Цитаты и ссылки на источники данных
    """
    
    llm_response = await self.llm.generate_analysis(idea, "ОТЧЁТ 1", {
        "market_data": market_data,
        "detailed_data": detailed_data
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)

async def _generate_report_2_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate detailed action plan for ОТЧЁТ 2 mode
    
    Acceptance Criteria:
        - US-2: Detailed 30-day action breakdown
        - SC-004: Distinguishable from other modes
    """
    prompt = f"""
    Вы - эксперт по операционному планированию.
    Создайте детальный 30-дневный план действий для следующей идеи:
    
    Идея: {idea}
    
    Сфокусируйтесь на Section 6 (ПЛАН ДЕЙСТВИЙ):
    1. Понедельный план на 30 дней
    2. Конкретные задачи с дедлайнами
    3. Необходимые ресурсы для каждой задачи
    4. Ключевые метрики успеха
    5. Потенциальные риски и решения
    
    Формат:
    Неделя 1: [Цели недели]
    - День 1: [Задача 1] (Ресурсы: [ресурсы], Метрика: [метрика])
    - День 2: [Задача 2] (Ресурсы: [ресурсы], Метрика: [метрика])
    - ...
    
    Включите:
    - Конкретные измеримые задачи
    - Реалистичные временные оценки
    - Приоритизацию задач
    - Рекомендации по инструментам
    """
    
    llm_response = await self.llm.generate_analysis(idea, "ОТЧЁТ 2", {
        "market_data": market_data
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)

async def _generate_report_3_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate extended roadmap for ОТЧЁТ 3 mode
    
    Acceptance Criteria:
        - US-2: Extended 3-12 month roadmap
        - SC-004: Distinguishable from other modes
    """
    prompt = f"""
    Вы - стратегический планировщик.
    Создайте расширенный roadmap на 3-12 месяцев для следующей идеи:
    
    Идея: {idea}
    
    Сфокусируйтесь на Section 7 (ПЛАН РЕАЛИЗАЦИИ):
    1. Квартальный roadmap на 12 месяцев
    2. Ключевые этапы и вехи
    3. Ресурсное планирование
    4. Финансовые прогнозы
    5. Метрики успеха и KPI
    
    Формат:
    Месяц 1-3: [Цели квартала]
    - Веха 1: [Описание] (Срок: [дата], Бюджет: [сумма], Ответственный: [роль])
    - Веха 2: [Описание] (Срок: [дата], Бюджет: [сумма], Ответственный: [роль])
    - ...
    
    Включите:
    - Ключевые бизнес-метрики
    - План масштабирования
    - Стратегию выхода на новые рынки
    - План привлечения инвестиций (если нужно)
    """
    
    llm_response = await self.llm.generate_analysis(idea, "ОТЧЁТ 3", {
        "market_data": market_data
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)
```

#### 7. Section-Specific Modes

```python
async def _generate_timing_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate timing-focused analysis for ПОЧЕМУ_СЕЙЧАС mode
    
    Acceptance Criteria:
        - US-2: Timing and opportunity analysis
        - SC-004: Distinguishable from other modes
    """
    # Extract trend data
    yandex_data = next((s for s in market_data.sources if s.source == "yandex"), None)
    trend_info = ""
    
    if yandex_data and yandex_data.get('trends'):
        trends = yandex_data['trends']
        trend_info = f"""
        Текущие тренды:
        - Ежемесячные поиски: {trends.get('monthly_searches', 'N/A')}
        - Динамика: {trends.get('trend', 'N/A')}
        - Конкуренция: {trends.get('competition', 'N/A')}
        """
    
    prompt = f"""
    Вы - аналитик рыночного timing.
    Проанализируйте, почему сейчас хорошее время для следующей идеи:
    
    Идея: {idea}
    
    Рыночные тренды:
    {trend_info}
    
    Сфокусируйтесь на Section 2 (ПОЧЕМУ СЕЙЧАС):
    1. Текущие рыночные условия
    2. Политические/регуляторные изменения
    3. Потребительские тренды
    4. Окно возможностей
    5. Риски задержки
    
    Включите:
    - Анализ макроэкономических факторов
    - Оценку рыночного цикла
    - Прогноз развития ниши
    - Рекомендации по timing запуска
    """
    
    llm_response = await self.llm.generate_analysis(idea, "ПОЧЕМУ_СЕЙЧАС", {
        "market_data": market_data,
        "trend_info": trend_info
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)

async def _generate_gap_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate gap-focused analysis for РЫНОЧНЫЙ_РАЗРЫВ mode
    
    Acceptance Criteria:
        - US-2: Competitive gap analysis
        - SC-004: Distinguishable from other modes
    """
    # Extract competitor data
    competitors = []
    for source in market_data.sources:
        if source.products:
            competitors.extend([
                {
                    'name': p['title'],
                    'price': p['price'],
                    'source': source.source,
                    'rating': p.get('rating')
                }
                for p in source.products[:5]
            ])
    
    competitor_info = "Конкуренты:\n"
    for i, comp in enumerate(competitors[:10], 1):
        competitor_info += f"{i}. {comp['name']} ({comp['source']}) - {comp['price']}\n"
    
    prompt = f"""
    Вы - эксперт по конкурентному анализу.
    Найдите рыночные разрывы для следующей идеи:
    
    Идея: {idea}
    
    Конкурентная информация:
    {competitor_info}
    
    Сфокусируйтесь на Section 3 (РЫНОЧНЫЙ РАЗРЫВ):
    1. Что отсутствует на рынке
    2. Почему существующие решения не работают
    3. Уникальный угол предложения
    4. Конкурентные преимущества
    5. Барьеры для конкурентов
    
    Включите:
    - SWOT-анализ конкурентов
    - Анализ слабых мест конкурентов
    - Возможности для дифференциации
    - Стратегии захвата рыночной доли
    """
    
    llm_response = await self.llm.generate_analysis(idea, "РЫНОЧНЫЙ_РАЗРЫВ", {
        "market_data": market_data,
        "competitor_info": competitor_info
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)

async def _generate_evidence_analysis(self, idea: str, market_data: dict) -> Dict:
    """
    Generate evidence-focused analysis for ДОКАЗАТЕЛЬСТВА mode
    
    Acceptance Criteria:
        - US-2: Evidence-focused validation
        - SC-004: Distinguishable from other modes
    """
    # Extract all evidence data
    evidence_data = "Доказательства и сигналы:\n\n"
    
    for source in market_data.sources:
        if source.source == "wb":
            evidence_data += f"Wildberries: {source.price_range or 'Нет данных'}\n"
        elif source.source == "ozon":
            evidence_data += f"Ozon: {source.price_range or 'Нет данных'}\n"
        elif source.source == "yandex":
            trends = source.get('trends', {})
            evidence_data += f"Yandex: {trends.get('monthly_searches', 'N/A')} поисков/месяц\n"
    
    prompt = f"""
    Вы - исследователь данных, специализирующийся на валидации бизнес-идей.
    Соберите и проанализируйте доказательства для следующей идеи:
    
    Идея: {idea}
    
    Доказательства:
    {evidence_data}
    
    Сфокусируйтесь на Section 5 (ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ):
    1. Валидация спроса (данные WB/Ozon/Yandex)
    2. Сигналы от конкурентов
    3. Анализ цен и позиционирования
    4. Потребительские отзывы и рейтинги
    5. Рыночные тренды и прогнозы
    
    Включите:
    - Конкретные цифры и статистику
    - Сравнительный анализ с конкурентами
    - Оценку рыночного потенциала
    - Цитаты и ссылки на все источники
    - Рекомендации по дальнейшей валидации
    """
    
    llm_response = await self.llm.generate_analysis(idea, "ДОКАЗАТЕЛЬСТВА", {
        "market_data": market_data,
        "evidence_data": evidence_data
    })
    
    return self._parse_llm_response(llm_response, idea, market_data)
```

### Response Parsing and Structuring

```python
def _parse_llm_response(self, llm_response: str, idea: str, market_data: dict) -> Dict:
    """
    Parse LLM response into structured 7-section format
    
    Acceptance Criteria:
        - US-1: 7-section report structure maintained
        - SC-004: Mode-specific focus preserved
    """
    # Parse LLM response into sections
    # This would use more sophisticated parsing in production
    
    sections = {
        'section_1': self._extract_section(llm_response, 1),
        'section_2': self._extract_section(llm_response, 2),
        'section_3': self._extract_section(llm_response, 3),
        'section_4': self._extract_section(llm_response, 4),
        'section_5': self._extract_section(llm_response, 5),
        'section_6': self._extract_section(llm_response, 6),
        'section_7': self._extract_section(llm_response, 7),
    }
    
    # Add citations from market data
    for section_key in sections:
        sections[section_key] = self._add_citations(sections[section_key], market_data)
    
    return sections

def _extract_section(self, text: str, section_num: int) -> str:
    """Extract section from LLM response"""
    # Simple extraction - would be more sophisticated in production
    section_markers = {
        1: "КАРТОЧКА ИДЕИ",
        2: "ПОЧЕМУ СЕЙЧАС",
        3: "РЫНОЧНЫЙ РАЗРЫВ",
        4: "НЕДОСТАЮЩИЕ ДАННЫЕ",
        5: "ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ",
        6: "ПЛАН ДЕЙСТВИЙ",
        7: "ПЛАН РЕАЛИЗАЦИИ"
    }
    
    marker = section_markers[section_num]
    
    if marker in text:
        # Find section start
        start = text.find(marker)
        
        # Find next section or end
        next_marker = section_markers.get(section_num + 1, None)
        if next_marker and next_marker in text:
            end = text.find(next_marker)
        else:
            end = len(text)
        
        return text[start:end].strip()
    
    return f"{marker}: [Анализ не доступен]"

def _add_citations(self, section_text: str, market_data: dict) -> str:
    """Add proper citations to section text"""
    # Add citations from market data sources
    citations = []
    
    for source in market_data.sources:
        if source.citation:
            citations.append(source.citation)
    
    if citations:
        section_text += "\n\n📌 Источники:\n" + "\n".join(citations)
    
    return section_text

def _format_market_data(self, market_data: dict) -> str:
    """Format market data for LLM context"""
    formatted = "Рыночные данные:\n\n"
    
    for source in market_data.sources:
        if source.source == "wb":
            formatted += f"Wildberries: {source.price_range or 'Нет данных'}\n"
            if source.products:
                formatted += f"  Топ-продукты: {', '.join([p['title'] for p in source.products[:3]])}\n"
        elif source.source == "ozon":
            formatted += f"Ozon: {source.price_range or 'Нет данных'}\n"
            if source.products:
                formatted += f"  Топ-продукты: {', '.join([p['title'] for p in source.products[:3]])}\n"
        elif source.source == "yandex":
            trends = source.get('trends', {})
            formatted += f"Yandex: {trends.get('monthly_searches', 'N/A')} поисков/месяц, "
            formatted += f"Тренд: {trends.get('trend', 'N/A')}\n"
    
    return formatted
```

### Unit Tests

```python
# tests/test_mode_analysis.py
import pytest
from bot.mode_analysis import ModeAnalyzer
from unittest.mock import AsyncMock

class TestModeAnalysis:
    """Test mode-specific analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_all_modes_supported(self):
        """Test that all 11 modes are supported"""
        analyzer = ModeAnalyzer()
        modes = [
            "ОЦЕНКА", "БИЗНЕС-ПЛАН", "МАРКЕТИНГ", "ИСПОЛНЕНИЕ", "САЙТ",
            "ОТЧЁТ 1", "ОТЧЁТ 2", "ОТЧЁТ 3", "ПОЧЕМУ_СЕЙЧАС", "РЫНОЧНЫЙ_РАЗРЫВ", "ДОКАЗАТЕЛЬСТВА"
        ]
        
        for mode in modes:
            # Mock LLM response
            analyzer.llm.generate_analysis = AsyncMock(return_value="Test analysis")
            
            result = await analyzer.analyze("Test idea", mode)
            assert result is not None
            assert "section_1" in result
    
    @pytest.mark.asyncio
    async def test_mode_structure(self):
        """Test that all modes maintain 7-section structure"""
        analyzer = ModeAnalyzer()
        analyzer.llm.generate_analysis = AsyncMock(return_value="Test analysis")
        
        result = await analyzer.analyze("Test idea", "БИЗНЕС-ПЛАН")
        
        # Check all 7 sections are present
        for i in range(1, 8):
            assert f"section_{i}" in result
    
    @pytest.mark.asyncio
    async def test_mode_focus(self):
        """Test that different modes produce different focus"""
        analyzer = ModeAnalyzer()
        
        # Test that different modes call LLM with different parameters
        analyzer.llm.generate_analysis = AsyncMock()
        
        await analyzer.analyze("Test idea", "БИЗНЕС-ПЛАН")
        call_args = analyzer.llm.generate_analysis.call_args
        assert "БИЗНЕС-ПЛАН" in call_args[0][1]  # Mode should be passed
        
        await analyzer.analyze("Test idea", "МАРКЕТИНГ")
        call_args = analyzer.llm.generate_analysis.call_args
        assert "МАРКЕТИНГ" in call_args[0][1]  # Different mode
    
    def test_citation_formatting(self):
        """Test that citations are properly formatted"""
        analyzer = ModeAnalyzer()
        
        # Test citation formatting method
        section = "Test section"
        market_data = {
            'sources': [
                {'citation': '[https://wb.ru, 14.12.2025 15:30, "test"]'}
            ]
        }
        
        result = analyzer._add_citations(section, market_data)
        assert "📌 Источники:" in result
        assert "https://wb.ru" in result
```

---

## Success Criteria

- [ ] All 11 analysis modes implemented and functional
- [ ] Each mode produces distinct, focused results
- [ ] All modes maintain required 7-section structure
- [ ] Mode-specific prompt engineering working
- [ ] Unit test coverage >80% for all modes
- [ ] Integration with Telegram bot completed
- [ ] Mode analysis ready for production use

---

## Next Tasks

This completes the core analysis engine. Next steps:
- [ ] Task 009: Testing (comprehensive testing of all modes)
- [ ] Task 010: Deployment (prepare for production)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1 (Russia-First V, Reality-First III)
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (US-2, SC-004)
- **Plan**: `plan.md` Phase 3.2
- **Architecture**: `architecture-decisions.md` Analysis Engine section