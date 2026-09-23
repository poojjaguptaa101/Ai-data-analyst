"""
Thin wrapper around the Anthropic API so the rest of the app doesn't depend
on SDK specifics. Swap `LLMClient` internals to use a different provider
(e.g. OpenAI) without touching the orchestrator.
"""
from __future__ import annotations
import os
from typing import List, Dict, Any
from anthropic import Anthropic

MODEL = "claude-opus-4-5"  # update to the current model string as needed


class LLMClient:
    def __init__(self, api_key: str | None = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def create_message(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
        max_tokens: int = 1500,
    ):
        kwargs: Dict[str, Any] = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        return self.client.messages.create(**kwargs)
