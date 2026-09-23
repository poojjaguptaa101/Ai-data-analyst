"""
Core orchestrator: takes a user's natural-language question, gives the LLM
the dataset schema + available tools, runs the tool-calling loop until the
LLM produces a final text answer, and returns the answer plus any chart/SQL
artifacts produced along the way.
"""
from __future__ import annotations
from typing import Dict, Any, List
import json

from backend.agent.tools import TOOL_SCHEMAS, execute_tool
from backend.llm.client import LLMClient
from backend.data.registry import store

SYSTEM_PROMPT = """You are an AI data analyst. You help users understand their CSV data
through natural language conversation.

Rules:
- You MUST use the provided tools to get real numbers. Never invent or estimate values.
- After a tool result comes back, explain it in plain, concise language and state the
  reasoning behind your answer (why this is the result, not just what the result is).
- If a query is ambiguous (e.g. column names not specified), make a reasonable assumption
  based on the schema and state the assumption explicitly.
- Keep answers focused and business-friendly; avoid unnecessary technical jargon.
- When asked to "generate SQL" explicitly, include the SQL query in your final answer.
"""


class Orchestrator:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def handle_query(self, session_id: str, user_query: str) -> Dict[str, Any]:
        dataframes = store.get_dataframes(session_id)
        if not dataframes:
            return {"answer": "Please upload at least one CSV file first.", "artifacts": []}

        schema = store.schema_summary(session_id)
        history = store.get_history(session_id)

        messages: List[Dict[str, Any]] = list(history) + [
            {"role": "user", "content": f"Dataset schema:\n{json.dumps(schema, default=str)}\n\nQuestion: {user_query}"}
        ]

        artifacts: List[Dict[str, Any]] = []
        final_text = ""

        # Tool-calling loop (max 5 iterations to prevent runaway loops)
        for _ in range(5):
            response = self.llm.create_message(
                system=SYSTEM_PROMPT, messages=messages, tools=TOOL_SCHEMAS
            )

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b.text for b in response.content if b.type == "text"]
            if text_blocks:
                final_text = " ".join(text_blocks)

            if not tool_use_blocks:
                break  # LLM gave a final answer with no further tool calls

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                try:
                    result = execute_tool(block.name, block.input, dataframes)
                    if block.name == "generate_chart":
                        artifacts.append({"type": "chart", "data": result})
                except Exception as e:  # surface errors back to the LLM so it can recover
                    result = {"error": str(e)}
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        store.append_history(session_id, "user", user_query)
        store.append_history(session_id, "assistant", final_text)

        return {"answer": final_text, "artifacts": artifacts}
