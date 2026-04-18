# Quick Start Guide - Electronics Dynamic Pricing System

## For First-Time Users

### Step 1: Install Dependencies
```bash
cd electronics_pricing
pip install -r requirements.txt
```

**What gets installed**:
- pandas, numpy (data processing)
- scikit-learn, xgboost (machine learning)
- matplotlib, seaborn, plotly (visualization)
- streamlit (interactive dashboard)
- statsmodels (statistical analysis)

### Step 2: Generate Data & Run Analysis Pipeline
```bash
python main.py
```

**What happens**:
1. ⚙️ Generates 2 years of synthetic sales data (5,840 records)
2. 📊 Creates 6 EDA visualizations
3. 🤖 Trains 3 ML models per product (24 total)
4. 📈 Analyzes price elasticity
5. 🎯 Optimizes prices for revenue
6. 🎪 Simulates pricing strategies
7. 💾 Saves all results and models

**Duration**: ~30-40 seconds
**Output**: Console logs showing progress step-by-step

### Step 3: View Results on Dashboard
```bash
streamlit run dashboard/app.py
```

**What opens**:
- Interactive web dashboard at `http://localhost:8501`
- 6 different analysis pages
- Real-time product selector
- Interactive charts and data explorer

**Keyboard Shortcut**: Press `q` to quit

---

## What Users Will See

### Console Output (After Running main.py)
```
================================================================================
ELECTRONICS DYNAMIC PRICING OPTIMIZATION SYSTEM
================================================================================

[STEP 1] GENERATING SYNTHETIC DATA...
✓ Generated 730 days of data for 8 products
✓ Created 5,840 sales records

[STEP 2] EXPLORATORY DATA ANALYSIS...
✓ Total Revenue: $38,466,024.42
✓ Total Profit: $14,386,644.42
✓ 6 visualizations saved

[STEP 3] TRAINING DEMAND FORECASTING MODELS...
✓ Trained Linear Regression, Random Forest, XGBoost
✓ Best model selected based on R² for each product

[STEP 4] ANALYZING PRICE ELASTICITY...
✓ Elastic Products: 6
✓ Inelastic Products: 2

[STEP 5] OPTIMIZING PRICES FOR REVENUE...
✓ Optimal prices calculated for all 8 products

[STEP 6] SIMULATING PRICING STRATEGIES...
✓ Compared Aggressive, Competitive, Premium strategies

FINAL RECOMMENDATIONS SUMMARY
================================================================================
Product          | Current Price | Optimal Price | Best Strategy | Uplift %
Smartphone       | $700          | $578.38       | Premium       | 131.19%
Headphones       | $150          | $210.00       | Premium       | 278.21%
Tablet           | $500          | $364.65       | Premium       | 60.96%
...
================================================================================
PIPELINE EXECUTION COMPLETED SUCCESSFULLY!
```

### Generated Files & Folders

```
✅ data/
   📄 sales_data.csv - Full transaction history
   📄 products_meta.csv - Product specifications
   📄 final_recommendations.csv - Pricing recommendations
   📁 eda_outputs/ - Contains 9 visualization PNG files:
      📊 revenue_trend.png
      📊 price_vs_demand.png
      📊 revenue_by_product.png
      📊 monthly_heatmap.png
      📊 price_distribution.png
      📊 correlation_heatmap.png
      📊 elasticity_analysis.png
      📊 price_optimization_curves.png
      📊 strategy_comparison.png

✅ models/
   🤖 24 trained ML models (Linear Regression, Random Forest, XGBoost)
   🔧 8 feature scalers for preprocessing

✅ main.py - Main pipeline script
✅ requirements.txt - Dependencies
✅ README.md - Full documentation
```

---

## What Users Can Do with the Dashboard

### Page 1: Overview
- **View**: 4 KPI cards (Revenue, Profit, Units, Price)
- **See**: Revenue trend with seasonal patterns
- **Explore**: Revenue breakdown by product
- **Do**: Identify top performers

### Page 2: Price Analysis
- **Select**: Any product from dropdown
- **View**: Price vs quantity-sold scatter plot
- **See**: Price statistics and distribution
- **Understand**: Product elasticity visually

### Page 3: Forecasting
- **Compare**: 3 ML models side-by-side
- **Check**: R², RMSE, MAE metrics
- **Evaluate**: Model accuracy and performance
- **Learn**: Which model works best

### Page 4: Optimization
- **Set**: Revenue or Profit toggle
- **View**: Price-vs-revenue curve
- **Find**: Optimal price point (marked with star)
- **Predict**: Expected demand and profit

### Page 5: Strategies
- **Compare**: Aggressive, Competitive, Premium pricing
- **See**: Revenue, profit, and margin for each
- **Analyze**: 4 comparison charts
- **Decide**: Best strategy per product

### Page 6: Data Explorer
- **Filter**: By date range and product
- **View**: Raw transaction data (sortable table)
- **Export**: Download as CSV
- **Analyze**: Individual transactions

---

## User Workflow

### For Business Users:
1. Run `python main.py` once (builds everything)
2. Run `streamlit run dashboard/app.py`
3. Select each product
4. Read the "Final Price" recommendation
5. Check the "Revenue Uplift" percentage
6. Review the "Best Strategy" suggestion
7. Export data if needed

### For Data Scientists:
1. Check `data/sales_data.csv` for raw data
2. Review `models/` folder for trained models
3. Load models using joblib: `joblib.load('models/Smartphone_Random_Forest.pkl')`
4. Make predictions: `model.predict(features)`
5. Modify `main.py` to test different parameters

### For Developers:
1. Examine `modules/` for clean, modular code
2. Use individual modules in your own scripts
3. Import specific analyzers: `from modules import DemandForecaster`
4. Extend dashboard by editing `dashboard/app.py`
5. Add new visualizations in `modules/eda.py`

---

## Common Tasks

### Task 1: See Revenue Trends
```bash
python main.py
# Look for "Revenue Trend Over Time" section
# Find PNG at: data/eda_outputs/revenue_trend.png
```

### Task 2: Check Product Elasticity
- Run dashboard → Page 2 → Select product
- Or open: data/eda_outputs/elasticity_analysis.png

### Task 3: View Pricing Recommendations
```bash
# Open with Excel:
data/final_recommendations.csv
```

### Task 4: Compare Strategies
- Run dashboard → Page 5
- See 4 charts comparing Aggressive/Competitive/Premium

### Task 5: Predict Demand for Custom Price
```python
from modules import DemandForecaster
import numpy as np

forecaster = DemandForecaster(models_dir='models')
forecaster.load_models()

features = np.array([[
    750,      # price
    750,      # competitor_price
    1.0,      # price_ratio
    1.07,     # price_vs_base
    0,        # is_promotion
    0,        # is_weekend
    2,        # day_of_week
    6,        # month
    15,       # day_of_month
    2,        # quarter
    26        # week_of_year
]])

demand = forecaster.predict('Smartphone', features)
print(f"Expected demand: {demand[0]:.2f} units")
```

---

## Troubleshooting

### Issue: ImportError when running main.py
**Solution**: Install missing packages
```bash
pip install -r requirements.txt
```

### Issue: Dashboard won't open
**Solution**: Check port 8501 is available
```bash
streamlit run dashboard/app.py --server.port=8502  # Use different port
```

### Issue: Models folder is empty
**Solution**: Run `python main.py` first to train models
```bash
python main.py  # Trains and saves models
```

### Issue: CSV files won't open in Excel
**Solution**: They're actually readable, just open normally:
```bash
data/sales_data.csv
```

---

## System Requirements

- **Python**: 3.8+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB for dependencies + generated files
- **OS**: Windows/Mac/Linux

---

## Next Steps

1. ✅ Run `python main.py` (2-3 minutes first time)
2. ✅ Run `streamlit run dashboard/app.py`
3. ✅ Explore each page on dashboard
4. ✅ Review visualizations in `data/eda_outputs/`
5. ✅ Check recommendations in `data/final_recommendations.csv`
6. ✅ Export data or integrate into your business process

---

**Enjoy exploring your pricing optimization insights!** 🚀
