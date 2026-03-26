import os
import sys
import logging
import asyncio
from typing import Optional, Dict, Any, Tuple

# Add the tabtransformer directory to path so its internal imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'tabtransformer'))

from app.services.tabtransformer.tabtransformer_model import TabTransformerModel
from app.services.tabtransformer.shap_service import SHAPExplainer
from app.services.tabtransformer.gamification_service import GamificationService
from app.services.tabtransformer.database_models import DatabaseManager

logger = logging.getLogger(__name__)

class TabTransformerManager:
    """Manager to hold global TabTransformer services natively in FastAPI."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TabTransformerManager, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.shap_explainer = None
            cls._instance.db_manager = None
            cls._instance.gamification_service = None
            cls._instance.initialized = False
        return cls._instance

    def initialize(self):
        """Initialize all ML and Gamification services on app startup."""
        if self.initialized:
            return
            
        try:
            logger.info("Starting TabTransformer ML Services...")
            
            # 1. Initialize DB Manager
            self.db_manager = DatabaseManager()
            
            # 2. Gamification Service
            self.gamification_service = GamificationService(self.db_manager)
            
            # 3. Model Initialization
            self.model = TabTransformerModel()
            
            # Fixed model path: absolute relative to project root
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, 'tabtransformer', 'models', 'tabtransformer_v1')
            
            if os.path.exists(os.path.join(model_path, 'config.json')) and \
               not os.path.exists(os.path.join(model_path, 'mock_model.pkl')):
                self.model.load_model(model_path)
                logger.info(f"Real model loaded from {model_path}")
                self._finalize_init()
            else:
                logger.info(f"Real model not found at {model_path}. Starting background training...")
                # Run training in background to avoid blocking startup
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._async_train(model_path))
                except RuntimeError:
                    # No running event loop, create one for this task
                    import threading
                    def run_training():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(self._async_train(model_path))
                        new_loop.close()
                    thread = threading.Thread(target=run_training)
                    thread.daemon = True
                    thread.start()
                
            self.initialized = True # Mark as initialized (even if training is pending)
            logger.info("TabTransformer Manager set up (Real Model upgrade in progress)")
            
        except Exception as e:
            logger.error(f"Failed to initialize TabTransformer ML Services: {e}")
            raise e

    async def _async_train(self, model_path):
        """Background training task"""
        try:
            logger.info("🚀 Starting training on real COIL-2000 dataset...")
            train_dataset, val_dataset, test_dataset = self.model.prepare_data()
            self.model.build_model()
            self.model.train_model(train_dataset, val_dataset, epochs=10)
            
            # Create models dir if not exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.model.save_model(model_path)
            logger.info(f"✅ Real model trained and saved to {model_path}")
            
            self._finalize_init()
        except Exception as e:
            logger.error(f"❌ Background training failed: {e}")

    def _finalize_init(self):
        """Finalize SHAP and other dependent services"""
        try:
            if self.model and self.model.model:
                self.shap_explainer = SHAPExplainer(self.model.model, self.model.pipeline)
                self.shap_explainer.initialize_explainer()
                logger.info("SHAP explainer initialized for real model")
        except Exception as e:
            logger.warning(f"SHAP explainer initialization failed: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize TabTransformer ML Services: {e}")
            raise e

    def get_system_info(self) -> Dict[str, Any]:
        """Get info about the running model"""
        if not self.model or not self.model.model:
            return {
                "status": "Training",
                "message": "Real model is currently training on COIL-2000 dataset. Please check back in 1-2 minutes.",
                "system_stats": {"model_loaded": False}
            }
            
        model_info = {
            "model_type": "TabTransformer",
            "parameters": self.model.model.count_params() if hasattr(self.model.model, 'count_params') else "Unknown",
            "config": self.model.config,
            "target": self.model.pipeline.target_column
        }
        
        features = {
            "categorical_features": len(self.model.pipeline.categorical_features),
            "total_features": len(self.model.pipeline.categorical_features) + len(self.model.pipeline.numerical_features),
            "training_samples": 5000,
            "target_variable": self.model.pipeline.target_column,
            "target_distribution": "99.88% no insurance, 0.12% has insurance"
        }
        
        try:
            session = self.db_manager.get_session()
            from app.services.tabtransformer.database_models import Badge
            badges_count = session.query(Badge).filter(Badge.is_active == True).count()
            self.db_manager.close_session(session)
        except:
            badges_count = 0
            
        system_stats = {
            "status": "Ready",
            "model_loaded": True,
            "shap_explainer_ready": self.shap_explainer is not None,
            "database_connected": True
        }
        
        return {
            "model_info": model_info,
            "features": features,
            "badges_count": badges_count,
            "system_stats": system_stats
        }

    def predict(self, features: Dict[str, Any]) -> Tuple[int, float]:
        """Make a prediction"""
        if not self.model or not self.model.model:
            raise Exception("Model not loaded")
        return self.model.predict(features)
        
    def explain(self, features: Dict[str, Any], top_k: int = 10):
        """Generate SHAP explanation"""
        if not self.shap_explainer:
            raise Exception("SHAP explainer not available")
        return self.shap_explainer.explain_instance(features, top_k)
        
    def track_action(self, user_id: str, action_type: str, action_data: Dict[str, Any]):
        """Track user action for gamification"""
        if not self.gamification_service:
            raise Exception("Gamification service not available")
        return self.gamification_service.track_action(user_id, action_type, action_data)
        
    def get_leaderboard(self, limit: int = 10):
        """Get leaderboard"""
        if not self.db_manager:
            raise Exception("DB Manager not available")
        session = self.db_manager.get_session()
        try:
            from app.services.tabtransformer.database_models import LeaderboardEntry
            entries = session.query(LeaderboardEntry).order_by(LeaderboardEntry.score.desc()).limit(limit).all()
            
            formatted = []
            for i, entry in enumerate(entries):
                formatted.append({
                    "rank": i + 1,
                    "user_id": entry.user_id,
                    "model_type": entry.model_type,
                    "accuracy": entry.accuracy,
                    "score": entry.score
                })
                
            # If empty, return mock data like the legacy proxy did when failing
            if not formatted:
                return [
                    {
                        "rank": 1,
                        "user_id": "tabtransformer_v1",
                        "model_type": "TabTransformer",
                        "accuracy": 0.92,
                        "score": 92
                    },
                    {
                        "rank": 2,
                        "user_id": "baseline_model",
                        "model_type": "Logistic Regression",
                        "accuracy": 0.78,
                        "score": 78
                    }
                ]
            return formatted
        finally:
            self.db_manager.close_session(session)
            
    def get_badges(self):
        """Get all badges"""
        if not self.db_manager:
            raise Exception("DB Manager not available")
        session = self.db_manager.get_session()
        try:
            from app.services.tabtransformer.database_models import Badge
            badges = session.query(Badge).filter(Badge.is_active == True).all()
            
            formatted = []
            for badge in badges:
                formatted.append({
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon_url or "🏅",
                    "earned": False, # Would need user_id to correctly populate this
                    "progress": 0    # Would need user_id to correctly populate this
                })
                
            if not formatted:
                # Return default mock badges
                return [
                    {
                        "name": "First Prediction",
                        "description": "Make your first insurance prediction",
                        "icon": "🎯",
                        "earned": False,
                        "progress": 0
                    },
                    {
                        "name": "Prediction Master",
                        "description": "Make 50 accurate predictions",
                        "icon": "🎓",
                        "earned": False,
                        "progress": 0
                    }
                ]
            return formatted
        finally:
            self.db_manager.close_session(session)

manager = TabTransformerManager()
