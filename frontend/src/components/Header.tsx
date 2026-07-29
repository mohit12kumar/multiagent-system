import { useState, useEffect } from 'react';
import { Bell, Search, Clock } from 'lucide-react';
import type { User } from '../types/api';

interface HeaderProps {
  user: User | null;
  backendOnline: boolean;
}

export const Header = ({ user, backendOnline }: HeaderProps) => {
  const [time, setTime] = useState('');
  const [showNotif, setShowNotif] = useState(false);

  useEffect(() => {
    const tick = () => setTime(new Date().toUTCString().slice(0, 25));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header
      className="flex items-center justify-between px-5 py-3 rounded-2xl mb-4 relative z-20"
      style={{
        background: 'rgba(13,20,33,0.85)',
        border: '1px solid var(--border)',
        backdropFilter: 'blur(20px)',
        boxShadow: '0 4px 32px rgba(0,0,0,0.4)'
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)', boxShadow: '0 4px 12px rgba(0,212,255,0.25)' }}>
          🏥
        </div>
        <div>
          <h1 className="text-sm font-bold text-[var(--text-primary)] tracking-tight">Enterprise Clinical Intelligence</h1>
          <p className="text-[10px] text-[var(--text-muted)]">AI-Powered Decision Support Platform</p>
        </div>
        <span className="badge badge-teal ml-1">v8.0</span>
      </div>

      {/* Search (decorative — command palette trigger) */}
      <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer flex-1 max-w-sm mx-8"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)' }}>
        <Search className="w-3.5 h-3.5 text-[var(--text-dim)]" />
        <span className="text-sm text-[var(--text-dim)]">Search patients, ICD-10, drugs…</span>
        <kbd className="ml-auto text-[9px] mono text-[var(--text-dim)] px-1.5 py-0.5 rounded"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border)' }}>
          ⌘K
        </kbd>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Backend status */}
        <div className={`hidden lg:flex items-center gap-1.5 text-[10px] font-semibold px-2.5 py-1.5 rounded-full ${backendOnline ? 'badge-success' : 'badge-danger'} badge`}>
          <span className={`w-1.5 h-1.5 rounded-full ${backendOnline ? 'animate-pulse' : ''}`}
            style={{ background: backendOnline ? 'var(--success)' : 'var(--danger)' }} />
          {backendOnline ? 'Backend Online' : 'Backend Offline'}
        </div>

        {/* Clock */}
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] mono text-[var(--text-muted)]">
          <Clock className="w-3 h-3 text-[var(--teal)]" />
          {time}
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            id="header-notifications"
            onClick={() => setShowNotif(v => !v)}
            className="relative p-2 rounded-xl btn-ghost transition-colors"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full" style={{ background: 'var(--teal)', boxShadow: '0 0 6px var(--teal)' }} />
          </button>
          {showNotif && (
            <div className="absolute right-0 mt-2 w-80 glass rounded-2xl shadow-2xl p-4 z-50 fade-in"
              style={{ border: '1px solid var(--border-bright)' }}>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-[var(--text-primary)]">Clinical Alerts</h4>
                <span className="badge badge-teal">Live</span>
              </div>
              <div className="space-y-2 text-xs text-[var(--text-muted)]">
                <div className="p-2.5 rounded-xl" style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.2)' }}>
                  ⚠️ <span className="text-[var(--warning)] font-semibold">Review Queue</span> — items awaiting clinician action
                </div>
                <div className="p-2.5 rounded-xl" style={{ background: 'var(--teal-dim)', border: '1px solid var(--teal-border)' }}>
                  🤖 <span className="text-[var(--teal)] font-semibold">AI Pipeline</span> — all agents operational
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User chip */}
        {user && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)' }}>
            <div className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold text-[#060B14]"
              style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>
              {(user.full_name || user.username).charAt(0).toUpperCase()}
            </div>
            <div className="hidden md:block text-left">
              <div className="text-[11px] font-semibold text-[var(--text-primary)]">{user.full_name || user.username}</div>
              <div className="text-[9px] font-bold uppercase tracking-wide" style={{ color: 'var(--teal)' }}>{user.role}</div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
