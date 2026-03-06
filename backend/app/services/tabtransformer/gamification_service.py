from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
from database_models import (
    User, Badge, UserBadge, UserAction, LeaderboardEntry, 
    PredictionHistory, ExplanationHistory, DatabaseManager, 
    POINTS_SYSTEM, initialize_database
)
from sqlalchemy import func, desc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis for caching and real-time features
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connected successfully")
except ImportError:
    redis_client = None
    logger.warning("Redis module not installed, using in-memory alternatives")
except Exception as e:
    redis_client = None
    logger.warning(f"Redis not available ({e}), using in-memory alternatives")

# Initialize database
db_manager = DatabaseManager()
db_manager.create_tables()
initialize_database(db_manager)

# Dependency to get database session
def get_db():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db_manager.close_session(db)

# Pydantic models
class UserActionRequest(BaseModel):
    """Request model for tracking user actions"""
    user_id: str = Field(..., description="User identifier")
    action_type: str = Field(..., description="Type of action (prediction, explanation, share, etc.)")
    action_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional action data")
    timestamp: Optional[datetime] = Field(default=None, description="Action timestamp")

class UserProgressResponse(BaseModel):
    """Response model for user progress"""
    user_id: str
    username: Optional[str]
    total_points: int
    current_streak: int
    longest_streak: int
    level: int
    badges: List[Dict[str, Any]]
    next_achievements: List[Dict[str, Any]]
    recent_actions: List[Dict[str, Any]]

class LeaderboardResponse(BaseModel):
    """Response model for leaderboard"""
    leaderboard_type: str
    period_start: datetime
    period_end: datetime
    entries: List[Dict[str, Any]]
    user_rank: Optional[int] = None

class BadgeCheckResponse(BaseModel):
    """Response model for badge check"""
    new_badges: List[Dict[str, Any]]
    total_points_earned: int
    level_up: bool

class GamificationService:
    """Core gamification logic service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_user(self, user_id: str, username: str = None) -> User:
        """Get existing user or create new one"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            user = User(
                id=user_id,
                username=username or user_id,
                created_at=datetime.utcnow()
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created new user: {user_id}")
        
        return user
    
    def track_action(self, user_id: str, action_type: str, action_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track user action and award points"""
        user = self.get_or_create_user(user_id)
        
        # Calculate points earned
        points_earned = POINTS_SYSTEM.get(action_type, 0)
        
        # Bonus points for specific conditions
        if action_type == "prediction" and action_data:
            # Bonus for high confidence
            if action_data.get("confidence") == "high":
                points_earned += POINTS_SYSTEM.get("high_confidence", 0)
            
            # Bonus for daily activity
            if self._is_first_prediction_today(user_id):
                points_earned += POINTS_SYSTEM.get("daily_prediction", 0)
        
        # Update user points and streak
        user.total_points += points_earned
        user.last_active = datetime.utcnow()
        
        # Update streak for predictions
        if action_type == "prediction":
            self._update_streak(user)
        
        # Update level based on points
        user.level = self._calculate_level(user.total_points)
        
        # Record action
        action = UserAction(
            user_id=user_id,
            action_type=action_type,
            points_earned=points_earned,
            action_data=json.dumps(action_data) if action_data else None
        )
        self.db.add(action)
        
        # Check for new badges
        new_badges = self._check_badges(user)
        
        self.db.commit()
        
        # Update Redis cache
        if redis_client:
            self._update_user_cache(user)
        
        return {
            "points_earned": points_earned,
            "total_points": user.total_points,
            "level": user.level,
            "current_streak": user.current_streak,
            "new_badges": new_badges
        }
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user progress"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user badges
        user_badges = self.db.query(UserBadge, Badge).join(Badge).filter(
            UserBadge.user_id == user_id
        ).all()
        
        badges = []
        for user_badge, badge in user_badges:
            badges.append({
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "category": badge.category,
                "earned_at": user_badge.earned_at.isoformat(),
                "points_earned": user_badge.points_earned
            })
        
        # Get recent actions
        recent_actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id
        ).order_by(desc(UserAction.timestamp)).limit(10).all()
        
        actions = []
        for action in recent_actions:
            actions.append({
                "action_type": action.action_type,
                "points_earned": action.points_earned,
                "timestamp": action.timestamp.isoformat(),
                "action_data": json.loads(action.action_data) if action.action_data else None
            })
        
        # Get next achievements
        next_achievements = self._get_next_achievements(user)
        
        return {
            "user_id": user.id,
            "username": user.username,
            "total_points": user.total_points,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "level": user.level,
            "badges": badges,
            "recent_actions": actions,
            "next_achievements": next_achievements
        }
    
    def get_leaderboard(self, leaderboard_type: str = "weekly", user_id: str = None) -> Dict[str, Any]:
        """Get leaderboard for specified time period"""
        # Calculate period dates
        now = datetime.utcnow()
        if leaderboard_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif leaderboard_type == "weekly":
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=7)
        elif leaderboard_type == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
        else:  # all_time
            period_start = datetime.utcnow().replace(year=2020, month=1, day=1)  # Far past
            period_end = now + timedelta(days=365)  # Far future
        
        # Get top users
        top_users = self.db.query(User).order_by(desc(User.total_points)).limit(100).all()
        
        entries = []
        user_rank = None
        
        for i, user in enumerate(top_users, 1):
            entry = {
                "rank": i,
                "user_id": user.id,
                "username": user.username,
                "total_points": user.total_points,
                "level": user.level,
                "current_streak": user.current_streak
            }
            entries.append(entry)
            
            if user.id == user_id:
                user_rank = i
        
        return {
            "leaderboard_type": leaderboard_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "entries": entries,
            "user_rank": user_rank
        }
    
    def _is_first_prediction_today(self, user_id: str) -> bool:
        """Check if this is the user's first prediction today"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        prediction_count = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.action_type == "prediction",
            UserAction.timestamp >= today_start
        ).count()
        
        return prediction_count == 1
    
    def _update_streak(self, user: User):
        """Update user's prediction streak"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Check if user predicted yesterday
        predicted_yesterday = self.db.query(UserAction).filter(
            UserAction.user_id == user.id,
            UserAction.action_type == "prediction",
            UserAction.timestamp >= yesterday_start,
            UserAction.timestamp <= yesterday_end
        ).first()
        
        if predicted_yesterday:
            user.current_streak += 1
            user.longest_streak = max(user.longest_streak, user.current_streak)
        else:
            # Check if user predicted today (continuing streak)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            predicted_today = self.db.query(UserAction).filter(
                UserAction.user_id == user.id,
                UserAction.action_type == "prediction",
                UserAction.timestamp >= today_start
            ).first()
            
            if not predicted_today:
                user.current_streak = 1
    
    def _calculate_level(self, total_points: int) -> int:
        """Calculate user level based on points"""
        # Simple exponential leveling: level = floor(sqrt(points / 100))
        import math
        return max(1, int(math.sqrt(total_points / 100)) + 1)
    
    def _check_badges(self, user: User) -> List[Dict[str, Any]]:
        """Check if user earned new badges"""
        new_badges = []
        
        # Get all available badges
        available_badges = self.db.query(Badge).filter(Badge.is_active == True).all()
        
        # Get user's existing badges
        existing_badge_ids = set(
            ub.badge_id for ub in self.db.query(UserBadge).filter(
                UserBadge.user_id == user.id
            ).all()
        )
        
        for badge in available_badges:
            if badge.id in existing_badge_ids:
                continue
            
            # Check badge conditions
            if self._check_badge_condition(user, badge):
                # Award badge
                user_badge = UserBadge(
                    user_id=user.id,
                    badge_id=badge.id,
                    points_earned=POINTS_SYSTEM.get("badge_earned", 50)
                )
                self.db.add(user_badge)
                
                # Add badge points to user total
                user.total_points += user_badge.points_earned
                
                new_badges.append({
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "category": badge.category,
                    "points_earned": user_badge.points_earned
                })
        
        return new_badges
    
    def _check_badge_condition(self, user: User, badge: Badge) -> bool:
        """Check if user meets badge condition"""
        if badge.condition_type == "count":
            # Count specific actions
            if badge.category == "prediction":
                count = self.db.query(UserAction).filter(
                    UserAction.user_id == user.id,
                    UserAction.action_type == "prediction"
                ).count()
            elif badge.category == "explanation":
                count = self.db.query(UserAction).filter(
                    UserAction.user_id == user.id,
                    UserAction.action_type == "explanation"
                ).count()
            elif badge.category == "sharing":
                count = self.db.query(UserAction).filter(
                    UserAction.user_id == user.id,
                    UserAction.action_type == "share"
                ).count()
            else:
                count = 0
            
            return count >= badge.condition_value
        
        elif badge.condition_type == "streak":
            return user.current_streak >= badge.condition_value
        
        elif badge.condition_type == "high_confidence":
            count = self.db.query(UserAction).filter(
                UserAction.user_id == user.id,
                UserAction.action_type == "prediction"
            ).join(PredictionHistory).filter(
                PredictionHistory.confidence == "high"
            ).count()
            return count >= badge.condition_value
        
        elif badge.condition_type == "leaderboard_rank":
            # Check if user is in top N
            leaderboard = self.get_leaderboard("weekly", user.id)
            return leaderboard.get("user_rank", 999) <= badge.condition_value
        
        return False
    
    def _get_next_achievements(self, user: User) -> List[Dict[str, Any]]:
        """Get next achievements user can unlock"""
        next_achievements = []
        
        # Get user's existing badges
        existing_badge_ids = set(
            ub.badge_id for ub in self.db.query(UserBadge).filter(
                UserBadge.user_id == user.id
            ).all()
        )
        
        # Get next badges in each category
        available_badges = self.db.query(Badge).filter(
            Badge.is_active == True,
            Badge.id.notin_(existing_badge_ids)
        ).all()
        
        for badge in available_badges:
            progress = self._get_badge_progress(user, badge)
            if progress["progress"] > 0:
                next_achievements.append({
                    "badge": {
                        "id": badge.id,
                        "name": badge.name,
                        "description": badge.description,
                        "icon": badge.icon,
                        "category": badge.category
                    },
                    "progress": progress["progress"],
                    "current": progress["current"],
                    "required": progress["required"],
                    "next_milestone": progress["next_milestone"]
                })
        
        # Sort by progress and limit to 5
        next_achievements.sort(key=lambda x: x["progress"], reverse=True)
        return next_achievements[:5]
    
    def _get_badge_progress(self, user: User, badge: Badge) -> Dict[str, Any]:
        """Get progress towards a specific badge"""
        if badge.condition_type == "count":
            if badge.category == "prediction":
                current = self.db.query(UserAction).filter(
                    UserAction.user_id == user.id,
                    UserAction.action_type == "prediction"
                ).count()
            elif badge.category == "explanation":
                current = self.db.query(UserAction).filter(
                    UserAction.user_id == user.id,
                    UserAction.action_type == "explanation"
                ).count()
            else:
                current = 0
            
            required = badge.condition_value
            progress = min(100, (current / required) * 100)
            
            return {
                "progress": progress,
                "current": current,
                "required": required,
                "next_milestone": required
            }
        
        elif badge.condition_type == "streak":
            current = user.current_streak
            required = badge.condition_value
            progress = min(100, (current / required) * 100)
            
            return {
                "progress": progress,
                "current": current,
                "required": required,
                "next_milestone": required
            }
        
        return {"progress": 0, "current": 0, "required": badge.condition_value, "next_milestone": badge.condition_value}
    
    def _update_user_cache(self, user: User):
        """Update user data in Redis cache"""
        if redis_client:
            cache_key = f"user:{user.id}"
            user_data = {
                "total_points": user.total_points,
                "level": user.level,
                "current_streak": user.current_streak,
                "last_active": user.last_active.isoformat()
            }
            redis_client.setex(cache_key, 3600, json.dumps(user_data))  # Cache for 1 hour
