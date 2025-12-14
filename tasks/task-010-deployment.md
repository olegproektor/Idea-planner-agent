# Task 010: Deployment

**Phase**: 4 - Testing & Deployment  
**Estimated Hours**: 3  
**Priority**: P1  
**Status**: Not Started

---

## Description

Deploy the idea-planner-agent MVP to Railway.app and configure the production environment. This task includes setting up the webhook, configuring environment variables, and preparing the application for public use.

---

## Acceptance Criteria

- [ ] Railway.app project created and configured (Architecture Decision)
- [ ] Webhook URL set up: `https://{app_name}.railway.app/telegram/webhook` (Technical Notes)
- [ ] SSL certificate configured (Let's Encrypt) (Technical Notes)
- [ ] Production environment variables configured (FR-008)
- [ ] Webhook functionality tested and working (FR-001)
- [ ] Deployment documentation completed
- [ ] Monitoring and logging configured (NFR-003)

---

## Subtasks with Hour Estimates

| Subtask | Hours | Description |
|---------|-------|-------------|
| 10.1 Set up Railway project | 0.5 | Create Railway.app project and connect GitHub |
| 10.2 Configure environment | 1.0 | Set up production environment variables |
| 10.3 Deploy application | 0.5 | Deploy to Railway.app |
| 10.4 Set up webhook | 0.5 | Configure Telegram webhook |
| 10.5 Test deployment | 0.3 | Verify webhook and bot functionality |
| 10.2 Create documentation | 0.2 | Write deployment documentation |

---

## Dependencies

**Depends on**: 
- Task 009 (Testing) - all tests must pass before deployment
- All previous implementation tasks

**Required for**: Production launch

---

## Testing Requirements

- [ ] Verify Railway.app deployment successful
- [ ] Confirm webhook URL accessible and secure
- [ ] Test Telegram bot responds to commands
- [ ] Validate all modes work in production
- [ ] Check error handling in production environment
- [ ] Verify logging and monitoring working

---

## Traceability to Constitution Principles

| Subtask | Constitution Principle | Spec Reference |
|---------|-----------------------|----------------|
| Railway setup | Engineering Quality (VI) | Architecture Decision |
| Webhook configuration | Reality-First (III) | Technical Notes |
| Environment variables | Ethics (VIII) | FR-008 |
| SSL certificate | Traceability (II) | Technical Notes |
| Production testing | Resilience (VII) | NFR-003 |

---

## Implementation Notes

### Railway.app Deployment Guide

```markdown
# Railway.app Deployment Guide

## Prerequisites
- Railway.app account
- GitHub repository connected
- All tests passing
- Production-ready code

## Step 1: Create Railway Project

1. Go to [Railway.app](https://railway.app) and sign in
2. Click "New Project" -> "Deploy from GitHub repo"
3. Select your idea-planner-agent repository
4. Choose main branch for deployment

## Step 2: Configure Environment Variables

Add the following environment variables in Railway dashboard:

### Telegram Configuration
- `TELEGRAM_TOKEN`: Your Telegram bot token from @BotFather
- `TELEGRAM_WEBHOOK_URL`: `https://your-app-name.up.railway.app/telegram/webhook`
- `TELEGRAM_WEBHOOK_SECRET`: Generate a random secret (e.g., `openssl rand -hex 16`)

### LLM Configuration
- `LLM_PROVIDER`: `groq`
- `LLM_API_KEY`: Your Groq API key
- `LLM_MODEL`: `llama-3.3-70b`

### Database Configuration
- `DATABASE_URL`: `sqlite:///bot.db` (default)
- `DATABASE_ECHO`: `False`

### Caching Configuration
- `CACHE_TTL`: `21600` (6 hours)
- `CACHE_MAXSIZE`: `1000`

### Production Configuration
- `DEVELOPMENT_MODE`: `False`
- `LOG_LEVEL`: `INFO`
- `LOG_FORMAT`: `json`

## Step 3: Configure Deployment Settings

1. Set build command: `pip install -r requirements.txt`
2. Set start command: `python main.py`
3. Enable automatic deployments for main branch
4. Set environment: Python 3.11

## Step 4: Deploy Application

1. Click "Deploy" button
2. Monitor deployment logs
3. Wait for successful deployment (green checkmark)

## Step 5: Set Up Telegram Webhook

After deployment:

1. Get your Railway.app URL (e.g., `https://your-app-name.up.railway.app`)
2. Set webhook using Telegram API:

```bash
curl -X POST \
  "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app-name.up.railway.app/telegram/webhook", "secret_token": "${TELEGRAM_WEBHOOK_SECRET}"}'
```

3. Verify webhook set correctly:

```bash
curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo"
```

## Step 6: Test Deployment

1. Send `/start` command to your bot
2. Verify bot responds correctly
3. Test basic idea analysis
4. Test all analysis modes
5. Verify error handling works

## Step 7: Set Up Monitoring

1. Configure Railway.app alerts for:
   - Application crashes
   - High memory usage
   - Failed deployments

2. Set up logging:
   - View logs in Railway dashboard
   - Configure log retention (30 days recommended)

## Step 8: Configure Custom Domain (Optional)

1. Add custom domain in Railway dashboard
2. Configure DNS records with your domain provider
3. Set up SSL certificate (automatic with Railway)
4. Update Telegram webhook URL if domain changes

## Troubleshooting

### Webhook Not Working
- Check Railway logs for errors
- Verify webhook URL is correct
- Test webhook manually with curl
- Check SSL certificate is valid

### Bot Not Responding
- Check Telegram token is correct
- Verify webhook is set properly
- Test with simple `/start` command
- Check application logs

### Deployment Failed
- Check build logs for errors
- Verify requirements.txt is complete
- Test locally before redeploying
- Check Python version compatibility

## Production Checklist

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Webhook set and verified
- [ ] SSL certificate valid
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Documentation updated
- [ ] Team notified of deployment
```

### Deployment Configuration Files

```python
# config/production.py
from config import Config

class ProductionConfig(Config):
    """Production-specific configuration"""
    
    DEVELOPMENT_MODE = False
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "json"
    
    # Production-specific settings
    DATABASE_ECHO = False
    CACHE_TTL = 21600  # 6 hours
    CACHE_MAXSIZE = 1000

# Override default config in production
if not Config.DEVELOPMENT_MODE:
    config = ProductionConfig()
```

### Webhook Setup Script

```python
# scripts/setup_webhook.py
import os
import requests
from config import config

def setup_telegram_webhook():
    """Set up Telegram webhook"""
    webhook_url = config.TELEGRAM_WEBHOOK_URL
    secret_token = config.TELEGRAM_WEBHOOK_SECRET
    
    # Set webhook
    response = requests.post(
        f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/setWebhook",
        json={
            "url": webhook_url,
            "secret_token": secret_token,
            "max_connections": 100,
            "allowed_updates": ["message", "callback_query"]
        }
    )
    
    if response.json().get("ok"):
        print(f"✅ Webhook set successfully: {webhook_url}")
        return True
    else:
        print(f"❌ Failed to set webhook: {response.text}")
        return False

def verify_webhook():
    """Verify webhook configuration"""
    response = requests.get(
        f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getWebhookInfo"
    )
    
    info = response.json().get("result", {})
    print(f"Webhook URL: {info.get('url', 'Not set')}")
    print(f"Pending updates: {info.get('pending_update_count', 0)}")
    print(f"Last error: {info.get('last_error_message', 'None')}")
    
    return info.get("url") == config.TELEGRAM_WEBHOOK_URL

if __name__ == "__main__":
    print("Setting up Telegram webhook...")
    
    if setup_telegram_webhook():
        print("Verifying webhook...")
        if verify_webhook():
            print("✅ Webhook setup complete!")
        else:
            print("⚠️ Webhook verification failed")
    else:
        print("❌ Webhook setup failed")
```

### Production Monitoring Setup

```python
# monitoring/setup_monitoring.py
import logging
from config import config

def setup_production_logging():
    """Set up production logging configuration"""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime) %(levelname) %(name) %(message) %(filename) %(lineno)"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": config.LOG_LEVEL
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/bot.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": config.LOG_LEVEL
            }
        },
        "root": {
            "handlers": ["console", "file"],
            "level": config.LOG_LEVEL
        }
    }
    
    import logging.config
    logging.config.dictConfig(logging_config)
    
    logger = logging.getLogger(__name__)
    logger.info("Production logging configured")
    
    return logger

def setup_error_tracking():
    """Set up error tracking (would integrate with Sentry, etc.)"""
    # In production, this would integrate with error tracking services
    # For MVP, we'll use basic logging
    
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        logger = logging.getLogger("exception")
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
    logging.getLogger("exception").info("Exception handling configured")

if __name__ == "__main__":
    setup_production_logging()
    setup_error_tracking()
    print("✅ Production monitoring configured")
```

### Deployment Verification Script

```python
# scripts/verify_deployment.py
import os
import requests
import json
from config import config

def verify_deployment():
    """Verify deployment health"""
    
    print("🔍 Verifying deployment...")
    
    # Check environment
    print(f"Environment: {'Production' if not config.DEVELOPMENT_MODE else 'Development'}")
    print(f"Telegram Token: {'Set' if config.TELEGRAM_TOKEN else 'Not set'}")
    print(f"LLM Provider: {config.LLM_PROVIDER}")
    
    # Test webhook (if in production)
    if not config.DEVELOPMENT_MODE:
        try:
            # Test webhook URL
            webhook_url = config.TELEGRAM_WEBHOOK_URL
            print(f"Testing webhook: {webhook_url}")
            
            # Simple GET request to test connectivity
            response = requests.get(webhook_url, timeout=10)
            print(f"Webhook status: {response.status_code}")
            
            if response.status_code == 405:  # Method Not Allowed (expected for webhook)
                print("✅ Webhook endpoint accessible")
            else:
                print(f"⚠️ Unexpected webhook response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Webhook test failed: {e}")
    
    # Test Telegram bot
    try:
        print("Testing Telegram bot...")
        
        # Get bot info
        response = requests.get(
            f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
        )
        
        if response.json().get("ok"):
            bot_info = response.json()["result"]
            print(f"✅ Bot connected: @{bot_info['username']}")
            print(f"Bot name: {bot_info['first_name']}")
        else:
            print(f"❌ Telegram bot connection failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Telegram bot test failed: {e}")
    
    # Test database
    try:
        print("Testing database...")
        from database import initialize_database, Session
        
        # Test database connection
        session = Session()
        session.execute("SELECT 1")
        session.close()
        
        print("✅ Database connection working")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    print("📋 Deployment verification complete!")

if __name__ == "__main__":
    verify_deployment()
```

---

## Success Criteria

- [ ] Railway.app project created and configured
- [ ] Webhook URL set up and working
- [ ] SSL certificate configured and valid
- [ ] Production environment variables configured
- [ ] Telegram bot responding to commands
- [ ] All analysis modes working in production
- [ ] Monitoring and logging configured
- [ ] Deployment documentation completed

---

## Next Tasks

- Production launch
- User testing and feedback collection
- Monitoring and maintenance
- Planning for v1.1 features

---

## References

- **Constitution**: `.specify/constitution.md` v0.1.1 (Engineering Quality VI)
- **Spec**: `.specify/specs/001-core/spec.md` v2.0 (Technical Notes)
- **Plan**: `plan.md` Phase 4.2
- **Architecture**: `architecture-decisions.md` Deployment Platform section