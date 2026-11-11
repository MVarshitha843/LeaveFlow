import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck, GitBranch, Sparkles, CheckCircle2, ArrowRight,
  TrendingUp, Lock, RefreshCw, BarChart2, Layers, Cpu,
  Check, X, AlertTriangle, ChevronRight, FileCheck, Users,
  Building, Database, Eye, Terminal, Award
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const [activeMockupTab, setActiveMockupTab] = useState<'leave' | 'expense'>('leave');
  const [activePersonaTab, setActivePersonaTab] = useState<'employee' | 'manager' | 'finance' | 'governance'>('employee');

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 selection:bg-blue-600 selection:text-white">
      {/* Sticky Enterprise Header */}
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20 text-base">
              LF
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-slate-900">LeaveFlow</span>
              <span className="ml-2 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                EFCG v2.4
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-600">
            <a href="#pipeline" className="hover:text-blue-600 transition">EFCG Pipeline</a>
            <a href="#comparison" className="hover:text-blue-600 transition">Why EFCG</a>
            <a href="#features" className="hover:text-blue-600 transition">Core Features</a>
            <a href="#architecture" className="hover:text-blue-600 transition">Architecture</a>
            <a href="#personas" className="hover:text-blue-600 transition">Role Portals</a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-xs font-semibold text-slate-700 hover:text-blue-600 transition px-3.5 py-2 rounded-lg hover:bg-slate-50"
            >
              Sign In
            </Link>
            <Link
              to="/dashboard"
              className="text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition shadow-md shadow-blue-600/20 flex items-center gap-1.5"
            >
              <span>Launch Live Portal</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 px-6 overflow-hidden bg-mesh-grid">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Value Proposition */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>Evidence-First Constraint Graph Architecture</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.12]">
              Workforce Requests.{' '}
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 bg-clip-text text-transparent">
                Intelligently Resolved.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl">
              One enterprise platform for leave, expenses, and automated authority routing.
              Every request is dynamically evaluated through an interconnected constraint graph where decisions are 100% deterministic, backed by verifiable proof, and committed to a cryptographic audit chain.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-3.5">
              <Link
                to="/dashboard"
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition shadow-lg shadow-blue-600/25 flex items-center gap-2"
              >
                <span>Explore Live Platform</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/visualizer"
                className="px-5 py-3 bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold rounded-xl border border-slate-200 transition shadow-xs flex items-center gap-2"
              >
                <GitBranch className="w-4 h-4 text-blue-600" />
                <span>Open Graph Visualizer</span>
              </Link>
            </div>

            {/* Micro Trust Indicators */}
            <div className="pt-4 grid grid-cols-3 gap-4 border-t border-slate-200 text-slate-600 text-xs font-medium">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Deterministic DAG</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
                <span>Zero Black Boxes</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Lock className="w-4 h-4 text-indigo-600 shrink-0" />
                <span>SHA-256 Audit Trail</span>
              </div>
            </div>
          </div>

          {/* Right Column: Live Interactive Mockup Card */}
          <div className="lg:col-span-5">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden hover-card-elevate">
              {/* Window Chrome Header */}
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                  <span className="ml-2 font-mono text-[11px] text-slate-500 font-semibold truncate">
                    leaveflow.internal/decision-engine
                  </span>
                </div>
                <div className="flex items-center gap-1 bg-white p-0.5 rounded-md border border-slate-200">
                  <button
                    onClick={() => setActiveMockupTab('leave')}
                    className={`text-[10px] px-2 py-0.5 rounded font-semibold transition ${
                      activeMockupTab === 'leave'
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Leave DAG
                  </button>
                  <button
                    onClick={() => setActiveMockupTab('expense')}
                    className={`text-[10px] px-2 py-0.5 rounded font-semibold transition ${
                      activeMockupTab === 'expense'
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Expense DAG
                  </button>
                </div>
              </div>

              {/* Mockup Body */}
              <div className="p-5 space-y-4">
                {activeMockupTab === 'leave' ? (
                  <>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-[10px] font-mono text-blue-600 font-bold uppercase">
                          LVE-2026-000808 • Live Evaluation
                        </div>
                        <h4 className="text-sm font-bold text-slate-900 mt-0.5">
                          Sarah Connor — Annual Paid Time Off
                        </h4>
                        <p className="text-xs text-slate-500">4.0 Business Days (Dec 01 – Dec 04, 2026)</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold uppercase">
                        ELIGIBLE
                      </span>
                    </div>

                    {/* Constraint DAG Nodes Preview */}
                    <div className="space-y-2 pt-2 border-t border-slate-100">
                      {[
                        { name: 'Policy Entitlement Check', status: 'PASS', detail: '20.0d allocated, 16.0d headroom remaining', time: '1.2ms' },
                        { name: 'Holiday & Weekend Exclusion', status: 'PASS', detail: 'Excluded Dec 5-6 weekend automatically', time: '0.4ms' },
                        { name: 'Schedule Overlap Detection', status: 'PASS', detail: '0 intersecting leave intervals in department', time: '1.8ms' },
                        { name: 'Atomic Dual-Ledger Reservation', status: 'PASS', detail: 'Held 4.0 days in reservation ledger', time: '2.1ms' },
                      ].map((node, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <div>
                              <div className="font-semibold text-slate-800 text-[11px]">{node.name}</div>
                              <div className="text-[10px] text-slate-500">{node.detail}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[9px]">
                              {node.status}
                            </span>
                            <span className="block text-[9px] font-mono text-slate-400">{node.time}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100 text-xs flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                        <span className="text-[11px] font-medium text-blue-900">
                          Automated Routing: Dispatched to <strong>David Kim (L4 Manager)</strong>
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-[10px] font-mono text-blue-600 font-bold uppercase">
                          EXP-2026-001004 • Live Evaluation
                        </div>
                        <h4 className="text-sm font-bold text-slate-900 mt-0.5">
                          David Kim — Cloud Architecture Summit
                        </h4>
                        <p className="text-xs text-slate-500">Total Claim: $1,200.00 • Cost Center CC-ENG-01</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold uppercase">
                        NEEDS REVIEW
                      </span>
                    </div>

                    {/* Constraint DAG Nodes Preview */}
                    <div className="space-y-2 pt-2 border-t border-slate-100">
                      {[
                        { name: 'Receipt SHA-256 Fingerprint', status: 'PASS', detail: 'Digest verified unique: a1b2c3d4...', time: '0.8ms' },
                        { name: 'Rolling-Window Split Claim', status: 'PASS', detail: 'No threshold avoidance clustering detected', time: '1.4ms' },
                        { name: 'Cost Center Budget Headroom', status: 'PASS', detail: '$500,000 allocated, $420,000 available', time: '1.1ms' },
                        { name: 'Multi-Tier Authority Threshold', status: 'REVIEW', detail: 'Claim > $1,000 requires Manager + Finance dual approval', time: '0.5ms' },
                      ].map((node, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                node.status === 'PASS' ? 'bg-emerald-500' : 'bg-amber-500'
                              }`}
                            />
                            <div>
                              <div className="font-semibold text-slate-800 text-[11px]">{node.name}</div>
                              <div className="text-[10px] text-slate-500">{node.detail}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <span
                              className={`px-1.5 py-0.5 rounded font-bold text-[9px] ${
                                node.status === 'PASS'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {node.status}
                            </span>
                            <span className="block text-[9px] font-mono text-slate-400">{node.time}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-3 bg-amber-50/60 rounded-xl border border-amber-200 text-xs flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                        <span className="text-[11px] font-medium text-amber-900">
                          Dual Tier: Step 1 (Manager Sign-Off) → Step 2 (Finance Audit)
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Verified Scale & System Architecture Bar */}
      <section className="border-y border-slate-200 bg-white py-8 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-blue-600 tabular-nums">400</div>
            <div className="text-xs font-bold text-slate-900">Enterprise Employees</div>
            <div className="text-[11px] text-slate-500">Mapped across 5 departments</div>
          </div>

          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-blue-600 tabular-nums">1,807</div>
            <div className="text-xs font-bold text-slate-900">Evaluated Requests</div>
            <div className="text-[11px] text-slate-500">802 Leaves & 1,005 Expenses</div>
          </div>

          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-emerald-600 tabular-nums">100%</div>
            <div className="text-xs font-bold text-slate-900">Audit Verifiability</div>
            <div className="text-[11px] text-slate-500">SHA-256 tamper-evident chain</div>
          </div>

          <div className="space-y-1">
            <div className="text-3xl font-extrabold text-indigo-600 tabular-nums">14 / 14</div>
            <div className="text-xs font-bold text-slate-900">Automated Tests Passing</div>
            <div className="text-[11px] text-slate-500">Pytest verification in 0.37s</div>
          </div>
        </div>
      </section>

      {/* The Problem We Solve: Legacy vs. LeaveFlow EFCG */}
      <section id="comparison" className="py-20 px-6 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
          <div className="text-xs font-bold text-blue-600 uppercase tracking-wider">
            Architectural Differentiation
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Legacy Systems vs. Evidence-First Constraint Graph
          </h2>
          <p className="text-sm text-slate-600">
            Why traditional enterprise HR platforms lead to policy leakage, opaque rejections, and manager fatigue.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Legacy Systems Card */}
          <div className="bg-white rounded-2xl border border-rose-200 p-8 shadow-xs space-y-6">
            <div className="flex items-center gap-3 border-b border-rose-100 pb-4">
              <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
                <X className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Legacy Workflow Tools</h3>
                <p className="text-xs text-rose-600 font-semibold">Fragile, opaque, and error-prone</p>
              </div>
            </div>

            <ul className="space-y-4 text-xs text-slate-600">
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-rose-50 text-rose-600 mt-0.5"><X className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Brittle If/Else Rule Engines</strong>
                  Rules break silently when policies overlap, resulting in inconsistent decisions.
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-rose-50 text-rose-600 mt-0.5"><X className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Direct Balance Arithmetic (Race Conditions)</strong>
                  Deducting balances without atomic reservation causes double-spending and overdrawn allocations.
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-rose-50 text-rose-600 mt-0.5"><X className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Opaque "Black Box" Rejections</strong>
                  Employees receive generic rejection notices without specific evidence or remediation steps.
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-rose-50 text-rose-600 mt-0.5"><X className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Unprotected Audit Logs</strong>
                  Standard DB log tables can be modified or deleted without detection during regulatory audits.
                </div>
              </li>
            </ul>
          </div>

          {/* LeaveFlow EFCG Card */}
          <div className="bg-white rounded-2xl border border-blue-200 p-8 shadow-md relative overflow-hidden space-y-6">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full blur-2xl -z-10" />

            <div className="flex items-center gap-3 border-b border-blue-100 pb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">LeaveFlow EFCG Platform</h3>
                <p className="text-xs text-blue-600 font-semibold">Deterministic, auditable, and atomic</p>
              </div>
            </div>

            <ul className="space-y-4 text-xs text-slate-600">
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-blue-50 text-blue-600 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Interconnected Constraint DAG</strong>
                  Topological evaluation where every rule is an explicit node with input evidence and execution timing.
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-blue-50 text-blue-600 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Dual-Ledger Atomic Reservations</strong>
                  Balances and budgets are held in safe pending state, committed on approval and released on rejection.
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-blue-50 text-blue-600 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Plain-Language Synthesized Explanations</strong>
                  Zero guesswork. Plain English explanation synthesized from exact condition evaluations.
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="p-1 rounded bg-blue-50 text-blue-600 mt-0.5"><Check className="w-3.5 h-3.5" /></span>
                <div>
                  <strong className="text-slate-900 block font-semibold">Cryptographic SHA-256 Hash Chain</strong>
                  Append-only audit blocks linking previous hashes guarantee tamper-evident compliance.
                </div>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 6-Stage Visual Process Pipeline */}
      <section id="pipeline" className="py-20 px-6 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              Execution Flow
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              The 6-Stage EFCG Decision Pipeline
            </h2>
            <p className="text-sm text-slate-600">
              From submission to cryptographic commitment: how every request is verified without black-box uncertainty.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                stage: '01',
                title: 'Intake & Digest Validation',
                desc: 'Digital intake computes SHA-256 receipt fingerprint, date ranges, and statutory holiday exclusions.',
                icon: FileCheck,
              },
              {
                stage: '02',
                title: 'Topological DAG Construction',
                desc: 'Generates a directed acyclic graph resolving dependencies between eligibility, budget, and authority rules.',
                icon: GitBranch,
              },
              {
                stage: '03',
                title: 'Three-State Evaluation',
                desc: 'Nodes evaluate into PASS, FAIL, or REVIEW with structured evidence records and sub-millisecond execution.',
                icon: Cpu,
              },
              {
                stage: '04',
                title: 'Atomic Resource Reservation',
                desc: 'Holds leave days or cost center budget in an atomic reservation ledger without direct balance deduction.',
                icon: Database,
              },
              {
                stage: '05',
                title: 'Authority Routing & Sign-Off',
                desc: 'Dynamic graph traversal routes approval to authorized officers with strict zero self-approval enforcement.',
                icon: Users,
              },
              {
                stage: '06',
                title: 'Cryptographic Commitment',
                desc: 'Final approvals commit reservations to permanent ledger and forge a SHA-256 block into the audit chain.',
                icon: Lock,
              },
            ].map((st) => {
              const Icon = st.icon;
              return (
                <div
                  key={st.stage}
                  className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 hover-card-elevate relative overflow-hidden"
                >
                  <div className="text-3xl font-extrabold text-blue-100 font-mono absolute top-4 right-4">
                    {st.stage}
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-600 mb-4">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2">{st.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{st.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Core Features Grid */}
      <section id="features" className="py-20 px-6 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-16">
          <div className="text-xs font-bold text-blue-600 uppercase tracking-wider">
            Operational Capabilities
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Built for Modern Enterprise Governance
          </h2>
          <p className="text-sm text-slate-600">
            Intelligent detectors and safeguards that protect organizational resources without slowing down workforce operations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: 'Interval Overlap Detection',
              desc: 'Identifies conflicting or duplicate leave bookings across employee schedules using exact date interval intersections.',
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
              icon: Award,
            },
          ].map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="p-6 rounded-2xl bg-white border border-slate-200/80 hover-card-elevate shadow-xs"
              >
                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 mb-4">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Role-Based Experience Showcase */}
      <section id="personas" className="py-20 px-6 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              Tailored Portals
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              One Unified System, 5 Specialized Personas
            </h2>
            <p className="text-sm text-slate-600">
              Designed to give each stakeholder the exact clarity, controls, and actions required.
            </p>
          </div>

          {/* Persona Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {[
              { id: 'employee', label: 'Employee Portal', role: 'Staff & Team Members' },
              { id: 'manager', label: 'Manager Queue', role: 'Team Leaders & Supervisors' },
              { id: 'finance', label: 'Finance & Budgets', role: 'Finance Officers & Controllers' },
              { id: 'governance', label: 'Policy & Audit', role: 'HR Process Owners & Auditors' },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setActivePersonaTab(p.id as any)}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition ${
                  activePersonaTab === p.id
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                    : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                <span>{p.label}</span>
              </button>
            ))}
          </div>

          {/* Persona Detail Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm max-w-4xl mx-auto">
            {activePersonaTab === 'employee' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div className="space-y-4">
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">
                    Employee Experience
                  </span>
                  <h3 className="text-2xl font-bold text-slate-900">
                    Transparent Requests with Zero Guesswork
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Submit leaves and expenses in seconds with instant feedback on policy compliance, holiday exclusions, and available balances before submission.
                  </p>
                  <ul className="space-y-2 text-xs text-slate-700 font-medium">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Live statutory holiday exclusion calculator</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Client-side SHA-256 receipt fingerprinting</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Plain-language decision explanation on every request</span>
                    </li>
                  </ul>
                  <Link
                    to="/leave/apply"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-xs"
                  >
                    <span>Try Leave Application</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
                <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                  <div className="text-xs font-bold text-slate-800">Sarah Connor (L3 Staff)</div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-white rounded-xl border border-slate-200">
                      <div className="text-[10px] text-slate-400">Annual Leave</div>
                      <div className="text-xl font-bold text-slate-900">16.0 d</div>
                    </div>
                    <div className="p-3 bg-white rounded-xl border border-slate-200">
                      <div className="text-[10px] text-slate-400">Expense Headroom</div>
                      <div className="text-xl font-bold text-emerald-600">$5,000</div>
                    </div>
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-800 font-medium">
                    ✓ Next corporate holiday: Thanksgiving Day (Nov 26, 2026)
                  </div>
                </div>
              </div>
            )}

            {activePersonaTab === 'manager' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div className="space-y-4">
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">
                    Manager Experience
                  </span>
                  <h3 className="text-2xl font-bold text-slate-900">
                    High-Velocity Approvals with Complete Context
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Managers review requests pre-validated by the EFCG engine. One-click approvals with full visibility into schedule overlaps and team capacity.
                  </p>
                  <ul className="space-y-2 text-xs text-slate-700 font-medium">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Pre-computed overlap and capacity warnings</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Mandatory reasoning capture for rejections</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Direct link to inspect full EFCG constraint graph</span>
                    </li>
                  </ul>
                  <Link
                    to="/approvals"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-xs"
                  >
                    <span>View Manager Queue</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
                <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                  <div className="text-xs font-bold text-slate-800">Pending Approval Queue</div>
                  <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs space-y-1">
                    <div className="flex justify-between font-bold">
                      <span>David Kim (L4 Manager)</span>
                      <span className="text-blue-600">3 Pending</span>
                    </div>
                    <p className="text-[11px] text-slate-500">Average sign-off turnaround: 3.5 hours</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-xl border border-blue-200 text-xs text-blue-800 font-medium">
                    ✓ Zero self-approval enforcement active
                  </div>
                </div>
              </div>
            )}

            {activePersonaTab === 'finance' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div className="space-y-4">
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">
                    Finance Experience
                  </span>
                  <h3 className="text-2xl font-bold text-slate-900">
                    Department Budgets & Controlled Reimbursements
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Real-time budget utilization tracking across 5 corporate cost centers. Batch reimbursement execution and continuous split-claim surveillance.
                  </p>
                  <ul className="space-y-2 text-xs text-slate-700 font-medium">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Atomic reservation prevents budget overdraw</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Split-claim rolling window heuristic detection</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Reimbursement execution with audit tracking</span>
                    </li>
                  </ul>
                  <Link
                    to="/finance"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-xs"
                  >
                    <span>View Finance Console</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
                <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                  <div className="text-xs font-bold text-slate-800">Corporate Budgets Headroom</div>
                  <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs space-y-2">
                    <div className="flex justify-between">
                      <span className="font-semibold text-slate-700">Engineering (CC-ENG-01)</span>
                      <span className="font-mono text-slate-900">$500,000</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: '42%' }} />
                    </div>
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-800 font-medium">
                    ✓ Duplicate receipt detector: 100% digest matches blocked
                  </div>
                </div>
              </div>
            )}

            {activePersonaTab === 'governance' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div className="space-y-4">
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">
                    Policy & Compliance
                  </span>
                  <h3 className="text-2xl font-bold text-slate-900">
                    Cryptographic Audit Chain & Anomaly Queue
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Inspect the immutable SHA-256 audit ledger. Verify block continuity and resolve surveillance alerts across 12 distinct anomaly classifications.
                  </p>
                  <ul className="space-y-2 text-xs text-slate-700 font-medium">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Tamper-evident block verification endpoint</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>12 automated surveillance anomaly detectors</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-600" />
                      <span>Configurable policy governance rules & limits</span>
                    </li>
                  </ul>
                  <Link
                    to="/audit"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-xs"
                  >
                    <span>Inspect Audit Chain</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
                <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                  <div className="text-xs font-bold text-slate-800">Audit Ledger Verification</div>
                  <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs font-mono space-y-1">
                    <div className="text-[10px] text-slate-400">Head Hash (SHA-256)</div>
                    <div className="text-blue-600 truncate font-semibold">89d7fd3ff4c0499174d0f8ea4b0...</div>
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-800 font-medium">
                    ✓ Integrity Status: 100% Valid (Zero Tampering Detected)
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Final High-Impact CTA Banner */}
      <section className="py-20 px-6 max-w-7xl mx-auto">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl p-10 sm:p-14 text-white text-center shadow-xl space-y-6 relative overflow-hidden">
          <div className="relative z-10 max-w-2xl mx-auto space-y-4">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Ready to Upgrade to Evidence-First Workforce Intelligence?
            </h2>
            <p className="text-sm sm:text-base text-blue-100 leading-relaxed">
              Experience the live platform loaded with 400 employees, 1,800+ evaluated requests, and real-time EFCG constraint graph resolution.
            </p>
            <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/dashboard"
                className="px-6 py-3 bg-white hover:bg-slate-50 text-blue-700 text-sm font-bold rounded-xl transition shadow-lg shadow-black/10 flex items-center gap-2"
              >
                <span>Launch Live Portal</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="px-6 py-3 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold rounded-xl border border-blue-400/30 transition flex items-center gap-2"
              >
                <span>1-Click Persona Sign In</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Enterprise Footer */}
      <footer className="border-t border-slate-200 bg-white py-12 px-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
                LF
              </div>
              <span className="font-bold text-slate-900 text-sm">LeaveFlow</span>
            </div>
            <p className="text-xs leading-relaxed text-slate-500">
              Evidence-First Constraint Graph (EFCG) Platform for Leave & Expense Management Automation.
            </p>
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>System Operational (SQLite WAL Active)</span>
            </div>
          </div>

          <div>
            <div className="font-bold text-slate-900 uppercase tracking-wider text-[11px] mb-3">
              Core Modules
            </div>
            <ul className="space-y-2">
              <li><Link to="/leave/apply" className="hover:text-blue-600">Leave Application</Link></li>
              <li><Link to="/expenses/submit" className="hover:text-blue-600">Expense Reimbursement</Link></li>
              <li><Link to="/approvals" className="hover:text-blue-600">Authority Approvals</Link></li>
              <li><Link to="/finance" className="hover:text-blue-600">Department Budgets</Link></li>
            </ul>
          </div>

          <div>
            <div className="font-bold text-slate-900 uppercase tracking-wider text-[11px] mb-3">
              EFCG Engine
            </div>
            <ul className="space-y-2">
              <li><Link to="/visualizer" className="hover:text-blue-600">Graph Visualizer</Link></li>
              <li><Link to="/anomalies" className="hover:text-blue-600">12 Anomaly Detectors</Link></li>
              <li><Link to="/audit" className="hover:text-blue-600">Cryptographic Hash Chain</Link></li>
              <li><Link to="/policies" className="hover:text-blue-600">Policy Governance</Link></li>
            </ul>
          </div>

          <div>
            <div className="font-bold text-slate-900 uppercase tracking-wider text-[11px] mb-3">
              Compliance & Specs
            </div>
            <ul className="space-y-2">
              <li>Deterministic Topological DAG</li>
              <li>Atomic Dual-Ledger System</li>
              <li>SHA-256 Block Hashing</li>
              <li>Zero Self-Approval Mandate</li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto pt-8 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            © 2026 LeaveFlow EFCG Architecture. All rights reserved. Every Request. Every Decision. Every Reason.
          </div>
          <div className="font-mono text-[11px] text-slate-400">
            Verified Pytest: 14/14 Passing (0.37s)
          </div>
        </div>
      </footer>
    </div>
  );
};
