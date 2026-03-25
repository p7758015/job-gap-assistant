import pytest

from app.schemas import AnalyzeRequest
from app.services.analyzer import JobGapAnalyzer


class FakeOpenAIClient:
    async def call_openai(self, payload: dict) -> dict:
        # Return a response that matches the updated `AnalyzeResponse` shape.
        return {
            "skills": {
                "must_have": ["FastAPI", "API design", "Writing unit tests"],
                "nice_to_have": ["HTTP"],
                "bonus": ["System design basics"],
            },
            "fit_score": 80,
            "fit_explanation": "Your profile shows strong FastAPI and testing experience that matches the JD.",
            "gaps": ["Database integration depth", "Broader system design"],
            "projects": [
                {
                    "title": "FastAPI service with DB integration",
                    "description": "Implement endpoints backed by a DB layer and cover them with integration tests.",
                    "estimated_duration_weeks": 2,
                }
            ],
            "roadmap": [
                {
                    "week": 1,
                    "focus": "API architecture and strict Pydantic schemas",
                    "tasks": ["Design request/response models", "Implement endpoints", "Add unit tests"],
                },
                {
                    "week": 2,
                    "focus": "Database integration and integration tests",
                    "tasks": ["Add persistence layer", "Write integration tests", "Refine error handling"],
                },
            ],
        }


@pytest.mark.asyncio
async def test_analyzer_parses_and_validates_response():
    analyzer = JobGapAnalyzer(openai_client=FakeOpenAIClient())
    req = AnalyzeRequest(
        job_description="Backend engineer with FastAPI and testing experience.",
        candidate_profile="Built FastAPI endpoints and wrote unit tests.",
        response_language="ru",
    )

    resp = await analyzer.analyze(req)

    assert resp.fit_score == 80
    assert "FastAPI" in resp.skills.must_have
    assert len(resp.roadmap) == 2
    assert resp.roadmap[0].week == 1

