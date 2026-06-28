"""
matcher.py

Core logic: given resume text and job description text, figure out
how well they match.

HYBRID APPROACH (why):
- Pure semantic similarity (embeddings) can be fooled by surface word
  overlap unrelated to real meaning (e.g. "data pipelines" vs "CI/CD
  pipelines" scored high just because both contain "pipelines").
- Pure keyword matching is too rigid - it misses real synonyms
  ("Jenkins" should count toward "CI/CD experience").
- So we BLEND both: semantic score (captures meaning/synonyms) +
  keyword overlap score (anchors on exact technical terms that matter).

IDF WEIGHTING (why):
- Not all keywords are equally informative. A word like "experience" or
  "pipelines" appears in many lines and tells us little. A word like
  "jenkins" or "fastapi" appears rarely and is a strong signal.
- weight(word) = log(total_lines / lines_containing_word) + 1.
  Rare words -> high weight. Common words -> low weight.

GENERIC-OVERLAP PENALTY (why):
- Even with IDF weighting, a small free embedding model can still rate
  two phrases as similar mostly because they share ONE common/generic
  word (e.g. both contain "pipelines"), even though the real concepts
  differ (CI/CD pipelines vs data pipelines).
- We detect this specific failure mode: if a resume line's ONLY keyword
  overlap with the requirement consists of low-IDF (generic) words, we
  apply a penalty to its semantic score before blending - it can't win
  purely on a coincidental generic word match.

We also return the TOP-3 candidate resume lines per requirement, so
false positives are visible and the result is explainable.
"""

import re
import math
from services.embedder import embed_texts, cosine_similarity_matrix
import numpy as np

SEMANTIC_WEIGHT = 0.65
KEYWORD_WEIGHT = 0.35

MATCH_THRESHOLD = 0.28
RAW_SCORE_FLOOR = 0.05
RAW_SCORE_CEILING = 0.65

# A keyword counts as "high-value" (specific/technical) if its IDF weight
# is at or above this. Below this, it's treated as too generic to be
# trusted as the SOLE basis for a match.
HIGH_VALUE_IDF_THRESHOLD = 1.5

# Multiplier applied to the semantic score when the only overlap is generic.
GENERIC_OVERLAP_PENALTY = 0.5

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "to", "of", "in", "on", "for", "with", "at", "by",
    "from", "as", "this", "that", "these", "those", "it", "its", "we",
    "you", "your", "our", "their", "will", "have", "has", "had", "do",
    "does", "did", "experience", "required", "looking", "strong",
}

# Bare section headers that carry no matchable content on their own
# (e.g. "Education", "Required Skills"). Used as a backup safety net
# alongside the position-based detection below.
HEADER_BLOCKLIST = {
    "required skills", "soft skills", "technical skills", "responsibilities",
    "education", "projects", "certifications", "professional experience",
    "professional summary", "preferred qualifications", "about the role",
    "programming languages", "backend technologies", "databases",
    "cloud & devops", "tools", "skills", "summary", "experience",
}

# Common job-posting metadata field labels. Lines starting with one of
# these (e.g. "Location: Karachi, Pakistan") describe the JOB POSTING
# itself, not a skill or requirement a candidate's resume should be
# expected to satisfy - so we exclude them from matching entirely.
METADATA_FIELD_LABELS = {
    "location", "department", "employment type", "experience level",
    "salary", "salary range", "job type", "work type", "industry",
    "company", "position", "reports to", "team", "schedule",
    "contract type", "start date", "application deadline",
}


def is_metadata_line(line: str) -> bool:
    """
    Returns True if the line is a 'Label: value' job-posting metadata
    field (e.g. "Location: Karachi, Pakistan (Hybrid)"), based on an
    explicit list of common field labels - not a heuristic on length,
    so it won't accidentally catch real "Label: real skill content"
    lines like "Programming Languages: Python, Java".
    """
    if ":" not in line:
        return False
    label = line.split(":", 1)[0].strip().lower().lstrip("-").strip()
    return label in METADATA_FIELD_LABELS


# A short line is followed by a clearly longer line (a real sentence) at
# least this many words to be treated as a header-by-position signal.
HEADER_POSITION_MIN_WORDS = 4
HEADER_POSITION_NEXT_LINE_MIN_WORDS = 6


def is_known_header(line: str) -> bool:
    """Exact match against the conservative header blocklist."""
    stripped = line.strip().lstrip("-").strip()
    lower = stripped.lower().rstrip(":")
    return lower in HEADER_BLOCKLIST


def is_header_by_position(lines: list[str], i: int) -> bool:
    """
    A line is treated as a bare header if it's short AND the line right
    after it is clearly longer (a real sentence/bullet). This catches
    "Education" -> "Bachelor of Science..." but does NOT wrongly catch
    short-but-real lines like "Conflict resolution" when their neighbors
    are also short (e.g. a list of one-line soft skills).
    """
    stripped = lines[i].strip().lstrip("-").strip()
    word_count = len(stripped.split())
    if word_count > HEADER_POSITION_MIN_WORDS:
        return False

    if i + 1 >= len(lines):
        return False  # last line - no next-line context, assume real content

    next_line = lines[i + 1].strip().lstrip("-").strip()
    next_word_count = len(next_line.split())

    return next_word_count >= HEADER_POSITION_NEXT_LINE_MIN_WORDS


def is_real_content_line(lines: list[str], i: int) -> bool:
    """
    Returns False if the line at index i is a bare section header or a
    job-posting metadata field, detected via blocklist, position, or
    label matching. Returns True for everything else, including short
    lines that are genuine standalone content (e.g. "Conflict resolution").
    """
    line = lines[i]
    if is_metadata_line(line):
        return False
    if is_known_header(line):
        return False
    if is_header_by_position(lines, i):
        return False
    return True


def split_into_lines(text: str) -> list[str]:
    raw_lines = [line.strip() for line in text.split("\n")]
    raw_lines = [line for line in raw_lines if len(line) > 3]
    return [line for i, line in enumerate(raw_lines) if is_real_content_line(raw_lines, i)]


def extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9\+\#\.]+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}


def compute_idf_weights(all_keyword_sets: list[set[str]]) -> dict[str, float]:
    total_lines = len(all_keyword_sets)
    doc_freq: dict[str, int] = {}
    for kw_set in all_keyword_sets:
        for word in kw_set:
            doc_freq[word] = doc_freq.get(word, 0) + 1

    weights = {}
    for word, freq in doc_freq.items():
        weights[word] = math.log((total_lines + 1) / (freq + 1)) + 1
    return weights


def weighted_keyword_overlap_score(
    req_keywords: set[str],
    resume_keywords: set[str],
    idf_weights: dict[str, float],
) -> float:
    if not req_keywords:
        return 0.0
    total_weight = sum(idf_weights.get(w, 1.0) for w in req_keywords)
    if total_weight == 0:
        return 0.0
    overlap = req_keywords & resume_keywords
    matched_weight = sum(idf_weights.get(w, 1.0) for w in overlap)
    return matched_weight / total_weight


def overlap_is_only_generic(
    req_keywords: set[str],
    resume_keywords: set[str],
    idf_weights: dict[str, float],
) -> bool:
    """
    Returns True if the overlapping words between requirement and resume
    line exist, but EVERY one of them is below the high-value IDF
    threshold (i.e. the match is built entirely on generic words).
    Returns False if there's no overlap at all, or if at least one
    overlapping word is genuinely specific/high-value.
    """
    overlap = req_keywords & resume_keywords
    if not overlap:
        return False  # no overlap at all - not this failure mode
    return all(idf_weights.get(w, 1.0) < HIGH_VALUE_IDF_THRESHOLD for w in overlap)


def rescale_score(raw_score: float) -> int:
    clamped = max(RAW_SCORE_FLOOR, min(raw_score, RAW_SCORE_CEILING))
    scaled = (clamped - RAW_SCORE_FLOOR) / (RAW_SCORE_CEILING - RAW_SCORE_FLOOR)
    return round(scaled * 100)


def match_resume_to_jd(resume_text: str, jd_text: str, top_k: int = 3) -> dict:
    resume_lines = split_into_lines(resume_text)
    jd_lines = split_into_lines(jd_text)

    if not resume_lines or not jd_lines:
        return {"overall_score": 0, "matched": [], "missing": []}

    resume_embeddings = embed_texts(resume_lines)
    jd_embeddings = embed_texts(jd_lines)
    semantic_sim = cosine_similarity_matrix(jd_embeddings, resume_embeddings)

    resume_keyword_sets = [extract_keywords(line) for line in resume_lines]
    jd_keyword_sets = [extract_keywords(line) for line in jd_lines]

    idf_weights = compute_idf_weights(resume_keyword_sets + jd_keyword_sets)

    matched = []
    missing = []
    blended_scores_for_overall = []

    for i, requirement in enumerate(jd_lines):
        req_keywords = jd_keyword_sets[i]

        blended_per_line = []
        for j, resume_line in enumerate(resume_lines):
            sem_score = float(semantic_sim[i][j])
            kw_score = weighted_keyword_overlap_score(
                req_keywords, resume_keyword_sets[j], idf_weights
            )

            # Apply the generic-overlap penalty to the semantic score
            # BEFORE blending, so a coincidental shared generic word can't
            # prop up an otherwise-unrelated line.
            if overlap_is_only_generic(req_keywords, resume_keyword_sets[j], idf_weights):
                sem_score *= GENERIC_OVERLAP_PENALTY

            blended = (SEMANTIC_WEIGHT * sem_score) + (KEYWORD_WEIGHT * kw_score)
            blended_per_line.append(blended)

        blended_per_line = np.array(blended_per_line)
        top_indices = np.argsort(blended_per_line)[::-1][:top_k]
        best_score = float(blended_per_line[top_indices[0]])
        blended_scores_for_overall.append(best_score)

        candidates = [
            {"line": resume_lines[idx], "score": rescale_score(float(blended_per_line[idx]))}
            for idx in top_indices
        ]

        if best_score >= MATCH_THRESHOLD:
            matched.append({
                "requirement": requirement,
                "score": rescale_score(best_score),
                "candidates": candidates,
            })
        else:
            missing.append({
                "requirement": requirement,
                "score": rescale_score(best_score),
            })

    overall_raw = float(np.mean(blended_scores_for_overall)) if blended_scores_for_overall else 0.0
    overall_score = rescale_score(overall_raw)

    return {
        "overall_score": overall_score,
        "matched": matched,
        "missing": missing,
    }

def split_into_lines(text: str) -> list[str]:
    # First try newline splitting (ideal case)
    raw_lines = [line.strip() for line in text.split("\n")]
    raw_lines = [line for line in raw_lines if len(line) > 3]
    
    # If we got almost nothing (JD was pasted as one blob with no newlines),
    # fall back to splitting on sentence-ending punctuation instead
    if len(raw_lines) < 3:
        raw_lines = re.split(r'(?<=[.!?])\s+', text.strip())
        raw_lines = [line.strip() for line in raw_lines if len(line.strip()) > 3]
    
    return [line for i, line in enumerate(raw_lines) if is_real_content_line(raw_lines, i)]