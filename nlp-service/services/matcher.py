"""
matcher.py
"""

import re
import math
from services.embedder import embed_texts, cosine_similarity_matrix
import numpy as np

SEMANTIC_WEIGHT = 0.65
KEYWORD_WEIGHT = 0.35

MATCH_THRESHOLD = 0.45
RAW_SCORE_FLOOR = 0.05
RAW_SCORE_CEILING = 0.65

HIGH_VALUE_IDF_THRESHOLD = 1.5
GENERIC_OVERLAP_PENALTY = 0.5

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "to", "of", "in", "on", "for", "with", "at", "by",
    "from", "as", "this", "that", "these", "those", "it", "its", "we",
    "you", "your", "our", "their", "will", "have", "has", "had", "do",
    "does", "did", "experience", "required", "looking", "strong",
}

HEADER_BLOCKLIST = {
    "required skills", "soft skills", "technical skills", "responsibilities",
    "education", "projects", "certifications", "professional experience",
    "professional summary", "preferred qualifications", "about the role",
    "programming languages", "backend technologies", "databases",
    "cloud & devops", "tools", "skills", "summary", "experience",
    "languages", "frontend technologies", "other skills",
}

METADATA_FIELD_LABELS = {
    "location", "department", "employment type", "experience level",
    "salary", "salary range", "job type", "work type", "industry",
    "company", "position", "reports to", "team", "schedule",
    "contract type", "start date", "application deadline",
    "email", "phone", "linkedin", "github", "website", "address",
}

# Patterns that indicate a line is resume contact info, not a skill
CONTACT_PATTERNS = [
    r"^[\w\.\-]+@[\w\.\-]+\.\w+$",           # email
    r"^\+?[\d\s\-\(\)]{7,}$",                 # phone number
    r"^https?://",                             # URL
    r"^linkedin\.com",                         # linkedin
    r"^github\.com",                           # github
    r"^\d{4}\s*[-–]\s*(\d{4}|present)$",      # date range like 2018 - 2022
    r"^\d{4}$",                                # standalone year
]


def is_contact_line(line: str) -> bool:
    stripped = line.strip()
    for pattern in CONTACT_PATTERNS:
        if re.match(pattern, stripped, re.IGNORECASE):
            return True
    return False


def is_metadata_line(line: str) -> bool:
    if ":" not in line:
        return False
    label = line.split(":", 1)[0].strip().lower().lstrip("-").strip()
    return label in METADATA_FIELD_LABELS


HEADER_POSITION_MIN_WORDS = 4
HEADER_POSITION_NEXT_LINE_MIN_WORDS = 6


def is_known_header(line: str) -> bool:
    stripped = line.strip().lstrip("-").strip()
    lower = stripped.lower().rstrip(":")
    return lower in HEADER_BLOCKLIST


def is_header_by_position(lines: list[str], i: int) -> bool:
    stripped = lines[i].strip().lstrip("-").strip()
    word_count = len(stripped.split())
    if word_count > HEADER_POSITION_MIN_WORDS:
        return False
    if i + 1 >= len(lines):
        return False
    next_line = lines[i + 1].strip().lstrip("-").strip()
    next_word_count = len(next_line.split())
    return next_word_count >= HEADER_POSITION_NEXT_LINE_MIN_WORDS


def is_real_content_line(lines: list[str], i: int) -> bool:
    line = lines[i]
    if is_contact_line(line):
        return False
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

    if len(raw_lines) < 3:
        raw_lines = re.split(r'(?<=[.!?])\s+', text.strip())
        raw_lines = [line.strip() for line in raw_lines if len(line.strip()) > 3]

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
    overlap = req_keywords & resume_keywords
    if not overlap:
        return False
    return all(idf_weights.get(w, 1.0) < HIGH_VALUE_IDF_THRESHOLD for w in overlap)


def rescale_score(raw_score: float) -> int:
    clamped = max(RAW_SCORE_FLOOR, min(raw_score, RAW_SCORE_CEILING))
    scaled = (clamped - RAW_SCORE_FLOOR) / (RAW_SCORE_CEILING - RAW_SCORE_FLOOR)
    return round(scaled * 100)


def extract_years_from_text(text: str) -> int:
    """Extract the highest number of years mentioned in text."""
    matches = re.findall(r'(\d+)\+?\s*years?', text.lower())
    return max((int(m) for m in matches), default=0)


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

    # Extract total years of experience from full resume text once
    resume_total_years = extract_years_from_text(resume_text)

    matched = []
    missing = []
    blended_scores_for_overall = []

    for i, requirement in enumerate(jd_lines):
        req_keywords = jd_keyword_sets[i]

        # Hard rule: years of experience check
        required_yrs = extract_years_from_text(requirement)
        if required_yrs > 0 and resume_total_years < required_yrs:
            missing.append({"requirement": requirement, "score": 20})
            blended_scores_for_overall.append(0.1)
            continue

        blended_per_line = []
        for j, resume_line in enumerate(resume_lines):
            sem_score = float(semantic_sim[i][j])
            kw_score = weighted_keyword_overlap_score(
                req_keywords, resume_keyword_sets[j], idf_weights
            )
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