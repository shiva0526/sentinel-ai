import React from 'react';
import Link from 'next/link';
import { Shield } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const Navbar = () => {
  return (
    <nav className="fixed top-0 w-full z-50 bg-zinc-950/60 backdrop-blur-xl border-b border-zinc-800/50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500 blur-md opacity-40"></div>
            <Shield className="relative w-6 h-6 text-emerald-400" />
          </div>
          <span className="font-bold tracking-widest text-sm uppercase text-zinc-100">SENTINEL-AI</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
          <Link href="#features" className="hover:text-zinc-100 transition-colors">Features</Link>
          <Link href="#architecture" className="hover:text-zinc-100 transition-colors">Architecture</Link>
          <Link href="#pricing" className="hover:text-zinc-100 transition-colors">Pricing</Link>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors hidden md:block">Login</Link>
          <Link href="/dashboard">
            <Button size="md">Get Started</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
};
