"use client";

import { Navbar } from "@/components/landing/Navbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { ArchitectureTimeline } from "@/components/landing/ArchitectureTimeline";
import { PricingGrid } from "@/components/landing/PricingGrid";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-emerald-500/30 overflow-x-hidden">
      <Navbar />
      <HeroSection />
      <ArchitectureTimeline />
      <PricingGrid />
      <Footer />
    </div>
  );
}
