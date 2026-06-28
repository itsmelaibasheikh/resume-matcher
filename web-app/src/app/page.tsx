"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

function AnimatedStat({ value, label }: { value: string; label: string }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 300);
    return () => clearTimeout(t);
  }, []);

  return (
    <div
      className="transition-all duration-700"
      style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
    >
      <p className="text-3xl font-bold" style={{ color: "#a78bfa" }}>{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

const steps = [
  { number: "01", title: "Upload your resume", desc: "Drop a PDF — no copy-pasting, no reformatting." },
  { number: "02", title: "Paste the job description", desc: "Copy it straight from LinkedIn, Indeed, or anywhere." },
  { number: "03", title: "Get your match score", desc: "See exactly what you cover and what's missing — instantly." },
];

const features = [
  { icon: "⚡", title: "Semantic matching", desc: "Understands meaning, not just keywords. 'Led a team' matches 'leadership skills'." },
  { icon: "🎯", title: "Requirement breakdown", desc: "Every JD requirement checked individually so you know exactly where you stand." },
  { icon: "🔒", title: "Runs locally", desc: "Your resume never leaves your machine. No cloud, no storage, no tracking." },
];

export default function HomePage() {
  const [heroVisible, setHeroVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setHeroVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <main style={{ backgroundColor: "#0d0d0f", color: "#f8fafc" }}>
      {/* Hero */}
      <section className="max-w-4xl mx-auto px-8 pt-24 pb-20">
        <div
          className="transition-all duration-700"
          style={{ opacity: heroVisible ? 1 : 0, transform: heroVisible ? "translateY(0)" : "translateY(20px)" }}
        >
          <div
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs mb-6 border"
            style={{ backgroundColor: "#7c3aed15", borderColor: "#7c3aed40", color: "#a78bfa" }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
            Powered by semantic embeddings — no GPT, no API costs
          </div>

          <h1 className="text-6xl font-bold tracking-tight leading-tight mb-6">
            Know if you fit{" "}
            <span style={{ color: "#7c3aed" }}>before</span>
            <br /> you apply.
          </h1>

          <p className="text-lg text-gray-400 max-w-xl mb-10 leading-relaxed">
            Upload your resume, paste a job description, and get an honest
            match score — powered by real NLP running entirely on your machine.
          </p>

          <div className="flex items-center gap-4">
            <Link
              href="/scan"
              className="px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90"
              style={{ backgroundColor: "#7c3aed", color: "#fff" }}
            >
              Analyze my resume
            </Link>
            
             <Link
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="px-6 py-3 rounded-xl font-semibold text-sm border transition-all duration-200 hover:border-gray-500"
              style={{ borderColor: "#2e2e38", color: "#9ca3af" }}
            >
              View on GitHub
            </Link>
          </div>
        </div>

        <div
          className="grid grid-cols-3 gap-8 mt-20 pt-10 border-t"
          style={{ borderColor: "#1e1e24" }}
        >
          <AnimatedStat value="Hybrid" label="Semantic + keyword scoring" />
          <AnimatedStat value="Local" label="Runs on your machine" />
          <AnimatedStat value="Free" label="No API keys, no cost" />
        </div>
      </section>

      {/* How it works */}
      <section className="border-t py-20" style={{ borderColor: "#1e1e24" }}>
        <div className="max-w-4xl mx-auto px-8">
          <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">How it works</p>
          <h2 className="text-3xl font-bold mb-12">Three steps to clarity.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {steps.map((step, i) => (
              <div
                key={i}
                className="rounded-xl p-6 border transition-all duration-200 hover:border-purple-800"
                style={{ backgroundColor: "#1e1e24", borderColor: "#2e2e38" }}
              >
                <p className="text-xs font-mono mb-4" style={{ color: "#7c3aed" }}>{step.number}</p>
                <h3 className="font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t py-20" style={{ borderColor: "#1e1e24" }}>
        <div className="max-w-4xl mx-auto px-8">
          <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Why it works</p>
          <h2 className="text-3xl font-bold mb-12">Not just keyword matching.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={i}
                className="rounded-xl p-6 border transition-all duration-200 hover:border-purple-800"
                style={{ backgroundColor: "#1e1e24", borderColor: "#2e2e38" }}
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-xl mb-4"
                  style={{ backgroundColor: "#7c3aed15" }}
                >
                  {f.icon}
                </div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t py-20" style={{ borderColor: "#1e1e24" }}>
        <div className="max-w-4xl mx-auto px-8 text-center">
          <h2 className="text-4xl font-bold mb-4">Ready to see where you stand?</h2>
          <p className="text-gray-400 mb-8">Takes 30 seconds. No signup required.</p>
          <Link
            href="/scan"
            className="inline-block px-8 py-3 rounded-xl font-semibold transition-all duration-200 hover:opacity-90"
            style={{ backgroundColor: "#7c3aed", color: "#fff" }}
          >
            Analyze my resume
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center" style={{ borderColor: "#1e1e24" }}>
        <p className="text-xs text-gray-600">
          Built with FastAPI · sentence-transformers · Next.js · Tailwind
        </p>
      </footer>
    </main>
  );
}