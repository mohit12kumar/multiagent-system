import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart2, Users, CheckSquare, FileText, GitMerge, FileCode, Activity, ShieldAlert, Cpu, Settings, ChevronLeft, ChevronRight, Stethoscope } from 'lucide-react';

const Sidebar = ({ isCollapsed, onToggle }) => {
  const location = useLocation();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', path: '/doctor', icon: BarChart2 },
    { id: 'review', label: 'Review Queue', path: '/doctor/review', icon: CheckSquare, badge: '4' },
    { id: 'history', label: 'Patient History', path: '/doctor/history', icon: Users },
    { id: 'notes', label: 'Clinical Notes', path: '/patient', icon: FileText },
    { id: 'kg', label: 'Knowledge Graph', path: '/doctor?tab=kg', icon: GitMerge },
    { id: 'fhir', label: 'FHIR Export', path: '/doctor?tab=fhir', icon: FileCode },
    { id: 'analytics', label: 'Analytics', path: '/doctor?tab=analytics', icon: Activity },
    { id: 'aimonitor', label: 'AI Monitor', path: '/doctor?tab=aimonitor', icon: Cpu, pulse: true },
    { id: 'audit', label: 'Audit Log', path: '/doctor?tab=audit', icon: ShieldAlert },
    { id: 'settings', label: 'Settings', path: '/doctor?tab=settings', icon: Settings },
  ];

  const currentSearch = location.search;

  return (
    <aside
      style={{
        width: isCollapsed ? '72px' : '240px',
        height: '100vh',
        position: 'sticky',
        top: 0,
        background: 'rgba(11, 15, 25, 0.95)',
        backdropFilter: 'blur(16px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        zIndex: 40,
        flexShrink: 0,
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '20px 18px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          overflow: 'hidden',
          whiteSpace: 'nowrap',
        }}
      >
        <div
          style={{
            padding: '8px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)',
            color: '#ffffff',
            boxShadow: '0 0 15px rgba(79, 70, 229, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Stethoscope size={20} />
        </div>
        {!isCollapsed && (
          <div>
            <div style={{ fontSize: '15px', fontWeight: '800', color: '#ffffff', letterSpacing: '-0.02em' }}>
              CLINICAL AI
            </div>
            <div style={{ fontSize: '10px', color: '#06B6D4', fontWeight: '700', letterSpacing: '0.08em' }}>
              FOUNDRY ENTERPRISE
            </div>
          </div>
        )}
      </div>

      {/* Nav List */}
      <div style={{ flex: 1, padding: '16px 10px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => {
          const IconComp = item.icon;
          let isActive = false;
          if (item.path.includes('?tab=')) {
            isActive = currentSearch.includes(item.path.split('?')[1]);
          } else {
            isActive = location.pathname === item.path && !currentSearch;
          }

          return (
            <Link
              key={item.id}
              to={item.path}
              title={isCollapsed ? item.label : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: isCollapsed ? 'center' : 'space-between',
                padding: '10px 12px',
                borderRadius: '8px',
                color: isActive ? '#FFFFFF' : '#94A3B8',
                background: isActive ? 'rgba(79, 70, 229, 0.22)' : 'transparent',
                border: isActive ? '1px solid rgba(79, 70, 229, 0.4)' : '1px solid transparent',
                textDecoration: 'none',
                transition: 'all 0.2s ease',
              }}
              className="icon-glow-hover"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <IconComp
                  size={18}
                  color={isActive ? '#38BDF8' : item.pulse ? '#10B981' : '#94A3B8'}
                />
                {!isCollapsed && (
                  <span style={{ fontSize: '13px', fontWeight: isActive ? '600' : '500', color: isActive ? '#FFFFFF' : '#CBD5E1' }}>
                    {item.label}
                  </span>
                )}
              </div>

              {!isCollapsed && item.badge && (
                <span
                  style={{
                    background: '#EF4444',
                    color: 'white',
                    fontSize: '10px',
                    fontWeight: '800',
                    padding: '2px 6px',
                    borderRadius: '10px',
                  }}
                >
                  {item.badge}
                </span>
              )}

              {!isCollapsed && item.pulse && (
                <span className="pulse-dot" style={{ background: '#10B981' }} />
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer / Toggle collapse */}
      <div style={{ padding: '12px 14px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', display: 'flex', justifyContent: isCollapsed ? 'center' : 'flex-end' }}>
        <button
          onClick={onToggle}
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#94A3B8',
            borderRadius: '6px',
            padding: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
