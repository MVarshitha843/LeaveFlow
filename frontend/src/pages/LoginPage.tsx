import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/api';
import {
  Lock, Mail, ArrowRight, ShieldCheck, UserCheck, AlertCircle, CheckCircle2, Sparkles
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demoAccounts, setDemoAccounts] = useState<any[]>([]);

  useEffect(() => {
    authApi.getDemoAccounts()
      .then((res) => setDemoAccounts(res.data))
      .catch(() => {});
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.login({ email, password });
      login(res.data.access_token, res.data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (demoEmail: string) => {
    setLoading(true);
    setError(null);
    setEmail(demoEmail);
    setPassword('Password123!');
    try {
      const res = await authApi.login({ email: demoEmail, password: 'Password123!' });
      login(res.data.access_token, res.data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 bg-mesh-grid flex flex-col justify-center py-12 px-6 sm:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <Link to="/" className="inline-flex items-center gap-2.5 mb-4 group">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/25 group-hover:bg-blue-700 transition">
            LF
          </div>
          <span className="text-xl font-bold text-slate-900 tracking-tight">LeaveFlow</span>
        </Link>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">
          Sign In to Your Workspace
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Evidence-First Leave & Expense Intelligence Platform
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 sm:px-8 shadow-xl rounded-2xl border border-slate-200">
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Corporate Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="name@leaveflow.internal"
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 bg-white"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* 1-Click Demo Accounts Quick Switcher */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <div className="flex items-center gap-1.5 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span className="text-xs font-bold text-slate-900">
                1-Click Verified Demo Accounts
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mb-3">
              Click any role to log in with authentic authority credentials:
            </p>

            <div className="grid grid-cols-1 gap-2">
              {[
                { role: 'EMPLOYEE', label: 'Employee Portal', desc: 'Sarah Connor (L3 Staff)', email: 'employee@leaveflow.internal' },
                { role: 'MANAGER', label: 'Manager Portal', desc: 'David Kim (L4 Manager)', email: 'manager@leaveflow.internal' },
                { role: 'FINANCE', label: 'Finance Portal', desc: 'Claire Redfield (Finance Head)', email: 'finance@leaveflow.internal' },
                { role: 'PROCESS_OWNER', label: 'Process Owner Portal', desc: 'Marcus Sterling (HR Policy)', email: 'process.owner@leaveflow.internal' },
                { role: 'ADMIN', label: 'Admin Portal', desc: 'Eleanor Vance (System Exec)', email: 'admin@leaveflow.internal' },
              ].map((account) => (
                <button
                  key={account.role}
                  type="button"
                  onClick={() => handleQuickDemoLogin(account.email)}
                  disabled={loading}
                  className="w-full p-2.5 rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 text-left transition flex items-center justify-between group bg-slate-50/50"
                >
                  <div>
                    <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 transition">
                      {account.label}
                    </span>
                    <span className="text-[10px] text-slate-500 block">
                      {account.desc}
                    </span>
                  </div>
                  <UserCheck className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
