"""
Utility functions for the Forecast Volume Review application.

Provides helper functions for data validation, file operations,
and common calculations used throughout the app.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
import streamlit as st


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a dataframe contains all required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        True if all columns present, False otherwise
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return False
    
    return True


def validate_file_exists(file_path: str) -> bool:
    """
    Check if a file exists at the specified path.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file exists, False otherwise
    """
    return Path(file_path).exists()


def get_file_path(country: str, file_type: str, base_dir: str = "../data") -> str:
    """
    Construct the full file path for a country's data file.
    
    Args:
        country: Country name (Chile, Guatemala, Peru)
        file_type: Type of file (intervalo_conf, category)
        base_dir: Base directory path
        
    Returns:
        Full file path
    """
    return f"{base_dir}/{country}_forecast_baseline_{file_type}.csv"


def safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0) -> pd.Series:
    """
    Safely divide two series, handling division by zero.
    
    Args:
        numerator: Series for numerator
        denominator: Series for denominator
        fill_value: Value to use when denominator is zero
        
    Returns:
        Result series with NaN values filled
    """
    result = pd.Series(np.divide(
        numerator,
        denominator,
        where=denominator != 0,
        out=np.full_like(numerator, fill_value)
    ))
    return result.fillna(fill_value)


def aggregate_by_groupby(
    df: pd.DataFrame,
    groupby_cols: List[str],
    agg_dict: dict
) -> pd.DataFrame:
    """
    Generic aggregation function with error handling.
    
    Args:
        df: DataFrame to aggregate
        groupby_cols: Columns to group by
        agg_dict: Dictionary of column_name: aggregation_function pairs
        
    Returns:
        Aggregated dataframe
    """
    try:
        result = df.groupby(groupby_cols).agg(agg_dict).reset_index()
        return result
    except Exception as e:
        st.error(f"Error during aggregation: {str(e)}")
        raise


def get_date_range_formatted(df: pd.DataFrame, date_col: str = 'Date') -> str:
    """
    Get formatted date range from a dataframe.
    
    Args:
        df: DataFrame with date column
        date_col: Name of date column
        
    Returns:
        Formatted string like "2025-01 to 2025-12"
    """
    try:
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        return f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}"
    except Exception:
        return "Unknown"


def get_unique_values_sorted(df: pd.DataFrame, column: str) -> List:
    """
    Get unique sorted values from a dataframe column.
    
    Args:
        df: DataFrame
        column: Column name
        
    Returns:
        Sorted list of unique values
    """
    return sorted(df[column].unique().tolist())


def fill_missing_combinations(df: pd.DataFrame, groupby_cols: List[str]) -> pd.DataFrame:
    """
    Fill missing combinations in a grouped dataframe with zeros.
    
    This is useful when some combinations don't have data for all periods.
    
    Args:
        df: DataFrame with grouped data
        groupby_cols: Columns that define combinations
        
    Returns:
        DataFrame with all combinations filled
    """
    # Get all unique values for each column
    unique_vals = {col: df[col].unique() for col in groupby_cols}
    
    # Create all combinations
    from itertools import product
    all_combos = list(product(*[unique_vals[col] for col in groupby_cols]))
    df_all = pd.DataFrame(all_combos, columns=groupby_cols)
    
    # Merge with original data
    result = df_all.merge(df, on=groupby_cols, how='left')
    
    return result


def calculate_month_year_columns(df: pd.DataFrame, date_col: str = 'Date') -> pd.DataFrame:
    """
    Add Year and Month columns to dataframe.
    
    Args:
        df: DataFrame with date column
        date_col: Name of date column
        
    Returns:
        DataFrame with added Year and Month columns
    """
    df_copy = df.copy()
    df_copy['Year'] = df_copy[date_col].dt.year
    df_copy['Month'] = df_copy[date_col].dt.month.astype(str).str.zfill(2)
    return df_copy


def format_large_number(num: float, decimals: int = 0) -> str:
    """
    Format a large number with comma separators.
    
    Args:
        num: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted string
    """
    if pd.isna(num):
        return "N/A"
    return f"{num:,.{decimals}f}"


def format_percentage(num: float, decimals: int = 2) -> str:
    """
    Format a number as percentage.
    
    Args:
        num: Number to format (0-100)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if pd.isna(num):
        return "N/A"
    return f"{num:.{decimals}f}%"


def get_color_for_value(value: float, thresholds: dict) -> str:
    """
    Get a color based on value thresholds for conditional formatting.
    
    Args:
        value: Value to check
        thresholds: Dict with 'red', 'yellow', 'green' keys containing threshold values
        
    Returns:
        Color string (hex or name)
    """
    if pd.isna(value):
        return "gray"
    
    if value >= thresholds.get('green', float('inf')):
        return "green"
    elif value >= thresholds.get('yellow', float('inf')):
        return "orange"
    else:
        return "red"


def validate_parameter_combination(
    undo_qa: bool,
    undo_qa_categories: list,
    keep_comb_forecast: bool,
    keep_comb_forecast_categories: list
) -> Tuple[bool, str]:
    """
    Validate that parameter combinations are valid.
    
    Args:
        undo_qa: Flag for undo QA
        undo_qa_categories: Categories for undo QA
        keep_comb_forecast: Flag for keep combination
        keep_comb_forecast_categories: Categories to keep
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # If undo_qa is True, must have categories
    if undo_qa and not undo_qa_categories:
        return False, "If 'Undo QA' is enabled, select at least one category"
    
    # If keep_comb_forecast is True, must have categories
    if keep_comb_forecast and not keep_comb_forecast_categories:
        return False, "If 'Keep Combination Forecast' is enabled, select at least one category"
    
    # Check for category overlap (warning, not error)
    if (undo_qa and keep_comb_forecast and
        set(undo_qa_categories) & set(keep_comb_forecast_categories)):
        st.warning(
            "⚠️ Some categories appear in both 'Undo QA' and 'Keep Combination Forecast'. "
            "This may lead to unexpected behavior."
        )
    
    return True, ""


@st.cache_data
def load_csv_safe(file_path: str) -> Optional[pd.DataFrame]:
    """
    Safely load a CSV file with error handling and caching.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        DataFrame or None if loading fails
    """
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading file {file_path}: {str(e)}")
        return None


def get_summary_stats(df: pd.DataFrame) -> dict:
    """
    Calculate summary statistics for the dataset.
    
    Args:
        df: Aggregated dataframe (with volume_total column)
        
    Returns:
        Dictionary of summary statistics
    """
    return {
        'total_volume': df['volume_total'].sum(),
        'avg_som': df['SOM'].mean(),
        'num_categories': df['Category'].nunique(),
        'num_periods': df['Date'].nunique(),
        'date_range': get_date_range_formatted(df),
        'categories': sorted(df['Category'].unique().tolist())
    }
