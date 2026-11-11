import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { expenseApi, employeeApi } from '../services/api';
import { ExpensePolicy, CostCenter, ExpenseLine } from '../types';
import {
  CreditCard, Upload, Plus, Trash2, ArrowRight, AlertTriangle,
  CheckCircle2, XCircle, ShieldCheck, DollarSign, FileText, Sparkles, Building
} from 'lucide-react';

export const ExpenseSubmitPage: React.FC = () => {
  const navigate = useNavigate();

  const [policies, setPolicies] = useState<ExpensePolicy[]>([]);
  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [category, setCategory] = useState('TRAVEL');
  const [costCenterId, setCostCenterId] = useState('');
  const [merchant, setMerchant] = useState('');
  const [claimDate, setClaimDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [receiptUrl, setReceiptUrl] = useState('');
  const [receiptHash, setReceiptHash] = useState('');
  const [uploadingReceipt, setUploadingReceipt] = useState(false);

  // Multi-line expense items
  const [lines, setLines] = useState<{ category: string; description: string; amount: number }[]>([
    { category: 'TRAVEL', description: '', amount: 0 }
  ]);

  const [dryRunResult, setDryRunResult] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    loadPoliciesAndCostCenters();
  }, []);

  const loadPoliciesAndCostCenters = async () => {
    try {
      const [pRes, cRes] = await Promise.all([
        expenseApi.policies(),
        employeeApi.costCenters(),
      ]);
      setPolicies(pRes.data);
      setCostCenters(cRes.data);
      if (cRes.data.length > 0) {
        setCostCenterId(cRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const totalAmount = lines.reduce((sum, l) => sum + (Number(l.amount) || 0), 0);

  // Compute SHA-256 client-side and upload receipt to authoritative backend
  const handleReceiptChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setReceiptFile(file);
      setUploadingReceipt(true);
      setError(null);

      try {
        // 1. Client-side SHA-256 fingerprinting for immediate preview
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        setReceiptHash(hashHex);

        // 2. Authoritative Server upload
        const formData = new FormData();
        formData.append('file', file);
        const upRes = await expenseApi.uploadReceipt(formData);
        setReceiptUrl(upRes.data.receipt_url);
      } catch (err) {
        setError('Failed to process and upload receipt file.');
      } finally {
        setUploadingReceipt(false);
      }
    }
  };

  // Trigger dry-run EFCG check when key fields change
  useEffect(() => {
    if (costCenterId && merchant && totalAmount > 0) {
      triggerDryRun();
    } else {
      setDryRunResult(null);
    }
  }, [costCenterId, category, merchant, claimDate, totalAmount, receiptHash]);

  const triggerDryRun = async () => {
    try {
      const res = await expenseApi.dryRun({
        cost_center_id: costCenterId,
        category,
        merchant,
        claim_date: claimDate,
        total_amount: totalAmount,
        description: description || 'Business claim',
        receipt_url: receiptUrl || undefined,
        receipt_hash: receiptHash || undefined,
      });
      setDryRunResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const addLine = () => {
    setLines([...lines, { category, description: '', amount: 0 }]);
  };

  const removeLine = (idx: number) => {
    if (lines.length > 1) {
      setLines(lines.filter((_, i) => i !== idx));
    }
  };

  const updateLine = (idx: number, field: string, val: any) => {
    const updated = [...lines];
    (updated[idx] as any)[field] = val;
    setLines(updated);
  };

  const handleSubmit = async () => {
    setShowSummary(false);
    setSubmitting(true);
    setError(null);
    try {
      const res = await expenseApi.submit({
        cost_center_id: costCenterId,
        category,
        merchant,
        claim_date: claimDate,
        total_amount: totalAmount,
        description,
        receipt_url: receiptUrl || undefined,
        receipt_hash: receiptHash || undefined,
        lines: lines.map((l) => ({
          category: l.category,
          description: l.description || description || 'Expense item',
          amount: l.amount,
        })),
      });
      navigate(`/requests/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit expense claim');
      setSubmitting(false);
    }
  };

  const selectedPolicy = policies.find((p) => p.category === category);
  const selectedCostCenter = costCenters.find((c) => c.id === costCenterId);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <CreditCard className="w-5 h-5" />
            </span>
            <span>Submit Expense Claim</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Itemized business expenses evaluated with authoritative backend SHA-256 receipt validation and split-claim heuristics.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
          <span>EFCG Constraint Engine Active</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2 shadow-xs">
          <XCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Form Column */}
        <div className="md:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Expense Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full text-xs py-2.5 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
              >
                {policies.map((p) => (
                  <option key={p.id} value={p.category}>
                    {p.category} (Limit: ${p.max_per_claim.toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Target Cost Center
              </label>
              <select
                value={costCenterId}
                onChange={(e) => setCostCenterId(e.target.value)}
                className="w-full text-xs py-2.5 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
              >
                {costCenters.map((cc) => (
                  <option key={cc.id} value={cc.id}>
                    {cc.code} - {cc.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Merchant / Vendor
              </label>
              <input
                type="text"
                value={merchant}
                onChange={(e) => setMerchant(e.target.value)}
                required
                placeholder="e.g. United Airlines, AWS, Hilton"
                className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Date of Expense
              </label>
              <input
                type="date"
                value={claimDate}
                onChange={(e) => setClaimDate(e.target.value)}
                required
                className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Business Purpose / Justification
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="e.g. Travel to client site for technical onboarding"
              className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
            />
          </div>

          {/* Line Items Section */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Itemized Line Breakdown
              </label>
              <button
                type="button"
                onClick={addLine}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-2.5">
              {lines.map((line, idx) => (
                <div key={idx} className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs font-mono font-bold text-slate-400">#{idx + 1}</span>
                  <input
                    type="text"
                    value={line.description}
                    onChange={(e) => updateLine(idx, 'description', e.target.value)}
                    placeholder="Line description"
                    className="flex-1 text-xs py-1.5 px-2.5 rounded-lg border border-slate-300 bg-white text-slate-800"
                  />
                  <div className="relative w-32">
                    <span className="absolute left-2.5 top-1.5 text-xs text-slate-400 font-bold">$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={line.amount || ''}
                      onChange={(e) => updateLine(idx, 'amount', parseFloat(e.target.value) || 0)}
                      placeholder="0.00"
                      className="w-full text-xs py-1.5 pl-6 pr-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 font-bold tabular-nums"
                    />
                  </div>
                  {lines.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeLine(idx)}
                      className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end items-center gap-2 mt-3 pt-2 border-t border-slate-100 text-xs">
              <span className="text-slate-500 font-medium">Cumulative Claim Total:</span>
              <span className="text-base font-extrabold text-slate-900 tabular-nums">
                ${totalAmount.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Receipt Upload & Cryptographic Fingerprinting */}
          <div className="p-4 rounded-xl border border-dashed border-slate-300 bg-slate-50/60 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <Upload className="w-4 h-4 text-blue-600" />
                <span>Receipt Upload & SHA-256 Fingerprint</span>
              </label>
              {receiptHash && (
                <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                  SHA-256 Fingerprinted
                </span>
              )}
            </div>

            <input
              type="file"
              accept="image/*,.pdf"
              onChange={handleReceiptChange}
              className="text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
            />

            {receiptHash && (
              <div className="text-[10px] font-mono text-slate-600 break-all bg-white p-2.5 rounded-lg border border-slate-200">
                <span className="font-bold text-slate-800">Digest: </span>{receiptHash}
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => setShowSummary(true)}
            disabled={!merchant || totalAmount <= 0 || submitting}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span>Review Claim & Check Constraints</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Right Column: EFCG Live Feedback */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Cost Center Budget Headroom
            </span>
            <div className="text-2xl font-extrabold text-slate-900 tabular-nums">
              ${selectedCostCenter ? selectedCostCenter.available_spend.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
            </div>
            <p className="text-[11px] text-slate-500">
              {selectedCostCenter?.code} - {selectedCostCenter?.name}
            </p>
          </div>

          {dryRunResult && (
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">EFCG Pre-Validation</span>
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

              <div className="space-y-1.5 text-xs">
                {dryRunResult.evaluation.nodes.map((node: any) => (
                  <div key={node.id} className="flex items-center justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-700 font-medium">{node.name}</span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        node.status === 'PASS'
                          ? 'text-emerald-700 bg-emerald-50'
                          : node.status === 'FAIL'
                          ? 'text-rose-700 bg-rose-50'
                          : 'text-amber-700 bg-amber-50'
                      }`}
                    >
                      {node.status}
                    </span>
                  </div>
                ))}
              </div>

              <p className="text-[11px] text-slate-600 leading-relaxed pt-2">
                {dryRunResult.evaluation.explanation}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showSummary && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900">
              Confirm Expense Submission
            </h3>
            <div className="space-y-2 p-3 bg-slate-50 rounded-xl text-xs text-slate-700 border border-slate-100">
              <div className="flex justify-between">
                <span className="text-slate-500">Merchant:</span>
                <span className="font-semibold">{merchant}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Cost Center:</span>
                <span className="font-semibold">{selectedCostCenter?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Total Claim:</span>
                <span className="font-bold text-blue-600">${totalAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Receipt SHA-256:</span>
                <span className="font-mono text-[10px] truncate max-w-[180px]">{receiptHash || 'None'}</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowSummary(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition shadow-xs"
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
