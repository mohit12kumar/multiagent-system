import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Command, Activity, CheckSquare, History, GitMerge, FileCode, BarChart2, ShieldAlert, Cpu, X, User } from 'lucide-react';

const CommandPalette = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const actions = [
    { id: 'dashboard', label: 'Doctor Command Center', category: 'Navigation', icon: BarChart2, path: '/doctor' },
    { id: 'review', label: 'Patient Review Queue', category: 'Navigation', icon: CheckSquare, path: '/doctor/review' },
    { id: 'history', label: 'Patient History & EHR Search', category: 'Navigation', icon: History, path: '/doctor/history' },
    { id: 'kg', label: 'Clinical Knowledge Graph Visualizer', category: 'Analytics', icon: GitMerge, path: '/doctor?tab=kg' },
    { id: 'fhir', label: 'FHIR R4 Bundle Inspector & Export', category: 'Integration', icon: FileCode, path: '/doctor?tab=fhir' },
    { id: 'aimonitor', label: 'Multi-Agent Telemetry & Pipeline Monitor', category: 'AI Intelligence', icon: Cpu, path: '/doctor?tab=aimonitor' },
    { id: 'patient_john', label: 'Patient Profile: John Doe (PAT-88421)', category: 'Quick Patient Lookup', icon: User, path: '/doctor/history?q=PAT-88421' },
    { id: 'patient_sarah', label: 'Patient Profile: Sarah Connor (PAT-99104)', category: 'Quick Patient Lookup', icon: User, path: '/doctor/history?q=PAT-99104' },
  ];

  const filtered = actions.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(true);
      }
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % (filtered.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          navigate(filtered[selectedIndex].path);
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, navigate, onClose]);

  if (!isOpen) return null;

  return (
    <div className="command-palette-backdrop" onClick={onClose}>
      <div className="command-palette-modal animate-fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Input Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <Search size={20} color="#38bdf8" />
          <input
            type="text"
            autoFocus
            placeholder="Type a command or search patients... (Press ESC to close)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#ffffff',
              fontSize: '15px',
              fontFamily: 'inherit',
            }}
          />
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '10px' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
              No matching clinical commands or patient records found.
            </div>
          ) : (
            filtered.map((item, idx) => {
              const IconComp = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    navigate(item.path);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(79, 70, 229, 0.25)' : 'transparent',
                    border: isSelected ? '1px solid rgba(79, 70, 229, 0.4)' : '1px solid transparent',
                    transition: 'all 0.15s ease',
                    marginBottom: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ padding: '6px', borderRadius: '6px', background: isSelected ? '#4F46E5' : 'rgba(255,255,255,0.06)', color: '#ffffff' }}>
                      <IconComp size={16} />
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: isSelected ? '#ffffff' : '#e2e8f0' }}>
                        {item.label}
                      </div>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>{item.category}</span>
                    </div>
                  </div>
                  {isSelected && (
                    <span style={{ fontSize: '11px', color: '#818cf8', fontWeight: '600' }}>
                      Jump to →
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 16px', background: 'rgba(0,0,0,0.3)', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '11px', color: '#94a3b8' }}>
          <div>
            Navigation: <span style={{ color: '#f8fafc', fontWeight: '600' }}>↑ ↓ Arrow keys</span> to select, <span style={{ color: '#f8fafc', fontWeight: '600' }}>Enter</span> to trigger
          </div>
          <div>
            <Command size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
            Clinical AI Platform v2.4
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
