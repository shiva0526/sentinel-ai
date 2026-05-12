"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export const PricingGrid = () => {
  return (
    <section id="pricing" className="py-24 px-4 bg-zinc-950 relative border-t border-zinc-900">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-emerald-500/5 rounded-[100%] blur-[100px] pointer-events-none" />
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Transparent Pricing</h2>
          <p className="text-zinc-400 max-w-2xl mx-auto">Scale your DevSecOps autonomously.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 items-stretch max-w-5xl mx-auto">
          {/* Card 1 */}
          <motion.div {...fadeIn} className="flex">
            <Card className="p-8 bg-zinc-900/30 flex flex-col w-full">
              <h3 className="text-lg font-medium text-white mb-2">Scout</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold text-white">₹0</span>
                <span className="text-sm text-zinc-500">/mo</span>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> 5 Scans per month</li>
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> Public Repositories</li>
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> Standard Arena Sandbox</li>
              </ul>
              <div className="mt-auto">
                <Link href="/dashboard" className="block">
                  <Button variant="secondary" className="w-full py-3">Start Free</Button>
                </Link>
              </div>
            </Card>
          </motion.div>

          {/* Card 2 - Highlighted */}
          <motion.div {...fadeIn} transition={{ duration: 0.6, delay: 0.2 }} className="relative transform md:-translate-y-4 flex">
            <Card allowOverflow className="p-8 bg-zinc-900/80 border-emerald-500/50 shadow-[0_0_40px_rgba(16,185,129,0.15)] flex flex-col w-full">
              <div className="absolute top-0 inset-x-0 flex justify-center -translate-y-1/2">
                <span className="bg-gradient-to-r from-emerald-500 to-teal-400 text-zinc-950 text-xs font-bold px-3 py-1 rounded-full tracking-wide uppercase">
                  Most Popular
                </span>
              </div>
              <h3 className="text-lg font-medium text-white mb-2">Sentinel Pro</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold text-white">₹2,499</span>
                <span className="text-sm text-zinc-500">/mo</span>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3 text-sm text-zinc-300"><Check className="w-4 h-4 text-emerald-400" /> Unlimited Scans</li>
                <li className="flex items-center gap-3 text-sm text-zinc-300"><Check className="w-4 h-4 text-emerald-400" /> Private Repositories</li>
                <li className="flex items-center gap-3 text-sm text-zinc-300"><Check className="w-4 h-4 text-emerald-400" /> Priority Arena Resources</li>
                <li className="flex items-center gap-3 text-sm text-zinc-300"><Check className="w-4 h-4 text-emerald-400" /> Automated Pull Requests</li>
              </ul>
              <div className="mt-auto">
                <Link href="/dashboard" className="block">
                  <Button size="md" className="w-full py-3">Upgrade to Pro</Button>
                </Link>
              </div>
            </Card>
          </motion.div>

          {/* Card 3 */}
          <motion.div {...fadeIn} transition={{ duration: 0.6, delay: 0.4 }} className="flex">
            <Card className="p-8 bg-zinc-900/30 flex flex-col w-full">
              <h3 className="text-lg font-medium text-white mb-2">Enterprise</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold text-white">Custom</span>
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> Dedicated Docker Nodes</li>
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> SOC2 Compliance Rulesets</li>
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> 24/7 Dedicated Support</li>
                <li className="flex items-center gap-3 text-sm text-zinc-400"><Check className="w-4 h-4 text-emerald-400" /> Custom LLM Integration</li>
              </ul>
              <div className="mt-auto">
                <Link href="/dashboard" className="block">
                  <Button variant="secondary" className="w-full py-3">Contact Sales</Button>
                </Link>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
