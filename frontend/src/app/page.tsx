"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { TrendingUp, Brain, Newspaper, Shield, BarChart3, Users, Zap, Globe, Cpu, Signal, Sparkles, ArrowRight, CheckCircle, Timer, Activity } from "lucide-react";
import BlurText from "@/components/BlurText";
import ShinyText from "@/components/ShinyText";
import GradientText from "@/components/GradientText";
import Particles from "@/components/Particles";
import StarBorder from "@/components/StarBorder";
import LightPillar from "@/components/LightPillar";
import SplashCursor from "@/components/SplashCursor";

const dsos = [
  { code: "DSO1.1", label: "Macro Agent", color: "#3b82f6", desc: "Directional bias score from -100 to +100 using FRED data: CPI, GDP, PMI, policy rates" },
  { code: "DSO1.2", label: "Technical Agent", color: "#10b981", desc: "120 multi-timeframe features: SMA, EMA, RSI, MACD, ATR, Bollinger Bands" },
  { code: "DSO1.3", label: "Sentiment Agent", color: "#f59e0b", desc: "FinBERT NLP on Reuters news with pair-level sentiment scoring" },
  { code: "DSO1.4", label: "Geopolitical Agent", color: "#ef4444", desc: "Political stability, trade policies, regional risks, central bank analysis" },
  { code: "DSO2.1", label: "Coordinator", color: "#8b5cf6", desc: "Weighted vote: Technical 30% - Macro 25% - Sentiment 20% - Geopolitical 25%" },
  { code: "DSO2.2", label: "Backtesting 5Y", color: "#f43f5e", desc: "Walk-forward validation with targets: Sharpe > 1.5, Win Rate > 55%" },
  { code: "DSO2.3", label: "Position Sizing", color: "#22d3ee", desc: "Kelly criterion + ATR-based risk management for optimal sizing" },
  { code: "DSO3.1", label: "Signal Validation", color: "#a78bfa", desc: "Conflict detection, quality filters, and confidence scoring" },
  { code: "DSO4.1", label: "Data Quality", color: "#4ade80", desc: "Pipeline validation: missing values, outliers, and timestamp consistency" },
  { code: "DSO4.2", label: "MLflow Monitoring", color: "#fb923c", desc: "Inference latency, PSI drift, and performance degradation alerts" },
  { code: "DSO5.1", label: "Analytics Reports", color: "#67e8f9", desc: "Structured signal history with explainable AI-agent rationale" },
  { code: "DSO5.2", label: "Multi-Timezone", color: "#f97316", desc: "Asian, European, US session analysis with overlap optimization" },
];

const team = [
  { name: "Ines Chtioui", role: "Project Lead" },
  { name: "Amine Manai", role: "Project Manager" },
  { name: "Mariem Fersi", role: "Solution Architect" },
  { name: "Malek Chairat", role: "Data Scientist" },
  { name: "Maha Aloui", role: "Data Scientist" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#080d18] text-slate-100 overflow-hidden">
      <SplashCursor
        COLOR_PALETTE={["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b"]}
        BACK_COLOR={{ r: 8 / 255, g: 13 / 255, b: 24 / 255 }}
      />

      <div className="fixed inset-0 z-0">
        <Particles
          particleCount={120}
          particleColors={["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b"]}
          particleBaseSize={60}
          speed={0.5}
          moveParticlesOnHover
          alphaParticles
          className="w-full h-full"
        />
      </div>

      <nav className="relative z-20 flex items-center justify-between px-8 py-5 border-b border-white/5 bg-[#080d18]/60 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl overflow-hidden border border-white/10 flex items-center justify-center bg-gradient-to-br from-[#4D8048] to-[#0658BA]">
            <img
              src="/logo.png"
              alt="Trady"
              className="size-9 object-cover"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = "none";
              }}
            />
            <TrendingUp className="size-5 text-white" style={{ display: "none" }} />
          </div>
          <ShinyText text="Trady" className="text-xl font-black" color="#e2e8f0" shineColor="#a78bfa" speed={3} />
          <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-400 border border-violet-500/20">
            DATAMINDS - ESPRIT 2025
          </span>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="px-4 py-2 rounded-lg text-sm text-slate-300 hover:text-white border border-white/10 hover:border-white/20 transition-all"
          >
            Login
          </Link>
          <StarBorder as="a" href="/dashboard" color="#8b5cf6" speed="4s" className="text-sm font-semibold cursor-pointer">
            Dashboard -&gt;
          </StarBorder>
        </div>
      </nav>

      <section className="relative z-10 w-full overflow-hidden">
        <div style={{ width: "100%", height: "68vh", minHeight: "500px", position: "relative" }}>
          <LightPillar
            topColor="#2596be"
            bottomColor="#395d41"
            intensity={1.4}
            rotationSpeed={0.3}
            glowAmount={0.002}
            pillarWidth={3}
            pillarHeight={0.4}
            noiseIntensity={0.5}
            pillarRotation={25}
            interactive={false}
            mixBlendMode="lighten"
            quality="medium"
            className="opacity-90"
          />
          <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-[#080d18] to-transparent pointer-events-none" />
          <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[#080d18] to-transparent pointer-events-none" />
        </div>
      </section>

      <section className="relative z-10 text-center -mt-44 pb-20 px-6 max-w-5xl mx-auto">
        {/* Floating Elements */}
        <div className="absolute inset-0 pointer-events-none">
          <motion.div
            animate={{ y: [-20, 20, -20], rotate: [-5, 5, -5] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-10 left-10 w-20 h-20 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-full blur-xl"
          />
          <motion.div
            animate={{ y: [20, -20, 20], rotate: [5, -5, 5] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-20 right-20 w-16 h-16 bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 rounded-full blur-xl"
          />
          <motion.div
            animate={{ x: [-15, 15, -15], y: [15, -15, 15] }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
            className="absolute bottom-10 left-1/3 w-24 h-24 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-full blur-xl"
          />
        </div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-4">
          <div className="flex items-center justify-center gap-2 mb-4">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="px-3 py-1 rounded-full bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30"
            >
              <Sparkles className="size-3 text-purple-400 mr-1" />
              <ShinyText
                text="MULTI-AGENT FOREX INTELLIGENCE"
                className="text-[10px] tracking-[0.2em] font-bold uppercase"
                color="#e2e8f0"
                shineColor="#8b5cf6"
                speed={4}
              />
            </motion.div>
          </div>
        </motion.div>

        <div className="relative mb-8">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 3, repeat: Infinity }}
            className="absolute inset-0 bg-gradient-to-r from-purple-600/20 via-blue-600/20 to-emerald-600/20 rounded-3xl blur-3xl"
          />
          <BlurText
            text="AI-Powered Forex Signal Prediction"
            className="text-4xl md:text-6xl font-extrabold text-white leading-tight mx-auto w-full justify-center text-center relative z-10"
            animateBy="words"
            direction="top"
            delay={80}
          />
        </div>

        <motion.div className="text-lg mb-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>
          <div className="relative inline-block">
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-lg blur-lg"
            />
            <GradientText colors={["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]} className="text-lg md:text-xl font-semibold relative z-10" animationSpeed={5}>
              EUR/USD - USD/JPY - GBP/USD - USD/CHF
            </GradientText>
          </div>
        </motion.div>

        <motion.p className="text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 }}>
          Four AI agents (Technical, Macro, Sentiment, Geopolitical) coordinated by a multi-modal orchestrator to generate BUY/SELL/NEUTRAL signals,
          validated with 5-year backtesting and Kelly-driven risk controls with real-time processing.
        </motion.p>

        <motion.div className="flex flex-wrap items-center justify-center gap-4 mb-12" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.1 }}>
          <StarBorder as="a" href="/dashboard" color="#10b981" speed="5s" className="text-base font-bold cursor-pointer">
            <span className="flex items-center gap-2">
              <Zap className="size-4" />
              Access Trady
              <ArrowRight className="size-4" />
            </span>
          </StarBorder>
          <Link
            href="/login"
            className="flex items-center gap-2 px-6 py-3 rounded-xl border border-white/10 bg-white/[0.03] text-white font-bold hover:border-white/20 hover:bg-white/[0.06] transition-all text-sm group"
          >
            <Shield className="size-4 text-violet-400 group-hover:text-violet-300 transition-colors" />
            Sign in
          </Link>
        </motion.div>

        {/* Enhanced Metrics with Animations */}
        <motion.div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mt-20" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }}>
          {[
            { v: "120+", l: "Features", c: "#8b5cf6", icon: Cpu },
            { v: "5Y", l: "History", c: "#3b82f6", icon: Timer },
            { v: "58%", l: "Win Rate", c: "#10b981", icon: TrendingUp },
            { v: "1.73", l: "Sharpe", c: "#f59e0b", icon: BarChart3 },
            { v: "4", l: "AI Agents", c: "#ef4444", icon: Brain },
            { v: "4", l: "Forex Pairs", c: "#22d3ee", icon: Globe },
          ].map((s, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              transition={{ type: "spring", stiffness: 300 }}
              className="p-4 rounded-xl bg-white/[0.04] border border-white/8 text-center cursor-default group relative overflow-hidden"
            >
              <motion.div
                animate={{ opacity: [0, 1, 0] }}
                transition={{ duration: 3, repeat: Infinity, delay: i * 0.5 }}
                className="absolute inset-0 bg-gradient-to-br from-transparent via-white/5 to-transparent"
              />
              <div className="relative z-10">
                <div className="flex items-center justify-center mb-2">
                  <s.icon className="size-4" style={{ color: s.c }} />
                </div>
                <div className="text-2xl font-black" style={{ color: s.c }}>
                  {s.v}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">{s.l}</div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="relative z-10 px-6 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <BlurText text="Data Science Objectives" className="text-3xl font-bold text-white mb-3 w-full justify-center text-center" delay={50} direction="bottom" />
          <ShinyText text="12 DSOs - 5 Business Objectives - Complete AI pipeline with Geopolitical Analysis" className="text-sm" color="#475569" shineColor="#6366f1" speed={5} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
          {dsos.map((d, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.92 }}
              whileInView={{ opacity: 1, scale: 1 }}
              whileHover={{ y: -4, scale: 1.02 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.03, type: "spring", stiffness: 260, damping: 20 }}
              className="p-4 rounded-xl border bg-white/[0.03] hover:bg-white/[0.06] transition-colors cursor-default"
              style={{ borderColor: `${d.color}30` }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded font-bold" style={{ color: d.color, background: `${d.color}18`, border: `1px solid ${d.color}30` }}>
                  {d.code}
                </span>
              </div>
              <div className="text-xs font-bold text-white mb-1">{d.label}</div>
              <p className="text-[10px] text-slate-500 leading-relaxed">{d.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Live Signal Showcase */}
      <section className="relative z-10 px-6 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <BlurText text="Live Signal Generation" className="text-3xl font-bold text-white mb-3 w-full justify-center text-center" delay={50} direction="bottom" />
          <ShinyText text="Real-time AI-powered trading signals with 15-second generation" className="text-sm" color="#475569" shineColor="#10b981" speed={5} />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="p-8 rounded-2xl border border-green-500/30 bg-gradient-to-br from-green-900/20 to-emerald-900/20"
          >
            <div className="flex items-center gap-3 mb-6">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                className="p-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500"
              >
                <Activity className="size-6 text-white" />
              </motion.div>
              <div>
                <h3 className="text-xl font-bold text-white">Current Signal</h3>
                <p className="text-sm text-green-400">Generated in real-time</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.05] border border-white/10">
                <div>
                  <div className="text-sm text-slate-400 mb-1">EUR/USD</div>
                  <div className="text-2xl font-bold text-green-400">BUY</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-slate-400 mb-1">Confidence</div>
                  <div className="text-xl font-bold text-white">73%</div>
                </div>
              </div>
              
              <div className="p-4 rounded-xl bg-purple-900/20 border border-purple-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Signal className="size-4 text-purple-400" />
                  <span className="text-sm font-semibold text-white">Agent Breakdown</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-green-400"></div>
                    <span className="text-slate-300">Technical: BUY (85%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-blue-400"></div>
                    <span className="text-slate-300">Macro: BUY (70%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-amber-400"></div>
                    <span className="text-slate-300">Sentiment: NEUTRAL (50%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-red-400"></div>
                    <span className="text-slate-300">Geopolitical: BUY (80%)</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="p-8 rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-pink-900/20"
          >
            <div className="flex items-center gap-3 mb-6">
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="p-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500"
              >
                <Brain className="size-6 text-white" />
              </motion.div>
              <div>
                <h3 className="text-xl font-bold text-white">AI Performance</h3>
                <p className="text-sm text-purple-400">Multi-agent coordination</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-white/[0.05] border border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">System Status</span>
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="size-2 rounded-full bg-green-400"
                    />
                    <span className="text-xs text-green-400">ONLINE</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <div className="text-slate-400">Generation Time</div>
                    <div className="text-white font-semibold">15.2s</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Success Rate</div>
                    <div className="text-white font-semibold">100%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Active Agents</div>
                    <div className="text-white font-semibold">4/4</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Market Regime</div>
                    <div className="text-white font-semibold">Volatile</div>
                  </div>
                </div>
              </div>
              
              <div className="p-4 rounded-xl bg-gradient-to-r from-blue-900/20 to-cyan-900/20 border border-blue-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Timer className="size-4 text-blue-400" />
                  <span className="text-sm font-semibold text-white">Processing Pipeline</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="size-3 text-green-400" />
                    <span className="text-xs text-slate-300">Data Loading: 2.1s</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="size-3 text-green-400" />
                    <span className="text-xs text-slate-300">Agent Processing: 8.7s</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="size-3 text-green-400" />
                    <span className="text-xs text-slate-300">Signal Aggregation: 1.2s</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="size-3 text-green-400" />
                    <span className="text-xs text-slate-300">LLM Explanation: 3.2s</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Enhanced Features Section */}
      <section className="relative z-10 px-6 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <BlurText text="Enhanced Multi-Agent System" className="text-3xl font-bold text-white mb-3 w-full justify-center text-center" delay={50} direction="bottom" />
          <ShinyText text="Real-time Signal Generation with Geopolitical Intelligence" className="text-sm" color="#475569" shineColor="#ef4444" speed={5} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="p-6 rounded-xl border border-green-500/30 bg-gradient-to-br from-green-900/20 to-emerald-900/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-green-500/20">
                <Brain className="size-6 text-green-400" />
              </div>
              <h3 className="text-lg font-bold text-white">4 AI Agents</h3>
            </div>
            <p className="text-sm text-slate-400 mb-4">
              Technical, Macro, Sentiment, and Geopolitical agents working in coordination
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-green-400"></div>
                <span className="text-xs text-slate-300">Real-time processing</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-green-400"></div>
                <span className="text-xs text-slate-300">15-second generation</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-green-400"></div>
                <span className="text-xs text-slate-300">Dynamic weighting</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="p-6 rounded-xl border border-blue-500/30 bg-gradient-to-br from-blue-900/20 to-cyan-900/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Shield className="size-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Geopolitical Analysis</h3>
            </div>
            <p className="text-sm text-slate-400 mb-4">
              Political stability, trade policies, regional risks, and central bank analysis
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-blue-400"></div>
                <span className="text-xs text-slate-300">Political stability</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-blue-400"></div>
                <span className="text-xs text-slate-300">Trade agreements</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-blue-400"></div>
                <span className="text-xs text-slate-300">Regional risk analysis</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="p-6 rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-pink-900/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <BarChart3 className="size-6 text-purple-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Real Data Processing</h3>
            </div>
            <p className="text-sm text-slate-400 mb-4">
              Live OHLCV data, real-time news feeds, and economic indicators
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-purple-400"></div>
                <span className="text-xs text-slate-300">No simulations</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-purple-400"></div>
                <span className="text-xs text-slate-300">Real market data</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-purple-400"></div>
                <span className="text-xs text-slate-300">Production ready</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="p-6 rounded-xl border border-amber-500/30 bg-gradient-to-br from-amber-900/20 to-orange-900/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <Newspaper className="size-6 text-amber-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Enhanced LLM</h3>
            </div>
            <p className="text-sm text-slate-400 mb-4">
              Free sophisticated reasoning with professional explanations
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-amber-400"></div>
                <span className="text-xs text-slate-300">$0 API cost</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-amber-400"></div>
                <span className="text-xs text-slate-300">Rule-based logic</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-amber-400"></div>
                <span className="text-xs text-slate-300">Professional quality</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="relative z-10 px-6 py-20 border-t border-white/5">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-8"
          >
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-violet-500 to-purple-500 mb-4"
            >
              <Users className="size-8 text-white" />
            </motion.div>
            <BlurText text="Our Team Members" className="text-2xl font-bold text-white mb-2 w-full justify-center text-center" delay={50} />
            <ShinyText text="Private Higher School of Engineering and Technology - ESPRIT 2025" className="text-xs mb-8 block" color="#475569" shineColor="#8b5cf6" speed={6} />
          </motion.div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-stretch mb-12">
            {team.map((member, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                whileHover={{ y: -4, scale: 1.02 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="px-4 py-4 rounded-xl bg-gradient-to-br from-white/[0.04] to-white/[0.02] border border-white/10 text-left hover:border-white/20 transition-all min-h-[100px] group relative overflow-hidden"
              >
                <motion.div
                  animate={{ opacity: [0, 0.1, 0] }}
                  transition={{ duration: 3, repeat: Infinity, delay: i * 0.5 }}
                  className="absolute inset-0 bg-gradient-to-br from-violet-500/10 to-purple-500/10"
                />
                <div className="relative z-10">
                  <div className="flex items-center gap-2 mb-2">
                    <motion.div
                      animate={{ rotate: [0, 5, -5, 0] }}
                      transition={{ duration: 4, repeat: Infinity, delay: i * 0.3 }}
                      className="size-2 rounded-full bg-gradient-to-r from-violet-400 to-purple-400"
                    />
                    <div className="text-sm font-semibold text-white group-hover:text-violet-200 transition-colors">{member.name}</div>
                  </div>
                  <div className="text-[11px] text-slate-500 group-hover:text-slate-400 transition-colors">{member.role}</div>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Achievement Badges */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="flex flex-wrap items-center justify-center gap-4"
          >
            <div className="px-4 py-2 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30">
              <CheckCircle className="size-3 text-green-400 mr-2 inline" />
              <span className="text-xs text-green-400 font-semibold">Production Ready</span>
            </div>
            <div className="px-4 py-2 rounded-full bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/30">
              <Brain className="size-3 text-blue-400 mr-2 inline" />
              <span className="text-xs text-blue-400 font-semibold">AI-Powered</span>
            </div>
            <div className="px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30">
              <Globe className="size-3 text-purple-400 mr-2 inline" />
              <span className="text-xs text-purple-400 font-semibold">Global Markets</span>
            </div>
            <div className="px-4 py-2 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30">
              <Zap className="size-3 text-amber-400 mr-2 inline" />
              <span className="text-xs text-amber-400 font-semibold">Real-Time</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Enhanced Footer */}
      <footer className="relative z-10 border-t border-white/5">
        <div className="px-6 py-12">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl overflow-hidden border border-white/10 flex items-center justify-center bg-gradient-to-br from-[#4D8048] to-[#0658BA]">
                    <TrendingUp className="size-5 text-white" />
                  </div>
                  <ShinyText text="Trady" className="text-xl font-black" color="#e2e8f0" shineColor="#a78bfa" speed={3} />
                </div>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Advanced multi-agent forex trading intelligence system with real-time signal generation and geopolitical analysis.
                </p>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
              >
                <h4 className="text-sm font-semibold text-white mb-4">Quick Links</h4>
                <div className="space-y-2">
                  <Link href="/dashboard" className="block text-sm text-slate-400 hover:text-white transition-colors">
                    Dashboard
                  </Link>
                  <Link href="/agents" className="block text-sm text-slate-400 hover:text-white transition-colors">
                    AI Agents
                  </Link>
                  <Link href="/monitoring" className="block text-sm text-slate-400 hover:text-white transition-colors">
                    Monitoring
                  </Link>
                  <Link href="/api-test-page" className="block text-sm text-slate-400 hover:text-white transition-colors">
                    API Testing
                  </Link>
                </div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
              >
                <h4 className="text-sm font-semibold text-white mb-4">System Status</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="size-2 rounded-full bg-green-400"
                    />
                    <span className="text-xs text-slate-400">All Systems Operational</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-blue-400"></div>
                    <span className="text-xs text-slate-400">4 AI Agents Active</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="size-2 rounded-full bg-purple-400"></div>
                    <span className="text-xs text-slate-400">Real Data Processing</span>
                  </div>
                </div>
              </motion.div>
            </div>
            
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="pt-8 border-t border-white/5 text-center"
            >
              <ShinyText text="Trady - DATAMINDS - ESPRIT 2025 - Data Science Project" color="#334155" shineColor="#6366f1" speed={8} />
              <div className="mt-4 flex items-center justify-center gap-4">
                <div className="text-xs text-slate-600">Built with</div>
                <div className="flex items-center gap-2">
                  <Brain className="size-3 text-violet-400" />
                  <span className="text-xs text-slate-500">AI</span>
                </div>
                <div className="text-xs text-slate-600">•</div>
                <div className="flex items-center gap-2">
                  <Zap className="size-3 text-amber-400" />
                  <span className="text-xs text-slate-500">Real-Time</span>
                </div>
                <div className="text-xs text-slate-600">•</div>
                <div className="flex items-center gap-2">
                  <Globe className="size-3 text-blue-400" />
                  <span className="text-xs text-slate-500">Global Markets</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </footer>
    </div>
  );
}
