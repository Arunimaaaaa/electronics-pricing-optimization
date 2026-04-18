"""
Elasticity analysis module using log-log regression.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.formula.api import ols
from pathlib import Path
from typing import Dict
from .utils import get_logger, create_output_dir

logger = get_logger(__name__)


class ElasticityAnalyzer:
    """Compute price elasticity of demand using log-log regression."""

    def __init__(self, output_dir: str = 'data/eda_outputs'):
        """
        Initialize ElasticityAnalyzer.
        
        Parameters:
        -----------
        output_dir : str
            Output directory for plots
        """
        self.output_dir = create_output_dir(output_dir)
        self.elasticities = {}
        logger.info("ElasticityAnalyzer initialized")

    def compute_elasticity(self, sales_df: pd.DataFrame) -> Dict:
        """
        Compute price elasticity for all products.
        
        For each product, use log-log regression:
        ln(quantity + 1) ~ ln(price) + ln(competitor_price) + promotion + month + ...
        
        Parameters:
        -----------
        sales_df : pd.DataFrame
            Sales data
            
        Returns:
        --------
        elasticities : Dict
            Elasticity statistics per product
        """
        logger.info("Computing price elasticity...")
        
        elasticities = {}
        
        for product in sorted(sales_df['product'].unique()):
            logger.info(f"Computing elasticity for {product}...")
            
            prod_data = sales_df[sales_df['product'] == product].copy()
            
            # Create log-transformed variables
            prod_data['log_quantity'] = np.log(prod_data['quantity_sold'] + 1)
            prod_data['log_price'] = np.log(prod_data['price'])
            prod_data['log_competitor_price'] = np.log(prod_data['competitor_price'])
            
            # Fit log-log regression
            model = ols('log_quantity ~ log_price + log_competitor_price + is_promotion + C(month)', 
                       data=prod_data).fit()
            
            # Extract elasticity coefficient
            elasticity = model.params.get('log_price', np.nan)
            pvalue = model.pvalues.get('log_price', np.nan)
            r_squared = model.rsquared
            
            # Interpretation
            if abs(elasticity) > 1:
                interpretation = "Elastic (demand changes more than price)"
            else:
                interpretation = "Inelastic (demand changes less than price)"
            
            elasticities[product] = {
                'elasticity': elasticity,
                'p_value': pvalue,
                'r_squared': r_squared,
                'interpretation': interpretation,
                'model': model,
            }
            
            logger.info(f"  Elasticity: {elasticity:.3f} (p-value: {pvalue:.4f})")
            logger.info(f"  R²: {r_squared:.4f} - {interpretation}")
        
        self.elasticities = elasticities
        logger.info("Elasticity computation completed!")
        
        return elasticities

    def plot_elasticity_comparison(self) -> None:
        """Plot elasticity comparison across products."""
        logger.info("Generating elasticity comparison plot...")
        
        if not self.elasticities:
            logger.warning("No elasticities computed yet")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        products = list(self.elasticities.keys())
        elasticity_values = [self.elasticities[p]['elasticity'] for p in products]
        interpretations = [self.elasticities[p]['interpretation'] for p in products]
        
        # Plot 1: Elasticity values
        colors = ['#e74c3c' if e < -1 else '#3498db' for e in elasticity_values]
        bars = ax1.barh(products, elasticity_values, color=colors, edgecolor='black', linewidth=1.5)
        
        ax1.axvline(x=-1, color='red', linestyle='--', linewidth=2, label='Unit Elasticity')
        ax1.set_xlabel('Price Elasticity of Demand', fontsize=12, fontweight='bold')
        ax1.set_title('Price Elasticity by Product', fontsize=14, fontweight='bold', pad=20)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, elasticity_values)):
            ax1.text(value - 0.1 if value < 0 else value + 0.05, bar.get_y() + bar.get_height()/2,
                    f'{value:.3f}', ha='right' if value < 0 else 'left', va='center', 
                    fontsize=9, fontweight='bold')
        
        # Plot 2: R² values
        r_squared_values = [self.elasticities[p]['r_squared'] for p in products]
        bars2 = ax2.barh(products, r_squared_values, color='#2ecc71', edgecolor='black', linewidth=1.5)
        
        ax2.set_xlabel('R² (Model Fit)', fontsize=12, fontweight='bold')
        ax2.set_title('Model Fit (R²) by Product', fontsize=14, fontweight='bold', pad=20)
        ax2.set_xlim(0, 1)
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars2, r_squared_values)):
            ax2.text(value - 0.05, bar.get_y() + bar.get_height()/2,
                    f'{value:.3f}', ha='right', va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'elasticity_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Elasticity comparison plot saved")

    def print_summary(self) -> None:
        """Print elasticity summary."""
        logger.info("\n" + "="*80)
        logger.info("PRICE ELASTICITY ANALYSIS SUMMARY")
        logger.info("="*80)
        
        if not self.elasticities:
            logger.warning("No elasticities computed")
            return
        
        elastic_count = 0
        inelastic_count = 0
        
        for product, stats in sorted(self.elasticities.items()):
            logger.info(f"\n{product}:")
            logger.info(f"  Elasticity: {stats['elasticity']:.4f}")
            logger.info(f"  p-value: {stats['p_value']:.4f} {'(Significant)' if stats['p_value'] < 0.05 else '(Not Significant)'}")
            logger.info(f"  R²: {stats['r_squared']:.4f}")
            logger.info(f"  Type: {stats['interpretation']}")
            
            if abs(stats['elasticity']) > 1:
                elastic_count += 1
            else:
                inelastic_count += 1
        
        logger.info("\n" + "-"*80)
        logger.info(f"Summary: {elastic_count} Elastic Products, {inelastic_count} Inelastic Products")
        logger.info("="*80 + "\n")


def get_elasticity_summary(elasticities: Dict) -> pd.DataFrame:
    """Create a dataframe summary of elasticities."""
    summary_data = []
    
    for product, stats in elasticities.items():
        summary_data.append({
            'Product': product,
            'Elasticity': round(stats['elasticity'], 4),
            'P-value': round(stats['p_value'], 4),
            'R²': round(stats['r_squared'], 4),
            'Type': 'Elastic' if abs(stats['elasticity']) > 1 else 'Inelastic',
        })
    
    return pd.DataFrame(summary_data).sort_values('Elasticity')
