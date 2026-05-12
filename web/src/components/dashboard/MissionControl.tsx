"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Terminal as TerminalIcon, Shield, Activity, Play } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface MissionControlProps {
  repoPath: string;
  setRepoPath: (path: string) => void;
  isRunning: boolean;
  onLaunch: () => void;
}

export const MissionControl = ({ repoPath, setRepoPath, isRunning, onLaunch }: MissionControlProps) => {
  return (
    <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
      <Card className="p-6 group">
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        
        <div className="flex items-center gap-2 mb-8 px-2">
          <TerminalIcon className="w-4 h-4 text-emerald-400/80" />
          <h2 className="text-[11px] font-bold tracking-[0.3em] text-zinc-400 uppercase">Mission Control</h2>
        </div>

        <div className="space-y-5">
          <div className="group/input relative">
            <label className="block text-[9px] font-bold font-mono text-zinc-500 uppercase tracking-[0.2em] mb-2.5 ml-1">Target Repository</label>
            <input
              type="text"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              disabled={isRunning}
              placeholder="Paste the repo link..."
              className="w-full bg-zinc-950/80 border border-zinc-800/50 rounded-xl px-4 py-3.5 text-xs font-mono text-zinc-300 focus:outline-none focus:border-emerald-500/30 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder:text-zinc-700 disabled:opacity-50"
            />
          </div>

          <Button 
            onClick={onLaunch}
            disabled={isRunning || !repoPath.trim()}
            className="w-full py-4"
          >
            <div className="flex items-center justify-center gap-2">
              {isRunning ? (
                <Activity className="w-5 h-5 text-zinc-950 animate-pulse" />
              ) : (
                <Play className="w-5 h-5 text-zinc-950 fill-current" />
              )}
              <span className="text-sm font-bold tracking-[0.1em]">
                {isRunning ? "EXECUTING..." : "INITIALIZE PURPLE TEAM"}
              </span>
            </div>
          </Button>
        </div>
      </Card>
      
      <Card className="bg-zinc-900/30 p-6 flex-1 border-zinc-800/40">
         <h3 className="text-[10px] font-bold font-mono text-zinc-500 uppercase tracking-[0.3em] mb-6 flex items-center gap-2 px-1">
           <Shield className="w-3.5 h-3.5 text-emerald-500/60" /> Defense Matrix
         </h3>
         <div className="space-y-4 px-1">
            <div className="flex justify-between items-center group/item">
               <span className="text-[11px] font-medium text-zinc-500 group-hover/item:text-zinc-400 transition-colors">Threat Intel Sync</span>
               <Badge variant="success" className="px-2 py-0 h-4 min-w-[32px] justify-center">OK</Badge>
            </div>
            <div className="h-[1px] w-full bg-zinc-800/30" />
            <div className="flex justify-between items-center group/item">
               <span className="text-[11px] font-medium text-zinc-500 group-hover/item:text-zinc-400 transition-colors">Sandbox Containers</span>
               <Badge variant="outline" className="px-2 py-0 h-4 border-zinc-700 text-zinc-500">IDLE</Badge>
            </div>
            <div className="h-[1px] w-full bg-zinc-800/30" />
            <div className="flex justify-between items-center group/item">
               <span className="text-[11px] font-medium text-zinc-500 group-hover/item:text-zinc-400 transition-colors">LLM Node</span>
               <span className="text-[10px] font-bold font-mono text-emerald-400/80">CONNECTED</span>
            </div>
         </div>
      </Card>
    </div>
  );
};
