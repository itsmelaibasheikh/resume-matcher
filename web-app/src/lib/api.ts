import axios from "axios";

const NLP_SERVICE_URL = "http://127.0.0.1:8000";

export interface MatchCandidate {
  line: string;
  score: number;
}

export interface MatchedRequirement {
  requirement: string;
  score: number;
  candidates: MatchCandidate[];
}

export interface MissingRequirement {
  requirement: string;
  score: number;
}

export interface MatchResult {
  overall_score: number;
  matched: MatchedRequirement[];
  missing: MissingRequirement[];
}

export async function matchResumeToPDF(
  resumeFile: File,
  jdText: string
): Promise<MatchResult> {
  const formData = new FormData();
  formData.append("resume_file", resumeFile);
  formData.append("jd_text", jdText);

  const response = await axios.post(`${NLP_SERVICE_URL}/match-pdf`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}