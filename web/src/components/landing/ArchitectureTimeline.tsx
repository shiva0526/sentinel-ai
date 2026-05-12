"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Search, Server, GitBranch } from 'lucide-react';
import { Card } from '@/components/ui/Card';

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export const ArchitectureTimeline = () => {
  return (
    <section id="architecture" className="py-24 px-4 bg-zinc-950 relative border-t border-zinc-900">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">How It Works</h2>
          <p className="text-zinc-400 max-w-2xl mx-auto">Our tri-phase autonomous remediation pipeline.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 relative">
          <div className="hidden md:block absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-zinc-800 to-transparent -translate-y-1/2" />

          {/* Step 1 */}
          <motion.div {...fadeIn}>
            <Card className="p-8 hover:bg-zinc-900/80 transition-colors">
              <div className="w-12 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center mb-6 shadow-xl relative z-10 mx-auto md:mx-0">
                <Search className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3 text-center md:text-left">1. Semantic Detection</h3>
              <p className="text-sm text-zinc-400 text-center md:text-left leading-relaxed">
                Ingests your entire repository into a ChromaDB vector store. Performs deep semantic scanning to identify logical flaws and CVEs with surgical precision.
              </p>
            </Card>
          </motion.div>

          {/* Step 2 */}
          <motion.div {...fadeIn} transition={{ duration: 0.6, delay: 0.2 }}>
            <Card className="p-8 hover:bg-zinc-900/80 transition-colors">
              <div className="w-12 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center mb-6 shadow-xl relative z-10 mx-auto md:mx-0">
                <Server className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3 text-center md:text-left">2. Adversarial Sandbox</h3>
              <p className="text-sm text-zinc-400 text-center md:text-left leading-relaxed">
                A LangGraph agent dynamically generates a patch, while a Red Team agent actively attempts to exploit it inside a secure Docker container. Only verified patches survive.
              </p>
            </Card>
          </motion.div>

          {/* Step 3 */}
          <motion.div {...fadeIn} transition={{ duration: 0.6, delay: 0.4 }}>
            <Card className="p-8 hover:bg-zinc-900/80 transition-colors">
              <div className="w-12 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center mb-6 shadow-xl relative z-10 mx-auto md:mx-0">
                <GitBranch className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3 text-center md:text-left">3. GitOps Delivery</h3>
              <p className="text-sm text-zinc-400 text-center md:text-left leading-relaxed">
                Once validated, the patch is cleanly applied to the AST via tree-sitter. A new branch is pushed and an automated Pull Request is raised for your review.
              </p>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
