import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional
import time

# Import local modules
from src.database import SessionLocal, UserCRUD, IdeaCRUD, AnalysisCRUD, AnalysisMode
from src.config import settings
from src.ru_search.aggregator import MarketDataAggregator

# Configure logger
logger = logging.getLogger("bot")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command with Russian welcome message and mode explanation.
    """
    try:
        # Get user info
        user = update.effective_user
        telegram_id = str(user.id)
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        language_code = user.language_code
        
        # Create or update user in database
        db = SessionLocal()
        try:
            existing_user = UserCRUD.get_user_by_telegram_id(db, telegram_id)
            if not existing_user:
                UserCRUD.create_user(
                    db=db,
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code
                )
                logger.info(f"New user created: {telegram_id}")
            else:
                # Update user info if changed
                UserCRUD.update_user(
                    db=db,
                    user_id=existing_user.id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code
                )
                logger.info(f"User updated: {telegram_id}")
        finally:
            db.close()
        
        # Russian welcome message with mode explanation
        welcome_message = (
            "🌟 Добро пожаловать в Idea Planner Bot! 🌟\n\n"
            "Этот бот поможет вам анализировать и развивать ваши бизнес-идеи.\n\n"
            "📋 Доступные режимы анализа:\n"
            "• ОЦЕНКА - Быстрая оценка идеи\n"
            "• БИЗНЕС-ПЛАН - Разработка бизнес-плана\n"
            "• МАРКЕТИНГ - Маркетинговый анализ\n"
            "• ИСПОЛНЕНИЕ - План реализации\n"
            "• САЙТ - Разработка веб-сайта\n"
            "• ОТЧЁТ 1, ОТЧЁТ 2, ОТЧЁТ 3 - Различные типы отчетов\n"
            "• ПОЧЕМУ_СЕЙЧАС - Анализ актуальности\n"
            "• РЫНОЧНЫЙ_РАЗРЫВ - Анализ рыночных возможностей\n"
            "• ДОКАЗАТЕЛЬСТВА - Сбор доказательств концепции\n\n"
            "🔍 Поиск по российскому рынку:\n"
            "• Используйте /market <запрос> для поиска товаров\n"
            "• Пример: /market смартфоны\n"
            "• Поддерживаются Wildberries, Ozon и Yandex Market\n\n"
            "Просто отправьте вашу идею текстом, и я начну анализ!"
        )
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"User {telegram_id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in start_handler for user {update.effective_user.id}: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command with Russian help message.
    """
    try:
        help_message = (
            "🆘 Справка по Idea Planner Bot 🆘\n\n"
            "📝 Как использовать бота:\n"
            "1. Отправьте /start для начала работы\n"
            "2. Просто отправьте вашу бизнес-идею текстом\n"
            "3. Бот сохранит вашу идею и начнет анализ\n"
            "4. Вы получите уведомление о прогрессе\n\n"
            "🔍 Функции поиска по рынку:\n"
            "• /market <запрос> - Поиск товаров на российских площадках\n"
            "• /search <запрос> - Альтернативная команда поиска\n"
            "• /analyze <запрос> - Анализ рынка по запросу\n"
            "Пример: /market смартфоны\n\n"
            "💡 Советы:\n"
            "• Описывайте идеи как можно подробнее\n"
            "• Указывайте целевую аудиторию и рынок\n"
            "• Можете отправлять несколько идей\n"
            "• Используйте /help для вызова этой справки\n\n"
            "🔧 Техническая поддержка:\n"
            "Если у вас возникли проблемы, обратитесь к администратору."
        )
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"User {update.effective_user.id} requested help")
        
    except Exception as e:
        logger.error(f"Error in help_handler for user {update.effective_user.id}: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении справки. Пожалуйста, попробуйте позже.")

async def idea_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Message handler that accepts any text as idea, shows progress indicator,
    stores idea in database, and provides placeholder response.
    """
    try:
        # Get user and idea text
        user = update.effective_user
        idea_text = update.message.text
        telegram_id = str(user.id)
        
        if not idea_text or idea_text.strip() == "":
            await update.message.reply_text("⚠️ Пожалуйста, отправьте непустое сообщение с вашей идеей.")
            return
        
        # Show progress indicator
        progress_message = await update.message.reply_text("⏳ Обработка вашей идеи... Пожалуйста, подождите.")
        
        # Create or update user in database
        db = SessionLocal()
        try:
            # Get or create user
            existing_user = UserCRUD.get_user_by_telegram_id(db, telegram_id)
            if not existing_user:
                UserCRUD.create_user(
                    db=db,
                    telegram_id=telegram_id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language_code=user.language_code
                )
                logger.info(f"New user created for idea: {telegram_id}")
            else:
                # Update user info if needed
                UserCRUD.update_user(
                    db=db,
                    user_id=existing_user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language_code=user.language_code
                )
            
            # Get user id
            user_db = UserCRUD.get_user_by_telegram_id(db, telegram_id)
            user_id = user_db.id
            
            # Store idea in database
            idea = IdeaCRUD.create_idea(
                db=db,
                user_id=user_id,
                text=idea_text,
                mode=AnalysisMode.EVALUATION  # Default mode
            )
            
            logger.info(f"Idea stored successfully: {idea.id} for user {user_id}")
            
            # Simulate processing time
            time.sleep(2)
            
            # Update progress message
            await progress_message.edit_text("✅ Ваша идея сохранена! Начинаю анализ...")
            
            # Create analysis record
            analysis = AnalysisCRUD.create_analysis(
                db=db,
                idea_id=idea.id,
                user_id=user_id
            )
            
            logger.info(f"Analysis created: {analysis.id} for idea {idea.id}")
            
            # Final response
            response_message = (
                f"🎉 Спасибо за вашу идею! 🎉\n\n"
                f"📝 Ваша идея: \"{idea_text}\"\n\n"
                f"🔍 Мы начали анализ в режиме: {analysis.idea.mode.value}\n"
                f"⏳ Статус: {analysis.status.value}\n\n"
                f"💡 Вы получите уведомление, когда анализ будет завершен.\n"
                f"Можете отправлять другие идеи или использовать /help для справки."
            )
            
            await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in idea_handler for user {update.effective_user.id}: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке вашей идеи. Пожалуйста, попробуйте позже.")

async def market_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle market search commands for Russian market analysis.
    Supports commands like /market, /search, /analyze.
    """
    try:
        # Get user info
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Get ru_search logger
        ru_search_logger = logging.getLogger("ru_search")
        
        # Get the query from the command arguments
        query_text = " ".join(context.args) if context.args else None
        
        if not query_text or query_text.strip() == "":
            help_message = (
                "🔍 Поиск по рынку России 🔍\n\n"
                "Использование: /market <запрос>\n"
                "Пример: /market смартфоны\n"
                "Это выполнит поиск по Wildberries, Ozon и Yandex Market"
            )
            await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
            ru_search_logger.info(f"User {telegram_id} requested market search help")
            return
        
        # Show progress indicator
        progress_message = await update.message.reply_text("⏳ Выполняю поиск по рынку... Это может занять несколько секунд.")
        
        # Get market aggregator from bot_data
        market_aggregator = context.bot_data.get('market_aggregator')
        
        # Check if market aggregator is available
        if not market_aggregator:
            await progress_message.edit_text("❌ Ошибка: Сервис поиска по рынку временно недоступен.")
            ru_search_logger.error(f"Market aggregator not available for user {telegram_id}")
            return
         
        # Perform market search
        try:
            ru_search_logger.info(f"Starting market search for user {telegram_id}: {query_text}")
            
            # Use the market aggregator to search
            search_results = await market_aggregator.search(
                query=query_text,
                sources=["wildberries", "ozon", "yandex"],
                use_cache=True,
                timeout=90
            )
            
            ru_search_logger.info(f"Market search completed for user {telegram_id}: {query_text}")
            
            # Format the results
            summary = search_results.get('summary', {})
            source_results = search_results.get('source_results', {})
            errors = search_results.get('errors', [])
            
            # Log summary statistics
            ru_search_logger.info(f"Search summary for '{query_text}': {summary.get('total_products', 0)} products, avg price: {summary.get('average_price', 0):.2f} ₽")
            
            # Prepare response message
            response_lines = []
            response_lines.append(f"📊 Результаты поиска по запросу: *{query_text}*")
            response_lines.append(f"🕒 Время выполнения: {summary.get('execution_time', 0):.2f} секунд")
            response_lines.append("")
            
            # Add summary statistics
            response_lines.append("📈 Статистика:")
            response_lines.append(f"• Всего товаров: {summary.get('total_products', 0)}")
            response_lines.append(f"• Уникальных товаров: {summary.get('unique_products', 0)}")
            response_lines.append(f"• Средняя цена: {summary.get('average_price', 0):.2f} ₽")
            response_lines.append(f"• Диапазон цен: {summary.get('price_range', 'N/A')}")
            response_lines.append("")
            
            # Add source-specific results
            response_lines.append("🛒 Результаты по источникам:")
            for source_name, source_data in source_results.items():
                products = source_data.get('products', [])
                cache_hit = source_data.get('cache_hit', False)
                count = source_data.get('count', 0)
                
                cache_status = "🔄 (из кеша)" if cache_hit else "🔍 (новый поиск)"
                response_lines.append(f"• {source_name.capitalize()}: {count} товаров {cache_status}")
                ru_search_logger.info(f"Source {source_name}: {count} products, cache_hit: {cache_hit}")
            
            # Add error information if any
            if errors:
                response_lines.append("")
                response_lines.append("⚠️ Ошибки:")
                for error in errors:
                    response_lines.append(f"• {error.get('source', 'Unknown')}: {error.get('error', 'Unknown error')}")
                    ru_search_logger.warning(f"Search error for {error.get('source', 'Unknown')}: {error.get('error', 'Unknown error')}")
            
            # Send the response
            response_message = "\n".join(response_lines)
            await progress_message.edit_text(response_message, parse_mode=ParseMode.MARKDOWN)
            
            ru_search_logger.info(f"Market search results sent to user {telegram_id}")
            
        except Exception as search_error:
            ru_search_logger.error(f"Market search failed for user {telegram_id}: {search_error}")
            await progress_message.edit_text(f"❌ Ошибка при поиске по рынку: {str(search_error)}")
            
    except Exception as e:
        ru_search_logger.error(f"Error in market_search_handler for user {update.effective_user.id}: {e}")
        await update.message.reply_text("❌ Произошла ошибка при поиске по рынку. Пожалуйста, попробуйте позже.")


async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE, error):
    """
    Global error handler with graceful error messages and logging.
    """
    try:
        # Log the error with structured format
        logger.error(f"Error occurred: {error}")
        logger.error(f"Update context: {update}")
         
        # Extract user info if available
        user_id = "unknown"
        if update and update.effective_user:
            user_id = update.effective_user.id
            logger.error(f"Error for user {user_id}")
         
        # Send graceful error message to user if it's a message update
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Извините, произошла ошибка. Мы уже работаем над её исправлением.\n"
                    "Пожалуйста, попробуйте позже или обратитесь к администратору."
                )
            except Exception as reply_error:
                logger.error(f"Failed to send error reply to user {user_id}: {reply_error}")
         
        # Additional error details logging
        if hasattr(error, 'message'):
            logger.error(f"Error message: {error.message}")
        if hasattr(error, 'code'):
            logger.error(f"Error code: {error.code}")
             
    except Exception as handler_error:
        # Fallback error handling to prevent infinite loops
        logger.error(f"Critical error in error_handler: {handler_error}")
        logger.error(f"Original error was: {error}")