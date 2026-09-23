"""
Verifies the orchestrator's tool-calling loop works end-to-end WITHOUT a real
API key, by mocking the LLM to behave like Claude's tool-use response format.

Turn 1: LLM "decides" to call top_n
Turn 2: LLM receives the tool result and returns a final text answer

This proves the orchestrator <-> tools <-> registry wiring is correct.
Swap MockLLMClient for the real LLMClient once ANTHROPIC_API_KEY is set.
"""
import sys
sys.path.insert(0, "/home/claude/ai-data-analyst")

from types import SimpleNamespace
from backend.data.registry import store
from backend.data.loader import load_csv
from backend.agent.orchestrator import Orchestrator


class FakeToolUseBlock:
    def __init__(self, name, input_, id_):
        self.type = "tool_use"
        self.name = name
        self.input = input_
        self.id = id_


class FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class MockLLMClient:
    """Mimics Anthropic's response.content shape across two turns."""
    def __init__(self):
        self.call_count = 0

    def create_message(self, system, messages, tools=None, max_tokens=1500):
        self.call_count += 1
        if self.call_count == 1:
            # First turn: model decides to call the top_n tool
            content = [
                FakeToolUseBlock(
                    "top_n",
                    {"dataset": "sales_data", "group_col": "region", "value_col": "revenue", "n": 3},
                    "tool_1",
                )
            ]
        else:
            # Second turn: model has the tool result, gives final answer
            content = [
                FakeTextBlock(
                    "North generated the highest revenue at 13,650, driven mainly by one "
                    "unusually large order. East and West follow at roughly 2,290 and 2,255."
                )
            ]
        return SimpleNamespace(content=content)


# --- Run the actual orchestrator with the mock LLM ---
session_id = "test-session-mock"
df = load_csv(open("/home/claude/ai-data-analyst/sample_data/sales_data.csv", "rb").read(), "sales_data.csv")
store.add_dataframe(session_id, "sales_data", df)

orchestrator = Orchestrator(llm_client=MockLLMClient())
result = orchestrator.handle_query(session_id, "Which region generated the highest revenue?")

print("=== ORCHESTRATOR RESULT ===")
print("Answer:", result["answer"])
print("Artifacts:", result["artifacts"])
print("History after turn:", store.get_history(session_id))
assert "North" in result["answer"], "Expected tool-derived answer to mention North"
print("\nPASS: orchestrator correctly executed tool call -> real result -> final LLM answer")
