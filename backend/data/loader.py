"""
CSV loading + validation.

Handles: encoding detection fallback, empty-file checks, duplicate-column
handling, and basic data-quality reporting used by the "data quality checks"
bonus feature.
"""
from __future__ import annotations
import io
from typing import Dict, Any
import pandas as pd


class CSVValidationError(Exception):
    pass


def load_csv(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load a CSV from raw bytes with a couple of encoding fallbacks."""
    if not file_bytes:
        raise CSVValidationError(f"{filename} is empty.")

    for encoding in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            raise CSVValidationError(f"{filename} has no parsable data.")
    else:
        raise CSVValidationError(f"Could not decode {filename} with utf-8 or latin-1.")

    if df.empty:
        raise CSVValidationError(f"{filename} parsed but contains no rows.")

    # De-duplicate column names if the CSV has repeats
    if df.columns.duplicated().any():
        df.columns = _dedupe_columns(df.columns)

    return df


def _dedupe_columns(columns) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for col in columns:
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
    return result


def data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Bonus: basic data-quality checks used to warn the user upfront."""
    return {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
    }
