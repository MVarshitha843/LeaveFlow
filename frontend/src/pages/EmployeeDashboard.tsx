import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { leaveApi, expenseApi, analyticsApi } from '../services/api';
import { LeaveBalance, LeaveRequest, ExpenseClaim, AnalyticsOverview } from '../types';
import {
  Calendar, CreditCard, Clock, CheckCircle2, XCircle, AlertTriangle,
  ArrowRight, PlusCircle, TrendingUp, ShieldCheck, DollarSign, Layers,
  Sparkles, FileText
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid
} from 'recharts';

export const EmployeeDashboard: React.FC = () => {
  const { user } = useAuth();
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [recentLeaves, setRecentLeaves] = useState<LeaveRequest[]>([]);
  const [recentExpenses, setRecentExpenses] = useState<ExpenseClaim[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [balRes, lveRes, expRes, anaRes] = await Promise.all([
        leaveApi.balances(),
        leaveApi.list({ limit: 5 }),
        expenseApi.list({ limit: 5 }),
        analyticsApi.overview(),
      ]);
      setBalances(balRes.data);
      setRecentLeaves(lveRes.data);
      setRecentExpenses(expRes.data);
      setAnalytics(anaRes.data);
    } catch (err) {
      console.error('Failed to load employee dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
      case 'REIMBURSED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PENDING_APPROVAL':
      case 'SUBMITTED':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'REJECTED':
      case 'CANCELLED':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200';
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Hero Card */}
      <div className="bg-white rounded-2xl p-6 md:p-8 border border-slate-200/90 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-50/70 rounded-full blur-3xl -z-10" />

        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Explainable Workforce Intelligence</span>
          </div>

          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900">
            Welcome back, {user?.first_name}!
          </h1>

          <p className="text-xs md:text-sm text-slate-600 mt-2 leading-relaxed">
            Your requests are evaluated by the Evidence-First Constraint Graph with atomic resource reservation and tamper-evident audit history.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-6">
            <Link
              to="/leave/apply"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-sm shadow-blue-600/20 flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Apply for Leave</span>
            </Link>
            <Link
              to="/expenses/submit"
              className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold border border-slate-200 transition shadow-xs flex items-center gap-1.5"
            >
              <CreditCard className="w-3.5 h-3.5 text-blue-600" />
              <span>Submit Expense Claim</span>
            </Link>
            <Link
              to="/requests"
              className="px-4 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900 rounded-xl text-xs font-semibold transition"
            >
              <span>View All Requests</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Leave Balances Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Available Leave Allocations (Year 2026)
            </h2>
            <p className="text-xs text-slate-500">Atomic Resource Ledger Linked</p>
          </div>
          <span className="text-xs font-semibold text-blue-600 font-mono">
            {balances.length} Active Policies
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {balances.slice(0, 6).map((b) => {
            const utilizationPct = b.allocated_days > 0
              ? Math.min(Math.round(((b.used_days + b.reserved_days) / b.allocated_days) * 100), 100)
              : 0;

            return (
              <div
                key={b.id}
                className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs hover-card-elevate"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-slate-800">{b.policy_name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                    {b.leave_policy_id}
                  </span>
                </div>

                <div className="flex items-baseline gap-2 mb-3">
                  <span className="text-3xl font-extrabold text-slate-900 tabular-nums">
                    {b.available_days.toFixed(1)}
                  </span>
                  <span className="text-xs text-slate-500">days available</span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-100 rounded-full h-1.5 mb-3 overflow-hidden">
                  <div
                    className="bg-blue-600 h-1.5 rounded-full"
                    style={{ width: `${utilizationPct}%` }}
                  />
                </div>

                <div className="pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-[11px] text-slate-500">
                  <div>
                    <span className="block text-[10px] text-slate-400">Allocated</span>
                    <span className="font-semibold text-slate-700">{b.allocated_days}d</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-400">Used</span>
                    <span className="font-semibold text-slate-700">{b.used_days}d</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-400">Reserved</span>
                    <span className="font-semibold text-amber-600">{b.reserved_days}d</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Operational Metrics & Trends */}
      {analytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Monthly Leave Trends</h3>
            <p className="text-xs text-slate-500 mb-4">Calculated from operational database records</p>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.monthly_leave_trends}>
                  <defs>
                    <linearGradient id="leaveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: 8, fontSize: 12, boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                  />
                  <Area type="monotone" dataKey="days" stroke="#2563EB" strokeWidth={2} fillOpacity={1} fill="url(#leaveGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Monthly Expense Activity</h3>
            <p className="text-xs text-slate-500 mb-4">Total claim volume and reimbursements</p>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.monthly_expense_trends}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                  <Tooltip
                    formatter={(val: any) => `$${Number(val).toLocaleString()}`}
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: 8, fontSize: 12, boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="amount" fill="#2563EB" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Recent Requests Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Leave Requests */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900">Recent Leave Requests</h3>
            <Link to="/requests" className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1">
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider">
                  <th className="pb-2.5">Request ID</th>
                  <th className="pb-2.5">Dates</th>
                  <th className="pb-2.5">Days</th>
                  <th className="pb-2.5">Status</th>
                  <th className="pb-2.5 text-right">EFCG</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {recentLeaves.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No leave requests filed yet.
                    </td>
                  </tr>
                ) : (
                  recentLeaves.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 font-mono font-semibold text-blue-600">
                        <Link to={`/requests/${r.id}`}>{r.id}</Link>
                      </td>
                      <td className="py-3">{r.start_date}</td>
                      <td className="py-3 font-semibold">{r.business_days}d</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(r.status)}`}>
                          {r.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <Link
                          to={`/visualizer?requestId=${r.id}`}
                          className="text-[10px] font-semibold text-blue-600 hover:underline"
                        >
                          Graph
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Expense Claims */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900">Recent Expense Claims</h3>
            <Link to="/requests" className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1">
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider">
                  <th className="pb-2.5">Claim ID</th>
                  <th className="pb-2.5">Merchant</th>
                  <th className="pb-2.5">Amount</th>
                  <th className="pb-2.5">Status</th>
                  <th className="pb-2.5 text-right">EFCG</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {recentExpenses.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No expense claims filed yet.
                    </td>
                  </tr>
                ) : (
                  recentExpenses.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 font-mono font-semibold text-blue-600">
                        <Link to={`/requests/${e.id}`}>{e.id}</Link>
                      </td>
                      <td className="py-3 font-medium text-slate-800">{e.merchant}</td>
                      <td className="py-3 font-semibold tabular-nums">${e.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(e.status)}`}>
                          {e.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <Link
                          to={`/visualizer?requestId=${e.id}`}
                          className="text-[10px] font-semibold text-blue-600 hover:underline"
                        >
                          Graph
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
