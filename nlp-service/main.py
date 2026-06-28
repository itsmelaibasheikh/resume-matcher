"""
main.py

FastAPI app entry point. Exposes our matching logic (services/matcher.py)
as a real HTTP API that a frontend (or Postman, or a browser) can call.

Run locally with:
    uvicorn main:app --reload

Then visit http://127.0.0.1:8000/docs for an interactive API tester
(FastAPI generates this automatically - no extra code needed).
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.matcher import match_resume_to_jd
from services.pdf_parser import extract_text_from_pdf

app = FastAPI(
    title="Resume Matcher NLP Service",
    description="Semantic + keyword hybrid matching between resumes and job descriptions.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / response schemas (Pydantic models) ---

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str


class MatchCandidate(BaseModel):
    line: str
    score: int


class MatchedRequirement(BaseModel):
    requirement: str
    score: int
    candidates: list[MatchCandidate]


class MissingRequirement(BaseModel):
    requirement: str
    score: int


class MatchResponse(BaseModel):
    overall_score: int
    matched: list[MatchedRequirement]
    missing: list[MissingRequirement]


# --- Routes ---

@app.get("/")
def health_check():
    """Simple endpoint to confirm the service is running."""
    return {"status": "ok", "service": "resume-matcher-nlp"}


@app.post("/match", response_model=MatchResponse)
def match_endpoint(payload: MatchRequest):
    """
    Original endpoint. Accepts resume + job description as plain TEXT
    (both fields are strings), returns the structured match result.
    Useful for testing, or when the frontend already has plain text
    (e.g. pasted into a textarea).
    """
    result = match_resume_to_jd(payload.resume_text, payload.jd_text)
    return result


@app.post("/match-pdf", response_model=MatchResponse)
async def match_pdf_endpoint(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
):
    """
    Accepts an uploaded PDF resume FILE plus the job description as a
    FORM FIELD (not a URL query parameter) - this matters because query
    parameters can silently collapse real line breaks into spaces in
    some clients, which breaks our line-by-line matching logic. Form
    fields preserve newlines correctly.
    """
    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported for resume_file.",
        )

    file_bytes = await resume_file.read()

    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. It may be corrupted, password-protected, or an image-only scan.",
        )

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in this PDF. It may be a scanned image rather than real text.",
        )

    result = match_resume_to_jd(resume_text, jd_text)
    return result

@app.post("/debug-pdf")
async def debug_pdf(resume_file: UploadFile = File(...)):
    file_bytes = await resume_file.read()
    resume_text = extract_text_from_pdf(file_bytes)
    return {"text_length": len(resume_text), "preview": resume_text[:1000]}