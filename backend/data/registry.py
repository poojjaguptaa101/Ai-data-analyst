"""
Session-scoped storage for uploaded DataFrames and conversation history.

For a single-instance deployment, an in-memory dict is sufficient. For
horizontal scaling, swap this for a Redis-backed store keeping the same
interface.
"""
from __future__ import annotations
import threading
from typing import Dict, List, Any
import pandas as pd


class SessionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._frames: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def add_dataframe(self, session_id: str, name: str, df: pd.DataFrame) -> None:
        with self._lock:
            self._frames.setdefault(session_id, {})[name] = df

    def get_dataframes(self, session_id: str) -> Dict[str, pd.DataFrame]:
        return self._frames.get(session_id, {})

    def get_dataframe(self, session_id: str, name: str) -> pd.DataFrame | None:
        return self._frames.get(session_id, {}).get(name)

    def schema_summary(self, session_id: str) -> Dict[str, Any]:
        """Return a JSON-serializable schema description for all datasets in a session."""
        out = {}
        for name, df in self.get_dataframes(session_id).items():
            out[name] = {
                "columns": [
                    {"name": c, "dtype": str(df[c].dtype)} for c in df.columns
                ],
                "n_rows": len(df),
                "sample": df.head(3).to_dict(orient="records"),
            }
        return out

    def append_history(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._history.setdefault(session_id, []).append(
                {"role": role, "content": content}
            )

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._history.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._frames.pop(session_id, None)
            self._history.pop(session_id, None)


# Single process-wide instance (swap for Redis-backed store in production)
store = SessionStore()
