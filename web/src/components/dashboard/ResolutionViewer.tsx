"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { LockOpen, GitBranch } from 'lucide-react';
import { ScanResult } from '@/types';

interface ResolutionViewerProps {
  results: ScanResult;
}

export const ResolutionViewer = ({ results }: ResolutionViewerProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 40 }}
      className="mt-6"
    >
      <div className="bg-zinc-900/60 backdrop-blur-xl border border-emerald-500/30 rounded-2xl shadow-2xl overflow-hidden relative">
         <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-teal-400" />
         
         <div className="p-6 md:p-8">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-8">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                     <LockOpen className="w-5 h-5" />
                  </div>
                  <h3 className="text-xl font-bold text-white tracking-wide uppercase">Threat Neutralized</h3>
                </div>
                <div className="flex items-center gap-2 text-zinc-400 font-mono text-xs">
                  <span>Target: {results.file_fixed}</span>
                  <span className="text-zinc-600">|</span>
                  <span className="text-emerald-400 font-bold">{results.detected_threat}</span>
                </div>
              </div>
              
              {results.pr_url && (
                <a 
                  href={results.pr_url} 
                  target="_blank" 
                  rel="noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 rounded-lg transition-colors group cursor-pointer shadow-lg"
                >
                  <GitBranch className="w-4 h-4 text-emerald-400 group-hover:text-emerald-300" />
                  <span className="text-sm font-mono text-zinc-300 group-hover:text-white">View PR</span>
                </a>
              )}
            </div>

            <div className="grid lg:grid-cols-2 gap-4">
              {/* Before */}
              <div className="bg-red-950/20 border border-red-900/30 rounded-xl overflow-hidden flex flex-col">
                <div className="bg-red-950/50 border-b border-red-900/30 px-4 py-2 flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-red-400 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500" /> VULNERABLE
                  </span>
                </div>
                <div className="p-4 overflow-x-auto text-xs font-mono text-zinc-300 whitespace-pre flex-1">
                  {results.vulnerable_code}
                </div>
              </div>

              {/* After */}
              <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-xl overflow-hidden flex flex-col">
                <div className="bg-emerald-950/50 border-b border-emerald-900/30 px-4 py-2 flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-emerald-400 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" /> SECURED
                  </span>
                </div>
                <div className="p-4 overflow-x-auto text-xs font-mono text-zinc-300 whitespace-pre flex-1">
                  {results.secure_patch}
                </div>
              </div>
            </div>
         </div>
      </div>
    </motion.div>
  );
};
