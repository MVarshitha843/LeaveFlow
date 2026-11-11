import React from 'react';
import {
  FileText, Download, ShieldCheck, Database, Calendar, CreditCard,
  ShieldAlert, Lock
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const reports = [
    {
      title: 'Leave Requests Export (CSV)',
      desc: 'All historical and active employee leave applications, business days, and EFCG outcomes.',
      url: '/api/reports/leave-csv',
      filename: 'leaveflow_leave_requests.csv',
      icon: Calendar,
      color: 'text-blue-600 bg-blue-50 border-blue-200',
    },
    {
      title: 'Expense Claims Export (CSV)',
      desc: 'Comprehensive expense claims register with merchants, cost centers, and receipt hashes.',
      url: '/api/reports/expense-csv',
      filename: 'leaveflow_expense_claims.csv',
      icon: CreditCard,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-200',
    },
    {
      title: 'Tamper-Evident Audit Ledger (CSV)',
      desc: 'Cryptographic append-only SHA-256 block chain record for external regulatory audits.',
      url: '/api/reports/audit-csv',
      filename: 'leaveflow_audit_trail.csv',
      icon: ShieldCheck,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-200',
    },
    {
      title: 'Surveillance Anomaly Register (CSV)',
      desc: 'Complete register of 12 anomaly classifications, detection methods, and review states.',
      url: '/api/reports/anomalies-csv',
      filename: 'leaveflow_anomalies.csv',
      icon: ShieldAlert,
      color: 'text-amber-600 bg-amber-50 border-amber-200',
    },
    {
      title: 'Ground Truth Anomaly Manifest (JSON)',
      desc: 'Restricted evaluation export of seeded ground truth labels. Kept isolated from decision engine.',
      url: '/api/reports/ground-truth',
      filename: 'ground_truth_manifest.json',
      icon: Lock,
      color: 'text-rose-600 bg-rose-50 border-rose-200',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
            <FileText className="w-5 h-5" />
          </span>
          <span>Operational Reports & Regulatory Data Exports</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          One-click downloads of verified operational datasets in structured CSV and JSON formats.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((r, idx) => {
          const Icon = r.icon;
          return (
            <div
              key={idx}
              className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between hover-card-elevate"
            >
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl border ${r.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{r.title}</h3>
                    <span className="text-[10px] font-mono text-slate-400 font-semibold">{r.filename}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{r.desc}</p>
              </div>

              <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-medium">Ready to download</span>
                <a
                  href={r.url}
                  download={r.filename}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-xs"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
