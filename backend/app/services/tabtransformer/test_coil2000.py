import asyncio
import sys
import os

# Add the browniepoint2 directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coil2000_data_pipeline import COIL2000DataPipeline
from tabtransformer_model import TabTransformerModel
import logging

async def test_coil2000_integration():
    """Test COIL 2000 dataset integration with TabTransformer"""
    
    print("🧪 Testing COIL 2000 Integration with TabTransformer")
    print("=" * 60)
    
    try:
        # Initialize data pipeline
        print("\n📊 Step 1: Initialize COIL 2000 Data Pipeline...")
        pipeline = COIL2000DataPipeline()
        
        # Prepare data
        print("📊 Step 2: Preparing COIL 2000 dataset...")
        X, y = pipeline.prepare_data()
        
        # Get data summary
        summary = pipeline.get_data_summary()
        print("✅ COIL 2000 Dataset Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # Split data
        print("\n📊 Step 3: Splitting data...")
        X_train, X_val, X_test, y_train, y_val, y_test = pipeline.split_data(X, y)
        
        print(f"✅ Data split completed:")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Validation samples: {len(X_val)}")
        print(f"   Test samples: {len(X_test)}")
        print(f"   Categorical features: {len(pipeline.categorical_features)}")
        print(f"   Numerical features: {len(pipeline.numerical_features)}")
        
        # Initialize TabTransformer model
        print("\n🤖 Step 4: Initializing TabTransformer Model...")
        model = TabTransformerModel()
        
        # Build model
        print("🤖 Step 5: Building TabTransformer architecture...")
        model.build_model()
        
        print(f"✅ Model built successfully:")
        print(f"   Total parameters: {model.model.count_params():,}")
        print(f"   Embedding dimension: {model.config['embedding_dim']}")
        print(f"   Depth: {model.config['depth']}")
        print(f"   Attention heads: {model.config['heads']}")
        
        # Create TensorFlow datasets
        print("\n📊 Step 6: Creating TensorFlow datasets...")
        train_dataset = pipeline.create_tf_dataset(X_train, y_train)
        val_dataset = pipeline.create_tf_dataset(X_val, y_val, shuffle=False)
        
        print("✅ TensorFlow datasets created successfully")
        
        # Test single prediction
        print("\n🎯 Step 7: Testing single prediction...")
        sample_instance = X_test.iloc[0].to_dict()
        class_label, probability = model.predict(sample_instance)
        
        print(f"✅ Single prediction successful:")
        print(f"   Prediction: {class_label}")
        print(f"   Probability: {probability:.4f}")
        print(f"   Class: {'Has Insurance' if class_label == 1 else 'No Insurance'}")
        print(f"   Confidence: {'High' if probability > 0.8 else 'Medium' if probability > 0.6 else 'Low'}")
        
        # Test batch prediction
        print("\n📦 Step 8: Testing batch prediction...")
        batch_instances = X_test.head(5).to_dict('records')
        batch_predictions = model.predict_batch(batch_instances)
        
        print(f"✅ Batch prediction successful:")
        print(f"   Batch size: {len(batch_instances)}")
        print(f"   Predictions: {len(batch_predictions)}")
        
        for i, (pred, prob) in enumerate(batch_predictions):
            print(f"   Instance {i+1}: {pred} ({prob:.4f})")
        
        # Save model and artifacts
        print("\n💾 Step 9: Saving model and artifacts...")
        model_path = model.save_model()
        
        print(f"✅ Model saved to: {model_path}")
        print(f"✅ Preprocessing artifacts saved")
        
        # Test model loading
        print("\n🔄 Step 10: Testing model loading...")
        new_model = TabTransformerModel()
        new_model.load_model(model_path)
        
        # Test prediction with loaded model
        loaded_pred, loaded_prob = new_model.predict(sample_instance)
        
        print(f"✅ Model loading and prediction successful:")
        print(f"   Original prediction: {class_label} ({probability:.4f})")
        print(f"   Loaded model prediction: {loaded_pred} ({loaded_prob:.4f})")
        print(f"   Predictions match: {class_label == loaded_pred and abs(probability - loaded_prob) < 1e-6}")
        
        print("\n🎉 COIL 2000 Integration Test Completed Successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ COIL 2000 Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_coil2000_integration())
