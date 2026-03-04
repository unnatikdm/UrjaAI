import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

# Load artifacts
# We need to recreate the test set to evaluate properly
import sys
sys.path.append('.')
from ensemble_training import load_and_merge, engineer_features

def evaluate_models():
    print("Loading data and generating features...")
    df = load_and_merge()
    df = engineer_features(df)
    
    # Use the same split logic as in training
    n = len(df)
    val_end = int(n * 0.9)
    test_df = df.iloc[val_end:]
    
    target = 'data'
    features = joblib.load('ensemble_features.joblib')
    scaler = joblib.load('ensemble_scaler.joblib')
    
    X_test = test_df[features]
    y_test = test_df[target]
    X_test_scaled = scaler.transform(X_test)
    
    # Load Models
    model_xgb = joblib.load('ensemble_xgb.joblib')
    model_lgb = joblib.load('ensemble_lgb.joblib')
    
    # Predictions
    pred_xgb = model_xgb.predict(X_test_scaled)
    pred_lgb = model_lgb.predict(X_test_scaled)
    ensemble_preds = (pred_xgb + pred_lgb) / 2
    
    # Metrics
    def get_metrics(y_true, y_pred, name):
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        # MAPE (avoiding division by zero)
        mape = np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 0.1, None))) * 100
        return {"Model": name, "RMSE": rmse, "MAE": mae, "R2": r2, "MAPE%": mape}

    results = []
    results.append(get_metrics(y_test, pred_xgb, "XGBoost"))
    results.append(get_metrics(y_test, pred_lgb, "LightGBM"))
    results.append(get_metrics(y_test, ensemble_preds, "Ensemble (XGB+LGB)"))
    
    df_results = pd.DataFrame(results)
    print("\n--- Model Performance Comparison ---")
    print(df_results.to_string(index=False))
    
    # Check Directional Accuracy
    # Did we correctly predict if the next hour goes up or down?
    y_diff = np.diff(y_test)
    pred_diff = np.diff(ensemble_preds)
    directional_acc = np.mean((y_diff > 0) == (pred_diff > 0)) * 100
    print(f"\nDirectional Accuracy: {directional_acc:.2f}%")

    # Save to disk
    df_results.to_csv('model_metrics.csv', index=False)

if __name__ == "__main__":
    evaluate_models()
