"""
Exploratory Data Analysis module for visualizing sales data.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
from .utils import get_logger, create_output_dir

logger = get_logger(__name__)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class EDA:
    """Exploratory Data Analysis for electronics pricing data."""

    def __init__(self, output_dir: str = 'data/eda_outputs', figsize: tuple = (14, 6)):
        """
        Initialize EDA class.
        
        Parameters:
        -----------
        output_dir : str
            Directory to save plots
        figsize : tuple
            Figure size for plots
        """
        self.output_dir = create_output_dir(output_dir)
        self.figsize = figsize
        logger.info(f"EDA initialized with output_dir: {output_dir}")

    def analyze(self, sales_df: pd.DataFrame, products_meta: pd.DataFrame) -> None:
        """
        Run complete EDA and save all visualizations.
        
        Parameters:
        -----------
        sales_df : pd.DataFrame
            Sales data
        products_meta : pd.DataFrame
            Product metadata
        """
        logger.info("Starting EDA analysis...")
        
        self.revenue_trend(sales_df)
        self.price_vs_demand(sales_df)
        self.revenue_by_product(sales_df, products_meta)
        self.monthly_heatmap(sales_df)
        self.price_distribution(sales_df)
        self.correlation_heatmap(sales_df)
        
        logger.info("EDA analysis completed!")
        logger.info(f"All plots saved to {self.output_dir}")

    def revenue_trend(self, sales_df: pd.DataFrame) -> None:
        """Plot revenue trend with rolling average."""
        logger.info("Generating revenue trend plot...")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Daily revenue
        daily_revenue = sales_df.groupby('date')['revenue'].sum().reset_index()
        daily_revenue = daily_revenue.sort_values('date')
        
        # Rolling average
        rolling_avg = daily_revenue['revenue'].rolling(window=30).mean()
        
        ax.plot(daily_revenue['date'], daily_revenue['revenue'], 
               alpha=0.4, label='Daily Revenue', linewidth=1)
        ax.plot(daily_revenue['date'], rolling_avg, 
               label='30-Day Rolling Average', linewidth=2, color='red')
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Revenue ($)', fontsize=12, fontweight='bold')
        ax.set_title('Revenue Trend Over Time', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'revenue_trend.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Revenue trend plot saved")

    def price_vs_demand(self, sales_df: pd.DataFrame) -> None:
        """Plot price vs demand scatter for each product."""
        logger.info("Generating price vs demand plots...")
        
        products = sales_df['product'].unique()
        n_products = len(products)
        
        n_cols = 2
        n_rows = (n_products + 1) // 2
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n_rows * 5))
        axes = axes.flatten()
        
        for idx, product in enumerate(sorted(products)):
            prod_data = sales_df[sales_df['product'] == product]
            
            scatter = axes[idx].scatter(prod_data['price'], prod_data['quantity_sold'],
                                       c=prod_data['revenue'], cmap='viridis',
                                       alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
            
            axes[idx].set_xlabel('Price ($)', fontsize=10, fontweight='bold')
            axes[idx].set_ylabel('Quantity Sold', fontsize=10, fontweight='bold')
            axes[idx].set_title(f'{product}', fontsize=12, fontweight='bold')
            axes[idx].grid(True, alpha=0.3)
            
            cbar = plt.colorbar(scatter, ax=axes[idx])
            cbar.set_label('Revenue ($)', fontsize=9)
        
        # Remove extra subplots
        for idx in range(n_products, len(axes)):
            fig.delaxes(axes[idx])
        
        plt.suptitle('Price vs Demand by Product', fontsize=16, fontweight='bold', y=1.00)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'price_vs_demand.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Price vs demand plot saved")

    def revenue_by_product(self, sales_df: pd.DataFrame, 
                          products_meta: pd.DataFrame) -> None:
        """Bar chart of total revenue by product."""
        logger.info("Generating revenue by product plot...")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        revenue_by_product = sales_df.groupby('product')['revenue'].sum().sort_values(ascending=False)
        
        colors = sns.color_palette("husl", len(revenue_by_product))
        bars = ax.bar(range(len(revenue_by_product)), revenue_by_product.values, color=colors, edgecolor='black', linewidth=1.5)
        
        ax.set_xticks(range(len(revenue_by_product)))
        ax.set_xticklabels(revenue_by_product.index, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Total Revenue ($)', fontsize=12, fontweight='bold')
        ax.set_title('Total Revenue by Product (2 Years)', fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, revenue_by_product.values)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                   f'${value:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'revenue_by_product.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Revenue by product plot saved")

    def monthly_heatmap(self, sales_df: pd.DataFrame) -> None:
        """Heatmap of revenue by product and month."""
        logger.info("Generating monthly heatmap...")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Create pivot table
        heatmap_data = sales_df.groupby(['product', 'month'])['revenue'].sum().unstack(fill_value=0)
        
        sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlGnBu', 
                   cbar_kws={'label': 'Revenue ($)'}, ax=ax, linewidths=0.5)
        
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel('Product', fontsize=12, fontweight='bold')
        ax.set_title('Revenue Heatmap: Product vs Month', fontsize=14, fontweight='bold', pad=20)
        
        # Set month labels
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels([months[i-1] if i > 0 else '' for i in range(1, 13)], rotation=0)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'monthly_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Monthly heatmap saved")

    def price_distribution(self, sales_df: pd.DataFrame) -> None:
        """Violin plot of price distribution by product."""
        logger.info("Generating price distribution plot...")
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        sns.violinplot(data=sales_df, x='product', y='price', ax=ax, 
                      palette='Set2', inner='box', linewidth=1.5)
        
        ax.set_xlabel('Product', fontsize=12, fontweight='bold')
        ax.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
        ax.set_title('Price Distribution by Product', fontsize=14, fontweight='bold', pad=20)
        ax.tick_params(axis='x', rotation=45)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'price_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Price distribution plot saved")

    def correlation_heatmap(self, sales_df: pd.DataFrame) -> None:
        """Correlation heatmap for numeric features."""
        logger.info("Generating correlation heatmap...")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Select numeric columns
        numeric_cols = ['price', 'competitor_price', 'quantity_sold', 'revenue', 'profit', 'day_of_week', 'month']
        corr_data = sales_df[numeric_cols].corr()
        
        sns.heatmap(corr_data, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={'label': 'Correlation'}, ax=ax,
                   vmin=-1, vmax=1)
        
        ax.set_title('Correlation Matrix: Numeric Features', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Correlation heatmap saved")


def get_summary_statistics(sales_df: pd.DataFrame, products_meta: pd.DataFrame) -> None:
    """Print summary statistics."""
    logger.info("\n" + "="*60)
    logger.info("DATA SUMMARY STATISTICS")
    logger.info("="*60)
    
    logger.info(f"\nTotal Records: {len(sales_df):,}")
    logger.info(f"Date Range: {sales_df['date'].min().date()} to {sales_df['date'].max().date()}")
    logger.info(f"Number of Products: {len(sales_df['product'].unique())}")
    
    logger.info(f"\nTotal Revenue: ${sales_df['revenue'].sum():,.2f}")
    logger.info(f"Total Profit: ${sales_df['profit'].sum():,.2f}")
    logger.info(f"Total Units Sold: {sales_df['quantity_sold'].sum():,}")
    
    logger.info("\nRevenue by Product:")
    revenue_summary = sales_df.groupby('product')[['quantity_sold', 'revenue', 'profit']].sum().sort_values('revenue', ascending=False)
    for product, row in revenue_summary.iterrows():
        logger.info(f"  {product}: ${row['revenue']:,.2f} (Profit: ${row['profit']:,.2f}, Units: {int(row['quantity_sold']):,})")
    
    logger.info("\n" + "="*60)
