import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow importing project local QA functions.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "notebooks_local"))

from funcsQA_simplification import (  # noqa: E402
    forecast_optimal_reconciliation,
    reconstruct_baseline_forecast_cat,
    test_volume_conservation,
)


def _parse_list(raw_value: str) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _prepare_baseline_combination(df_baseline_combination: pd.DataFrame) -> pd.DataFrame:
    df = df_baseline_combination.copy()
    df["volume_KO_FORECAST_ACT"] = np.where(
        df.Type == "Forecasted", df.volume_uc_KO_FORECAST, df.volume_uc_KO_ACTUAL
    )
    df["volume_NOKO_FORECAST_ACT"] = np.where(
        df.Type == "Forecasted", df.volume_uc_NOKO_FORECAST, df.volume_uc_NOKO_ACTUAL
    )
    df["price_KO"] = np.where(
        df.Type == "Forecasted", df.price_lc_KO_FORECAST, df.price_lc_KO_ACTUAL
    )
    df["price_NOKO"] = np.where(
        df.Type == "Forecasted", df.price_lc_NOKO_FORECAST, df.price_lc_NOKO_ACTUAL
    )
    df["Date"] = pd.to_datetime(df["ds"])
    return df


def _prepare_baseline_category(
    df_baseline_cat: pd.DataFrame, df_baseline_combination: pd.DataFrame
) -> pd.DataFrame:
    df = df_baseline_cat.copy()
    last_observed_date = (
        df_baseline_combination.loc[df_baseline_combination["Type"] == "Observed", "Date"].max()
    )
    df["Date"] = pd.to_datetime(df["Date"])
    df["Type"] = np.where(df["Date"] <= last_observed_date, "Observed", "Forecasted")
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    return df.sort_values("Date").copy()


def _apply_undo_qa(
    forecast_recalculated_cat: pd.DataFrame,
    df_baseline_cat: pd.DataFrame,
    undo_qa_categories: list[str],
) -> pd.DataFrame:
    df = pd.merge(
        forecast_recalculated_cat,
        df_baseline_cat[["combination", "Date", "volume_KO_FORECAST_ACT", "volume_NOKO_FORECAST_ACT"]],
        left_on=["Category", "Date"],
        right_on=["combination", "Date"],
        how="left",
    )
    df["volume_KO_FORECAST_ACT_aj"] = np.where(
        df["Category"].isin(undo_qa_categories),
        df["volume_KO_FORECAST_ACT"],
        df["volume_KO_FORECAST_ACT_aj"],
    )
    df["volume_NOKO_FORECAST_ACT_aj"] = np.where(
        df["Category"].isin(undo_qa_categories),
        df["volume_NOKO_FORECAST_ACT"],
        df["volume_NOKO_FORECAST_ACT_aj"],
    )
    return df.drop(["volume_KO_FORECAST_ACT", "volume_NOKO_FORECAST_ACT", "combination"], axis=1)


def _disaggregate_to_combination(
    df_baseline_combination: pd.DataFrame,
    forecast_recalculated_cat: pd.DataFrame,
    keep_comb_forecast: bool,
    keep_comb_forecast_categories: list[str],
) -> pd.DataFrame:
    df = df_baseline_combination[
        [
            "combination",
            "Date",
            "Bottler",
            "Category",
            "Sub_Category",
            "MS_SS",
            "Refillability",
            "volume_KO_FORECAST_ACT",
            "volume_NOKO_FORECAST_ACT",
            "price_KO",
            "price_NOKO",
            "Type",
        ]
    ].copy()
    df = pd.merge(df, forecast_recalculated_cat, on=["Category", "Date"], how="left")

    df["prop_category_KO"] = df["volume_KO_FORECAST_ACT"] / df.groupby(["Category", "Date"])[
        "volume_KO_FORECAST_ACT"
    ].transform("sum")
    df["prop_category_NOKO"] = df["volume_NOKO_FORECAST_ACT"] / df.groupby(["Category", "Date"])[
        "volume_NOKO_FORECAST_ACT"
    ].transform("sum")
    df["prop_N_COMB"] = 1 / df.groupby(["Category", "Date"])["combination"].transform("nunique")

    df["FLAG_PROP_N_COMB_KO"] = (
        df.groupby(["Category", "Date"])["prop_category_KO"].transform("sum") == 0
    )
    df["FLAG_PROP_N_COMB_NOKO"] = (
        df.groupby(["Category", "Date"])["prop_category_NOKO"].transform("sum") == 0
    )

    df["prop_category_KO"] = np.where(
        df["FLAG_PROP_N_COMB_KO"], df["prop_N_COMB"], df["prop_category_KO"]
    )
    df["prop_category_NOKO"] = np.where(
        df["FLAG_PROP_N_COMB_NOKO"], df["prop_N_COMB"], df["prop_category_NOKO"]
    )

    df["volume_KO_FORECAST_ACT_aj_por_cat"] = (
        df["prop_category_KO"] * df["volume_KO_FORECAST_ACT_aj"]
    )
    df["volume_NOKO_FORECAST_ACT_aj_por_cat"] = (
        df["prop_category_NOKO"] * df["volume_NOKO_FORECAST_ACT_aj"]
    )

    test_volume_conservation(df, forecast_recalculated_cat)

    if keep_comb_forecast and keep_comb_forecast_categories:
        df["volume_KO_FORECAST_ACT_aj_por_cat"] = np.where(
            df["Category"].isin(keep_comb_forecast_categories),
            df["volume_KO_FORECAST_ACT"],
            df["volume_KO_FORECAST_ACT_aj_por_cat"],
        )
        df["volume_NOKO_FORECAST_ACT_aj_por_cat"] = np.where(
            df["Category"].isin(keep_comb_forecast_categories),
            df["volume_NOKO_FORECAST_ACT"],
            df["volume_NOKO_FORECAST_ACT_aj_por_cat"],
        )

    return df


def _build_output_frame(df_baseline_combination_recalculated: pd.DataFrame, country: str) -> pd.DataFrame:
    df = df_baseline_combination_recalculated[
        [
            "combination",
            "Date",
            "Bottler",
            "Category",
            "Sub_Category",
            "MS_SS",
            "Refillability",
            "volume_KO_FORECAST_ACT_aj_por_cat",
            "volume_NOKO_FORECAST_ACT_aj_por_cat",
            "price_KO",
            "price_NOKO",
            "Type",
            "node_flag",
        ]
    ].rename(
        columns={
            "volume_KO_FORECAST_ACT_aj_por_cat": "volume_KO_FORECAST_ACT",
            "volume_NOKO_FORECAST_ACT_aj_por_cat": "volume_NOKO_FORECAST_ACT",
        }
    )

    df["Country"] = country
    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Year_Month"] = df["Date"].dt.strftime("%Y M%m")
    df["value_KO_FORECAST_ACT"] = df["volume_KO_FORECAST_ACT"] * df["price_KO"]
    df["value_NOKO_FORECAST_ACT"] = df["volume_NOKO_FORECAST_ACT"] * df["price_NOKO"]
    return df


def run_pipeline(
    country: str,
    data_dir: Path,
    output_file: Path,
    reconciliation: bool,
    undo_qa: bool,
    undo_qa_categories: list[str],
    keep_comb_forecast: bool,
    keep_comb_forecast_categories: list[str],
) -> None:
    file_baseline = data_dir / f"{country}_forecast_baseline_intervalo_conf.csv"
    file_cat = data_dir / f"{country}_forecast_baseline_category.csv"

    if not file_baseline.exists():
        raise FileNotFoundError(f"Baseline file not found: {file_baseline}")
    if not file_cat.exists():
        raise FileNotFoundError(f"Category file not found: {file_cat}")

    df_baseline_combination = _prepare_baseline_combination(pd.read_csv(file_baseline))
    df_baseline_cat = _prepare_baseline_category(pd.read_csv(file_cat), df_baseline_combination)

    if reconciliation:
        df_baseline_cat = forecast_optimal_reconciliation(df_baseline_combination, df_baseline_cat)

    forecast_recalculated_cat, _ = reconstruct_baseline_forecast_cat(df_baseline_cat)
    forecast_recalculated_cat = forecast_recalculated_cat.rename(columns={"combination": "Category"})

    if undo_qa and undo_qa_categories:
        forecast_recalculated_cat = _apply_undo_qa(
            forecast_recalculated_cat,
            df_baseline_cat,
            undo_qa_categories,
        )

    df_baseline_combination_recalculated = _disaggregate_to_combination(
        df_baseline_combination,
        forecast_recalculated_cat,
        keep_comb_forecast,
        keep_comb_forecast_categories,
    )

    output_df = _build_output_frame(df_baseline_combination_recalculated, country)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_file, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run Vector QA pipeline from local CSV files and generate "
            "{country}_forecast_baseline_post_qa.csv"
        )
    )
    parser.add_argument("--country", required=True, help="Country name, e.g. Guatemala")
    parser.add_argument(
        "--data-dir",
        default=str(PROJECT_ROOT / "data"),
        help="Directory that contains input CSV files",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Output CSV path. Defaults to <data-dir>/{country}_forecast_baseline_post_qa.csv",
    )

    parser.add_argument(
        "--no-reconciliation",
        action="store_true",
        help="Disable forecast optimal reconciliation step",
    )
    parser.add_argument("--undo-qa", action="store_true", help="Undo QA for selected categories")
    parser.add_argument(
        "--undo-qa-categories",
        default="",
        help="Comma-separated categories for undo QA, e.g. Juices,Water",
    )
    parser.add_argument(
        "--keep-comb-forecast",
        action="store_true",
        help="Keep original combination forecast for selected categories",
    )
    parser.add_argument(
        "--keep-comb-forecast-categories",
        default="",
        help="Comma-separated categories for keep combination forecast",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_file = (
        Path(args.output_file)
        if args.output_file
        else data_dir / f"{args.country}_forecast_baseline_post_qa.csv"
    )

    undo_qa_categories = _parse_list(args.undo_qa_categories)
    keep_comb_forecast_categories = _parse_list(args.keep_comb_forecast_categories)

    run_pipeline(
        country=args.country,
        data_dir=data_dir,
        output_file=output_file,
        reconciliation=not args.no_reconciliation,
        undo_qa=args.undo_qa,
        undo_qa_categories=undo_qa_categories,
        keep_comb_forecast=args.keep_comb_forecast,
        keep_comb_forecast_categories=keep_comb_forecast_categories,
    )

    print(f"Generated: {output_file}")


if __name__ == "__main__":
    main()
