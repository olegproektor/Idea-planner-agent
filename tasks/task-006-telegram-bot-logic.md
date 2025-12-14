# Task 006: Telegram Bot Logic

**Phase**: 2 - Core Features  
**Estimated Hours**: 15  
**Priority**: P1  
**Status**: Not Started

---

## Description

Implement the core Telegram bot logic including mode detection, 7-section report generation, citation formatting, and all user interaction features. This task extends the basic skeleton from Task 004.

---

## Acceptance Criteria

- [ ] Mode detection regex implemented: `РЕЖИМ: {mode}` (FR-006, US-2)
- [ ] All 11 modes supported and functional (US-2)
- [ ] 7-section report generation working (FR-004, US-1)
- [ ] Citation formatting according to constitution (FR-005, AC-1..AC-4)
- [ ] Data freshness indicators implemented (⚠️, 🔴) (AC-2)
- [ ] Message splitting for Telegram 4096 char limit (Edge Cases)
- [ ] Error handling for all edge cases (US-4)
- [ ] Progress indicator system enhanced (US-1)
- [ ] Bot provides complete, useful responses to users

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 6.1 Implement mode detection | 2.0 | Regex for mode detection and validation |
| 6.2 Create mode handlers | 4.0 | Implement logic for all 11 modes |
| 6.3 Implement 7-section reports | 3.0 | Generate structured 7-section analysis |
| 6.4 Add citation formatting | 2.0 | Proper citation formatting per constitution |
| 6.5 Implement message splitting | 1.0 | Handle Telegram message length limits |
| 6.6 Enhance error handling | 2.0 | Comprehensive error handling for all cases |
| 6.7 Add progress updates | 1.0 | Enhanced progress indicator system |

---

## Dependencies

**Depends on**: 
- Task 004 (Telegram Bot Skeleton) - base bot structure
- Task 005 (ru_search Module) - data collection functionality
- Task 002 (Database Implementation) - user and job tracking
- Task 003 (Configuration System) - bot configuration

**Required for**: 
- Task 007 (LLM Integration) - integrates with bot logic
- Task 008 (Mode Analysis) - extends mode functionality

---

## Testing Requirements

- [ ] Verify all 11 modes are detected and handled correctly
- [ ] Test 7-section report generation for all modes
- [ ] Confirm citation formatting matches constitution requirements
- [ ] Validate message splitting works for long reports
- [ ] Test error handling for all edge cases
- [ ] Verify progress indicators update appropriately
- [ ] Confirm bot responses are useful and complete

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| Mode detection | Reality-First (III) | FR-006, US-2 |
| Mode handlers | Russia-First (V) | US-2, SC-004 |
| 7-section reports | Citations (IV) | FR-004, US-1 |
| Citation formatting | Traceability (II) | FR-005, AC-1..AC-4 |
| Message splitting | Engineering Quality (VI) | Edge Cases |
| Error handling | Resilience (VII) | US-4, NFR-003 |
| Progress updates | Ethics (VIII) | US-1, NFR-001 |

---

## Implementation Notes

### Mode Detection System

```python
# bot/modes.py
import re
from typing import Optional, Tuple

# Supported modes (from US-2)
SUPPORTED_MODES = [
    "ОЦЕНКА", "БИЗНЕС-ПЛАН", "МАРКЕТИНГ", "ИСПОЛНЕНИЕ", "САЙТ",
    "ОТЧЁТ 1", "ОТЧЁТ 2", "ОТЧЁТ 3", "ПОЧЕМУ_СЕЙЧАС", "РЫНОЧНЫЙ_РАЗРЫВ", "ДОКАЗАТЕЛЬСТВА"
]

def detect_mode(message_text: str) -> Tuple[Optional[str], str]:
    """
    Detect mode from message text
    
    Args:
        message_text: Full user message
        
    Returns:
        Tuple of (mode, idea_text) or (None, original_text)
        
    Acceptance Criteria:
        - FR-006: Regex detects РЕЖИМ: {mode}
        - US-2: All 11 modes supported
        - Resilience VII: Invalid mode handled gracefully
    """
    # Pattern: РЕЖИМ: mode_name (case-insensitive for Russian)
    pattern = r'^РЕЖИМ:\s*(.+?)\s*[:\n]'
    match = re.search(pattern, message_text, re.IGNORECASE)
    
    if match:
        detected_mode = match.group(1).strip().upper()
        
        # Find closest match for typo handling
        if detected_mode not in SUPPORTED_MODES:
            closest = _find_closest_mode(detected_mode)
            if closest:
                detected_mode = closest
            else:
                return None, message_text  # Invalid mode
        
        # Extract idea text (after mode declaration)
        idea_text = message_text[match.end():].strip()
        return detected_mode, idea_text
    
    return None, message_text

def _find_closest_mode(invalid_mode: str) -> Optional[str]:
    """Find closest supported mode for typo handling"""
    from difflib import get_close_matches
    
    matches = get_close_matches(invalid_mode, SUPPORTED_MODES, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_mode_description(mode: str) -> str:
    """Get description for each mode"""
    descriptions = {
        "ОЦЕНКА": "Сбалансированный анализ (по умолчанию)",
        "БИЗНЕС-ПЛАН": "Фокус на финансовых показателях для инвесторов",
        "МАРКЕТИНГ": "Анализ целевой аудитории и каналов продвижения",
        "ИСПОЛНЕНИЕ": "Детальный план реализации идеи",
        "САЙТ": "Рекомендации по структуре и контенту сайта",
        "ОТЧЁТ 1": "Глубокий анализ данных WB/Ozon",
        "ОТЧЁТ 2": "Детальный 30-дневный план действий",
        "ОТЧЁТ 3": "Расширенный roadmap на 3-12 месяцев",
        "ПОЧЕМУ_СЕЙЧАС": "Анализ рыночного timing и возможностей",
        "РЫНОЧНЫЙ_РАЗРЫВ": "Исследование конкурентных преимуществ",
        "ДОКАЗАТЕЛЬСТВА": "Фокус на валидации данных и сигналах"
    }
    return descriptions.get(mode, "Неизвестный режим")
```

### 7-Section Report Generator

```python
# bot/report_generator.py
from typing import Dict, List
from ru_search import search
from bot.modes import SUPPORTED_MODES

class ReportGenerator:
    def __init__(self):
        self.data_cache = {}
    
    async def generate_report(
        self,
        idea_text: str,
        mode: str = "ОЦЕНКА",
        progress_callback=None
    ) -> List[str]:
        """
        Generate 7-section report for user idea
        
        Args:
            idea_text: User's business idea
            mode: Analysis mode (default: "ОЦЕНКА")
            progress_callback: Function to update progress
        
        Returns:
            List of Telegram messages (split if needed)
            
        Acceptance Criteria:
            - FR-004: 7-section report structure
            - US-1: All sections in strict order
            - NFR-001: p90 latency < 2 minutes
        """
        # Update progress
        if progress_callback:
            await progress_callback("🔍 Ищу данные по вашей идее...")
        
        # Get market data
        search_results = search(idea_text, sources=["wb", "ozon", "yandex"])
        
        if progress_callback:
            await progress_callback("📊 Анализирую рыночные данные...")
        
        # Generate sections based on mode
        sections = []
        
        # Section 1: КАРТОЧКА ИДЕИ
        sections.append(self._generate_section_1(idea_text, search_results, mode))
        
        # Section 2: ПОЧЕМУ СЕЙЧАС
        sections.append(self._generate_section_2(idea_text, search_results, mode))
        
        # Section 3: РЫНОЧНЫЙ РАЗРЫВ
        sections.append(self._generate_section_3(idea_text, search_results, mode))
        
        # Section 4: НЕДОСТАЮЩИЕ ДАННЫЕ
        sections.append(self._generate_section_4(idea_text, search_results, mode))
        
        # Section 5: ДОКАЗАТЕЛЬСТВА И СИГНАЛЫ
        sections.append(self._generate_section_5(idea_text, search_results, mode))
        
        # Section 6: ПЛАН ДЕЙСТВИЙ
        sections.append(self._generate_section_6(idea_text, search_results, mode))
        
        # Section 7: ПЛАН РЕАЛИЗАЦИИ
        sections.append(self._generate_section_7(idea_text, search_results, mode))
        
        # Combine sections and split for Telegram
        full_report = "\n\n".join(sections)
        return self._split_for_telegram(full_report)
    
    def _generate_section_1(self, idea: str, data: Dict, mode: str) -> str:
        """Section 1: КАРТОЧКА ИДЕИ"""
        # Mode-specific generation logic
        if mode == "БИЗНЕС-ПЛАН":
            return self._generate_business_plan_section_1(idea, data)
        elif mode == "МАРКЕТИНГ":
            return self._generate_marketing_section_1(idea, data)
        # ... other modes
        else:  # Default ОЦЕНКА mode
            return self._generate_default_section_1(idea, data)
    
    def _generate_default_section_1(self, idea: str, data: Dict) -> str:
        """Default Section 1 generation"""
        wb_data = next((s for s in data.sources if s.source == "wb"), None)
        ozon_data = next((s for s in data.sources if s.source == "ozon"), None)
        
        section = f"📋 КАРТОЧКА ИДЕИ\n\n"
        section += f"**Идея:** {idea}\n\n"
        
        # Problem and Solution
        section += "**Проблема:** "
        section += "Решение проблемы с [описание проблемы]\n\n"
        
        section += "**Решение:** "
        section += "Ваше предложение решает проблему через [описание решения]\n\n"
        
        # Target Audience
        section += "**Целевая аудитория:** "
        section += "Потребители в возрасте 25-45 лет, интересующиеся [тема]\n\n"
        
        # Market Size
        section += "**Размер рынка:** "
        if wb_data and wb_data.price_range:
            section += f"{wb_data.price_range} (WB), "
        if ozon_data and ozon_data.price_range:
            section += f"{ozon_data.price_range} (Ozon)"
        section += "\n\n"
        
        # Competitors
        section += "**Конкуренты:** "
        competitors = []
        if wb_data and wb_data.products:
            competitors.extend([p['title'] for p in wb_data.products[:3]])
        if ozon_data and ozon_data.products:
            competitors.extend([p['title'] for p in ozon_data.products[:3]])
        section += ", ".join(competitors[:5]) + "\n\n"
        
        # Monetization
        section += "**Монетизация:** "
        section += "Продажа через маркетплейсы, собственный сайт, розничные партнеры\n\n"
        
        # Risks
        section += "**Риски:** "
        section += "Высокая конкуренция, зависимость от поставщиков, сезонность\n"
        
        return section
    
    # ... other section generation methods
    
    def _split_for_telegram(self, text: str) -> List[str]:
        """Split long messages for Telegram 4096 char limit"""
        max_length = 4096
        messages = []
        
        if len(text) <= max_length:
            return [text]
        
        # Split by sections first
        sections = text.split("\n\n")
        current_message = ""
        
        for i, section in enumerate(sections):
            if len(current_message) + len(section) + 2 <= max_length:
                if current_message:
                    current_message += "\n\n"
                current_message += section
            else:
                messages.append(current_message)
                current_message = section
        
        if current_message:
            messages.append(current_message)
        
        # Add message indicators
        for i, msg in enumerate(messages):
            messages[i] = f"📄 Часть {i+1}/{len(messages)}\n\n{msg}"
        
        return messages
```

### Citation Formatting

```python
# bot/citations.py
from datetime import datetime
import pytz

def format_citation(url: str, description: str) -> str:
    """
    Format citation according to constitution standard
    
    Args:
        url: Source URL
        description: What the citation confirms
        
    Returns:
        Formatted citation string
        
    Acceptance Criteria:
        - AC-1: Proper citation format
        - Russia-First V: MSK timezone
    """
    # Get current time in Moscow timezone
    msk_tz = pytz.timezone('Europe/Moscow')
    timestamp = datetime.now(msk_tz).strftime('%d.%m.%Y %H:%M')
    
    return f"[{url}, {timestamp}, \"{description}\"]"

def add_freshness_indicator(citation: str, timestamp_str: str) -> str:
    """
    Add freshness indicator based on data age
    
    Args:
        citation: Original citation
        timestamp_str: Timestamp string (DD.MM.YYYY HH:MM)
        
    Returns:
        Citation with freshness indicator if needed
        
    Acceptance Criteria:
        - AC-2: Data freshness indicators
    """
    try:
        # Parse timestamp
        timestamp = datetime.strptime(timestamp_str, '%d.%m.%Y %H:%M')
        msk_tz = pytz.timezone('Europe/Moscow')
        timestamp = msk_tz.localize(timestamp)
        
        now = datetime.now(msk_tz)
        age_hours = (now - timestamp).total_seconds() / 3600
        
        # Add indicators based on age
        if age_hours > 48:
            return f"🔴 Данные устаревшие (от {timestamp_str})\n{citation}"
        elif age_hours > 6:
            return f"⚠️ Данные от {timestamp_str}\n{citation}"
        else:
            return citation
            
    except:
        return citation
```

### Enhanced Message Handler

```python
# bot/handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modes import detect_mode, get_mode_description
from bot.report_generator import ReportGenerator
from bot.citations import format_citation, add_freshness_indicator
import logging

logger = logging.getLogger(__name__)

class IdeaHandler:
    def __init__(self):
        self.report_generator = ReportGenerator()
    
    async def handle_idea(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Enhanced message handler with full analysis logic
        
        Acceptance Criteria:
            - FR-003: Idea analysis triggered
            - US-1: Progress indicator shown
            - US-4: Graceful error handling
        """
        try:
            message_text = update.message.text.strip()
            
            # Validate input
            if not message_text or len(message_text) < 5:
                await update.message.reply_text(
                    "❌ Пожалуйста, опишите вашу идею в 1-2 предложениях"
                )
                return
            
            # Detect mode
            mode, idea_text = detect_mode(message_text)
            
            if not idea_text:
                await update.message.reply_text(
                    "❌ Пожалуйста, укажите идею после режима. "
                    "Пример: РЕЖИМ: БИЗНЕС-ПЛАН Производство посуды"
                )
                return
            
            # Show initial progress
            progress_msg = await update.message.reply_text("⏳ Анализирую вашу идею...")
            
            # Update progress callback
            async def progress_callback(text: str):
                try:
                    await progress_msg.edit_text(text)
                except:
                    pass  # Message might have been deleted
            
            # Generate report
            try:
                report_messages = await self.report_generator.generate_report(
                    idea_text, 
                    mode or "ОЦЕНКА", 
                    progress_callback
                )
                
                # Send report
                for i, message in enumerate(report_messages):
                    if i == 0:
                        # Add mode info to first message
                        if mode:
                            message = f"🎯 Режим: {mode} - {get_mode_description(mode)}\n\n{message}"
                        else:
                            message = f"🎯 Режим: ОЦЕНКА (по умолчанию)\n\n{message}"
                    
                    await update.message.reply_text(
                        message,
                        parse_mode='Markdown',
                        disable_web_page_preview=False
                    )
                
                # Add share button
                share_button = InlineKeyboardButton(
                    "📤 Поделиться",
                    url=f"t.me/share/url?url=https://t.me/ideaplanneragent_bot&text=Посмотри+этот+анализ+идеи!"
                )
                keyboard = InlineKeyboardMarkup([[share_button]])
                
                await update.message.reply_text(
                    "💡 Надеюсь, этот анализ был полезен! Вы можете:",
                    reply_markup=keyboard
                )
                
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                await progress_msg.edit_text(
                    "⚠️ Не удалось сгенерировать полный отчет. "
                    "Вот что удалось получить:"
                )
                # TODO: Send partial results
                
        except Exception as e:
            logger.error(f"Error in idea handler: {e}")
            await update.message.reply_text(
                "⚠️ Произошла ошибка при обработке вашей идеи. "
                "Пожалуйста, попробуйте позже."
            )
```

### Error Handling Enhancements

```python
# bot/error_handling.py
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def enhanced_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Enhanced error handling with user feedback
    
    Acceptance Criteria:
        - US-4: Graceful degradation
        - NFR-003: Structured logging
    """
    error = context.error
    
    # Log detailed error information
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": str(context)
    }
    
    logger.error(f"Bot error: {error_data}", exc_info=True)
    
    # User-friendly error messages
    if isinstance(update, Update):
        if "rate limit" in str(error).lower():
            await update.message.reply_text(
                "⏳ Превышен лимит запросов. Пожалуйста, подождите 1 минуту и попробуйте снова."
            )
        elif "timeout" in str(error).lower():
            await update.message.reply_text(
                "⏱️ Сервис временно недоступен. Попробуйте через несколько минут."
            )
        else:
            await update.message.reply_text(
                "⚠️ Произошла техническая ошибка. "
                "Наша команда уже работает над решением."
            )
            
        # Offer retry option
        retry_button = InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry")
        keyboard = InlineKeyboardMarkup([[retry_button]])
        await update.message.reply_text("Вы можете:", reply_markup=keyboard)
```

---

## Success Criteria

- [ ] All 11 analysis modes implemented and functional
- [ ] 7-section reports generated correctly for all modes
- [ ] Citation formatting matches constitution requirements
- [ ] Data freshness indicators working properly
- [ ] Message splitting handles long reports gracefully
- [ ] Error handling provides useful feedback to users
- [ ] Progress indicators update appropriately during analysis
- [ ] Bot ready for LLM integration and mode-specific enhancements

---

## Next Tasks

- [ ] Task 007: LLM Integration (extends bot functionality)
- [ ] Task 008: Mode Analysis (enhances mode-specific features)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1 (All principles)
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (FR-004..FR-007, US-1..US-5)
- **Plan**: `plan.md` Phase 2.2
- **Architecture**: `architecture-decisions.md` Telegram Bot section