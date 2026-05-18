"""FastAPI entry point for the Insurance Claims Agent."""
from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .extractor import extract_fields
from .reasoning import build_reasoning
from .router import decide_route
from .schemas import ClaimResponse
from .utils import extract_text, upload_to_azure_blob
from .validator import validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("claims-agent")

app = FastAPI(
    title="Autonomous Insurance Claims Processing Agent",
    description="Process FNOL documents: extract, validate, classify, and route insurance claims.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/process-claim", response_model=ClaimResponse)
async def process_claim(file: UploadFile = File(...)) -> ClaimResponse:
    """Upload a PDF/TXT FNOL document and receive a structured routing decision."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required.")

    name = file.filename.lower()
    if not (name.endswith(".pdf") or name.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files are supported.")

    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Optional: archive original to Azure Blob Storage
        upload_to_azure_blob(file.filename, data)

        text = extract_text(file.filename, data)
        if not text or not text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the document (even with OCR).",
            )

        fields = extract_fields(text)
        missing = validate(fields)
        route, triggers = decide_route(fields, missing)
        reasoning = build_reasoning(fields, missing, route, triggers)

        return ClaimResponse(
            extractedFields=fields.model_dump(),
            missingFields=missing,
            recommendedRoute=route,
            reasoning=reasoning,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to process claim")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc
