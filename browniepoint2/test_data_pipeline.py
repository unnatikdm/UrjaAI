"""
COIL 2000 Integration Test - No TensorFlow Required
This demonstrates the data pipeline works with real COIL 2000 data
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the browniepoint2 directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coil2000_data_pipeline import COIL2000DataPipeline
import logging

def test_coil2000_data_only():
    """Test COIL 2000 data pipeline without TensorFlow"""
    
    print("🧪 Testing COIL 2000 Data Pipeline (No TensorFlow)")
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
        
        # Show sample data
        print("\n📋 Step 4: Sample Data Preview...")
        print("✅ Training data sample:")
        print(X_train.head(3))
        
        print("\n📋 Step 5: Target Distribution...")
        print("✅ Target distribution:")
        print(y_train.value_counts())
        
        # Test preprocessing on single instance
        print("\n🔄 Step 6: Testing single instance preprocessing...")
        sample_instance = X_test.iloc[0].to_dict()
        processed_instance = pipeline.preprocess_single_instance(sample_instance)
        
        print("✅ Single instance preprocessing successful:")
        print(f"   Original features: {len(sample_instance)}")
        print(f"   Processed features: {len(processed_instance)}")
        
        # Save artifacts
        print("\n💾 Step 7: Saving preprocessing artifacts...")
        pipeline.save_preprocessing_artifacts()
        
        # Test loading artifacts
        print("\n🔄 Step 8: Testing artifact loading...")
        new_pipeline = COIL2000DataPipeline()
        new_pipeline.load_preprocessing_artifacts()
        
        print("✅ Artifact loading successful:")
        print(f"   Categorical features: {len(new_pipeline.categorical_features)}")
        print(f"   Numerical features: {len(new_pipeline.numerical_features)}")
        
        # Test data consistency
        print("\n🔍 Step 9: Testing data consistency...")
        original_processed = pipeline.preprocess_single_instance(sample_instance)
        loaded_processed = new_pipeline.preprocess_single_instance(sample_instance)
        
        consistent = True
        for key in original_processed:
            if key not in loaded_processed:
                consistent = False
                break
            if not np.allclose(original_processed[key], loaded_processed[key]):
                consistent = False
                break
        
        print(f"✅ Data consistency check: {'PASSED' if consistent else 'FAILED'}")
        
        print("\n🎉 COIL 2000 Data Pipeline Test Completed Successfully!")
        print("=" * 60)
        
        # Show feature details
        print("\n📊 Feature Details:")
        print(f"   Categorical features ({len(pipeline.categorical_features)}):")
        for i, feature in enumerate(pipeline.categorical_features[:10]):  # Show first 10
            vocab_size = len(pipeline.feature_vocab.get(feature, []))
            print(f"     {i+1}. {feature} (vocab size: {vocab_size})")
        
        if len(pipeline.categorical_features) > 10:
            print(f"     ... and {len(pipeline.categorical_features) - 10} more")
        
        print(f"\n   Numerical features ({len(pipeline.numerical_features)}):")
        for i, feature in enumerate(pipeline.numerical_features[:10]):  # Show first 10
            print(f"     {i+1}. {feature}")
        
        if len(pipeline.numerical_features) > 10:
            print(f"     ... and {len(pipeline.numerical_features) - 10} more")
        
        return True
        
    except Exception as e:
        print(f"\n❌ COIL 2000 Data Pipeline Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_business_value():
    """Demonstrate the business value of COIL 2000 dataset"""
    
    print("\n💼 Business Value Demonstration")
    print("=" * 40)
    
    print("📋 COIL 2000 Insurance Dataset:")
    print("   • Source: Real insurance company data")
    print("   • Task: Predict CARAVAN insurance ownership")
    print("   • Business: Customer targeting for insurance products")
    print("   • Features: 86 customer attributes")
    print("   • Samples: 5,822 real customers")
    
    print("\n🎯 Business Applications:")
    print("   • Identify high-potential insurance customers")
    print("   • Optimize marketing campaigns")
    print("   • Reduce customer acquisition costs")
    print("   • Personalize product offerings")
    
    print("\n🔍 Model Explainability Benefits:")
    print("   • Understand customer risk factors")
    print("   • Comply with insurance regulations")
    print("   • Explain decisions to stakeholders")
    print("   • Improve underwriting processes")
    
    print("\n🎮 Gamification Benefits:")
    print("   • Train sales teams on customer profiling")
    print("   • Engage employees in learning")
    print("   • Competition drives better predictions")
    print("   • Track performance over time")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run data pipeline test
    success = test_coil2000_data_only()
    
    if success:
        # Show business value
        demonstrate_business_value()
        
        print(f"\n🚀 Ready for TensorFlow Integration!")
        print(f"   Install TensorFlow: pip install tensorflow")
        print(f"   Run full test: python test_coil2000.py")
        print(f"   Start API: python main_app.py")
    else:
        print(f"\n❌ Data pipeline test failed. Check the errors above.")
