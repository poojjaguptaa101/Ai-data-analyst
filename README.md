<<<<<<< HEAD
# AI-Powered Data Analyst

Upload one or more CSV files and interact with your data using natural language — ask
questions, get charts, detect anomalies, and see the reasoning behind every answer.

## Features

- Upload and validate one or more CSV files
- Natural-language Q&A over your data
- Business insights and summaries (top-N, trends, descriptive stats)
- Chart generation: bar, line, pie, scatter (Plotly)
- SQL generation and execution (via DuckDB, directly on your CSVs — no database setup needed)
- Anomaly detection (Z-score, IQR, and optional Isolation Forest) with plain-language reasoning
- Conversation memory across a session
- Data quality report endpoint (missing values, duplicates, dtypes)

See [`docs/architecture.md`](docs/architecture.md) for the full system design and a
request-lifecycle walkthrough.

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **LLM**: Anthropic Claude (tool-calling), pluggable in `backend/llm/client.py`
- **SQL engine**: DuckDB (queries pandas DataFrames directly)
- **Charts**: Plotly
- **Anomaly detection**: scikit-learn (Isolation Forest) + statistical methods

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd ai-data-analyst
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 3. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Run the frontend (separate terminal)

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501`, upload `sample_data/sales_data.csv`, and start asking questions.

## Run with Docker

```bash
export ANTHROPIC_API_KEY=your_key_here
docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

## Example Questions

- "Which region generated the highest revenue?"
- "Show monthly sales trends."
- "Which products are underperforming?"
- "What are the top five customers?"
- "Generate SQL for this analysis."
- "Detect anomalies in the dataset."

## Running Tests

```bash
pytest tests/
```

## Sample Dataset

`sample_data/sales_data.csv` contains synthetic order-level sales data (region, product,
customer, quantity, revenue) with one intentionally-injected outlier row for demoing anomaly
detection.

## Project Structure

```
ai-data-analyst/
├── backend/
│   ├── main.py              # FastAPI app (upload, query, quality endpoints)
│   ├── agent/
│   │   ├── orchestrator.py  # LLM tool-calling loop
│   │   └── tools.py         # tool schemas + dispatch
│   ├── data/
│   │   ├── loader.py        # CSV validation
│   │   └── registry.py      # session-scoped DataFrame + history store
│   ├── analysis/
│   │   ├── sql_engine.py    # DuckDB execution
│   │   ├── anomaly.py       # zscore / IQR / isolation forest
│   │   └── insights.py      # summary stats, top-N, trends
│   └── llm/
│       └── client.py        # Anthropic API wrapper
├── frontend/
│   └── app.py                # Streamlit chat UI
├── sample_data/
│   └── sales_data.csv
├── tests/
│   └── test_analysis.py
├── docs/
│   └── architecture.md       # architecture diagram + design notes
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Assumptions & Implementation Notes

- Session state (uploaded DataFrames + conversation history) is stored in-memory per process.
  For multi-instance production deployment, swap `backend/data/registry.py`'s `SessionStore`
  for a Redis-backed implementation — the interface is designed to make this a drop-in change.
- The LLM is used purely for **orchestration and explanation** — all actual computation (sums,
  averages, outlier detection, SQL execution) happens in deterministic Python/DuckDB code. This
  avoids hallucinated numbers, which is the main failure mode of naive "chat with your CSV"
  implementations.
- Anomaly detection defaults to Z-score/IQR (fast, interpretable); Isolation Forest is available
  as an opt-in for multivariate cases.
- Authentication is out of scope for this assignment; each browser session gets its own
  server-side session ID.
- Model name in `backend/llm/client.py` should be updated to whichever Claude model version is
  current at deployment time.

## Screenshots & Demo

_Add screenshots and a link to the demo video here before submission._

## Architecture Diagram

See [`docs/architecture.md`](docs/architecture.md) — includes a Mermaid flowchart of the
end-to-end request lifecycle.
=======
# Ai-data-analyst
>>>>>>> origin/main
