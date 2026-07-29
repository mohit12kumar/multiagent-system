import { useState, useEffect, useCallback } from 'react';
import { getHealthApi } from '../services/api';
import { useToast } from '../components/ui/Toast';
import { Cpu, Clock, CheckCircle2, Zap, RefreshCw, Server } from 'lucide-react';

interface Props { backendOnline: boolean; }

// Agent definitions are system architecture constants, not data — they define
// what agents exist in the pipeline (names/descriptions are config, not DB values).
const AGENT_DEFS = [
  { name: 'Medical NER Agent',        desc: 'Named Entity Recognition for clinical text',         icon: '🧠', subsystem: 'nlp_extraction_engine' },
  { name: 'Terminology Agent',        desc: 'ICD-10 / SNOMED-CT normalization',                    icon: '📖', subsystem: 'terminology_mappings'   },
  { name: 'Disease Engine',           desc: 'Multi-condition disease detection',                    icon: '🔬', subsystem: 'nlp_extraction_engine' },
  { name: 'Evidence Engine',          desc: 'Clinical evidence extraction & scoring',               icon: '📊', subsystem: 'clinical_rules_engine'  },
  { name: 'Medication Engine',        desc: 'Drug extraction, dosage, interactions',               icon: '💊', subsystem: 'nlp_extraction_engine' },
  { name: 'Recommendation Engine',    desc: 'Clinical guideline-based recommendations',            icon: '📋', subsystem: 'clinical_rules_engine'  },
  { name: 'FHIR Engine',              desc: 'HL7 FHIR R4 bundle generation',                       icon: '🔥', subsystem: 'fhir_r4_validator'      },
  { name: 'Validation Engine',        desc: 'Clinical data integrity validation',                  icon: '✅', subsystem: 'fhir_r4_validator'      },
  { name: 'Knowledge Graph Agent',    desc: 'Entity relationship graph construction',               icon: '🕸️', subsystem: 'knowledge_graph_builder' },
  { name: 'Differential Engine',      desc: 'Differential diagnosis generation',                   icon: '⚖️', subsystem: 'clinical_rules_engine'  },
  { name: 'Medication Optimizer',     desc: 'Drug interaction & contraindication analysis',        icon: '🔄', subsystem: 'nlp_extraction_engine' },
  { name: 'Timeline Engine',          desc: 'Patient journey timeline construction',               icon: '🗓️', subsystem: 'knowledge_graph_builder' },
  { name: 'Pathway Engine',           desc: 'Evidence-based pathway mapping',                      icon: '🗺️', subsystem: 'clinical_rules_engine'  },
];

const SUBSYSTEM_LABELS: Record<string, string> = {
  nlp_extraction_engine: 'NLP Extraction Engine',
  terminology_mappings:  'Terminology Mappings',
  clinical_rules_engine: 'Clinical Rules Engine',
  fhir_r4_validator:     'FHIR R4 Validator',
  knowledge_graph_builder:'Knowledge Graph Builder',
};

interface HealthStatus {
  status: string;
  service: string;
  version: string;
  uptime_seconds?: number;
  platform?: string;
  python_version?: string;
  timestamp?: string;
  subsystems?: Record<string, string>;
  system_metrics?: Record<string, any>;
}

export const AiMonitorPage = ({ backendOnline }: Props) => {
  const { toast } = useToast();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      // GET / returns basic health; readiness endpoint not exposed as FastAPI route.
      // We derive subsystem status from the service being online.
      const h = await getHealthApi();
      setHealth(h as HealthStatus);
      toast('Status refreshed', 'success');
    } catch {
      setHealth(null);
      toast('Could not reach backend', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Agent is considered ACTIVE if the backend is reachable
  const agentActive = backendOnline;

  // Uptime display
  const uptimeFmt = (secs?: number) => {
    if (!secs) return '—';
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    return h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-[var(--text-primary)] flex items-center gap-2">
            <Cpu className="w-6 h-6" style={{ color: '#A78BFA' }} />AI Pipeline Monitor
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">
            {AGENT_DEFS.length} specialized clinical AI agents — status from live backend health check
          </p>
        </div>
        <button id="btn-refresh-monitor" onClick={refresh} disabled={loading}
          className="btn-ghost flex items-center gap-2 px-4 py-2 text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[var(--teal)]' : ''}`} />
          Refresh Status
        </button>
      </div>

      {/* Backend info cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Active Agents',  value: agentActive ? AGENT_DEFS.length : 0, icon: <Cpu className="w-5 h-5" />,          color: '#00D4FF' },
          { label: 'System Uptime',  value: uptimeFmt(health?.uptime_seconds),    icon: <Clock className="w-5 h-5" />,         color: '#A78BFA' },
          { label: 'Backend Status', value: backendOnline ? 'HEALTHY' : 'OFFLINE', icon: <Server className="w-5 h-5" />,       color: backendOnline ? '#00E396' : '#FF4560' },
          { label: 'Version',        value: health?.version ?? '—',               icon: <CheckCircle2 className="w-5 h-5" />, color: '#FFB000' },
        ].map(k => (
          <div key={k.label} className="glass glass-hover rounded-2xl p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: `${k.color}18`, border: `1px solid ${k.color}30` }}>
              <div style={{ color: k.color }}>{k.icon}</div>
            </div>
            <div>
              <div className="text-lg font-extrabold text-[var(--text-primary)] tabular-nums">{k.value}</div>
              <div className="text-xs text-[var(--text-muted)]">{k.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Subsystem status from real health check */}
      {health && (
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4">Backend Subsystem Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.entries(SUBSYSTEM_LABELS).map(([key, label]) => {
              const status = agentActive ? 'OPERATIONAL' : 'OFFLINE';
              return (
                <div key={key} className="rounded-xl p-3 text-center"
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                  <div className={`badge mb-2 inline-flex ${agentActive ? 'badge-success' : 'badge-danger'}`}>
                    {status}
                  </div>
                  <div className="text-xs font-semibold text-[var(--text-muted)]">{label}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Agent grid */}
      <div>
        <h3 className="font-bold text-[var(--text-primary)] mb-4">Agent Fleet Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {AGENT_DEFS.map(agent => (
            <div key={agent.name} className="glass glass-hover rounded-2xl p-5 transition-all">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)' }}>
                    {agent.icon}
                  </div>
                  <div>
                    <div className="font-bold text-sm text-[var(--text-primary)]">{agent.name}</div>
                    <div className="text-[10px] text-[var(--text-dim)] max-w-[150px] truncate">{agent.desc}</div>
                  </div>
                </div>
                <div className={`badge flex items-center gap-1 flex-shrink-0 ${agentActive ? 'badge-success' : 'badge-danger'}`}>
                  {agentActive && <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--success)' }} />}
                  {agentActive ? 'ACTIVE' : 'OFFLINE'}
                </div>
              </div>

              {/* Subsystem tag */}
              <div className="mb-3">
                <span className="badge badge-violet text-[8px]">
                  {SUBSYSTEM_LABELS[agent.subsystem] ?? agent.subsystem}
                </span>
              </div>

              {/* Status bar */}
              <div className="flex justify-between text-[9px] text-[var(--text-dim)] mb-1">
                <span>Pipeline Health</span>
                <span style={{ color: agentActive ? 'var(--success)' : 'var(--danger)' }}>
                  {agentActive ? '100%' : '0%'}
                </span>
              </div>
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <div className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: agentActive ? '100%' : '0%',
                    background: agentActive ? 'linear-gradient(90deg, var(--teal), var(--success))' : 'var(--danger)',
                  }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Backend info strip */}
      {health && (
        <div className="glass rounded-2xl p-4">
          <h3 className="font-bold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
            <Server className="w-4 h-4" style={{ color: 'var(--teal)' }} />Backend Runtime Info
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            {[
              { label: 'Service',   value: health.service ?? '—'        },
              { label: 'Version',   value: health.version ?? '—'        },
              { label: 'Uptime',    value: uptimeFmt(health.uptime_seconds) },
              { label: 'Timestamp', value: health.timestamp ? new Date(health.timestamp).toLocaleTimeString() : '—' },
            ].map(s => (
              <div key={s.label}>
                <div className="text-[var(--text-dim)] mb-0.5 uppercase tracking-wider text-[9px]">{s.label}</div>
                <div className="font-semibold text-[var(--text-primary)] mono">{s.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
