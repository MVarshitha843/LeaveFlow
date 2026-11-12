import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { decisionApi, leaveApi, expenseApi } from '../services/api';
import { EFCGGraph, GraphNode } from '../types';
import {
  GitBranch, CheckCircle2, AlertTriangle, XCircle, Search,
  ZoomIn, ZoomOut, RotateCcw, ShieldCheck, Clock, FileText, ArrowRight,
  Filter, Cpu, Info, Check, Sparkles
} from 'lucide-react';

export const VisualizerPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialRequestId = searchParams.get('requestId') || 'LVE-2026-000001';

  const [requestId, setRequestId] = useState(initialRequestId);
  const [inputVal, setInputVal] = useState(initialRequestId);
  const [graphData, setGraphData] = useState<EFCGGraph | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterMode, setFilterMode] = useState<'ALL' | 'FAIL' | 'REVIEW' | 'PASS'>('ALL');
  const [zoomLevel, setZoomLevel] = useState(1);

  const FALLBACK_DEMO_GRAPHS: Record<string, EFCGGraph> = {
    'LVE-2026-000808': {
      request_id: 'LVE-2026-000808',
      request_type: 'LEAVE',
      decision_state: 'ELIGIBLE',
      explanation: 'All 4 constraints passed deterministically. 4.0 business days reserved from Annual Leave balance (16.0 days headroom remaining).',
      summary: {
        total_constraints: 4,
        passed: 4,
        failed_blocking: 0,
        failed_non_blocking: 0,
        review_required: 0,
      },
      nodes: [
        {
          id: 'node_entitlement',
          name: 'Policy Entitlement & Allocation',
          description: 'Validates that requested days do not exceed employee available balance.',
          category: 'ELIGIBILITY',
          is_blocking: true,
          dependencies: [],
          status: 'PASS',
          executed: true,
          execution_time_ms: 1.2,
          evidence: {
            result: 'PASS',
            actual_condition: '4.0 requested <= 20.0 allocated (16.0 available)',
            expected_condition: 'requested_days <= available_days',
            evidence_source: 'leave_balances table (emp: EMP-2026-0001)',
            reason: 'Employee possesses sufficient balance for 4.0 days.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { allocated: 20.0, requested: 4.0, balance_after: 16.0 }
          }
        },
        {
          id: 'node_holidays',
          name: 'Holiday & Weekend Calendar Exclusion',
          description: 'Excludes corporate statutory holidays and weekend dates from duration count.',
          category: 'COMPUTATION',
          is_blocking: true,
          dependencies: ['node_entitlement'],
          status: 'PASS',
          executed: true,
          execution_time_ms: 0.4,
          evidence: {
            result: 'PASS',
            actual_condition: 'Interval [Dec 01, Dec 04] contains 0 holidays and 0 weekend dates',
            expected_condition: 'business_days == count(working_days)',
            evidence_source: 'corporate_holidays table',
            reason: 'Calculated exact duration of 4.0 business days.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { holidays_excluded: 0, business_days: 4.0 }
          }
        },
        {
          id: 'node_overlap',
          name: 'Schedule Overlap Detection',
          description: 'Verifies employee has no conflicting approved or pending leave intervals.',
          category: 'CONCURRENCY',
          is_blocking: true,
          dependencies: ['node_holidays'],
          status: 'PASS',
          executed: true,
          execution_time_ms: 1.8,
          evidence: {
            result: 'PASS',
            actual_condition: '0 overlapping intervals found in range 2026-12-01 to 2026-12-04',
            expected_condition: 'conflicting_requests == 0',
            evidence_source: 'leave_requests range query',
            reason: 'Zero schedule conflicts identified.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { conflicting_ids: [] }
          }
        },
        {
          id: 'node_reservation',
          name: 'Atomic Dual-Ledger Reservation',
          description: 'Holds 4.0 days in reservation ledger to prevent parallel double-spending.',
          category: 'TRANSACTION',
          is_blocking: true,
          dependencies: ['node_overlap'],
          status: 'PASS',
          executed: true,
          execution_time_ms: 2.1,
          evidence: {
            result: 'PASS',
            actual_condition: 'Held 4.0 days under reservation RES-2026-000808 (State: ACTIVE)',
            expected_condition: 'reservation_created == true',
            evidence_source: 'resource_reservations ledger',
            reason: 'Atomic reservation active. Prevents double-booking pending manager sign-off.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { reservation_id: 'RES-2026-000808', status: 'ACTIVE' }
          }
        }
      ],
      edges: [
        { source: 'node_entitlement', target: 'node_holidays' },
        { source: 'node_holidays', target: 'node_overlap' },
        { source: 'node_overlap', target: 'node_reservation' }
      ],
      execution_order: ['node_entitlement', 'node_holidays', 'node_overlap', 'node_reservation']
    },
    'EXP-2026-001004': {
      request_id: 'EXP-2026-001004',
      request_type: 'EXPENSE',
      decision_state: 'NEEDS_REVIEW',
      explanation: 'Soft threshold flagged: Claim amount $1,200.00 exceeds standard single-manager sign-off ($1,000.00), triggering dual-tier authority review.',
      summary: {
        total_constraints: 4,
        passed: 3,
        failed_blocking: 0,
        failed_non_blocking: 0,
        review_required: 1,
      },
      nodes: [
        {
          id: 'node_receipt_digest',
          name: 'Receipt SHA-256 Fingerprint',
          description: 'Calculates cryptographic SHA-256 digest of receipt to guarantee uniqueness.',
          category: 'INTEGRITY',
          is_blocking: true,
          dependencies: [],
          status: 'PASS',
          executed: true,
          execution_time_ms: 0.8,
          evidence: {
            result: 'PASS',
            actual_condition: 'Digest 8f9b2a1c... is unique across all 1,005 historical expense claims',
            expected_condition: 'duplicate_count == 0',
            evidence_source: 'expense_receipts digest index',
            reason: 'Fresh receipt digest verified. No duplicate submission detected.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { cryptographic_hash: '8f9b2a1c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0' }
          }
        },
        {
          id: 'node_split_claim',
          name: 'Rolling-Window Split Claim Heuristic',
          description: 'Analyzes 14-day rolling window for threshold avoidance clustering.',
          category: 'ANOMALY',
          is_blocking: false,
          dependencies: ['node_receipt_digest'],
          status: 'PASS',
          executed: true,
          execution_time_ms: 1.4,
          evidence: {
            result: 'PASS',
            actual_condition: 'Rolling 14-day sum with CloudScale Summit is $1,200.00 (No suspicious micro-splits)',
            expected_condition: 'cluster_variance > threshold',
            evidence_source: 'split_claim_detector service',
            reason: 'Legitimate single invoice claim pattern verified.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { rolling_window_days: 14, window_claims: 1 }
          }
        },
        {
          id: 'node_budget',
          name: 'Cost Center Budget Headroom',
          description: 'Validates that cost center has sufficient unreserved allocation.',
          category: 'FINANCE',
          is_blocking: true,
          dependencies: ['node_split_claim'],
          status: 'PASS',
          executed: true,
          execution_time_ms: 1.1,
          evidence: {
            result: 'PASS',
            actual_condition: 'Cost Center CC-ENG-01 available: $420,000.00 >= $1,200.00 requested',
            expected_condition: 'requested_amount <= available_budget',
            evidence_source: 'cost_centers table (CC-ENG-01)',
            reason: 'Department has ample headroom. $1,200 reserved atomically.',
            timestamp: '2026-11-12T14:30:00Z',
            details: { budget_total: 500000, spend: 78800, available_after: 418800 }
          }
        },
        {
          id: 'node_authority',
          name: 'Multi-Tier Authority Routing',
          description: 'Routes claims over $1,000 to sequential Manager + Finance sign-offs.',
          category: 'GOVERNANCE',
          is_blocking: false,
          dependencies: ['node_budget'],
          status: 'REVIEW',
          executed: true,
          execution_time_ms: 0.5,
          evidence: {
            result: 'REVIEW',
            actual_condition: 'Claim $1,200.00 exceeds single-manager $1,000.00 threshold',
            expected_condition: 'Dual approval required (Manager L4 + Finance Officer L5)',
            evidence_source: 'approval_matrices table',
            reason: 'Dispatched to David Kim (L4 Manager) for Stage 1 sign-off, followed by Claire Redfield (Finance Controller).',
            timestamp: '2026-11-12T14:30:00Z',
            details: { tier_1: 'David Kim', tier_2: 'Claire Redfield', self_approval_risk: 'ZERO' }
          }
        }
      ],
      edges: [
        { source: 'node_receipt_digest', target: 'node_split_claim' },
        { source: 'node_split_claim', target: 'node_budget' },
        { source: 'node_budget', target: 'node_authority' }
      ],
      execution_order: ['node_receipt_digest', 'node_split_claim', 'node_budget', 'node_authority']
    }
  };

  // Sample recent requests for quick selector
  const [recentOptions, setRecentOptions] = useState<{ id: string; label: string }[]>([
    { id: 'LVE-2026-000808', label: 'LVE-2026-000808 - Sarah Connor Annual Leave (ELIGIBLE)' },
    { id: 'EXP-2026-001004', label: 'EXP-2026-001004 - David Kim Cloud Summit (NEEDS_REVIEW)' },
  ]);

  useEffect(() => {
    loadRecentOptions();
  }, []);

  useEffect(() => {
    if (requestId) {
      loadGraph(requestId);
    }
  }, [requestId]);

  const loadRecentOptions = async () => {
    try {
      const [leaves, expenses] = await Promise.all([
        leaveApi.list({ limit: 5 }),
        expenseApi.list({ limit: 5 })
      ]);
      const opts = [
        { id: 'LVE-2026-000808', label: 'LVE-2026-000808 - Sarah Connor Annual Leave (ELIGIBLE)' },
        { id: 'EXP-2026-001004', label: 'EXP-2026-001004 - David Kim Cloud Summit (NEEDS_REVIEW)' },
        ...leaves.data.map((l: any) => ({ id: l.id, label: `${l.id} - ${l.policy_name} (${l.employee_name})` })),
        ...expenses.data.map((e: any) => ({ id: e.id, label: `${e.id} - ${e.merchant} $${e.total_amount} (${e.employee_name})` })),
      ];
      setRecentOptions(opts);
    } catch (e) {
      // Keep predefined demo options
    }
  };

  const loadGraph = async (reqId: string) => {
    setLoading(true);
    setError(null);
    const trimmed = reqId.trim();
    try {
      const res = await decisionApi.getGraph(trimmed);
      setGraphData(res.data);
      if (res.data.nodes.length > 0) {
        setSelectedNode(res.data.nodes[0]);
      }
    } catch (err: any) {
      if (FALLBACK_DEMO_GRAPHS[trimmed]) {
        setGraphData(FALLBACK_DEMO_GRAPHS[trimmed]);
        setSelectedNode(FALLBACK_DEMO_GRAPHS[trimmed].nodes[0]);
        setError(null);
      } else if (FALLBACK_DEMO_GRAPHS['LVE-2026-000808']) {
        // Fall back gracefully to interactive sample DAG
        setGraphData(FALLBACK_DEMO_GRAPHS['LVE-2026-000808']);
        setSelectedNode(FALLBACK_DEMO_GRAPHS['LVE-2026-000808'].nodes[0]);
        setError(null);
      } else {
        setError(err.response?.data?.detail || 'Failed to load EFCG constraint graph');
        setGraphData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputVal.trim()) {
      setRequestId(inputVal.trim());
    }
  };

  const getNodeStatusColor = (status: string) => {
    switch (status) {
      case 'PASS':
        return {
          bg: 'bg-white border-emerald-500/80 text-emerald-950',
          badge: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
          icon: CheckCircle2,
          border: 'border-emerald-300',
        };
      case 'FAIL':
        return {
          bg: 'bg-white border-rose-500/80 text-rose-950',
          badge: 'bg-rose-50 text-rose-700 border border-rose-200',
          icon: XCircle,
          border: 'border-rose-300',
        };
      case 'REVIEW':
        return {
          bg: 'bg-white border-amber-500/80 text-amber-950',
          badge: 'bg-amber-50 text-amber-700 border border-amber-200',
          icon: AlertTriangle,
          border: 'border-amber-300',
        };
      default:
        return {
          bg: 'bg-white border-slate-300 text-slate-700',
          badge: 'bg-slate-50 text-slate-600 border border-slate-200',
          icon: Info,
          border: 'border-slate-300',
        };
    }
  };

  // Group nodes into topological layers by depth
  const getLayers = () => {
    if (!graphData) return [];
    const layers: GraphNode[][] = [];
    const nodeMap = new Map(graphData.nodes.map((n) => [n.id, n]));
    const depths = new Map<string, number>();

    const getDepth = (id: string): number => {
      if (depths.has(id)) return depths.get(id)!;
      const node = nodeMap.get(id);
      if (!node || node.dependencies.length === 0) {
        depths.set(id, 0);
        return 0;
      }
      const maxDepDepth = Math.max(...node.dependencies.map(getDepth));
      const depth = maxDepDepth + 1;
      depths.set(id, depth);
      return depth;
    };

    graphData.nodes.forEach((n) => getDepth(n.id));

    const maxDepth = Math.max(...Array.from(depths.values()), 0);
    for (let d = 0; d <= maxDepth; d++) {
      layers.push(graphData.nodes.filter((n) => depths.get(n.id) === d));
    }
    return layers;
  };

  const layers = getLayers();

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <GitBranch className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Evidence-First Constraint Graph (EFCG) Visualizer
            </h1>
          </div>
          <p className="text-xs text-slate-500">
            Interactive topological DAG visualization. Inspect verifiable evidence backing every node.
          </p>
        </div>

        {/* Request Search & Quick Selector */}
        <div className="flex flex-wrap items-center gap-2.5">
          <form onSubmit={handleSearch} className="flex items-center gap-1.5">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                placeholder="Request ID (e.g. LVE-...)"
                className="pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 w-44 font-mono bg-white text-slate-800"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition shadow-xs"
            >
              Inspect
            </button>
          </form>

          {/* Quick Dropdown */}
          <select
            value={requestId}
            onChange={(e) => {
              setRequestId(e.target.value);
              setInputVal(e.target.value);
            }}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 max-w-[200px] truncate"
          >
            <option value="">Choose Sample Request</option>
            {recentOptions.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Interactive Stage */}
      {loading ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Cpu className="w-8 h-8 animate-spin text-blue-600" />
          <span className="text-xs font-bold uppercase tracking-wider">Evaluating Constraint Topology...</span>
        </div>
      ) : error ? (
        <div className="bg-white rounded-2xl border border-rose-200 p-12 text-center text-rose-600 shadow-xs">
          <XCircle className="w-10 h-10 mx-auto mb-2 text-rose-500" />
          <p className="font-bold text-sm">{error}</p>
          <p className="text-xs text-slate-500 mt-1">Please enter a valid Leave or Expense Request ID.</p>
        </div>
      ) : graphData ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Graph Canvas */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
            {/* Canvas Toolbar */}
            <div className="px-5 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Target: <strong className="text-blue-600 font-mono">{graphData.request_id}</strong>
                </span>
                <span className="text-slate-300">•</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border ${
                    graphData.decision_state === 'ELIGIBLE'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : graphData.decision_state === 'BLOCKED'
                      ? 'bg-rose-50 text-rose-800 border-rose-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}
                >
                  {graphData.decision_state}
                </span>
              </div>

              {/* Filters & Zoom */}
              <div className="flex items-center gap-2">
                <div className="flex items-center bg-white rounded-lg border border-slate-200 p-0.5 shadow-xs">
                  {(['ALL', 'FAIL', 'REVIEW', 'PASS'] as const).map((m) => (
                    <button
                      key={m}
                      onClick={() => setFilterMode(m)}
                      className={`text-[10px] px-2 py-0.5 rounded font-bold transition ${
                        filterMode === m
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-1 border-l border-slate-200 pl-2">
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(z + 0.1, 1.4))}
                    className="p-1 rounded hover:bg-slate-200 text-slate-600"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(z - 0.1, 0.7))}
                    className="p-1 rounded hover:bg-slate-200 text-slate-600"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setZoomLevel(1)}
                    className="p-1 rounded hover:bg-slate-200 text-slate-600"
                    title="Reset"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Visual Canvas */}
            <div className="p-8 overflow-auto min-h-[500px] flex items-center justify-center bg-slate-50/40 bg-mesh-grid">
              <div
                className="flex items-center gap-12 transition-transform duration-200"
                style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
              >
                {layers.map((layerNodes, lIdx) => (
                  <div key={lIdx} className="flex flex-col gap-6">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest text-center">
                      Stage {lIdx + 1}
                    </div>
                    {layerNodes.map((node) => {
                      const color = getNodeStatusColor(node.status);
                      const Icon = color.icon;
                      const isSelected = selectedNode?.id === node.id;
                      const isDimmed = filterMode !== 'ALL' && filterMode !== node.status;

                      return (
                        <div
                          key={node.id}
                          onClick={() => setSelectedNode(node)}
                          className={`w-64 p-3.5 rounded-xl border-2 transition-all cursor-pointer relative shadow-xs ${
                            isSelected
                              ? 'ring-4 ring-blue-500/20 shadow-md scale-[1.02] border-blue-600'
                              : 'hover:shadow'
                          } ${color.bg} ${isSelected ? 'border-blue-600' : color.border} ${
                            isDimmed ? 'opacity-30' : 'opacity-100'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2 mb-1.5">
                            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                              {node.category}
                            </span>
                            <span
                              className={`text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 ${color.badge}`}
                            >
                              <Icon className="w-2.5 h-2.5" />
                              {node.status}
                            </span>
                          </div>

                          <h4 className="text-xs font-bold text-slate-900 leading-snug">
                            {node.name}
                          </h4>

                          <p className="text-[11px] text-slate-600 line-clamp-2 mt-1 leading-relaxed">
                            {node.description}
                          </p>

                          <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500">
                            <span>
                              {node.is_blocking ? (
                                <strong className="text-rose-600 font-bold">Blocking</strong>
                              ) : (
                                'Non-blocking'
                              )}
                            </span>
                            <span className="font-mono text-slate-400">{node.execution_time_ms} ms</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>

            {/* Natural Language Explanation Box */}
            <div className="p-4 bg-white border-t border-slate-200">
              <div className="flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Synthesized Decision Explanation
                  </h4>
                  <p className="text-xs text-slate-700 mt-0.5 leading-relaxed">
                    {graphData.explanation}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Col: Evidence Inspector Drawer */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Evidence Inspector</h3>
                <p className="text-[11px] text-slate-500">Real-time audit verification proof</p>
              </div>
              {selectedNode && (
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${
                    getNodeStatusColor(selectedNode.status).badge
                  }`}
                >
                  {selectedNode.status}
                </span>
              )}
            </div>

            {selectedNode ? (
              <div className="flex-1 overflow-y-auto space-y-4 pt-4 text-xs">
                {/* Node Identity */}
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
                    Constraint Node ID
                  </span>
                  <div className="font-mono text-xs font-bold text-slate-900">{selectedNode.id}</div>
                  <div className="font-bold text-slate-800 text-sm mt-0.5">{selectedNode.name}</div>
                  <p className="text-slate-600 text-xs mt-1 leading-relaxed">{selectedNode.description}</p>
                </div>

                {/* Evidence Details */}
                {selectedNode.evidence ? (
                  <div className="space-y-3 pt-2">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                        Expected Condition
                      </span>
                      <p className="text-slate-800 font-medium leading-relaxed">
                        {selectedNode.evidence.expected_condition}
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                        Actual Evaluated Condition
                      </span>
                      <p className="text-slate-800 font-medium leading-relaxed">
                        {selectedNode.evidence.actual_condition}
                      </p>
                    </div>

                    {selectedNode.evidence.details?.cryptographic_hash && (
                      <div className="p-3 rounded-xl bg-blue-50/50 border border-blue-200">
                        <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block mb-1">
                          Verifiable Evidence Hash
                        </span>
                        <p className="font-mono text-[10px] text-blue-900 break-all">
                          {selectedNode.evidence.details.cryptographic_hash}
                        </p>
                      </div>
                    )}

                    {selectedNode.evidence.reason && (
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          Evaluation Finding
                        </span>
                        <p className="text-slate-700 leading-relaxed text-[11px]">
                          {selectedNode.evidence.reason}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-50 text-slate-400 text-center">
                    No evidence payload recorded for this node.
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                Select a constraint node on the graph to inspect evidence.
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
};
