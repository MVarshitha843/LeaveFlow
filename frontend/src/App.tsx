import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';

// Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { EmployeeDashboard } from './pages/EmployeeDashboard';
import { LeaveApplyPage } from './pages/LeaveApplyPage';
import { ExpenseSubmitPage } from './pages/ExpenseSubmitPage';
import { RequestTrackingPage } from './pages/RequestTrackingPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { FinancePage } from './pages/FinancePage';
import { VisualizerPage } from './pages/VisualizerPage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { PolicyGovernancePage } from './pages/PolicyGovernancePage';
import { AuditLedgerPage } from './pages/AuditLedgerPage';
import { EmployeeDirectoryPage } from './pages/EmployeeDirectoryPage';
import { ReportsPage } from './pages/ReportsPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white text-xs font-mono">
        Authenticating LeaveFlow Session...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Landing & Auth */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Dashboard Shell */}
          <Route
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<EmployeeDashboard />} />
            <Route path="/leave/apply" element={<LeaveApplyPage />} />
            <Route path="/expenses/submit" element={<ExpenseSubmitPage />} />
            <Route path="/requests" element={<RequestTrackingPage />} />
            <Route path="/requests/:id" element={<RequestTrackingPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/finance" element={<FinancePage />} />
            <Route path="/visualizer" element={<VisualizerPage />} />
            <Route path="/anomalies" element={<AnomaliesPage />} />
            <Route path="/policies" element={<PolicyGovernancePage />} />
            <Route path="/audit" element={<AuditLedgerPage />} />
            <Route path="/employees" element={<EmployeeDirectoryPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
