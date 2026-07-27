import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Stethoscope, Search, Bell, Settings, LogOut, ShieldCheck, Command, Sun, Moon } from 'lucide-react';

const Navbar = ({ onOpenCommandPalette }) => {
  const { user, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);

  if (!user) return null;

  const isDoctor = user.role === 'doctor';

  const mockNotifications = [
    { id: 1, title: 'Critical Allergy Flag', desc: 'Patient PAT-88421 flagged for Penicillin anaphylaxis risk.', time: '5m ago', type: 'critical' },
    { id: 2, title: 'Review Queue Update', desc: 'Dr. Jenkins approved 3 extracted clinical notes.', time: '20m ago', type: 'success' },
    { id: 3, title: 'FHIR Export Ready', desc: 'FHIR R4 Bundle generated for Session #e9f2a4.', time: '1h ago', type: 'info' },
  ];

  return (
    <nav
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 30,
        background: 'rgba(11, 15, 25, 0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '12px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '20px',
      }}
    >
      {/* Left: Command Search trigger */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, maxWidth: '480px' }}>
        <button
          onClick={onOpenCommandPalette}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            width: '100%',
            padding: '8px 14px',
            background: 'rgba(18, 24, 38, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            color: '#94A3B8',
            cursor: 'pointer',
            fontSize: '13px',
            transition: 'all 0.2s ease',
          }}
          className="glass-card"
        >
          <Search size={16} color="#38BDF8" />
          <span style={{ flex: 1, textAlign: 'left' }}>Search patient, ICD-10, or command...</span>
          <kbd
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '4px',
              padding: '2px 6px',
              fontSize: '11px',
              color: '#CBD5E1',
              fontFamily: 'sans-serif',
            }}
          >
            Ctrl K
          </kbd>
        </button>
      </div>

      {/* Right: Hospital System Telemetry & User Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Hospital Node Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '20px' }}>
          <span className="pulse-dot" style={{ background: '#10B981' }} />
          <span style={{ fontSize: '11px', fontWeight: '700', color: '#34D399', letterSpacing: '0.04em' }}>
            EPIC / CERNER NODE ONLINE
          </span>
        </div>

        {/* Notifications Popover */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              padding: '8px',
              color: '#CBD5E1',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              position: 'relative',
            }}
            title="Notifications"
          >
            <Bell size={18} />
            <span style={{ position: 'absolute', top: '-4px', right: '-4px', width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444' }} />
          </button>

          {showNotifications && (
            <div
              className="glass-panel animate-fade-in"
              style={{
                position: 'absolute',
                top: '46px',
                right: 0,
                width: '320px',
                padding: '16px',
                zIndex: 50,
                background: '#111827',
                border: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#ffffff' }}>System Telemetry Alerts</span>
                <span style={{ fontSize: '11px', color: '#38BDF8', cursor: 'pointer' }}>Mark all read</span>
              </div>
              {mockNotifications.map((n) => (
                <div key={n.id} style={{ marginBottom: '10px', padding: '8px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', borderLeft: `3px solid ${n.type === 'critical' ? '#EF4444' : n.type === 'success' ? '#10B981' : '#38BDF8'}` }}>
                  <div style={{ fontSize: '12px', fontWeight: '600', color: '#F8FAFC' }}>{n.title}</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>{n.desc}</div>
                  <div style={{ fontSize: '10px', color: '#64748B', marginTop: '4px' }}>{n.time}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Doctor Avatar / Profile Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingLeft: '8px', borderLeft: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF' }}>
              {user.full_name || user.username}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end', marginTop: '2px' }}>
              <span className={`badge ${isDoctor ? 'badge-indigo' : 'badge-emerald'}`}>
                {user.role.toUpperCase()}
              </span>
            </div>
          </div>

          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #4F46E5 0%, #8B5CF6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: '800',
              color: '#ffffff',
              fontSize: '14px',
              boxShadow: '0 0 10px rgba(79, 70, 229, 0.4)',
            }}
          >
            {(user.full_name || user.username).charAt(0).toUpperCase()}
          </div>

          <button
            onClick={logout}
            className="btn btn-secondary"
            style={{ padding: '8px', borderRadius: '8px' }}
            title="Sign Out"
          >
            <LogOut size={16} color="#EF4444" />
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
