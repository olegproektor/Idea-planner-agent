# Architecture Decisions — idea-planner-agent MVP

**Date:** 2024-12-14  
**Phase:** Plan  
**Status:** Approved

## Database
- **Decision:** SQLite
- **Rationale:** Simple setup, sufficient for 100 concurrent users, easy PostgreSQL migration later
- **Implementation:** `bot.db` file, SQLAlchemy ORM

## Caching Strategy
- **Decision:** In-memory dict with TTL (cachetools)
- **Rationale:** Zero setup, sufficient for MVP, data loss on restart acceptable
- **Implementation:** `cachetools.TTLCache(maxsize=1000, ttl=21600)` (6 hours)
- **Future:** Migrate to Redis in v1.1 if needed

## LLM Provider
- **Decision:** Configurable provider (Groq/Llama-3.3-70b default)
- **Rationale:** Flexibility for testing different LLMs
- **Implementation:** Abstract `LLMProvider` interface, `GroqProvider` default
- **Config:** `.env` variable `LLM_PROVIDER=groq`

## ru_search_tool
- **Decision:** Separate module `ru_search/`
- **Rationale:** Reusability, clean architecture, can use in other projects
- **API Design:**
from ru_search import search
results = search(query="посуда", sources=["wb", "ozon"])

text

## Deployment Platform
- **Decision:** Railway.app
- **Rationale:** Easiest webhook setup, auto HTTPS, simple GitHub integration
- **Free tier:** 500 hours/month sufficient for MVP testing
- **Migration path:** Can move to Google Cloud Run later (1-2h work)

## Secrets Management
- **Decision:** Both .env (local) + Railway env vars (production)
- **Rationale:** Best of both worlds — convenient local dev, secure production
- **Implementation:**
config.py
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LLM_API_KEY = os.getenv("LLM_API_KEY")

text
- **.env** file (git-ignored) for local
- **Railway dashboard** env vars for production

## Testing Strategy
- **Decision:** Unit tests + Integration tests (no E2E for MVP)
- **Rationale:** 80%+ coverage achievable, mock Telegram API, avoid E2E complexity
- **Tools:** pytest, unittest.mock
- **Coverage target:** >80% (constitution requirement)
- **E2E:** Defer to v1.1 after MVP validation

## Testing Pyramid
text
  /\
 /E2E\    ← v1.1
/------\
/Integr.\ ← Mock Telegram API
/----------
/Unit Tests \ ← 80%+ coverage
/--------------\

text

## Traceability
All decisions aligned with:
- Constitution v0.1.1 (engineering quality, testing requirements)
- Spec.md v2.0 (FR-010..FR-013 caching, NFR-003 quality gates)
- Spec-Driven Development methodology

## Next Phase
- **Plan.md generation** via Kilo Code Architect Mode
- **Target completion:** 2024-12-14 18:30-19:00 MSK