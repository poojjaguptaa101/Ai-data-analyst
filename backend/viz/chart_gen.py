"""
Generates Plotly charts from a DataFrame based on parameters chosen by the
orchestrator/LLM (chart type + x/y columns).
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import plotly.express as px


SUPPORTED_TYPES = {"bar", "line", "pie", "scatter"}


def generate_chart(
    df: pd.DataFrame, chart_type: str, x: str, y: str | None = None, title: str | None = None
) -> Dict[str, Any]:
    chart_type = chart_type.lower()
    if chart_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported chart type '{chart_type}'. Supported: {SUPPORTED_TYPES}")
    if x not in df.columns:
        raise ValueError(f"Column '{x}' not found in dataset.")
    if y and y not in df.columns:
        raise ValueError(f"Column '{y}' not found in dataset.")

    title = title or f"{chart_type.title()} chart: {y or x} by {x}"

    if chart_type == "bar":
        fig = px.bar(df, x=x, y=y, title=title)
    elif chart_type == "line":
        fig = px.line(df, x=x, y=y, title=title)
    elif chart_type == "pie":
        fig = px.pie(df, names=x, values=y, title=title)
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x, y=y, title=title)

    return {"chart_json": fig.to_json(), "chart_type": chart_type}
