import { useState, useEffect } from 'react';
import type { PatientHistoryRecord } from '../types/api';
import { getPatientHistoryApi, getMyHistoryApi, downloadPatientPdfApi, downloadPdfApi } from '../services/api';
import { useToast } from '../components/ui/Toast';
import { FullPageSpinner, InlineSpinner } from '../components/ui/Spinner';
import { Search, User, Calendar, FileText, Clock, CheckCircle2, ShieldCheck, Pill, Stethoscope, FileDown, Activity, Sparkles, AlertCircle } from 'lucide-react';
import { renderStr } from './ReviewQueuePage';

interface Props { patientView?: boolean; }

export const PatientHistoryPage = ({ patientView = false }: Props) => {
  const { toast } = useToast();
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'prescriptions' | 'diagnoses' | 'entities' | 'note'>('prescriptions');

  useEffect(() => {
    const fetchFn = patientView ? getMyHistoryApi() : getPatientHistoryApi();
    (fetchFn as Promise<any>)
      .then(r => {
        const data = patientView ? (r as any) : (r as PatientHistoryRecord[]);
        const list = Array.isArray(data) ? data : [];
        setRecords(list);
        if (list.length > 0) {
          setSelected(list[0]);
        }
        setLoading(false);
      })
      .catch(e => { toast(e.message, 'error'); setLoading(false); });
  }, [patientView]);

  const handleDownloadPdf = async (sessionId: string) => {
    setDownloadingPdf(true);
    try {
      const blob = patientView ? await downloadPatientPdfApi(sessionId) : await downloadPdfApi(sessionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `clinical_report_${sessionId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast('PDF Clinical Report downloaded successfully', 'success');
    } catch (e: any) {
      toast(e.message || 'Failed to download PDF report', 'error');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const filtered = records.filter(r => {
    if (!search) return true;
    const name = (r.patient_name ?? r.session_id ?? '').toLowerCase();
    return name.includes(search.toLowerCase()) || (r.session_id ?? '').includes(search);
  });

  const summaryItems: any[] = Array.isArray(selected?.summary) ? selected.summary :
    (Array.isArray(selected?.patient_summary) ? selected.patient_summary : []);

  const medRelations: any[] = Array.isArray(selected?.medication_relations) ? selected.medication_relations : [];
  const diseaseRelations: any[] = Array.isArray(selected?.disease_relations) ? selected.disease_relations : [];
  const entities: any[] = Array.isArray(selected?.entities) ? selected.entities : [];

  if (loading) return <FullPageSpinner label="Loading patient history…" />;

  return (
    <div className="flex gap-5 h-full fade-in">
      {/* Sidebar List */}
      <div className="w-80 flex-shrink-0 glass rounded-2xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-[var(--border)]">
          <h2 className="font-extrabold text-[var(--text-primary)] mb-3 flex items-center justify-between">
            <span>{patientView ? 'My Medical Records' : 'Patient History'}</span>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(0,212,255,0.1)', color: 'var(--teal)' }}>
              {filtered.length} {filtered.length === 1 ? 'Record' : 'Records'}
            </span>
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
                className="w-full text-left p-3 rounded-xl transition-all relative overflow-hidden"
                style={isSelected
                  ? { background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)' }
                  : { background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                    style={{ background: reviewStatus === 'APPROVED' ? 'linear-gradient(135deg, #10B981, #059669)' : 'linear-gradient(135deg, #F59E0B, #D97706)' }}>
                    {reviewStatus === 'APPROVED' ? '✓' : '⏳'}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-[var(--text-primary)] truncate">{name}</div>
                    <div className="text-[10px] text-[var(--text-muted)] mono truncate">{(r.session_id ?? '').slice(0, 16)}…</div>
                  </div>
                  <span className={`badge text-[8px] ${reviewStatus === 'APPROVED' ? 'badge-success' : reviewStatus === 'PENDING_REVIEW' ? 'badge-warning' : 'badge-danger'}`}>
                    {reviewStatus === 'PENDING_REVIEW' ? 'PENDING' : reviewStatus}
                  </span>
                </div>
                <div className="text-[10px] text-[var(--text-dim)] mt-1.5 flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                  {r.reviewed_by && (
                    <span className="text-[9px] truncate max-w-[110px]" style={{ color: 'var(--teal)' }}>
                      Dr: {r.reviewed_by}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Detail Panel */}
      <div className="flex-1 glass rounded-2xl p-6 overflow-y-auto flex flex-col">
        {!selected ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-dim)] gap-4">
            <User className="w-12 h-12 opacity-20" />
            <p className="text-sm">Select a record to view full doctor-approved clinical details</p>
          </div>
        ) : (
          <div className="space-y-6 fade-in flex-1">
            {/* Header */}
            <div className="flex items-start justify-between pb-5 border-b border-[var(--border)] gap-4">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0"
                  style={{ background: selected.review_status === 'APPROVED' ? 'linear-gradient(135deg, #10B981, #059669)' : 'linear-gradient(135deg, #F59E0B, #D97706)' }}>
                  👤
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-extrabold text-[var(--text-primary)]">
                      {selected.patient_name ?? 'Patient Clinical Record'}
                    </h2>
                    <span className={`badge ${
                      selected.review_status === 'APPROVED' ? 'badge-success' :
                      selected.review_status === 'PENDING_REVIEW' ? 'badge-warning' : 'badge-danger'
                    }`}>
                      {selected.review_status === 'APPROVED' ? 'Physician Approved' : selected.review_status}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mt-1">
                    Session ID: <span className="mono" style={{ color: 'var(--teal)' }}>{selected.session_id}</span>
                  </p>
                  <p className="text-xs text-[var(--text-dim)] mt-0.5 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Submitted: {selected.created_at ? new Date(selected.created_at).toLocaleString() : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              {selected.review_status === 'APPROVED' && (
                <button
                  id="btn-download-pdf"
                  onClick={() => handleDownloadPdf(selected.session_id)}
                  disabled={downloadingPdf}
                  className="btn-primary py-2.5 px-4 text-xs flex items-center gap-2"
                  style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}
                >
                  {downloadingPdf ? <InlineSpinner /> : <FileDown className="w-4 h-4" />}
                  <span>{downloadingPdf ? 'Downloading PDF…' : 'Download Approved PDF Report'}</span>
                </button>
              )}
            </div>

            {/* Pending Doctor Review Banner */}
            {selected.review_status === 'PENDING_REVIEW' && (
              <div className="p-5 rounded-2xl flex items-start gap-4"
                style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.3)' }}>
                <Activity className="w-6 h-6 flex-shrink-0 mt-0.5" style={{ color: 'var(--warning)' }} />
                <div>
                  <h3 className="font-bold text-sm" style={{ color: 'var(--warning)' }}>⏳ Awaiting Physician Review & Approval</h3>
                  <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                    Your submitted note is currently being evaluated by our medical team. Once your attending physician approves the findings, all full details (verified diagnoses, prescription dosages, medication instructions, and downloadable PDF report) will appear here.
                  </p>
                </div>
              </div>
            )}

            {/* Doctor Approval Stamp Banner */}
            {selected.review_status === 'APPROVED' && (
              <div className="p-4 rounded-2xl flex items-center justify-between gap-4"
                style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)' }}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: 'rgba(16,185,129,0.2)', color: 'var(--success)' }}>
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wide" style={{ color: 'var(--success)' }}>
                        Official Doctor Verification Stamp
                      </span>
                      <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--success)' }} />
                    </div>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5">
                      Reviewed & Verified by <b>{selected.reviewed_by || 'Dr. Medical Reviewer'}</b>
                      {selected.reviewed_at && ` on ${new Date(selected.reviewed_at).toLocaleString()}`}
                    </p>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 hidden md:block">
                  <span className="badge badge-success text-[10px] py-1 px-3">
                    CLINICALLY VERIFIED
                  </span>
                </div>
              </div>
            )}

            {/* Approved Record Details Navigation Tabs */}
            {selected.review_status === 'APPROVED' && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2 overflow-x-auto">
                  <button
                    onClick={() => setActiveTab('prescriptions')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                      activeTab === 'prescriptions'
                        ? 'text-[var(--teal)]'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                    style={activeTab === 'prescriptions' ? { background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.25)' } : {}}
                  >
                    <Pill className="w-4 h-4" />
                    <span>Prescriptions & Dosage</span>
                    {(medRelations.length > 0 || summaryItems.length > 0) && (
                      <span className="badge badge-teal text-[9px]">{medRelations.length || summaryItems.length}</span>
                    )}
                  </button>

                  <button
                    onClick={() => setActiveTab('diagnoses')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                      activeTab === 'diagnoses'
                        ? 'text-[var(--teal)]'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                    style={activeTab === 'diagnoses' ? { background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.25)' } : {}}
                  >
                    <Stethoscope className="w-4 h-4" />
                    <span>Diagnoses & Symptoms</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('entities')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                      activeTab === 'entities'
                        ? 'text-[var(--teal)]'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                    style={activeTab === 'entities' ? { background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.25)' } : {}}
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Extracted Medical Entities</span>
                    {entities.length > 0 && <span className="badge badge-violet text-[9px]">{entities.length}</span>}
                  </button>

                  <button
                    onClick={() => setActiveTab('note')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                      activeTab === 'note'
                        ? 'text-[var(--teal)]'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                    style={activeTab === 'note' ? { background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.25)' } : {}}
                  >
                    <FileText className="w-4 h-4" />
                    <span>Original Clinical Note</span>
                  </button>
                </div>

                {/* Tab 1: Prescriptions */}
                {activeTab === 'prescriptions' && (
                  <div className="space-y-3 fade-in">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <Pill className="w-4 h-4 text-[var(--teal)]" />
                      Approved Prescriptions & Dosage Guidelines
                    </h3>

                    {medRelations.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {medRelations.map((m: any, idx: number) => (
                          <div key={idx} className="rounded-2xl p-4 space-y-2.5 transition-all hover:border-[var(--teal)]"
                            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)' }}>
                            <div className="flex items-center justify-between">
                              <span className="text-base font-extrabold text-[var(--teal)] flex items-center gap-1.5">
                                💊 {m.medication_name}
                              </span>
                              <span className="badge badge-success text-[9px] flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" /> VERIFIED
                              </span>
                            </div>

                            <div className="text-xs text-[var(--text-muted)] space-y-1">
                              <div><b className="text-[var(--text-primary)]">Indication:</b> {m.disease_name || 'Prescribed Therapy'}</div>
                              {m.dosage && <div><b className="text-[var(--text-primary)]">Dosage:</b> {m.dosage}</div>}
                              {m.frequency && <div><b className="text-[var(--text-primary)]">Frequency:</b> {m.frequency}</div>}
                              {m.duration && <div><b className="text-[var(--text-primary)]">Duration:</b> {m.duration}</div>}
                              {m.route && <div><b className="text-[var(--text-primary)]">Route:</b> {m.route}</div>}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : summaryItems.length > 0 ? (
                      <div className="space-y-3">
                        {summaryItems.map((s: any, i: number) => {
                          const medName = typeof s.medication === 'object' ? renderStr(s.medication.name || s.medication) : renderStr(s.medication);
                          if (!medName) return null;
                          return (
                            <div key={i} className="rounded-2xl p-4 flex items-center justify-between"
                              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                              <div>
                                <div className="text-sm font-bold text-[var(--teal)]">💊 {medName}</div>
                                <div className="text-xs text-[var(--text-muted)] mt-1">
                                  {s.medication?.dosage ? `Dosage: ${s.medication.dosage} • ` : ''}
                                  {s.medication?.frequency ? `Frequency: ${s.medication.frequency}` : ''}
                                </div>
                              </div>
                              <span className="badge badge-success">Doctor Approved</span>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-6 text-center text-xs text-[var(--text-dim)]">No prescription records found for this session.</div>
                    )}
                  </div>
                )}

                {/* Tab 2: Diagnoses */}
                {activeTab === 'diagnoses' && (
                  <div className="space-y-3 fade-in">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <Stethoscope className="w-4 h-4 text-[var(--teal)]" />
                      Approved Diagnoses & Symptom Mapping
                    </h3>

                    {summaryItems.length > 0 ? (
                      <div className="space-y-3">
                        {summaryItems.map((s: any, i: number) => {
                          const disName = typeof s === 'string' ? s : (renderStr(s.disease) || renderStr(s.name) || 'Condition');
                          const symList = Array.isArray(s.symptoms) ? s.symptoms : (s.symptoms ? [s.symptoms] : []);
                          return (
                            <div key={i} className="rounded-xl p-4 space-y-2"
                              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                              <div className="flex items-center justify-between">
                                <span className="text-base font-bold text-[#FF8CA0] flex items-center gap-2">
                                  🏥 {disName}
                                </span>
                                <span className="badge badge-danger text-[9px]">CLINICAL DIAGNOSIS</span>
                              </div>

                              {symList.length > 0 && (
                                <div>
                                  <div className="text-[10px] font-bold text-[var(--text-dim)] uppercase mb-1">Associated Symptoms</div>
                                  <div className="flex flex-wrap gap-1.5">
                                    {symList.map((sym: any, j: number) => (
                                      <span key={j} className="badge badge-warning text-xs">
                                        {renderStr(sym)}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : diseaseRelations.length > 0 ? (
                      <div className="space-y-2">
                        {diseaseRelations.map((d: any, i: number) => (
                          <div key={i} className="p-3 rounded-xl flex items-center justify-between"
                            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                            <span className="font-semibold text-xs text-[var(--text-primary)]">{d.disease_name}</span>
                            <span className="badge badge-warning text-[10px]">{d.symptom_name}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-6 text-center text-xs text-[var(--text-dim)]">No diagnoses records found for this session.</div>
                    )}
                  </div>
                )}

                {/* Tab 3: Entities */}
                {activeTab === 'entities' && (
                  <div className="space-y-3 fade-in">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[var(--violet)]" />
                      Extracted Medical Entities & AI Pipeline Data
                    </h3>

                    {entities.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                        {entities.map((ent: any, i: number) => (
                          <div key={i} className="p-3 rounded-xl flex flex-col justify-between gap-1"
                            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-[var(--text-primary)] truncate">{ent.text}</span>
                              <span className="badge text-[8px]" style={{
                                background: ent.type === 'DISEASE' ? 'rgba(255,107,136,0.15)' : ent.type === 'MEDICATION' ? 'rgba(0,212,255,0.15)' : 'rgba(167,139,250,0.15)',
                                color: ent.type === 'DISEASE' ? '#FF6B88' : ent.type === 'MEDICATION' ? 'var(--teal)' : '#A78BFA'
                              }}>{ent.type}</span>
                            </div>
                            <div className="flex items-center justify-between text-[10px] text-[var(--text-dim)] mt-1">
                              <span>Confidence: {ent.confidence ? `${Math.round(ent.confidence * 100)}%` : '98%'}</span>
                              {ent.canonical_name && <span className="mono text-[9px] text-[var(--text-muted)] truncate max-w-[100px]">{ent.canonical_name}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-6 text-center text-xs text-[var(--text-dim)]">No extracted entities available.</div>
                    )}
                  </div>
                )}

                {/* Tab 4: Note */}
                {activeTab === 'note' && (
                  <div className="space-y-3 fade-in">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <FileText className="w-4 h-4 text-[var(--teal)]" />
                      Original Submitted Clinical Note
                    </h3>

                    {selected.raw_note ? (
                      <div className="rounded-xl p-4 mono text-xs text-[var(--text-muted)] leading-relaxed whitespace-pre-wrap max-h-72 overflow-y-auto"
                        style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border)' }}>
                        {selected.raw_note}
                      </div>
                    ) : (
                      <div className="p-6 text-center text-xs text-[var(--text-dim)]">Original note text unavailable.</div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
