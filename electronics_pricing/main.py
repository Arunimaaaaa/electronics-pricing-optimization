"""
Main script to execute the complete pricing optimization pipeline.
"""
import logging
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules import (
    set_seed, get_logger, create_output_dir,
    DataGenerator, load_data, EDA, get_summary_statistics,
    DemandForecaster, ElasticityAnalyzer, get_elasticity_summary,
    PricingOptimizer, SimulationEngine
)

logger = get_logger(__name__)


def main():
    """Run complete pipeline."""
    
    logger.info("\n" + "="*80)
    logger.info("ELECTRONICS DYNAMIC PRICING OPTIMIZATION SYSTEM")
    logger.info("="*80 + "\n")
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Create output directories
    create_output_dir('data')
    create_output_dir('data/eda_outputs')
    create_output_dir('models')
    
    # ============================================================================
    # STEP 1: DATA GENERATION
    # ============================================================================
    logger.info("\n[STEP 1] GENERATING SYNTHETIC DATA...")
    logger.info("-"*80)
    
    generator = DataGenerator(output_dir='data', seed=42)
    sales_df, products_meta = generator.generate_data(
        start_date='2022-01-01',
        end_date='2023-12-31'
    )
    generator.save_data(sales_df, products_meta)
    
    # ============================================================================
    # STEP 2: EXPLORATORY DATA ANALYSIS
    # ============================================================================
    logger.info("\n[STEP 2] EXPLORATORY DATA ANALYSIS...")
    logger.info("-"*80)
    
    get_summary_statistics(sales_df, products_meta)
    
    eda = EDA(output_dir='data/eda_outputs')
    eda.analyze(sales_df, products_meta)
    
    # ============================================================================
    # STEP 3: DEMAND FORECASTING
    # ============================================================================
    logger.info("\n[STEP 3] TRAINING DEMAND FORECASTING MODELS...")
    logger.info("-"*80)
    
    forecaster = DemandForecaster(output_dir='data', models_dir='models')
    training_results = forecaster.train_all(sales_df, products_meta, test_size=0.2)
    forecaster.save_models()
    
    logger.info("\nTraining Results Summary:")
    for product, result in sorted(training_results.items()):
        logger.info(f"\n{product}:")
        logger.info(f"  Best Model: {result['best_model']}")
        for model_name, metrics in result['metrics'].items():
            logger.info(f"  {model_name}:")
            logger.info(f"    R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}")
    
    # ============================================================================
    # STEP 4: ELASTICITY ANALYSIS
    # ============================================================================
    logger.info("\n[STEP 4] ANALYZING PRICE ELASTICITY...")
    logger.info("-"*80)
    
    elasticity_analyzer = ElasticityAnalyzer(output_dir='data/eda_outputs')
    elasticity_results = elasticity_analyzer.compute_elasticity(sales_df)
    elasticity_analyzer.print_summary()
    elasticity_analyzer.plot_elasticity_comparison()
    
    elasticity_summary = get_elasticity_summary(elasticity_results)
    logger.info("\nElasticity Summary:")
    logger.info(elasticity_summary.to_string(index=False))
    
    # ============================================================================
    # STEP 5: PRICE OPTIMIZATION
    # ============================================================================
    logger.info("\n[STEP 5] OPTIMIZING PRICES FOR REVENUE...")
    logger.info("-"*80)
    
    optimizer = PricingOptimizer(output_dir='data/eda_outputs')
    optimization_results = optimizer.optimize_prices(
        products_meta, forecaster,
        objective='revenue',
        n_prices=100
    )
    optimizer.plot_optimization_curves()
    
    opt_summary = optimizer.get_optimization_summary()
    logger.info("\nPrice Optimization Summary:")
    logger.info(opt_summary.to_string(index=False))
    
    # ============================================================================
    # STEP 6: STRATEGY SIMULATION
    # ============================================================================
    logger.info("\n[STEP 6] SIMULATING PRICING STRATEGIES...")
    logger.info("-"*80)
    
    simulator = SimulationEngine(output_dir='data/eda_outputs')
    simulation_results = simulator.simulate_strategies(
        optimization_results, forecaster, products_meta
    )
    simulator.plot_strategy_comparison()
    
    best_strategies = simulator.get_best_strategy_per_product()
    logger.info("\nBest Strategy by Product (for Profit):")
    logger.info(best_strategies.to_string(index=False))
    
    # ============================================================================
    # STEP 7: FINAL SUMMARY & RECOMMENDATIONS
    # ============================================================================
    logger.info("\n" + "="*80)
    logger.info("FINAL RECOMMENDATIONS SUMMARY")
    logger.info("="*80)
    
    # Merge all results
    final_summary = []
    for product in sorted(products_meta['product'].values):
        opt_result = optimization_results.get(product, {})
        best_strat = best_strategies[best_strategies['Product'] == product].iloc[0] if product in best_strategies['Product'].values else None
        
        if opt_result and best_strat is not None:
            base_price = opt_result['base_price']
            optimal_price = opt_result['optimal_price']
            best_strategy = best_strat['Best Strategy']
            strategy_multiplier = {'Aggressive': 0.85, 'Competitive': 1.00, 'Premium': 1.15}
            recommended_price = optimal_price * strategy_multiplier.get(best_strategy, 1.0)
            
            current_revenue = base_price * 10  # Approximate
            optimal_revenue = opt_result['expected_revenue']
            uplift = ((optimal_revenue - current_revenue) / current_revenue * 100) if current_revenue > 0 else 0
            
            final_summary.append({
                'Product': product,
                'Current Price ($)': base_price,
                'Optimal Price ($)': round(optimal_price, 2),
                'Recommended Strategy': best_strategy,
                'Final Price ($)': round(recommended_price, 2),
                'Expected Revenue ($)': round(opt_result['expected_revenue'], 2),
                'Revenue Uplift (%)': round(uplift, 2),
            })
    
    final_df = pd.DataFrame(final_summary)
    logger.info("\nFinal Pricing Recommendations:")
    logger.info(final_df.to_string(index=False))
    
    # Save final summary
    final_df.to_csv('data/final_recommendations.csv', index=False)
    logger.info("\nFinal recommendations saved to data/final_recommendations.csv")
    
    logger.info("\n" + "="*80)
    logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    logger.info("="*80)
    logger.info("\nGenerated Outputs:")
    logger.info("  - CSV Data: data/sales_data.csv, data/products_meta.csv")
    logger.info("  - Visualizations: data/eda_outputs/")
    logger.info("  - Models: models/")
    logger.info("  - Recommendations: data/final_recommendations.csv")
    logger.info("\nYou can now run the Streamlit dashboard with:")
    logger.info("  streamlit run dashboard/app.py")
    logger.info("="*80 + "\n")


if __name__ == '__main__':
    import pandas as pd
    main()
