"use client";

import { useState, useCallback, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { Shield, Search, Crosshair, Activity, Wrench, Rocket } from "lucide-react";
import { PipelineStatus, ScanResult, PipelineStage } from "@/types";
import { MissionControl } from "@/components/dashboard/MissionControl";
import { LiveTerminal } from "@/components/dashboard/LiveTerminal";
import { ResolutionViewer } from "@/components/dashboard/ResolutionViewer";
import { Badge } from "@/components/ui/Badge";

const PIPELINE_STAGES: PipelineStage[] = [
  { id: 1, label: "Vectorizing & Scanning Repo", desc: "ChromaDB semantic search across codebase", status_key: "Scanning", icon: Search },
  { id: 2, label: "Surgically Isolating Function", desc: "AST-based extraction of vulnerable target", status_key: "Extracting", icon: Crosshair },
  { id: 3, label: "Go Arena: Red vs Blue Simulation", desc: "Adversarial LangGraph sandbox execution", status_key: "Battling", icon: Activity },
  { id: 4, label: "AST Patch Injection", desc: "Surgical code replacement via tree-sitter", status_key: "Patching", icon: Wrench },
  { id: 5, label: "GitOps PR Delivery", desc: "Branch creation, commit, and push", status_key: "Delivering", icon: Rocket },
];

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export default function WarRoom() {
  const [repoPath, setRepoPath] = useState("");
  const [status, setStatus] = useState<PipelineStatus>("Idle");
  const [results, setResults] = useState<ScanResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [currentStage, setCurrentStage] = useState(0);

  const abortRef = useRef<AbortController | null>(null);

  const handleLaunch = useCallback(async () => {
    setResults(null);
    setErrorMessage("");
    setCurrentStage(0);

    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    const stageDurations = [1200, 900, 1800, 800, 700];

    try {
      for (let i = 0; i < PIPELINE_STAGES.length; i++) {
        setStatus(PIPELINE_STAGES[i].status_key as PipelineStatus);
        setCurrentStage(i + 1);
        await sleep(stageDurations[i]);
      }

      const response = await fetch("http://localhost:8080/scan_and_fix_repo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `API returned status ${response.status}`);
      }

      const data: ScanResult = await response.json();
      setResults(data);
      setStatus("Success");
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setStatus("Error");
      setErrorMessage(err instanceof Error ? err.message : "Unknown error occurred");
    }
  }, [repoPath]);

  const isRunning = status !== "Idle" && status !== "Success" && status !== "Error";

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 relative overflow-hidden font-sans selection:bg-emerald-500/30">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900 via-zinc-950 to-zinc-950 opacity-80" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

      <div className="max-w-7xl mx-auto px-4 py-8 lg:py-12 relative z-10">
        <div className="grid grid-cols-12 gap-6">
          
          {/* Header */}
          <div className="col-span-12 flex flex-col md:flex-row items-start md:items-center justify-between mb-4 gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl shadow-[0_0_20px_rgba(16,185,129,0.2)]">
                <Shield className="w-8 h-8 text-emerald-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-widest uppercase flex items-center gap-2 text-zinc-100">
                  SENTINEL-AI
                </h1>
                <p className="text-xs text-zinc-500 tracking-[0.2em] uppercase font-mono mt-1">
                  DevSecOps Command Center
                </p>
              </div>
            </div>
            
            <Badge variant="neutral" className="px-3 py-1.5">
               <Activity className="w-3 h-3 text-emerald-500" />
               SYSTEM ONLINE
            </Badge>
          </div>

          <MissionControl 
            repoPath={repoPath} 
            setRepoPath={setRepoPath} 
            isRunning={isRunning} 
            onLaunch={handleLaunch} 
          />

          <LiveTerminal 
            status={status} 
            currentStage={currentStage} 
            errorMessage={errorMessage} 
            stages={PIPELINE_STAGES}
            isRunning={isRunning}
          />
        </div>

        <AnimatePresence>
          {status === "Success" && results && (
            <ResolutionViewer results={results} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
