import { useState } from 'react';
import {
  LayoutDashboard, ClipboardList, Users, FileText, Flame,
  BarChart3, Cpu, ScrollText, Settings, GitBranch,
  ChevronLeft, ChevronRight, Activity, Wifi, LogOut
} from 'lucide-react';
import type { User } from '../types/api';

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  userRole: string;
  user: User | null;
  onLogout: () => void;
}

const doctorNav = [
  { id: 'dashboard',       icon: LayoutDashboard, label: 'Dashboard',         group: 'main' },
  { id: 'review-queue',    icon: ClipboardList,   label: 'Review Queue',       group: 'main', badge: 'live' as const },
  { id: 'patient-history', icon: Users,           label: 'Patient History',    group: 'main' },
  { id: 'clinical-notes',  icon: FileText,        label: 'Clinical Notes',     group: 'main' },
  { id: 'fhir-inspector',  icon: Flame,           label: 'FHIR Inspector',     group: 'tools' },
  { id: 'knowledge-graph', icon: GitBranch,       label: 'Knowledge Graph',    group: 'tools' },
  { id: 'analytics',       icon: BarChart3,       label: 'Analytics',          group: 'tools' },
  { id: 'ai-monitor',      icon: Cpu,             label: 'AI Monitor',         group: 'tools', badge: 'live' as const },
  { id: 'audit-logs',      icon: ScrollText,      label: 'Audit Logs',         group: 'system' },
  { id: 'settings',        icon: Settings,        label: 'Settings',           group: 'system' },
];

const patientNav = [
  { id: 'patient-portal',  icon: LayoutDashboard, label: 'My Portal',          group: 'main' },
  { id: 'submit-note',     icon: FileText,        label: 'Submit Note',        group: 'main' },
  { id: 'my-history',      icon: Users,           label: 'My History',         group: 'main' },
];

export const Sidebar = ({ activePage, onNavigate, userRole, user, onLogout }: SidebarProps) => {
  const [collapsed, setCollapsed] = useState(false);
  const nav = userRole === 'patient' ? patientNav : doctorNav;
  const groups = [...new Set(nav.map(n => n.group))];

  return (
    <aside
      className={`flex-shrink-0 flex flex-col h-full transition-all duration-300 ease-in-out relative z-10 ${collapsed ? 'w-[60px]' : 'w-[220px]'}`}
      style={{ background: 'rgba(13,20,33,0.9)', borderRight: '1px solid var(--border)', backdropFilter: 'blur(20px)' }}
    >
      {/* Logo */}
      <div className={`flex items-center gap-3 py-5 ${collapsed ? 'justify-center px-0' : 'px-4'} border-b border-[var(--border)]`}>
        <div className="w-8 h-8 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)', boxShadow: '0 4px 12px rgba(0,212,255,0.3)' }}>
          🏥
        </div>
        {!collapsed && (
          <div>
            <div className="text-sm font-bold text-[var(--text-primary)] tracking-tight">ClinicalAI</div>
            <div className="text-[10px] font-semibold" style={{ color: 'var(--teal)' }}>Enterprise v8.0</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 space-y-0.5 px-2">
        {groups.map(group => (
          <div key={group}>
            {!collapsed && (
              <p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[var(--text-dim)] px-2 pt-4 pb-1.5">
                {group}
              </p>
            )}
            {nav.filter(n => n.group === group).map(item => {
              const Icon = item.icon;
              const active = activePage === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-${item.id}`}
                  onClick={() => onNavigate(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={`w-full flex items-center gap-2.5 rounded-xl py-2 text-sm font-medium transition-all duration-150 relative group
                    ${collapsed ? 'justify-center px-0' : 'px-3'}
                    ${active
                      ? 'text-[var(--teal)]'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  style={active ? {
                    background: 'rgba(0,212,255,0.08)',
                    border: '1px solid rgba(0,212,255,0.18)',
                    boxShadow: '0 0 12px rgba(0,212,255,0.06)'
                  } : { background: 'transparent', border: '1px solid transparent' }}
                >
                  {active && !collapsed && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r-full" style={{ background: 'var(--teal)' }} />
                  )}
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {!collapsed && <span className="flex-1 text-left text-[13px] truncate">{item.label}</span>}
                  {!collapsed && (item as any).badge === 'live' && (
                    <span className="badge badge-teal text-[8px] py-0.5">LIVE</span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Status strip */}
      {!collapsed && (
        <div className="px-3 py-3 border-t border-[var(--border)] space-y-1.5">
          <div className="flex items-center gap-1.5">
            <span className="relative flex w-2 h-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: 'var(--success)' }} />
              <span className="relative inline-flex rounded-full w-2 h-2" style={{ background: 'var(--success)' }} />
            </span>
            <span className="text-[10px] font-semibold" style={{ color: 'var(--success)' }}>All Systems Online</span>
          </div>
          <div className="space-y-1 text-[10px] text-[var(--text-dim)]">
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-1"><Activity className="w-2.5 h-2.5" />FastAPI Backend</span>
              <span style={{ color: 'var(--success)' }}>●</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-1"><Wifi className="w-2.5 h-2.5" />AI Pipeline</span>
              <span style={{ color: 'var(--success)' }}>●</span>
            </div>
          </div>
        </div>
      )}

      {/* User + logout */}
      {!collapsed && user && (
        <div className="px-3 pb-3 border-t border-[var(--border)] pt-2">
          <div className="flex items-center gap-2 p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-[#060B14] flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>
              {(user.full_name || user.username).charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[11px] font-semibold text-[var(--text-primary)] truncate">{user.full_name || user.username}</div>
              <div className="text-[9px] font-bold uppercase tracking-wide" style={{ color: 'var(--teal)' }}>{user.role}</div>
            </div>
            <button onClick={onLogout} title="Sign out" className="text-[var(--text-muted)] hover:text-[var(--danger)] transition-colors">
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center py-3 border-t border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--teal)] transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </aside>
  );
};
