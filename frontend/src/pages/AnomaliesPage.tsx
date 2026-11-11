import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { anomalyApi } from '../services/api';
import { AnomalyAlert } from '../types';
import {
  ShieldAlert, AlertTriangle, CheckCircle2, XCircle, RefreshCw,
  Search, Filter, ArrowRight, Eye, ShieldCheck, Clock
} from 'lucide-react';

export const AnomaliesPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [selectedAlert, setSelectedAlert] = useState<AnomalyAlert | null>(null);
  const [reviewStatus, setReviewStatus] = useState<string>('CONFIRMED');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [updating, setUpdating] = useState(false);
  const [bannerMsg, setBannerMsg] = useState<string | null>(null);

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, severityFilter]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (severityFilter !== 'ALL') params.severity = severityFilter;
      const res = await anomalyApi.list(params);
      setAlerts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSystemScan = async () => {
    setScanning(true);
    setBannerMsg(null);
    try {
      const res = await anomalyApi.scan();
      setBannerMsg(res.data.message);
      loadAlerts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedAlert) return;
    setUpdating(true);
    try {
      await anomalyApi.review(selectedAlert.id, reviewStatus, reviewNotes);
      setBannerMsg(`Alert #${selectedAlert.id} updated to ${reviewStatus}`);
      setSelectedAlert(null);
      loadAlerts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Status update failed');
    } finally {
      setUpdating(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300 font-bold';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-300 font-medium';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-600" />
            <span>Continuous Anomaly Review Queue</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            12-category automated surveillance scanning: split claims, duplicate hashes, schedule overlaps, and tenure boundaries.
          </p>
        </div>

        <button
          onClick={handleRunSystemScan}
          disabled={scanning}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-md shadow-blue-600/20 flex items-center gap-2 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
          <span>{scanning ? 'Scanning System...' : 'Trigger Full Audit Scan'}</span>
        </button>
      </div>

      {bannerMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{bannerMsg}</span>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 bg-white text-slate-700"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="UNDER_REVIEW">UNDER_REVIEW</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="DISMISSED">DISMISSED</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 bg-white text-slate-700"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>

        <span className="text-xs text-slate-400 font-semibold">
          Showing {alerts.length} detected anomaly alert(s)
        </span>
      </div>

      {/* Anomaly Alerts Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-16 text-center text-slate-400 text-xs">
            Scanning and loading anomaly records...
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-16 text-center text-slate-400 space-y-2">
            <ShieldCheck className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="text-sm font-semibold text-slate-700">Clean Surveillance State</p>
            <p className="text-xs text-slate-400">No matching anomaly alerts found for current filter criteria.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {alerts.map((a) => (
              <div
                key={a.id}
                className="p-5 hover:bg-slate-50 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded border uppercase ${getSeverityBadge(a.severity)}`}>
                      {a.severity}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-900">
                      {a.anomaly_type.replace(/_/g, ' ')}
                    </span>
                    {a.request_id && (
                      <>
                        <span className="text-slate-300">•</span>
                        <Link
                          to={`/requests/${a.request_id}`}
                          className="font-mono text-xs font-semibold text-blue-600 hover:underline"
                        >
                          {a.request_id}
                        </Link>
                      </>
                    )}
                  </div>

                  <p className="text-xs text-slate-800 leading-relaxed font-medium">
                    {a.explanation}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 pt-0.5">
                    <span>Detection Method: <strong className="text-slate-600">{a.detection_method}</strong></span>
                    <span>•</span>
                    <span>Status: <strong className="text-slate-700 uppercase">{a.status}</strong></span>
                    <span>•</span>
                    <span>{new Date(a.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => {
                      setSelectedAlert(a);
                      setReviewStatus(a.status);
                      setReviewNotes('');
                    }}
                    className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                  >
                    Inspect & Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail / Review Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">
                Anomaly Alert Investigation #{selectedAlert.id}
              </h3>
              <span className={`text-[10px] px-2 py-0.5 rounded border uppercase ${getSeverityBadge(selectedAlert.severity)}`}>
                {selectedAlert.severity}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Anomaly Explanation
                </span>
                <p className="text-slate-800 leading-relaxed">{selectedAlert.explanation}</p>
              </div>

              {selectedAlert.suggested_action && (
                <div className="p-3 bg-blue-50/60 border border-blue-200/60 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block">
                    Recommended Remediation
                  </span>
                  <p className="text-blue-950 font-medium leading-relaxed">{selectedAlert.suggested_action}</p>
                </div>
              )}

              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Captured Verifiable Evidence (JSON)
                </span>
                <pre className="p-3 rounded-xl bg-slate-900 text-emerald-400 font-mono text-[11px] overflow-x-auto">
                  {JSON.stringify(JSON.parse(selectedAlert.evidence_json), null, 2)}
                </pre>
              </div>

              {/* Status Updater */}
              <div className="pt-2 border-t border-slate-200 space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Set Surveillance Review State
                  </label>
                  <select
                    value={reviewStatus}
                    onChange={(e) => setReviewStatus(e.target.value)}
                    className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 text-slate-800"
                  >
                    <option value="OPEN">OPEN (Unreviewed)</option>
                    <option value="UNDER_REVIEW">UNDER_REVIEW (Active Investigation)</option>
                    <option value="CONFIRMED">CONFIRMED (Confirmed Policy Variance)</option>
                    <option value="DISMISSED">DISMISSED (False Positive / Authorized)</option>
                    <option value="RESOLVED">RESOLVED (Remediation Executed)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Reviewer Notes / Case History
                  </label>
                  <textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    rows={2}
                    placeholder="Enter audit remarks..."
                    className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 text-slate-800"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleUpdateStatus}
                disabled={updating}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition shadow"
              >
                {updating ? 'Saving...' : 'Update Status'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
