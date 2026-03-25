"""
Pydantic schemas for request/response contracts.

These types are used both by FastAPI for validation and by the analyzer
for parsing the model's JSON output into a strongly typed response.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class _BaseSchema(BaseModel):
    """Shared strict config: forbid unknown fields."""

    model_config = ConfigDict(extra="forbid")


class AnalyzeRequest(_BaseSchema):
    """
    Input contract for the /analyze endpoint.

    The LLM receives `job_description` and optional `candidate_profile`.
    """

    job_description: str = Field(..., description="Plain text job description.")
    candidate_profile: Optional[str] = Field(
        default=None, description="Optional plain text describing your current experience/skills."
    )
    response_language: Literal["ru", "en"] = Field(
        default="ru", description="Language for the generated explanation."
    )


class Skills(_BaseSchema):
    """Extracted skills/technologies grouped by priority."""

    must_have: list[str] = Field(..., description="Required skills/technologies extracted from the JD.")
    nice_to_have: list[str] = Field(..., description="Nice-to-have skills/technologies mentioned in the JD.")
    bonus: list[str] = Field(..., description="Bonus skills/technologies that may help, but aren't required.")


class Project(_BaseSchema):
    title: str = Field(..., description="Project title.")
    description: str = Field(..., description="Project description (what to build/do).")
    estimated_duration_weeks: int = Field(
        ..., description="Rough project duration in weeks (integer)."
    )


class RoadmapWeek(_BaseSchema):
    week: int = Field(..., description="Week number in the roadmap.")
    focus: str = Field(..., description="Main focus for the week (single string).")
    tasks: list[str] = Field(..., description="Concrete tasks to complete during the week.")


class AnalyzeResponse(_BaseSchema):
    skills: Skills = Field(..., description="Skills extracted from the JD.")
    fit_score: int = Field(..., description="How well the candidate matches the job (0..100).")
    fit_explanation: str = Field(
        ..., description="Explanation of the fit score, taking candidate_profile into account."
    )
    gaps: list[str] = Field(..., description="Detected gaps vs the job.")
    projects: list[Project] = Field(..., description="Specific projects to close the gaps.")
    roadmap: list[RoadmapWeek] = Field(..., description="Roadmap to improve (2-4 weeks recommended).")

