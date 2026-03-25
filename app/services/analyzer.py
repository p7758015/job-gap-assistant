"""
Analyzer logic for `job-gap-assistant`.

It takes user input, builds a prompt for an LLM, and then parses the JSON
output into strongly typed Pydantic models.
"""

from __future__ import annotations

from typing import Any, Optional

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.openai_client import OpenAIClient


class JobGapAnalyzer:
    """Business logic for analyzing a job description vs. candidate profile."""

    def __init__(self, *, openai_client: OpenAIClient) -> None:
        self._openai_client = openai_client

    async def analyze(self, req: AnalyzeRequest) -> AnalyzeResponse:
        return await self.analyze_job_description(
            job_description=req.job_description,
            candidate_profile=req.candidate_profile,
            response_language=req.response_language,
        )

    async def analyze_job_description(
        self,
        *,
        job_description: str,
        candidate_profile: Optional[str],
        response_language: str = "ru",
    ) -> AnalyzeResponse:
        """
        Analyze job description and optional candidate profile.

        Requirements:
          - one OpenAI API call
          - model must emit strict JSON only (no extra text)
          - response must match `AnalyzeResponse` schema
        """

        system_prompt = (
            "You are a senior hiring manager and career coach. "
            "Return ONLY a valid JSON object and nothing else (no markdown, no commentary). "
            "The JSON MUST match the provided schema exactly: keys, nesting, and types. "
            "If you cannot infer something, omit it from arrays rather than inventing new items. "
            "Do not add any extra keys."
        )

        # JSON schema template (values are examples only).
        user_payload: dict[str, Any] = {
            "instructions": {
                "language_for_text": response_language,
                "rules": [
                    "Return ONLY JSON.",
                    "skills.must_have must be non-empty.",
                    "fit_score must be integer 0..100.",
                    "roadmap must contain 2..4 weeks, week numbers should start at 1.",
                    "projects estimated_duration_weeks should be integer >= 1.",
                    "Avoid inventing technologies/requirements that are not present in the JD. "
                    "You may include generic concepts (algorithms, systems, debugging mindset, soft skills) even if not explicitly named.",
                    "Use candidate_profile evidence to score fit and to produce gaps/projects/roadmap.",
                    "Make gaps align with missing/weak parts of candidate_profile compared to JD."
                ],
                "output_schema_example": {
                    "skills": {
                        "must_have": ["..."],
                        "nice_to_have": ["..."],
                        "bonus": ["..."],
                    },
                    "fit_score": 0,
                    "fit_explanation": "...",
                    "gaps": ["..."],
                    "projects": [
                        {
                            "title": "...",
                            "description": "...",
                            "estimated_duration_weeks": 1,
                        }
                    ],
                    "roadmap": [
                        {"week": 1, "focus": "...", "tasks": ["task1", "task2"]}
                    ],
                },
            },
            "input": {
                "job_description": job_description,
                "candidate_profile": candidate_profile,
            },
        }

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._stringify_prompt(user_payload)},
        ]

        raw: dict[str, Any] = await self._openai_client.call_openai(
            {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.2,
            }
        )

        return AnalyzeResponse.model_validate(raw)

    @staticmethod
    def _stringify_prompt(payload: dict[str, Any]) -> str:
        """
        Convert a prompt payload into a compact string.

        This avoids accidental formatting differences and keeps the request predictable.
        """

        import json

        return json.dumps(payload, ensure_ascii=False)

