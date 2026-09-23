"""
Anomaly detection: statistical methods (Z-score, IQR) by default, with an
optional Isolation Forest for multivariate numeric anomaly detection.

Each flagged row includes a human-readable reason, which the LLM uses to
explain "why it was flagged" without inventing numbers.
"""
from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def detect_anomalies_zscore(
    df: pd.DataFrame, column: str, threshold: float = 3.0
) -> Dict[str, Any]:
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")
    series = pd.to_numeric(df[column], errors="coerce")
    mean, std = series.mean(), series.std()
    if std == 0 or pd.isna(std):
        return {"method": "zscore", "column": column, "anomalies": []}

    z_scores = (series - mean) / std
    flagged_idx = z_scores[abs(z_scores) > threshold].index

    anomalies: List[Dict[str, Any]] = []
    for idx in flagged_idx:
        anomalies.append(
            {
                "row_index": int(idx),
                "value": float(series[idx]),
                "z_score": round(float(z_scores[idx]), 2),
                "reason": (
                    f"Value {series[idx]:.2f} is {abs(z_scores[idx]):.1f} standard "
                    f"deviations from the mean ({mean:.2f}), exceeding the "
                    f"threshold of {threshold}."
                ),
            }
        )
    return {"method": "zscore", "column": column, "threshold": threshold, "anomalies": anomalies}


def detect_anomalies_iqr(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")
    series = pd.to_numeric(df[column], errors="coerce")
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr

    flagged = series[(series < lower) | (series > upper)]
    anomalies = [
        {
            "row_index": int(idx),
            "value": float(val),
            "reason": (
                f"Value {val:.2f} falls outside the expected IQR range "
                f"[{lower:.2f}, {upper:.2f}]."
            ),
        }
        for idx, val in flagged.items()
    ]
    return {"method": "iqr", "column": column, "bounds": [lower, upper], "anomalies": anomalies}


def detect_anomalies_isolation_forest(
    df: pd.DataFrame, columns: List[str], contamination: float = 0.05
) -> Dict[str, Any]:
    """Optional multivariate anomaly detection (bonus)."""
    from sklearn.ensemble import IsolationForest

    numeric_df = df[columns].apply(pd.to_numeric, errors="coerce").dropna()
    if numeric_df.empty:
        return {"method": "isolation_forest", "columns": columns, "anomalies": []}

    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(numeric_df)
    flagged_idx = numeric_df.index[preds == -1]

    anomalies = [
        {
            "row_index": int(idx),
            "values": {c: float(numeric_df.loc[idx, c]) for c in columns},
            "reason": "Flagged as a multivariate outlier by Isolation Forest across "
            f"columns {columns}.",
        }
        for idx in flagged_idx
    ]
    return {"method": "isolation_forest", "columns": columns, "anomalies": anomalies}
