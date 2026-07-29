import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';
interface Toast { id: number; message: string; type: ToastType; }
interface ToastCtx { toast: (msg: string, type?: ToastType) => void; }

const ToastContext = createContext<ToastCtx | null>(null);

const ICONS: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />,
  error:   <XCircle     className="w-4 h-4 text-[var(--danger)]"  />,
  warning: <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />,
  info:    <Info        className="w-4 h-4 text-[var(--teal)]"    />,
};

const BG: Record<ToastType, string> = {
  success: 'border-[rgba(0,227,150,0.25)] bg-[rgba(0,227,150,0.08)]',
  error:   'border-[rgba(255,69,96,0.25)]  bg-[rgba(255,69,96,0.08)]',
  warning: 'border-[rgba(255,176,0,0.25)]  bg-[rgba(255,176,0,0.08)]',
  info:    'border-[rgba(0,212,255,0.25)]   bg-[rgba(0,212,255,0.08)]',
};

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  let nextId = 0;

  const toast = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++nextId;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  const dismiss = (id: number) => setToasts(prev => prev.filter(t => t.id !== id));

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed top-5 right-5 z-[9999] flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id}
            className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl shadow-2xl fade-in min-w-[280px] max-w-[380px] ${BG[t.type]}`}>
            {ICONS[t.type]}
            <p className="text-sm text-[var(--text-primary)] flex-1 font-medium">{t.message}</p>
            <button onClick={() => dismiss(t.id)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
};
