import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { leaveApi } from '../services/api';
import { LeavePolicy, LeaveBalance } from '../types';
import {
  Calendar, CheckCircle2, AlertTriangle, XCircle, ArrowRight,
  Info, ShieldCheck, FileText, Upload
} from 'lucide-react';

export const LeaveApplyPage: React.FC = () => {
  const navigate = useNavigate();

  const [policies, setPolicies] = useState<LeavePolicy[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [policyId, setPolicyId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [docUrl, setDocUrl] = useState('');

  // Live dry run evaluation
  const [dryRunLoading, setDryRunLoading] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSummaryModal, setShowSummaryModal] = useState(false);

  useEffect(() => {
    loadPoliciesAndBalances();
  }, []);

  const loadPoliciesAndBalances = async () => {
    try {
      const [pRes, bRes] = await Promise.all([
        leaveApi.policies(),
        leaveApi.balances(),
      ]);
      setPolicies(pRes.data);
      setBalances(bRes.data);
      if (pRes.data.length > 0) {
        setPolicyId(pRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Run dry run when policy, start, or end changes
  useEffect(() => {
    if (policyId && startDate && endDate && startDate <= endDate) {
      triggerDryRun();
    } else {
      setDryRunResult(null);
    }
  }, [policyId, startDate, endDate]);

  const triggerDryRun = async () => {
    setDryRunLoading(true);
    try {
      const res = await leaveApi.dryRun({
        policy_id: policyId,
        start_date: startDate,
        end_date: endDate,
        reason: reason || 'Planned absence',
        document_url: docUrl || undefined,
      });
      setDryRunResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setDryRunLoading(false);
    }
  };

  const selectedBalance = balances.find((b) => b.leave_policy_id === policyId);
  const selectedPolicy = policies.find((p) => p.id === policyId);

  const handleSubmit = async () => {
    setShowSummaryModal(false);
    setSubmitting(true);
    setError(null);
    try {
      const res = await leaveApi.submit({
        policy_id: policyId,
        start_date: startDate,
        end_date: endDate,
        reason,
        document_url: docUrl || undefined,
      });
      navigate(`/requests/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit leave request');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-600" />
          <span>Apply for Leave</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Submit leave requests evaluated with real-time EFCG constraint checks and automatic holiday exclusions.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Form Form Column */}
        <div className="md:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          {/* Policy Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Leave Category / Policy
            </label>
            <select
              value={policyId}
              onChange={(e) => setPolicyId(e.target.value)}
              className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800"
            >
              {policies.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (Max {p.max_consecutive_days} consecutive days)
                </option>
              ))}
            </select>
            {selectedPolicy?.description && (
              <p className="text-[11px] text-slate-500 mt-1">{selectedPolicy.description}</p>
            )}
          </div>

          {/* Date Pickers */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                min={startDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800"
              />
            </div>
          </div>

          {/* Reason */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Reason for Absence
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
              rows={3}
              placeholder="Provide context for manager review..."
              className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800"
            />
          </div>

          {/* Supporting Document */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Supporting Document URL / Reference (Optional)
            </label>
            <input
              type="text"
              value={docUrl}
              onChange={(e) => setDocUrl(e.target.value)}
              placeholder="e.g. /uploads/medical_certificate.pdf"
              className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800"
            />
          </div>

          <button
            type="button"
            onClick={() => setShowSummaryModal(true)}
            disabled={!startDate || !endDate || !reason || submitting}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span>Review & Submit Application</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Right Column: Live EFCG Preview & Balance Info */}
        <div className="space-y-4">
          {/* Balance Card */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Policy Balance Headroom
            </span>
            <div className="text-2xl font-extrabold text-slate-900 tabular-nums">
              {selectedBalance ? selectedBalance.available_days.toFixed(1) : '0.0'}
              <span className="text-xs font-normal text-slate-500 ml-1">days available</span>
            </div>
            <div className="mt-2 text-[11px] text-slate-500">
              Allocated: {selectedBalance?.allocated_days || 0}d • Used: {selectedBalance?.used_days || 0}d
            </div>
          </div>

          {/* Live Dry-Run Results */}
          {dryRunResult && (
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">Live EFCG Dry-Run</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                    dryRunResult.evaluation.decision_state === 'ELIGIBLE'
                      ? 'bg-emerald-100 text-emerald-800'
                      : dryRunResult.evaluation.decision_state === 'BLOCKED'
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {dryRunResult.evaluation.decision_state}
                </span>
              </div>

              {/* Day Calc Breakdown */}
              <div className="p-3 bg-slate-50 rounded-xl space-y-1.5 text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Calendar Days:</span>
                  <span className="font-semibold text-slate-900">{dryRunResult.calculation.calendar_days}d</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Excluded Weekends:</span>
                  <span className="font-semibold text-slate-700">-{dryRunResult.calculation.weekend_days}d</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Excluded Holidays:</span>
                  <span className="font-semibold text-slate-700">-{dryRunResult.calculation.holiday_days}d</span>
                </div>
                <div className="pt-1 border-t border-slate-200 flex justify-between font-bold text-blue-600">
                  <span>Net Business Days:</span>
                  <span>{dryRunResult.calculation.business_days}d</span>
                </div>
              </div>

              {/* Holiday Exclusions List */}
              {dryRunResult.calculation.excluded_dates.length > 0 && (
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Excluded Calendar Dates
                  </span>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {dryRunResult.calculation.excluded_dates.map((ex: any, idx: number) => (
                      <div key={idx} className="text-[11px] flex justify-between text-slate-600">
                        <span>{ex.date} ({ex.day_of_week})</span>
                        <span className="font-medium text-slate-500">{ex.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Explanation */}
              <p className="text-[11px] text-slate-600 leading-relaxed pt-1 border-t border-slate-100">
                {dryRunResult.evaluation.explanation}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Summary Modal */}
      {showSummaryModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900">
              Confirm Leave Application Summary
            </h3>
            <p className="text-xs text-slate-500">
              Please review the calculated absence details before initiating the approval workflow:
            </p>

            <div className="space-y-2 p-3 bg-slate-50 rounded-xl text-xs text-slate-700">
              <div className="flex justify-between">
                <span className="text-slate-500">Policy:</span>
                <span className="font-semibold">{selectedPolicy?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Dates:</span>
                <span className="font-semibold">{startDate} to {endDate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Calculated Business Days:</span>
                <span className="font-bold text-blue-600">
                  {dryRunResult?.calculation.business_days || 0} working day(s)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">EFCG Recommendation:</span>
                <span className="font-bold uppercase text-emerald-600">
                  {dryRunResult?.evaluation.decision_state || 'ELIGIBLE'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowSummaryModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition shadow"
              >
                {submitting ? 'Submitting...' : 'Confirm Submission'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
