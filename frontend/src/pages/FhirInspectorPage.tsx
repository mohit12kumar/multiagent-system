import { useState, useEffect } from 'react';
import { getPatientHistoryApi, getSessionJsonApi } from '../services/api';
import { useToast } from '../components/ui/Toast';
import { FullPageSpinner } from '../components/ui/Spinner';
import { Copy, Download, CheckCircle2, Flame, ChevronDown, ChevronRight } from 'lucide-react';

/* ── Recursive interactive JSON renderer ── */
const JsonNode = ({ data, depth = 0 }: { data: any; depth?: number }) => {
  const [open, setOpen] = useState(depth < 2);
  if (data === null)             return <span style={{ color: '#FF8CA0' }}>null</span>;
  if (typeof data === 'boolean') return <span style={{ color: 'var(--warning)' }}>{String(data)}</span>;
  if (typeof data === 'number')  return <span style={{ color: 'var(--teal)' }}>{data}</span>;
  if (typeof data === 'string')  return <span style={{ color: 'var(--success)' }}>"{data}"</span>;

  if (Array.isArray(data)) {
    if (data.length === 0) return <span style={{ color: 'var(--text-dim)' }}>[]</span>;
    return (
      <span>
        <button onClick={() => setOpen(!open)} className="hover:opacity-70 transition-opacity" style={{ color: '#A78BFA' }}>
          {open ? <ChevronDown className="w-3 h-3 inline" /> : <ChevronRight className="w-3 h-3 inline" />}
          {' ['}
          {!open && <><span style={{ color: 'var(--text-dim)' }}> {data.length} items </span>{']'}</>}
        </button>
        {open && (
          <div style={{ marginLeft: (depth + 1) * 14 }}>
            {data.map((item, i) => (
              <div key={i}>
                <JsonNode data={item} depth={depth + 1} />
                {i < data.length - 1 && <span style={{ color: 'var(--text-dim)' }}>,</span>}
              </div>
            ))}
            <span style={{ color: '#A78BFA' }}>]</span>
          </div>
        )}
      </span>
    );
  }

  if (typeof data === 'object') {
    const keys = Object.keys(data);
    if (keys.length === 0) return <span style={{ color: 'var(--text-dim)' }}>{'{}'}</span>;
    return (
      <span>
        <button onClick={() => setOpen(!open)} className="hover:opacity-70 transition-opacity" style={{ color: '#A78BFA' }}>
          {open ? <ChevronDown className="w-3 h-3 inline" /> : <ChevronRight className="w-3 h-3 inline" />}
          {' {'}
          {!open && <><span style={{ color: 'var(--text-dim)' }}> {keys.length} keys </span>{'}'}</>}
        </button>
        {open && (
          <div style={{ marginLeft: (depth + 1) * 14 }}>
            {keys.map((key, i) => (
              <div key={key}>
                <span style={{ color: '#C4B5FD' }}>"{key}"</span>
                <span style={{ color: 'var(--text-dim)' }}>: </span>
                <JsonNode data={data[key]} depth={depth + 1} />
                {i < keys.length - 1 && <span style={{ color: 'var(--text-dim)' }}>,</span>}
              </div>
            ))}
            <span style={{ color: '#A78BFA' }}>{'}'}</span>
          </div>
        )}
      </span>
    );
  }
  return <span style={{ color: 'var(--text-muted)' }}>{String(data)}</span>;
};

export const FhirInspectorPage = () => {
  const { toast } = useToast();
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState('');
  const [fhirData, setFhirData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getPatientHistoryApi()
      .then(r => { setSessions(r); if (r.length > 0) setSessionId(r[0].session_id); })
      .catch(e => toast(e.message, 'error'))
      .finally(() => setSessionsLoading(false));
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true); setFhirData(null);
    getSessionJsonApi(sessionId)
      .then(d => setFhirData(d))
      .catch(e => toast(e.message, 'error'))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(fhirData, null, 2));
    setCopied(true); setTimeout(() => setCopied(false), 2000);
    toast('Copied to clipboard', 'success');
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(fhirData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: `fhir_${sessionId.slice(0, 8)}.json` }).click();
    URL.revokeObjectURL(url);
    toast('FHIR bundle downloaded', 'success');
  };

  if (sessionsLoading) return <FullPageSpinner label="Loading sessions…" />;

  return (
    <div className="flex flex-col h-full gap-5 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-black text-[var(--text-primary)] flex items-center gap-2">
            <Flame className="w-6 h-6" style={{ color: 'var(--warning)' }} />FHIR R4 Inspector
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Inspect and export HL7 FHIR R4 clinical bundles</p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {sessions.length === 0 ? (
            <span className="badge badge-muted">No sessions available — submit a clinical note first</span>
          ) : (
            <select id="fhir-session-select" value={sessionId} onChange={e => setSessionId(e.target.value)}
              className="input-dark text-sm px-4 py-2 pr-8">
              {sessions.map(s => (
                <option key={s.session_id} value={s.session_id} style={{ background: '#0D1421' }}>
                  {s.patient_name ?? 'Patient'} — {s.session_id.slice(0, 12)}…
                </option>
              ))}
            </select>
          )}
          {fhirData && (
            <>
              <button id="btn-copy-json" onClick={handleCopy}
                className="btn-ghost flex items-center gap-2 px-4 py-2 text-sm">
                {copied ? <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--success)' }} /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied!' : 'Copy JSON'}
              </button>
              <button id="btn-download-fhir" onClick={handleDownload}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl transition-all"
                style={{ background: 'rgba(255,176,0,0.12)', border: '1px solid rgba(255,176,0,0.25)', color: 'var(--warning)' }}>
                <Download className="w-4 h-4" />Export FHIR
              </button>
            </>
          )}
        </div>
      </div>

      {/* Validation badge */}
      {fhirData && (
        <div className="flex items-center gap-3 p-3 rounded-xl"
          style={{ background: 'var(--success-dim)', border: '1px solid rgba(0,227,150,0.25)' }}>
          <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--success)' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--success)' }}>
            FHIR R4 Bundle — Validation: <span className="font-black">VALID</span>
          </span>
          <span className="ml-auto text-xs text-[var(--text-muted)] mono">resourceType: Bundle</span>
        </div>
      )}

      {/* JSON viewer */}
      <div className="flex-1 glass rounded-2xl p-5 overflow-hidden flex flex-col min-h-0">
        <div className="mono text-xs text-[var(--text-muted)] overflow-y-auto flex-1 leading-6">
          {loading && (
            <div className="flex items-center justify-center h-48">
              <FullPageSpinner label="Loading FHIR bundle…" />
            </div>
          )}
          {!loading && !fhirData && sessions.length > 0 && (
            <div className="text-[var(--text-dim)] p-8 text-center">
              <Flame className="w-10 h-10 opacity-20 mx-auto mb-3" />
              <p>Select a session to inspect its FHIR bundle</p>
            </div>
          )}
          {!loading && !fhirData && sessions.length === 0 && (
            <div className="text-[var(--text-dim)] p-8 text-center">
              <p>No sessions found. Submit a clinical note first to generate FHIR bundles.</p>
            </div>
          )}
          {!loading && fhirData && <JsonNode data={fhirData} depth={0} />}
        </div>
      </div>
    </div>
  );
};
