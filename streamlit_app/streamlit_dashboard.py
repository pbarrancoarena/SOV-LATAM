import os
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
ANALYSIS_COMBINATIONS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "historical_decisions", "analysis_combinations.json"))
YEAR_COLORS = ["#1f77b4", "#ff7f0e", "#d62728"]
ALLOWED_YEARS = [2024, 2025, 2026]


def get_country_options():
    if not os.path.isdir(DATA_DIR):
        return []

    countries = []
    for file_name in os.listdir(DATA_DIR):
        if file_name.endswith("_forecast_baseline_post_qa.csv"):
            country = file_name.replace("_forecast_baseline_post_qa.csv", "")
            countries.append(country)
    return sorted(set(countries))


def save_analysis_combination(country, filters, variables_to_analyze=None):
    """Save the selected combination filters to JSON.
    
    Args:
        country: Country name
        filters: Dictionary with filter values
        variables_to_analyze: List of variables to analyze (e.g., ['volumen_ko', 'volumen_noko'])
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(ANALYSIS_COMBINATIONS_FILE), exist_ok=True)
    
    # Load existing combinations
    if os.path.exists(ANALYSIS_COMBINATIONS_FILE):
        with open(ANALYSIS_COMBINATIONS_FILE, 'r') as f:
            combinations = json.load(f)
    else:
        combinations = []
    
    # Default variables if not specified
    if variables_to_analyze is None:
        variables_to_analyze = ['volumen_ko', 'volumen_noko', 'precio_ko', 'precio_noko']
    
    # Create new combination entry
    new_combination = {
        "timestamp": datetime.now().isoformat(),
        "country": country,
        "Bottler": filters.get("Bottler", "All"),
        "Category": filters.get("Category", "All"),
        "Sub_Category": filters.get("Sub_Category", "All"),
        "MS_SS": filters.get("MS_SS", "All"),
        "Refillability": filters.get("Refillability", "All"),
        "variables_to_analyze": variables_to_analyze
    }
    
    combinations.append(new_combination)
    
    # Save to file
    with open(ANALYSIS_COMBINATIONS_FILE, 'w') as f:
        json.dump(combinations, f, indent=2)
    
    return new_combination


def load_analysis_combinations():
    """Load all saved analysis combinations from JSON."""
    if os.path.exists(ANALYSIS_COMBINATIONS_FILE):
        with open(ANALYSIS_COMBINATIONS_FILE, 'r') as f:
            return json.load(f)
    return []


@st.cache_data(show_spinner=False)
def load_data(country):
    file_path = os.path.join(DATA_DIR, f"{country}_forecast_baseline_post_qa.csv")
    df = pd.read_csv(file_path)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    if "Month" not in df.columns and "Date" in df.columns:
        df["Month"] = df["Date"].dt.month

    if "Year" not in df.columns and "Date" in df.columns:
        df["Year"] = df["Date"].dt.year

    return df


def add_filter_option(label, values, key):
    options = ["All"] + sorted(values)
    return st.sidebar.selectbox(label, options, index=0, key=key)


def apply_filters(df, filters):
    filtered = df.copy()
    for column, value in filters.items():
        if value != "All" and column in filtered.columns:
            filtered = filtered[filtered[column] == value]
    return filtered


def aggregate_data(df):
    base_columns = ["Date", "Month", "Year", "Type"]
    numeric_columns = [
        "volume_KO_FORECAST_ACT",
        "volume_NOKO_FORECAST_ACT",
        "value_KO_FORECAST_ACT",
        "value_NOKO_FORECAST_ACT",
    ]
    available_columns = [col for col in base_columns if col in df.columns]
    available_metrics = [col for col in numeric_columns if col in df.columns]

    aggregated = (
        df.groupby(available_columns, dropna=False)[available_metrics]
        .sum()
        .reset_index()
    )
    return aggregated


def compute_metrics(df):
    df = df.copy()
    df["price_KO"] = df["value_KO_FORECAST_ACT"] / df["volume_KO_FORECAST_ACT"]
    df["price_NOKO"] = df["value_NOKO_FORECAST_ACT"] / df["volume_NOKO_FORECAST_ACT"]
    df["price_index"] = df["price_KO"] / df["price_NOKO"]
    df["SOM"] = (
        df["volume_KO_FORECAST_ACT"]
        / (df["volume_KO_FORECAST_ACT"] + df["volume_NOKO_FORECAST_ACT"])
        * 100
    )
    df["SOV"] = (
        df["value_KO_FORECAST_ACT"]
        / (df["value_KO_FORECAST_ACT"] + df["value_NOKO_FORECAST_ACT"])
        * 100
    )

    df = df.sort_values(["Year", "Type", "Date", "Month"]).reset_index(drop=True)

    df["pct_vol_change_KO"] = (
        df.groupby(["Year", "Type"])["volume_KO_FORECAST_ACT"]
        .pct_change(fill_method=None)
        .mul(100)
    )
    df["pct_vol_change_NOKO"] = (
        df.groupby(["Year", "Type"])["volume_NOKO_FORECAST_ACT"]
        .pct_change(fill_method=None)
        .mul(100)
    )
    df["pct_price_change_KO"] = (
        df.groupby(["Year", "Type"])["price_KO"].pct_change(fill_method=None).mul(100)
    )
    df["pct_price_change_NOKO"] = (
        df.groupby(["Year", "Type"])["price_NOKO"].pct_change(fill_method=None).mul(100)
    )
    df["pct_change_price_index"] = (
        df.groupby(["Year", "Type"])["price_index"].pct_change(fill_method=None).mul(100)
    )
    df["pct_change_SOM"] = (
        df.groupby(["Year", "Type"])["SOM"].pct_change(fill_method=None).mul(100)
    )
    df["pct_change_SOV"] = (
        df.groupby(["Year", "Type"])["SOV"].pct_change(fill_method=None).mul(100)
    )

    return df


def build_color_map(years):
    colors = {}
    for index, year in enumerate(sorted(years)):
        colors[year] = YEAR_COLORS[index % len(YEAR_COLORS)]
    return colors


def safe_pct_growth(current, previous):
    if pd.isna(previous) or previous == 0 or pd.isna(current):
        return None
    return (current - previous) / previous * 100


def format_pct(value):
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def render_kpi(label, growth_value):
    if growth_value is None:
        st.metric(label, "N/A")
        return
    delta_text = f"{growth_value:+.2f}%"
    st.metric(label, "", delta_text, delta_color="normal")


def compute_yearly_totals(df, value_col):
    if "Year" not in df.columns or value_col not in df.columns:
        return {}
    return df.groupby("Year", dropna=True)[value_col].sum().to_dict()


def render_yoy_kpis(df):
    total_volume_col = "volume_KO_FORECAST_ACT"
    noko_volume_col = "volume_NOKO_FORECAST_ACT"

    if total_volume_col not in df.columns or noko_volume_col not in df.columns:
        st.warning("Volume columns are missing; YoY KPIs are unavailable.")
        return

    totals_ko = compute_yearly_totals(df, total_volume_col)
    totals_noko = compute_yearly_totals(df, noko_volume_col)
    totals_all = {
        year: totals_ko.get(year, 0) + totals_noko.get(year, 0)
        for year in ALLOWED_YEARS
    }

    growth_24_25_total = safe_pct_growth(totals_all.get(2025), totals_all.get(2024))
    growth_25_26_total = safe_pct_growth(totals_all.get(2026), totals_all.get(2025))

    growth_24_25_ko = safe_pct_growth(totals_ko.get(2025), totals_ko.get(2024))
    growth_25_26_ko = safe_pct_growth(totals_ko.get(2026), totals_ko.get(2025))

    growth_24_25_noko = safe_pct_growth(totals_noko.get(2025), totals_noko.get(2024))
    growth_25_26_noko = safe_pct_growth(totals_noko.get(2026), totals_noko.get(2025))

    st.subheader("YoY Growth (Volume)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi("Total Volume 2024 → 2025", growth_24_25_total)
    with col2:
        render_kpi("KO Volume 2024 → 2025", growth_24_25_ko)
    with col3:
        render_kpi("NOKO Volume 2024 → 2025", growth_24_25_noko)

    col4, col5, col6 = st.columns(3)
    with col4:
        render_kpi("Total Volume 2025 → 2026", growth_25_26_total)
    with col5:
        render_kpi("KO Volume 2025 → 2026", growth_25_26_ko)
    with col6:
        render_kpi("NOKO Volume 2025 → 2026", growth_25_26_noko)
        


def format_volume_value(value):
    if pd.isna(value):
        return ""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def build_volume_ticks(series):
    clean = series.dropna()
    if clean.empty:
        return None
    min_val = clean.min()
    max_val = clean.max()
    if min_val == max_val:
        tickvals = [min_val]
    else:
        tickvals = np.linspace(min_val, max_val, num=5)
    ticktext = [format_volume_value(value) for value in tickvals]
    return tickvals, ticktext


def add_metric_traces(
    fig,
    df,
    row,
    col,
    y_col,
    pct_col,
    title,
    y_label,
    color_map,
    y_format=None,
    show_legend=False,
):
    month_labels = [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]

    for year in sorted(df["Year"].dropna().unique()):
        year_df = df[df["Year"] == year]
        for type_label, dash in [("Observed", "solid"), ("Forecasted", "dot")]:
            if "Type" in year_df.columns:
                type_df = year_df[year_df["Type"] == type_label]
            else:
                type_df = year_df

            if type_df.empty:
                continue

            text_values = []
            if pct_col in type_df.columns:
                for value in type_df[pct_col]:
                    text_values.append("" if pd.isna(value) else f"{value:.1f}%")
            else:
                text_values = None

            fig.add_trace(
                go.Scatter(
                    x=type_df["Month"],
                    y=type_df[y_col],
                    mode="lines+markers+text",
                    text=text_values,
                    textposition="top center",
                    name=f"{year} {type_label}",
                    line=dict(color=color_map.get(year), dash=dash),
                    marker=dict(color=color_map.get(year)),
                    legendgroup=str(year),
                    showlegend=show_legend,
                ),
                row=row,
                col=col,
            )

    fig.update_xaxes(
        title_text="Month",
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=month_labels,
        tickangle=-25,
        row=row,
        col=col,
    )
    fig.update_yaxes(title_text=y_label, row=row, col=col)
    fig.update_annotations(selector=dict(text=title), row=row, col=col)

    if y_format == "volume":
        ticks = build_volume_ticks(df[y_col])
        if ticks:
            tickvals, ticktext = ticks
            fig.update_yaxes(
                tickmode="array",
                tickvals=tickvals,
                ticktext=ticktext,
                row=row,
                col=col,
            )


def render_dashboard(df):
    years = df["Year"].dropna().unique()
    if len(years) == 0:
        st.warning("No data available for the selected filters.")
        return

    color_map = build_color_map(years)

    fig = make_subplots(
        rows=4,
        cols=2,
        subplot_titles=[
            "Volume KO",
            "Volume NOKO",
            "Price KO",
            "Price NOKO",
            "SOM",
            "SOV",
            "Price Index",
            "",
        ],
        horizontal_spacing=0.08,
        vertical_spacing=0.1,
    )

    add_metric_traces(
        fig,
        df,
        1,
        1,
        "volume_KO_FORECAST_ACT",
        "pct_vol_change_KO",
        "Volume KO",
        "Volume",
        color_map,
        y_format="volume",
        show_legend=True,
    )
    add_metric_traces(
        fig,
        df,
        1,
        2,
        "volume_NOKO_FORECAST_ACT",
        "pct_vol_change_NOKO",
        "Volume NOKO",
        "Volume",
        color_map,
        y_format="volume",
    )
    add_metric_traces(
        fig,
        df,
        2,
        1,
        "price_KO",
        "pct_price_change_KO",
        "Price KO",
        "Price",
        color_map,
    )
    add_metric_traces(
        fig,
        df,
        2,
        2,
        "price_NOKO",
        "pct_price_change_NOKO",
        "Price NOKO",
        "Price",
        color_map,
    )
    add_metric_traces(
        fig,
        df,
        3,
        1,
        "SOM",
        "pct_change_SOM",
        "SOM",
        "SOM",
        color_map,
    )
    add_metric_traces(
        fig,
        df,
        3,
        2,
        "SOV",
        "pct_change_SOV",
        "SOV",
        "SOV",
        color_map,
    )
    add_metric_traces(
        fig,
        df,
        4,
        1,
        "price_index",
        "pct_change_price_index",
        "Price Index",
        "Price Index",
        color_map,
    )

    fig.update_xaxes(visible=False, row=4, col=2)
    fig.update_yaxes(visible=False, row=4, col=2)

    fig.update_layout(
        height=1200,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=80, l=60, r=40, b=40),
    )
    st.plotly_chart(fig, width='stretch')


def main():
    st.set_page_config(page_title="Validation Graphs", layout="wide")
    st.title("Validation Graphs")


    country_options = get_country_options()
    if not country_options:
        st.error("No input files found in the data folder.")
        return

    country = st.sidebar.selectbox("Country", country_options, index=0)
    df = load_data(country)
    df = df[df["Year"].isin(ALLOWED_YEARS)].copy()

    filtered = df.copy()
    filters = {}

    filters["Bottler"] = add_filter_option(
        "Bottler", filtered["Bottler"].dropna().unique(), "bottler"
    )
    filtered = apply_filters(filtered, {"Bottler": filters["Bottler"]})

    filters["Category"] = add_filter_option(
        "Category", filtered["Category"].dropna().unique(), "category"
    )
    filtered = apply_filters(filtered, {"Category": filters["Category"]})

    filters["Sub_Category"] = add_filter_option(
        "Subcategory", filtered["Sub_Category"].dropna().unique(), "subcategory"
    )
    filtered = apply_filters(filtered, {"Sub_Category": filters["Sub_Category"]})

    filters["MS_SS"] = add_filter_option(
        "MS_SS", filtered["MS_SS"].dropna().unique(), "ms_ss"
    )
    filtered = apply_filters(filtered, {"MS_SS": filters["MS_SS"]})

    filters["Refillability"] = add_filter_option(
        "Refillability", filtered["Refillability"].dropna().unique(), "refillability"
    )
    filtered = apply_filters(
        filtered, {"Refillability": filters["Refillability"]}
    )
    
    # Variables selection for analysis
    st.sidebar.divider()
    st.sidebar.subheader("Variables a Analizar")
    
    available_variables = {
        'volumen_ko': 'Volumen KO',
        'volumen_noko': 'Volumen NOKO',
        'precio_ko': 'Precio KO',
        'precio_noko': 'Precio NOKO'
    }
    
    selected_variables = st.sidebar.multiselect(
        "Selecciona las variables para el validador:",
        options=list(available_variables.keys()),
        default=['volumen_ko', 'volumen_noko'],
        format_func=lambda x: available_variables[x],
        help="Estas variables se usarán como default en el Forecast Validator",
        key="variables_to_analyze"
    )
    
    # Button to save analysis combination
    st.sidebar.divider()
    if st.sidebar.button("➕ Añadir esta combinación a análisis", key="save_combination"):
        if not selected_variables:
            st.sidebar.error("⚠️ Selecciona al menos una variable")
        else:
            combination = save_analysis_combination(country, filters, selected_variables)
            st.sidebar.success(f"✓ Combinación guardada")
            st.sidebar.json(combination)
    
    # Display saved combinations
    st.sidebar.divider()
    st.sidebar.subheader("Combinaciones Guardadas")
    saved_combinations = load_analysis_combinations()
    
    if saved_combinations:
        with st.sidebar.expander(f"Ver {len(saved_combinations)} combinaciones guardadas"):
            for i, combo in enumerate(reversed(saved_combinations[-10:]), 1):  # Show last 10
                st.write(f"**{i}. {combo['timestamp'][:10]}** - {combo['country']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"**Bottler:** {combo['Bottler']}")
                with col2:
                    st.caption(f"**Category:** {combo['Category']}")
                with col3:
                    st.caption(f"**Sub_Category:** {combo['Sub_Category']}")
                st.caption(f"**MS_SS:** {combo['MS_SS']} | **Refillability:** {combo['Refillability']}")
                
                # Show variables to analyze if available
                if 'variables_to_analyze' in combo:
                    vars_text = ', '.join([v.replace('_', ' ').title() for v in combo['variables_to_analyze']])
                    st.caption(f"**Variables:** {vars_text}")
                
                st.divider()
    else:
        st.sidebar.info("No hay combinaciones guardadas aún")
    
    render_yoy_kpis(filtered)
    
    aggregated = aggregate_data(filtered)
    metrics_df = compute_metrics(aggregated)

    if "Type" in df.columns:
        last_observed_date = df[df["Type"] == "Observed"]["Date"].max()
        if pd.notna(last_observed_date):
            st.caption(f"Last observed date: {last_observed_date.date()}")
            
    # Display the filtered data table
    with st.expander("Show Filtered Data"):
        st.dataframe(filtered)
        
        
    # Display a line to separate the tables from the charts
    st.markdown("---")
    
    st.markdown("### Dashboard")
    
    render_dashboard(metrics_df)


if __name__ == "__main__":
    main()