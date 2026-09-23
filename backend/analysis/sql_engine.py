"""
Executes LLM-generated SQL directly against in-memory pandas DataFrames
using DuckDB. No separate database server is needed.
"""
from __future__ import annotations
from typing import Dict, Any
import duckdb
import pandas as pd


class SQLExecutionError(Exception):
    pass


def run_sql(query: str, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Run `query` against the given named DataFrames.
    Table names in the SQL must match the keys of `dataframes`.
    """
    if not dataframes:
        raise SQLExecutionError("No datasets loaded for this session.")

    con = duckdb.connect(database=":memory:")
    try:
        for name, df in dataframes.items():
            con.register(name, df)
        result_df = con.execute(query).fetchdf()
    except Exception as e:  # duckdb raises its own exception types
        raise SQLExecutionError(f"SQL execution failed: {e}") from e
    finally:
        con.close()

    return {
        "columns": list(result_df.columns),
        "rows": result_df.head(200).to_dict(orient="records"),
        "n_rows_total": len(result_df),
    }
