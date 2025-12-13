# idea_planner_agent — Complete Project Context

**Version:** 1.0  
**Date:** 2025-12-13  
**Status:** Phase 1 — Requirements (Constitution)

---

## 📑 TABLE OF CONTENTS

1. [Quick Start](#-quick-start-for-ai-assistants)
2. [Project Mission](#-project-mission)
3. [Methodology: Spec-Driven Development](#-methodology-spec-driven-development)
4. [Tech Stack](#️-tech-stack)
5. [Agent Capabilities](#-agent-capabilities)
6. [Russian Market Focus](#-russian-market-focus)
7. [Learning Principles](#-learning-principles)
8. [Kilo Code Integration](#-kilo-code-integration)
9. [Key References](#-key-references)
10. [Communication Guidelines](#-communication-guidelines)
11. [Constraints](#-constraints)
12. [Session Workflow](#-session-workflow)
13. [Success Criteria](#-success-criteria)
14. [Current Status](#-current-status)
15. [Estimated Timeline](#-estimated-timeline)
16. [Document Maintenance](#-document-maintenance)
17. [Glossary](#-glossary)
18. [Contact & Resources](#-contact--resources)

---

## 🚀 QUICK START (For AI Assistants)

**Context:** This is a **Spec-Driven Development** project for an AI agent that validates business ideas for the Russian market.

**Current Phase:** Phase 1 — Requirements (Constitution)

**Your Role:** Help with planning, architecture, review, debugging, and learning support.

**Key Constraints:**
- ❌ No code without plan
- ❌ No plan without spec
- ❌ No spec without constitution

**Workflow:** Constitution → Spec → Plan → Tasks → Code

**Next Milestone:** Constitution approval → move to Specification

---

## 🎯 PROJECT MISSION

Разработка **idea_planner_agent** — AI-агента для соло-основателей в России, который помогает валидировать и прорабатывать бизнес-идеи с использованием реальных данных российского рынка.

### Vision

**Inspiration:** [IdeaBrowser.com](https://ideabrowser.com) ($499/год) — мы создаём российскую версию, но:

- ✅ Бесплатно / Freemium модель
- ✅ Open-source
- ✅ Фокус на российский рынок (Wildberries, Ozon, санкции)
- ✅ AI-агент с живыми данными (не статичная база идей)

### Target Users

- Соло-основатели в России
- Малый бизнес / ИП
- Корпоративные интрапренёры
- Студенты предпринимательских программ

### Value Proposition

**Для пользователя:**
- Получает структурированный анализ идеи за 2 минуты
- Видит реальные данные с WB/Ozon (цены, конкуренты, спрос)
- Понимает, что делать дальше (30-day action plan)
- Бесплатно (базовая версия)

**Для меня (как разработчика):**
- Учусь Spec-Driven Development
- Строю production-ready AI agent
- Open-source портфолио
- Потенциальная монетизация (B2B SaaS)

---

## 📐 METHODOLOGY: SPEC-DRIVEN DEVELOPMENT

### Why SDD?

**Проблема традиционного подхода (vibe coding):**
- ❌ Начинаешь писать код без чёткого понимания требований
- ❌ "Попробую так, не работает, попробую иначе"
- ❌ Результат: spaghetti code, технический долг, не понятно зачем что нужно

**Решение SDD:**
- ✅ Requirements First — сначала ЧТО, потом КАК
- ✅ Traceability — каждая строка кода имеет обоснование
- ✅ AI-friendly — LLM лучше следует spec, чем промптам
- ✅ Learning — учишься архитектуре, а не "фиксить баги"

### Workflow (строгая последовательность)

Constitution (Устав)
→ Фундаментальные принципы проекта
→ Как принимаем решения
→ Output: .specify/constitution.md

Specification (Спецификация)
→ ЧТО должен делать агент
→ User Stories, acceptance criteria
→ Output: .specify/specs/001-core/spec.md
→ пользовательские истории, критерии принятия

Clarification (Уточнение)
→ AI задаёт вопросы о неясных моментах
→ Уточняем требования
→ Output: Updated spec.md

Plan (Технический план)
→ КАК реализовать технически
→ Architecture, tech stack, data model
→ Output: .specify/specs/001-core/plan.md
→ Архитектура, технологический стек, модель данных

Tasks (Задачи)
→ Разбивка на атомарные задачи
→ Implementation checklist
→ Output: .specify/specs/001-core/tasks.md
→ Чек-лист реализации

Implementation (Реализация)
→ Кодинг с AI (Kilo Code)
→ Следуем tasks.md
→ Output: src/, tests/, docs/
→ Output: src/, tests/, docs/

Validation (Валидация)
→ Tests, review, documentation
→ Соответствует ли spec?
→ Output: Working agent ✅
→ Тесты, обзор, документация

text

**Каждый этап завершается перед следующим!**

### Key Principles

1. **Requirements First** — никогда не пиши код без spec
2. **Traceability** — код → task → plan → spec → constitution
3. **Living Documentation** — spec обновляется вместе с кодом
4. **AI as Partner** — используй AI для генерации spec/plan/code
5. **Test-Driven** — тесты с первого дня

### Sources

- [Martinelli: Spec-Driven Development with AI](https://martinelli.ch/spec-driven-development-with-ai-a-new-approach-and-a-journey-into-the-past/)
- [GitHub Spec Kit](https://github.com/github/spec-kit)
- [LinkedIn Learning: Spec Kit Course](https://github.com/LinkedInLearning/spec-driven-development-with-github-spec-kit-4641001)

---

## 🛠️ TECH STACK

### Agent Framework

**Google ADK (genai-sdk)**

**Why:**
- ✅ Official Google agent framework
- ✅ Best integration with Gemini
- ✅ Built-in tool calling, memory, context management
- ✅ Python-native

**Alternatives considered:**
- LangChain (too complex, много boilerplate)
- AutoGPT (опенсорс, но abandoned)
- CrewAI (интересен для multi-agent, но оверкилл для MVP)

### LLM

**Groq API / Llama-3.3-70b-versatile**

**Why:**
- ✅ Fast inference (100-300 tokens/sec)
- ✅ Good at coding tasks
- ✅ Affordable ($0.59 / 1M input tokens)
- ✅ Function calling support

**Alternatives:**
- OpenAI GPT-4 (дороже, санкции)
- Anthropic Claude (дороже, но лучше reasoning)
- Gemini (рассмотрим для production)

**Note:** Groq/Llama-3.3 **НЕ поддерживает** forced function calling → нужен wrapper!

### SDD Tool

**GitHub Spec Kit**

**Why:**
- ✅ CLI для SDD workflow
- ✅ Шаблоны для constitution/spec/plan/tasks
- ✅ Интеграция с VS Code / Kilo Code
- ✅ Open-source, maintained by GitHub

**Usage:**
specify init --here --ai kilocode
specify constitution
specify spec
specify plan
specify tasks
Укажите init --здесь --AI Kilocode.

text

### AI Coding Assistant

**Kilo Code (VS Code extension)**

**Why:**
- ✅ Multiple modes (Architect, Code, Debug, Ask, Orchestrator)
- ✅ MCP support (custom tools)
- ✅ Context mentions (@file)
- ✅ Spec Kit integration

**Modes mapping:**
- Constitution/Spec: **Architect Mode** (only .md edits)
- Plan: **Architect Mode**
- Tasks: **Code Mode**
- Implementation: **Orchestrator Mode** (delegates subtasks)
- Debugging: **Debug Mode**
- Learning: **Ask Mode** (no code changes)

**Docs:** [kilo.ai/docs](https://kilo.ai/docs)

### Language & Testing

**Python 3.11+**

**Why:**
- ✅ Rich AI/ML ecosystem
- ✅ Type hints (better AI code generation)
- ✅ Async support (для API calls)

**Testing: pytest**
- Unit tests (functions, tools)
- Integration tests (agent + tools)
- E2E tests (full user scenarios)

**Target coverage:** >80%

### Data Sources

**Russian Market APIs:**

1. **Wildberries API** (unofficial)
   - Product search, prices, ratings, reviews
   - Seller data, sales estimates

2. **Yandex Search API** / Yandex.XML
   - Keyword search
   - News search (для trends)

3. **Yandex.Wordstat** (unofficial scraping)
   - Search volume by keyword
   - Regional breakdown
   - Seasonal trends

4. **VK API** (optional)
   - Community search
   - Posts analysis (sentiment)

5. **Telegram Bot API** (optional)
   - Channel search
   - Subscriber counts

---

## 🎯 AGENT CAPABILITIES

### Output Structure (7 Sections)

**User prompt example:**
Оцени идею: производство и продажа деревянной посуды

text

**Agent output:**

#### 1. IDEA CARD (КАРТОЧКА ИДЕИ)

**Problem (Проблема):**
Пластиковая посуда вредна, металлическая холодная, стеклянная хрупкая. Экологичная альтернатива в дефиците.

**Solution (Решение):**
Деревянная посуда (тарелки, миски, ложки, разделочные доски) из российского дерева (берёза, дуб).

**Target Audience (ЦА):**
- Эко-сознательные покупатели 25-45 лет
- Городские жители с доходом 60K+/мес
- Родители маленьких детей (безопасность)
- Кафе/рестораны с эко-позиционированием

**Market (Russia) (Рынок РФ):**
- Размер: ~15 млрд ₽/год (посуда для дома)
- Рост: +12% YoY (тренд на эко)
- **Данные WB:** 50K+ товаров "деревянная посуда", 500K+ отзывов

**Competitors (Конкуренты):**
1. **EcoWood** (WB) — средний чек 1,200₽, рейтинг 4.7, 15K отзывов
2. **ДоброДерево** (WB) — средний чек 800₽, рейтинг 4.5, 8K отзывов
3. **WoodStyle** (Ozon) — средний чек 1,500₽, рейтинг 4.6, 5K отзывов

**Monetization (Монетизация):**
- B2C через WB/Ozon: наценка 2.5-3x (закуп 300₽ → продажа 900₽)
- B2B рестораны: оптовые поставки с наценкой 1.8x
- Premium линия: эксклюзивные доски 3,000-5,000₽

**Risks (Риски):**
- Высокая конкуренция на WB (50K товаров)
- Качество дерева (трещины, деформация)
- Логистика (хрупкий товар)
- Сертификация (контакт с пищей)

---

#### 2. WHY NOW (RUSSIA) (ПОЧЕМУ СЕЙЧАС В РОССИИ)

**Timing:**
- Санкции → дефицит импортной эко-посуды (Ikea ушла)
- Импортозамещение → спрос на локальные бренды
- Рост цен на пластик → деревянная посуда становится конкурентной

**Policy changes:**
- Запрет одноразового пластика в общепите (2024)
- Субсидии на эко-производство (МСП.РФ)

**Consumer trends:**
- Яндекс.Wordstat: "деревянная посуда" +35% YoY
- VK: 200+ активных сообществ про zero waste

**Window of opportunity:**
- 12-18 месяцев до насыщения рынка крупными игроками

---

#### 3. MARKET GAP (RUSSIA) (РЫНОЧНЫЙ РАЗРЫВ В РОССИИ)

**What's missing:**
- Качественные доски для сыра/подачи (премиум сегмент недоразвит)
- Детская посуда из дерева (мало предложений)
- Кастомизация (гравировка, персонализация)

**Why existing solutions fail:**
- Низкое качество (трещины через 2-3 месяца)
- Плохая упаковка (товар приходит поврежденным)
- Нет storytelling (просто "посуда", а не "эко-миссия")

**Unique angle:**
- Российское дерево + storytelling (какой лес, откуда)
- Гарантия 2 года (vs стандартная 6 месяцев)
- Zero waste упаковка (картон, без пластика)

---

#### 4. MISSING DATA (НЕДОСТАЮЩИЕ ДАННЫЕ)

**Критические вопросы для founder:**

1. **Sourcing:** Откуда закупать дерево? (Цена, качество, сертификаты)
2. **Production:** Своё производство или дропшиппинг? (Капекс, контроль качества)
3. **Pricing:** Средний чек? (Тестировали ли спрос при разных ценах?)
4. **Distribution:** Только WB/Ozon или свой сайт? (Маржинальность, зависимость от платформ)
5. **Marketing:** Как привлекать? (Инфлюенсеры, таргет, SEO?)
6. **Certification:** Сертификат контакта с пищей получен? (Сроки, стоимость)
7. **Returns:** Процент возвратов? (Хрупкий товар = высокий возврат?)
8. **Unit Economics:** COGS, CPA, LTV посчитаны? (Рентабельность подтверждена?)
9. **Seasonality:** Есть ли сезонность? (Q4 выше из-за подарков?)
10. **Competitors reaction:** Что будут делать EcoWood/ДоброДерево при вашем запуске?

---

#### 5. PROOF & SIGNALS (RUSSIA) (ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ ДЛЯ РФ)

**Что проверить на Wildberries/Ozon:**

**Demand validation:**
- Топ-10 товаров "деревянная посуда": какие отзывы? Что хвалят/ругают?
- Фильтр "новинки за 30 дней": сколько новых продавцов? (Рынок растёт или стагнирует?)
- Сезонность: сравнить продажи Q4 2024 vs Q1 2025

**Competitor signals:**
- EcoWood: динамика отзывов (растут или падают?)
- Средний рейтинг по категории: 4.5+ (качество важно!)
- Главные жалобы: "треснула через месяц", "плохая упаковка"

**Price analysis:**
- Распределение цен: 300-3,000₽ (широкий разброс)
- Sweet spot: 800-1,200₽ (максимум продаж)
- Premium: 2,000+ (низкий объём, но высокая маржа)

**Marketing channels:**
- Яндекс.Директ: CPC "деревянная посуда" ~30₽
- VK Реклама: CPM ~150₽, CTR 0.5-1%
- Инфлюенсеры: nano (5K-20K подписчиков) ~5K₽/пост

---

#### 6. ACTION PLAN (30 DAYS) (ПЛАН ДЕЙСТВИЙ НА 30 ДНЕЙ)

**Week 1: Research & Validation**
- Day 1-2: Анализ топ-20 продавцов на WB (цены, отзывы, объёмы)
- Day 3-4: Опрос 20 потенциальных клиентов (что важно при выборе?)
- Day 5-7: Поиск 3 поставщиков дерева (образцы, цены, сертификаты)

**Week 2: MVP Planning**
- Day 8-10: Выбор 5 SKU для MVP (тарелки, доски, ложки)
- Day 11-12: Дизайн упаковки (zero waste, Instagram-friendly)
- Day 13-14: Unit economics расчёт (COGS, маркетинг, маржа)

**Week 3: Supplier & Production**
- Day 15-17: Заказ образцов у 3 поставщиков (тестирование качества)
- Day 18-20: Выбор финального поставщика (цена, качество, логистика)
- Day 21: Заказ первой партии 100 шт (тестовая)

**Week 4: Pre-launch**
- Day 22-24: Регистрация на WB/Ozon (документы, карточки товаров)
- Day 25-27: Фотосессия продуктов (5-7 фото на SKU)
- Day 28-30: Настройка Яндекс.Директ (первая кампания 10K₽ бюджет)

---

#### 7. EXECUTION ROADMAP (3-12 MONTHS) (ПЛАН РЕАЛИЗАЦИИ 3-12 МЕСЯЦЕВ)

**Stage 1 (Month 1-2): MVP Launch**
- Запуск 5 SKU на WB
- Первые 50 продаж (друзья, семья, таргет)
- Collect feedback (NPS, отзывы)
- Iterate packaging (если много возвратов)
- **Goal:** Unit economics подтверждены (маржа >25%)

**Stage 2 (Month 3-6): Growth**
- Expansion на Ozon
- Increase SKU до 15 (новые категории: детская посуда, премиум доски)
- Hiring: 1 человек на маркетинг (SMM, инфлюенсеры)
- B2B pilot: 3-5 кафе/ресторанов (оптовые поставки)
- **Goal:** 500 продаж/месяц, 300K₽ выручка/мес

**Stage 3 (Month 6-12): Scaling**
- Свой сайт (Tilda / WordPress + payment)
- Email marketing (1K подписчиков → 10K)
- B2B scaling: 20+ ресторанов, корпоративные подарки
- New line: кастомизация (гравировка на заказ)
- Raise seed: 3-5M₽ (от ФРИИ, GenerationS или angel)
- **Goal:** 2,000 продаж/мес, 1.5M₽ выручка/мес, breakeven

**Stage 4 (Month 12+): Maturity**
- Franchise model (мастерские по регионам)
- Export: Казахстан, Беларусь
- Product line expansion: деревянная мебель для детей
- Exit option: продажа бизнеса или IPO на российской бирже (10-15 лет)

---

### Modes (9)

**Режимы меняют фокус анализа**, но структура 7 секций остаётся:

| Mode | Focus | Use Case |
|------|-------|----------|
| **РЕЖИМ: ОЦЕНКА** | Balanced analysis | Default, все 7 секций равномерно |
| **РЕЖИМ: БИЗНЕС-ПЛАН** | Monetization, market, roadmap | Для инвесторов, детальная финмодель |
| **РЕЖИМ: МАРКЕТИНГ** | Audience, positioning, channels | GTM strategy, customer acquisition |
| **РЕЖИМ: ИСПОЛНЕНИЕ** | Action plans | Week-by-week breakdown, execution focus |
| **РЕЖИМ: САЙТ** | Website structure | Landing page structure + Hero/Features/Pricing/FAQ |
| **РЕЖИМ: ОТЧЁТ 1** | Brief memo (1-2 pages) | Quick overview для busy founders |
| **РЕЖИМ: ОТЧЁТ 2** | Extended analysis (5-10 pages) | Detailed research, competitor deep dive |
| **РЕЖИМ: ОТЧЁТ 3** | Investor package (15-20 pages) | Финмодель, scenarios, sensitivity, exit strategy |
| **РЕЖИМ: ПОЧЕМУ_СЕЙЧАС** | Deep dive on timing | Expand Section 2, timing analysis |
| **РЕЖИМ: РЫНОЧНЫЙ_РАЗРЫВ** | Deep dive on gaps | Expand Section 3, positioning opportunities |
| **РЕЖИМ: ДОКАЗАТЕЛЬСТВА** | Validation checklist | Expand Section 5, what to test first |

**Mode detection:**
- User пишет: "РЕЖИМ: БИЗНЕС-ПЛАН Оцени идею: деревянная посуда"
- Agent извлекает режим через regex
- Применяет соответствующий фокус

---

## 🇷🇺 RUSSIAN MARKET FOCUS

### Why Russian Market is Different

**Sanctions & Import Substitution:**
- Western brands left (Ikea, Zara Home) → opportunities для локальных
- Import restrictions → локализация production
- Cross-border logistics harder → focus на domestic sourcing

**Payment Systems:**
- Visa/Mastercard не работают → Mir, YooMoney, СБП
- PayPal недоступен → локальные платёжки

**Advertising Channels:**
- Google Ads ограничен → Яндекс.Директ
- Facebook/Instagram ограничены → VK Реклама, Telegram Ads
- TikTok работает, но compliance риски

**Consumer Behavior:**
- Средний чек ниже (покупательная способность)
- Доверие к отзывам на WB/Ozon (не Google Reviews)
- Предпочтение локальных брендов (патриотизм + санкции)

### Data Sources

**Primary:**

1. **Wildberries** (www.wildberries.ru)
   - #1 marketplace Russia, 100M+ products
   - API: unofficial (scraping или партнёрская программа)
   - Data: prices, ratings, reviews, sales estimates, seller info
   - **Critical:** Основной источник competitor analysis

2. **Ozon** (www.ozon.ru)
   - #2 marketplace, growing fast
   - API: Ozon Seller API (требует регистрации как продавец)
   - Data: similar to WB
   - **Use case:** Cross-validation WB data

3. **Yandex.Wordstat** (wordstat.yandex.ru)
   - Keyword search volume
   - Regional breakdown (Москва vs регионы)
   - Seasonal trends (по месяцам)
   - **Critical:** Demand validation

**Secondary:**

4. **VK** (vk.com)
   - Social signals (communities, posts)
   - API: VK API (требует app registration)
   - Data: community size, engagement, sentiment
   - **Use case:** Audience research

5. **Telegram**
   - Channels search (через боты)
   - Subscriber counts, engagement
   - **Use case:** Niche communities, founder groups

6. **Пикабу** (pikabu.ru)
   - Reddit-like platform
   - Entrepreneur discussions
   - **Use case:** Qualitative insights

7. **МСП.РФ** (msp.rf)
   - Government SME support data
   - Grants, subsidies info
   - **Use case:** Funding opportunities

### Context Adaptations

**Language:**
- Agent output: Русский язык
- Prices: Рубли (₽)
- Dates: DD.MM.YYYY (не MM/DD/YYYY)

**Pricing Considerations:**
- Средний доход Москва: 100K₽/мес
- Средний доход регионы: 50K₽/мес
- Disposable income: ~30% от дохода
- Price sensitivity: High (сравнивают на 5+ сайтах)

**Marketing Channels Costs:**
- Яндекс.Директ CPC: 10-100₽ (зависит от ниши)
- VK Реклама CPM: 50-300₽
- Telegram Ads CPM: 100-500₽
- Инфлюенсеры: 1K-100K₽/пост (зависит от охвата)

**Regulations:**
- ИП регистрация: 1-2 недели, ~10K₽
- ООО регистрация: 2-4 недели, ~30K₽
- Сертификация товаров (пищевой контакт): 50-200K₽, 2-6 месяцев
- Маркировка (Честный знак): обязательна для некоторых категорий

---

## 🎓 LEARNING PRINCIPLES

### My Learning Goals

**Primary:**
- ✅ Научиться **Spec-Driven Development** (применимо ко всем проектам)
- ✅ Понять **Agent Architecture** (orchestration, tools, memory, modes)
- ✅ Освоить **AI-assisted coding** (не vibe coding, а structured approach)
- ✅ Приобрести **production-ready practices** (tests, error handling, docs, observability)

**Secondary:**
- Портфолио open-source проекта
- Понимание монетизации AI tools
- Опыт работы с Russian market data APIs

### Working Rules

**1. Requirements First**
- Я читаю spec/plan **ПЕРЕД** кодингом
- Не пишу код, если не понял **ЗАЧЕМ** он нужен
- Если непонятно — спрашиваю "почему так", а не "как сделать"

**2. Traceability**
- Каждое решение: `код → task → plan → spec → constitution`
- Если не могу проследить цепочку — решение сомнительно
- При review спрашиваю: "где это в spec?"

**3. Ask Why, Not Just How**
- Не просто "как реализовать forced tool call"
- А "зачем нужен forced tool call" → "потому что LLM игнорирует instruction"
- **Понимание > быстрый результат**

**4. Tests with Code**
- Тесты пишутся **ВМЕСТЕ** с кодом, не после
- TDD где возможно (write test → implement → refactor)
- Минимум: happy path + 2-3 edge cases

**5. Document as You Go**
- Комментарии, docstrings, README обновляются **сразу**
- Spec = living documentation (устарела → обновляем)
- Commit messages осмысленные (не "fix bug", а "Fix ru_search_tool timeout handling")

**6. Learn by Teaching**
- Объясняю концепты другим (Rubber duck debugging)
- Пишу туториалы / README для будущих контрибьюторов
- Если не могу объяснить — не понял до конца

---

## 🔧 KILO CODE INTEGRATION

### Modes Mapping

| SDD Этап | Kilo Code Mode | Tool Access | Why |
|----------|---------------|-------------|-----|
| **Constitution** | Architect Mode 🏗️ | `read`, `browser`, `mcp`, `edit` (только .md) | Planning без риска сломать код |
| **Specification** | Architect Mode 🏗️ | Same | User Stories, acceptance criteria |
| **Plan** | Architect Mode 🏗️ | Same | System design, architecture decisions |
| **Tasks** | Code Mode 💻 | Full access | Generate tasks.md breakdown |
| **Implementation** | Orchestrator Mode 🎯 | Delegates to other modes | Breaks complex tasks into subtasks |
| **Debugging** | Debug Mode 🐛 | Full access | Systematic troubleshooting |
| **Learning** | Ask Mode 📚 | `read`, `browser`, `mcp` only | Questions без изменения кода |

### Mode Switching

**Keyboard shortcut:** `Ctrl + .` (Windows) / `⌘ + .` (Mac)

**Cycle:**
Code → Ask → Architect → Debug → Orchestrator → Code (repeat)
Код → Ask → Architect → Debug → Orchestrator → Code (повторять)

text

### Best Practices

**✅ DO:**
- Use **Architect Mode** для всех `.md` файлов (spec, plan, docs)
- Use **Orchestrator Mode** для сложных multi-file tasks (он разобьёт на подзадачи)
- Use **Code Mode** для straightforward implementation
- Use **Debug Mode** когда что-то не работает (systematic troubleshooting)
- Use **Ask Mode** для "объясни мне концепт X" без риска сломать код

**❌ DON'T:**
- Не используй Code Mode для планирования (можешь случайно изменить код)
- Не используй Architect Mode для implementation (он не может редактировать код)
- Не пропускай Orchestrator Mode для сложных задач (он декомпозирует правильно)

### Context Mentions

**Синтаксис:** `@filename` в Kilo Code Chat

**Пример:**
Chat (Architect Mode):
"Create specification based on @.specify/constitution.md
Чат (режим архитектора): «Создайте спецификацию на основе @.specify/constitution.md

Include User Stories:

US-1: Basic idea evaluation
US-1: Базовая оценка идей

US-2: Mode detection

US-3: 7-section output"

text

**Why важно:**
- ✅ Spec/Plan всегда в контексте AI
- ✅ AI не придумывает — следует документам
- ✅ Traceability: код → @plan.md → @spec.md → @constitution.md

---

## 📚 KEY REFERENCES

### SDD Methodology

1. **Martinelli: Spec-Driven Development with AI**
   - URL: https://martinelli.ch/spec-driven-development-with-ai-a-new-approach-and-a-journey-into-the-past/
   - **Key takeaway:** Constitution → Spec → Plan → Tasks → Code workflow
   - **Read:** Sections "The Problem", "The Solution", "Workflow Example"

2. **GitHub Spec Kit Repository**
   - URL: https://github.com/github/spec-kit
   - **Key takeaway:** CLI tools `/speckit.constitution`, `/speckit.spec`, etc.
   - **Read:** README.md, EXAMPLES/

3. **LinkedIn Learning: Spec Kit Course**
   - URL: https://github.com/LinkedInLearning/spec-driven-development-with-github-spec-kit-4641001
   - **Key takeaway:** Step-by-step example project
   - **Use:** Reference implementation

### Inspiration

4. **IdeaBrowser.com**
   - URL: https://ideabrowser.com
   - **Key takeaway:** Depth of analysis, 7-section structure inspiration
   - **Study:** [Day 4 Example (GuestGuide)](https://www.ideabrowser.com/advent/dec-4-2025)

### Tools

5. **Kilo Code Documentation**
   - URL: https://kilo.ai/docs
   - **Key sections:** Using Modes, Orchestrator Mode, Context Mentions
   - **Read:** Basic Usage, Core Concepts

6. **Google ADK Documentation**
   - URL: https://ai.google.dev/gemini-api/docs/adk
   - **Key sections:** Agent, Tools, Memory
   - **Read:** Quickstart, Advanced Features

7. **Groq API Documentation**
   - URL: https://console.groq.com/docs
   - **Key sections:** Chat Completions, Function Calling
   - **Note:** Function calling limited (need wrapper!)

### Project

8. **GitHub Repository: idea-planner-agent**
   - URL: https://github.com/olegproektor/idea-planner-agent
   - **Current status:** Phase 1 (Requirements)

---

## 💬 COMMUNICATION GUIDELINES

### Language

**Agent Output (for users):**
- Русский язык
- Formal/Informal: Informal ("ты", не "вы") — более friendly
- Terminology: Minimize англицизмы (используй "целевая аудитория", не "таргет")

**Technical Discussion:**
- English/Russian (мне комфортнее смешивать)
- Code comments: English (best practice)
- Commit messages: English
- Documentation: Russian (для Russian users)

### Explanation Style

**Simple Language:**
- Я учусь — объясняй доступно
- Избегай jargon без объяснения
- Example: Не "orchestration layer for agentic workflow", а "обёртка, которая заставляет агента вызывать инструмент"

**Examples:**
- Показывай конкретные примеры (не абстракции)
- Code snippets > verbal descriptions
- Diagrams welcome (ASCII art, Mermaid, etc.)

**Why, Not Just How:**
- Объясняй **причины** решений
- Example: Не просто "используй wrapper", а "wrapper нужен, потому что Groq/Llama-3.3 не поддерживает forced function calling, поэтому LLM игнорирует instruction"

**Visual Aids:**
- Tables для comparisons
- Lists для steps/features
- Diagrams для architecture

---

## 🚫 CONSTRAINTS

### What NOT to Do

❌ **НЕ предлагай "просто попробуй"**
- Без обоснования в spec
- Example BAD: "Попробуй добавить wrapper, может сработает"
- Example GOOD: "Wrapper нужен (см. Plan section 3.2), потому что..."

❌ **НЕ пиши код без plan**
- Code без plan = vibe coding
- Сначала plan.md, потом код

❌ **НЕ пропускай SDD этапы**
- Нельзя прыгнуть с spec сразу к implementation
- Workflow sequential: Constitution → Spec → Clarify → Plan → Tasks → Code

❌ **НЕ используй "в v1 было так"**
- Это clean start
- Lessons learned из v1 = OK, но не "давай как раньше"

❌ **НЕ hallucinate**
- Если не знаешь — скажи честно "не знаю, нужно проверить"
- Не придумывай API endpoints, цены, статистику

❌ **НЕ игнорируй feedback**
- Если я говорю "не понял, объясни иначе" — объясняй иначе
- Если я не согласен — обсуждаем, не настаиваешь

---

## 📝 SESSION WORKFLOW

### Typical Iteration

**1. Я создаю artifact в Kilo Code**
- Constitution.md, spec.md, plan.md, или code files
- Use appropriate mode (Architect для .md, Code/Orchestrator для code)

**2. Я коммичу в GitHub**
git add .
git commit -m "Add constitution with 8 core principles"
git push
git add.

text

**3. Я даю тебе ссылку в Perplexity Space**
Created constitution:
https://github.com/olegproektor/idea-planner-agent/blob/main/.specify/constitution.md

Review please!

text

**4. Ты читаешь через fetch_url**
fetch_url("https://github.com/olegproektor/idea-planner-agent/blob/main/.specify/constitution.md")

text

**5. Ты даёшь feedback/next steps**
Constitution выглядит хорошо! ✅

Minor suggestion:

Principle 3 ("Forced Tool Calls") — добавь примеры, когда wrapper не нужен
(например, если используем Gemini вместо Groq)

После fix → переходим к Specification! 🚀

Next steps:

Update constitution.md
Обновление constitution.md

Commit & push

Start specification with User Stories...
Начните спецификацию с User Stories...

text

**6. Repeat для следующего этапа**

---

### My Role

**Я помогаю с:**

- **Planning & Architecture** — high-level design, tech stack choices
- **Review** — documents (spec, plan) и code quality assurance
- **Debugging** — когда Kilo Code не справляется или проблема сложная
- **Explaining Concepts** — learning support, "почему так, а не иначе"
- **Strategic Decisions** — architecture choices, trade-offs, priorities

### Your Role

**Ты делаешь:**

- **Hands-on Coding** — создание файлов через Kilo Code
- **Version Control** — commits, push, branches (если нужно)
- **Testing** — QA, user testing, edge cases
- **Final Decisions** — я советую, **ты решаешь**
- **Learning** — через практику (learning by doing)

---

## ✅ SUCCESS CRITERIA

### Functional Requirements

**1. Agent анализирует любую бизнес-идею за <2 минуты**
- Input: текстовое описание идеи
- Output: 7 секций анализа
- Time: <2 min (average)

**2. ru_search_tool ВСЕГДА вызывается перед ответом**
- No hallucination (все данные реальные)
- Wrapper enforces tool call

**3. Output всегда в 7-section формате**
- Idea Card, Why Now, Market Gap, Missing Data, Proof & Signals, Action Plan, Roadmap
- Consistent structure

**4. 9 режимов работают корректно**
- Mode detection через regex
- Каждый режим меняет фокус анализа

**5. Данные реальные (WB/Ozon/Yandex)**
- Цены, конкуренты, тренды — не выдуманные
- Citations к источникам (где взяли данные)

---

### Technical Requirements

**6. Unit/integration tests покрытие >80%**
- pytest
- Coverage report: `pytest --cov=src`

**7. Error handling везде**
- Graceful failures (API timeout → fallback)
- User-friendly error messages

**8. Документация актуальна**
- README.md
- API docs (если будет API)
- Inline comments, docstrings

**9. Code quality**
- Type hints everywhere
- Linting (ruff или flake8)
- Formatting (black)

---

### Learning Requirements

**10. Я понимаю, КАК работает агент**
- Implementation details (wrapper, tool calling, mode detection)
- Могу объяснить код

**11. Я понимаю, ПОЧЕМУ сделано так**
- Architectural decisions обоснованы
- Traceability: код → plan → spec → constitution

**12. Я могу объяснить каждое решение**
- На вопрос "зачем X" могу проследить до constitution/spec
- No magic, все решения documented

---

## 🎯 CURRENT STATUS

### Timeline

**Start Date:** 2025-12-13  
**Current Phase:** Phase 1 — Requirements (Constitution)  
**Estimated Completion:** 2025-12-27 (14 days)

### Phase Progress

#### Phase 0: Setup ✅ (Completed 2025-12-13)
- [x] GitHub repo created: https://github.com/olegproektor/idea-planner-agent
- [x] Perplexity Space configured
- [x] Spec Kit installed (`specify --version`)
- [x] Kilo Code ready (modes tested)
- [x] Context document created (this file)

#### Phase 1: Requirements ← **CURRENT**
- [ ] **Constitution** (today, 1-2 hours)
  - [ ] Draft constitution.md in Architect Mode
  - [ ] Review & iterate
  - [ ] Commit & push
  
- [ ] **Specification** (tomorrow, 2-3 hours)
  - [ ] User Stories (US-1 to US-5)
  - [ ] Acceptance criteria
  - [ ] Non-functional requirements
  
- [ ] **Clarification** (tomorrow, 1 hour)
  - [ ] AI asks questions
  - [ ] Answer & update spec

#### Phase 2: Planning (Day 3-4, 2-3 hours)
- [ ] Technical Plan (architecture, tech stack)
- [ ] Data Model (agent state, tool inputs/outputs)
- [ ] Tasks Breakdown (implementation checklist)

#### Phase 3: Implementation (Day 5-10, 10-15 hours)
- [ ] Phase 1: Core Agent (agent.py with instruction)
- [ ] Phase 2: Tools (ru_search.py)
- [ ] Phase 3: Wrapper (forced tool calls)
- [ ] Phase 4: Modes (mode detection, focus adaptation)
- [ ] Phase 5: Testing (unit, integration, e2e)

#### Phase 4: Validation (Day 11-14, 4-6 hours)
- [ ] Unit Tests (>80% coverage)
- [ ] Integration Tests (agent + tools)
- [ ] E2E Tests (full user scenarios)
- [ ] Documentation Review (README, API docs)
- [ ] Performance Testing (<2 min per analysis)

---

## 📅 ESTIMATED TIMELINE

| Phase | Duration | Hours | Completion Date |
|-------|----------|-------|-----------------|
| **Phase 0: Setup** | 1 day | 2h | ✅ 2025-12-13 |
| **Phase 1: Requirements** | 2 days | 4-6h | 2025-12-15 |
| **Phase 2: Planning** | 1 day | 2-3h | 2025-12-16 |
| **Phase 3: Implementation** | 6 days | 10-15h | 2025-12-22 |
| **Phase 4: Validation** | 4 days | 4-6h | 2025-12-26 |
| **Buffer** | 1 day | - | 2025-12-27 |
| **TOTAL** | **14 days** | **20-30h** | **2025-12-27** |

**Target:** Working MVP by end of December 2025 🎯

---

## 📖 GLOSSARY

| Term | Definition |
|------|------------|
| **SDD** | Spec-Driven Development — methodology: Constitution → Spec → Plan → Tasks → Code |
| **Constitution** | Fundamental principles of the project (как принимаются решения) |
| **Spec** | Specification — WHAT the agent should do (User Stories, acceptance criteria) |
| **Plan** | Technical plan — HOW to implement (architecture, tech stack, data model) |
| **Tasks** | Breakdown into atomic tasks for implementation |
| **ADK** | Agent Development Kit (Google) — framework для AI agents |
| **WB** | Wildberries — #1 Russian marketplace |
| **Wrapper** | Orchestration layer that forces tool calls before LLM response |
| **Mode** | Kilo Code mode (Architect, Code, Debug, Ask, Orchestrator) |
| **Traceability** | Ability to trace decision: код → task → plan → spec → constitution |
| **Forced Tool Call** | Mechanism to ensure tool execution before LLM generates response |

---

## 🔄 DOCUMENT MAINTENANCE

### How to Update This Document

**When to update:**
- После завершения каждого SDD этапа (Constitution done → update status)
- При принятии важных архитектурных решений
- При изменении tech stack / tools
- При обнаружении ошибок / outdated info

**Who updates:**
- Ты (через VS Code / Dropbox web)
- Version controlled в GitHub? (опционально, можно и просто в Dropbox)

**Template for updates:**
Update:2025-12-14
Changed: Added section X, Updated tech stack choice Y
Reason: Decision made during Plan phase to use Z instead of Y

text

### Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-13 | Initial document created | Oleg Proektor |

---

## 📞 CONTACT & RESOURCES

### Project Links

- **GitHub:** https://github.com/olegproektor/idea-planner-agent
- **Perplexity Space:** idea_planner_agent — SDD Workflow
- **Dropbox Context:** This file

### External Resources

- **SDD:** https://martinelli.ch/spec-driven-development
- **Spec Kit:** https://github.com/github/spec-kit
- **Kilo Code:** https://kilo.ai/docs, https://kilo.ai/docs/basic-usage/orchestrator-mode, kilo.ai/docs/basic-usage/using-modes
- **IdeaBrowser:** https://www.ideabrowser.com/advent/dec-4-2025

---

END OF DOCUMENT

**Last Updated:** 2025-12-13 18:23 MSK  
**Version:** 1.0  
**Status:** Phase 1 (Requirements) — Constitution in progress  
**Next Milestone:** Constitution approved → Specification