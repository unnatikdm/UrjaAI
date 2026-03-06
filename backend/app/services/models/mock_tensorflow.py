"""
Mock TensorFlow Implementation for Testing
This allows us to test the TabTransformer system without actual TensorFlow
"""

import numpy as np
import pandas as pd
import os
from typing import Dict, List, Tuple, Any
import logging
from scipy.special import softmax

class MockTabTransformer:
    """Mock TabTransformer model for testing without TensorFlow"""
    
    def __init__(self, numerical_features, categorical_features, 
                 categorical_cardinalities, embedding_dim=16, depth=4, 
                 heads=8, attn_dropout=0.1, ff_dropout=0.1, 
                 mlp_hidden_factors=None):
        self.numerical_features = numerical_features
        self.categorical_features = categorical_features
        self.categorical_cardinalities = categorical_cardinalities
        self.embedding_dim = embedding_dim
        self.depth = depth
        self.heads = heads
        self.attn_dropout = attn_dropout
        self.ff_dropout = ff_dropout
        self.mlp_hidden_factors = mlp_hidden_factors or [2, 1]
        
        # Mock parameters
        self.params = {
            'embedding_weights': {},
            'attention_weights': {},
            'mlp_weights': {}
        }
        
        # Initialize mock weights
        self._initialize_weights()
        
        self.logger = logging.getLogger(__name__)
    
    def _initialize_weights(self):
        """Initialize mock weights for the model"""
        np.random.seed(42)
        
        # Embedding weights for each categorical feature
        for i, feature in enumerate(self.categorical_features):
            vocab_size = self.categorical_cardinalities[i]
            self.params['embedding_weights'][feature] = np.random.randn(
                vocab_size, self.embedding_dim
            ) * 0.1
        
        # Mock attention and MLP weights
        total_features = len(self.categorical_features) + len(self.numerical_features)
        hidden_dim = total_features * self.embedding_dim
        
        self.params['attention_weights']['query'] = np.random.randn(
            hidden_dim, hidden_dim
        ) * 0.1
        self.params['attention_weights']['key'] = np.random.randn(
            hidden_dim, hidden_dim
        ) * 0.1
        self.params['attention_weights']['value'] = np.random.randn(
            hidden_dim, hidden_dim
        ) * 0.1
        
        # MLP weights
        mlp_dims = [
            hidden_dim * self.mlp_hidden_factors[0],
            hidden_dim * self.mlp_hidden_factors[1],
            1  # Output
        ]
        
        for i in range(len(mlp_dims) - 1):
            self.params['mlp_weights'][f'layer_{i}'] = np.random.randn(
                mlp_dims[i], mlp_dims[i + 1]
            ) * 0.1
    
    def _embed_categorical_features(self, data_dict):
        """Embed categorical features"""
        embeddings = []
        
        for feature in self.categorical_features:
            if feature in data_dict:
                feature_values = data_dict[feature]
                if isinstance(feature_values, np.ndarray):
                    feature_values = feature_values.flatten()
                
                # Simple embedding lookup
                vocab_size = len(self.params['embedding_weights'][feature])
                feature_values = np.clip(feature_values, 0, vocab_size - 1).astype(int)
                
                embedded = self.params['embedding_weights'][feature][feature_values]
                embeddings.append(embedded)
        
        return np.concatenate(embeddings, axis=-1) if embeddings else np.array([])
    
    def _forward_pass(self, data_dict):
        """Mock forward pass through the model"""
        # Embed categorical features
        if self.categorical_features:
            cat_embedded = self._embed_categorical_features(data_dict)
        else:
            cat_embedded = np.array([])
        
        # Add numerical features
        if self.numerical_features:
            num_features = []
            for feature in self.numerical_features:
                if feature in data_dict:
                    values = data_dict[feature]
                    if isinstance(values, np.ndarray):
                        values = values.flatten()
                    num_features.append(values.reshape(-1, 1))
            
            if num_features:
                num_features = np.concatenate(num_features, axis=-1)
                if cat_embedded.size > 0:
                    combined = np.concatenate([cat_embedded, num_features], axis=-1)
                else:
                    combined = num_features
            else:
                combined = cat_embedded
        else:
            combined = cat_embedded
        
        # Mock attention mechanism (simplified)
        hidden_dim = combined.shape[-1]
        
        # Self-attention (simplified)
        query = np.dot(combined, self.params['attention_weights']['query'])
        key = np.dot(combined, self.params['attention_weights']['key'])
        value = np.dot(combined, self.params['attention_weights']['value'])
        
        # Attention scores (simplified)
        attention_scores = np.dot(query, key.T) / np.sqrt(hidden_dim)
        attention_weights = softmax(attention_scores, axis=-1)
        attended = np.dot(attention_weights, value)
        
        # MLP layers (simplified)
        hidden = attended
        for i in range(len(self.params['mlp_weights'])):
            layer_name = f'layer_{i}'
            hidden = np.dot(hidden, self.params['mlp_weights'][layer_name])
            if i < len(self.params['mlp_weights']) - 1:
                hidden = np.tanh(hidden)  # Activation
        
        # Sigmoid for binary classification
        output = 1 / (1 + np.exp(-hidden))
        
        return output
    
    def predict(self, data_dict):
        """Make prediction"""
        try:
            output = self._forward_pass(data_dict)
            prediction = int(output.flatten()[-1] > 0.5)
            probability = float(output.flatten()[-1])
            return prediction, probability
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            # Fallback prediction
            return np.random.randint(0, 2), np.random.random()
    
    def summary(self):
        """Print model summary"""
        total_params = 0
        
        # Count embedding parameters
        for i, feature in enumerate(self.categorical_features):
            vocab_size = self.categorical_cardinalities[i]
            total_params += vocab_size * self.embedding_dim
        
        # Count other parameters
        total_features = len(self.categorical_features) + len(self.numerical_features)
        hidden_dim = total_features * self.embedding_dim
        
        total_params += hidden_dim * hidden_dim * 3  # Attention
        total_params += hidden_dim * self.mlp_hidden_factors[0]  # MLP layer 1
        total_params += self.mlp_hidden_factors[0] * self.mlp_hidden_factors[1] * hidden_dim  # MLP layer 2
        total_params += self.mlp_hidden_factors[1] * hidden_dim  # Output layer
        
        print(f"Model: MockTabTransformer")
        print(f"Total parameters: {total_params:,}")
        print(f"Categorical features: {len(self.categorical_features)}")
        print(f"Numerical features: {len(self.numerical_features)}")
        print(f"Embedding dimension: {self.embedding_dim}")
        print(f"Depth: {self.depth}")
        print(f"Heads: {self.heads}")
    
    def save(self, model_path):
        """Mock save method"""
        import pickle
        os.makedirs(model_path, exist_ok=True)
        
        # Save model state
        model_state = {
            'numerical_features': self.numerical_features,
            'categorical_features': self.categorical_features,
            'categorical_cardinalities': self.categorical_cardinalities,
            'embedding_dim': self.embedding_dim,
            'depth': self.depth,
            'heads': self.heads,
            'params': self.params
        }
        
        with open(os.path.join(model_path, 'mock_model.pkl'), 'wb') as f:
            pickle.dump(model_state, f)
        
        print(f"Mock model saved to {model_path}")
    
    def load_weights(self, model_path):
        """Mock load weights method"""
        import pickle
        model_file = os.path.join(model_path, 'mock_model.pkl')
        
        if os.path.exists(model_file):
            with open(model_file, 'rb') as f:
                model_state = pickle.load(f)
                self.params = model_state['params']
                print(f"Mock model loaded from {model_path}")
        else:
            print(f"No mock model found at {model_path}")
    
    def compile(self, optimizer=None, loss=None, metrics=None):
        """Mock compile method"""
        self.optimizer = optimizer
        self.loss = loss
        self.metrics = metrics
        print("Mock model compiled")
    
    def fit(self, *args, **kwargs):
        """Mock fit method"""
        print("Mock training completed")
        # Return mock history
        class MockHistory:
            def __init__(self):
                self.history = {
                    'loss': [0.5, 0.4, 0.35, 0.32, 0.30],
                    'accuracy': [0.75, 0.78, 0.80, 0.82, 0.83],
                    'val_loss': [0.55, 0.45, 0.40, 0.38, 0.36],
                    'val_accuracy': [0.72, 0.76, 0.78, 0.79, 0.80],
                    'val_auc': [0.78, 0.81, 0.83, 0.85, 0.86]
                }
            def __getitem__(self, key):
                return self.history.get(key, [])
        
        return MockHistory()
    
    def evaluate(self, *args, **kwargs):
        """Mock evaluate method"""
        print("Mock evaluation completed")
        return [0.35, 0.80, 0.85]  # loss, accuracy, auc
    
    def count_params(self):
        """Count total parameters"""
        total_params = 0
        
        # Count embedding parameters
        for i, feature in enumerate(self.categorical_features):
            vocab_size = self.categorical_cardinalities[i]
            total_params += vocab_size * self.embedding_dim
        
        # Count other parameters
        total_features = len(self.categorical_features) + len(self.numerical_features)
        hidden_dim = total_features * self.embedding_dim
        
        total_params += hidden_dim * hidden_dim * 3  # Attention
        total_params += hidden_dim * self.mlp_hidden_factors[0]  # MLP layer 1
        total_params += self.mlp_hidden_factors[0] * self.mlp_hidden_factors[1] * hidden_dim  # MLP layer 2
        total_params += self.mlp_hidden_factors[1] * hidden_dim  # Output layer
        
        return total_params

# Mock tabtransformertf module
class MockTabTransformerTF:
    """Mock tabtransformertf module"""
    
    @staticmethod
    def TabTransformer(*args, **kwargs):
        return MockTabTransformer(*args, **kwargs)
