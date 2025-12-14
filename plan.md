# Idea-Planner-Agent MVP — Technical Plan

**Version**: 1.0 | **Date**: 14.12.2025 | **Status**: Approved
**Total Estimated Hours**: 65 hours
**Target Completion**: 2025-12-31

---

## 1. Overview

This plan outlines the Spec-Driven Development approach for building the idea-planner-agent MVP, a Telegram bot that validates business ideas for the Russian market using real data from Wildberries, Ozon, and Yandex.

**Key Principles**:
- Constitution > Spec > Plan > Tasks > Code
- Traceability from code to constitution
- Russia-first assumptions (₽, DD.MM.YYYY, Russian language)
- Reality-first data validation
- Graceful degradation over hallucination

---

## 2. Task Breakdown (Spec-Driven Development)

### Phase 1: Foundation (12 hours)

#### 1.1 Project Structure Setup (2 hours)
- [ ] Initialize Git repository with proper .gitignore
- [ ] Create directory structure: `src/`, `tests/`, `ru_search/`, `config/`
- [ ] Set up Python virtual environment
- [ ] Install core dependencies: `python-telegram-bot`, `cachetools`, `SQLAlchemy`

#### 1.2 Database Implementation (3 hours)
- [ ] Design SQLite schema for `bot.db`
- [ ] Implement SQLAlchemy ORM models:
  - `TelegramUser` (user_id, language, last_interaction)
  - `ChatContext` (chat_id, current_mode, last_idea)
  - `AnalysisJob` (job_id, status, created_at, updated_at)
  - `DataSnapshot` (snapshot_id, query, source, data, timestamp, freshness)
  - `Citation` (citation_id, url, timestamp_msk, note)
- [ ] Create database migration script

#### 1.3 Configuration System (2 hours)
- [ ] Create `.env` template with required variables:
  - `TELEGRAM_TOKEN`
  - `LLM_API_KEY`
  - `LLM_PROVIDER=groq`
  - `CACHE_TTL=21600`
- [ ] Implement `config.py` with environment variable loading
- [ ] Set up Railway.app environment variables template

#### 1.4 Basic Telegram Bot Skeleton (5 hours)
- [ ] Implement webhook-based bot using `python-telegram-bot`
- [ ] Create command handlers: `/start`, `/help`
- [ ] Implement message handler for idea analysis
- [ ] Set up basic error handling and logging
- [ ] Create progress indicator system (`⏳ Анализирую...`)

### Phase 2: Core Features (25 hours)

#### 2.1 ru_search Module (10 hours)
- [ ] Design clean API: `search(query, sources=["wb", "ozon", "yandex"])`
- [ ] Implement Wildberries scraper with rate limiting
- [ ] Implement Ozon scraper with error handling
- [ ] Implement Yandex Wordstat/Market integration
- [ ] Add caching layer using `cachetools.TTLCache`
- [ ] Implement data validation and normalization
- [ ] Create unit tests for search functionality (>80% coverage)

#### 2.2 Telegram Bot Core Logic (15 hours)
- [ ] Implement mode detection regex: `РЕЖИМ: {mode}`
- [ ] Create mode handler for 9 core modes (11 including submodes):
  - ОЦЕНКА (default)
  - БИЗНЕС-ПЛАН
  - МАРКЕТИНГ
  - ИСПОЛНЕНИЕ
  - САЙТ
  - ОТЧЁТ (with 3 submodes: ОТЧЁТ 1, 2, 3)
  - ПОЧЕМУ_СЕЙЧАС
  - РЫНОЧНЫЙ_РАЗРЫВ
  - ДОКАЗАТЕЛЬСТВА
- [ ] Implement 7-section report generation:
  1. КАРТОЧКА ИДЕИ
  2. ПОЧЕМУ СЕЙЧАС
  3. РЫНОЧНЫЙ РАЗРЫВ
  4. НЕДОСТАЮЩИЕ ДАННЫЕ
  5. ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ
  6. ПЛАН ДЕЙСТВИЙ
  7. ПЛАН РЕАЛИЗАЦИИ
- [ ] Implement citation formatting according to constitution
- [ ] Add data freshness indicators (⚠️, 🔴)
- [ ] Implement message splitting for Telegram 4096 char limit

### Phase 3: Analysis Engine (20 hours)

#### 3.1 LLM Integration (5 hours)
- [ ] Implement abstract `LLMProvider` interface
- [ ] Create `GroqProvider` implementation
- [ ] Add provider configuration system
- [ ] Implement fallback mechanism for LLM failures
- [ ] Add LLM response validation layer

#### 3.2 Mode-Specific Analysis (15 hours)
- [ ] Implement mode-specific analysis logic:
  - **ОЦЕНКА**: Balanced 7-section analysis
  - **БИЗНЕС-ПЛАН**: Investor-focused with financial projections
  - **МАРКЕТИНГ**: Customer acquisition and branding focus
  - **ИСПОЛНЕНИЕ**: Operational implementation details
  - **САЙТ**: Website structure and content recommendations
  - **ОТЧЁТ 1**: Deep WB/Ozon data analysis
  - **ОТЧЁТ 2**: Detailed 30-day action plan
  - **ОТЧЁТ 3**: Extended 3-12 month roadmap
  - **ПОЧЕМУ_СЕЙЧАС**: Timing and opportunity analysis
  - **РЫНОЧНЫЙ_РАЗРЫВ**: Competitive gap analysis
  - **ДОКАЗАТЕЛЬСТВА**: Evidence-focused validation
- [ ] Implement mode-specific prompt engineering
- [ ] Add unit tests for each mode (>80% coverage)

### Phase 4: Testing & Deployment (8 hours)

#### 4.1 Testing (5 hours)
- [ ] Write unit tests for all core modules (>80% coverage)
- [ ] Create integration tests for Telegram bot flow
- [ ] Implement mock testing for external APIs
- [ ] Set up test coverage reporting
- [ ] Create test data for all modes

#### 4.2 Deployment (3 hours)
- [ ] Set up Railway.app project
- [ ] Configure webhook URL: `https://{app_name}.railway.app/telegram/webhook`
- [ ] Implement SSL certificate (Let's Encrypt)
- [ ] Set up production environment variables
- [ ] Deploy and test webhook functionality
- [ ] Create deployment documentation

---

## 3. Dependency Graph

graph TD
A[Project Structure] --> B[Database]
A --> C[Configuration]
A --> D[Telegram Bot Skeleton]
B --> E[ru_search Module]
C --> E
D --> E
E --> F[LLM Integration]
E --> G[Mode Analysis]
F --> H[Testing]
G --> H
H --> I[Deployment]

text

**Key Dependencies**:
- ru_search module depends on database and configuration
- Telegram bot depends on ru_search module
- Mode analysis depends on LLM integration
- Testing depends on all core features
- Deployment depends on successful testing

---

## 4. Implementation Timeline

| Phase | Task Group | Hours | Start Date | End Date |
|-------|------------|-------|------------|----------|
| 1 | Foundation | 12 | 16.12.2025 | 17.12.2025 |
| 1.1 | Project Structure | 2 | 16.12.2025 10:00 | 16.12.2025 12:00 |
| 1.2 | Database | 3 | 16.12.2025 13:00 | 16.12.2025 16:00 |
| 1.3 | Configuration | 2 | 16.12.2025 16:30 | 16.12.2025 18:30 |
| 1.4 | Telegram Skeleton | 5 | 17.12.2025 10:00 | 17.12.2025 15:00 |
| 2 | Core Features | 25 | 18.12.2025 | 22.12.2025 |
| 2.1 | ru_search Module | 10 | 18.12.2025 10:00 | 19.12.2025 12:00 |
| 2.2 | Telegram Logic | 15 | 19.12.2025 13:00 | 22.12.2025 18:00 |
| 3 | Analysis Engine | 20 | 23.12.2025 | 26.12.2025 |
| 3.1 | LLM Integration | 5 | 23.12.2025 10:00 | 23.12.2025 15:00 |
| 3.2 | Mode Analysis | 15 | 24.12.2025 10:00 | 26.12.2025 18:00 |
| 4 | Testing & Deployment | 8 | 27.12.2025 | 28.12.2025 |
| 4.1 | Testing | 5 | 27.12.2025 10:00 | 27.12.2025 15:00 |
| 4.2 | Deployment | 3 | 28.12.2025 10:00 | 28.12.2025 13:00 |

**Total**: 65 hours (within 40-80 hour MVP estimate)
**Buffer**: 3 days (29-31.12.2025) for fixes and polish

---

## 5. Traceability Matrix

### Tasks → Spec Requirements → Constitution

| Task | Spec Requirement | Constitution Principle |
|------|------------------|-----------------------|
| Telegram bot interface | FR-001, FR-002 | Russia-First (V) |
| Mode detection | FR-006, US-2 | Reality-First (III) |
| 7-section reports | FR-004, AC-1..AC-4 | Citations (IV) |
| Data citations | FR-005, AC-1..AC-4 | Traceability (II) |
| Error handling | FR-007, US-4 | Resilience (VII) |
| ru_search module | FR-010..FR-013 | Reality-First (III) |
| Caching strategy | FR-010..FR-013 | Engineering Quality (VI) |
| LLM integration | FR-008 | Ethics (VIII) |
| Testing >80% | NFR-003 | Engineering Quality (VI) |
| Deployment | Technical Notes | SDD (I) |

---

## 6. Russian Market Focus

### 6.1 Wildberries/Ozon/Yandex Integration
- **Wildberries Integration** (5 hours):
  - Implement WB API scraper with product search
  - Extract prices, ratings, and product counts
  - Handle WB-specific rate limiting
  - Cache WB data for 6 hours

- **Ozon Integration** (3 hours):
  - Implement Ozon API scraper
  - Extract product data and market trends
  - Handle Ozon authentication requirements
  - Cache Ozon data with proper TTL

- **Yandex Integration** (2 hours):
  - Implement Yandex Wordstat API
  - Extract search trends and CPC data
  - Handle Yandex XML format
  - Cache Yandex data separately

### 6.2 ru_search Module API
Clean API design for ru_search module
from ru_search import search

Example usage
results = search(
query="деревянная посуда",
sources=["wb", "ozon", "yandex"],
max_results=20,
cache_ttl=21600 # 6 hours in seconds
)

Returns structured data with citations
{
"wb": {
"products": [...],
"price_range": "800–1200 ₽",
"citation": "[https://wb.ru/..., 14.12.2025 15:30, 'WB search results']"
},
"ozon": {...},
"yandex": {...}
}

text

### 6.3 Telegram Bot for Russian Users
- **Language**: All responses in Russian
- **Currency**: ₽ format throughout
- **Dates**: DD.MM.YYYY format
- **Mobile Optimization**: Short paragraphs, emoji structure
- **Error Messages**: Russian error handling with retry options
- **Shareability**: Telegram-native sharing buttons

---

## 7. Architecture Decisions Integration

### 7.1 SQLite Database Setup
- **Implementation**: `bot.db` with SQLAlchemy ORM
- **Tables**: TelegramUser, ChatContext, AnalysisJob, DataSnapshot, Citation
- **Migration**: Simple SQLite migration script
- **Future**: PostgreSQL migration path documented

### 7.2 In-Memory Caching (cachetools)
- **Implementation**: `cachetools.TTLCache(maxsize=1000, ttl=21600)`
- **Cache Keys**: Query-based (per-idea basis)
- **Freshness**: 6-hour TTL with fallback indicators
- **Future**: Redis migration documented for v1.1

### 7.3 Configurable LLM Provider
- **Interface**: Abstract `LLMProvider` class
- **Default**: GroqProvider with Llama-3.3-70b
- **Configuration**: `.env` variable `LLM_PROVIDER=groq`
- **Fallback**: Graceful degradation on LLM failures

### 7.4 Railway.app Deployment
- **Webhook**: `https://{app_name}.railway.app/telegram/webhook`
- **SSL**: Automatic Let's Encrypt certificate
- **Environment**: Railway environment variables
- **Monitoring**: Basic logging and metrics

### 7.5 Testing Strategy
- **Unit Tests**: pytest with >80% coverage
- **Integration Tests**: Mock Telegram API
- **Coverage**: pytest-cov reporting
- **E2E**: Deferred to v1.1

---

## 8. Risk Assessment

### High Risks
- **WB/Ozon API changes**: Mitigate with robust error handling and fallback to cached data
- **Telegram API rate limits**: Implement proper rate limiting and retry logic
- **LLM reliability**: Implement fallback mechanisms and graceful degradation

### Medium Risks
- **Data freshness**: Implement clear freshness indicators and cache invalidation
- **Mobile formatting**: Test extensively on Telegram mobile clients
- **Performance**: Monitor p90 latency and optimize as needed

### Low Risks
- **Database migration**: SQLite to PostgreSQL path is straightforward
- **Deployment**: Railway.app provides simple webhook setup
- **Testing**: Unit and integration tests provide good coverage

---

## 9. Success Metrics

### Technical Success Criteria
- **SC-001**: p90 response time < 2 minutes
- **SC-002**: 100% citation coverage for all facts/numbers
- **SC-003**: Graceful degradation on all source failures
- **SC-004**: All 9 modes (11 with submodes) functional and distinguishable
- **SC-005**: Telegram sharing functionality working

### Quality Gates
- **Test Coverage**: >80% unit + integration test coverage
- **Performance**: All operations complete within SLA
- **Documentation**: Complete traceability from code to constitution
- **Error Handling**: No unhandled exceptions in production

---

## 10. Next Steps

1. **Review and Approval**: Team review of this plan.md ✅
2. **Task Creation**: Break down into detailed tasks.md
3. **Implementation**: Begin Phase 1 - Foundation (16.12.2025)
4. **Iterative Development**: Follow Spec-Driven Development process
5. **Continuous Testing**: Maintain >80% test coverage

**Approvers**:
- [x] Constitution compliance check
- [x] Spec requirements coverage
- [x] Architecture decisions alignment
- [x] Timeline feasibility review

---

## Appendix: Key References

- **Constitution**: `.specify/constitution.md` v0.1.1
- **Spec**: `.specify/specs/001-core/spec.md` v2.0
- **Architecture**: `architecture-decisions.md` v1.0
- **Template**: `.specify/templates/plan-template.md`

**Last Updated**: 14.12.2025 18:08 MSK
