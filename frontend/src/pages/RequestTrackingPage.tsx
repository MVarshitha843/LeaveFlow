import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { leaveApi, expenseApi, approvalApi, auditApi, decisionApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  Layers, CheckCircle2, Clock, XCircle, AlertTriangle, GitBranch,
  ShieldCheck, FileText, ArrowLeft, ArrowRight, UserCheck, Calendar, CreditCard
} from 'lucide-react';

export const RequestTrackingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [requestData, setRequestData] = useState<any | null>(null);
  const [approvalSteps, setApprovalSteps] = useState<any[]>([]);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [decisionDetails, setDecisionDetails] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Fallback request list when no ID in route
  const [requestList, setRequestList] = useState<{ id: string; type: string; summary: string; status: string; date: string }[]>([]);

  useEffect(() => {
    if (id) {
      loadRequestDetails(id);
    } else {
      loadAllRequestsList();
    }
  }, [id]);

  const loadAllRequestsList = async () => {
    setLoading(true);
    try {
      const [leaves, expenses] = await Promise.all([
        leaveApi.list({ limit: 50 }),
        expenseApi.list({ limit: 50 })
      ]);
      const list = [
        ...leaves.data.map((l: any) => ({
          id: l.id,
          type: 'LEAVE',
          summary: `${l.policy_name} (${l.business_days}d) - ${l.reason}`,
          status: l.status,
          date: l.created_at,
          employee_name: l.employee_name
        })),
        ...expenses.data.map((e: any) => ({
          id: e.id,
          type: 'EXPENSE',
          summary: `${e.merchant} ($${e.total_amount.toFixed(2)}) - ${e.description}`,
          status: e.status,
          date: e.created_at,
          employee_name: e.employee_name
        }))
      ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      setRequestList(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRequestDetails = async (reqId: string) => {
    setLoading(true);
    try {
      const isLeave = reqId.startsWith('LVE');
      const [reqRes, stepsRes, auditRes, decRes] = await Promise.all([
        isLeave ? leaveApi.get(reqId) : expenseApi.get(reqId),
        approvalApi.getSteps(reqId),
        auditApi.requestTrail(reqId),
        decisionApi.getDetails(reqId),
      ]);
      setRequestData({ ...reqRes.data, isLeave });
      setApprovalSteps(stepsRes.data);
      setAuditEvents(auditRes.data);
      setDecisionDetails(decRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelRequest = async () => {
    if (!id || !window.confirm('Are you sure you want to cancel this request? Reserved balances will be released immediately.')) return;
    setCancelling(true);
    try {
      if (id.startsWith('LVE')) {
        await leaveApi.cancel(id);
      } else {
        await expenseApi.cancel(id);
      }
      setActionMsg('Request cancelled successfully and reservations released.');
      loadRequestDetails(id);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel request');
    } finally {
      setCancelling(false);
    }
  };

  if (!id) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <span>Request Repository & Lifecycle Tracking</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Select any submitted leave or expense request to inspect its real-time approval stages, constraint evaluations, and audit events.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Request ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Applicant</th>
                <th className="py-3 px-4">Summary</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {loading ? (
                <tr><td colSpan={6} className="py-12 text-center text-slate-400">Loading requests...</td></tr>
              ) : requestList.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-mono font-bold text-blue-600">
                    <Link to={`/requests/${item.id}`}>{item.id}</Link>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {item.type}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-medium">{(item as any).employee_name || 'Staff'}</td>
                  <td className="py-3 px-4 max-w-xs truncate">{item.summary}</td>
                  <td className="py-3 px-4">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      item.status === 'APPROVED' || item.status === 'REIMBURSED'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : item.status === 'REJECTED' || item.status === 'CANCELLED'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-blue-50 text-blue-700 border-blue-200'
                    }`}>
                      {item.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      to={`/requests/${item.id}`}
                      className="px-2.5 py-1 bg-slate-100 hover:bg-blue-600 hover:text-white rounded-lg text-slate-700 transition font-semibold text-[11px]"
                    >
                      Track
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (loading || !requestData) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center text-slate-400">
        Loading request details...
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back button & Action banner */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/requests')}
          className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Request Directory</span>
        </button>

        {requestData.status !== 'CANCELLED' && requestData.status !== 'REJECTED' && (
          <button
            onClick={handleCancelRequest}
            disabled={cancelling}
            className="px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg transition"
          >
            {cancelling ? 'Releasing...' : 'Cancel Request & Release Ledger'}
          </button>
        )}
      </div>

      {actionMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Main Request Header Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-base font-bold text-slate-900">{requestData.id}</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 uppercase">
              {requestData.isLeave ? 'Leave Request' : 'Expense Claim'}
            </span>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                requestData.status === 'APPROVED' || requestData.status === 'REIMBURSED'
                  ? 'bg-emerald-100 text-emerald-800'
                  : requestData.status === 'REJECTED' || requestData.status === 'CANCELLED'
                  ? 'bg-rose-100 text-rose-800'
                  : 'bg-blue-100 text-blue-800'
              }`}
            >
              {requestData.status.replace('_', ' ')}
            </span>
          </div>

          <p className="text-xs text-slate-600 mt-1">
            Submitted by <strong>{requestData.employee_name}</strong> on {new Date(requestData.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-100 pt-3 md:pt-0 md:pl-6 text-right">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              {requestData.isLeave ? 'Business Working Days' : 'Total Claim Amount'}
            </span>
            <span className="text-2xl font-extrabold text-slate-900 tabular-nums">
              {requestData.isLeave ? `${requestData.business_days} days` : `$${requestData.total_amount.toFixed(2)}`}
            </span>
          </div>

          <Link
            to={`/visualizer?requestId=${requestData.id}`}
            className="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border border-blue-200/60"
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>Interactive Graph</span>
          </Link>
        </div>
      </div>

      {/* Decision Engine Explainability Breakdown */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">EFCG Decision Synthesizer</h3>
          </div>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
              requestData.decision_state === 'ELIGIBLE'
                ? 'bg-emerald-100 text-emerald-800'
                : requestData.decision_state === 'BLOCKED'
                ? 'bg-rose-100 text-rose-800'
                : 'bg-amber-100 text-amber-800'
            }`}
          >
            State: {requestData.decision_state}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
          <p className="font-semibold text-slate-900 mb-1">Synthesized Plain-Language Explanation:</p>
          <p>{requestData.decision_explanation}</p>
        </div>

        {/* Constraint Evaluation Table */}
        {decisionDetails && decisionDetails.evaluations && (
          <div className="pt-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Evaluated Policy Constraints
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {decisionDetails.evaluations.map((ev: any) => (
                <div key={ev.id} className="p-3 rounded-xl border border-slate-200 bg-white text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">{ev.constraint_name}</span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.2 rounded uppercase ${
                        ev.result === 'PASS'
                          ? 'bg-emerald-50 text-emerald-700'
                          : ev.result === 'FAIL'
                          ? 'bg-rose-50 text-rose-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {ev.result}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-snug">{ev.evidence_summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Approval Workflow Timeline */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-blue-600" />
          <span>Approval Authority Chain</span>
        </h3>

        <div className="relative border-l-2 border-slate-200 ml-4 space-y-6 py-2">
          {approvalSteps.map((step, idx) => (
            <div key={step.id} className="relative pl-6">
              <div
                className={`absolute -left-2.5 top-0.5 w-5 h-5 rounded-full border-2 bg-white flex items-center justify-center ${
                  step.status === 'APPROVED'
                    ? 'border-emerald-500 text-emerald-600'
                    : step.status === 'REJECTED'
                    ? 'border-rose-500 text-rose-600'
                    : 'border-blue-500 text-blue-600'
                }`}
              >
                {step.status === 'APPROVED' ? (
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                ) : step.status === 'REJECTED' ? (
                  <XCircle className="w-3 h-3 text-rose-600" />
                ) : (
                  <Clock className="w-3 h-3 text-blue-600" />
                )}
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-900">
                    Step {step.step_order}: {step.approver_name || step.approver_id}
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600">
                    {step.approver_role || 'Manager'}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                      step.status === 'APPROVED'
                        ? 'bg-emerald-50 text-emerald-700'
                        : step.status === 'REJECTED'
                        ? 'bg-rose-50 text-rose-700'
                        : 'bg-blue-50 text-blue-700'
                    }`}
                  >
                    {step.status.replace('_', ' ')}
                  </span>
                </div>

                {step.comments && (
                  <p className="text-xs text-slate-600 mt-1 bg-slate-50 p-2 rounded-lg border border-slate-200">
                    "{step.comments}"
                  </p>
                )}

                {step.action_timestamp && (
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    Action timestamp: {new Date(step.action_timestamp).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Proof-Carrying Tamper-Evident Audit Trail */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" />
          <span>Proof-Carrying Audit Events (SHA-256 Linked Block Ledger)</span>
        </h3>

        <div className="space-y-2">
          {auditEvents.map((ev) => (
            <div key={ev.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">
                  #{ev.id} • {ev.action}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {new Date(ev.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-600 break-all">
                Payload: {ev.payload_json}
              </p>
              <div className="pt-1 flex items-center gap-2 text-[10px] font-mono text-slate-400 truncate">
                <span>Prev: {ev.previous_hash.slice(0, 16)}...</span>
                <span>•</span>
                <span className="text-blue-600 font-semibold">Sign: {ev.current_hash.slice(0, 16)}...</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
