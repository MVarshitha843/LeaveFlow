import React, { useState, useEffect } from 'react';
import { auditApi } from '../services/api';
import { AuditEvent } from '../types';
import {
  ShieldCheck, ShieldAlert, CheckCircle2, RefreshCw, Key,
  Lock, ArrowRight, FileText, Database, Copy, Check
} from 'lucide-react';

export const AuditLedgerPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const res = await auditApi.events({ limit: 50 });
      setEvents(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyIntegrity = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await auditApi.verify();
      setVerificationResult(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Verification request failed');
    } finally {
      setVerifying(false);
    }
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <ShieldCheck className="w-5 h-5" />
            </span>
            <span>Tamper-Evident Hash Audit Ledger</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Application-level append-only cryptographic hash chain. Any retroactive database modification or payload deletion breaks the block chain.
          </p>
        </div>

        <button
          onClick={handleVerifyIntegrity}
          disabled={verifying}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-md shadow-blue-600/20 flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
          <span>{verifying ? 'Verifying Chain...' : 'Verify Cryptographic Integrity'}</span>
        </button>
      </div>

      {/* Verification Status Card */}
      {verificationResult && (
        <div
          className={`p-5 rounded-2xl border shadow-xs ${
            verificationResult.is_valid
              ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950'
              : 'bg-rose-50 border-rose-300 text-rose-950'
          }`}
        >
          <div className="flex items-start gap-3">
            {verificationResult.is_valid ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            )}
            <div className="space-y-1 text-xs">
              <h4 className="text-sm font-bold">
                {verificationResult.is_valid
                  ? 'Cryptographic Verification Passed — Zero Tampering Detected'
                  : 'INTEGRITY ALERT: Chain Pointer or Payload Compromised!'}
              </h4>
              <p className="text-xs leading-relaxed">{verificationResult.message}</p>
              <div className="pt-2 flex flex-wrap gap-4 text-[11px] font-mono">
                <span>Total Checked: <strong>{verificationResult.total_events}</strong> events</span>
                {verificationResult.head_hash && (
                  <span className="truncate max-w-sm">
                    Head Hash: <strong className="text-blue-700">{verificationResult.head_hash.slice(0, 24)}...</strong>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Events Stream */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Chronological Hash-Linked Blocks
          </span>
          <span className="text-[11px] text-slate-400">
            Genesis Hash: <strong className="font-mono text-slate-600">00000000...</strong>
          </span>
        </div>

        {loading ? (
          <div className="p-16 text-center text-slate-400 text-xs">Loading ledger blocks...</div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">Ledger is empty.</div>
        ) : (
          <div className="space-y-3">
            {events.map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-xs transition text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 font-mono font-bold flex items-center justify-center text-[10px]">
                      #{ev.id}
                    </span>
                    <span className="font-bold text-slate-900">{ev.action}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {ev.entity_type}: {ev.entity_id}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(ev.timestamp).toLocaleString()}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-slate-200 font-mono text-[11px] text-slate-700 break-all">
                  {ev.payload_json}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px] font-mono pt-1 text-slate-500">
                  <div className="truncate bg-slate-100 p-1.5 rounded border border-slate-200/60">
                    <span className="text-slate-400 font-sans font-bold">PREV HASH: </span>
                    {ev.previous_hash}
                  </div>
                  <div className="truncate bg-blue-50/80 p-1.5 rounded text-blue-900 border border-blue-200/60 flex items-center justify-between">
                    <span className="truncate"><span className="text-blue-500 font-sans font-bold">BLOCK HASH: </span>{ev.current_hash}</span>
                    <button
                      onClick={() => copyHash(ev.current_hash)}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                      title="Copy Hash"
                    >
                      {copiedHash === ev.current_hash ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
