import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
from datetime import datetime
import sys
from pathlib import Path

# Add notebooks_local to path to import funcsQA_simplification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'notebooks_local'))

from funcsQA_simplification import (
    forecast_optimal_reconciliation, 
    reconstruct_baseline_forecast_cat,
    test_volume_conservation
)

# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================
st.set_page_config(page_title="QA Category Validation", layout="wide", initial_sidebar_state="expanded")
st.title("QA Category Validation - Real-time Analysis")

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORICAL_DECISIONS_DIR = BASE_DIR / "historical_decisions"
DECISIONS_FILE = HISTORICAL_DECISIONS_DIR / "forecast_decisions.json"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_data
def get_available_countries():
    """Extract countries from available CSV files in data folder."""
    countries = set()
    if DATA_DIR.exists():
        for file in DATA_DIR.glob("*_forecast_baseline_intervalo_conf.csv"):
            country = file.name.replace("_forecast_baseline_intervalo_conf.csv", "")
            countries.add(country)
    return sorted(list(countries))

@st.cache_data
def load_data(country):
    """Load baseline combination and category data."""
    try:
        df_comb = pd.read_csv(DATA_DIR / f"{country}_forecast_baseline_intervalo_conf.csv")
        df_cat = pd.read_csv(DATA_DIR / f"{country}_forecast_baseline_category.csv")
        return df_comb, df_cat
    except FileNotFoundError as e:
        st.error(f"Error loading data for {country}: {e}")
        return None, None

def prepare_baseline_data(df_baseline_combination):
    """Prepare baseline combination data with necessary calculations."""
    df_baseline_combination['volume_KO_FORECAST_ACT'] = np.where(
        df_baseline_combination.Type == 'Forecasted',
        df_baseline_combination.volume_uc_KO_FORECAST,
        df_baseline_combination.volume_uc_KO_ACTUAL
    )
    df_baseline_combination['volume_NOKO_FORECAST_ACT'] = np.where(
        df_baseline_combination.Type == 'Forecasted',
        df_baseline_combination.volume_uc_NOKO_FORECAST,
        df_baseline_combination.volume_uc_NOKO_ACTUAL
    )
    df_baseline_combination['price_KO'] = np.where(
        df_baseline_combination.Type == 'Forecasted',
        df_baseline_combination.price_lc_KO_FORECAST,
        df_baseline_combination.price_lc_KO_ACTUAL
    )
    df_baseline_combination['price_NOKO'] = np.where(
        df_baseline_combination.Type == 'Forecasted',
        df_baseline_combination.price_lc_NOKO_FORECAST,
        df_baseline_combination.price_lc_NOKO_ACTUAL
    )
    df_baseline_combination['Date'] = pd.to_datetime(df_baseline_combination['ds'])
    return df_baseline_combination

def prepare_category_data(df_baseline_cat, df_baseline_combination):
    """Prepare category data with date information."""
    last_observed_date = df_baseline_combination[df_baseline_combination.Type == 'Observed'].Date.max()
    df_baseline_cat['Date'] = pd.to_datetime(df_baseline_cat['Date'])
    df_baseline_cat['Type'] = np.where(df_baseline_cat['Date'] <= last_observed_date, 'Observed', 'Forecasted')
    df_baseline_cat['Year'] = df_baseline_cat['Date'].dt.year
    df_baseline_cat['Month'] = df_baseline_cat['Date'].dt.month
    df_baseline_cat = df_baseline_cat.sort_values('Date').copy()
    return df_baseline_cat, last_observed_date

def get_categories(df_baseline_cat):
    """Get unique categories from data."""
    return sorted(df_baseline_cat['combination'].unique().tolist())

def apply_transformations(df_baseline_combination, df_baseline_cat, reconciliation, 
                         undo_qa, undo_qa_categories, keep_comb_forecast, keep_comb_forecast_categories):
    """Apply all transformations to the data."""
    
    # Reconciliation
    if reconciliation:
        df_baseline_cat = forecast_optimal_reconciliation(df_baseline_combination, df_baseline_cat)
    
    # Reconstruct baseline forecast
    forecast_recalculated_cat, df_all_som = reconstruct_baseline_forecast_cat(df_baseline_cat)
    forecast_recalculated_cat.rename(columns={'combination': 'Category'}, inplace=True)
    
    # Undo QA
    if undo_qa and len(undo_qa_categories) > 0:
        forecast_recalculated_cat = pd.merge(
            forecast_recalculated_cat,
            df_baseline_cat[['combination', 'Date', 'volume_KO_FORECAST_ACT', 'volume_NOKO_FORECAST_ACT']],
            left_on=['Category', 'Date'],
            right_on=['combination', 'Date'],
            how='left'
        )
        forecast_recalculated_cat['volume_KO_FORECAST_ACT_aj'] = np.where(
            forecast_recalculated_cat['Category'].isin(undo_qa_categories),
            forecast_recalculated_cat['volume_KO_FORECAST_ACT'],
            forecast_recalculated_cat['volume_KO_FORECAST_ACT_aj']
        )
        forecast_recalculated_cat['volume_NOKO_FORECAST_ACT_aj'] = np.where(
            forecast_recalculated_cat['Category'].isin(undo_qa_categories),
            forecast_recalculated_cat['volume_NOKO_FORECAST_ACT'],
            forecast_recalculated_cat['volume_NOKO_FORECAST_ACT_aj']
        )
        forecast_recalculated_cat.drop(['volume_KO_FORECAST_ACT', 'volume_NOKO_FORECAST_ACT', 'combination'], axis=1, inplace=True)
    
    # Disaggregate by category
    df_baseline_combination_recalculated = df_baseline_combination[
        ['combination', 'Date', 'Bottler', 'Category', 'Sub_Category', 'MS_SS', 'Refillability',
         'volume_KO_FORECAST_ACT', 'volume_NOKO_FORECAST_ACT', 'price_KO', 'price_NOKO', 'Type']
    ].copy()
    df_baseline_combination_recalculated = pd.merge(
        df_baseline_combination_recalculated, forecast_recalculated_cat, on=['Category', 'Date'], how='left'
    )
    
    # Calculate weights
    df_baseline_combination_recalculated['prop_category_KO'] = (
        df_baseline_combination_recalculated['volume_KO_FORECAST_ACT'] / 
        df_baseline_combination_recalculated.groupby(['Category', 'Date'])['volume_KO_FORECAST_ACT'].transform('sum')
    )
    df_baseline_combination_recalculated['prop_category_NOKO'] = (
        df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT'] / 
        df_baseline_combination_recalculated.groupby(['Category', 'Date'])['volume_NOKO_FORECAST_ACT'].transform('sum')
    )
    df_baseline_combination_recalculated['prop_N_COMB'] = (
        1 / df_baseline_combination_recalculated.groupby(['Category', 'Date'])['combination'].transform('nunique')
    )
    
    df_baseline_combination_recalculated['FLAG_PROP_N_COMB_KO'] = (
        df_baseline_combination_recalculated.groupby(['Category', 'Date'])['prop_category_KO'].transform('sum') == 0
    )
    df_baseline_combination_recalculated['FLAG_PROP_N_COMB_NOKO'] = (
        df_baseline_combination_recalculated.groupby(['Category', 'Date'])['prop_category_NOKO'].transform('sum') == 0
    )
    
    df_baseline_combination_recalculated['prop_category_KO'] = np.where(
        df_baseline_combination_recalculated['FLAG_PROP_N_COMB_KO'],
        df_baseline_combination_recalculated['prop_N_COMB'],
        df_baseline_combination_recalculated['prop_category_KO']
    )
    df_baseline_combination_recalculated['prop_category_NOKO'] = np.where(
        df_baseline_combination_recalculated['FLAG_PROP_N_COMB_NOKO'],
        df_baseline_combination_recalculated['prop_N_COMB'],
        df_baseline_combination_recalculated['prop_category_NOKO']
    )
    
    # Disaggregate volumes
    df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj_por_cat'] = (
        df_baseline_combination_recalculated['prop_category_KO'] * df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj']
    )
    df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT_aj_por_cat'] = (
        df_baseline_combination_recalculated['prop_category_NOKO'] * df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT_aj']
    )
    
    # Keep combination forecast
    if keep_comb_forecast and len(keep_comb_forecast_categories) > 0:
        df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj_por_cat'] = np.where(
            df_baseline_combination_recalculated['Category'].isin(keep_comb_forecast_categories),
            df_baseline_combination_recalculated['volume_KO_FORECAST_ACT'],
            df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj_por_cat']
        )
        df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT_aj_por_cat'] = np.where(
            df_baseline_combination_recalculated['Category'].isin(keep_comb_forecast_categories),
            df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT'],
            df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT_aj_por_cat']
        )
    
    return df_baseline_combination_recalculated, last_observed_date

def calculate_metrics(df_baseline_combination_recalculated):
    """Calculate SOM and SOV metrics."""
    # SOM
    df_baseline_combination_recalculated['SOM'] = (
        df_baseline_combination_recalculated['volume_KO_FORECAST_ACT'] /
        (df_baseline_combination_recalculated['volume_KO_FORECAST_ACT'] + df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT']) * 100
    )
    df_baseline_combination_recalculated['SOM_aj_por_cat'] = (
        df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj_por_cat'] /
        (df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj_por_cat'] + df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT_aj_por_cat']) * 100
    )
    
    df_baseline_combination_recalculated['VAR_SOM'] = (
        df_baseline_combination_recalculated.sort_values(['combination', 'Date']).groupby('combination').SOM.diff()
    )
    df_baseline_combination_recalculated['VAR_SOM_aj_por_cat'] = (
        df_baseline_combination_recalculated.sort_values(['combination', 'Date']).groupby('combination').SOM_aj_por_cat.diff()
    )
    
    # Value
    df_baseline_combination_recalculated['value_lc_KO'] = (
        df_baseline_combination_recalculated['volume_KO_FORECAST_ACT'] * df_baseline_combination_recalculated['price_KO']
    )
    df_baseline_combination_recalculated['value_lc_NOKO'] = (
        df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT'] * df_baseline_combination_recalculated['price_NOKO']
    )
    
    df_baseline_combination_recalculated['value_lc_KO_aj_por_cat'] = (
        df_baseline_combination_recalculated['volume_KO_FORECAST_ACT_aj_por_cat'] * df_baseline_combination_recalculated['price_KO']
    )
    df_baseline_combination_recalculated['value_lc_NOKO_aj_por_cat'] = (
        df_baseline_combination_recalculated['volume_NOKO_FORECAST_ACT_aj_por_cat'] * df_baseline_combination_recalculated['price_NOKO']
    )
    
    return df_baseline_combination_recalculated

def aggregate_by_category(df_data):
    """Aggregate data by category and date."""
    agg_cols = [
        'volume_KO_FORECAST_ACT', 'volume_NOKO_FORECAST_ACT',
        'volume_KO_FORECAST_ACT_aj_por_cat', 'volume_NOKO_FORECAST_ACT_aj_por_cat',
        'value_lc_KO', 'value_lc_NOKO',
        'value_lc_KO_aj_por_cat', 'value_lc_NOKO_aj_por_cat'
    ]
    
    df_agg = df_data.groupby(['Date', 'Category'])[agg_cols].sum().reset_index()
    
    # Recalculate metrics
    df_agg['SOM'] = (df_agg['volume_KO_FORECAST_ACT'] /
                     (df_agg['volume_KO_FORECAST_ACT'] + df_agg['volume_NOKO_FORECAST_ACT']) * 100)
    df_agg['SOM_aj_por_cat'] = (df_agg['volume_KO_FORECAST_ACT_aj_por_cat'] /
                                 (df_agg['volume_KO_FORECAST_ACT_aj_por_cat'] + df_agg['volume_NOKO_FORECAST_ACT_aj_por_cat']) * 100)
    df_agg['SOV'] = (df_agg['value_lc_KO'] /
                     (df_agg['value_lc_KO'] + df_agg['value_lc_NOKO']) * 100)
    df_agg['SOV_aj_por_cat'] = (df_agg['value_lc_KO_aj_por_cat'] /
                                (df_agg['value_lc_KO_aj_por_cat'] + df_agg['value_lc_NOKO_aj_por_cat']) * 100)
    
    df_agg['VAR_SOM'] = df_agg.sort_values(['Category', 'Date']).groupby('Category').SOM.diff()
    df_agg['VAR_SOM_aj_por_cat'] = df_agg.sort_values(['Category', 'Date']).groupby('Category').SOM_aj_por_cat.diff()
    
    return df_agg

def create_year_comparison_chart(df_agg, country, metric='SOM', years=[2024, 2025, 2026], last_observed_date=None):
    """Create year-over-year comparison chart."""
    
    categories = sorted(df_agg['Category'].unique())
    color_map = {2024: "#1f77b4", 2025: '#ff7f0e', 2026: '#d62728'}
    
    figs = []
    
    for category in categories:
        df_cat = df_agg[df_agg['Category'] == category].copy()
        
        fig = go.Figure()
        
        for year in years:
            mask = df_cat['Date'].dt.year == year
            df_year = df_cat[mask].copy()
            df_year = df_year.sort_values('Date')
            
            if len(df_year) == 0:
                continue
            
            # Original metric
            fig.add_trace(go.Scatter(
                x=df_year['Date'].dt.month,
                y=df_year[metric],
                mode='lines+markers',
                name=f'{year}',
                line=dict(color=color_map[year], dash='solid', width=2),
                marker=dict(size=6)
            ))
            
            # Adjusted metric - only for forecasted data
            metric_adj = metric + '_aj_por_cat'
            if last_observed_date:
                df_forecast = df_year[df_year['Date'] > last_observed_date]
                if len(df_forecast) > 0:
                    fig.add_trace(go.Scatter(
                        x=df_forecast['Date'].dt.month,
                        y=df_forecast[metric_adj],
                        mode='lines+markers',
                        name=f'{year} (adjusted)',
                        line=dict(color=color_map[year], dash='dash', width=2),
                        marker=dict(size=5, symbol='diamond')
                    ))
            
            # Add variance annotations for all data points
            var_col = f'VAR_{metric}'
            for _, row in df_year.iterrows():
                if pd.notnull(row.get(var_col)):
                    fig.add_annotation(
                        x=row['Date'].month,
                        y=row[metric],
                        text=f"{row.get(var_col, 0):.2f}pp",
                        showarrow=False,
                        yshift=15,
                        font=dict(size=9, color=color_map[year])
                    )
                    
                    # Add adjusted variance annotation only for forecasted data
                    if last_observed_date and row['Date'] > last_observed_date:
                        var_col_aj = var_col + '_aj_por_cat'
                        if pd.notnull(row.get(var_col_aj)):
                            fig.add_annotation(
                                x=row['Date'].month,
                                y=row[metric_adj],
                                text=f"{row.get(var_col_aj, 0):.2f}pp",
                                showarrow=False,
                                yshift=-20,
                                font=dict(size=9, color=color_map[year])
                            )
        
        fig.update_layout(
            title=f'{category} - {metric} by Year - {country}',
            xaxis_title='Month',
            yaxis_title=metric,
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
        
        figs.append((category, fig))
    
    return figs

def save_decision(country, settings):
    """Save decision to timestamped JSON file organized by year and month."""
    HISTORICAL_DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get current year and month
    now = datetime.now()
    year = now.year
    month = now.month
    filename = f"category_parameters_log_{year}_{month:02d}.json"
    filepath = HISTORICAL_DECISIONS_DIR / filename
    
    # Load existing parameters
    if filepath.exists():
        with open(filepath, 'r') as f:
            parameters = json.load(f)
    else:
        parameters = []
    
    # Create new entry
    new_entry = {
        "timestamp": now.isoformat(),
        "year": year,
        "month": month,
        "country": country,
        "reconciliation": bool(settings['reconciliation']),
        "undo_qa": bool(settings['undo_qa']),
        "keep_comb_forecast": bool(settings['keep_comb_forecast']),
        "undo_qa_categories": list(settings['undo_qa_categories']),
        "keep_comb_forecast_categories": list(settings['keep_comb_forecast_categories'])
    }
    
    parameters.append(new_entry)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(parameters, f, indent=2)
    
    return new_entry, filename

# ============================================================================
# MAIN APP LAYOUT
# ============================================================================

st.sidebar.markdown("## Configuration Controls")

# Select country
countries = get_available_countries()
if not countries:
    st.error("No countries found in data folder. Please ensure CSV files are in the data directory.")
    st.stop()

selected_country = st.sidebar.selectbox("Select Country", countries, key="country_select")

# Load data
df_combination, df_category = load_data(selected_country)

if df_combination is None or df_category is None:
    st.error(f"Could not load data for {selected_country}")
    st.stop()

# Prepare data
df_combination = prepare_baseline_data(df_combination)
df_category, last_observed_date = prepare_category_data(df_category, df_combination)
available_categories = get_categories(df_category)

# Sidebar controls
with st.sidebar:
    st.divider()
    st.subheader("Reconciliation Options")
    reconciliation = st.toggle("Apply Reconciliation", value=True, key="reconciliation_toggle")
    
    st.divider()
    st.subheader("Undo QA Options")
    undo_qa = st.toggle("Apply Undo QA", value=False, key="undo_qa_toggle")
    undo_qa_categories = []
    if undo_qa:
        undo_qa_categories = st.multiselect(
            "Select categories for Undo QA",
            available_categories,
            key="undo_qa_categories",
            help="Categories to which undo QA will be applied"
        )
    
    st.divider()
    st.subheader("Keep Combination Forecast Options")
    keep_comb_forecast = st.toggle("Keep Combination Forecast", value=False, key="keep_comb_toggle")
    keep_comb_forecast_categories = []
    if keep_comb_forecast:
        keep_comb_forecast_categories = st.multiselect(
            "Select categories to keep combination forecast",
            available_categories,
            key="keep_comb_forecast_categories",
            help="Categories where combination forecast will be preserved"
        )

# Apply transformations
try:
    df_result, _ = apply_transformations(
        df_combination,
        df_category.copy(),
        reconciliation,
        undo_qa,
        undo_qa_categories,
        keep_comb_forecast,
        keep_comb_forecast_categories
    )
    
    df_result = calculate_metrics(df_result)
    df_agg = aggregate_by_category(df_result)
    
except Exception as e:
    st.error(f"Error processing data: {str(e)}")
    st.stop()

# Main content area
tab1, tab2, tab3 = st.tabs(["SOM Analysis", "SOV Analysis", "Settings"])

with tab1:
    st.subheader(f"Share of Mouth (SOM) - {selected_country}")
    som_figs = create_year_comparison_chart(df_agg, selected_country, metric='SOM', 
                                             years=[2024, 2025, 2026], last_observed_date=last_observed_date)
    
    for category, fig in som_figs:
        st.plotly_chart(fig, width='stretch')

with tab2:
    st.subheader(f"Share of Value (SOV) - {selected_country}")
    sov_figs = create_year_comparison_chart(df_agg, selected_country, metric='SOV', 
                                             years=[2024, 2025, 2026], last_observed_date=last_observed_date)
    
    for category, fig in sov_figs:
        st.plotly_chart(fig, width='stretch')

with tab3:
    st.subheader("Current Analysis Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Country Selected", selected_country)
        st.metric("Reconciliation", "✓ Enabled" if reconciliation else "✗ Disabled")
        st.metric("Undo QA", "✓ Enabled" if undo_qa else "✗ Disabled")
        st.metric("Keep Comb Forecast", "✓ Enabled" if keep_comb_forecast else "✗ Disabled")
    
    with col2:
        st.write("**Undo QA Categories:**")
        if undo_qa_categories:
            for cat in undo_qa_categories:
                st.write(f"  • {cat}")
        else:
            st.write("  (none selected)")
        
        st.write("**Keep Comb Forecast Categories:**")
        if keep_comb_forecast_categories:
            for cat in keep_comb_forecast_categories:
                st.write(f"  • {cat}")
        else:
            st.write("  (none selected)")
    
    st.divider()
    
    # Save current settings
    if st.button("💾 Save Current Analysis", key="save_decision"):
        settings = {
            'reconciliation': reconciliation,
            'undo_qa': undo_qa,
            'keep_comb_forecast': keep_comb_forecast,
            'undo_qa_categories': undo_qa_categories,
            'keep_comb_forecast_categories': keep_comb_forecast_categories
        }
        
        entry, filename = save_decision(selected_country, settings)
        st.success(f"✓ Analysis saved to {filename}")
        st.json(entry)
    
    st.divider()
    
    # Show historical decisions
    st.subheader("Recent Analysis History")
    
    recent_decisions = []
    
    # Scan for all category_parameters_log files
    if HISTORICAL_DECISIONS_DIR.exists():
        for log_file in sorted(HISTORICAL_DECISIONS_DIR.glob("category_parameters_log_*.json"), reverse=True):
            try:
                with open(log_file, 'r') as f:
                    file_decisions = json.load(f)
                
                # Get decisions for current country
                for decision in reversed(file_decisions):
                    if decision['country'] == selected_country:
                        recent_decisions.append(decision)
                        if len(recent_decisions) >= 5:
                            break
                
                if len(recent_decisions) >= 5:
                    break
            except (json.JSONDecodeError, IOError):
                st.warning(f"Could not read {log_file.name}")
    
    if recent_decisions:
        for i, dec in enumerate(recent_decisions, 1):
            with st.expander(f"{i}. {dec['timestamp'][:19]} - {dec['country']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Reconciliation:** {dec['reconciliation']}")
                    st.write(f"**Undo QA:** {dec['undo_qa']}")
                    st.write(f"**Keep Comb Forecast:** {dec['keep_comb_forecast']}")
                with col2:
                    st.write(f"**Undo QA Categories:** {', '.join(dec['undo_qa_categories']) if dec['undo_qa_categories'] else 'None'}")
                    st.write(f"**Keep Comb Forecast Categories:** {', '.join(dec['keep_comb_forecast_categories']) if dec['keep_comb_forecast_categories'] else 'None'}")
    else:
        st.info("No previous analyses for this country.")

st.markdown("---")
st.caption(f"Last observed date: {last_observed_date.strftime('%Y-%m-%d') if last_observed_date else 'N/A'}")
