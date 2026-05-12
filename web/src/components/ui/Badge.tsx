import React from 'react';
import { cn } from '@/lib/utils';

export const Badge = ({ className, children, variant = 'default' }: { className?: string; children: React.ReactNode, variant?: 'default' | 'success' | 'warning' | 'error' | 'outline' | 'neutral' }) => {
  const variants = {
    default: "bg-zinc-800 text-zinc-300",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
    error: "bg-red-500/10 text-red-400 border border-red-500/20",
    neutral: "bg-zinc-900/80 border border-zinc-800 text-zinc-400 shadow-xl",
    outline: "border border-zinc-800 text-zinc-400"
  };

  return (
    <span className={cn("inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-[10px] font-mono uppercase tracking-wider", variants[variant], className)}>
      {children}
    </span>
  );
};
