import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { PatientHistoryPage } from './pages/PatientHistoryPage';
import { ClinicalNotesPage } from './pages/ClinicalNotesPage';
import { FhirInspectorPage } from './pages/FhirInspectorPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AiMonitorPage } from './pages/AiMonitorPage';
import { PatientPortalPage } from './pages/PatientPortalPage';
import { getHealthApi } from './services/api';
import { GitBranch, ScrollText, Settings } from 'lucide-react';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

const PlaceholderPage = ({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) => (
  <div className="glass flex flex-col items-center justify-center gap-5 h-full min-h-[400px] text-center p-12">
    <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)' }}>
      {icon}
    </div>
    <div>
      <p className="text-lg font-bold text-[var(--text-primary)]">{title}</p>
      <p className="text-sm text-[var(--text-muted)] mt-1 max-w-sm">{description}</p>
    </div>
    <span className="badge badge-violet">Coming Soon</span>
  </div>
);

function App() {
  const { isAuthenticated, user, logout } = useAuth();
  const [activePage, setActivePage] = useState(() =>
    user?.role === 'patient' ? 'patient-portal' : 'dashboard'
  );
  const [backendOnline, setBackendOnline] = useState(false);

  // Poll backend health every 30s
  const checkHealth = useCallback(async () => {
    try { await getHealthApi(); setBackendOnline(true); }
    catch { setBackendOnline(false); }
  }, []);

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 30_000);
    return () => clearInterval(id);
  }, [checkHealth]);

  if (!isAuthenticated) return <LoginPage />;

  const renderPage = () => {
    // Patient role
    if (user?.role === 'patient') {
      if (activePage === 'submit-note') return <ClinicalNotesPage />;
      if (activePage === 'my-history') return <PatientHistoryPage patientView />;
      return <PatientPortalPage />;
    }

    // Doctor role
    switch (activePage) {
      case 'dashboard':       return <DashboardPage />;
      case 'review-queue':    return <ReviewQueuePage />;
      case 'patient-history': return <PatientHistoryPage />;
      case 'clinical-notes':  return <ClinicalNotesPage />;
      case 'fhir-inspector':  return <FhirInspectorPage />;
      case 'analytics':       return <AnalyticsPage />;
      case 'ai-monitor':      return <AiMonitorPage backendOnline={backendOnline} />;
      case 'knowledge-graph': return (
        <PlaceholderPage icon={<GitBranch className="w-8 h-8 text-[var(--violet)]" />}
          title="Knowledge Graph" description="Interactive entity relationship network — ReactFlow integration in the next release." />
      );
      case 'audit-logs': return (
        <PlaceholderPage icon={<ScrollText className="w-8 h-8 text-[var(--teal)]" />}
          title="Audit Logs" description="Full immutable audit trail with HIPAA-compliant log retention — coming in v8.1." />
      );
      case 'settings': return (
        <PlaceholderPage icon={<Settings className="w-8 h-8 text-[var(--text-muted)]" />}
          title="Platform Settings" description="API endpoint configuration, AI pipeline tuning, and notification preferences." />
      );
      default: return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden relative" style={{ background: 'var(--bg-base)' }}>
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        userRole={user?.role ?? 'doctor'}
        user={user}
        onLogout={logout}
      />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <div className="px-4 pt-4">
          <Header user={user} backendOnline={backendOnline} />
        </div>
        <main className="flex-1 overflow-auto px-4 pb-4">
          <ErrorBoundary key={activePage}>
            {renderPage()}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

export default App;
