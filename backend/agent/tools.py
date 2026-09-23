"""
Tool schemas exposed to the LLM (Anthropic tool-calling format) and the
Python functions that actually execute them.

The LLM never computes numbers itself — it only decides *which* tool to
call and with *what arguments*. Execution always happens here, against the
real DataFrames, so results are never hallucinated.
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd

from backend.analysis.sql_engine import run_sql
from backend.analysis.anomaly import (
    detect_anomalies_zscore,
    detect_anomalies_iqr,
    detect_anomalies_isolation_forest,
)
from backend.analysis.insights import summary_stats, top_n, monthly_trend
from backend.viz.chart_gen import generate_chart


TOOL_SCHEMAS = [
    {
        "name": "run_sql",
        "description": "Run a SQL query against the loaded dataset(s). Table names must "
        "match the dataset names provided in the schema.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A valid SQL query."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "generate_chart",
        "description": "Generate a chart (bar, line, pie, or scatter) from a dataset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string"},
                "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter"]},
                "x": {"type": "string"},
                "y": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["dataset", "chart_type", "x"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Detect anomalies/outliers in a numeric column using statistical "
        "methods (zscore or iqr), or across multiple columns using isolation_forest.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string"},
                "method": {"type": "string", "enum": ["zscore", "iqr", "isolation_forest"]},
                "column": {"type": "string", "description": "Required for zscore/iqr."},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required for isolation_forest.",
                },
            },
            "required": ["dataset", "method"],
        },
    },
    {
        "name": "summary_stats",
        "description": "Get descriptive statistics (mean, std, min, max, quartiles) for "
        "all numeric columns in a dataset.",
        "input_schema": {
            "type": "object",
            "properties": {"dataset": {"type": "string"}},
            "required": ["dataset"],
        },
    },
    {
        "name": "top_n",
        "description": "Get the top or bottom N groups by summed value of a column "
        "(e.g. top 5 customers by revenue).",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string"},
                "group_col": {"type": "string"},
                "value_col": {"type": "string"},
                "n": {"type": "integer", "default": 5},
                "ascending": {"type": "boolean", "default": False},
            },
            "required": ["dataset", "group_col", "value_col"],
        },
    },
    {
        "name": "monthly_trend",
        "description": "Get a monthly aggregated trend for a value column over a date column.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string"},
                "date_col": {"type": "string"},
                "value_col": {"type": "string"},
            },
            "required": ["dataset", "date_col", "value_col"],
        },
    },
]


def execute_tool(
    tool_name: str, tool_input: Dict[str, Any], dataframes: Dict[str, pd.DataFrame]
) -> Dict[str, Any]:
    """Dispatch a tool call from the LLM to the actual implementation."""
    if tool_name == "run_sql":
        return run_sql(tool_input["query"], dataframes)

    dataset_name = tool_input.get("dataset")
    df = dataframes.get(dataset_name) if dataset_name else None
    if tool_name != "run_sql" and df is None:
        raise ValueError(f"Dataset '{dataset_name}' not found.")

    if tool_name == "generate_chart":
        return generate_chart(
            df,
            chart_type=tool_input["chart_type"],
            x=tool_input["x"],
            y=tool_input.get("y"),
            title=tool_input.get("title"),
        )
    if tool_name == "detect_anomalies":
        method = tool_input["method"]
        if method == "zscore":
            return detect_anomalies_zscore(df, tool_input["column"])
        if method == "iqr":
            return detect_anomalies_iqr(df, tool_input["column"])
        if method == "isolation_forest":
            return detect_anomalies_isolation_forest(df, tool_input["columns"])
        raise ValueError(f"Unknown anomaly method '{method}'.")
    if tool_name == "summary_stats":
        return summary_stats(df)
    if tool_name == "top_n":
        return top_n(
            df,
            tool_input["group_col"],
            tool_input["value_col"],
            tool_input.get("n", 5),
            tool_input.get("ascending", False),
        )
    if tool_name == "monthly_trend":
        return monthly_trend(df, tool_input["date_col"], tool_input["value_col"])

    raise ValueError(f"Unknown tool '{tool_name}'.")
