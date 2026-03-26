import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add the browniepoint2 directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_app import app
from tabtransformer_model import TabTransformerModel
from shap_service import SHAPExplainer
from gamification_service import GamificationService
from database_models import DatabaseManager

class TestTabTransformerIntegration:
    """Comprehensive integration tests for TabTransformer platform"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_user_id = "test_user_integration"
        self.sample_features = {
            'age': 39,
            'workclass': 'State-gov',
            'education': 'Bachelors',
            'marital_status': 'Never-married',
            'occupation': 'Adm-clerical',
            'relationship': 'Not-in-family',
            'race': 'White',
            'gender': 'Male',
            'capital_gain': 2174,
            'capital_loss': 0,
            'hours_per_week': 40,
            'native_country': 'United-States'
        }
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Starting TabTransformer Integration Tests")
        print("=" * 60)
        
        test_results = []
        
        # Test 1: Health Check
        result = await self.test_health_check()
        test_results.append(("Health Check", result))
        
        # Test 2: Model Information
        result = await self.test_model_info()
        test_results.append(("Model Information", result))
        
        # Test 3: Basic Prediction
        result = await self.test_basic_prediction()
        test_results.append(("Basic Prediction", result))
        
        # Test 4: Prediction with Explanation
        result = await self.test_prediction_with_explanation()
        test_results.append(("Prediction with Explanation", result))
        
        # Test 5: Batch Prediction
        result = await self.test_batch_prediction()
        test_results.append(("Batch Prediction", result))
        
        # Test 6: SHAP Waterfall Explanation
        result = await self.test_waterfall_explanation()
        test_results.append(("SHAP Waterfall Explanation", result))
        
        # Test 7: Gamification - User Creation
        result = await self.test_user_creation()
        test_results.append(("User Creation", result))
        
        # Test 8: Gamification - Action Tracking
        result = await self.test_action_tracking()
        test_results.append(("Action Tracking", result))
        
        # Test 9: Gamification - User Progress
        result = await self.test_user_progress()
        test_results.append(("User Progress", result))
        
        # Test 10: Gamification - Leaderboard
        result = await self.test_leaderboard()
        test_results.append(("Leaderboard", result))
        
        # Test 11: Comprehensive Prediction
        result = await self.test_comprehensive_prediction()
        test_results.append(("Comprehensive Prediction", result))
        
        # Test 12: Feature Summary
        result = await self.test_feature_summary()
        test_results.append(("Feature Summary", result))
        
        # Print results
        self.print_test_results(test_results)
        
        return test_results
    
    async def test_health_check(self):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Check...")
        try:
            response = self.client.get("/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Model loaded: {data.get('model_loaded')}")
                print(f"   SHAP ready: {data.get('shap_explainer_ready')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_model_info(self):
        """Test model information endpoint"""
        print("\n📊 Testing Model Information...")
        try:
            response = self.client.get("/info")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Model info retrieved")
                print(f"   Model type: {data.get('model_info', {}).get('model_type')}")
                print(f"   Parameters: {data.get('model_info', {}).get('parameters'):,}")
                print(f"   Total features: {data.get('features', {}).get('total_features')}")
                print(f"   Badges available: {data.get('badges_count')}")
                return True
            else:
                print(f"❌ Model info failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Model info error: {e}")
            return False
    
    async def test_basic_prediction(self):
        """Test basic prediction endpoint"""
        print("\n🎯 Testing Basic Prediction...")
        try:
            request_data = {
                "features": self.sample_features
            }
            
            response = self.client.post("/api/v1/predict", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Basic prediction successful")
                print(f"   Prediction: {data.get('prediction')}")
                print(f"   Class: {data.get('prediction_class')}")
                print(f"   Probability: {data.get('probability'):.3f}")
                print(f"   Confidence: {data.get('confidence')}")
                print(f"   Processing time: {data.get('processing_time_ms'):.2f}ms")
                return True
            else:
                print(f"❌ Basic prediction failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Basic prediction error: {e}")
            return False
    
    async def test_prediction_with_explanation(self):
        """Test prediction with explanation"""
        print("\n🔍 Testing Prediction with Explanation...")
        try:
            request_data = {
                "features": self.sample_features,
                "explain": True,
                "user_id": self.test_user_id
            }
            
            response = self.client.post("/api/v1/predict", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                has_explanation = "explanation" in data and data["explanation"] is not None
                
                print(f"✅ Prediction with explanation successful")
                print(f"   Prediction: {data.get('prediction')}")
                print(f"   Explanation included: {has_explanation}")
                
                if has_explanation:
                    explanation = data["explanation"]
                    print(f"   Top feature: {explanation.get('top_features', [{}])[0].get('feature', 'N/A')}")
                
                return True
            else:
                print(f"❌ Prediction with explanation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Prediction with explanation error: {e}")
            return False
    
    async def test_batch_prediction(self):
        """Test batch prediction"""
        print("\n📦 Testing Batch Prediction...")
        try:
            batch_features = [self.sample_features] * 3
            
            request_data = {
                "instances": batch_features,
                "user_id": self.test_user_id
            }
            
            response = self.client.post("/api/v1/predict/batch", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', [])
                
                print(f"✅ Batch prediction successful")
                print(f"   Total processed: {data.get('total_processed')}")
                print(f"   Predictions returned: {len(predictions)}")
                print(f"   Processing time: {data.get('processing_time_ms'):.2f}ms")
                
                return len(predictions) == 3
            else:
                print(f"❌ Batch prediction failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Batch prediction error: {e}")
            return False
    
    async def test_waterfall_explanation(self):
        """Test SHAP waterfall explanation"""
        print("\n💧 Testing SHAP Waterfall Explanation...")
        try:
            request_data = {
                "features": self.sample_features,
                "top_k": 5,
                "user_id": self.test_user_id
            }
            
            response = self.client.post("/api/v1/explain/waterfall", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                has_waterfall = "waterfall_data" in data
                
                print(f"✅ Waterfall explanation successful")
                print(f"   Request ID: {data.get('request_id')}")
                print(f"   Prediction: {data.get('prediction')}")
                print(f"   Waterfall data: {has_waterfall}")
                
                if has_waterfall:
                    waterfall_data = data.get('waterfall_data', [])
                    print(f"   Waterfall steps: {len(waterfall_data)}")
                
                return True
            else:
                print(f"❌ Waterfall explanation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Waterfall explanation error: {e}")
            return False
    
    async def test_user_creation(self):
        """Test user creation"""
        print("\n👤 Testing User Creation...")
        try:
            request_data = {
                "user_id": self.test_user_id,
                "username": "integration_test_user",
                "email": "test@example.com"
            }
            
            response = self.client.post("/api/v1/gamification/user/create", json=request_data)
            
            if response.status_code in [200, 409]:  # 409 means user already exists
                print(f"✅ User creation successful (user exists or created)")
                return True
            else:
                print(f"❌ User creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ User creation error: {e}")
            return False
    
    async def test_action_tracking(self):
        """Test action tracking"""
        print("\n📈 Testing Action Tracking...")
        try:
            request_data = {
                "user_id": self.test_user_id,
                "action_type": "prediction",
                "action_data": {
                    "confidence": "high",
                    "explanation_requested": True
                }
            }
            
            response = self.client.post("/api/v1/gamification/track", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Action tracking successful")
                print(f"   Points earned: {data.get('points_earned')}")
                print(f"   Total points: {data.get('total_points')}")
                print(f"   Level: {data.get('level')}")
                print(f"   New badges: {len(data.get('new_badges', []))}")
                
                return True
            else:
                print(f"❌ Action tracking failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Action tracking error: {e}")
            return False
    
    async def test_user_progress(self):
        """Test user progress retrieval"""
        print("\n📊 Testing User Progress...")
        try:
            response = self.client.get(f"/api/v1/gamification/user/{self.test_user_id}/progress")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User progress retrieved")
                print(f"   Username: {data.get('username')}")
                print(f"   Total points: {data.get('total_points')}")
                print(f"   Level: {data.get('level')}")
                print(f"   Current streak: {data.get('current_streak')}")
                print(f"   Badges earned: {len(data.get('badges', []))}")
                
                return True
            else:
                print(f"❌ User progress failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ User progress error: {e}")
            return False
    
    async def test_leaderboard(self):
        """Test leaderboard retrieval"""
        print("\n🏆 Testing Leaderboard...")
        try:
            response = self.client.get("/api/v1/gamification/leaderboard/weekly")
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get('entries', [])
                
                print(f"✅ Leaderboard retrieved")
                print(f"   Leaderboard type: {data.get('leaderboard_type')}")
                print(f"   Total entries: {len(entries)}")
                
                if entries:
                    print(f"   Top user: {entries[0].get('username')} ({entries[0].get('total_points')} points)")
                
                return True
            else:
                print(f"❌ Leaderboard failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Leaderboard error: {e}")
            return False
    
    async def test_comprehensive_prediction(self):
        """Test comprehensive prediction endpoint"""
        print("\n🚀 Testing Comprehensive Prediction...")
        try:
            request_data = {
                "features": self.sample_features,
                "explain": True,
                "user_id": self.test_user_id,
                "top_k_features": 5
            }
            
            response = self.client.post("/api/v1/predict/comprehensive", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Comprehensive prediction successful")
                print(f"   Request ID: {data.get('request_id')}")
                print(f"   Prediction: {data.get('prediction')}")
                print(f"   Probability: {data.get('probability'):.3f}")
                print(f"   Explanation included: {data.get('explanation') is not None}")
                print(f"   Gamification included: {data.get('gamification') is not None}")
                print(f"   Processing time: {data.get('processing_time_ms'):.2f}ms")
                
                return True
            else:
                print(f"❌ Comprehensive prediction failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Comprehensive prediction error: {e}")
            return False
    
    async def test_feature_summary(self):
        """Test feature summary endpoint"""
        print("\n📋 Testing Feature Summary...")
        try:
            response = self.client.get("/api/v1/features/summary")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Feature summary retrieved")
                print(f"   Categorical features: {len(data.get('categorical_features', []))}")
                print(f"   Numerical features: {len(data.get('numerical_features', []))}")
                
                if 'feature_summary' in data:
                    summary = data['feature_summary']
                    print(f"   Feature summary available: {len(summary.get('feature_summary', {}))}")
                
                return True
            else:
                print(f"❌ Feature summary failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Feature summary error: {e}")
            return False
    
    def print_test_results(self, test_results):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🏁 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total tests: {len(test_results)}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success rate: {(passed/len(test_results))*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed! Your TabTransformer platform is ready!")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Check the logs above.")

# Main execution
async def main():
    """Run all integration tests"""
    tester = TestTabTransformerIntegration()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
