import logging
import logging.config
from typing import Optional
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os

# Import local modules
from src.config import settings
from src.database import init_db, get_db, SessionLocal
from src.handlers import start_handler, help_handler, idea_handler, market_search_handler, error_handler
from src.ru_search.aggregator import MarketDataAggregator

# Configure structured logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "level": "INFO"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO"
    },
    "loggers": {
        "telegram": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["console"]
        },
        "bot": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["console"]
        },
        "ru_search": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["console"]
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("bot")

class TelegramBot:
    """
    Main Telegram Bot class handling initialization, webhook setup, and lifecycle management.
    """
    
    def __init__(self):
        """
        Initialize the Telegram bot with configuration and database integration.
        """
        self.settings = settings
        self.bot_token = self.settings.TELEGRAM_TOKEN
        self.webhook_url = f"https://{os.getenv('DOMAIN', 'localhost')}/telegram/webhook"
        self.app = None
        self.webhook_server = None
        self.fastapi_app = FastAPI()
        self.market_aggregator = None
         
        # Initialize database
        init_db()
        logger.info("Database initialized")
         
        # Initialize MarketDataAggregator with config settings
        self._initialize_market_aggregator()
         
        # Setup FastAPI routes
        self._setup_fastapi_routes()
         
        logger.info(f"Telegram Bot initialized with token: {self.bot_token[:5]}...")
        
        # Initialize ru_search logger
        self.ru_search_logger = logging.getLogger("ru_search")
    
    def _initialize_market_aggregator(self):
        """
        Initialize the MarketDataAggregator with configuration settings.
        """
        try:
            # Use CACHE_TTL from config settings
            cache_ttl = self.settings.CACHE_TTL
            self.market_aggregator = MarketDataAggregator(cache_ttl=cache_ttl)
            logger.info(f"MarketDataAggregator initialized with cache TTL: {cache_ttl} seconds")
        except Exception as e:
            logger.error(f"Failed to initialize MarketDataAggregator: {e}")
            self.market_aggregator = None
    
    def _setup_fastapi_routes(self):
        """
        Setup FastAPI routes for webhook handling.
        """
        @self.fastapi_app.post("/telegram/webhook")
        async def webhook_handler(request: Request):
            """
            Handle incoming Telegram webhook requests.
            """
            try:
                # Get JSON data from request
                data = await request.json()
                logger.info(f"Received webhook data: {data}")
                
                # Create update object from webhook data
                update = Update.de_json(data, None)
                
                # Process update using the application
                if self.app:
                    await self.app.process_update(update)
                
                return JSONResponse(content={"status": "ok"})
                
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/health")
        async def health_check():
            """
            Health check endpoint.
            """
            return JSONResponse(content={"status": "healthy"})
    
    def build_application(self) -> Application:
        """
        Build and configure the Telegram Application instance.
         
        Returns:
            Application: Configured Telegram Application instance
        """
        # Build application with persistence and configuration
        app = (
            ApplicationBuilder()
            .token(self.bot_token)
            .http_version("1.1")
            .get_updates_http_version("1.1")
            .build()
        )
         
        # Add handlers from handlers module
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("market", market_search_handler))
        app.add_handler(CommandHandler("search", market_search_handler))
        app.add_handler(CommandHandler("analyze", market_search_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, idea_handler))
         
        # Add error handler
        app.add_error_handler(error_handler)
        
        # Add market_aggregator to bot_data for access in handlers
        app.bot_data['market_aggregator'] = self.market_aggregator
         
        return app
    
    
    def setup_webhook(self):
        """
        Setup Telegram webhook for the bot.
        
        Returns:
            bool: True if webhook setup was successful, False otherwise
        """
        try:
            if not self.app:
                self.app = self.build_application()
            
            # Set webhook using the application
            webhook_url = f"https://{os.getenv('DOMAIN', 'your-domain.com')}/telegram/webhook"
            
            # Remove any existing webhook first
            self.app.bot.delete_webhook()
            
            # Set new webhook
            result = self.app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            if result:
                logger.info(f"Webhook successfully set to: {webhook_url}")
                return True
            else:
                logger.error("Failed to set webhook")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            return False
    
    def remove_webhook(self):
        """
        Remove the Telegram webhook.
        
        Returns:
            bool: True if webhook removal was successful, False otherwise
        """
        try:
            if self.app:
                result = self.app.bot.delete_webhook()
                if result:
                    logger.info("Webhook successfully removed")
                    return True
                else:
                    logger.error("Failed to remove webhook")
                    return False
            return False
        except Exception as e:
            logger.error(f"Error removing webhook: {e}")
            return False
    
    def start_polling(self):
        """
        Start the bot using polling (for development/testing).
        """
        if not self.app:
            self.app = self.build_application()
        
        logger.info("Starting bot in polling mode...")
        self.app.run_polling()
    
    def start_webhook_server(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Start the bot using webhook mode with FastAPI server.
        
        Args:
            host: Host address to bind the server
            port: Port to listen on
        """
        if not self.app:
            self.app = self.build_application()
        
        # Setup webhook first
        if not self.setup_webhook():
            logger.error("Failed to setup webhook, cannot start webhook server")
            return
        
        logger.info(f"Starting FastAPI server on {host}:{port}")
        uvicorn.run(self.fastapi_app, host=host, port=port)
    
    def shutdown(self):
        """
        Gracefully shutdown the bot and clean up resources.
        """
        logger.info("Shutting down bot...")
         
        # Clean up MarketDataAggregator
        if self.market_aggregator:
            try:
                self.market_aggregator.close()
                logger.info("MarketDataAggregator closed")
            except Exception as e:
                logger.error(f"Error closing MarketDataAggregator: {e}")
         
        # Remove webhook
        self.remove_webhook()
         
        # Close database sessions
        try:
            SessionLocal.remove()
            logger.info("Database sessions closed")
        except Exception as e:
            logger.error(f"Error closing database sessions: {e}")
         
        # Stop application
        if self.app:
            if hasattr(self.app, 'shutdown'):
                self.app.shutdown()
            if hasattr(self.app, 'stop'):
                self.app.stop()
            logger.info("Telegram application stopped")
         
        logger.info("Bot shutdown complete")
    
    def __enter__(self):
        """
        Context manager entry point.
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point - ensures proper cleanup.
        """
        self.shutdown()

# Global bot instance for easy access
bot = TelegramBot()

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "polling":
        bot.start_polling()
    elif len(sys.argv) > 1 and sys.argv[1] == "webhook":
        bot.start_webhook_server()
    else:
        print("Usage:")
        print("  python src/bot.py polling  - Start bot in polling mode")
        print("  python src/bot.py webhook   - Start bot in webhook mode")