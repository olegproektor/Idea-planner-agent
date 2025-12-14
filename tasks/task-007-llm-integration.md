# Task 007: LLM Integration

**Phase**: 3 - Analysis Engine  
**Estimated Hours**: 5  
**Priority**: P2  
**Status**: Not Started

---

## Description

Integrate Large Language Model (LLM) functionality into the idea-planner-agent for advanced analysis capabilities. This task implements the abstract LLM provider interface and integrates it with the Telegram bot.

---

## Acceptance Criteria

- [ ] Abstract `LLMProvider` interface implemented (FR-008)
- [ ] `GroqProvider` implementation working with Llama-3.3-70b (Architecture Decision)
- [ ] Provider configuration system functional (FR-008)
- [ ] Fallback mechanism for LLM failures implemented (Resilience VII)
- [ ] LLM response validation layer working (Engineering Quality VI)
- [ ] Integration with Telegram bot completed
- [ ] All LLM operations respect ethical guidelines (Ethics VIII)

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 7.1 Design LLM interface | 1.0 | Create abstract LLMProvider interface |
| 7.2 Implement Groq provider | 2.0 | Groq API integration with Llama-3.3-70b |
| 7.3 Add configuration system | 0.5 | Provider selection and configuration |
| 7.4 Implement fallback mechanism | 1.0 | Graceful degradation on failures |
| 7.5 Add validation layer | 0.5 | Response validation and error handling |

---

## Dependencies

**Depends on**: 
- Task 003 (Configuration System) - for API keys and settings
- Task 006 (Telegram Bot Logic) - for integration points

**Required for**: 
- Task 008 (Mode Analysis) - uses LLM for advanced analysis

---

## Testing Requirements

- [ ] Verify LLM interface works with multiple providers
- [ ] Test Groq provider handles API errors gracefully
- [ ] Confirm configuration system switches providers correctly
- [ ] Validate fallback mechanism works on LLM failures
- [ ] Test response validation catches invalid outputs
- [ ] Verify integration with Telegram bot works smoothly

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| LLM interface | Engineering Quality (VI) | FR-008 |
| Groq provider | Reality-First (III) | Architecture Decision |
| Configuration | Traceability (II) | FR-008 |
| Fallback mechanism | Resilience (VII) | US-4 |
| Validation layer | Ethics (VIII) | AC-4 |

---

## Implementation Notes

### Abstract LLM Provider Interface

```python
# llm/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel

class LLMRequest(BaseModel):
    """Standardized LLM request format"""
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1024
    system_message: Optional[str] = None
    context: Optional[Dict] = None

class LLMResponse(BaseModel):
    """Standardized LLM response format"""
    content: str
    usage: Dict[str, int]
    model: str
    provider: str
    raw_response: Optional[Dict] = None

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def __init__(self, api_key: str, model: str = "default"):
        """Initialize provider with API key"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
        retry: int = 3
    ) -> LLMResponse:
        """
        Generate response from LLM
        
        Args:
            request: LLMRequest with prompt and parameters
            retry: Number of retry attempts
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMError: If generation fails after retries
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: LLMResponse) -> bool:
        """
        Validate LLM response for quality and safety
        
        Args:
            response: LLMResponse to validate
            
        Returns:
            bool: True if response is valid
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict:
        """
        Return provider capabilities
        
        Returns:
            Dict with max_tokens, models, etc.
        """
        pass

class LLMError(Exception):
    """Custom exception for LLM errors"""
    pass
```

### Groq Provider Implementation

```python
# llm/providers/groq.py
import os
import asyncio
from typing import Dict, Optional
from groq import AsyncGroq
from .base import LLMProvider, LLMRequest, LLMResponse, LLMError

class GroqProvider(LLMProvider):
    """Groq API provider implementation"""
    
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b"):
        """
        Initialize Groq provider
        
        Args:
            api_key: Groq API key
            model: Model name (default: llama-3.3-70b)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
        self.model = model
        self.client = AsyncGroq(api_key=self.api_key)
        
        if not self.api_key:
            raise ValueError("Groq API key is required")
    
    async def generate(
        self,
        request: LLMRequest,
        retry: int = 3
    ) -> LLMResponse:
        """
        Generate response using Groq API
        
        Acceptance Criteria:
            - FR-008: Configurable LLM provider
            - Resilience VII: Retry mechanism
        """
        last_error = None
        
        for attempt in range(retry):
            try:
                # Prepare messages
                messages = []
                if request.system_message:
                    messages.append({"role": "system", "content": request.system_message})
                messages.append({"role": "user", "content": request.prompt})
                
                # Make API call
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                
                # Create standardized response
                llm_response = LLMResponse(
                    content=response.choices[0].message.content,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    model=self.model,
                    provider="groq",
                    raw_response=response.model_dump()
                )
                
                # Validate response
                if not self.validate_response(llm_response):
                    raise LLMError("Invalid LLM response")
                
                return llm_response
                
            except Exception as e:
                last_error = e
                if attempt < retry - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        raise LLMError(f"Failed after {retry} attempts: {str(last_error)}")
    
    def validate_response(self, response: LLMResponse) -> bool:
        """
        Validate Groq response
        
        Acceptance Criteria:
            - AC-4: Data accuracy validation
            - Ethics VIII: Content safety
        """
        # Check for empty response
        if not response.content or len(response.content.strip()) < 10:
            return False
        
        # Check for inappropriate content (basic check)
        inappropriate_terms = ["error", "cannot", "unable", "sorry"]
        if any(term in response.content.lower() for term in inappropriate_terms):
            return False
        
        return True
    
    def get_capabilities(self) -> Dict:
        """Return Groq provider capabilities"""
        return {
            "max_tokens": 8192,
            "models": ["llama-3.3-70b", "llama-3.1-70b", "llama-3.1-8b"],
            "concurrent_requests": 10,
            "supports_streaming": True
        }
```

### LLM Provider Factory

```python
# llm/factory.py
from typing import Dict, Type
from .providers.base import LLMProvider
from .providers.groq import GroqProvider

class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    PROVIDERS: Dict[str, Type[LLMProvider]] = {
        "groq": GroqProvider,
        # Add other providers here
    }
    
    @staticmethod
    def create_provider(
        provider_name: str,
        api_key: str = None,
        model: str = None
    ) -> LLMProvider:
        """
        Create LLM provider instance
        
        Args:
            provider_name: Name of provider (groq, etc.)
            api_key: API key for provider
            model: Specific model to use
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider not supported
        """
        provider_class = LLMProviderFactory.PROVIDERS.get(provider_name.lower())
        
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        return provider_class(api_key=api_key, model=model)
```

### LLM Integration with Telegram Bot

```python
# bot/llm_integration.py
from llm.factory import LLMProviderFactory
from llm.providers.base import LLMRequest, LLMResponse, LLMError
from config import config
import logging

logger = logging.getLogger(__name__)

class LLMIntegration:
    """LLM integration for Telegram bot"""
    
    def __init__(self):
        self.provider = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize LLM provider from config"""
        try:
            self.provider = LLMProviderFactory.create_provider(
                provider_name=config.LLM_PROVIDER,
                api_key=config.LLM_API_KEY,
                model=config.LLM_MODEL
            )
            logger.info(f"Initialized LLM provider: {config.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            self.provider = None
    
    async def generate_analysis(
        self,
        idea: str,
        mode: str,
        context: dict = None
    ) -> str:
        """
        Generate analysis using LLM
        
        Args:
            idea: Business idea text
            mode: Analysis mode
            context: Additional context data
            
        Returns:
            Generated analysis text
            
        Acceptance Criteria:
            - FR-008: LLM integration working
            - Resilience VII: Fallback on failure
        """
        if not self.provider:
            logger.warning("No LLM provider available, using fallback")
            return self._fallback_analysis(idea, mode)
        
        try:
            # Create mode-specific prompt
            prompt = self._create_prompt(idea, mode, context)
            
            # Create LLM request
            request = LLMRequest(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2048,
                system_message=self._get_system_message(mode)
            )
            
            # Generate response
            response = await self.provider.generate(request)
            
            # Validate response
            if not self._validate_llm_response(response):
                raise LLMError("Invalid LLM response")
            
            return response.content
            
        except LLMError as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_analysis(idea, mode)
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            return self._fallback_analysis(idea, mode)
    
    def _create_prompt(self, idea: str, mode: str, context: dict) -> str:
        """Create mode-specific prompt"""
        base_prompt = f"""
        Вы - эксперт по бизнес-анализу для российского рынка.
        Проанализируйте следующую бизнес-идею в режиме {mode}:
        
        Идея: {idea}
        
        Контекст:
        {context.get('market_data', 'Нет данных')}
        
        Требования:
        1. Ответ на русском языке
        2. Используйте формат Markdown
        3. Включите конкретные цифры и факты
        4. Укажите источники в формате [URL, DD.MM.YYYY HH:MM, "описание"]
        5. Разделите ответ на логические абзацы (максимум 3 предложения каждый)
        """
        
        # Add mode-specific instructions
        if mode == "БИЗНЕС-ПЛАН":
            base_prompt += "\n6. Сфокусируйтесь на финансовых показателях и инвестиционной привлекательности"
        elif mode == "МАРКЕТИНГ":
            base_prompt += "\n6. Уделите внимание целевой аудитории и каналам продвижения"
        # ... other modes
        
        return base_prompt
    
    def _get_system_message(self, mode: str) -> str:
        """Get system message for mode"""
        system_messages = {
            "ОЦЕНКА": "Вы - сбалансированный бизнес-аналитик",
            "БИЗНЕС-ПЛАН": "Вы - финансовый эксперт, готовите анализ для инвесторов",
            "МАРКЕТИНГ": "Вы - маркетинговый стратег",
            "ИСПОЛНЕНИЕ": "Вы - опытный проектный менеджер",
            "САЙТ": "Вы - веб-стратег и UX-специалист",
            "ОТЧЁТ 1": "Вы - аналитик данных, специалист по маркетплейсам",
            "ОТЧЁТ 2": "Вы - эксперт по операционному планированию",
            "ОТЧЁТ 3": "Вы - стратегический планировщик",
            "ПОЧЕМУ_СЕЙЧАС": "Вы - аналитик рыночных трендов",
            "РЫНОЧНЫЙ_РАЗРЫВ": "Вы - эксперт по конкурентному анализу",
            "ДОКАЗАТЕЛЬСТВА": "Вы - исследователь данных"
        }
        
        return system_messages.get(mode, "Вы - бизнес-аналитик")
    
    def _validate_llm_response(self, response: LLMResponse) -> bool:
        """Validate LLM response quality"""
        # Check minimum length
        if len(response.content.strip()) < 100:
            return False
        
        # Check for hallucination indicators
        hallucination_terms = ["не могу", "нет информации", "не знаю"]
        if any(term in response.content.lower() for term in hallucination_terms):
            return False
        
        return True
    
    def _fallback_analysis(self, idea: str, mode: str) -> str:
        """
        Fallback analysis when LLM unavailable
        
        Acceptance Criteria:
            - Resilience VII: Graceful degradation
        """
        logger.warning("Using fallback analysis for LLM")
        
        # Basic fallback response
        fallback = f"""
        📊 Базовый анализ идеи: {idea}
        
        **Режим:** {mode}
        
        ⚠️ Полный анализ временно недоступен. Вот основные моменты:
        
        1. **Потенциал идеи:** Средний
        2. **Целевая аудитория:** Потребители 25-45 лет
        3. **Конкуренция:** Высокая
        4. **Рекомендации:** Проведите дополнительное исследование рынка
        
        🔄 Попробуйте позже для полного анализа.
        """
        
        return fallback
```

### Integration with Report Generator

```python
# Update to bot/report_generator.py
from bot.llm_integration import LLMIntegration

class ReportGenerator:
    def __init__(self):
        self.data_cache = {}
        self.llm_integration = LLMIntegration()  # Add LLM integration
    
    async def generate_report(
        self,
        idea_text: str,
        mode: str = "ОЦЕНКА",
        progress_callback=None
    ) -> List[str]:
        """Updated to use LLM integration"""
        # ... existing code ...
        
        # Get market data
        search_results = search(idea_text, sources=["wb", "ozon", "yandex"])
        
        # Get LLM analysis for mode-specific sections
        llm_context = {
            'market_data': self._format_market_data(search_results),
            'mode': mode,
            'idea': idea_text
        }
        
        llm_analysis = await self.llm_integration.generate_analysis(
            idea_text, 
            mode, 
            llm_context
        )
        
        # Use LLM analysis for appropriate sections
        sections = []
        
        # Section 1: Use LLM for comprehensive analysis
        sections.append(self._generate_section_1_with_llm(idea_text, llm_analysis, mode))
        
        # ... other sections using LLM analysis where appropriate
        
        return self._split_for_telegram("\n\n".join(sections))
    
    def _generate_section_1_with_llm(self, idea: str, llm_analysis: str, mode: str) -> str:
        """Generate Section 1 using LLM analysis"""
        # Extract relevant parts from LLM analysis
        section = f"📋 КАРТОЧКА ИДЕИ (Анализ с использованием ИИ)\n\n"
        section += llm_analysis  # Use full LLM analysis for this section
        
        return section
```

---

## Success Criteria

- [ ] LLM provider interface implemented and working
- [ ] Groq provider successfully integrated with proper error handling
- [ ] Configuration system allows provider switching
- [ ] Fallback mechanism provides graceful degradation
- [ ] Response validation prevents low-quality outputs
- [ ] Integration with Telegram bot completed and tested
- [ ] All LLM operations respect ethical guidelines

---

## Next Tasks

- [ ] Task 008: Mode Analysis (depends on this LLM integration)

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1 (Ethics VIII, Resilience VII)
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (FR-008)
- **Plan**: `plan.md` Phase 3.1
- **Architecture**: `architecture-decisions.md` LLM Provider section