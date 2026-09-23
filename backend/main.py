"""
FastAPI entrypoint. Exposes:
  POST /upload     — upload one or more CSV files for a session
  POST /query       — ask a natural-language question about the uploaded data
  GET  /quality/{session_id}/{dataset} — data quality report (bonus)
  GET  /health       — health check
"""
from __future__ import annotations
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from backend.data.loader import load_csv, CSVValidationError, data_quality_report
from backend.data.registry import store
from backend.agent.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-data-analyst")

app = FastAPI(title="AI-Powered Data Analyst")
orchestrator = Orchestrator()


class QueryRequest(BaseModel):
    session_id: str
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/session")
def create_session():
    return {"session_id": str(uuid.uuid4())}


@app.post("/upload")
async def upload_csv(session_id: str, files: list[UploadFile] = File(...)):
    uploaded = []
    for file in files:
        content = await file.read()
        try:
            df = load_csv(content, file.filename)
        except CSVValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        name = file.filename.rsplit(".", 1)[0]
        store.add_dataframe(session_id, name, df)
        uploaded.append({"name": name, "rows": len(df), "columns": list(df.columns)})
        logger.info(f"Loaded dataset '{name}' with {len(df)} rows for session {session_id}")

    return {"session_id": session_id, "datasets": uploaded}


@app.get("/quality/{session_id}/{dataset}")
def quality_report(session_id: str, dataset: str):
    df = store.get_dataframe(session_id, dataset)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return data_quality_report(df)


@app.post("/query")
def query(req: QueryRequest):
    try:
        result = orchestrator.handle_query(req.session_id, req.question)
    except Exception as e:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(e))
    return result
