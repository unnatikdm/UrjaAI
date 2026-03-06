from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import uuid

from gamification_service import GamificationService, get_db
from database_models import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for gamification API
class TrackActionRequest(BaseModel):
    """Request model for tracking user actions"""
    user_id: str = Field(..., description="User identifier")
    action_type: str = Field(..., description="Type of action")
    action_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional action data")
    timestamp: Optional[datetime] = Field(default=None, description="Action timestamp")

class TrackActionResponse(BaseModel):
    """Response model for action tracking"""
    success: bool
    points_earned: int
    total_points: int
    level: int
    current_streak: int
    new_badges: List[Dict[str, Any]]

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
    period_start: str
    period_end: str
    entries: List[Dict[str, Any]]
    user_rank: Optional[int] = None

class BadgeCheckResponse(BaseModel):
    """Response model for badge check"""
    new_badges: List[Dict[str, Any]]
    total_points_earned: int
    level_up: bool

class PointsSummaryResponse(BaseModel):
    """Response model for points summary"""
    total_points: int
    points_by_category: Dict[str, int]
    recent_points: List[Dict[str, Any]]
    level_progress: Dict[str, Any]

# Gamification API endpoints
async def track_user_action(
    request: TrackActionRequest, 
    background_tasks: BackgroundTasks,
    db: DatabaseManager = Depends(get_db)
):
    """Track user action and award points"""
    try:
        gamification = GamificationService(db)
        
        # Track the action
        result = gamification.track_action(
            user_id=request.user_id,
            action_type=request.action_type,
            action_data=request.action_data
        )
        
        # Log activity for analytics
        background_tasks.add_task(
            log_gamification_activity,
            request.user_id,
            request.action_type,
            result
        )
        
        return TrackActionResponse(
            success=True,
            points_earned=result["points_earned"],
            total_points=result["total_points"],
            level=result["level"],
            current_streak=result["current_streak"],
            new_badges=result["new_badges"]
        )
        
    except Exception as e:
        logger.error(f"Failed to track user action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_progress(
    user_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Get comprehensive user progress"""
    try:
        gamification = GamificationService(db)
        progress = gamification.get_user_progress(user_id)
        
        return UserProgressResponse(**progress)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_leaderboard(
    leaderboard_type: str = "weekly",
    user_id: Optional[str] = None,
    db: DatabaseManager = Depends(get_db)
):
    """Get leaderboard for specified time period"""
    try:
        if leaderboard_type not in ["daily", "weekly", "monthly", "all_time"]:
            raise HTTPException(status_code=400, detail="Invalid leaderboard type")
        
        gamification = GamificationService(db)
        leaderboard = gamification.get_leaderboard(leaderboard_type, user_id)
        
        return LeaderboardResponse(**leaderboard)
        
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def check_user_badges(
    user_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Check and award new badges for user"""
    try:
        gamification = GamificationService(db)
        
        # Get user
        user = gamification.get_or_create_user(user_id)
        initial_points = user.total_points
        
        # Check for new badges
        new_badges = gamification._check_badges(user)
        
        # Calculate points earned from badges
        points_earned = sum(badge["points_earned"] for badge in new_badges)
        total_points = initial_points + points_earned
        
        # Check if user leveled up
        initial_level = gamification._calculate_level(initial_points)
        new_level = gamification._calculate_level(total_points)
        level_up = new_level > initial_level
        
        gamification.db.commit()
        
        return BadgeCheckResponse(
            new_badges=new_badges,
            total_points_earned=points_earned,
            level_up=level_up
        )
        
    except Exception as e:
        logger.error(f"Failed to check user badges: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_points_summary(
    user_id: str,
    days: int = 30,
    db: DatabaseManager = Depends(get_db)
):
    """Get detailed points summary for user"""
    try:
        gamification = GamificationService(db)
        
        # Get user
        user = gamification.get_or_create_user(user_id)
        
        # Get points by category
        points_by_category = {}
        from database_models import UserAction
        from sqlalchemy import func
        
        category_points = gamification.db.query(
            UserAction.action_type,
            func.sum(UserAction.points_earned).label('total_points')
        ).filter(
            UserAction.user_id == user_id
        ).group_by(UserAction.action_type).all()
        
        for action_type, points in category_points:
            points_by_category[action_type] = int(points)
        
        # Get recent points
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_actions = gamification.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.timestamp >= cutoff_date
        ).order_by(UserAction.timestamp.desc()).limit(20).all()
        
        recent_points = []
        for action in recent_actions:
            recent_points.append({
                "action_type": action.action_type,
                "points_earned": action.points_earned,
                "timestamp": action.timestamp.isoformat()
            })
        
        # Calculate level progress
        current_level = user.level
        next_level_points = current_level * current_level * 100  # Level^2 * 100
        current_level_points = (current_level - 1) * (current_level - 1) * 100
        points_in_level = user.total_points - current_level_points
        points_needed_for_next = next_level_points - current_level_points
        level_progress = min(100, (points_in_level / points_needed_for_next) * 100) if points_needed_for_next > 0 else 100
        
        level_progress_data = {
            "current_level": current_level,
            "current_points": user.total_points,
            "next_level_points": next_level_points,
            "points_in_level": points_in_level,
            "points_needed_for_next": points_needed_for_next,
            "progress_percentage": level_progress
        }
        
        return PointsSummaryResponse(
            total_points=user.total_points,
            points_by_category=points_by_category,
            recent_points=recent_points,
            level_progress=level_progress_data
        )
        
    except Exception as e:
        logger.error(f"Failed to get points summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_available_badges(
    db: DatabaseManager = Depends(get_db)
):
    """Get list of all available badges"""
    try:
        from database_models import Badge
        
        badges = db.query(Badge).filter(Badge.is_active == True).all()
        
        badge_list = []
        for badge in badges:
            badge_list.append({
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "category": badge.category,
                "points_required": badge.points_required,
                "condition_type": badge.condition_type,
                "condition_value": badge.condition_value
            })
        
        return {"badges": badge_list}
        
    except Exception as e:
        logger.error(f"Failed to get available badges: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_user(
    user_id: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    db: DatabaseManager = Depends(get_db)
):
    """Create new user"""
    try:
        gamification = GamificationService(db)
        
        # Check if user already exists
        from database_models import User
        existing_user = db.query(User).filter(User.id == user_id).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Create new user
        user = gamification.get_or_create_user(user_id, username)
        if username:
            user.username = username
        if email:
            user.email = email
        
        gamification.db.commit()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "total_points": user.total_points,
            "level": user.level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_stats(
    user_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Get user statistics"""
    try:
        gamification = GamificationService(db)
        user = gamification.get_or_create_user(user_id)
        
        # Get action counts
        from database_models import UserAction
        from sqlalchemy import func
        
        action_counts = gamification.db.query(
            UserAction.action_type,
            func.count(UserAction.id).label('count')
        ).filter(
            UserAction.user_id == user_id
        ).group_by(UserAction.action_type).all()
        
        stats = {
            "user_id": user.id,
            "username": user.username,
            "total_points": user.total_points,
            "level": user.level,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "created_at": user.created_at.isoformat(),
            "last_active": user.last_active.isoformat(),
            "action_counts": dict(action_counts),
            "total_actions": sum(count for _, count in action_counts)
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def log_gamification_activity(user_id: str, action_type: str, result: Dict[str, Any]):
    """Log gamification activity for analytics (background task)"""
    try:
        logger.info(f"Gamification activity - User: {user_id}, Action: {action_type}, Points: {result.get('points_earned', 0)}")
        # Here you could send to analytics service, log to file, etc.
    except Exception as e:
        logger.error(f"Failed to log gamification activity: {e}")

# API route definitions (to be added to main FastAPI app)
GAMIFICATION_ROUTES = [
    ("/api/v1/gamification/track", track_user_action, ["POST"]),
    ("/api/v1/gamification/user/{user_id}/progress", get_user_progress, ["GET"]),
    ("/api/v1/gamification/leaderboard/{leaderboard_type}", get_leaderboard, ["GET"]),
    ("/api/v1/gamification/user/{user_id}/badges/check", check_user_badges, ["POST"]),
    ("/api/v1/gamification/user/{user_id}/points", get_points_summary, ["GET"]),
    ("/api/v1/gamification/badges", get_available_badges, ["GET"]),
    ("/api/v1/gamification/user/create", create_user, ["POST"]),
    ("/api/v1/gamification/user/{user_id}/stats", get_user_stats, ["GET"])
]

def add_gamification_routes(app: FastAPI):
    """Add gamification routes to FastAPI app"""
    for path, endpoint, methods in GAMIFICATION_ROUTES:
        app.add_api_route(path, endpoint, methods=methods)

if __name__ == "__main__":
    # Test gamification service
    from database_models import DatabaseManager
    
    db_manager = DatabaseManager()
    db = db_manager.get_session()
    
    try:
        gamification = GamificationService(db)
        
        # Test user creation and action tracking
        result = gamification.track_action("test_user_123", "prediction", {
            "confidence": "high",
            "explanation_requested": True
        })
        
        print("Action tracking result:")
        print(f"Points earned: {result['points_earned']}")
        print(f"Total points: {result['total_points']}")
        print(f"New badges: {len(result['new_badges'])}")
        
        # Get user progress
        progress = gamification.get_user_progress("test_user_123")
        print(f"\nUser progress:")
        print(f"Level: {progress['level']}")
        print(f"Streak: {progress['current_streak']}")
        print(f"Badges: {len(progress['badges'])}")
        
    finally:
        db_manager.close_session(db)
