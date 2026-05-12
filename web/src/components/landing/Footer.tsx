import React from 'react';
import Link from 'next/link';
import { Shield, GitBranch } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="border-t border-zinc-900 bg-zinc-950/80 py-12 px-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2 opacity-80">
          <Shield className="w-5 h-5 text-emerald-500" />
          <span className="text-sm font-bold tracking-wider text-zinc-300 uppercase">SENTINEL-AI</span>
        </div>
        
        <div className="flex items-center gap-6 text-sm text-zinc-500">
          <Link href="/dashboard" className="hover:text-zinc-300 transition-colors">Terms of Service</Link>
          <Link href="/dashboard" className="hover:text-zinc-300 transition-colors">Privacy Policy</Link>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-zinc-300 transition-colors flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            GitHub
          </a>
        </div>
        
        <div className="text-sm text-zinc-600">
          &copy; {new Date().getFullYear()} SentinelAI Security. All rights reserved.
        </div>
      </div>
    </footer>
  );
};
