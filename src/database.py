from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

# SQLite database setup
engine = create_engine('sqlite:///bot.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Enums for status and modes
class AnalysisStatus(enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class AnalysisMode(enum.Enum):
    EVALUATION = "ОЦЕНКА"
    BUSINESS_PLAN = "БИЗНЕС-ПЛАН"
    MARKETING = "МАРКЕТИНГ"
    EXECUTION = "ИСПОЛНЕНИЕ"
    WEBSITE = "САЙТ"
    REPORT_1 = "ОТЧЁТ 1"
    REPORT_2 = "ОТЧЁТ 2"
    REPORT_3 = "ОТЧЁТ 3"
    WHY_NOW = "ПОЧЕМУ_СЕЙЧАС"
    MARKET_GAP = "РЫНОЧНЫЙ_РАЗРЫВ"
    EVIDENCE = "ДОКАЗАТЕЛЬСТВА"

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ideas = relationship("Idea", back_populates="user")
    analyses = relationship("Analysis", back_populates="user")

# Idea Model
class Idea(Base):
    __tablename__ = "ideas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    mode = Column(Enum(AnalysisMode), default=AnalysisMode.EVALUATION)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ideas")
    analyses = relationship("Analysis", back_populates="idea")

# Analysis Model
class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.QUEUED)
    report = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    idea = relationship("Idea", back_populates="analyses")
    user = relationship("User", back_populates="analyses")

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# CRUD Operations for User
class UserCRUD:
    @staticmethod
    def create_user(db, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None, language_code: str = None):
        db_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_id(db, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_telegram_id(db, telegram_id: str):
        return db.query(User).filter(User.telegram_id == telegram_id).first()

    @staticmethod
    def update_user(db, user_id: int, username: str = None, first_name: str = None, last_name: str = None, language_code: str = None):
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            if username is not None:
                db_user.username = username
            if first_name is not None:
                db_user.first_name = first_name
            if last_name is not None:
                db_user.last_name = last_name
            if language_code is not None:
                db_user.language_code = language_code
            db.commit()
            db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db, user_id: int):
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
        return db_user

# CRUD Operations for Idea
class IdeaCRUD:
    @staticmethod
    def create_idea(db, user_id: int, text: str, mode: AnalysisMode = AnalysisMode.EVALUATION):
        db_idea = Idea(
            user_id=user_id,
            text=text,
            mode=mode
        )
        db.add(db_idea)
        db.commit()
        db.refresh(db_idea)
        return db_idea

    @staticmethod
    def get_idea_by_id(db, idea_id: int):
        return db.query(Idea).filter(Idea.id == idea_id).first()

    @staticmethod
    def get_ideas_by_user_id(db, user_id: int):
        return db.query(Idea).filter(Idea.user_id == user_id).all()

    @staticmethod
    def update_idea(db, idea_id: int, text: str = None, mode: AnalysisMode = None):
        db_idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if db_idea:
            if text is not None:
                db_idea.text = text
            if mode is not None:
                db_idea.mode = mode
            db.commit()
            db.refresh(db_idea)
        return db_idea

    @staticmethod
    def delete_idea(db, idea_id: int):
        db_idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if db_idea:
            db.delete(db_idea)
            db.commit()
        return db_idea

# CRUD Operations for Analysis
class AnalysisCRUD:
    @staticmethod
    def create_analysis(db, idea_id: int, user_id: int, status: AnalysisStatus = AnalysisStatus.QUEUED, report: str = None):
        db_analysis = Analysis(
            idea_id=idea_id,
            user_id=user_id,
            status=status,
            report=report
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        return db_analysis

    @staticmethod
    def get_analysis_by_id(db, analysis_id: int):
        return db.query(Analysis).filter(Analysis.id == analysis_id).first()

    @staticmethod
    def get_analyses_by_idea_id(db, idea_id: int):
        return db.query(Analysis).filter(Analysis.idea_id == idea_id).all()

    @staticmethod
    def get_analyses_by_user_id(db, user_id: int):
        return db.query(Analysis).filter(Analysis.user_id == user_id).all()

    @staticmethod
    def update_analysis(db, analysis_id: int, status: AnalysisStatus = None, report: str = None):
        db_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if db_analysis:
            if status is not None:
                db_analysis.status = status
            if report is not None:
                db_analysis.report = report
            db.commit()
            db.refresh(db_analysis)
        return db_analysis

    @staticmethod
    def delete_analysis(db, analysis_id: int):
        db_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if db_analysis:
            db.delete(db_analysis)
            db.commit()
        return db_analysis

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()