import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { notificationApi } from '../services/api';
import { NotificationItem } from '../types';
import {
  Calendar, CreditCard, CheckSquare, ShieldAlert, GitBranch,
  BarChart3, Settings, Users, LogOut, Bell, Menu, X, ChevronDown,
  Layers, FileText, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck,
  Building, Sparkles
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { user, logout, switchRoleLogin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotifications = async () => {
    try {
      const [listRes, countRes] = await Promise.all([
        notificationApi.list(),
        notificationApi.unreadCount(),
      ]);
      setNotifications(listRes.data);
      setUnreadCount(countRes.data.unread_count);
    } catch (err) {
      // Ignore polling errors
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: 1 })));
    } catch (err) {
      console.error(err);
    }
  };

  const navItems = [
    { label: 'Overview', path: '/dashboard', icon: BarChart3, roles: ['EMPLOYEE', 'MANAGER', 'FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Apply Leave', path: '/leave/apply', icon: Calendar, roles: ['EMPLOYEE', 'MANAGER', 'FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Submit Expense', path: '/expenses/submit', icon: CreditCard, roles: ['EMPLOYEE', 'MANAGER', 'FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'My Requests', path: '/requests', icon: Layers, roles: ['EMPLOYEE', 'MANAGER', 'FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Approval Queue', path: '/approvals', icon: CheckSquare, roles: ['MANAGER', 'FINANCE', 'ADMIN'] },
    { label: 'Finance & Budgets', path: '/finance', icon: Building, roles: ['FINANCE', 'ADMIN'] },
    { label: 'EFCG Graph Visualizer', path: '/visualizer', icon: GitBranch, roles: ['EMPLOYEE', 'MANAGER', 'FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Anomaly Review Queue', path: '/anomalies', icon: ShieldAlert, roles: ['FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Policy Governance', path: '/policies', icon: Settings, roles: ['PROCESS_OWNER', 'ADMIN'] },
    { label: 'Audit Hash Ledger', path: '/audit', icon: ShieldCheck, roles: ['FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Team Directory', path: '/employees', icon: Users, roles: ['MANAGER', 'PROCESS_OWNER', 'ADMIN'] },
    { label: 'Reports & Exports', path: '/reports', icon: FileText, roles: ['MANAGER', 'FINANCE', 'PROCESS_OWNER', 'ADMIN'] },
  ];

  const filteredNav = navItems.filter((item) =>
    user?.role ? item.roles.includes(user.role) : false
  );

  const demoRoles = [
    { role: 'EMPLOYEE', email: 'employee@leaveflow.internal', label: 'Employee Portal' },
    { role: 'MANAGER', email: 'manager@leaveflow.internal', label: 'Manager Portal' },
    { role: 'FINANCE', email: 'finance@leaveflow.internal', label: 'Finance Portal' },
    { role: 'PROCESS_OWNER', email: 'process.owner@leaveflow.internal', label: 'Process Owner Portal' },
    { role: 'ADMIN', email: 'admin@leaveflow.internal', label: 'Admin Portal' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-slate-900 border-r border-slate-800 text-slate-300 select-none shrink-0">
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 font-bold">
              LF
            </div>
            <div>
              <span className="font-bold text-base text-white tracking-tight">LeaveFlow</span>
              <span className="ml-1.5 text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
                EFCG
              </span>
            </div>
          </Link>
        </div>

        {/* User Card */}
        <div className="p-4 mx-3 my-3 bg-slate-800/60 rounded-xl border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-semibold text-sm">
              {user?.first_name[0]}{user?.last_name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="text-[10px] font-mono text-blue-400 font-medium">
                  {user?.id}
                </span>
                <span className="text-slate-600">•</span>
                <span className="text-[10px] uppercase font-semibold text-slate-400">
                  {user?.role.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto py-2">
          {filteredNav.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  active
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Role Quick Switcher in Sidebar footer */}
        <div className="p-3 border-t border-slate-800">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold px-2 mb-2">
            Switch Persona (1-Click)
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {demoRoles.map((dr) => (
              <button
                key={dr.role}
                onClick={() => switchRoleLogin(dr.email)}
                className={`text-[10px] py-1.5 px-2 rounded text-left truncate transition ${
                  user?.role === dr.role
                    ? 'bg-blue-500/20 text-blue-300 font-semibold border border-blue-500/40'
                    : 'bg-slate-800/40 hover:bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {dr.role.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            onClick={logout}
            className="w-full mt-3 flex items-center justify-center gap-2 py-2 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 rounded-lg transition"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                LeaveFlow Intelligence
              </span>
              <span className="text-slate-300">/</span>
              <span className="text-sm font-bold text-slate-800 capitalize">
                {location.pathname.replace('/', '').replace('-', ' ') || 'Dashboard'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Quick Portal Switcher dropdown */}
            <div className="relative">
              <button
                onClick={() => setRoleMenuOpen(!roleMenuOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition shadow-sm"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Active: <strong className="text-blue-600 font-semibold">{user?.role}</strong></span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {roleMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-slate-200 py-1.5 z-50">
                  <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                    Switch Test Account
                  </div>
                  {demoRoles.map((dr) => (
                    <button
                      key={dr.role}
                      onClick={() => {
                        setRoleMenuOpen(false);
                        switchRoleLogin(dr.email);
                      }}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-slate-50 flex items-center justify-between text-slate-700"
                    >
                      <span className="font-medium">{dr.label}</span>
                      {user?.role === dr.role && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-white">
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Drawer Popover */}
              {notifOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-2xl border border-slate-200 z-50 overflow-hidden">
                  <div className="px-4 py-3 bg-slate-900 text-white flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bell className="w-4 h-4 text-blue-400" />
                      <span className="text-xs font-bold uppercase tracking-wider">Notifications</span>
                    </div>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllRead}
                        className="text-[11px] text-blue-300 hover:text-white transition font-medium"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div className="max-h-96 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <div className="p-8 text-center text-xs text-slate-400">
                        No notifications yet. You're completely up to date!
                      </div>
                    ) : (
                      notifications.slice(0, 15).map((n) => (
                        <div
                          key={n.id}
                          onClick={() => {
                            if (n.link_url) navigate(n.link_url);
                            setNotifOpen(false);
                          }}
                          className={`p-3.5 text-xs hover:bg-slate-50 cursor-pointer transition ${
                            n.is_read === 0 ? 'bg-blue-50/50' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-slate-800">{n.title}</span>
                            <span className="text-[10px] text-slate-400">
                              {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-slate-600 text-xs leading-relaxed">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
