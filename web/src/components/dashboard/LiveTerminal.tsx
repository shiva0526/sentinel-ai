"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Activity } from 'lucide-react';
import { PipelineStatus, PipelineStage } from '@/types';

interface LiveTerminalProps {
  status: PipelineStatus;
  currentStage: number;
  errorMessage: string;
  stages: PipelineStage[];
  isRunning: boolean;
}

export const LiveTerminal = ({ status, currentStage, errorMessage, stages, isRunning }: LiveTerminalProps) => {
  return (
    <div className="col-span-12 lg:col-span-8">
      <div className="bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl flex flex-col shadow-2xl h-full min-h-[400px] overflow-hidden">
        {/* macOS Style Header */}
        <div className="bg-zinc-950/50 border-b border-zinc-800 px-4 py-3 flex items-center gap-4">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex-1 text-center font-mono text-xs text-zinc-500">
            sentinel-ai@orchestrator ~ /pipeline
          </div>
        </div>

        {/* Terminal Content */}
        <div className="flex-1 p-6 flex flex-col font-mono text-sm space-y-6 overflow-y-auto">
          {status === "Idle" && (
            <div className="text-zinc-500 flex items-center h-full justify-center opacity-50">
              Awaiting initialization sequence...
            </div>
          )}
          
          {status === "Error" && (
            <div className="p-4 border border-red-500/30 bg-red-500/10 rounded-lg text-red-400">
              <span className="font-bold">FATAL ERROR:</span> {errorMessage}
            </div>
          )}

          {(isRunning || status === "Success") && stages.map((stage) => {
            const isActive = currentStage === stage.id && isRunning;
            const isCompleted = currentStage > stage.id || status === "Success";
            const Icon = stage.icon;
            
            if (currentStage < stage.id && status !== "Success") return null;

            return (
              <motion.div 
                key={stage.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`flex items-start gap-4 ${isCompleted ? 'text-zinc-300' : 'text-zinc-100'}`}
              >
                <div className={`mt-0.5 w-6 h-6 rounded flex items-center justify-center shrink-0
                  ${isCompleted ? 'text-emerald-400' : isActive ? 'text-amber-400' : 'text-zinc-600'}
                `}>
                   {isCompleted ? <CheckCircle className="w-4 h-4" /> : isActive ? <Activity className="w-4 h-4 animate-pulse" /> : <Icon className="w-4 h-4" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${isCompleted ? 'text-emerald-400' : isActive ? 'text-amber-400' : 'text-zinc-500'}`}>
                      [{stage.status_key.toUpperCase()}]
                    </span>
                    <span>{stage.label}</span>
                  </div>
                  <div className="text-xs text-zinc-500 mt-1">{stage.desc}</div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
