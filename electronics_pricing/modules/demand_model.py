"""
Demand forecasting module using machine learning models.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
from pathlib import Path
from typing import Dict, Tuple, List
import joblib
import json
from .utils import get_logger, create_output_dir

logger = get_logger(__name__)


class DemandForecaster:
    """Demand forecasting using multiple ML models."""

    def __init__(self, output_dir: str = 'data', models_dir: str = 'models'):
        """
        Initialize DemandForecaster.
        
        Parameters:
        -----------
        output_dir : str
            Output directory for data
        models_dir : str
            Directory to save trained models
        """
        self.output_dir = Path(output_dir)
        self.models_dir = create_output_dir(models_dir)
        self.models = {}  # {product: {model_name: model}}
        self.scalers = {}  # {product: scaler}
        self.metrics = {}  # {product: {model_name: metrics}}
        self.feature_names = None
        logger.info("DemandForecaster initialized")

    def prepare_features(self, sales_df: pd.DataFrame, products_meta: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for modeling.
        
        Parameters:
        -----------
        sales_df : pd.DataFrame
            Sales data
        products_meta : pd.DataFrame
            Product metadata
            
        Returns:
        --------
        features_df : pd.DataFrame
            Feature matrix with target variable
        """
        logger.info("Preparing features...")
        
        features_df = sales_df.copy()
        
        # Merge product metadata
        features_df = features_df.merge(products_meta, on='product', how='left')
        
        # Create derived features
        features_df['price_ratio'] = features_df['price'] / features_df['competitor_price']
        features_df['price_vs_base'] = features_df['price'] / features_df['base_price']
        
        # Time-based features
        features_df['day_of_month'] = features_df['date'].dt.day
        features_df['quarter'] = features_df['date'].dt.quarter
        features_df['week_of_year'] = features_df['date'].dt.isocalendar().week
        
        logger.info(f"Created {len(features_df.columns) - len(sales_df.columns)} new features")
        
        return features_df

    def train_all(self, sales_df: pd.DataFrame, products_meta: pd.DataFrame, 
                 test_size: float = 0.2) -> Dict:
        """
        Train models for all products.
        
        Parameters:
        -----------
        sales_df : pd.DataFrame
            Sales data
        products_meta : pd.DataFrame
            Product metadata
        test_size : float
            Test set fraction (using time-based split)
            
        Returns:
        --------
        results : Dict
            Training results
        """
        logger.info("Training demand models for all products...")
        
        features_df = self.prepare_features(sales_df, products_meta)
        
        # Define features
        feature_cols = [
            'price', 'competitor_price', 'price_ratio', 'price_vs_base',
            'is_promotion', 'is_weekend', 'day_of_week', 'month',
            'day_of_month', 'quarter', 'week_of_year'
        ]
        
        self.feature_names = feature_cols
        
        products = features_df['product'].unique()
        results = {}
        
        for product in sorted(products):
            logger.info(f"Training models for {product}...")
            
            prod_data = features_df[features_df['product'] == product].sort_values('date')
            
            X = prod_data[feature_cols].values
            y = prod_data['quantity_sold'].values
            
            # Time-based split
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            logger.info(f"  Train set: {len(X_train)}, Test set: {len(X_test)}")
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            self.scalers[product] = scaler
            self.models[product] = {}
            self.metrics[product] = {}
            
            # Train Linear Regression
            lr_model = LinearRegression()
            lr_model.fit(X_train_scaled, y_train)
            y_pred_lr = lr_model.predict(X_test_scaled)
            metrics_lr = self._compute_metrics(y_test, y_pred_lr)
            self.models[product]['Linear Regression'] = lr_model
            self.metrics[product]['Linear Regression'] = metrics_lr
            logger.info(f"  Linear Regression - R²: {metrics_lr['r2']:.4f}, RMSE: {metrics_lr['rmse']:.2f}")
            
            # Train Random Forest
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=15)
            rf_model.fit(X_train, y_train)
            y_pred_rf = rf_model.predict(X_test)
            metrics_rf = self._compute_metrics(y_test, y_pred_rf)
            self.models[product]['Random Forest'] = rf_model
            self.metrics[product]['Random Forest'] = metrics_rf
            logger.info(f"  Random Forest - R²: {metrics_rf['r2']:.4f}, RMSE: {metrics_rf['rmse']:.2f}")
            
            # Train XGBoost
            xgb_model = xgb.XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=6)
            xgb_model.fit(X_train, y_train)
            y_pred_xgb = xgb_model.predict(X_test)
            metrics_xgb = self._compute_metrics(y_test, y_pred_xgb)
            self.models[product]['XGBoost'] = xgb_model
            self.metrics[product]['XGBoost'] = metrics_xgb
            logger.info(f"  XGBoost - R²: {metrics_xgb['r2']:.4f}, RMSE: {metrics_xgb['rmse']:.2f}")
            
            # Select best model
            best_model_name = max(self.metrics[product], key=lambda x: self.metrics[product][x]['r2'])
            results[product] = {
                'best_model': best_model_name,
                'metrics': self.metrics[product],
            }
            logger.info(f"  Best model for {product}: {best_model_name}")
        
        logger.info("Training completed!")
        return results

    def predict(self, product: str, features: np.ndarray) -> np.ndarray:
        """
        Make predictions for a product.
        
        Parameters:
        -----------
        product : str
            Product name
        features : np.ndarray
            Feature matrix (n_samples, n_features)
            
        Returns:
        --------
        predictions : np.ndarray
            Predicted quantities
        """
        if product not in self.models or len(self.models[product]) == 0:
            raise ValueError(f"No trained models for {product}")
        
        # Get best model
        best_model_name = max(self.metrics[product], key=lambda x: self.metrics[product][x]['r2'])
        model = self.models[product][best_model_name]
        
        # Scale features if using Linear Regression
        if best_model_name == 'Linear Regression':
            features = self.scalers[product].transform(features)
        
        predictions = model.predict(features)
        predictions = np.maximum(predictions, 0)  # Ensure non-negative
        
        return predictions

    def get_metrics(self, product: str) -> Dict:
        """Get metrics for a product's models."""
        return self.metrics.get(product, {})

    def save_models(self) -> None:
        """Save all trained models to disk."""
        logger.info("Saving trained models...")
        
        for product, product_models in self.models.items():
            for model_name, model in product_models.items():
                model_path = self.models_dir / f"{product.replace(' ', '_')}_{model_name.replace(' ', '_')}.pkl"
                joblib.dump(model, model_path)
        
        # Save scalers
        for product, scaler in self.scalers.items():
            scaler_path = self.models_dir / f"{product.replace(' ', '_')}_scaler.pkl"
            joblib.dump(scaler, scaler_path)
        
        # Save metrics as JSON
        metrics_path = self.models_dir / "metrics.json"
        joblib.dump(self.metrics, metrics_path)
        
        logger.info(f"Models saved to {self.models_dir}")

    def load_models(self) -> None:
        """Load trained models from disk."""
        logger.info("Loading trained models...")
        
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not model_files:
            logger.warning("No model files found")
            return
        
        # Load scalers
        for scaler_file in self.models_dir.glob("*_scaler.pkl"):
            product = scaler_file.stem.replace('_scaler', '').replace('_', ' ')
            self.scalers[product] = joblib.load(scaler_file)
        
        logger.info(f"Loaded {len(self.scalers)} scalers")
        
        # Load metrics from saved JSON/pkl file if it exists
        metrics_path = self.models_dir / "metrics.json"
        if metrics_path.exists():
            try:
                self.metrics = joblib.load(metrics_path)
                logger.info(f"Loaded metrics for {len(self.metrics)} products")
            except Exception as e:
                logger.warning(f"Could not load metrics: {e}")
        
        # Load trained models (not scalers)
        for model_file in self.models_dir.glob("*.pkl"):
            # Skip scaler files and metrics file
            if '_scaler.pkl' in str(model_file) or 'metrics.json' in str(model_file):
                continue
            
            stem = model_file.stem
            
            # Parse filename: try to match known model name patterns at the end
            product = None
            model_name = None
            
            # Check for known model name suffixes
            for suffix in ['_Linear_Regression', '_Random_Forest', '_XGBoost']:
                if stem.endswith(suffix):
                    product = stem[:-len(suffix)].replace('_', ' ')
                    model_name = suffix[1:].replace('_', ' ')  # Remove leading '_'
                    break
            
            # Skip if we couldn't identify the model
            if product is None or model_name is None:
                logger.warning(f"Could not parse model file: {model_file.name}")
                continue
            
            # Initialize product entries if needed
            if product not in self.models:
                self.models[product] = {}
            if product not in self.metrics:
                self.metrics[product] = {}
            
            # Load and store the model
            try:
                model = joblib.load(model_file)
                self.models[product][model_name] = model
                logger.debug(f"Loaded model: {product} - {model_name}")
            except Exception as e:
                logger.error(f"Error loading model {model_file.name}: {e}")
        
        logger.info(f"Loaded models for {len(self.models)} products")

    @staticmethod
    def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Compute evaluation metrics."""
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        return {
            'rmse': np.sqrt(mse),
            'mae': mae,
            'r2': r2,
        }
