# Project Progress — Resume Matcher

## What this project is
A tool that compares a resume against a job description using AI (semantic
embeddings) + keyword matching, and shows: overall match %, which
requirements are met, which are missing.

## Status: CORE ENGINE DONE AND WORKING

### Done:
1. **embedder.py** — wraps sentence-transformers (`all-MiniLM-L6-v2`) to
   turn text into vectors and compute similarity.
2. **matcher.py** — the real logic:
   - Hybrid scoring: blends semantic similarity (65%) + IDF-weighted
     keyword overlap (35%)
   - Generic-overlap penalty: stops false positives from coincidental
     shared common words (e.g. "pipelines" alone isn't enough to match
     "CI/CD pipelines" to "data pipelines")
   - Header/metadata filtering: strips out bare section headers
     ("Education", "Skills") and job-posting metadata fields
     ("Location:", "Department:") so they don't pollute results
   - Returns top-3 candidate matches per requirement for explainability
3. **main.py** — FastAPI wrapper exposing `/match` as a real API endpoint.
   Tested successfully via `/docs` (Swagger UI) with a real resume + JD.

### Verified working on real test data:
- Tested with a realistic 10-bullet resume vs a realistic 25+ line JD.
- Correctly matched: CI/CD, Docker/Kubernetes, REST APIs, AWS, databases,
  testing, Agile/Scrum, mentoring, leadership, soft skills.
- Correctly flagged as missing: cooking (sanity-check trap), conflict
  resolution, effective communication (genuinely not in that resume).
- No header/metadata noise in output anymore.

## NOT done yet (next steps, in order):
1. **PDF parser** — accept actual .pdf file uploads, extract text
   (pdfplumber already installed for this).
2. **Next.js frontend** — the actual website UI.
3. **MongoDB** — save user accounts + past scan history.
4. **Structural/ATS-style checks** (optional) — contact info present,
   word count, date formatting, etc.
5. **Deploy** — Next.js on Vercel, this service on Render, MongoDB Atlas.

## How to resume this project (DO THIS FIRST when you come back)
1. Open the `nlp-service` folder in VS Code.
2. Open terminal, activate venv: `venv\Scripts\activate`
3. Run the server: `uvicorn main:app --reload`
4. Test at: `http://127.0.0.1:8000/docs`

## Key files
- `services/embedder.py` — embedding model wrapper
- `services/matcher.py` — all matching/scoring logic (the important one)
- `main.py` — FastAPI app + `/match` endpoint
- `requirements.txt` — Python dependencies (Python 3.13 / Windows verified)