import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

const ICONS = {
  success: <CheckCircle size={18} color="#10b981" />,
  error:   <XCircle    size={18} color="#ef4444" />,
  warning: <AlertTriangle size={18} color="#f59e0b" />,
  info:    <Info       size={18} color="#3b82f6" />,
};

const BG = {
  success: 'rgba(16,185,129,0.15)',
  error:   'rgba(239,68,68,0.15)',
  warning: 'rgba(245,158,11,0.15)',
  info:    'rgba(59,130,246,0.15)',
};

const BORDER = {
  success: 'rgba(16,185,129,0.4)',
  error:   'rgba(239,68,68,0.4)',
  warning: 'rgba(245,158,11,0.4)',
  info:    'rgba(59,130,246,0.4)',
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    if (duration > 0) {
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}

      {/* Toast container */}
      <div style={{
        position: 'fixed', bottom: '24px', right: '24px',
        display: 'flex', flexDirection: 'column', gap: '10px',
        zIndex: 9999, maxWidth: '380px', width: '100%',
      }}>
        {toasts.map(toast => (
          <div key={toast.id} style={{
            display: 'flex', alignItems: 'flex-start', gap: '10px',
            padding: '14px 16px',
            background: BG[toast.type],
            border: `1px solid ${BORDER[toast.type]}`,
            borderRadius: '12px',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
            animation: 'slideInRight 0.3s ease',
          }}>
            <span style={{ flexShrink: 0, marginTop: '1px' }}>{ICONS[toast.type]}</span>
            <span style={{ flex: 1, fontSize: '14px', color: '#f1f5f9', lineHeight: '1.4' }}>
              {toast.message}
            </span>
            <button
              onClick={() => removeToast(toast.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer',
                       color: '#94a3b8', padding: '0', flexShrink: 0 }}
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(40px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
