from __future__ import annotations
import tensorflow as tf
from tabtransformertf.models.tabtransformer import TabTransformer
import mlflow
import mlflow.tensorflow
TENSORFLOW_AVAILABLE = True
# from mock_tensorflow import MockTabTransformerTF # Removed mock fallback

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Any
import logging
from coil2000_data_pipeline import COIL2000DataPipeline

class TabTransformerModel:
    """TabTransformer model training and management"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self.get_default_config()
        self.model = None
        self.pipeline = COIL2000DataPipeline()
        self.history = None
        
        self.logger = logging.getLogger(__name__)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default model configuration"""
        return {
            # Model architecture
            'embedding_dim': 16,  # Reduced for COIL 2000's many features
            'depth': 6,  # Increased depth for complex patterns
            'heads': 8,
            'attn_dropout': 0.2,
            'ff_dropout': 0.2,
            'mlp_hidden_factors': [4, 2],  # Larger for 86 features
            
            # Training parameters
            'learning_rate': 1e-4,
            'weight_decay': 0.01,
            'batch_size': 64,  # Increased batch size
            'epochs': 100,  # More epochs for real data
            'patience': 15,
            
            # Data parameters
            'test_size': 0.2,
            'val_size': 0.1,
            
            # Model saving
            'target_column': 'correct',
            'model_dir': 'models',
            'experiment_name': 'coil2000_tabtransformer'
        }
    
    def prepare_data(self) -> Tuple[tf.data.Dataset, tf.data.Dataset, tf.data.Dataset]:
        """Prepare training, validation, and test datasets"""
        self.logger.info("Preparing data...")
        
        # Load and preprocess data
        X, y = self.pipeline.prepare_data()
        
        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.pipeline.split_data(
            X, y, self.config['test_size'], self.config['val_size']
        )
        
        # Create TensorFlow datasets
        train_dataset = self.pipeline.create_tf_dataset(
            X_train, y_train, self.config['batch_size'], shuffle=True
        )
        val_dataset = self.pipeline.create_tf_dataset(
            X_val, y_val, self.config['batch_size'], shuffle=False
        )
        test_dataset = self.pipeline.create_tf_dataset(
            X_test, y_test, self.config['batch_size'], shuffle=False
        )
        
        self.logger.info(f"Data prepared - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return train_dataset, val_dataset, test_dataset
    
    def build_model(self) -> tf.keras.Model:
        """Build TabTransformer model"""
        self.logger.info("Building TabTransformer model...")
        
        # Get feature information
        categorical_features = self.pipeline.categorical_features
        numerical_features = self.pipeline.numerical_features
        feature_vocab = self.pipeline.feature_vocab
        
        # 0.0.8 needs a lookup dict: {feature_name: StringLookupLayer}
        categorical_lookup = self.pipeline.categorical_lookup
        
        if TENSORFLOW_AVAILABLE:
            # Build real TensorFlow model
            # 0.0.8 API requires categorical_lookup to be Keras StringLookup layers
            self.model = TabTransformer(
                out_dim=1,
                out_activation='sigmoid',
                numerical_features=numerical_features,
                categorical_features=categorical_features,
                categorical_lookup=categorical_lookup,
                embedding_dim=self.config['embedding_dim'],
                depth=self.config['depth'],
                heads=self.config['heads'],
                attn_dropout=self.config['attn_dropout'],
                ff_dropout=self.config['ff_dropout'],
                mlp_hidden_factors=self.config['mlp_hidden_factors']
            )
            
            # Compile model
            optimizer = tf.keras.optimizers.AdamW(
                learning_rate=self.config['learning_rate'],
                weight_decay=self.config['weight_decay']
            )
            
            self.model.compile(
                optimizer=optimizer,
                loss='binary_crossentropy',
                metrics=['accuracy', 'AUC']
            )
            
            self.logger.info(f"Real TensorFlow model built with {self.model.count_params():,} parameters")
        else:
            # Build mock model
            self.model = TabTransformer(
                numerical_features=numerical_features,
                categorical_features=categorical_features,
                categorical_cardinalities=categorical_cardinalities,
                embedding_dim=self.config['embedding_dim'],
                depth=self.config['depth'],
                heads=self.config['heads'],
                attn_dropout=self.config['attn_dropout'],
                ff_dropout=self.config['ff_dropout'],
                mlp_hidden_factors=self.config['mlp_hidden_factors']
            )
            
            self.logger.info(f"Mock TensorFlow model built with {self.model.count_params():,} parameters")
        
        return self.model
    
    def train_model(self, train_dataset, val_dataset) -> Dict[str, Any]:
        """Train the TabTransformer model"""
        self.logger.info("Starting model training...")
        
        if TENSORFLOW_AVAILABLE:
            # Real TensorFlow training
            return self._train_tensorflow_model(train_dataset, val_dataset)
        else:
            # Mock training for demonstration
            return self._train_mock_model(train_dataset, val_dataset)
    
    def _train_tensorflow_model(self, train_dataset, val_dataset) -> Dict[str, Any]:
        """Train real TensorFlow model"""
        # Set up MLflow
        mlflow.set_experiment(self.config['experiment_name'])
        
        with mlflow.start_run() as run:
            # Log parameters
            mlflow.log_params(self.config)
            
            # Callbacks
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=self.config['patience'],
                    restore_best_weights=True,
                    verbose=1
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7,
                    verbose=1
                ),
                mlflow.tensorflow.MlflowCallback()
            ]
            
            # Train model
            self.history = self.model.fit(
                train_dataset,
                validation_data=val_dataset,
                epochs=self.config['epochs'],
                callbacks=callbacks,
                verbose=1
            )
            
            # Log metrics
            final_val_loss = self.history.history['val_loss'][-1]
            final_val_acc = self.history.history['val_accuracy'][-1]
            final_val_auc = self.history.history['val_auc'][-1]
            
            mlflow.log_metrics({
                'final_val_loss': final_val_loss,
                'final_val_accuracy': final_val_acc,
                'final_val_auc': final_val_auc
            })
            
            self.logger.info(f"Training completed - Val Loss: {final_val_loss:.4f}, Val Acc: {final_val_acc:.4f}, Val AUC: {final_val_auc:.4f}")
            
            return {
                'run_id': run.info.run_id,
                'final_val_loss': final_val_loss,
                'final_val_accuracy': final_val_acc,
                'final_val_auc': final_val_auc
            }
    
    def _train_mock_model(self, train_dataset, val_dataset) -> Dict[str, Any]:
        """Mock training for demonstration"""
        self.logger.info("Running mock training (TensorFlow not available)...")
        
        # Simulate training epochs
        import time
        time.sleep(2)  # Simulate training time
        
        # Mock training metrics
        mock_metrics = {
            'run_id': 'mock_run_123',
            'final_val_loss': 0.45,
            'final_val_accuracy': 0.78,
            'final_val_auc': 0.82
        }
        
        self.logger.info(f"Mock training completed - Val Loss: {mock_metrics['final_val_loss']:.4f}, Val Acc: {mock_metrics['final_val_accuracy']:.4f}, Val AUC: {mock_metrics['final_val_auc']:.4f}")
        
        return mock_metrics
    
    def evaluate_model(self, test_dataset: tf.data.Dataset) -> Dict[str, float]:
        """Evaluate the trained model"""
        self.logger.info("Evaluating model...")
        
        results = self.model.evaluate(test_dataset, verbose=0)
        
        metrics = {
            'test_loss': results[0],
            'test_accuracy': results[1],
            'test_auc': results[2] if len(results) > 2 else None
        }
        
        self.logger.info(f"Test Results - Loss: {metrics['test_loss']:.4f}, Acc: {metrics['test_accuracy']:.4f}")
        
        return metrics
    
    def save_model(self, model_path: str = None) -> str:
        """Save the trained model"""
        if model_path is None:
            model_path = os.path.join(self.config['model_dir'], 'tabtransformer_v1')
        
        os.makedirs(model_path, exist_ok=True)
        
        # Save model in TensorFlow SavedModel format
        self.model.save(model_path)
        
        # Save preprocessing artifacts
        self.pipeline.save_preprocessing_artifacts(model_path)
        
        # Save model config
        import json
        with open(os.path.join(model_path, 'config.json'), 'w') as f:
            json.dump(self.config, f, indent=2)
        
        self.logger.info(f"Model saved to {model_path}")
        return model_path
    
    def load_model(self, model_path: str) -> tf.keras.Model:
        """Load a trained model"""
        self.logger.info(f"Loading model from {model_path}")
        
        # Load preprocessing artifacts
        self.pipeline.load_preprocessing_artifacts(model_path)
        
        # Load model config
        import json
        with open(os.path.join(model_path, 'config.json'), 'r') as f:
            self.config = json.load(f)
        
        # Rebuild model architecture
        self.build_model()
        
        # Load weights
        self.model.load_weights(model_path)
        
        self.logger.info("Model loaded successfully")
        return self.model
    
    def predict(self, data: Dict[str, Any]) -> Tuple[float, float]:
        """Make prediction on single instance"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Preprocess input
        processed_data = self.pipeline.preprocess_single_instance(data)
        
        # Make prediction
        if TENSORFLOW_AVAILABLE:
            prediction = self.model.predict(processed_data, verbose=0)
            probability = float(prediction[0][0])
            class_label = int(probability > 0.5)
        else:
            # Mock prediction
            class_label, probability = self.model.predict(processed_data)
        
        return class_label, probability
    
    def predict_batch(self, data_list: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """Make predictions on batch of instances"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Convert to DataFrame
        df = pd.DataFrame(data_list)
        
        # Preprocess
        df_encoded = self.pipeline.encode_categorical_features(df, fit=False)
        df_processed = self.pipeline.scale_numerical_features(df_encoded, fit=False)
        
        # Convert to dictionary format
        dataset_dict = {}
        for feature in self.pipeline.categorical_features:
            dataset_dict[feature] = df_processed[feature].values
        
        for feature in self.pipeline.numerical_features:
            dataset_dict[feature] = df_processed[feature].values
        
        # Make predictions
        if TENSORFLOW_AVAILABLE:
            predictions = self.model.predict(dataset_dict, verbose=0)
            
            results = []
            for pred in predictions:
                probability = float(pred[0])
                class_label = int(probability > 0.5)
                results.append((class_label, probability))
        else:
            # Mock batch predictions
            results = []
            for i, instance in enumerate(data_list):
                processed_instance = self.pipeline.preprocess_single_instance(instance)
                class_label, probability = self.model.predict(processed_instance)
                results.append((class_label, probability))
        
        return results
    
    def get_model_summary(self) -> str:
        """Get model summary"""
        if self.model is None:
            return "Model not built yet"
        
        import io
        import sys
        
        # Capture model summary
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        self.model.summary()
        sys.stdout = old_stdout
        
        return buffer.getvalue()

# Training script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize model
    model_trainer = TabTransformerModel()
    
    # Prepare data
    train_dataset, val_dataset, test_dataset = model_trainer.prepare_data()
    
    # Build model
    model_trainer.build_model()
    
    # Print model summary
    print(model_trainer.get_model_summary())
    
    # Train model
    training_results = model_trainer.train_model(train_dataset, val_dataset)
    
    # Evaluate model
    test_results = model_trainer.evaluate_model(test_dataset)
    
    # Save model
    model_path = model_trainer.save_model()
    
    print(f"\nTraining completed successfully!")
    print(f"Model saved to: {model_path}")
    print(f"Test Accuracy: {test_results['test_accuracy']:.4f}")
    print(f"Test AUC: {test_results['test_auc']:.4f}")
