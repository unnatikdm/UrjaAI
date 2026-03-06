from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    """User model for gamification system"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    total_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    # Relationships
    user_actions = relationship("UserAction", back_populates="user")
    user_badges = relationship("UserBadge", back_populates="user")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="user")

class Badge(Base):
    """Badge model for achievements"""
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(10), nullable=False)
    category = Column(String(20), nullable=False)  # prediction, explanation, streak, etc.
    points_required = Column(Integer, nullable=False)
    condition_type = Column(String(20), nullable=False)  # count, streak, accuracy, etc.
    condition_value = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")

class UserBadge(Base):
    """Association table for users and badges"""
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    points_earned = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="user_badges")
    badge = relationship("Badge", back_populates="user_badges")

class UserAction(Base):
    """Track user actions for gamification"""
    __tablename__ = "user_actions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(20), nullable=False)  # prediction, explanation, share, etc.
    points_earned = Column(Integer, default=0)
    action_data = Column(Text)  # JSON string with additional action data
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_actions")

class LeaderboardEntry(Base):
    """Leaderboard entries for different time periods"""
    __tablename__ = "leaderboard_entries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    leaderboard_type = Column(String(20), nullable=False)  # daily, weekly, monthly, all_time
    rank = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="leaderboard_entries")

class PredictionHistory(Base):
    """Track prediction history"""
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    request_id = Column(String, nullable=False)
    prediction = Column(Integer, nullable=False)
    probability = Column(Float, nullable=False)
    confidence = Column(String(10), nullable=False)
    features = Column(Text)  # JSON string of input features
    explanation_requested = Column(Boolean, default=False)
    processing_time_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ExplanationHistory(Base):
    """Track explanation history"""
    __tablename__ = "explanation_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    request_id = Column(String, nullable=False)
    prediction_request_id = Column(String, nullable=False)
    explanation_data = Column(Text)  # JSON string of SHAP explanation
    processing_time_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database setup
class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Use SQLite for development
            database_url = "sqlite:///gamification.db"
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()

# Badge definitions
BADGE_DEFINITIONS = [
    {
        "name": "First Prediction",
        "description": "Made your first prediction",
        "icon": "🎯",
        "category": "prediction",
        "points_required": 1,
        "condition_type": "count",
        "condition_value": 1
    },
    {
        "name": "Prediction Novice",
        "description": "Made 10 predictions",
        "icon": "🌟",
        "category": "prediction",
        "points_required": 10,
        "condition_type": "count",
        "condition_value": 10
    },
    {
        "name": "Prediction Expert",
        "description": "Made 50 predictions",
        "icon": "⭐",
        "category": "prediction",
        "points_required": 50,
        "condition_type": "count",
        "condition_value": 50
    },
    {
        "name": "Prediction Master",
        "description": "Made 100 predictions",
        "icon": "🏆",
        "category": "prediction",
        "points_required": 100,
        "condition_type": "count",
        "condition_value": 100
    },
    {
        "name": "Curious Mind",
        "description": "Viewed 5 explanations",
        "icon": "🔍",
        "category": "explanation",
        "points_required": 5,
        "condition_type": "count",
        "condition_value": 5
    },
    {
        "name": "Data Detective",
        "description": "Viewed 20 explanations",
        "icon": "🕵️",
        "category": "explanation",
        "points_required": 20,
        "condition_type": "count",
        "condition_value": 20
    },
    {
        "name": "Insight Seeker",
        "description": "Viewed 50 explanations",
        "icon": "💡",
        "category": "explanation",
        "points_required": 50,
        "condition_type": "count",
        "condition_value": 50
    },
    {
        "name": "Daily Streak",
        "description": "3-day prediction streak",
        "icon": "🔥",
        "category": "streak",
        "points_required": 3,
        "condition_type": "streak",
        "condition_value": 3
    },
    {
        "name": "Week Warrior",
        "description": "7-day prediction streak",
        "icon": "💪",
        "category": "streak",
        "points_required": 7,
        "condition_type": "streak",
        "condition_value": 7
    },
    {
        "name": "Month Master",
        "description": "30-day prediction streak",
        "icon": "👑",
        "category": "streak",
        "points_required": 30,
        "condition_type": "streak",
        "condition_value": 30
    },
    {
        "name": "High Confidence",
        "description": "Made 10 high-confidence predictions",
        "icon": "🎖️",
        "category": "accuracy",
        "points_required": 10,
        "condition_type": "high_confidence",
        "condition_value": 10
    },
    {
        "name": "Knowledge Sharer",
        "description": "Shared 5 explanations",
        "icon": "📤",
        "category": "sharing",
        "points_required": 5,
        "condition_type": "count",
        "condition_value": 5
    },
    {
        "name": "Community Leader",
        "description": "Top 10 in weekly leaderboard",
        "icon": "👥",
        "category": "leaderboard",
        "points_required": 1,
        "condition_type": "leaderboard_rank",
        "condition_value": 10
    }
]

# Points system
POINTS_SYSTEM = {
    "prediction": 10,
    "explanation": 5,
    "share": 20,
    "high_confidence": 15,
    "daily_prediction": 5,  # Bonus for daily activity
    "streak_day": 2,  # Bonus per streak day
    "badge_earned": 50
}

# Initialize database with badges
def initialize_database(db_manager: DatabaseManager):
    """Initialize database with default badges"""
    session = db_manager.get_session()
    
    try:
        # Check if badges already exist
        existing_badges = session.query(Badge).count()
        if existing_badges > 0:
            print(f"Database already initialized with {existing_badges} badges")
            return
        
        # Add default badges
        for badge_data in BADGE_DEFINITIONS:
            badge = Badge(**badge_data)
            session.add(badge)
        
        session.commit()
        print(f"Initialized database with {len(BADGE_DEFINITIONS)} badges")
        
    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db_manager.close_session(session)

if __name__ == "__main__":
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.create_tables()
    initialize_database(db_manager)
    print("Database initialized successfully!")
