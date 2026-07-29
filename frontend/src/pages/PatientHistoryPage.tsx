import { useState, useEffect } from 'react';
import type { PatientHistoryRecord } from '../types/api';
import { getPatientHistoryApi, getMyHistoryApi } from '../services/api';
import { useToast } from '../components/ui/Toast';
import { FullPageSpinner } from '../components/ui/Spinner';
import { Search, User, Calendar, FileText, Clock } from 'lucide-react';
import { renderStr } from './ReviewQueuePage';

interface Props { patientView?: boolean; }

export const PatientHistoryPage = ({ patientView = false }: Props) => {
  const { toast } = useToast();
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    const fetch = patientView ? getMyHistoryApi() : getPatientHistoryApi();
    (fetch as Promise<any>)
      .then(r => {
        const data = patientView ? (r as any) : (r as PatientHistoryRecord[]);
        setRecords(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(e => { toast(e.message, 'error'); setLoading(false); });
  }, [patientView]);

  const filtered = records.filter(r => {
    if (!search) return true;
    const name = (r.patient_name ?? r.session_id ?? '').toLowerCase();
    return name.includes(search.toLowerCase()) || (r.session_id ?? '').includes(search);
  });

  const summaryItems: any[] = Array.isArray(selected?.summary) ? selected.summary :
    (Array.isArray(selected?.patient_summary) ? selected.patient_summary : []);

  if (loading) return <FullPageSpinner label="Loading patient history…" />;

  return (
    <div className="flex gap-5 h-full fade-in">
      {/* List */}
      <div className="w-80 flex-shrink-0 glass rounded-2xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-[var(--border)]">
          <h2 className="font-extrabold text-[var(--text-primary)] mb-3">
            {patientView ? 'My History' : 'Patient History'}
          </h2>
          {!patientView && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-dim)]" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search patients…"
                className="input-dark w-full pl-9 pr-3 py-2 text-xs" />
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {filtered.length === 0 ? (
            <div className="p-8 text-center">
              <User className="w-8 h-8 text-[var(--text-dim)] mx-auto mb-2 opacity-30" />
              <p className="text-sm text-[var(--text-dim)]">
                {patientView ? 'No records yet. Submit a clinical note to get started.' : 'No patient records found.'}
              </p>
            </div>
          ) : filtered.map(r => {
            const name = r.patient_name ?? `Session ${(r.session_id ?? '').slice(0, 8)}`;
            const isSelected = selected?.history_id === r.history_id || selected?.session_id === r.session_id;
            const reviewStatus = r.review_status ?? 'APPROVED';
            return (
              <button key={r.history_id ?? r.session_id} onClick={() => setSelected(r)}
                className="w-full text-left p-3 rounded-xl transition-all"
                style={isSelected
                  ? { background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)' }
                  : { background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>👤</div>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-[var(--text-primary)] truncate">{name}</div>
                    <div className="text-[10px] text-[var(--text-muted)] mono truncate">{(r.session_id ?? '').slice(0, 16)}…</div>
                  </div>
                  {patientView && (
                    <span className={`badge text-[8px] ${reviewStatus === 'APPROVED' ? 'badge-success' : reviewStatus === 'PENDING_REVIEW' ? 'badge-warning' : 'badge-danger'}`}>
                      {reviewStatus === 'PENDING_REVIEW' ? 'PENDING' : reviewStatus}
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-[var(--text-dim)] mt-1.5 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'N/A'}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 glass rounded-2xl p-6 overflow-y-auto">
        {!selected ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-dim)] gap-4">
            <User className="w-12 h-12 opacity-20" />
            <p className="text-sm">Select a {patientView ? 'record' : 'patient'} to view details</p>
          </div>
        ) : (
          <div className="space-y-6 fade-in">
            {/* Header */}
            <div className="flex items-start gap-5 pb-5 border-b border-[var(--border)]">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>👤</div>
              <div>
                <h2 className="text-xl font-extrabold text-[var(--text-primary)]">
                  {selected.patient_name ?? 'Patient Record'}
                </h2>
                <p className="text-sm text-[var(--text-muted)] mt-0.5">
                  Session: <span className="mono" style={{ color: 'var(--teal)' }}>{selected.session_id}</span>
                </p>
                <p className="text-xs text-[var(--text-dim)] mt-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {selected.created_at ? new Date(selected.created_at).toLocaleString() : 'N/A'}
                </p>
                {selected.review_status && (
                  <span className={`badge mt-2 inline-flex ${
                    selected.review_status === 'APPROVED' ? 'badge-success' :
                    selected.review_status === 'PENDING_REVIEW' ? 'badge-warning' : 'badge-danger'
                  }`}>{selected.review_status}</span>
                )}
              </div>
            </div>

            {/* Patient message (for patient view pending) */}
            {patientView && selected.review_status === 'PENDING_REVIEW' && (
              <div className="p-4 rounded-xl" style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.25)' }}>
                <p className="text-sm font-semibold" style={{ color: 'var(--warning)' }}>⏳ Awaiting Doctor Review</p>
                <p className="text-xs text-[var(--text-muted)] mt-1">Your clinical note is being reviewed by your physician. The full summary will be available once approved.</p>
              </div>
            )}

            {/* Structured summary */}
            {summaryItems.length > 0 && (
              <div>
                <h3 className="font-bold text-[var(--text-primary)] mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4" style={{ color: 'var(--teal)' }} />AI Structured Summary
                </h3>
                <div className="space-y-3">
                  {summaryItems.map((s: any, i: number) => {
                    const disName = typeof s === 'string' ? s : (renderStr(s.disease) || renderStr(s.name) || 'Condition');
                    const symList = Array.isArray(s.symptoms) ? s.symptoms : (s.symptoms ? [s.symptoms] : []);
                    const medName = typeof s.medication === 'object' ? renderStr(s.medication.name || s.medication) : renderStr(s.medication);
                    return (
                      <div key={i} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-bold" style={{ color: '#FF8CA0' }}>{disName}</span>
                          <span className="badge badge-danger text-[8px]">CONDITION</span>
                        </div>
                        {symList.length > 0 && (
                          <div className="mb-2">
                            <div className="text-[10px] font-bold text-[var(--text-dim)] uppercase mb-1">Symptoms</div>
                            <div className="flex flex-wrap gap-1.5">
                              {symList.map((sym: any, j: number) => (
                                <span key={j} className="badge badge-warning">{renderStr(sym)}</span>
                              ))}
                            </div>
                          </div>
                        )}
                        {medName && (
                          <div>
                            <div className="text-[10px] font-bold text-[var(--text-dim)] uppercase mb-1">Medication</div>
                            <span className="badge badge-teal">
                              💊 {medName} {s.medication?.dosage ?? ''} {s.medication?.frequency ?? ''}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Raw note (doctor view only) */}
            {!patientView && selected.raw_note && (
              <div>
                <h3 className="font-bold text-[var(--text-primary)] mb-3">Original Clinical Note</h3>
                <div className="rounded-xl p-4 mono text-xs text-[var(--text-muted)] leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto"
                  style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)' }}>
                  {selected.raw_note}
                </div>
              </div>
            )}

            {summaryItems.length === 0 && !selected.raw_note && (
              <div className="text-center text-[var(--text-dim)] py-8">
                <FileText className="w-8 h-8 opacity-20 mx-auto mb-2" />
                <p className="text-sm">No summary data available for this record.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
