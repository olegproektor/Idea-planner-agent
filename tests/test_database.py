#!/usr/bin/env python3
"""
Comprehensive tests for database operations covering User, Idea, and Analysis models.
Tests all CRUD operations and aims for >80% coverage.
"""

import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the project root to Python path to import src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the database models and CRUD operations
from src.database import (
    Base, User, Idea, Analysis, 
    UserCRUD, IdeaCRUD, AnalysisCRUD,
    AnalysisStatus, AnalysisMode,
    init_db, get_db
)

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        # Close the session and drop all tables
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db_session):
    """Create a test user for use in tests"""
    user_data = {
        "telegram_id": "123456789",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "ru"
    }
    
    user = UserCRUD.create_user(db_session, **user_data)
    return user

@pytest.fixture
def test_idea(db_session, test_user):
    """Create a test idea for use in tests"""
    idea_data = {
        "user_id": test_user.id,
        "text": "Test business idea about eco-friendly products",
        "mode": AnalysisMode.EVALUATION
    }
    
    idea = IdeaCRUD.create_idea(db_session, **idea_data)
    return idea

@pytest.fixture
def test_analysis(db_session, test_user, test_idea):
    """Create a test analysis for use in tests"""
    analysis_data = {
        "idea_id": test_idea.id,
        "user_id": test_user.id,
        "status": AnalysisStatus.QUEUED,
        "report": "Initial analysis report"
    }
    
    analysis = AnalysisCRUD.create_analysis(db_session, **analysis_data)
    return analysis


# ============ USER MODEL TESTS ============

def test_create_user(db_session):
    """Test creating a new user"""
    user_data = {
        "telegram_id": "987654321",
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "language_code": "en"
    }
    
    user = UserCRUD.create_user(db_session, **user_data)
    
    assert user is not None
    assert user.id is not None
    assert user.telegram_id == "987654321"
    assert user.username == "newuser"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.language_code == "en"
    assert user.created_at is not None

def test_get_user_by_id(db_session, test_user):
    """Test retrieving a user by ID"""
    user = UserCRUD.get_user_by_id(db_session, test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.telegram_id == test_user.telegram_id

def test_get_user_by_telegram_id(db_session, test_user):
    """Test retrieving a user by Telegram ID"""
    user = UserCRUD.get_user_by_telegram_id(db_session, test_user.telegram_id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.telegram_id == test_user.telegram_id

def test_update_user(db_session, test_user):
    """Test updating user information"""
    updated_data = {
        "username": "updateduser",
        "first_name": "Updated",
        "last_name": "User",
        "language_code": "ru"
    }
    
    user = UserCRUD.update_user(db_session, test_user.id, **updated_data)
    
    assert user is not None
    assert user.username == "updateduser"
    assert user.first_name == "Updated"
    assert user.last_name == "User"
    assert user.language_code == "ru"

def test_delete_user(db_session, test_user):
    """Test deleting a user"""
    # First verify the user exists
    user_before = UserCRUD.get_user_by_id(db_session, test_user.id)
    assert user_before is not None
    
    # Delete the user
    deleted_user = UserCRUD.delete_user(db_session, test_user.id)
    assert deleted_user is not None
    
    # Verify the user no longer exists
    user_after = UserCRUD.get_user_by_id(db_session, test_user.id)
    assert user_after is None


# ============ IDEA MODEL TESTS ============

def test_create_idea(db_session, test_user):
    """Test creating a new idea"""
    idea_data = {
        "user_id": test_user.id,
        "text": "New innovative business idea",
        "mode": AnalysisMode.BUSINESS_PLAN
    }
    
    idea = IdeaCRUD.create_idea(db_session, **idea_data)
    
    assert idea is not None
    assert idea.id is not None
    assert idea.user_id == test_user.id
    assert idea.text == "New innovative business idea"
    assert idea.mode == AnalysisMode.BUSINESS_PLAN
    assert idea.created_at is not None

def test_get_idea_by_id(db_session, test_idea):
    """Test retrieving an idea by ID"""
    idea = IdeaCRUD.get_idea_by_id(db_session, test_idea.id)
    
    assert idea is not None
    assert idea.id == test_idea.id
    assert idea.text == test_idea.text

def test_get_ideas_by_user_id(db_session, test_user):
    """Test retrieving all ideas for a user"""
    # Create multiple ideas for the user
    idea1 = IdeaCRUD.create_idea(db_session, test_user.id, "Idea 1", AnalysisMode.EVALUATION)
    idea2 = IdeaCRUD.create_idea(db_session, test_user.id, "Idea 2", AnalysisMode.MARKETING)
    
    ideas = IdeaCRUD.get_ideas_by_user_id(db_session, test_user.id)
    
    assert len(ideas) == 2
    assert all(idea.user_id == test_user.id for idea in ideas)
    assert any(idea.text == "Idea 1" for idea in ideas)
    assert any(idea.text == "Idea 2" for idea in ideas)

def test_update_idea(db_session, test_idea):
    """Test updating an idea"""
    updated_data = {
        "text": "Updated business idea text",
        "mode": AnalysisMode.MARKETING
    }
    
    idea = IdeaCRUD.update_idea(db_session, test_idea.id, **updated_data)
    
    assert idea is not None
    assert idea.text == "Updated business idea text"
    assert idea.mode == AnalysisMode.MARKETING

def test_delete_idea(db_session, test_idea):
    """Test deleting an idea"""
    # First verify the idea exists
    idea_before = IdeaCRUD.get_idea_by_id(db_session, test_idea.id)
    assert idea_before is not None
    
    # Delete the idea
    deleted_idea = IdeaCRUD.delete_idea(db_session, test_idea.id)
    assert deleted_idea is not None
    
    # Verify the idea no longer exists
    idea_after = IdeaCRUD.get_idea_by_id(db_session, test_idea.id)
    assert idea_after is None


# ============ ANALYSIS MODEL TESTS ============

def test_create_analysis(db_session, test_user, test_idea):
    """Test creating a new analysis"""
    analysis_data = {
        "idea_id": test_idea.id,
        "user_id": test_user.id,
        "status": AnalysisStatus.RUNNING,
        "report": "Detailed analysis report content"
    }
    
    analysis = AnalysisCRUD.create_analysis(db_session, **analysis_data)
    
    assert analysis is not None
    assert analysis.id is not None
    assert analysis.idea_id == test_idea.id
    assert analysis.user_id == test_user.id
    assert analysis.status == AnalysisStatus.RUNNING
    assert analysis.report == "Detailed analysis report content"
    assert analysis.created_at is not None
    assert analysis.updated_at is not None

def test_get_analysis_by_id(db_session, test_analysis):
    """Test retrieving an analysis by ID"""
    analysis = AnalysisCRUD.get_analysis_by_id(db_session, test_analysis.id)
    
    assert analysis is not None
    assert analysis.id == test_analysis.id
    assert analysis.report == test_analysis.report

def test_get_analyses_by_idea_id(db_session, test_user, test_idea):
    """Test retrieving all analyses for an idea"""
    # Create multiple analyses for the idea
    analysis1 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.DONE, "Report 1")
    analysis2 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.FAILED, "Report 2")
    
    analyses = AnalysisCRUD.get_analyses_by_idea_id(db_session, test_idea.id)
    
    assert len(analyses) == 2
    assert all(analysis.idea_id == test_idea.id for analysis in analyses)
    assert any(analysis.report == "Report 1" for analysis in analyses)
    assert any(analysis.report == "Report 2" for analysis in analyses)

def test_get_analyses_by_user_id(db_session, test_user, test_idea):
    """Test retrieving all analyses for a user"""
    # Create multiple analyses for the user
    analysis1 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.DONE, "User Report 1")
    analysis2 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.QUEUED, "User Report 2")
    
    analyses = AnalysisCRUD.get_analyses_by_user_id(db_session, test_user.id)
    
    assert len(analyses) == 2
    assert all(analysis.user_id == test_user.id for analysis in analyses)
    assert any(analysis.report == "User Report 1" for analysis in analyses)
    assert any(analysis.report == "User Report 2" for analysis in analyses)

def test_update_analysis(db_session, test_analysis):
    """Test updating an analysis"""
    updated_data = {
        "status": AnalysisStatus.DONE,
        "report": "Updated comprehensive analysis report"
    }
    
    analysis = AnalysisCRUD.update_analysis(db_session, test_analysis.id, **updated_data)
    
    assert analysis is not None
    assert analysis.status == AnalysisStatus.DONE
    assert analysis.report == "Updated comprehensive analysis report"

def test_delete_analysis(db_session, test_analysis):
    """Test deleting an analysis"""
    # First verify the analysis exists
    analysis_before = AnalysisCRUD.get_analysis_by_id(db_session, test_analysis.id)
    assert analysis_before is not None
    
    # Delete the analysis
    deleted_analysis = AnalysisCRUD.delete_analysis(db_session, test_analysis.id)
    assert deleted_analysis is not None
    
    # Verify the analysis no longer exists
    analysis_after = AnalysisCRUD.get_analysis_by_id(db_session, test_analysis.id)
    assert analysis_after is None


# ============ RELATIONSHIP TESTS ============

def test_user_ideas_relationship(db_session, test_user):
    """Test the relationship between User and Idea models"""
    # Create ideas for the user
    idea1 = IdeaCRUD.create_idea(db_session, test_user.id, "User Idea 1", AnalysisMode.EVALUATION)
    idea2 = IdeaCRUD.create_idea(db_session, test_user.id, "User Idea 2", AnalysisMode.BUSINESS_PLAN)
    
    # Refresh the user to get the relationship
    db_session.refresh(test_user)
    
    assert len(test_user.ideas) == 2
    assert any(idea.text == "User Idea 1" for idea in test_user.ideas)
    assert any(idea.text == "User Idea 2" for idea in test_user.ideas)

def test_user_analyses_relationship(db_session, test_user, test_idea):
    """Test the relationship between User and Analysis models"""
    # Create analyses for the user
    analysis1 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.DONE, "Analysis 1")
    analysis2 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.RUNNING, "Analysis 2")
    
    # Refresh the user to get the relationship
    db_session.refresh(test_user)
    
    assert len(test_user.analyses) == 2
    assert any(analysis.report == "Analysis 1" for analysis in test_user.analyses)
    assert any(analysis.report == "Analysis 2" for analysis in test_user.analyses)

def test_idea_analyses_relationship(db_session, test_user, test_idea):
    """Test the relationship between Idea and Analysis models"""
    # Create analyses for the idea
    analysis1 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.QUEUED, "Idea Analysis 1")
    analysis2 = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.DONE, "Idea Analysis 2")
    
    # Refresh the idea to get the relationship
    db_session.refresh(test_idea)
    
    assert len(test_idea.analyses) == 2
    assert any(analysis.report == "Idea Analysis 1" for analysis in test_idea.analyses)
    assert any(analysis.report == "Idea Analysis 2" for analysis in test_idea.analyses)


# ============ EDGE CASE TESTS ============

def test_create_user_with_minimal_data(db_session):
    """Test creating a user with only required fields"""
    user = UserCRUD.create_user(db_session, telegram_id="minimal123")
    
    assert user is not None
    assert user.telegram_id == "minimal123"
    assert user.username is None
    assert user.first_name is None
    assert user.last_name is None
    assert user.language_code is None

def test_get_nonexistent_user(db_session):
    """Test retrieving a non-existent user"""
    user = UserCRUD.get_user_by_id(db_session, 999999)
    assert user is None
    
    user_by_telegram = UserCRUD.get_user_by_telegram_id(db_session, "nonexistent")
    assert user_by_telegram is None

def test_update_nonexistent_user(db_session):
    """Test updating a non-existent user"""
    user = UserCRUD.update_user(db_session, 999999, username="newuser")
    assert user is None

def test_delete_nonexistent_user(db_session):
    """Test deleting a non-existent user"""
    user = UserCRUD.delete_user(db_session, 999999)
    assert user is None

def test_analysis_status_transitions(db_session, test_user, test_idea):
    """Test valid status transitions for analysis"""
    # Create analysis with QUEUED status
    analysis = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.QUEUED)
    
    # Transition to RUNNING
    analysis = AnalysisCRUD.update_analysis(db_session, analysis.id, status=AnalysisStatus.RUNNING)
    assert analysis.status == AnalysisStatus.RUNNING
    
    # Transition to DONE
    analysis = AnalysisCRUD.update_analysis(db_session, analysis.id, status=AnalysisStatus.DONE)
    assert analysis.status == AnalysisStatus.DONE

def test_analysis_mode_enum(db_session, test_user):
    """Test all analysis modes"""
    modes_to_test = [
        AnalysisMode.EVALUATION,
        AnalysisMode.BUSINESS_PLAN,
        AnalysisMode.MARKETING,
        AnalysisMode.EXECUTION,
        AnalysisMode.WEBSITE,
        AnalysisMode.REPORT_1,
        AnalysisMode.REPORT_2,
        AnalysisMode.REPORT_3,
        AnalysisMode.WHY_NOW,
        AnalysisMode.MARKET_GAP,
        AnalysisMode.EVIDENCE
    ]
    
    for mode in modes_to_test:
        idea = IdeaCRUD.create_idea(db_session, test_user.id, f"Idea for {mode.value}", mode)
        assert idea.mode == mode

def test_relationship_integrity_after_deletion(db_session, test_user, test_idea):
    """Test that relationships are properly maintained after deletions"""
    # Create analysis
    analysis = AnalysisCRUD.create_analysis(db_session, test_idea.id, test_user.id, AnalysisStatus.DONE, "Test report")
    
    # First delete the analysis to maintain referential integrity
    AnalysisCRUD.delete_analysis(db_session, analysis.id)
    
    # Then delete the idea
    IdeaCRUD.delete_idea(db_session, test_idea.id)
    
    # Verify both are deleted
    analysis_check = AnalysisCRUD.get_analysis_by_id(db_session, analysis.id)
    assert analysis_check is None  # Analysis should be deleted
    
    idea_check = IdeaCRUD.get_idea_by_id(db_session, test_idea.id)
    assert idea_check is None  # Idea should be deleted


# ============ DATABASE INITIALIZATION TEST ============

def test_database_initialization():
    """Test that database initialization works correctly"""
    # Create a temporary in-memory database
    temp_engine = create_engine("sqlite:///:memory:")
    temp_session = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)
    
    # Initialize database
    Base.metadata.create_all(bind=temp_engine)
    
    # Verify tables were created
    db = temp_session()
    try:
        # Check if tables exist by attempting to query them
        user_count = db.query(User).count()
        idea_count = db.query(Idea).count()
        analysis_count = db.query(Analysis).count()
        
        assert user_count == 0
        assert idea_count == 0
        assert analysis_count == 0
    finally:
        db.close()