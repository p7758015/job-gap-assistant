"""
FastAPI entrypoint for `job-gap-assistant`.

It exposes an API endpoint that accepts:
  - job description text
  - user's current experience text

And returns structured analysis:
  - key competencies & technologies
  - fit score
  - mini-projects to close gaps
  - a 2-4 week roadmap
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import JobGapAnalyzer
from app.services.openai_client import OpenAIClient
from pydantic import ValidationError

app = FastAPI(title="job-gap-assistant", version="0.1.0")

# Resolve frontend directory relative to this file so it works
# both locally and inside Docker.
FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()

if FRONTEND_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static",
    )


@app.on_event("startup")
def _startup() -> None:
    """
    Initialize dependencies once at application startup.

    Requires `OPENAI_API_KEY` env var.
    """

    openai_client = OpenAIClient()
    analyzer = JobGapAnalyzer(openai_client=openai_client)

    # Stored on `app.state` so request handlers can reuse it.
    app.state.analyzer = analyzer


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """
    Serve the frontend SPA index.html.

    When running inside Docker, both API and SPA are available on :8000.
    """

    index_path = FRONTEND_DIR / "index.html"
    if not index_path.is_file():
        # Simple fallback: indicate that the frontend is missing.
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(index_path)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    analyzer: JobGapAnalyzer = app.state.analyzer
    try:
        return await analyzer.analyze(req)
    except ValueError as exc:
        # Business/validation errors we can explain safely.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        # The LLM output didn't match the expected strict schema.
        raise HTTPException(
            status_code=400,
            detail="Model output validation failed (invalid structured response).",
        ) from exc
    except Exception as exc:
        # Avoid leaking internal details; keep it generic for the portfolio demo.
        raise HTTPException(status_code=500, detail="Internal server error") from exc

