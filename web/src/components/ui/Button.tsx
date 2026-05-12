import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = ({ className, variant = 'primary', size = 'md', children, ...props }: ButtonProps) => {
  const baseStyles = "inline-flex items-center justify-center rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap tracking-wide";
  
  const variants = {
    primary: "relative bg-gradient-to-r from-emerald-500 to-teal-400 text-zinc-950 shadow-lg shadow-emerald-500/10 hover:shadow-emerald-500/20 hover:from-emerald-400 hover:to-teal-300 active:scale-[0.98]",
    secondary: "bg-zinc-800 text-white hover:bg-zinc-700",
    outline: "border border-zinc-700 bg-zinc-900/50 text-zinc-300 hover:bg-zinc-800 hover:text-white",
    ghost: "text-zinc-400 hover:text-zinc-100"
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-8 py-4 text-sm"
  };

  if (variant === 'primary') {
    return (
      <button 
        className={cn(baseStyles, variants.primary, sizes[size], "border border-emerald-400/20 shadow-lg shadow-emerald-500/5 hover:shadow-emerald-500/10 active:scale-[0.98]", className)} 
        {...props}
      >
        {children}
      </button>
    );
  }

  return (
    <button 
      className={cn(baseStyles, variants[variant], sizes[size], className)} 
      {...props}
    >
      {children}
    </button>
  );
};
