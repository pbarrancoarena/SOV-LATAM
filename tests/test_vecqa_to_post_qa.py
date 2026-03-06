"""
Tests para scripts/vecqa_to_post_qa.py

Ejecutar: pytest tests/test_vecqa_to_post_qa.py -v
"""

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import vecqa_to_post_qa as vecqa


def test_parse_list_empty_and_csv_values():
    """Debe convertir CSV en lista y manejar vacios."""
    assert vecqa._parse_list("") == []
    assert vecqa._parse_list("  ") == []
    assert vecqa._parse_list("Juices, Water ,Energy") == ["Juices", "Water", "Energy"]


def test_prepare_baseline_combination_uses_forecast_and_actual_values():
    """Debe seleccionar columnas forecast/actual segun Type."""
    df = pd.DataFrame(
        {
            "Type": ["Observed", "Forecasted"],
            "volume_uc_KO_FORECAST": [100.0, 200.0],
            "volume_uc_KO_ACTUAL": [90.0, 180.0],
            "volume_uc_NOKO_FORECAST": [300.0, 400.0],
            "volume_uc_NOKO_ACTUAL": [280.0, 380.0],
            "price_lc_KO_FORECAST": [1.5, 1.6],
            "price_lc_KO_ACTUAL": [1.4, 1.5],
            "price_lc_NOKO_FORECAST": [1.2, 1.3],
            "price_lc_NOKO_ACTUAL": [1.1, 1.2],
            "ds": ["2025-01-01", "2025-02-01"],
        }
    )

    out = vecqa._prepare_baseline_combination(df)

    assert out.loc[0, "volume_KO_FORECAST_ACT"] == 90.0
    assert out.loc[1, "volume_KO_FORECAST_ACT"] == 200.0
    assert out.loc[0, "volume_NOKO_FORECAST_ACT"] == 280.0
    assert out.loc[1, "volume_NOKO_FORECAST_ACT"] == 400.0
    assert pd.api.types.is_datetime64_any_dtype(out["Date"])


def test_prepare_baseline_category_marks_observed_and_forecasted():
    """Debe etiquetar Type con base en la ultima fecha observada."""
    df_comb = pd.DataFrame(
        {
            "Type": ["Observed", "Observed", "Forecasted"],
            "Date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        }
    )
    df_cat = pd.DataFrame(
        {
            "Date": ["2025-01-01", "2025-02-01", "2025-03-01"],
            "combination": ["Juices", "Juices", "Juices"],
        }
    )

    out = vecqa._prepare_baseline_category(df_cat, df_comb)

    assert list(out["Type"]) == ["Observed", "Observed", "Forecasted"]
    assert list(out["Month"]) == [1, 2, 3]
    assert list(out["Year"]) == [2025, 2025, 2025]


def test_run_pipeline_raises_when_input_files_are_missing(tmp_path):
    """Debe fallar con mensaje claro cuando no existen archivos de entrada."""
    with pytest.raises(FileNotFoundError, match="Baseline file not found"):
        vecqa.run_pipeline(
            country="Nowhere",
            data_dir=tmp_path,
            output_file=tmp_path / "out.csv",
            reconciliation=True,
            undo_qa=False,
            undo_qa_categories=[],
            keep_comb_forecast=False,
            keep_comb_forecast_categories=[],
        )


def test_build_output_frame_adds_derived_columns():
    """Debe generar columnas finales esperadas y valores derivados."""
    df = pd.DataFrame(
        {
            "combination": ["C1"],
            "Date": ["2025-01-01"],
            "Bottler": ["B"],
            "Category": ["Juices"],
            "Sub_Category": ["S"],
            "MS_SS": ["MS"],
            "Refillability": ["REFILLABLE"],
            "volume_KO_FORECAST_ACT_aj_por_cat": [10.0],
            "volume_NOKO_FORECAST_ACT_aj_por_cat": [20.0],
            "price_KO": [2.0],
            "price_NOKO": [3.0],
            "Type": ["Forecasted"],
            "node_flag": ["SOM_ORIGINAL_ORIGINAL"],
        }
    )

    out = vecqa._build_output_frame(df, "Guatemala")

    assert out.loc[0, "Country"] == "Guatemala"
    assert out.loc[0, "Year"] == 2025
    assert out.loc[0, "Month"] == 1
    assert out.loc[0, "Year_Month"] == "2025 M01"
    assert out.loc[0, "value_KO_FORECAST_ACT"] == 20.0
    assert out.loc[0, "value_NOKO_FORECAST_ACT"] == 60.0


def test_main_parses_cli_and_calls_run_pipeline(monkeypatch, capsys, tmp_path):
    """Debe parsear argumentos CLI y delegar a run_pipeline con valores correctos."""
    captured = {}

    def fake_run_pipeline(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(vecqa, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "vecqa_to_post_qa.py",
            "--country",
            "Guatemala",
            "--data-dir",
            str(tmp_path),
            "--undo-qa",
            "--undo-qa-categories",
            "Juices,Water",
            "--keep-comb-forecast",
            "--keep-comb-forecast-categories",
            "Juices",
            "--no-reconciliation",
        ],
    )

    vecqa.main()
    stdout = capsys.readouterr().out

    assert captured["country"] == "Guatemala"
    assert captured["data_dir"] == tmp_path
    assert captured["reconciliation"] is False
    assert captured["undo_qa"] is True
    assert captured["undo_qa_categories"] == ["Juices", "Water"]
    assert captured["keep_comb_forecast"] is True
    assert captured["keep_comb_forecast_categories"] == ["Juices"]
    assert captured["output_file"] == tmp_path / "Guatemala_forecast_baseline_post_qa.csv"
    assert "Generated:" in stdout
