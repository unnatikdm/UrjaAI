import shap
import numpy as np
import pandas as pd
try:
    import tensorflow as tf
except ImportError:
    tf = None
from typing import Dict, List, Any, Optional
import logging
import pickle
import os
from datetime import datetime
import uuid

class SHAPExplainer:
    """SHAP explanation service for TabTransformer models"""
    
    def __init__(self, model, data_pipeline, background_samples: int = 100):
        self.model = model
        self.data_pipeline = data_pipeline
        self.background_samples = background_samples
        self.explainer = None
        self.background_data = None
        self.expected_value = None
        
        self.logger = logging.getLogger(__name__)
    
    def prepare_background_data(self, X_background: pd.DataFrame = None):
        """Prepare background data for SHAP explainer"""
        if X_background is None:
            # Generate sample background data
            self.logger.info("Generating background data...")
            X_background, _ = self.data_pipeline.prepare_data()
            X_background = X_background.sample(n=min(self.background_samples, len(X_background)), random_state=42)
        
        # Preprocess background data
        self.background_data = {}
        for feature in self.data_pipeline.categorical_features:
            self.background_data[feature] = X_background[feature].values
        
        for feature in self.data_pipeline.numerical_features:
            self.background_data[feature] = X_background[feature].values
        
        self.logger.info(f"Background data prepared with {len(X_background)} samples")
        return self.background_data
    
    def initialize_explainer(self):
        """Initialize SHAP KernelExplainer"""
        if self.background_data is None:
            self.prepare_background_data()
        
        self.logger.info("Initializing SHAP KernelExplainer...")
        
        # Define prediction function for SHAP
        def model_predict(data_dict):
            return self.model.model.predict(data_dict, verbose=0)
        
        # Initialize KernelExplainer
        self.explainer = shap.KernelExplainer(
            model_predict,
            self.background_data,
            link="logit"
        )
        
        # Calculate expected value
        self.expected_value = self.explainer.expected_value
        
        self.logger.info("SHAP explainer initialized successfully")
    
    def explain_instance(self, instance_data: Dict[str, Any], top_k: int = 10) -> Dict[str, Any]:
        """Generate SHAP explanation for a single instance"""
        if self.explainer is None:
            self.initialize_explainer()
        
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        try:
            # Preprocess instance
            processed_instance = self.data_pipeline.preprocess_single_instance(instance_data)
            
            # Get model prediction
            class_label, probability = self.model.predict(instance_data)
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(processed_instance, nsamples=100)
            
            # Extract SHAP values for the positive class
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Positive class
            
            # Prepare feature importance data
            feature_importance = []
            all_features = (self.data_pipeline.categorical_features + 
                          self.data_pipeline.numerical_features)
            
            for i, feature in enumerate(all_features):
                if i < len(shap_values):
                    feature_value = instance_data.get(feature, 0)
                    shap_value = float(shap_values[i])
                    contribution = "positive" if shap_value > 0 else "negative"
                    
                    feature_importance.append({
                        "feature": feature,
                        "value": feature_value,
                        "shap_value": shap_value,
                        "contribution": contribution,
                        "abs_shap_value": abs(shap_value)
                    })
            
            # Sort by absolute SHAP value
            feature_importance.sort(key=lambda x: x['abs_shap_value'], reverse=True)
            
            # Get top features
            top_features = feature_importance[:top_k]
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Prepare waterfall data
            waterfall_data = []
            cumulative_shap = 0
            
            for feature_info in top_features:
                cumulative_shap += feature_info['shap_value']
                waterfall_data.append({
                    "feature": feature_info['feature'],
                    "value": feature_info['value'],
                    "shap_value": feature_info['shap_value'],
                    "contribution": feature_info['contribution'],
                    "cumulative_shap": cumulative_shap,
                    "cumulative_probability": self._shap_to_probability(cumulative_shap + self.expected_value)
                })
            
            # Prepare response
            explanation = {
                "request_id": request_id,
                "expected_value": float(self.expected_value),
                "prediction": class_label,
                "prediction_probability": probability,
                "base_probability": self._shap_to_probability(self.expected_value),
                "processing_time_ms": processing_time,
                "feature_importance": feature_importance,
                "top_features": top_features,
                "waterfall_data": waterfall_data,
                "summary": {
                    "total_features": len(feature_importance),
                    "positive_contributors": len([f for f in feature_importance if f['contribution'] == 'positive']),
                    "negative_contributors": len([f for f in feature_importance if f['contribution'] == 'negative']),
                    "max_shap_value": max(f['shap_value'] for f in feature_importance),
                    "min_shap_value": min(f['shap_value'] for f in feature_importance)
                }
            }
            
            self.logger.info(f"SHAP explanation generated in {processing_time:.2f}ms")
            return explanation
            
        except Exception as e:
            self.logger.error(f"SHAP explanation failed: {e}")
            raise
    
    def explain_batch(self, instances: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """Generate SHAP explanations for multiple instances"""
        explanations = []
        
        for i, instance in enumerate(instances):
            try:
                explanation = self.explain_instance(instance, top_k)
                explanation['instance_id'] = i
                explanations.append(explanation)
            except Exception as e:
                self.logger.error(f"Failed to explain instance {i}: {e}")
                explanations.append({
                    "instance_id": i,
                    "error": str(e),
                    "request_id": str(uuid.uuid4())
                })
        
        return explanations
    
    def _shap_to_probability(self, shap_value: float) -> float:
        """Convert SHAP value to probability using sigmoid"""
        return 1 / (1 + np.exp(-shap_value))
    
    def get_feature_summary(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get feature importance summary across multiple instances"""
        all_shap_values = []
        all_features = (self.data_pipeline.categorical_features + 
                       self.data_pipeline.numerical_features)
        
        # Collect SHAP values for all instances
        for instance in instances:
            try:
                explanation = self.explain_instance(instance)
                feature_importance = explanation['feature_importance']
                
                for feature_info in feature_importance:
                    all_shap_values.append({
                        'feature': feature_info['feature'],
                        'shap_value': feature_info['shap_value'],
                        'abs_shap_value': feature_info['abs_shap_value']
                    })
            except Exception as e:
                self.logger.warning(f"Failed to get SHAP values for instance: {e}")
                continue
        
        if not all_shap_values:
            return {"error": "No valid SHAP values calculated"}
        
        # Calculate summary statistics for each feature
        feature_summary = {}
        for feature in all_features:
            feature_shap_values = [sv for sv in all_shap_values if sv['feature'] == feature]
            
            if feature_shap_values:
                shap_vals = [sv['shap_value'] for sv in feature_shap_values]
                abs_shap_vals = [sv['abs_shap_value'] for sv in feature_shap_values]
                
                feature_summary[feature] = {
                    "mean_shap_value": np.mean(shap_vals),
                    "std_shap_value": np.std(shap_vals),
                    "mean_abs_shap_value": np.mean(abs_shap_vals),
                    "max_shap_value": np.max(shap_vals),
                    "min_shap_value": np.min(shap_vals),
                    "importance_rank": None  # Will be filled later
                }
        
        # Rank features by mean absolute SHAP value
        ranked_features = sorted(
            feature_summary.items(),
            key=lambda x: x[1]['mean_abs_shap_value'],
            reverse=True
        )
        
        for i, (feature, summary) in enumerate(ranked_features):
            feature_summary[feature]['importance_rank'] = i + 1
        
        return {
            "feature_summary": feature_summary,
            "total_instances": len(instances),
            "successful_explanations": len(all_shap_values) // len(all_features),
            "top_features": ranked_features[:10]
        }
    
    def save_explainer(self, save_path: str):
        """Save SHAP explainer state"""
        explainer_data = {
            'expected_value': self.expected_value,
            'background_samples': self.background_samples,
            'data_pipeline_info': {
                'categorical_features': self.data_pipeline.categorical_features,
                'numerical_features': self.data_pipeline.numerical_features,
                'feature_vocab': self.data_pipeline.feature_vocab
            }
        }
        
        os.makedirs(save_path, exist_ok=True)
        with open(os.path.join(save_path, 'shap_explainer.pkl'), 'wb') as f:
            pickle.dump(explainer_data, f)
        
        self.logger.info(f"SHAP explainer state saved to {save_path}")
    
    def load_explainer(self, load_path: str):
        """Load SHAP explainer state"""
        explainer_path = os.path.join(load_path, 'shap_explainer.pkl')
        
        if os.path.exists(explainer_path):
            with open(explainer_path, 'rb') as f:
                explainer_data = pickle.load(f)
            
            self.expected_value = explainer_data['expected_value']
            self.background_samples = explainer_data['background_samples']
            
            # Re-initialize explainer
            self.initialize_explainer()
            
            self.logger.info(f"SHAP explainer state loaded from {load_path}")
        else:
            self.logger.warning("No saved explainer state found, initializing new explainer")
            self.initialize_explainer()

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # This would be used with the trained model
    from tabtransformer_model import TabTransformerModel
    
    # Load trained model
    model = TabTransformerModel()
    model.load_model('models/tabtransformer_v1')
    
    # Initialize SHAP explainer
    explainer = SHAPExplainer(model, model.pipeline)
    
    # Test explanation
    test_instance = {
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
    
    # Generate explanation
    explanation = explainer.explain_instance(test_instance)
    print("SHAP Explanation:")
    print(f"Prediction: {explanation['prediction']}")
    print(f"Probability: {explanation['prediction_probability']:.3f}")
    print(f"Top feature: {explanation['top_features'][0]['feature']}")
    print(f"SHAP value: {explanation['top_features'][0]['shap_value']:.3f}")
