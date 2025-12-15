# Task 003: Configuration System

**Phase**: 1 - Foundation  
**Estimated Hours**: 2  
**Priority**: P1  
**Status**: Not Started

---

## Description

Create a flexible configuration system for the idea-planner-agent MVP that supports both development and production environments. This includes environment variables, configuration files, and secrets management.

---

## Acceptance Criteria

- [ ] `.env` template created with all required variables (FR-001)
- [ ] `config.py` module implemented with environment loading (NFR-003)
- [ ] Railway.app environment variables template documented
- [ ] Configuration system supports both local and production environments
- [ ] All sensitive data properly secured

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 3.1 Create .env template | 0.5 | Define all required environment variables |
| 3.2 Implement config.py | 1.0 | Create configuration loading module |
| 3.3 Document Railway setup | 0.5 | Create deployment configuration guide |

---

## Dependencies

**Depends on**: Task 001 (Project Structure Setup)

**Required for**: Task 004 (Telegram Bot Skeleton), Task 005 (ru_search Module)

---

## Testing Requirements

- [ ] Verify all environment variables load correctly
- [ ] Test configuration in both development and production modes
- [ ] Confirm sensitive data is not exposed in logs
- [ ] Validate configuration validation works properly
- [ ] Test Railway.app environment variable setup

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| .env template | Ethics (VIII) | FR-008 |
| Configuration loading | Engineering Quality (VI) | NFR-003 |
| Secrets management | Reality-First (III) | Constitution v0.1.1 |
| Environment separation | Traceability (II) | Technical Notes |

---

## Implementation Notes

### .env Template

```env
# .env.template

# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here

# LLM Configuration
LLM_PROVIDER=groq
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=llama-3.3-70b

# Database Configuration
DATABASE_URL=sqlite:///bot.db
DATABASE_ECHO=False

# Caching Configuration
CACHE_TTL=21600
CACHE_MAXSIZE=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Development Configuration
DEVELOPMENT_MODE=True
```

### Configuration Module

```python
# config.py
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    
    # Caching Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "21600"))
    CACHE_MAXSIZE: int = int(os.getenv("CACHE_MAXSIZE", "1000"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # Development Configuration
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "True").lower() == "true"
    
    def validate(self):
        """Validate required configuration values"""
        required_vars = {
            "TELEGRAM_TOKEN": self.TELEGRAM_TOKEN,
            "LLM_API_KEY": self.LLM_API_KEY,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
        
        return True

# Initialize configuration
config = Config()

# Validate configuration on import
if not config.DEVELOPMENT_MODE:
    config.validate()
```

### Railway.app Configuration Guide

```markdown
# Railway.app Deployment Configuration

## Environment Variables Setup

1. **Telegram Bot Configuration**:
   - `TELEGRAM_TOKEN`: Your Telegram bot token from @BotFather
   - `TELEGRAM_WEBHOOK_URL`: `https://your-app.railway.app/telegram/webhook`
   - `TELEGRAM_WEBHOOK_SECRET`: Generate a random secret for webhook validation

2. **LLM Configuration**:
   - `LLM_PROVIDER`: `groq` (default)
   - `LLM_API_KEY`: Your Groq API key
   - `LLM_MODEL`: `llama-3.3-70b` (default)

3. **Database Configuration**:
   - `DATABASE_URL`: `sqlite:///bot.db` (default)
   - `DATABASE_ECHO`: `False` (production)

4. **Caching Configuration**:
   - `CACHE_TTL`: `21600` (6 hours)
   - `CACHE_MAXSIZE`: `1000`

5. **Logging Configuration**:
   - `LOG_LEVEL`: `INFO`
   - `LOG_FORMAT`: `json`

6. **Production Configuration**:
   - `DEVELOPMENT_MODE`: `False`

## Deployment Steps

1. Create new Railway project
2. Connect GitHub repository
3. Add all environment variables in Railway dashboard
4. Deploy application
5. Set up custom domain (optional)
```

---

## Success Criteria

- [ ] All required environment variables defined and documented
- [ ] Configuration module properly loads and validates settings
- [ ] Development and production configurations working
- [ ] Railway.app deployment configuration documented
- [ ] Sensitive data properly secured

---

## Next Tasks

- [ ] Task 004: Telegram Bot Skeleton (depends on this task)
- [ ] Task 005: ru_search Module (depends on this task)
- [ ] Task 006: Telegram Bot Logic (depends on this task)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (FR-008)
- **Plan**: `plan.md` Phase 1.3
- **Architecture**: `architecture-decisions.md` Secrets Management section
---

## Completion Summary

**Completed**: 2025-12-15 18:11 MSK  
**Actual Time**: ~3 hours (estimated: 3h) ✅  
**Test Results**: 26/26 tests PASSED

**Files Created**:
- `src/config.py` - Pydantic Settings with type validation
- `.env.example` - Template with correct defaults (21600s cache, SQLite)
- `tests/test_config.py` - 26 comprehensive tests
- `requirements.txt` - Updated with pydantic, pydantic-settings, python-dotenv

**Test Coverage**:
- 26 test cases covering all scenarios
- 100% pass rate
- Tests isolated with TestSettings class

**Key Achievements**:
- ✅ Type-safe configuration with Pydantic BaseSettings
- ✅ Secure secrets management (.env in .gitignore)
- ✅ Required fields: TELEGRAM_TOKEN, GROQ_API_KEY
- ✅ Optional fields with correct defaults (CACHE_TTL=21600, DATABASE_URL=sqlite)
- ✅ Comprehensive validation and error handling
- ✅ Ready for Task-004 integration

**Status**: ✅ COMPLETED

**Traceability**:
- Implements: plan.md Phase 1.3
- Refs: architecture-decisions.md (Secrets Management)
- Follows: constitution.md Principle VI (Engineering Quality)

**Next**: Task-004 (Telegram Bot Skeleton)