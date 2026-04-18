"""
Price optimization module.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Tuple
from .utils import get_logger, create_output_dir

logger = get_logger(__name__)


class PricingOptimizer:
    """Optimize product prices to maximize revenue or profit."""

    def __init__(self, output_dir: str = 'data/eda_outputs'):
        """
        Initialize PricingOptimizer.
        
        Parameters:
        -----------
        output_dir : str
            Output directory for plots
        """
        self.output_dir = create_output_dir(output_dir)
        self.optimization_results = {}
        logger.info("PricingOptimizer initialized")

    def optimize_prices(self, products_meta: pd.DataFrame, demand_forecaster,
                       objective: str = 'revenue', n_prices: int = 100) -> Dict:
        """
        Optimize prices for all products.
        
        Parameters:
        -----------
        products_meta : pd.DataFrame
            Product metadata
        demand_forecaster : DemandForecaster
            Trained demand forecaster
        objective : str
            'revenue' or 'profit'
        n_prices : int
            Number of prices to evaluate
            
        Returns:
        --------
        results : Dict
            Optimization results per product
        """
        logger.info(f"Optimizing prices for {objective}...")
        
        results = {}
        
        for _, product_row in products_meta.iterrows():
            product = product_row['product']
            base_price = product_row['base_price']
            cost_price = product_row['cost_price']
            
            logger.info(f"Optimizing {product}...")
            
            # Generate price range
            min_price = base_price * 0.60
            max_price = base_price * 1.40
            test_prices = np.linspace(min_price, max_price, n_prices)
            
            # Predict demand for each price
            demands = []
            revenues = []
            profits = []
            
            for price in test_prices:
                # Create feature vector (using average values for other features)
                features = np.array([[
                    price,  # price
                    price * 1.0,  # competitor_price (assume equal)
                    1.0,  # price_ratio
                    price / base_price,  # price_vs_base
                    0,  # is_promotion
                    0,  # is_weekend
                    2,  # day_of_week (mid-week)
                    6,  # month (mid-year)
                    15,  # day_of_month
                    2,  # quarter
                    26,  # week_of_year
                ]])
                
                demand = demand_forecaster.predict(product, features)[0]
                revenue = price * demand
                profit = (price - cost_price) * demand
                
                demands.append(demand)
                revenues.append(revenue)
                profits.append(profit)
            
            # Find optimal price
            if objective == 'revenue':
                opt_idx = np.argmax(revenues)
            else:  # profit
                opt_idx = np.argmax(profits)
            
            optimal_price = test_prices[opt_idx]
            optimal_demand = demands[opt_idx]
            optimal_revenue = revenues[opt_idx]
            optimal_profit = profits[opt_idx]
            
            results[product] = {
                'optimal_price': round(optimal_price, 2),
                'expected_demand': round(optimal_demand, 2),
                'expected_revenue': round(optimal_revenue, 2),
                'expected_profit': round(optimal_profit, 2),
                'base_price': base_price,
                'cost_price': cost_price,
                'price_curve': pd.DataFrame({
                    'price': test_prices,
                    'demand': demands,
                    'revenue': revenues,
                    'profit': profits,
                }),
            }
            
            logger.info(f"  Optimal Price: ${optimal_price:.2f}")
            logger.info(f"  Expected Demand: {optimal_demand:.2f} units")
            
            if objective == 'revenue':
                logger.info(f"  Expected Revenue: ${optimal_revenue:.2f}")
            else:
                logger.info(f"  Expected Profit: ${optimal_profit:.2f}")
        
        self.optimization_results = results
        logger.info("Price optimization completed!")
        
        return results

    def plot_optimization_curves(self, product: str = None) -> None:
        """
        Plot price vs revenue/profit curves.
        
        Parameters:
        -----------
        product : str
            Product name (if None, plot all)
        """
        logger.info("Generating optimization curves...")
        
        if product:
            if product not in self.optimization_results:
                logger.warning(f"Product {product} not found in results")
                return
            
            self._plot_single_product(product)
        else:
            products = list(self.optimization_results.keys())
            n_products = len(products)
            n_cols = 2
            n_rows = (n_products + 1) // 2
            
            fig = plt.figure(figsize=(16, n_rows * 5))
            
            for idx, product in enumerate(sorted(products), 1):
                ax = plt.subplot(n_rows, n_cols, idx)
                self._plot_on_axis(ax, product)
            
            plt.suptitle('Price Optimization Curves', fontsize=16, fontweight='bold', y=0.995)
            plt.tight_layout()
            plt.savefig(self.output_dir / 'price_optimization_curves.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        logger.info("Optimization curves plot saved")

    def _plot_single_product(self, product: str) -> None:
        """Plot optimization curve for a single product."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        result = self.optimization_results[product]
        curve_df = result['price_curve']
        
        optimal_price = result['optimal_price']
        optimal_revenue = result['expected_revenue']
        optimal_profit = result['expected_profit']
        
        # Revenue curve
        ax1.plot(curve_df['price'], curve_df['revenue'], linewidth=2.5, color='#3498db', label='Revenue')
        ax1.scatter([optimal_price], [optimal_revenue], color='red', s=200, zorder=5, 
                   marker='*', edgecolors='darkred', linewidth=2, label=f'Optimal: ${optimal_price:.2f}')
        ax1.set_xlabel('Price ($)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Revenue ($)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{product} - Revenue Optimization', fontsize=13, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Profit curve
        ax2.plot(curve_df['price'], curve_df['profit'], linewidth=2.5, color='#2ecc71', label='Profit')
        ax2.scatter([optimal_price], [optimal_profit], color='red', s=200, zorder=5,
                   marker='*', edgecolors='darkred', linewidth=2, label=f'Optimal: ${optimal_price:.2f}')
        ax2.set_xlabel('Price ($)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Profit ($)', fontsize=12, fontweight='bold')
        ax2.set_title(f'{product} - Profit Optimization', fontsize=13, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f'optimization_{product.replace(" ", "_")}.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_on_axis(self, ax, product: str) -> None:
        """Plot optimization curve on given axis."""
        result = self.optimization_results[product]
        curve_df = result['price_curve']
        
        optimal_price = result['optimal_price']
        optimal_revenue = result['expected_revenue']
        
        ax.plot(curve_df['price'], curve_df['revenue'], linewidth=2, color='#3498db')
        ax.scatter([optimal_price], [optimal_revenue], color='red', s=150, zorder=5, marker='*', edgecolors='darkred', linewidth=1.5)
        
        ax.set_xlabel('Price ($)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Revenue ($)', fontsize=10, fontweight='bold')
        ax.set_title(f'{product}\nOptimal: ${optimal_price:.2f}', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)

    def get_optimization_summary(self) -> pd.DataFrame:
        """Get summary of optimization results."""
        summary_data = []
        
        for product, result in sorted(self.optimization_results.items()):
            summary_data.append({
                'Product': product,
                'Base Price ($)': result['base_price'],
                'Optimal Price ($)': result['optimal_price'],
                'Expected Demand': result['expected_demand'],
                'Expected Revenue ($)': result['expected_revenue'],
                'Expected Profit ($)': result['expected_profit'],
            })
        
        return pd.DataFrame(summary_data)
