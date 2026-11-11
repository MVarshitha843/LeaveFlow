import React, { useState, useEffect } from 'react';
import { policyApi } from '../services/api';
import { LeavePolicy, ExpensePolicy } from '../types';
import {
  Settings, CheckCircle2, Clock, ShieldCheck, Edit3, Save, X, Layers
} from 'lucide-react';

export const PolicyGovernancePage: React.FC = () => {
  const [leavePolicies, setLeavePolicies] = useState<LeavePolicy[]>([]);
  const [expensePolicies, setExpensePolicies] = useState<ExpensePolicy[]>([]);
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingLeave, setEditingLeave] = useState<LeavePolicy | null>(null);
  const [editingExpense, setEditingExpense] = useState<ExpensePolicy | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const res = await policyApi.getAll();
      setLeavePolicies(res.data.leave_policies);
      setExpensePolicies(res.data.expense_policies);
      setVersions(res.data.recent_versions);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveLeave = async () => {
    if (!editingLeave) return;
    setSaving(true);
    try {
      await policyApi.updateLeave(editingLeave.id, {
        days_per_year: editingLeave.days_per_year,
        max_consecutive_days: editingLeave.max_consecutive_days,
        documentation_required_days: editingLeave.documentation_required_days,
      });
      setMsg(`Leave policy ${editingLeave.name} updated.`);
      setEditingLeave(null);
      loadPolicies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveExpense = async () => {
    if (!editingExpense) return;
    setSaving(true);
    try {
      await policyApi.updateExpense(editingExpense.id, {
        max_per_claim: editingExpense.max_per_claim,
        daily_limit: editingExpense.daily_limit,
        receipt_required_above: editingExpense.receipt_required_above,
      });
      setMsg(`Expense policy ${editingExpense.category} updated.`);
      setEditingExpense(null);
      loadPolicies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-blue-600" />
          <span>Policy Governance & Rule Versioning</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Configure statutory leave thresholds, expense category allowances, and maintain version history.
        </p>
      </div>

      {msg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{msg}</span>
        </div>
      )}

      {/* Leave Policies Section */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Configured Leave Policies</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {leavePolicies.map((p) => (
            <div key={p.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-slate-900">{p.name}</span>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                  {p.code}
                </span>
              </div>

              <div className="space-y-1.5 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Days / Year:</span>
                  <span className="font-semibold text-slate-800">{p.days_per_year}d</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Consecutive:</span>
                  <span className="font-semibold text-slate-800">{p.max_consecutive_days}d</span>
                </div>
                <div className="flex justify-between">
                  <span>Doc Required Above:</span>
                  <span className="font-semibold text-slate-800">{p.documentation_required_days}d</span>
                </div>
              </div>

              <button
                onClick={() => setEditingLeave(p)}
                className="w-full py-1.5 text-xs font-semibold text-blue-600 hover:bg-blue-50 border border-blue-200 rounded-lg transition flex items-center justify-center gap-1.5"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Adjust Limits</span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Expense Policies Section */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Expense Category Policy Limits</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {expensePolicies.map((p) => (
            <div key={p.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-slate-900">{p.category}</span>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-700">
                  {p.currency}
                </span>
              </div>

              <div className="space-y-1.5 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Max / Claim:</span>
                  <span className="font-semibold text-slate-800">${p.max_per_claim.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Daily Cap:</span>
                  <span className="font-semibold text-slate-800">${p.daily_limit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Receipt Threshold:</span>
                  <span className="font-semibold text-slate-800">${p.receipt_required_above.toFixed(2)}</span>
                </div>
              </div>

              <button
                onClick={() => setEditingExpense(p)}
                className="w-full py-1.5 text-xs font-semibold text-blue-600 hover:bg-blue-50 border border-blue-200 rounded-lg transition flex items-center justify-center gap-1.5"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Adjust Limits</span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Rule Version History */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Governance Rule Versions</h3>
        <div className="space-y-2">
          {versions.length === 0 ? (
            <p className="text-xs text-slate-400">Baseline rule version 1 active.</p>
          ) : (
            versions.map((v) => (
              <div key={v.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-900">{v.rule_type} — Version #{v.version_number}</span>
                  <span className="text-slate-500 block text-[11px]">{v.description}</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  {new Date(v.effective_date).toLocaleDateString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Edit Leave Modal */}
      {editingLeave && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">
              Edit Policy: {editingLeave.name}
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Days Allocated Per Year</label>
                <input
                  type="number"
                  value={editingLeave.days_per_year}
                  onChange={(e) => setEditingLeave({ ...editingLeave, days_per_year: parseFloat(e.target.value) || 0 })}
                  className="w-full py-1.5 px-3 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Max Consecutive Days</label>
                <input
                  type="number"
                  value={editingLeave.max_consecutive_days}
                  onChange={(e) => setEditingLeave({ ...editingLeave, max_consecutive_days: parseInt(e.target.value) || 0 })}
                  className="w-full py-1.5 px-3 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Documentation Required Above (Days)</label>
                <input
                  type="number"
                  value={editingLeave.documentation_required_days}
                  onChange={(e) => setEditingLeave({ ...editingLeave, documentation_required_days: parseInt(e.target.value) || 0 })}
                  className="w-full py-1.5 px-3 rounded-lg border border-slate-300"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setEditingLeave(null)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveLeave}
                disabled={saving}
                className="px-3 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                {saving ? 'Saving...' : 'Save Rule Version'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Expense Modal */}
      {editingExpense && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">
              Edit Policy: {editingExpense.category}
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Max Per Claim ($)</label>
                <input
                  type="number"
                  value={editingExpense.max_per_claim}
                  onChange={(e) => setEditingExpense({ ...editingExpense, max_per_claim: parseFloat(e.target.value) || 0 })}
                  className="w-full py-1.5 px-3 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Daily Limit ($)</label>
                <input
                  type="number"
                  value={editingExpense.daily_limit}
                  onChange={(e) => setEditingExpense({ ...editingExpense, daily_limit: parseFloat(e.target.value) || 0 })}
                  className="w-full py-1.5 px-3 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Receipt Required Above ($)</label>
                <input
                  type="number"
                  value={editingExpense.receipt_required_above}
                  onChange={(e) => setEditingExpense({ ...editingExpense, receipt_required_above: parseFloat(e.target.value) || 0 })}
                  className="w-full py-1.5 px-3 rounded-lg border border-slate-300"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setEditingExpense(null)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveExpense}
                disabled={saving}
                className="px-3 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                {saving ? 'Saving...' : 'Save Rule Version'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
