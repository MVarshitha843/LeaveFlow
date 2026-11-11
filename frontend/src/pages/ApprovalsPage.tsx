import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { approvalApi } from '../services/api';
import { PendingApprovalItem } from '../types';
import {
  CheckSquare, CheckCircle2, XCircle, HelpCircle, ArrowRight,
  GitBranch, Clock, UserCheck, AlertTriangle, ShieldCheck
} from 'lucide-react';

export const ApprovalsPage: React.FC = () => {
  const [pendingItems, setPendingItems] = useState<PendingApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<PendingApprovalItem | null>(null);
  const [actionType, setActionType] = useState<'APPROVE' | 'REJECT' | 'REQUEST_INFO'>('APPROVE');
  const [comments, setComments] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<'ALL' | 'LEAVE' | 'EXPENSE'>('ALL');

  useEffect(() => {
    loadPending();
  }, []);

  const loadPending = async () => {
    setLoading(true);
    try {
      const res = await approvalApi.pending();
      setPendingItems(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openActionModal = (item: PendingApprovalItem, type: 'APPROVE' | 'REJECT' | 'REQUEST_INFO') => {
    setSelectedItem(item);
    setActionType(type);
    setComments('');
  };

  const handleExecuteAction = async () => {
    if (!selectedItem) return;
    if ((actionType === 'REJECT' || actionType === 'REQUEST_INFO') && !comments.trim()) {
      alert(`A comment is mandatory when performing a ${actionType} action.`);
      return;
    }

    setActionLoading(true);
    try {
      if (actionType === 'APPROVE') {
        await approvalApi.approve(selectedItem.step_id, comments || 'Approved via queue');
        setSuccessMsg(`Approved request ${selectedItem.request_id} successfully.`);
      } else if (actionType === 'REJECT') {
        await approvalApi.reject(selectedItem.step_id, comments);
        setSuccessMsg(`Rejected request ${selectedItem.request_id}. Balance/budget hold released.`);
      } else if (actionType === 'REQUEST_INFO') {
        await approvalApi.requestInfo(selectedItem.step_id, comments);
        setSuccessMsg(`Requested additional information for ${selectedItem.request_id}.`);
      }
      setSelectedItem(null);
      loadPending();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredItems = pendingItems.filter((item) => {
    if (filterType === 'ALL') return true;
    return item.request_type === filterType;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <CheckSquare className="w-5 h-5" />
            </span>
            <span>Authorized Approval Queue</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Review pending employee leave and expense requests. All actions are cryptographically signed and committed to the audit ledger.
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-white rounded-xl border border-slate-200 p-1 shadow-xs">
          {(['ALL', 'LEAVE', 'EXPENSE'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`text-xs px-3 py-1.5 rounded-lg font-bold transition ${
                filterType === t
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t === 'ALL' ? 'All Pending' : t}
            </button>
          ))}
        </div>
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2 shadow-xs">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Pending Items List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-16 text-center text-slate-400 text-xs">
            Loading approval queue...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-16 text-center text-slate-400 space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="text-sm font-bold text-slate-700">All caught up!</p>
            <p className="text-xs text-slate-400">There are no pending approvals requiring your sign-off.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredItems.map((item) => (
              <div
                key={item.step_id}
                className="p-5 hover:bg-slate-50/70 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-600">
                      <Link to={`/requests/${item.request_id}`}>{item.request_id}</Link>
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                      {item.request_type}
                    </span>
                    <span className="text-slate-300">•</span>
                    <span className="text-xs font-bold text-slate-900">{item.applicant_name}</span>
                    <span className="text-slate-400 text-xs">({item.applicant_id})</span>
                  </div>

                  <p className="text-xs text-slate-700 font-medium leading-relaxed">
                    {item.summary}
                  </p>

                  <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                    <span className="flex items-center gap-1 font-medium text-slate-600">
                      Amount/Duration: <strong className="text-slate-900">{item.request_type === 'LEAVE' ? `${item.amount_or_days} business days` : `$${item.amount_or_days.toFixed(2)}`}</strong>
                    </span>
                    <span>•</span>
                    <span>Assigned Step #{item.step_order}</span>
                    <span>•</span>
                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    to={`/visualizer?requestId=${item.request_id}`}
                    className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition border border-transparent hover:border-blue-200"
                    title="View EFCG Graph Evidence"
                  >
                    <GitBranch className="w-4 h-4" />
                  </Link>

                  <button
                    onClick={() => openActionModal(item, 'REQUEST_INFO')}
                    className="px-3 py-1.5 text-xs font-bold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition"
                  >
                    Request Info
                  </button>

                  <button
                    onClick={() => openActionModal(item, 'REJECT')}
                    className="px-3 py-1.5 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition"
                  >
                    Reject
                  </button>

                  <button
                    onClick={() => openActionModal(item, 'APPROVE')}
                    className="px-4 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-xs"
                  >
                    Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Decision Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900">
              {actionType === 'APPROVE' && 'Approve Workforce Request'}
              {actionType === 'REJECT' && 'Reject Request & Release Hold'}
              {actionType === 'REQUEST_INFO' && 'Request Additional Evidence'}
            </h3>

            <p className="text-xs text-slate-600">
              Target Request: <strong className="text-slate-900 font-mono">{selectedItem.request_id}</strong> ({selectedItem.applicant_name})
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                {actionType === 'APPROVE' ? 'Approval Notes (Optional)' : 'Mandatory Explanation / Justification'}
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                required={actionType !== 'APPROVE'}
                rows={3}
                placeholder={
                  actionType === 'APPROVE'
                    ? 'e.g. Verified project deadlines and workload coverage. Approved.'
                    : actionType === 'REJECT'
                    ? 'State exact policy grounds for rejection...'
                    : 'Specify required documentation or receipts needed...'
                }
                className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800 bg-white"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteAction}
                disabled={actionLoading}
                className={`px-4 py-2 text-xs font-bold text-white rounded-lg transition shadow-xs ${
                  actionType === 'APPROVE'
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : actionType === 'REJECT'
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : 'bg-amber-600 hover:bg-amber-700'
                }`}
              >
                {actionLoading ? 'Processing...' : `Confirm ${actionType}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
