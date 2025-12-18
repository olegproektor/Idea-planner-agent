# idea_planner_agent

AI-агент для валидации бизнес-идей на российском рынке.

## Описание

Агент анализирует бизнес-идеи с использованием реальных данных с Wildberries, Ozon, Yandex и предоставляет структурированный отчёт из 7 секций.

## Методология

Spec-Driven Development с GitHub Spec Kit.

## Текущий статус

**Updated: 18.12.2025**

- Phase: Implementation (Tasks 1-5 complete)
- Next: Task-006 (Telegram bot logic) + Task-007 (LLM integration)

### Completed:
✅ Constitution v0.1.1 (.specify/constitution.md)
✅ Spec v2.0 (.specify/specs/001-core-spec.md)
✅ Plan v1.0 (plan.md, 65h estimate)
✅ Tasks 001-010 breakdown
✅ Database layer (97% coverage)
✅ Config system (Pydantic)
✅ Telegram bot skeleton (38/38 tests)
✅ ru_search module (81% tests passing)

### Known Issues:
⚠️ WB/Ozon scraping blocked (403) - Need public API solution
⚠️ Groq API not integrated - Priority task
⚠️ 15 tests failing in ru_search (mock-related, not blockers)

## Tech Stack

- Google ADK + Groq/Llama-3.3-70b
- GitHub Spec Kit
- Kilo Code
- Python 3.11+
