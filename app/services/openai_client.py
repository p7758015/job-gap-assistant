"""
OpenAI API client wrapper.

This module intentionally hides OpenAI SDK details behind a small interface:
`call_openai(payload: dict) -> dict` which returns a parsed JSON object.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from openai import AsyncOpenAI

try:
    # Loads variables from a local `.env` file (development convenience).
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


class OpenAIClient:
    """
    Thin wrapper around OpenAI's async chat completions.

    Expects:
      - `OPENAI_API_KEY` in environment
      - optional `OPENAI_MODEL` in environment
    """

    def __init__(self, *, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        # Development convenience:
        # - if `.env` exists in the repo root, load it into environment variables
        # - do NOT overwrite existing env vars
        if load_dotenv is not None:
            repo_root = Path(__file__).resolve().parents[2]
            load_dotenv(dotenv_path=repo_root / ".env", override=False)

        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing OPENAI_API_KEY.\n"
                "Set it in your environment or put it into `.env` (copied from `.env.example`)."
            )

        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self._client = AsyncOpenAI(api_key=api_key)

    async def call_openai(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Call OpenAI chat completions and parse the result as JSON.

        Expected payload keys:
          - `messages`: list[{"role": "...", "content": "..."}]
          - optional `model`: model name
          - optional `temperature`: float

        The method uses official OpenAI Python SDK and reads `OPENAI_API_KEY`
        from environment (see `__init__`).
        """

        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("payload must include non-empty `messages` list.")

        model = payload.get("model") or self._model
        temperature = payload.get("temperature", 0.2)

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                # Ask the model to emit a JSON object when supported.
                response_format={"type": "json_object"},
            )
        except TypeError:
            # Fallback for older SDK versions that don't support `response_format`.
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty message content.")

        return self._parse_json_object(content)

    # Backward-compatible helper (kept in case other modules still call it).
    async def chat_completion_json(
        self,
        *,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self.call_openai(
            {"messages": messages, "model": model, "temperature": 0.2}
        )

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not an object.")
            return parsed
        except json.JSONDecodeError:
            # Fallback: extract the first {...} block from a longer output.
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                raise RuntimeError("Failed to parse JSON from OpenAI response.")
            parsed = json.loads(match.group(0))
            if not isinstance(parsed, dict):
                raise RuntimeError("Parsed JSON is not an object.")
            return parsed

