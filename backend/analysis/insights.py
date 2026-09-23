"""
Generates descriptive summaries and trend information used to ground
LLM insight-generation in real computed numbers.
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd


def summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    numeric = df.select_dtypes(include="number")
    return {
        "numeric_summary": numeric.describe().to_dict(),
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "column_types": {c: str(df[c].dtype) for c in df.columns},
    }


def top_n(df: pd.DataFrame, group_col: str, value_col: str, n: int = 5, ascending: bool = False) -> Dict[str, Any]:
    if group_col not in df.columns or value_col not in df.columns:
        raise ValueError("Specified columns not found in dataset.")
    grouped = (
        df.groupby(group_col)[value_col]
        .sum()
        .sort_values(ascending=ascending)
        .head(n)
    )
    return {
        "group_col": group_col,
        "value_col": value_col,
        "results": [{"group": str(k), "value": float(v)} for k, v in grouped.items()],
    }


def monthly_trend(df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, Any]:
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError("Specified columns not found in dataset.")
    temp = df[[date_col, value_col]].copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col])
    monthly = temp.groupby(temp[date_col].dt.to_period("M"))[value_col].sum()
    return {
        "date_col": date_col,
        "value_col": value_col,
        "trend": [{"month": str(k), "value": float(v)} for k, v in monthly.items()],
    }
