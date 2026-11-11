import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck, GitBranch, Sparkles, CheckCircle2, ArrowRight,
  TrendingUp, Lock, RefreshCw, BarChart2, Layers, Cpu
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 text-white selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/25 text-base">
              LF
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white">LeaveFlow</span>
              <span className="ml-2 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                EFCG Platform
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-xs font-semibold text-slate-300 hover:text-white transition px-3 py-1.5"
            >
              Sign In
            </Link>
            <Link
              to="/dashboard"
              className="text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition shadow-md shadow-blue-600/30 flex items-center gap-1.5"
            >
              <span>Explore Platform</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-blue-900/25 via-slate-900 to-slate-900 -z-10" />

        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Introducing Evidence-First Constraint Graph (EFCG) Architecture</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Workforce Requests.{' '}
            <span className="bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
              Intelligently Resolved.
            </span>
          </h1>

          <p className="text-base md:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            One intelligent enterprise platform for leave, expenses, approvals, and evidence-backed decisions.
            Every request is evaluated through an interconnected constraint graph where every decision is backed by verifiable proof.
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/dashboard"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-xl transition shadow-lg shadow-blue-500/30 flex items-center gap-2"
            >
              <span>Launch Live Portal</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/visualizer"
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl border border-slate-700 transition flex items-center gap-2"
            >
              <GitBranch className="w-4 h-4 text-blue-400" />
              <span>Interactive Graph Visualizer</span>
            </Link>
          </div>
        </div>

        {/* EFCG Visual Explainer Preview Card */}
        <div className="max-w-5xl mx-auto mt-16 p-4 rounded-3xl bg-slate-800/40 border border-slate-700/60 shadow-2xl backdrop-blur-sm">
          <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-rose-500" />
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="ml-2 font-mono text-xs text-slate-400">EFCG Decision Pipeline — Stage 1 to 6</span>
              </div>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-0.5 rounded-full uppercase">
                Zero Black-Box
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
                <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider block mb-1">Stage 1–3</span>
                <h4 className="text-sm font-bold text-white">Three-State Evaluation</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Evaluates independent constraints into <strong className="text-emerald-400">PASS</strong>, <strong className="text-rose-400">FAIL</strong>, or <strong className="text-amber-400">REVIEW</strong> with structured evidence records.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
                <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider block mb-1">Stage 4–5</span>
                <h4 className="text-sm font-bold text-white">Resource Reservation Ledger</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Atomic DB transactions hold balances without direct arithmetic. Commits on final approval, releases on rejection.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
                <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider block mb-1">Stage 6</span>
                <h4 className="text-sm font-bold text-white">Tamper-Evident Audit Chain</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Every state transition forms a SHA-256 block linked to previous hashes. Cryptographic proof of zero tampering.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="py-20 px-6 border-t border-slate-800 max-w-6xl mx-auto">
        <div className="text-center mb-16 space-y-3">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Built for Modern Enterprise Operations
          </h2>
          <p className="text-sm text-slate-400 max-w-lg mx-auto">
            Eliminate traditional workflow bottlenecks with explainable decision automation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: 'Interval Overlap Detection',
              desc: 'Prevents duplicate or conflicting leave bookings across employee schedules using exact date interval intersections.',
              icon: Layers,
            },
            {
              title: 'Split-Claim Heuristic',
              desc: 'Detects suspicious rolling-window transaction clustering designed to evade manager approval thresholds without false fraud claims.',
              icon: TrendingUp,
            },
            {
              title: 'SHA-256 Receipt Fingerprinting',
              desc: 'Identifies identical receipt attachments across claims using cryptographic SHA-256 digest comparisons.',
              icon: Lock,
            },
            {
              title: 'Zero Self-Approval Guarantee',
              desc: 'Enforces strict organizational authority routing. Never permits self-approval, auto-escalating to independent officers.',
              icon: ShieldCheck,
            },
            {
              title: 'Business Day & Holiday Calculator',
              desc: 'Excludes statutory corporate holidays and weekend intervals automatically for exact leave day deduction.',
              icon: RefreshCw,
            },
            {
              title: 'Continuous Anomaly Review Queue',
              desc: 'Identifies 12 enterprise anomaly classifications with severity grading, suggested remediation, and resolution workflows.',
              icon: Cpu,
            },
          ].map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition"
              >
                <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-10 px-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white">LeaveFlow</span>
            <span>— Evidence-First Leave & Expense Intelligence Platform</span>
          </div>
          <div>Tagline: "Every Request. Every Decision. Every Reason."</div>
        </div>
      </footer>
    </div>
  );
};
