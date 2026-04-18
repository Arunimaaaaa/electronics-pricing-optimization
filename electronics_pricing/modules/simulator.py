"""
Simulation module for comparing pricing strategies.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict
from .utils import get_logger, create_output_dir

logger = get_logger(__name__)


class SimulationEngine:
    """Simulate different pricing strategies and compare results."""

    def __init__(self, output_dir: str = 'data/eda_outputs'):
        """
        Initialize SimulationEngine.
        
        Parameters:
        -----------
        output_dir : str
            Output directory for plots
        """
        self.output_dir = create_output_dir(output_dir)
        self.simulation_results = {}
        logger.info("SimulationEngine initialized")

    def simulate_strategies(self, optimizer_results: Dict, demand_forecaster,
                           products_meta: pd.DataFrame) -> Dict:
        """
        Simulate three strategies: Aggressive, Competitive, Premium.
        
        Parameters:
        -----------
        optimizer_results : Dict
            Optimization results from PricingOptimizer
        demand_forecaster : DemandForecaster
            Trained demand forecaster
        products_meta : pd.DataFrame
            Product metadata
            
        Returns:
        --------
        simulation_results : Dict
            Simulation results
        """
        logger.info("Simulating pricing strategies...")
        
        strategies = {
            'Aggressive': 0.85,
            'Competitive': 1.00,
            'Premium': 1.15,
        }
        
        results_all = []
        
        for product in sorted(optimizer_results.keys()):
            logger.info(f"Simulating strategies for {product}...")
            
            opt_result = optimizer_results[product]
            optimal_price = opt_result['optimal_price']
            cost_price = opt_result['cost_price']
            
            product_results = {'product': product}
            
            for strategy_name, multiplier in strategies.items():
                strategy_price = optimal_price * multiplier
                
                # Create feature vector for prediction
                features = np.array([[
                    strategy_price,
                    strategy_price * 1.0,
                    1.0,
                    strategy_price / opt_result['base_price'],
                    0,
                    0,
                    2,
                    6,
                    15,
                    2,
                    26,
                ]])
                
                demand = demand_forecaster.predict(product, features)[0]
                revenue = strategy_price * demand
                profit = (strategy_price - cost_price) * demand
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                product_results[f'{strategy_name}_Price'] = round(strategy_price, 2)
                product_results[f'{strategy_name}_Demand'] = round(demand, 2)
                product_results[f'{strategy_name}_Revenue'] = round(revenue, 2)
                product_results[f'{strategy_name}_Profit'] = round(profit, 2)
                product_results[f'{strategy_name}_Margin%'] = round(margin, 2)
                
                logger.info(f"  {strategy_name}: Price=${strategy_price:.2f}, Revenue=${revenue:.2f}, Profit=${profit:.2f}")
            
            results_all.append(product_results)
        
        self.simulation_results = results_all
        logger.info("Strategy simulation completed!")
        
        return results_all

    def plot_strategy_comparison(self) -> None:
        """Plot strategy comparison charts."""
        logger.info("Generating strategy comparison plots...")
        
        if not self.simulation_results:
            logger.warning("No simulation results available")
            return
        
        results_df = pd.DataFrame(self.simulation_results)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Revenue Comparison
        revenue_cols = [col for col in results_df.columns if 'Revenue' in col]
        revenue_data = results_df[['product'] + revenue_cols].set_index('product')
        revenue_data.columns = [col.replace('_Revenue', '') for col in revenue_data.columns]
        
        revenue_data.plot(kind='bar', ax=axes[0, 0], color=['#e74c3c', '#3498db', '#f39c12'], 
                         edgecolor='black', linewidth=1.5)
        axes[0, 0].set_ylabel('Revenue ($)', fontsize=12, fontweight='bold')
        axes[0, 0].set_title('Revenue by Strategy', fontsize=13, fontweight='bold', pad=15)
        axes[0, 0].legend(title='Strategy', fontsize=10)
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Profit Comparison
        profit_cols = [col for col in results_df.columns if 'Profit' in col and 'Margin' not in col]
        profit_data = results_df[['product'] + profit_cols].set_index('product')
        profit_data.columns = [col.replace('_Profit', '') for col in profit_data.columns]
        
        profit_data.plot(kind='bar', ax=axes[0, 1], color=['#e74c3c', '#3498db', '#f39c12'],
                        edgecolor='black', linewidth=1.5)
        axes[0, 1].set_ylabel('Profit ($)', fontsize=12, fontweight='bold')
        axes[0, 1].set_title('Profit by Strategy', fontsize=13, fontweight='bold', pad=15)
        axes[0, 1].legend(title='Strategy', fontsize=10)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Plot 3: Margin Comparison
        margin_cols = [col for col in results_df.columns if 'Margin%' in col]
        margin_data = results_df[['product'] + margin_cols].set_index('product')
        margin_data.columns = [col.replace('_Margin%', '') for col in margin_data.columns]
        
        margin_data.plot(kind='bar', ax=axes[1, 0], color=['#e74c3c', '#3498db', '#f39c12'],
                        edgecolor='black', linewidth=1.5)
        axes[1, 0].set_ylabel('Profit Margin (%)', fontsize=12, fontweight='bold')
        axes[1, 0].set_title('Profit Margin by Strategy', fontsize=13, fontweight='bold', pad=15)
        axes[1, 0].legend(title='Strategy', fontsize=10)
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Price Comparison
        price_cols = [col for col in results_df.columns if 'Price' in col]
        price_data = results_df[['product'] + price_cols].set_index('product')
        price_data.columns = [col.replace('_Price', '') for col in price_data.columns]
        
        price_data.plot(kind='bar', ax=axes[1, 1], color=['#e74c3c', '#3498db', '#f39c12'],
                       edgecolor='black', linewidth=1.5)
        axes[1, 1].set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        axes[1, 1].set_title('Price by Strategy', fontsize=13, fontweight='bold', pad=15)
        axes[1, 1].legend(title='Strategy', fontsize=10)
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.suptitle('Pricing Strategies Comparison', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'strategy_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Strategy comparison plot saved")

    def get_best_strategy_per_product(self) -> pd.DataFrame:
        """Identify best strategy for each product based on profit."""
        if not self.simulation_results:
            return pd.DataFrame()
        
        results_df = pd.DataFrame(self.simulation_results)
        
        best_strategies = []
        for idx, row in results_df.iterrows():
            profit_values = {
                'Aggressive': row['Aggressive_Profit'],
                'Competitive': row['Competitive_Profit'],
                'Premium': row['Premium_Profit'],
            }
            best_strategy = max(profit_values, key=profit_values.get)
            best_profit = profit_values[best_strategy]
            
            best_strategies.append({
                'Product': row['product'],
                'Best Strategy': best_strategy,
                'Best Profit ($)': round(best_profit, 2),
                'Aggressive Revenue ($)': row['Aggressive_Revenue'],
                'Competitive Revenue ($)': row['Competitive_Revenue'],
                'Premium Revenue ($)': row['Premium_Revenue'],
            })
        
        return pd.DataFrame(best_strategies).sort_values('Best Profit ($)', ascending=False)

    def get_simulation_summary(self) -> pd.DataFrame:
        """Get detailed simulation summary."""
        return pd.DataFrame(self.simulation_results)
