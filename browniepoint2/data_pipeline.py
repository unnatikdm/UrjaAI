import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle
import os
from typing import Dict, List, Tuple, Any
import logging

class TabTransformerDataPipeline:
    """Data preparation pipeline for TabTransformer model"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.categorical_features = []
        self.numerical_features = []
        self.target_column = None
        self.label_encoders = {}
        self.scalers = {}
        self.feature_vocab = {}
        self.feature_info = {}
        
        self.logger = logging.getLogger(__name__)
    
    def load_sample_data(self) -> pd.DataFrame:
        """Load sample dataset (Adult Income dataset as example)"""
        # Create sample data for demonstration
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'age': np.random.randint(18, 80, n_samples),
            'workclass': np.random.choice(['Private', 'Self-emp-not-inc', 'Self-emp-inc', 
                                        'Federal-gov', 'Local-gov', 'State-gov', 
                                        'Without-pay', 'Never-worked'], n_samples),
            'education': np.random.choice(['Bachelors', 'Some-college', '11th', 'HS-grad',
                                        'Prof-school', 'Assoc-acdm', 'Assoc-voc', '9th',
                                        '7th-8th', '12th', 'Masters', '1st-4th', '10th',
                                        'Doctorate', '5th-6th', 'Preschool'], n_samples),
            'marital_status': np.random.choice(['Married-civ-spouse', 'Divorced', 'Never-married',
                                             'Separated', 'Widowed', 'Married-spouse-absent',
                                             'Married-AF-spouse'], n_samples),
            'occupation': np.random.choice(['Tech-support', 'Craft-repair', 'Other-service',
                                         'Sales', 'Exec-managerial', 'Prof-specialty',
                                         'Handlers-cleaners', 'Machine-op-inspct',
                                         'Adm-clerical', 'Farming-fishing', 'Transport-moving',
                                         'Priv-house-serv', 'Protective-serv', 'Armed-Forces'], n_samples),
            'relationship': np.random.choice(['Wife', 'Own-child', 'Husband', 'Not-in-family',
                                          'Other-relative', 'Unmarried'], n_samples),
            'race': np.random.choice(['White', 'Asian-Pac-Islander', 'Amer-Indian-Eskimo',
                                    'Other', 'Black'], n_samples),
            'gender': np.random.choice(['Female', 'Male'], n_samples),
            'capital_gain': np.random.randint(0, 100000, n_samples),
            'capital_loss': np.random.randint(0, 5000, n_samples),
            'hours_per_week': np.random.randint(1, 99, n_samples),
            'native_country': np.random.choice(['United-States', 'Cambodia', 'England',
                                             'Puerto-Rico', 'Canada', 'Germany',
                                             'Outlying-US(Guam-USVI-etc)', 'India', 'Japan',
                                             'Greece', 'South', 'China', 'Cuba',
                                             'Iran', 'Honduras', 'Philippines', 'Italy',
                                             'Poland', 'Jamaica', 'Vietnam', 'Mexico',
                                             'Portugal', 'Ireland', 'France', 'Dominican-Republic',
                                             'Laos', 'Ecuador', 'Taiwan', 'Haiti',
                                             'Columbia', 'Hungary', 'Guatemala', 'Nicaragua',
                                             'Scotland', 'Thailand', 'Yugoslavia', 'El-Salvador',
                                             'Trinadad&Tobago', 'Peru', 'Hong', 'Holand-Netherlands'], n_samples)
        }
        
        # Create target variable based on some logic
        df = pd.DataFrame(data)
        df['income'] = ((df['education'].isin(['Bachelors', 'Masters', 'Doctorate', 'Prof-school'])) & 
                       (df['hours_per_week'] > 40) & 
                       (df['capital_gain'] > 5000)).astype(int)
        
        return df
    
    def identify_features(self, df: pd.DataFrame, target_column: str = 'income'):
        """Identify categorical and numerical features"""
        self.target_column = target_column
        
        # Separate features from target
        feature_columns = [col for col in df.columns if col != target_column]
        
        # Identify categorical and numerical features
        self.categorical_features = [col for col in feature_columns if df[col].dtype == 'object']
        self.numerical_features = [col for col in feature_columns if df[col].dtype in ['int64', 'float64']]
        
        self.logger.info(f"Categorical features: {len(self.categorical_features)}")
        self.logger.info(f"Numerical features: {len(self.numerical_features)}")
        
        return self.categorical_features, self.numerical_features
    
    def build_vocabulary(self, df: pd.DataFrame):
        """Build vocabulary for categorical features"""
        for feature in self.categorical_features:
            unique_values = df[feature].unique().tolist()
            # Add 'Unknown' category for unseen values
            unique_values.append('Unknown')
            self.feature_vocab[feature] = unique_values
            
        self.logger.info(f"Built vocabulary for {len(self.categorical_features)} categorical features")
    
    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Encode categorical features using label encoding"""
        df_encoded = df.copy()
        
        for feature in self.categorical_features:
            if fit:
                # Fit new encoder
                le = LabelEncoder()
                # Add 'Unknown' to vocabulary
                vocab = self.feature_vocab.get(feature, [])
                le.fit(vocab)
                self.label_encoders[feature] = le
            
            # Transform features
            le = self.label_encoders[feature]
            # Handle unseen values by mapping to 'Unknown'
            df_encoded[feature] = df_encoded[feature].apply(
                lambda x: x if x in le.classes_ else 'Unknown'
            )
            df_encoded[feature] = le.transform(df_encoded[feature])
        
        return df_encoded
    
    def scale_numerical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Scale numerical features using StandardScaler"""
        df_scaled = df.copy()
        
        if fit:
            for feature in self.numerical_features:
                scaler = StandardScaler()
                df_scaled[feature] = scaler.fit_transform(df_scaled[[feature]])
                self.scalers[feature] = scaler
        else:
            for feature in self.numerical_features:
                if feature in self.scalers:
                    scaler = self.scalers[feature]
                    df_scaled[feature] = scaler.transform(df_scaled[[feature]])
        
        return df_scaled
    
    def prepare_data(self, df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Complete data preparation pipeline"""
        if df is None:
            df = self.load_sample_data()
        
        # Identify features
        self.identify_features(df)
        
        # Build vocabulary
        self.build_vocabulary(df)
        
        # Encode categorical features
        df_encoded = self.encode_categorical_features(df, fit=True)
        
        # Scale numerical features
        df_processed = self.scale_numerical_features(df_encoded, fit=True)
        
        # Store feature info for model
        self.feature_info = {
            'categorical_features': self.categorical_features,
            'numerical_features': self.numerical_features,
            'feature_vocab': self.feature_vocab,
            'target_column': self.target_column
        }
        
        return df_processed.drop(columns=[self.target_column]), df_processed[self.target_column]
    
    def create_tf_dataset(self, X: pd.DataFrame, y: pd.DataFrame, 
                        batch_size: int = 32, shuffle: bool = True) -> tf.data.Dataset:
        """Create TensorFlow dataset from pandas DataFrames"""
        # Convert to dictionary format for TabTransformer
        dataset_dict = {}
        
        # Add categorical features
        for feature in self.categorical_features:
            dataset_dict[feature] = X[feature].values
        
        # Add numerical features
        for feature in self.numerical_features:
            dataset_dict[feature] = X[feature].values
        
        # Create dataset
        dataset = tf.data.Dataset.from_tensor_slices((dataset_dict, y.values))
        
        if shuffle:
            dataset = dataset.shuffle(buffer_size=len(X))
        
        dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
        
        return dataset
    
    def split_data(self, X: pd.DataFrame, y: pd.DataFrame, 
                   test_size: float = 0.2, val_size: float = 0.1) -> Tuple:
        """Split data into train, validation, and test sets"""
        # First split: train + val vs test
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Second split: train vs val
        val_size_adjusted = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_size_adjusted, 
            random_state=42, stratify=y_train_val
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_preprocessing_artifacts(self, save_dir: str = 'artifacts'):
        """Save preprocessing artifacts for inference"""
        os.makedirs(save_dir, exist_ok=True)
        
        # Save feature info
        with open(os.path.join(save_dir, 'feature_info.pkl'), 'wb') as f:
            pickle.dump(self.feature_info, f)
        
        # Save label encoders
        with open(os.path.join(save_dir, 'label_encoders.pkl'), 'wb') as f:
            pickle.dump(self.label_encoders, f)
        
        # Save scalers
        with open(os.path.join(save_dir, 'scalers.pkl'), 'wb') as f:
            pickle.dump(self.scalers, f)
        
        self.logger.info(f"Preprocessing artifacts saved to {save_dir}")
    
    def load_preprocessing_artifacts(self, load_dir: str = 'artifacts'):
        """Load preprocessing artifacts for inference"""
        # Load feature info
        with open(os.path.join(load_dir, 'feature_info.pkl'), 'rb') as f:
            self.feature_info = pickle.load(f)
        
        # Load label encoders
        with open(os.path.join(load_dir, 'label_encoders.pkl'), 'rb') as f:
            self.label_encoders = pickle.load(f)
        
        # Load scalers
        with open(os.path.join(load_dir, 'scalers.pkl'), 'rb') as f:
            self.scalers = pickle.load(f)
        
        # Update instance variables
        self.categorical_features = self.feature_info['categorical_features']
        self.numerical_features = self.feature_info['numerical_features']
        self.feature_vocab = self.feature_info['feature_vocab']
        self.target_column = self.feature_info['target_column']
        
        self.logger.info(f"Preprocessing artifacts loaded from {load_dir}")
    
    def preprocess_single_instance(self, data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """Preprocess a single instance for inference"""
        df = pd.DataFrame([data])
        
        # Encode categorical features
        df_encoded = self.encode_categorical_features(df, fit=False)
        
        # Scale numerical features
        df_processed = self.scale_numerical_features(df_encoded, fit=False)
        
        # Convert to dictionary format
        result = {}
        for feature in self.categorical_features:
            result[feature] = df_processed[feature].values
        
        for feature in self.numerical_features:
            result[feature] = df_processed[feature].values
        
        return result

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize pipeline
    pipeline = TabTransformerDataPipeline()
    
    # Prepare data
    X, y = pipeline.prepare_data()
    
    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test = pipeline.split_data(X, y)
    
    # Create TensorFlow datasets
    train_dataset = pipeline.create_tf_dataset(X_train, y_train)
    val_dataset = pipeline.create_tf_dataset(X_val, y_val, shuffle=False)
    
    # Save artifacts
    pipeline.save_preprocessing_artifacts()
    
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Categorical features: {len(pipeline.categorical_features)}")
    print(f"Numerical features: {len(pipeline.numerical_features)}")
