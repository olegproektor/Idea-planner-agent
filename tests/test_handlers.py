#!/usr/bin/env python3
"""
Comprehensive tests for Telegram bot handlers covering:
- Mock Telegram update/context objects
- /start command response
- /help command response
- Idea message handling (including database storage)
- Error handling
- Aim for >80% coverage
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import logging

# Set up environment variables before importing any modules
os.environ['TELEGRAM_TOKEN'] = 'test_telegram_token_for_testing'
os.environ['GROQ_API_KEY'] = 'test_groq_api_key_for_testing'

# Add the project root to Python path to import src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import after path is set
from src.handlers import start_handler, help_handler, idea_handler, error_handler
from src.database import SessionLocal, UserCRUD, IdeaCRUD, AnalysisCRUD, AnalysisMode, AnalysisStatus
from telegram import Update, User as TelegramUser, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode


def create_mock_update_with_user(user_id=12345, username="testuser", first_name="Test", last_name="User", language_code="en"):
    """Create a mock Telegram Update object with user information"""
    mock_user = MagicMock(spec=TelegramUser)
    mock_user.id = user_id
    mock_user.username = username
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    mock_user.language_code = language_code
    
    mock_message = MagicMock(spec=Message)
    mock_message.text = None
    
    mock_update = MagicMock(spec=Update)
    mock_update.effective_user = mock_user
    mock_update.message = mock_message
    
    return mock_update


def create_mock_update_with_message(user_id=12345, message_text="Test idea"):
    """Create a mock Telegram Update object with message"""
    mock_user = MagicMock(spec=TelegramUser)
    mock_user.id = user_id
    mock_user.username = "testuser"
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.language_code = "en"
    
    mock_message = MagicMock(spec=Message)
    mock_message.text = message_text
    
    mock_update = MagicMock(spec=Update)
    mock_update.effective_user = mock_user
    mock_update.message = mock_message
    
    return mock_update


def create_mock_context():
    """Create a mock Telegram context object"""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_start_handler_new_user():
    """Test /start command response for new user"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=99999)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Mock database operations
    with patch('src.handlers.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock UserCRUD.get_user_by_telegram_id to return None (new user)
        mock_user_crud = MagicMock()
        mock_user_crud.get_user_by_telegram_id.return_value = None
        
        with patch('src.handlers.UserCRUD', mock_user_crud):
            # Mock create_user to return a user object
            mock_created_user = MagicMock()
            mock_created_user.id = 1
            mock_user_crud.create_user.return_value = mock_created_user
            
            # Call the handler
            await start_handler(mock_update, mock_context)
            
            # Verify database operations
            mock_user_crud.get_user_by_telegram_id.assert_called_once_with(mock_db, "99999")
            mock_user_crud.create_user.assert_called_once()
            
            # Verify welcome message was sent
            mock_reply.assert_awaited_once()
            reply_call = mock_reply.await_args
            assert "🌟 Добро пожаловать в Idea Planner Bot! 🌟" in reply_call.args[0]
            assert ParseMode.MARKDOWN in reply_call.kwargs.values()


@pytest.mark.asyncio
async def test_start_handler_existing_user():
    """Test /start command response for existing user"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Mock database operations
    with patch('src.handlers.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock UserCRUD.get_user_by_telegram_id to return existing user
        mock_user_crud = MagicMock()
        mock_existing_user = MagicMock()
        mock_existing_user.id = 1
        mock_user_crud.get_user_by_telegram_id.return_value = mock_existing_user
        
        with patch('src.handlers.UserCRUD', mock_user_crud):
            # Mock update_user
            mock_user_crud.update_user.return_value = mock_existing_user
            
            # Call the handler
            await start_handler(mock_update, mock_context)
            
            # Verify database operations
            mock_user_crud.get_user_by_telegram_id.assert_called_once_with(mock_db, "12345")
            mock_user_crud.update_user.assert_called_once()
            mock_user_crud.create_user.assert_not_called()
            
            # Verify welcome message was sent
            mock_reply.assert_awaited_once()
            reply_call = mock_reply.await_args
            assert "🌟 Добро пожаловать в Idea Planner Bot! 🌟" in reply_call.args[0]


@pytest.mark.asyncio
async def test_start_handler_error():
    """Test /start command error handling"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Mock database to raise an exception
    with patch('src.handlers.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock UserCRUD to raise exception
        mock_user_crud = MagicMock()
        mock_user_crud.get_user_by_telegram_id.side_effect = Exception("Database error")
        
        with patch('src.handlers.UserCRUD', mock_user_crud):
            # Call the handler
            await start_handler(mock_update, mock_context)
            
            # Verify error message was sent
            mock_reply.assert_awaited_once()
            reply_call = mock_reply.await_args
            assert "❌ Произошла ошибка. Пожалуйста, попробуйте позже." in reply_call.args[0]


@pytest.mark.asyncio
async def test_help_handler_success():
    """Test /help command response"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Call the handler
    await help_handler(mock_update, mock_context)
    
    # Verify help message was sent
    mock_reply.assert_awaited_once()
    reply_call = mock_reply.await_args
    assert "🆘 Справка по Idea Planner Bot 🆘" in reply_call.args[0]
    assert ParseMode.MARKDOWN in reply_call.kwargs.values()


@pytest.mark.asyncio
async def test_help_handler_error():
    """Test /help command error handling"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply to raise exception on first call, succeed on second
    mock_reply = AsyncMock()
    call_count = 0
    def reply_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Reply error")
        # Second call (error message) should succeed
    
    mock_reply.side_effect = reply_side_effect
    mock_update.message.reply_text = mock_reply
    
    # Call the handler
    await help_handler(mock_update, mock_context)
    
    # Verify error handling worked
    assert mock_reply.await_count == 2  # Original call + error message call


@pytest.mark.asyncio
async def test_idea_handler_empty_message():
    """Test idea handler with empty message"""
    # Create mock update with empty message
    mock_update = create_mock_update_with_message(user_id=12345, message_text="")
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Call the handler
    await idea_handler(mock_update, mock_context)
    
    # Verify warning message was sent
    mock_reply.assert_awaited_once()
    reply_call = mock_reply.await_args
    assert "⚠️ Пожалуйста, отправьте непустое сообщение с вашей идеей." in reply_call.args[0]


@pytest.mark.asyncio
async def test_idea_handler_valid_idea():
    """Test idea handler with valid idea message"""
    # Create mock update with idea message
    mock_update = create_mock_update_with_message(user_id=12345, message_text="Great business idea!")
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Mock progress message
    mock_progress_message = AsyncMock()
    mock_progress_message.edit_text = AsyncMock()
    mock_reply.return_value = mock_progress_message
    
    # Mock database operations
    with patch('src.handlers.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock UserCRUD operations
        mock_user_crud = MagicMock()
        mock_existing_user = MagicMock()
        mock_existing_user.id = 1
        mock_user_crud.get_user_by_telegram_id.return_value = mock_existing_user
        mock_user_crud.update_user.return_value = mock_existing_user
        
        # Mock IdeaCRUD operations
        mock_idea_crud = MagicMock()
        mock_created_idea = MagicMock()
        mock_created_idea.id = 1
        mock_created_idea.text = "Great business idea!"
        mock_created_idea.mode = AnalysisMode.EVALUATION
        mock_idea_crud.create_idea.return_value = mock_created_idea
        
        # Mock AnalysisCRUD operations
        mock_analysis_crud = MagicMock()
        mock_created_analysis = MagicMock()
        mock_created_analysis.id = 1
        mock_created_analysis.status = AnalysisStatus.QUEUED
        mock_created_analysis.idea = mock_created_idea
        mock_analysis_crud.create_analysis.return_value = mock_created_analysis
        
        with patch('src.handlers.UserCRUD', mock_user_crud):
            with patch('src.handlers.IdeaCRUD', mock_idea_crud):
                with patch('src.handlers.AnalysisCRUD', mock_analysis_crud):
                    # Call the handler
                    await idea_handler(mock_update, mock_context)
                    
                    # Verify database operations
                    # get_user_by_telegram_id is called twice: once for checking user, once for getting user_id
                    assert mock_user_crud.get_user_by_telegram_id.call_count == 2
                    mock_idea_crud.create_idea.assert_called_once()
                    mock_analysis_crud.create_analysis.assert_called_once()
                    
                    # Verify progress messages
                    mock_reply.assert_awaited()
                    mock_progress_message.edit_text.assert_awaited_once()
                    
                    # Verify final response message
                    final_reply_call = mock_reply.await_args_list[-1]
                    assert "🎉 Спасибо за вашу идею! 🎉" in final_reply_call.args[0]
                    assert "Great business idea!" in final_reply_call.args[0]


@pytest.mark.asyncio
async def test_idea_handler_new_user_with_idea():
    """Test idea handler with new user and valid idea"""
    # Create mock update with idea message
    mock_update = create_mock_update_with_message(user_id=99999, message_text="New user idea")
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Mock progress message
    mock_progress_message = AsyncMock()
    mock_progress_message.edit_text = AsyncMock()
    mock_reply.return_value = mock_progress_message
    
    # Mock database operations
    with patch('src.handlers.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock UserCRUD operations for new user
        mock_user_crud = MagicMock()
        # Mock get_user_by_telegram_id to return None for first call, then return created user for second call
        call_count = [0]  # Use list to allow modification in nested function
        def get_user_side_effect(db, telegram_id):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # First call - no existing user
            else:
                return mock_created_user  # Second call - return created user
        
        mock_user_crud.get_user_by_telegram_id.side_effect = get_user_side_effect
        
        mock_created_user = MagicMock()
        mock_created_user.id = 1
        mock_user_crud.create_user.return_value = mock_created_user
        
        # Mock IdeaCRUD operations
        mock_idea_crud = MagicMock()
        mock_created_idea = MagicMock()
        mock_created_idea.id = 1
        mock_created_idea.text = "New user idea"
        mock_created_idea.mode = AnalysisMode.EVALUATION
        mock_idea_crud.create_idea.return_value = mock_created_idea
        
        # Mock AnalysisCRUD operations
        mock_analysis_crud = MagicMock()
        mock_created_analysis = MagicMock()
        mock_created_analysis.id = 1
        mock_created_analysis.status = AnalysisStatus.QUEUED
        mock_created_analysis.idea = mock_created_idea
        mock_analysis_crud.create_analysis.return_value = mock_created_analysis
        
        with patch('src.handlers.UserCRUD', mock_user_crud):
            with patch('src.handlers.IdeaCRUD', mock_idea_crud):
                with patch('src.handlers.AnalysisCRUD', mock_analysis_crud):
                    # Call the handler
                    await idea_handler(mock_update, mock_context)
                    
                    # Verify user was created
                    mock_user_crud.create_user.assert_called_once()
                    
                    # Verify idea and analysis were created
                    mock_idea_crud.create_idea.assert_called_once()
                    mock_analysis_crud.create_analysis.assert_called_once()


@pytest.mark.asyncio
async def test_idea_handler_error():
    """Test idea handler error handling"""
    # Create mock update with idea message
    mock_update = create_mock_update_with_message(user_id=12345, message_text="Test idea")
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.message.reply_text = mock_reply
    
    # Mock database to raise exception
    with patch('src.handlers.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Mock UserCRUD to raise exception
        mock_user_crud = MagicMock()
        mock_user_crud.get_user_by_telegram_id.side_effect = Exception("Database error")
        
        with patch('src.handlers.UserCRUD', mock_user_crud):
            # Call the handler
            await idea_handler(mock_update, mock_context)
            
            # Verify error message was sent (may be called twice: once for progress, once for error)
            assert mock_reply.await_count >= 1
            # Check the last call contains the error message
            if mock_reply.await_count > 0:
                reply_call = mock_reply.await_args_list[-1]
                assert "❌ Произошла ошибка при обработке вашей идеи." in reply_call.args[0]


@pytest.mark.asyncio
async def test_error_handler_with_update():
    """Test global error handler with update context"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.effective_message.reply_text = mock_reply
    
    # Create a test error
    test_error = Exception("Test error message")
    
    # Call the error handler
    await error_handler(mock_update, mock_context, test_error)
    
    # Verify error message was sent
    mock_reply.assert_awaited_once()
    reply_call = mock_reply.await_args
    assert "❌ Извините, произошла ошибка." in reply_call.args[0]


@pytest.mark.asyncio
async def test_error_handler_without_update():
    """Test global error handler without update context"""
    # Create mock context only
    mock_context = create_mock_context()
    
    # Create a test error
    test_error = Exception("Test error message")
    
    # Call the error handler with None update
    await error_handler(None, mock_context, test_error)
    
    # Should not crash and should handle gracefully


@pytest.mark.asyncio
async def test_error_handler_without_message():
    """Test global error handler without effective message"""
    # Create mock update without effective message
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_update.effective_message = None
    mock_context = create_mock_context()
    
    # Create a test error
    test_error = Exception("Test error message")
    
    # Call the error handler
    await error_handler(mock_update, mock_context, test_error)
    
    # Should handle gracefully without sending message


@pytest.mark.asyncio
async def test_error_handler_with_error_attributes():
    """Test global error handler with error having message and code attributes"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.effective_message.reply_text = mock_reply
    
    # Create a test error with attributes
    test_error = Exception("Test error message")
    test_error.code = 500
    
    # Call the error handler
    await error_handler(mock_update, mock_context, test_error)
    
    # Verify error message was sent
    mock_reply.assert_awaited_once()


@pytest.mark.asyncio
async def test_error_handler_fallback():
    """Test global error handler fallback when error handler itself fails"""
    # Create mock update and context
    mock_update = create_mock_update_with_user(user_id=12345)
    mock_context = create_mock_context()
    
    # Mock the message reply
    mock_reply = AsyncMock()
    mock_update.effective_message.reply_text = mock_reply
    
    # Create a test error
    test_error = Exception("Test error message")
    
    # Mock logger to raise exception only on the first error call
    with patch('src.handlers.logger') as mock_logger:
        call_count = 0
        def logger_error_side_effect(msg):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Only fail on first error log
                raise Exception("Logger error")
            # Allow subsequent calls to succeed
        
        mock_logger.error.side_effect = logger_error_side_effect
        
        # Call the error handler
        await error_handler(mock_update, mock_context, test_error)
        
        # Should handle the logger error gracefully and continue with fallback logging
        assert mock_logger.error.call_count >= 2  # Original error + fallback error


def test_handler_imports():
    """Test that all handlers can be imported successfully"""
    # This test ensures all handlers are properly defined and importable
    assert callable(start_handler)
    assert callable(help_handler)
    assert callable(idea_handler)
    assert callable(error_handler)


def test_handler_signatures():
    """Test that handlers have correct signatures"""
    import inspect
    
    # Check start_handler signature
    start_sig = inspect.signature(start_handler)
    assert len(start_sig.parameters) == 2
    assert 'update' in start_sig.parameters
    assert 'context' in start_sig.parameters
    
    # Check help_handler signature
    help_sig = inspect.signature(help_handler)
    assert len(help_sig.parameters) == 2
    assert 'update' in help_sig.parameters
    assert 'context' in help_sig.parameters
    
    # Check idea_handler signature
    idea_sig = inspect.signature(idea_handler)
    assert len(idea_sig.parameters) == 2
    assert 'update' in idea_sig.parameters
    assert 'context' in idea_sig.parameters
    
    # Check error_handler signature
    error_sig = inspect.signature(error_handler)
    assert len(error_sig.parameters) == 3
    assert 'update' in error_sig.parameters
    assert 'context' in error_sig.parameters
    assert 'error' in error_sig.parameters