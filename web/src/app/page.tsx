"use client";

import { useState, useCallback, useRef, useEffect } from "react";

// ─── Types ──────────────────────────────────────────────────────────────
type PipelineStatus =
  | "Idle"
  | "Scanning"
  | "Extracting"
  | "Battling"
  | "Patching"
  | "Delivering"
  | "Success"
  | "Error";

interface ScanResult {
  status: string;
  detected_threat: string;
  file_fixed: string;
  vulnerable_code: string;
  secure_patch: string;
  git_branch: string;
}

const PIPELINE_STAGES = [
  {
    id: 1,
    label: "Vectorizing & Scanning Repo",
    description: "ChromaDB semantic search across codebase",
    icon: "🔍",
    status_key: "Scanning" as PipelineStatus,
  },
  {
    id: 2,
    label: "Surgically Isolating Function",
    description: "AST-based extraction of vulnerable target",
    icon: "🎯",
    status_key: "Extracting" as PipelineStatus,
  },
  {
    id: 3,
    label: "Go Arena: Red vs Blue Simulation",
    description: "Adversarial LangGraph sandbox execution",
    icon: "⚔️",
    status_key: "Battling" as PipelineStatus,
  },
  {
    id: 4,
    label: "AST Patch Injection",
    description: "Surgical code replacement via tree-sitter",
    icon: "💉",
    status_key: "Patching" as PipelineStatus,
  },
  {
    id: 5,
    label: "GitOps PR Delivery",
    description: "Branch creation, commit, and push",
    icon: "🚀",
    status_key: "Delivering" as PipelineStatus,
  },
];

// ─── Helpers ────────────────────────────────────────────────────────────
function getStageIndex(status: PipelineStatus): number {
  const idx = PIPELINE_STAGES.findIndex((s) => s.status_key === status);
  return idx === -1 ? -1 : idx;
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

// ─── Main Dashboard Component ──────────────────────────────────────────
export default function WarRoom() {
  const [repoPath, setRepoPath] = useState("test_repo");
  const [status, setStatus] = useState<PipelineStatus>("Idle");
  const [results, setResults] = useState<ScanResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [elapsedTime, setElapsedTime] = useState(0);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Timer effect
  useEffect(() => {
    if (
      status !== "Idle" &&
      status !== "Success" &&
      status !== "Error"
    ) {
      timerRef.current = setInterval(() => {
        setElapsedTime((t) => t + 100);
      }, 100);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [status]);

  // ── Launch Pipeline ───────────────────────────────────────────
  const handleLaunch = useCallback(async () => {
    // Reset state
    setResults(null);
    setErrorMessage("");
    setElapsedTime(0);

    // Abort any previous request
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    // Simulate pipeline stages with mock timeouts, then fire the real API
    const stageDurations = [1200, 900, 1800, 800, 700]; // ms per stage visual delay

    try {
      // Walk through stages visually
      for (let i = 0; i < PIPELINE_STAGES.length; i++) {
        setStatus(PIPELINE_STAGES[i].status_key);
        await sleep(stageDurations[i]);
      }

      // Fire the real API call
      const response = await fetch("http://localhost:8080/scan_and_fix_repo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_path: repoPath,
        }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(
          errData.detail || `API returned status ${response.status}`
        );
      }

      const data: ScanResult = await response.json();
      setResults(data);
      setStatus("Success");
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setStatus("Error");
      setErrorMessage(
        err instanceof Error ? err.message : "Unknown error occurred"
      );
    }
  }, [repoPath]);

  const isRunning =
    status !== "Idle" && status !== "Success" && status !== "Error";
  const currentStageIdx = getStageIndex(status);

  return (
    <div className="relative min-h-screen">
      {/* Scan line overlay when running */}
      {isRunning && <div className="scan-overlay" />}

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* ─── Header ─────────────────────────────────────── */}
        <Header status={status} elapsedTime={elapsedTime} />

        {/* ─── Control Panel ──────────────────────────────── */}
        <ControlPanel
          repoPath={repoPath}
          setRepoPath={setRepoPath}
          onLaunch={handleLaunch}
          isRunning={isRunning}
        />

        {/* ─── Pipeline Tracker ───────────────────────────── */}
        <PipelineTracker
          currentStageIdx={currentStageIdx}
          status={status}
        />

        {/* ─── Error Display ──────────────────────────────── */}
        {status === "Error" && (
          <div className="animate-fade-in mt-6">
            <div className="glow-card border-sentinel-red/30 p-5">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-2xl">🚨</span>
                <div>
                  <h3 className="text-sentinel-red font-mono text-sm font-bold uppercase tracking-wider">
                    Pipeline Failure
                  </h3>
                  <p className="mt-1 font-mono text-sm text-slate-400">
                    {errorMessage}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ─── Results Diff ───────────────────────────────── */}
        {status === "Success" && results && (
          <ResultsDiff results={results} />
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
//  HEADER
// ═══════════════════════════════════════════════════════════════════════
function Header({
  status,
  elapsedTime,
}: {
  status: PipelineStatus;
  elapsedTime: number;
}) {
  const dotClass =
    status === "Idle"
      ? "idle"
      : status === "Success"
        ? "success"
        : status === "Error"
          ? "error"
          : "running";

  return (
    <header className="mb-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="mb-1 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-sentinel-green/20 bg-sentinel-green/5 text-lg">
              🛡️
            </div>
            <div>
              <h1 className="font-mono text-xl font-black tracking-wider text-white sm:text-2xl">
                ZEROGATE /{" "}
                <span className="text-sentinel-green">SENTINEL-AI</span>
              </h1>
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.3em] text-slate-500">
                War Room — Purple Team Command Center
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Timer */}
          {elapsedTime > 0 && (
            <div className="font-mono text-xs text-slate-500">
              <span className="text-slate-400">T+</span>
              {(elapsedTime / 1000).toFixed(1)}s
            </div>
          )}
          {/* Status Badge */}
          <div className="flex items-center gap-2 rounded-full border border-slate-700/50 bg-slate-800/50 px-4 py-1.5">
            <span className={`status-dot ${dotClass}`} />
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-300">
              {status}
            </span>
          </div>
        </div>
      </div>

      {/* Separator */}
      <div className="mt-5 h-px w-full bg-gradient-to-r from-transparent via-sentinel-green/20 to-transparent" />
    </header>
  );
}

// ═══════════════════════════════════════════════════════════════════════
//  CONTROL PANEL
// ═══════════════════════════════════════════════════════════════════════
function ControlPanel({
  repoPath,
  setRepoPath,
  onLaunch,
  isRunning,
}: {
  repoPath: string;
  setRepoPath: (v: string) => void;
  onLaunch: () => void;
  isRunning: boolean;
}) {
  return (
    <div className="glow-card mb-8 p-6">
      <div className="mb-4 flex items-center gap-2">
        <span className="text-sentinel-cyan text-sm">◆</span>
        <h2 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
          Mission Control
        </h2>
      </div>

      <div className="grid gap-4 md:grid-cols-[1fr_auto]">
        {/* Repo Path */}
        <div>
          <label
            htmlFor="repo-path"
            className="mb-1.5 block font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500"
          >
            Target Repo / GitHub URL
          </label>
          <input
            id="repo-path"
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="test_repo or https://github.com/..."
            disabled={isRunning}
            className="input-sentinel w-full rounded-lg px-4 py-3 font-mono text-sm"
          />
        </div>

        {/* Launch Button */}
        <div className="flex items-end">
          <button
            id="launch-button"
            onClick={onLaunch}
            disabled={isRunning || !repoPath.trim()}
            className="btn-sentinel w-full rounded-lg px-6 py-3 font-mono text-sm md:w-auto"
          >
            {isRunning ? (
              <span className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="3"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                EXECUTING...
              </span>
            ) : (
              "⚡ INITIALIZE PURPLE TEAM"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
//  PIPELINE TRACKER
// ═══════════════════════════════════════════════════════════════════════
function PipelineTracker({
  currentStageIdx,
  status,
}: {
  currentStageIdx: number;
  status: PipelineStatus;
}) {
  return (
    <div className="glow-card p-6">
      <div className="mb-5 flex items-center gap-2">
        <span className="text-sentinel-amber text-sm">◆</span>
        <h2 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
          Live Pipeline Tracker
        </h2>
      </div>

      <div className="space-y-3">
        {PIPELINE_STAGES.map((stage, idx) => {
          let stageState: "idle" | "active" | "completed" | "error" = "idle";

          if (status === "Error") {
            if (idx < currentStageIdx) stageState = "completed";
            else if (idx === currentStageIdx) stageState = "error";
          } else if (status === "Success") {
            stageState = "completed";
          } else if (currentStageIdx >= 0) {
            if (idx < currentStageIdx) stageState = "completed";
            else if (idx === currentStageIdx) stageState = "active";
          }

          return (
            <div
              key={stage.id}
              className={`pipeline-step flex items-center gap-4 rounded-lg border p-4 ${
                stageState === "active"
                  ? "active border-sentinel-amber/30 bg-sentinel-amber/[0.03]"
                  : stageState === "completed"
                    ? "completed border-sentinel-green/20 bg-sentinel-green/[0.02]"
                    : stageState === "error"
                      ? "error border-sentinel-red/30 bg-sentinel-red/[0.03]"
                      : "border-slate-800/60 bg-slate-900/30"
              }`}
            >
              {/* Step Number / Check / Spinner */}
              <div
                className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg font-mono text-sm font-bold ${
                  stageState === "completed"
                    ? "bg-sentinel-green/10 text-sentinel-green"
                    : stageState === "active"
                      ? "bg-sentinel-amber/10 text-sentinel-amber"
                      : stageState === "error"
                        ? "bg-sentinel-red/10 text-sentinel-red"
                        : "bg-slate-800/50 text-slate-600"
                }`}
              >
                {stageState === "completed" ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : stageState === "active" ? (
                  <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : stageState === "error" ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <span>{stage.id}</span>
                )}
              </div>

              {/* Stage Info */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-base">{stage.icon}</span>
                  <span
                    className={`font-mono text-sm font-semibold ${
                      stageState === "completed"
                        ? "text-sentinel-green"
                        : stageState === "active"
                          ? "text-sentinel-amber"
                          : stageState === "error"
                            ? "text-sentinel-red"
                            : "text-slate-500"
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
                <p
                  className={`mt-0.5 font-mono text-[11px] ${
                    stageState === "idle"
                      ? "text-slate-600"
                      : "text-slate-500"
                  }`}
                >
                  {stage.description}
                </p>
              </div>

              {/* Status Tag */}
              <div className="flex-shrink-0">
                {stageState === "completed" && (
                  <span className="rounded-full bg-sentinel-green/10 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-sentinel-green">
                    Complete
                  </span>
                )}
                {stageState === "active" && (
                  <span className="animate-pulse rounded-full bg-sentinel-amber/10 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-sentinel-amber">
                    Running
                  </span>
                )}
                {stageState === "error" && (
                  <span className="rounded-full bg-sentinel-red/10 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-sentinel-red">
                    Failed
                  </span>
                )}
                {stageState === "idle" && (
                  <span className="rounded-full bg-slate-800/40 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-600">
                    Pending
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
//  RESULTS DIFF
// ═══════════════════════════════════════════════════════════════════════
function ResultsDiff({ results }: { results: ScanResult }) {
  return (
    <div className="animate-slide-up mt-8 space-y-6">
      {/* Detected Threat Badge */}
      {results.detected_threat && (
        <div className="glow-card flex items-center gap-4 border-sentinel-amber/30 bg-sentinel-amber/[0.03] p-5">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-sentinel-red/10 text-2xl">
            🚨
          </div>
          <div className="flex-1">
            <p className="font-mono text-[10px] font-bold uppercase tracking-[0.25em] text-sentinel-amber">
              Threat Neutralized
            </p>
            <h3 className="font-mono text-lg font-black uppercase tracking-wider text-white">
              {results.detected_threat}
            </h3>
          </div>
          <span className="animate-pulse rounded-full border border-sentinel-red/40 bg-sentinel-red/10 px-4 py-1.5 font-mono text-xs font-bold uppercase tracking-wider text-sentinel-red">
            Auto-Detected
          </span>
        </div>
      )}

      {/* Success Banner */}
      <div className="glow-card flex flex-col items-center gap-4 border-sentinel-green/20 p-6 text-center sm:flex-row sm:text-left">
        <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-sentinel-green/10 text-3xl">
          ✅
        </div>
        <div className="flex-1">
          <h3 className="font-mono text-lg font-black uppercase tracking-wider text-sentinel-green">
            Vulnerability Neutralized
          </h3>
          <p className="mt-1 font-mono text-xs text-slate-400">
            Patched file:{" "}
            <span className="text-slate-300">{results.file_fixed}</span>
          </p>
        </div>
        <div className="badge-pulse flex items-center gap-2 rounded-full border border-sentinel-green/30 bg-sentinel-green/10 px-5 py-2">
          <svg className="h-4 w-4 text-sentinel-green" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className="font-mono text-sm font-bold text-sentinel-green">
            {results.git_branch}
          </span>
        </div>
      </div>

      {/* Code Diff Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Vulnerable Code */}
        <div className="animate-fade-in">
          <div className="mb-3 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-sentinel-red" />
            <h4 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-sentinel-red">
              Vulnerable Code
            </h4>
            <span className="ml-auto rounded bg-sentinel-red/10 px-2 py-0.5 font-mono text-[10px] font-bold text-sentinel-red">
              BEFORE
            </span>
          </div>
          <div className="code-vulnerable code-block overflow-hidden rounded-lg p-5">
            {results.vulnerable_code}
          </div>
        </div>

        {/* Secure Patch */}
        <div className="animate-fade-in" style={{ animationDelay: "0.2s" }}>
          <div className="mb-3 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-sentinel-green" />
            <h4 className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-sentinel-green">
              Secure Patch
            </h4>
            <span className="ml-auto rounded bg-sentinel-green/10 px-2 py-0.5 font-mono text-[10px] font-bold text-sentinel-green">
              AFTER
            </span>
          </div>
          <div className="code-secure code-block overflow-hidden rounded-lg p-5">
            {results.secure_patch}
          </div>
        </div>
      </div>
    </div>
  );
}
