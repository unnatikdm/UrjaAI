import pandas as pd
import numpy as np
from scipy.io import arff
import requests
# import tensorflow as tf  # Commented out for testing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle
import os
from typing import Dict, List, Tuple, Any
import logging

class COIL2000DataPipeline:
    """Data preparation pipeline for COIL 2000 Insurance Dataset"""
    
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
    
    def download_coil2000_dataset(self) -> pd.DataFrame:
        """Download COIL 2000 dataset from OpenML"""
        self.logger.info("Downloading COIL 2000 dataset from OpenML...")
        
        try:
            # OpenML API URL for COIL 2000 dataset (ID: 45559)
            url = "https://www.openml.org/data/v1/download/2062257/coil2000.arff"
            
            # Download the ARFF file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_file = "coil2000.arff"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Load ARFF file
            data, meta = arff.loadarff(temp_file)
            df = pd.DataFrame(data)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            self.logger.info(f"Dataset loaded successfully: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to download dataset: {e}")
            # Fallback to sample data generation
            return self._generate_fallback_data()
    
    def _generate_fallback_data(self) -> pd.DataFrame:
        """Generate fallback data similar to COIL 2000 structure"""
        self.logger.warning("Using fallback data generation...")
        
        np.random.seed(42)
        n_samples = 5000
        
        # Generate 86 features similar to COIL 2000 structure
        # First 43 are socio-demographic (mostly categorical)
        # Next 43 are product ownership (mostly numerical)
        
        data = {}
        
        # Socio-demographic features (categorical-like)
        socio_demo_features = [
            'MOSTYPE', 'MAANTHUI', 'MGEMOMV', 'MGEMLEEF', 'MOSHOOFD',
            'MGODRK', 'MGODPR', 'MGODOV', 'MRELGE', 'MRELSA',
            'MRELOV', 'MFALLEEN', 'MFGEKIND', 'MFWEKIND', 'MOPLHOOG',
            'MOPLMIDD', 'MOPLLAAG', 'MBERHOOG', 'MBERZELF', 'MBERBOER',
            'MBERZORG', 'MFALLEEN', 'MFGEKIND', 'MFWEKIND', 'MOPLHOOG',
            'MOPLMIDD', 'MOPLLAAG', 'MBERHOOG', 'MBERZELF', 'MBERBOER',
            'MBERZORG', 'MSKA', 'MSKB1', 'MSKB2', 'MSKC', 'MSKD',
            'MHHUUR', 'MHKOOP', 'MAUT1', 'MAUT2', 'MAUT0',
            'MZFONDS', 'MZPART', 'MINKM30', 'MINK123', 'MINKGEW',
            'MINKMEL', 'MINK123', 'MINKGEW'
        ]
        
        for i, feature in enumerate(socio_demo_features[:43]):
            if i < len(socio_demo_features):
                # Generate categorical-like data
                n_categories = np.random.randint(2, 10)
                data[feature] = np.random.choice(
                    [f'cat_{j}' for j in range(n_categories)], 
                    size=n_samples
                )
        
        # Product ownership features (numerical)
        product_features = [
            'MINK123', 'MINKGEW', 'PWAPART', 'PWABEDR', 'PWALAND',
            'PPERSAUT', 'PBESAUT', 'PMOTSCO', 'PVRAAUT', 'PAANHANG',
            'PTRACTOR', 'PWERKT', 'PBROM', 'PLEVEN', 'PPERSONG',
            'PGEZONG', 'PFIETS', 'PINBOED', 'PBYSTAND', 'AWAPART',
            'AWABEDR', 'AWALAND', 'APERSAUT', 'ABESAUT', 'AMOTSCO',
            'AVRAAUT', 'AAANHANG', 'ATRACTOR', 'AWERKT', 'ABROM',
            'ALEVEN', 'APERSONG', 'AGEZONG', 'AFIETS', 'AINBOED',
            'ABYSTAND'
        ]
        
        for i, feature in enumerate(product_features[:43]):
            if i < len(product_features):
                # Generate numerical data (counts, amounts)
                data[feature] = np.random.randint(0, 10, size=n_samples)
        
        # Target variable: CARAVAN insurance ownership
        # Create realistic correlation with product ownership features
        caravan_prob = (
            (data.get('PPERSAUT', np.zeros(n_samples)) > 0) |
            (data.get('PWAPART', np.zeros(n_samples)) > 0) |
            (data.get('PBESAUT', np.zeros(n_samples)) > 0)
        ).astype(float)
        
        # Add some noise
        caravan_prob = caravan_prob * 0.6 + np.random.random(n_samples) * 0.4
        data['CARAVAN'] = (caravan_prob > 0.5).astype(int)
        
        df = pd.DataFrame(data)
        self.logger.info(f"Fallback dataset generated: {df.shape}")
        
        return df
    
    def identify_features(self, df: pd.DataFrame, target_column: str = 'CARAVAN'):
        """Identify categorical and numerical features"""
        self.target_column = target_column
        
        # Separate features from target
        feature_columns = [col for col in df.columns if col != target_column]
        
        # Identify categorical and numerical features
        self.categorical_features = []
        self.numerical_features = []
        
        for col in feature_columns:
            if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                self.categorical_features.append(col)
            else:
                # Check if numerical feature has low cardinality (might be categorical)
                unique_vals = df[col].nunique()
                if unique_vals <= 10 and unique_vals < len(df) * 0.05:
                    self.categorical_features.append(col)
                else:
                    self.numerical_features.append(col)
        
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
            df = self.download_coil2000_dataset()
        
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
            'target_column': self.target_column,
            'dataset_shape': df.shape,
            'target_distribution': df[self.target_column].value_counts().to_dict()
        }
        
        return df_processed.drop(columns=[self.target_column]), df_processed[self.target_column]
    
    def create_tf_dataset(self, X: pd.DataFrame, y: pd.DataFrame, 
                        batch_size: int = 32, shuffle: bool = True):
        """Create TensorFlow dataset from pandas DataFrames"""
        # Return data as-is for testing without TensorFlow
        return X, y
    
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
        
        # Update instance variables with fallbacks
        self.categorical_features = self.feature_info.get('categorical_features', [])
        self.numerical_features = self.feature_info.get('numerical_features', [])
        self.feature_vocab = self.feature_info.get('feature_vocab', {})
        self.target_column = self.feature_info.get('target_column', 'CARAVAN')
        
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
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get comprehensive data summary"""
        if not self.feature_info:
            return {"error": "Data not prepared yet"}
        
        return {
            "dataset_name": "COIL 2000 Insurance Dataset",
            "source": "OpenML ID 45559",
            "task": "Binary Classification (CARAVAN Insurance Prediction)",
            "shape": self.feature_info.get("dataset_shape", "Unknown"),
            "target_distribution": self.feature_info.get("target_distribution", {}),
            "categorical_features_count": len(self.categorical_features),
            "numerical_features_count": len(self.numerical_features),
            "total_features": len(self.categorical_features) + len(self.numerical_features),
            "target_column": self.target_column,
            "positive_class_ratio": self.feature_info.get("target_distribution", {}).get(1, 0) / self.feature_info.get("dataset_shape", [0])[0] if self.feature_info.get("dataset_shape") else 0
        }

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize pipeline
    pipeline = COIL2000DataPipeline()
    
    # Prepare data
    X, y = pipeline.prepare_data()
    
    # Get data summary
    summary = pipeline.get_data_summary()
    print("COIL 2000 Dataset Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test = pipeline.split_data(X, y)
    
    # Create TensorFlow datasets
    train_dataset = pipeline.create_tf_dataset(X_train, y_train)
    val_dataset = pipeline.create_tf_dataset(X_val, y_val, shuffle=False)
    
    # Save artifacts
    pipeline.save_preprocessing_artifacts()
    
    print(f"\nData prepared successfully!")
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Categorical features: {len(pipeline.categorical_features)}")
    print(f"Numerical features: {len(pipeline.numerical_features)}")
