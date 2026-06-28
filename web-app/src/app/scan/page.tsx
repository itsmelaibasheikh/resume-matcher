"use client";

import { useState, useEffect, useRef } from "react";
import { matchResumeToPDF, MatchResult } from "@/lib/api";

function useCountUp(target: number, duration: number = 1000) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (target === 0) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return count;
}

function ScoreDisplay({ score }: { score: number }) {
  const count = useCountUp(score, 1200);
  const color = score >= 70 ? "#22d3ee" : score >= 45 ? "#a78bfa" : "#f87171";
  return (
    <div className="text-center py-8">
      <p className="text-sm uppercase tracking-widest text-gray-500 mb-2">
        Overall Match
      </p>
      <p className="text-8xl font-bold tabular-nums" style={{ color }}>
        {count}<span className="text-4xl">%</span>
      </p>
    </div>
  );
}

function RequirementCard({ text, score, type, index }: {
  text: string; score: number; type: "matched" | "missing"; index: number;
}) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), index * 60);
    return () => clearTimeout(timer);
  }, [index]);

  const borderColor = type === "matched" ? "#7c3aed" : "#ef4444";
  const scoreColor = type === "matched" ? "#22d3ee" : "#f87171";

  return (
    <div
      className="rounded-xl p-4 border transition-all duration-500"
      style={{
        backgroundColor: "#1e1e24",
        borderColor: visible ? borderColor + "40" : "transparent",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(12px)",
      }}
    >
      <div className="flex justify-between items-start gap-4">
        <p className="text-sm text-gray-300 leading-relaxed">{text}</p>
        <span className="text-sm font-bold shrink-0" style={{ color: scoreColor }}>
          {score}%
        </span>
      </div>
    </div>
  );
}

export default function ScanPage() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  async function handleSubmit() {
    if (!resumeFile || !jdText.trim()) {
      setError("Upload a resume and paste a job description.");
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const data = await matchResumeToPDF(resumeFile, jdText);
      setResult(data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch {
      setError("Could not reach the NLP service. Is it running?");
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.type === "application/pdf") setResumeFile(file);
  }

  return (
    <main className="min-h-screen p-8" style={{ backgroundColor: "#0d0d0f", color: "#f8fafc" }}>
      <div className="max-w-4xl mx-auto mb-10">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#7c3aed" }} />
          <span className="text-xs uppercase tracking-widest text-gray-500">Resume Matcher</span>
        </div>
        <h1 className="text-4xl font-bold tracking-tight">How well do you fit?</h1>
        <p className="text-gray-400 mt-2">
          Drop your resume and paste a job description. Get an honest match score in seconds.
        </p>
      </div>

      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Upload */}
          <div
            className="rounded-xl p-6 border-2 border-dashed transition-all cursor-pointer"
            style={{
              backgroundColor: "#1e1e24",
              borderColor: dragOver ? "#7c3aed" : resumeFile ? "#7c3aed80" : "#2e2e38",
            }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById("fileInput")?.click()}
          >
            <input
              id="fileInput" type="file" accept=".pdf" className="hidden"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
            />
            <div className="flex flex-col items-center justify-center h-32 gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                style={{ backgroundColor: "#7c3aed20" }}>📄</div>
              {resumeFile ? (
                <>
                  <p className="text-sm font-medium" style={{ color: "#a78bfa" }}>{resumeFile.name}</p>
                  <p className="text-xs text-gray-500">Click to change</p>
                </>
              ) : (
                <>
                  <p className="text-sm text-gray-400">Drop your resume here</p>
                  <p className="text-xs text-gray-600">PDF only</p>
                </>
              )}
            </div>
          </div>

          {/* JD */}
          <div className="rounded-xl p-4 border" style={{ backgroundColor: "#1e1e24", borderColor: "#2e2e38" }}>
            <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">Job Description</p>
            <textarea
              className="w-full h-40 bg-transparent text-sm text-gray-200 resize-none focus:outline-none placeholder-gray-600"
              placeholder="Paste the full job description here..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </div>
        </div>

        {error && <p className="text-sm mb-4" style={{ color: "#f87171" }}>{error}</p>}

        <button
          onClick={handleSubmit} disabled={loading}
          className="w-full py-3 rounded-xl font-semibold text-sm tracking-wide transition-all duration-200"
          style={{
            backgroundColor: loading ? "#2e2e38" : "#7c3aed",
            color: loading ? "#6b7280" : "#fff",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⟳</span> Analyzing...
            </span>
          ) : "Analyze Match →"}
        </button>

        {result && (
          <div ref={resultsRef} className="mt-12">
            <div className="rounded-2xl border mb-8" style={{ backgroundColor: "#1e1e24", borderColor: "#2e2e38" }}>
              <ScoreDisplay score={result.overall_score} />
            </div>

            {result.matched.length > 0 && (
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xs uppercase tracking-widest" style={{ color: "#22d3ee" }}>Matched</span>
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: "#22d3ee15", color: "#22d3ee" }}>
                    {result.matched.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {result.matched.map((item, i) => (
                    <RequirementCard key={i} text={item.requirement} score={item.score} type="matched" index={i} />
                  ))}
                </div>
              </div>
            )}

            {result.missing.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xs uppercase tracking-widest" style={{ color: "#f87171" }}>Missing</span>
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: "#ef444415", color: "#f87171" }}>
                    {result.missing.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {result.missing.map((item, i) => (
                    <RequirementCard key={i} text={item.requirement} score={item.score} type="missing" index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}