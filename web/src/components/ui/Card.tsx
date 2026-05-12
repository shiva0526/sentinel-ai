import React from 'react';
import { cn } from '@/lib/utils';

export const Card = ({ className, children, allowOverflow = false }: { className?: string; children: React.ReactNode; allowOverflow?: boolean }) => {
  return (
    <div className={cn(
      "bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl shadow-xl relative",
      !allowOverflow && "overflow-hidden",
      className
    )}>
      <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700/50 to-transparent" />
      {children}
    </div>
  );
};
