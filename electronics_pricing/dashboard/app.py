"""
Interactive Streamlit Dashboard for Electronics Pricing Optimization System.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
from datetime import datetime

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules import (
    load_data, get_logger, DemandForecaster,
    ElasticityAnalyzer, get_elasticity_summary,
    PricingOptimizer, SimulationEngine
)

logger = get_logger(__name__)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Electronics Pricing Dashboard",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.1rem;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_resource
def load_all_data():
    """Load all required data and models."""
    try:
        sales_df, products_meta = load_data('data')
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        
        # Load models
        forecaster = DemandForecaster(output_dir='data', models_dir='models')
        forecaster.load_models()
        
        # Load recommendations if available
        try:
            recommendations = pd.read_csv('data/final_recommendations.csv')
        except:
            recommendations = None
        
        return sales_df, products_meta, forecaster, recommendations
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None

sales_df, products_meta, forecaster, recommendations = load_all_data()

if sales_df is None:
    st.error("Failed to load data. Please ensure data files exist in the data/ directory.")
    st.stop()

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================
st.sidebar.markdown("## Configuration")

# Product selector
product_options = sorted(sales_df['product'].unique())
selected_product = st.sidebar.selectbox(
    "Select Product",
    product_options,
    index=0
)

# Objective selector
objective = st.sidebar.radio(
    "Optimization Objective",
    ["Revenue", "Profit"],
    horizontal=False
)

st.sidebar.markdown("---")

# Information section
st.sidebar.markdown("""
## Project Overview

**Electronics Dynamic Pricing Optimization System**

This dashboard helps businesses optimize product pricing to maximize revenue or profit using:
- Machine Learning demand forecasting
- Price elasticity analysis
- Strategy simulation

**Data Range:** 2022-01-01 to 2023-12-31
""")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
st.markdown('<div class="main-header">Electronics Pricing Dashboard</div>', unsafe_allow_html=True)
st.markdown("Optimize pricing strategy using AI-driven demand forecasting and elasticity analysis")

# Navigation
tabs = st.tabs([
    "Overview",
    "Price Analysis",
    "Forecasting",
    "Optimization",
    "Strategies",
    "Data Explorer"
])

# ============================================================================
# TAB 1: OVERVIEW
# ============================================================================
with tabs[0]:
    st.markdown('<div class="section-header">Dashboard Overview</div>', unsafe_allow_html=True)
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = sales_df['revenue'].sum()
    total_profit = sales_df['profit'].sum()
    total_units = sales_df['quantity_sold'].sum()
    avg_price = sales_df['price'].mean()
    
    with col1:
        st.metric(
            "Total Revenue",
            f"${total_revenue:,.0f}",
            delta=None,
            help="Total revenue across all products"
        )
    
    with col2:
        st.metric(
            "Total Profit",
            f"${total_profit:,.0f}",
            delta=None,
            help="Total profit across all products"
        )
    
    with col3:
        st.metric(
            "Units Sold",
            f"{total_units:,.0f}",
            delta=None,
            help="Total units sold"
        )
    
    with col4:
        st.metric(
            "Avg Price",
            f"${avg_price:.2f}",
            delta=None,
            help="Average selling price"
        )
    
    # Revenue trend
    st.markdown('<div class="subheader">Revenue Trend Over Time</div>', unsafe_allow_html=True)
    
    daily_revenue = sales_df.groupby('date')['revenue'].sum().reset_index().sort_values('date')
    rolling_avg = daily_revenue['revenue'].rolling(window=30).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['revenue'],
        mode='lines',
        name='Daily Revenue',
        line=dict(color='rgba(31, 119, 180, 0.3)', width=1),
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=rolling_avg,
        mode='lines',
        name='30-Day Moving Average',
        line=dict(color='#FF6B6B', width=3),
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Revenue:</b> $%{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        height=400,
        hovermode='x unified',
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        xaxis_title='Date',
        yaxis_title='Revenue ($)',
        font=dict(size=11),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue by product
    st.markdown('<div class="subheader">Revenue Distribution by Product</div>', unsafe_allow_html=True)
    
    revenue_by_product = sales_df.groupby('product')['revenue'].sum().sort_values(ascending=False)
    
    # Create DataFrame for Plotly compatibility
    revenue_df = pd.DataFrame({
        'Product': revenue_by_product.index,
        'Revenue': revenue_by_product.values
    })
    
    fig = px.bar(
        revenue_df,
        x='Revenue',
        y='Product',
        orientation='h',
        color='Revenue',
        color_continuous_scale='Viridis',
        text='Revenue',
        labels={'Revenue': 'Total Revenue ($)', 'Product': 'Product'}
    )
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside', 
                     hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>')
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: PRICE ANALYSIS
# ============================================================================
with tabs[1]:
    st.markdown('<div class="section-header">Price Analysis for ' + selected_product + '</div>', unsafe_allow_html=True)
    
    product_data = sales_df[sales_df['product'] == selected_product]
    
    # Price vs Demand Scatter
    st.markdown('<div class="subheader">Price vs Demand Relationship</div>', unsafe_allow_html=True)
    
    fig = px.scatter(
        product_data,
        x='price',
        y='quantity_sold',
        color='revenue',
        size='revenue',
        hover_data={'price': '$:.2f', 'quantity_sold': ':.0f', 'revenue': '$:,.0f'},
        color_continuous_scale='Viridis',
        labels={'price': 'Price ($)', 'quantity_sold': 'Quantity Sold'}
    )
    fig.update_layout(
        height=450,
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        hovermode='closest',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Price", f"${product_data['price'].mean():.2f}", help="Average price")
    with col2:
        st.metric("Price Range", f"${product_data['price'].min():.2f} - ${product_data['price'].max():.2f}", help="Min-Max price")
    with col3:
        st.metric("Avg Demand", f"{product_data['quantity_sold'].mean():.0f} units", help="Average quantity sold")
    with col4:
        st.metric("Total Sold", f"{product_data['quantity_sold'].sum():,} units", help="Total units sold")
    
    # Price distribution
    st.markdown('<div class="subheader">Price Distribution</div>', unsafe_allow_html=True)
    
    fig = px.histogram(
        product_data,
        x='price',
        nbins=30,
        labels={'price': 'Price ($)', 'count': 'Frequency'},
        color_discrete_sequence=['#3498db'],
        title='Price Distribution Analysis'
    )
    fig.update_layout(
        height=350,
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode='x unified'
    )
    fig.update_xaxes(title_text='Price ($)')
    fig.update_yaxes(title_text='Frequency')
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: FORECASTING
# ============================================================================
with tabs[2]:
    st.markdown('<div class="section-header">Demand Forecasting Models</div>', unsafe_allow_html=True)
    
    if selected_product in forecaster.metrics:
        metrics = forecaster.get_metrics(selected_product)
        
        # Model Performance Table
        st.markdown('<div class="subheader">Model Performance Comparison</div>', unsafe_allow_html=True)
        
        metrics_data = []
        for model_name, model_metrics in metrics.items():
            metrics_data.append({
                'Model': model_name,
                'R² Score': f"{model_metrics['r2']:.4f}",
                'RMSE': f"{model_metrics['rmse']:.2f}",
                'MAE': f"{model_metrics['mae']:.2f}",
            })
        
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        
        # Model Performance Chart
        st.markdown('<div class="subheader">R² Score Comparison</div>', unsafe_allow_html=True)
        
        r2_data = {model_name: metrics[model_name]['r2'] for model_name in metrics.keys()}
        
        # Create DataFrame for Plotly compatibility
        r2_df = pd.DataFrame({
            'Model': list(r2_data.keys()),
            'R2_Score': list(r2_data.values())
        })
        
        fig = px.bar(
            r2_df,
            x='Model',
            y='R2_Score',
            labels={'R2_Score': 'R² Score', 'Model': 'Model'},
            color='R2_Score',
            color_continuous_scale='Greens',
            text='R2_Score'
        )
        fig.update_traces(texttemplate='%{text:.4f}', textposition='outside',
                         hovertemplate='<b>%{x}</b><br>R²: %{y:.4f}<extra></extra>')
        fig.update_layout(
            height=350,
            plot_bgcolor='rgba(240, 242, 246, 0.5)',
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Best Model Indicator
        best_model = max(metrics.items(), key=lambda x: x[1]['r2'])
        st.success(f"Best Model: **{best_model[0]}** (R² = {best_model[1]['r2']:.4f})")
    else:
        st.warning("No metrics available for selected product")

# ============================================================================
# TAB 4: OPTIMIZATION
# ============================================================================
with tabs[3]:
    st.markdown('<div class="section-header">Price Optimization</div>', unsafe_allow_html=True)
    
    # Run optimization for selected product
    optimizer = PricingOptimizer()
    
    # Get product metadata
    product_meta = products_meta[products_meta['product'] == selected_product].iloc[0]
    
    # Run optimization
    with st.spinner(f"Optimizing price for {selected_product}..."):
        opt_result = optimizer.optimize_prices(
            products_meta[products_meta['product'] == selected_product],
            forecaster,
            objective=objective.lower(),
            n_prices=100
        )
    
    if selected_product in opt_result:
        result = opt_result[selected_product]
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Base Price", f"${result['base_price']:.2f}")
        with col2:
            st.metric("Optimal Price", f"${result['optimal_price']:.2f}", delta=f"{((result['optimal_price']/result['base_price']-1)*100):.1f}%")
        with col3:
            st.metric(objective, f"${result[f'expected_{objective.lower()}']:,.2f}")
        with col4:
            st.metric("Expected Demand", f"{result['expected_demand']:.0f} units")
        
        # Price Curve
        st.markdown('<div class="subheader">Price vs ' + objective + ' Curve</div>', unsafe_allow_html=True)
        
        curve_df = result['price_curve']
        objective_key = objective.lower()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=curve_df['price'],
            y=curve_df[objective_key],
            mode='lines',
            name=objective,
            line=dict(color='#3498db', width=3),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.2)',
            hovertemplate='<b>Price:</b> $%{x:.2f}<br><b>' + objective + ':</b> $%{y:,.0f}<extra></extra>'
        ))
        fig.add_vline(
            x=result['optimal_price'],
            line_dash="dash",
            line_color="red",
            annotation_text=f"Optimal: ${result['optimal_price']:.2f}",
            annotation_position="top left"
        )
        fig.update_layout(
            height=400,
            hovermode='x',
            plot_bgcolor='rgba(240, 242, 246, 0.5)',
            xaxis_title='Price ($)',
            yaxis_title=f'{objective} ($)',
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 5: STRATEGIES
# ============================================================================
with tabs[4]:
    st.markdown('<div class="section-header">Pricing Strategies Simulation</div>', unsafe_allow_html=True)
    
    # Run strategy simulation
    simulator = SimulationEngine()
    
    with st.spinner("Simulating pricing strategies..."):
        optimizer_for_sim = PricingOptimizer()
        opt_results_sim = optimizer_for_sim.optimize_prices(
            products_meta, forecaster, objective='revenue', n_prices=100
        )
        
        simulation_results = simulator.simulate_strategies(
            opt_results_sim, forecaster, products_meta
        )
    
    # Strategy comparison for selected product
    simulation_df = pd.DataFrame(simulation_results)
    product_sim = simulation_df[simulation_df['product'] == selected_product].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    strategies_info = {
        'Aggressive': {
            'price': product_sim['Aggressive_Price'],
            'revenue': product_sim['Aggressive_Revenue'],
            'profit': product_sim['Aggressive_Profit'],
            'color': '#e74c3c'
        },
        'Competitive': {
            'price': product_sim['Competitive_Price'],
            'revenue': product_sim['Competitive_Revenue'],
            'profit': product_sim['Competitive_Profit'],
            'color': '#3498db'
        },
        'Premium': {
            'price': product_sim['Premium_Price'],
            'revenue': product_sim['Premium_Revenue'],
            'profit': product_sim['Premium_Profit'],
            'color': '#f39c12'
        }
    }
    
    with col1:
        st.markdown("### Aggressive Strategy")
        st.markdown(f"**Price:** ${strategies_info['Aggressive']['price']:.2f}")
        st.markdown(f"**Revenue:** ${strategies_info['Aggressive']['revenue']:,.2f}")
        st.markdown(f"**Profit:** ${strategies_info['Aggressive']['profit']:,.2f}")
    
    with col2:
        st.markdown("### Competitive Strategy")
        st.markdown(f"**Price:** ${strategies_info['Competitive']['price']:.2f}")
        st.markdown(f"**Revenue:** ${strategies_info['Competitive']['revenue']:,.2f}")
        st.markdown(f"**Profit:** ${strategies_info['Competitive']['profit']:,.2f}")
    
    with col3:
        st.markdown("### Premium Strategy")
        st.markdown(f"**Price:** ${strategies_info['Premium']['price']:.2f}")
        st.markdown(f"**Revenue:** ${strategies_info['Premium']['revenue']:,.2f}")
        st.markdown(f"**Profit:** ${strategies_info['Premium']['profit']:,.2f}")
    
    # Strategy comparison chart
    st.markdown('<div class="subheader">Strategy Metrics Comparison</div>', unsafe_allow_html=True)
    
    strategies_data = {
        'Strategy': ['Aggressive', 'Competitive', 'Premium'],
        'Price': [
            strategies_info['Aggressive']['price'],
            strategies_info['Competitive']['price'],
            strategies_info['Premium']['price']
        ],
        'Revenue': [
            strategies_info['Aggressive']['revenue'],
            strategies_info['Competitive']['revenue'],
            strategies_info['Premium']['revenue']
        ],
        'Profit': [
            strategies_info['Aggressive']['profit'],
            strategies_info['Competitive']['profit'],
            strategies_info['Premium']['profit']
        ]
    }
    
    strategies_chart_df = pd.DataFrame(strategies_data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Price',
        x=strategies_chart_df['Strategy'],
        y=strategies_chart_df['Price'],
        marker_color=['#e74c3c', '#3498db', '#f39c12'],
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
    ))
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name='Profit',
        x=strategies_chart_df['Strategy'],
        y=strategies_chart_df['Profit'],
        marker_color=['#e74c3c', '#3498db', '#f39c12'],
        hovertemplate='<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>'
    ))
    fig2.update_layout(
        height=350,
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# TAB 6: DATA EXPLORER
# ============================================================================
with tabs[5]:
    st.markdown('<div class="section-header">Data Explorer</div>', unsafe_allow_html=True)
    
    # Data filters
    col1, col2 = st.columns(2)
    
    with col1:
        min_date = st.date_input("Start Date", sales_df['date'].min())
    with col2:
        max_date = st.date_input("End Date", sales_df['date'].max())
    
    # Filter data
    filtered_df = sales_df[
        (sales_df['date'] >= pd.to_datetime(min_date)) &
        (sales_df['date'] <= pd.to_datetime(max_date)) &
        (sales_df['product'] == selected_product)
    ].copy()
    
    st.markdown(f"**Showing {len(filtered_df)} records** for {selected_product}")
    
    # Display data
    st.dataframe(
        filtered_df[[
            'date', 'product', 'price', 'competitor_price',
            'quantity_sold', 'revenue', 'profit', 'is_promotion'
        ]].sort_values('date', ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"{selected_product}_data.csv",
        mime="text/csv"
    )

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Electronics Dynamic Pricing Optimization System | 
    <small>Powered by AI & Machine Learning | Data from 2022-2023</small></p>
</div>
""", unsafe_allow_html=True)
