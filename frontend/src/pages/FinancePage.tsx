import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { employeeApi, expenseApi, approvalApi, anomalyApi } from '../services/api';
import { Department, CostCenter, ExpenseClaim, AnomalyAlert } from '../types';
import {
  Building, DollarSign, TrendingUp, AlertTriangle, CheckCircle2,
  ArrowRight, ShieldAlert, GitBranch, RefreshCw, CreditCard
} from 'lucide-react';

export const FinancePage: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [approvedClaims, setApprovedClaims] = useState<ExpenseClaim[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [reimbursingId, setReimbursingId] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    loadFinanceData();
  }, []);

  const loadFinanceData = async () => {
    setLoading(true);
    try {
      const [deptRes, ccRes, claimRes, anoRes] = await Promise.all([
        employeeApi.departments(),
        employeeApi.costCenters(),
        expenseApi.list({ status: 'APPROVED', limit: 20 }),
        anomalyApi.list({ limit: 10 }),
      ]);
      setDepartments(deptRes.data);
      setCostCenters(ccRes.data);
      setApprovedClaims(claimRes.data);
      setAnomalies(anoRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDisburseReimbursement = async (claimId: string) => {
    setReimbursingId(claimId);
    setMsg(null);
    try {
      const res = await approvalApi.reimburse(claimId);
      setMsg(`Reimbursement of $${res.data.amount.toFixed(2)} disbursed! Transaction: ${res.data.transaction_ref}`);
      loadFinanceData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to process reimbursement');
    } finally {
      setReimbursingId(null);
    }
  };

  const totalBudget = departments.reduce((acc, d) => acc + d.annual_budget, 0);
  const totalSpend = departments.reduce((acc, d) => acc + d.current_spend, 0);
  const totalReserved = departments.reduce((acc, d) => acc + d.reserved_budget, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Building className="w-5 h-5 text-blue-600" />
          <span>Finance & Cost Center Intelligence Portal</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Departmental budget utilization, financial reserve ledgers, and disbursement settlement operations.
        </p>
      </div>

      {msg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{msg}</span>
        </div>
      )}

      {/* Financial Overview Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Total Corporate Budget
          </span>
          <span className="text-2xl font-extrabold text-slate-900 tabular-nums">
            ${totalBudget.toLocaleString()}
          </span>
          <span className="text-xs text-slate-500 block mt-1">FY 2026 Allocated Operating Capital</span>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Current Committed Spend
          </span>
          <span className="text-2xl font-extrabold text-slate-900 tabular-nums">
            ${totalSpend.toLocaleString()}
          </span>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2">
            <div
              className="bg-blue-600 h-1.5 rounded-full"
              style={{ width: `${Math.min((totalSpend / totalBudget) * 100, 100)}%` }}
            />
          </div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Resource Reservation Holds
          </span>
          <span className="text-2xl font-extrabold text-amber-600 tabular-nums">
            ${totalReserved.toLocaleString()}
          </span>
          <span className="text-xs text-slate-500 block mt-1">Pending approval in reservation ledger</span>
        </div>
      </div>

      {/* Department Budgets Grid */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Departmental Budget Headroom</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((d) => {
            const pct = d.annual_budget > 0 ? (d.current_spend / d.annual_budget) * 100 : 0;
            return (
              <div key={d.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900">{d.name}</span>
                  <span className="text-[10px] font-mono font-bold text-blue-600">{d.code}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-600 pt-1">
                  <span>Spend: ${d.current_spend.toLocaleString()}</span>
                  <span>Budget: ${d.annual_budget.toLocaleString()}</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      pct > 90 ? 'bg-rose-500' : pct > 70 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-slate-500 pt-1">
                  <span>Available: ${d.available_budget.toLocaleString()}</span>
                  <span className="font-bold">{pct.toFixed(1)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Approved Claims Ready for Disbursement */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Approved Claims Queued for Reimbursement
            </h3>
            <p className="text-xs text-slate-500">
              Fully approved expense claims authorized for payment settlement
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            {approvedClaims.length} Claims Ready
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                <th className="pb-2.5">Claim ID</th>
                <th className="pb-2.5">Applicant</th>
                <th className="pb-2.5">Cost Center</th>
                <th className="pb-2.5">Merchant</th>
                <th className="pb-2.5">Amount</th>
                <th className="pb-2.5 text-right">Settlement Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {approvedClaims.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No approved claims pending reimbursement disbursement.
                  </td>
                </tr>
              ) : (
                approvedClaims.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 font-mono font-bold text-blue-600">
                      <Link to={`/requests/${c.id}`}>{c.id}</Link>
                    </td>
                    <td className="py-3 font-medium">{c.employee_name}</td>
                    <td className="py-3 text-slate-500">{c.cost_center_name}</td>
                    <td className="py-3">{c.merchant}</td>
                    <td className="py-3 font-bold text-slate-900 tabular-nums">
                      ${c.total_amount.toFixed(2)}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleDisburseReimbursement(c.id)}
                        disabled={reimbursingId === c.id}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition shadow-sm"
                      >
                        {reimbursingId === c.id ? 'Processing...' : 'Disburse (ACH)'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
