import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional
import time

# Import local modules
from src.database import SessionLocal, UserCRUD, IdeaCRUD, AnalysisCRUD, AnalysisMode
from src.config import settings

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