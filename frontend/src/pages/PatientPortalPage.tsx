import { useState, useEffect } from 'react';
import { submitClinicalNoteApi, getMyHistoryApi, downloadPatientPdfApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { InlineSpinner } from '../components/ui/Spinner';
import { Send, FileText, CheckCircle2, Clock, Activity, ShieldCheck, FileDown, Pill, Stethoscope, ChevronRight } from 'lucide-react';
import { renderStr } from './ReviewQueuePage';

export const PatientPortalPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const data = await getMyHistoryApi();
      setHistory(Array.isArray(data) ? data : []);
    } catch {
      // ignore non-critical load failure
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!note.trim()) { toast('Please enter your symptoms or note', 'warning'); return; }
    setLoading(true); setResult(null);
    try {
      const r = await submitClinicalNoteApi(note);
      setResult(r); setNote('');
      toast('Note submitted successfully', 'success');
      fetchHistory();
    } catch (e: any) {
      toast(e.message ?? 'Submission failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (sessionId: string) => {
    setDownloadingId(sessionId);
    try {
      const blob = await downloadPatientPdfApi(sessionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `clinical_report_${sessionId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast('Downloaded official clinical report', 'success');
    } catch (e: any) {
      toast(e.message || 'Failed to download PDF', 'error');
    } finally {
      setDownloadingId(null);
    }
  };

  const approvedRecords = history.filter(h => h.review_status === 'APPROVED');
  const pendingRecords = history.filter(h => h.review_status === 'PENDING_REVIEW');

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in pb-8">
      {/* Welcome card */}
      <div className="glass rounded-2xl p-6 flex items-center justify-between gap-5">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>
            👤
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-[var(--text-primary)]">My Health Portal</h1>
            <p className="text-[var(--text-muted)] mt-0.5 text-sm">
              Welcome, <b style={{ color: 'var(--teal)' }}>{user?.full_name ?? user?.username}</b>.
              Submit symptoms for AI analysis and physician review.
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-3">
          <div className="text-right">
            <div className="text-xl font-extrabold" style={{ color: 'var(--success)' }}>{approvedRecords.length}</div>
            <div className="text-[10px] uppercase font-bold text-[var(--text-dim)] tracking-wider">Approved Reports</div>
          </div>
          {pendingRecords.length > 0 && (
            <div className="text-right pl-3 border-l border-[var(--border)]">
              <div className="text-xl font-extrabold" style={{ color: 'var(--warning)' }}>{pendingRecords.length}</div>
              <div className="text-[10px] uppercase font-bold text-[var(--text-dim)] tracking-wider">Pending Review</div>
            </div>
          )}
        </div>
      </div>

      {/* Submission form */}
      <div className="glass rounded-2xl p-6">
        <h2 className="font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5" style={{ color: 'var(--teal)' }} />Submit New Clinical Note
        </h2>
        <form id="patient-note-form" onSubmit={handleSubmit} className="space-y-4">
          <textarea
            id="patient-note-input"
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Describe your symptoms, current medications, and any relevant medical history…&#10;&#10;Example: I have been experiencing chest pain for the past 2 days, with shortness of breath when walking. I am currently taking Metformin 500mg twice daily for diabetes."
            rows={6}
            className="input-dark w-full p-4 text-sm leading-relaxed resize-none"
          />
          <button id="btn-submit-note" type="submit" disabled={loading || !note.trim()}
            className="btn-primary w-full py-3.5 flex items-center justify-center gap-2">
            {loading
              ? <><InlineSpinner /><span>Submitting to AI Pipeline…</span></>
              : <><Send className="w-4 h-4" /><span>Submit for Clinical Review</span></>}
          </button>
        </form>
      </div>

      {/* Immediate Result Banner */}
      {result && (
        <div className="glass rounded-2xl p-6 space-y-4 fade-in">
          <div className="flex items-center gap-2 font-bold" style={{ color: 'var(--success)' }}>
            <CheckCircle2 className="w-5 h-5" />Submission Received
          </div>
          <p className="text-sm text-[var(--text-muted)] leading-relaxed">
            {result.patient_message ?? 'Your clinical note has been submitted for doctor review.'}
          </p>
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Clock className="w-3.5 h-3.5" />
            Session ID: <span className="mono" style={{ color: 'var(--teal)' }}>{result.session_id}</span>
          </div>
          <div className="p-4 rounded-xl flex items-start gap-3"
            style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.25)' }}>
            <Activity className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: 'var(--warning)' }} />
            <p className="text-sm" style={{ color: '#FFD060' }}>
              Your note is pending physician review. You will be able to see your full health summary in <b>My History</b> once your doctor approves it.
            </p>
          </div>
        </div>
      )}

      {/* Recent Approved Health Records Section */}
      <div className="glass rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
          <div>
            <h2 className="font-extrabold text-[var(--text-primary)] flex items-center gap-2 text-lg">
              <ShieldCheck className="w-5 h-5 text-[var(--success)]" />
              Doctor-Approved Clinical Reports
            </h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Verified clinical diagnoses, prescriptions, and official reports approved by attending physicians.
            </p>
          </div>
          <span className="badge badge-success text-xs py-1 px-3">
            {approvedRecords.length} Verified
          </span>
        </div>

        {historyLoading ? (
          <div className="p-6 text-center text-xs text-[var(--text-dim)]">Loading approved records…</div>
        ) : approvedRecords.length === 0 ? (
          <div className="p-8 text-center rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px border-dashed var(--border)' }}>
            <ShieldCheck className="w-10 h-10 text-[var(--text-dim)] mx-auto mb-2 opacity-30" />
            <p className="text-sm font-semibold text-[var(--text-primary)]">No Doctor-Approved Reports Yet</p>
            <p className="text-xs text-[var(--text-muted)] mt-1 max-w-md mx-auto">
              Once your physician reviews and approves your submitted clinical notes, your verified health summaries, prescriptions, and official PDF reports will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {approvedRecords.map(item => {
              const summaryItems: any[] = Array.isArray(item.summary) ? item.summary : [];
              const meds: any[] = Array.isArray(item.medication_relations) ? item.medication_relations : [];

              return (
                <div key={item.history_id || item.session_id} className="rounded-2xl p-4 transition-all hover:border-[var(--teal)] space-y-3"
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold"
                        style={{ background: 'rgba(16,185,129,0.15)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.3)' }}>
                        ✓
                      </div>
                      <div>
                        <div className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                          Session {item.session_id.slice(0, 8)}
                          <span className="badge badge-success text-[8px]">APPROVED</span>
                        </div>
                        <div className="text-[11px] text-[var(--text-muted)] flex items-center gap-2 mt-0.5">
                          <span>Reviewed by <b>{item.reviewed_by || 'Dr. Medical Reviewer'}</b></span>
                          <span>•</span>
                          <span>{item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDownloadPdf(item.session_id)}
                      disabled={downloadingId === item.session_id}
                      className="btn-primary py-2 px-3 text-xs flex items-center gap-1.5"
                      style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}
                    >
                      {downloadingId === item.session_id ? <InlineSpinner /> : <FileDown className="w-3.5 h-3.5" />}
                      <span>{downloadingId === item.session_id ? 'Downloading…' : 'PDF Report'}</span>
                    </button>
                  </div>

                  {/* Summary / Medication Preview */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    {summaryItems.length > 0 && (
                      <div className="space-y-1">
                        <div className="text-[10px] font-bold text-[var(--text-dim)] uppercase flex items-center gap-1">
                          <Stethoscope className="w-3 h-3 text-[#FF8CA0]" /> Diagnoses
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {summaryItems.map((s: any, idx: number) => (
                            <span key={idx} className="badge badge-danger text-[10px]">
                              {renderStr(s.disease || s.name || s)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {(meds.length > 0 || summaryItems.some(s => s.medication)) && (
                      <div className="space-y-1">
                        <div className="text-[10px] font-bold text-[var(--text-dim)] uppercase flex items-center gap-1">
                          <Pill className="w-3 h-3 text-[var(--teal)]" /> Verified Medications
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {meds.length > 0 ? (
                            meds.map((m: any, idx: number) => (
                              <span key={idx} className="badge badge-teal text-[10px]">
                                💊 {m.medication_name} {m.dosage ? `(${m.dosage})` : ''}
                              </span>
                            ))
                          ) : (
                            summaryItems.filter(s => s.medication).map((s: any, idx: number) => (
                              <span key={idx} className="badge badge-teal text-[10px]">
                                💊 {renderStr(s.medication.name || s.medication)}
                              </span>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
