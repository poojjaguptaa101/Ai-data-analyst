import pandas as pd
import pytest

from backend.analysis.anomaly import detect_anomalies_zscore, detect_anomalies_iqr
from backend.analysis.insights import top_n, summary_stats
from backend.analysis.sql_engine import run_sql, SQLExecutionError
from backend.data.loader import load_csv, CSVValidationError


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "region": ["North", "South", "East", "West", "North"],
            "revenue": [100, 200, 150, 50000, 120],  # 50000 is an outlier
        }
    )


def test_zscore_detects_outlier(sample_df):
    result = detect_anomalies_zscore(sample_df, "revenue", threshold=1.5)
    assert len(result["anomalies"]) >= 1
    assert result["anomalies"][0]["value"] == 50000


def test_iqr_detects_outlier(sample_df):
    result = detect_anomalies_iqr(sample_df, "revenue")
    assert any(a["value"] == 50000 for a in result["anomalies"])


def test_top_n(sample_df):
    result = top_n(sample_df, "region", "revenue", n=2)
    assert len(result["results"]) == 2
    assert result["results"][0]["group"] == "West"  # highest revenue


def test_summary_stats(sample_df):
    result = summary_stats(sample_df)
    assert "revenue" in result["numeric_summary"]


def test_run_sql(sample_df):
    result = run_sql("SELECT region, SUM(revenue) as total FROM data GROUP BY region", {"data": sample_df})
    assert "columns" in result
    assert result["n_rows_total"] == 4  # 4 unique regions


def test_run_sql_invalid_query(sample_df):
    with pytest.raises(SQLExecutionError):
        run_sql("SELECT * FROM nonexistent_table", {"data": sample_df})


def test_load_csv_empty_bytes():
    with pytest.raises(CSVValidationError):
        load_csv(b"", "empty.csv")


def test_load_csv_valid():
    content = b"a,b\n1,2\n3,4\n"
    df = load_csv(content, "test.csv")
    assert len(df) == 2
    assert list(df.columns) == ["a", "b"]
