import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="glass rounded-2xl p-8 max-w-lg mx-auto my-12 text-center space-y-4 fade-in"
          style={{ border: '1px solid rgba(255,69,96,0.3)', background: 'rgba(255,69,96,0.06)' }}>
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto"
            style={{ background: 'var(--danger-dim)', border: '1px solid rgba(255,69,96,0.25)' }}>
            <AlertTriangle className="w-6 h-6" style={{ color: 'var(--danger)' }} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)]">Component Error</h2>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              {this.state.error?.message || 'An unexpected rendering error occurred.'}
            </p>
          </div>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            className="btn-primary px-4 py-2 text-xs flex items-center gap-2 mx-auto">
            <RefreshCw className="w-3.5 h-3.5" /> Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
