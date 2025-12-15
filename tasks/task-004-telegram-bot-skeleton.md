# Task 004: Telegram Bot Skeleton

**Phase**: 1 - Foundation  
**Estimated Hours**: 5  
**Priority**: P1  
**Status**: Not Started

---

## Description

Create the basic Telegram bot skeleton using webhook-based architecture. This task implements the core bot structure, command handlers, and basic functionality that will be extended in later tasks.

---

## Acceptance Criteria

- [ ] Webhook-based Telegram bot implemented using `python-telegram-bot` (FR-001)
- [ ] Command handlers created: `/start`, `/help` (FR-002)
- [ ] Basic message handler for idea analysis implemented (FR-003)
- [ ] Error handling and logging system in place (NFR-003)
- [ ] Progress indicator system working (`⏳ Анализирую...`) (US-1)
- [ ] Bot responds to basic commands and messages

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 4.1 Set up bot framework | 1.0 | Initialize python-telegram-bot with webhook support |
| 4.2 Implement command handlers | 1.5 | Create /start and /help command handlers |
| 4.3 Create message handler | 1.5 | Implement basic idea analysis message handler |
| 4.4 Add error handling | 0.5 | Implement comprehensive error handling |
| 4.5 Add logging system | 0.5 | Set up structured logging (JSON format) |

---

## Dependencies

**Depends on**: 
- Task 001 (Project Structure Setup)
- Task 002 (Database Implementation) - for user data storage
- Task 003 (Configuration System) - for bot configuration

**Required for**: 
- Task 006 (Telegram Bot Logic) - extends this skeleton
- Task 007 (LLM Integration) - integrates with bot

---

## Testing Requirements

- [ ] Verify bot responds to `/start` command with welcome message
- [ ] Test `/help` command provides useful information
- [ ] Confirm basic message handler processes idea inputs
- [ ] Validate error handling works for invalid inputs
- [ ] Test logging system captures all relevant events
- [ ] Verify progress indicator displays correctly

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| Bot framework | Russia-First (V) | FR-001, US-1 |
| Command handlers | Reality-First (III) | FR-002 |
| Message handler | Citations (IV) | FR-003 |
| Error handling | Resilience (VII) | US-4, NFR-003 |
| Logging system | Engineering Quality (VI) | NFR-003 |

---

## Implementation Notes

### Webhook-Based Bot Architecture

```python
# main.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes
import logging
from config import config

# Set up logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Добро пожаловать в Idea Planner Agent!\n\n"
        "Отправьте мне свою бизнес-идею, и я проведу анализ\n"
        "Пример: 'Производство деревянной посуды'"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 Как использовать бота:\n\n"
        "1. Отправьте свою бизнес-идею\n"
        "2. Для специального анализа используйте: РЕЖИМ: БИЗНЕС-ПЛАН\n"
        "3. Подождите 1-2 минуты для полного анализа\n"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (idea analysis)"""
    message_text = update.message.text
    
    # Show progress indicator
    progress_message = await update.message.reply_text("⏳ Анализирую вашу идею...")
    
    # Basic validation
    if not message_text or len(message_text.strip()) < 5:
        await progress_message.edit_text("❌ Пожалуйста, опишите вашу идею в 1-2 предложениях")
        return
    
    # TODO: Implement full analysis logic (will be added in Task 006)
    await progress_message.edit_text("✅ Анализ завершён! (Базовая версия)")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error in {context.error}")
    if hasattr(update, 'message'):
        await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")

def main():
    """Main bot application"""
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start bot
    if config.DEVELOPMENT_MODE:
        logger.info("Starting bot in polling mode (development)")
        application.run_polling()
    else:
        logger.info("Starting bot in webhook mode (production)")
        application.run_webhook(
            listen="0.0.0.0",
            port=8080,
            webhook_url=config.TELEGRAM_WEBHOOK_URL,
            secret_token=config.TELEGRAM_WEBHOOK_SECRET
        )

if __name__ == "__main__":
    main()
```

### Command Handler Implementation

```python
# handlers/commands.py
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    
    Acceptance Criteria:
    - FR-002: Bot responds to /start
    - Russia-First (V): Response in Russian
    """
    welcome_message = (
        "👋 Добро пожаловать в Idea Planner Agent!\n\n"
        "Я помогу вам проанализировать бизнес-идею для российского рынка.\n\n"
        "Просто отправьте мне описание вашей идеи, например:\n"
        "'Производство экологичной деревянной посуды'\n\n"
        "Для специальных режимов анализа используйте:\n"
        "РЕЖИМ: БИЗНЕС-ПЛАН - для инвесторов\n"
        "РЕЖИМ: МАРКЕТИНГ - для продвижения\n"
        "РЕЖИМ: ИСПОЛНЕНИЕ - для реализации"
    )
    
    await update.message.reply_text(welcome_message)
```

### Message Handler with Progress Indicator

```python
# handlers/messages.py
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def handle_idea_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle idea analysis messages
    
    Acceptance Criteria:
    - FR-003: Any text idea launches analysis
    - US-1: Shows progress indicator
    - NFR-001: p90 latency < 2 minutes
    """
    try:
        message_text = update.message.text.strip()
        
        # Validate input
        if not message_text or len(message_text) < 5:
            await update.message.reply_text(
                "❌ Пожалуйста, опишите вашу идею в 1-2 предложениях"
            )
            return
        
        # Show progress indicator
        progress_msg = await update.message.reply_text("⏳ Анализирую вашу идею...")
        
        # TODO: Implement mode detection (Task 006)
        # TODO: Implement full analysis (Task 006)
        # TODO: Implement 7-section report (Task 006)
        
        # Temporary response for skeleton
        await progress_msg.edit_text("✅ Базовый анализ завершён!")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")
```

### Error Handling and Logging

```python
# utils/error_handling.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

# Configure structured logging
logging.basicConfig(
    level="INFO",
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors gracefully
    
    Acceptance Criteria:
    - US-4: Graceful degradation instead of crashes
    - NFR-003: Structured logging
    """
    error = context.error
    
    # Log error details
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "update_type": type(update).__name__ if update else "unknown"
    }
    
    logger.error(f"Bot error: {error_data}")
    
    # Notify user if possible
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ Произошла техническая ошибка. "
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой."
        )
```

---

## Success Criteria

- [ ] Telegram bot responds to `/start` and `/help` commands
- [ ] Basic message handler processes idea inputs
- [ ] Progress indicator system working correctly
- [ ] Error handling prevents crashes and logs issues
- [ ] Logging system captures all relevant events
- [ ] Bot ready for extension with core logic

---

## Next Tasks

- [ ] Task 005: ru_search Module (can be done in parallel)
- [ ] Task 006: Telegram Bot Logic (extends this skeleton)
- [ ] Task 007: LLM Integration (integrates with bot)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (FR-001..FR-003, US-1, US-4)
- **Plan**: `plan.md` Phase 1.4
- **Architecture**: `architecture-decisions.md` Telegram Bot section
- **Technical Notes**: Webhook mode requirements

---

## Completion Summary

**Completed**: 2025-12-15 21:56 MSK  
**Actual Time**: ~5 hours (estimated: 5h) ✅  
**Test Results**: 38/38 tests PASSED in 5.73s

**Files Created**:
- `src/bot.py` - Webhook-based Telegram bot with FastAPI
- `src/handlers.py` - Command and message handlers
- `tests/test_bot.py` - 22 tests (bot initialization, webhook, FastAPI)
- `tests/test_handlers.py` - 16 tests (handlers + error handling)

**Functionality Implemented**:
- ✅ `/start` command with Russian welcome message and mode explanation
- ✅ `/help` command with detailed mode descriptions
- ✅ Message handler for idea analysis with progress indicator
- ✅ Progress indicator: "⏳ Анализирую вашу идею..."
- ✅ Database integration: UserCRUD, IdeaCRUD, AnalysisCRUD
- ✅ Error handling with graceful degradation
- ✅ Structured logging (NFR-003 compliant)
- ✅ FastAPI webhook endpoint: /telegram/webhook
- ✅ Health check endpoint: /health
- ✅ Type hints throughout

**Dependencies Added**:
- fastapi
- uvicorn
- pytest-asyncio
- httpx (for testing)

**Test Coverage**:
- 38 comprehensive tests
- 100% pass rate
- All handlers tested with mocks
- Error scenarios covered

**Key Achievements**:
- Clean separation: bot.py (infrastructure) + handlers.py (logic)
- Russia-First messages (все на русском)
- Ready for Railway.app deployment
- Ready for Task-005 (ru_search) integration

**Status**: ✅ COMPLETED

**Traceability**:
- Implements: spec.md FR-002, FR-003
- Refs: plan.md Phase 1.4
- Follows: constitution.md Principle V (Russia-First), VI (Engineering Quality)

**Next**: Task-005 (ru_search Module)
