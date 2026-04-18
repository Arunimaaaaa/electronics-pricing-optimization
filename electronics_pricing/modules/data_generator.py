"""
Data generation module for generating synthetic electronics sales data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple
from .utils import get_logger, set_seed, create_output_dir

logger = get_logger(__name__)


class DataGenerator:
    """Generate synthetic electronics sales data."""

    PRODUCTS = {
        'Laptop': {'base_price': 1000, 'base_demand': 5, 'elasticity': -1.8},
        'Smartphone': {'base_price': 700, 'base_demand': 20, 'elasticity': -1.6},
        'Tablet': {'base_price': 500, 'base_demand': 12, 'elasticity': -1.5},
        'Smartwatch': {'base_price': 300, 'base_demand': 15, 'elasticity': -1.2},
        'Headphones': {'base_price': 150, 'base_demand': 25, 'elasticity': -1.0},
        'Bluetooth Speaker': {'base_price': 80, 'base_demand': 30, 'elasticity': -0.9},
        'Gaming Console': {'base_price': 400, 'base_demand': 8, 'elasticity': -1.4},
        'Camera': {'base_price': 600, 'base_demand': 10, 'elasticity': -1.3},
    }

    def __init__(self, output_dir: str = 'data', seed: int = 42):
        """
        Initialize data generator.
        
        Parameters:
        -----------
        output_dir : str
            Output directory for generated data
        seed : int
            Random seed for reproducibility
        """
        set_seed(seed)
        self.output_dir = create_output_dir(output_dir)
        logger.info(f"DataGenerator initialized with output_dir: {output_dir}")

    def generate_data(self, start_date: str = '2022-01-01', 
                     end_date: str = '2023-12-31') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate synthetic sales data for 2 years.
        
        Parameters:
        -----------
        start_date : str
            Start date for data generation
        end_date : str
            End date for data generation
            
        Returns:
        --------
        sales_df : pd.DataFrame
            Daily sales data
        products_meta : pd.DataFrame
            Product metadata
        """
        logger.info("Starting data generation...")
        
        # Create date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        logger.info(f"Generated {len(dates)} days of data")
        
        # Create products metadata
        products_meta = self._create_products_meta()
        
        # Generate sales data
        sales_data = []
        
        for product_name, product_info in self.PRODUCTS.items():
            logger.info(f"Generating data for {product_name}...")
            
            base_price = product_info['base_price']
            base_demand = product_info['base_demand']
            elasticity = product_info['elasticity']
            cost_price = base_price * 0.6
            
            # Initialize price using random walk
            prices = self._generate_prices(base_price, len(dates))
            
            for i, date in enumerate(dates):
                price = prices[i]
                competitor_price = price * np.random.uniform(0.9, 1.1)
                
                # Seasonal effect
                month = date.month
                if month in [10, 11, 12]:  # Festival season
                    seasonal_effect = 1.25
                elif month in [4, 5, 6]:  # Summer
                    seasonal_effect = 1.10
                else:
                    seasonal_effect = 1.0
                
                # Weekend effect
                weekend_effect = 1.15 if date.weekday() >= 5 else 1.0
                
                # Promotion effect
                is_promotion = np.random.random() < 0.07
                promo_effect = 1.30 if is_promotion else 1.0
                
                # Calculate quantity sold using elasticity
                quantity = (
                    base_demand 
                    * (base_price / price) ** abs(elasticity)
                    * seasonal_effect
                    * weekend_effect
                    * promo_effect
                    * np.random.normal(1.0, 0.1)
                )
                
                quantity = max(0, int(np.round(quantity)))
                
                revenue = price * quantity
                profit = (price - cost_price) * quantity
                
                sales_data.append({
                    'date': date,
                    'product': product_name,
                    'price': round(price, 2),
                    'competitor_price': round(competitor_price, 2),
                    'quantity_sold': quantity,
                    'revenue': round(revenue, 2),
                    'profit': round(profit, 2),
                    'is_promotion': is_promotion,
                    'is_weekend': date.weekday() >= 5,
                    'month': month,
                    'day_of_week': date.weekday(),
                })
        
        sales_df = pd.DataFrame(sales_data)
        
        logger.info(f"Generated {len(sales_df)} sales records")
        logger.info(f"Date range: {sales_df['date'].min()} to {sales_df['date'].max()}")
        
        return sales_df, products_meta

    def _create_products_meta(self) -> pd.DataFrame:
        """Create product metadata dataframe."""
        products_data = []
        
        for product_name, info in self.PRODUCTS.items():
            products_data.append({
                'product': product_name,
                'base_price': info['base_price'],
                'cost_price': info['base_price'] * 0.6,
                'base_demand': info['base_demand'],
                'elasticity': info['elasticity'],
            })
        
        return pd.DataFrame(products_data)

    def _generate_prices(self, base_price: float, num_days: int, 
                        volatility: float = 0.02) -> np.ndarray:
        """
        Generate prices using random walk.
        
        Parameters:
        -----------
        base_price : float
            Base price for the product
        num_days : int
            Number of days to generate
        volatility : float
            Price volatility
            
        Returns:
        --------
        prices : np.ndarray
            Generated prices
        """
        prices = np.zeros(num_days)
        prices[0] = base_price
        
        min_price = base_price * 0.70
        max_price = base_price * 1.40
        
        for i in range(1, num_days):
            change = np.random.normal(0, volatility * base_price)
            prices[i] = prices[i - 1] + change
            prices[i] = np.clip(prices[i], min_price, max_price)
        
        return prices

    def save_data(self, sales_df: pd.DataFrame, products_meta: pd.DataFrame) -> None:
        """
        Save generated data to CSV files.
        
        Parameters:
        -----------
        sales_df : pd.DataFrame
            Sales data
        products_meta : pd.DataFrame
            Product metadata
        """
        sales_path = self.output_dir / 'sales_data.csv'
        products_path = self.output_dir / 'products_meta.csv'
        
        sales_df.to_csv(sales_path, index=False)
        products_meta.to_csv(products_path, index=False)
        
        logger.info(f"Sales data saved to {sales_path}")
        logger.info(f"Products metadata saved to {products_path}")


def load_data(data_dir: str = 'data') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load previously generated data.
    
    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
        
    Returns:
    --------
    sales_df : pd.DataFrame
        Sales data
    products_meta : pd.DataFrame
        Product metadata
    """
    data_dir = Path(data_dir)
    sales_df = pd.read_csv(data_dir / 'sales_data.csv')
    products_meta = pd.read_csv(data_dir / 'products_meta.csv')
    
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    
    logger.info(f"Loaded sales data: {len(sales_df)} records")
    logger.info(f"Loaded product metadata: {len(products_meta)} products")
    
    return sales_df, products_meta
