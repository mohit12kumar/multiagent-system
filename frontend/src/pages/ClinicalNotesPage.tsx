import { useState } from 'react';
import { extractClinicalTextApi, submitClinicalNoteApi } from '../services/api';
import { useToast } from '../components/ui/Toast';
import { InlineSpinner, FullPageSpinner } from '../components/ui/Spinner';
import { FileText, Brain, Send, CheckCircle2, AlertCircle } from 'lucide-react';
import type { ExtractionResponse } from '../types/api';
import { renderStr } from './ReviewQueuePage';

const SAMPLE_NOTE = `Patient: John Doe, 58-year-old male presenting with chest pain, shortness of breath, and dizziness.
Vitals: BP 160/95, HR 102 bpm, RR 20/min, Temp 37.2°C, SpO2 94%.
Labs: Troponin-I 0.12 ng/mL (elevated), BNP 320 pg/mL, HbA1c 8.2%, Creatinine 1.6 mg/dL.
History of Type 2 Diabetes Mellitus and Essential Hypertension.
No Known Drug Allergies (NKDA).
ECG: ST elevation in anterolateral leads.
Medications: Metformin 500mg PO BID, Lisinopril 10mg PO OD.
Impression: Acute STEMI in a patient with poorly controlled T2DM and HTN.`;

export const ClinicalNotesPage = () => {
  const { toast } = useToast();
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExtractionResponse | null>(null);

  const run = async (isDoctor: boolean) => {
    if (!note.trim()) { toast('Please enter a clinical note first', 'warning'); return; }
    setLoading(true); setResult(null);
    try {
      const r = isDoctor ? await extractClinicalTextApi(note) : await submitClinicalNoteApi(note);
      setResult(r as ExtractionResponse);
      toast('Extraction completed successfully', 'success');
    } catch (e: any) {
      toast(e.message ?? 'Extraction failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const summary: any[] = Array.isArray(result?.patient_summary)
    ? result!.patient_summary as any[]
    : (result?.patient_summary as any)?.structured_summary ?? [];

  return (
    <div className="space-y-5 fade-in">
      <div>
        <h1 className="text-2xl font-black text-[var(--text-primary)]">Clinical Note Submission</h1>
        <p className="text-sm text-[var(--text-muted)] mt-0.5">Submit patient notes to the AI multi-agent extraction pipeline</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Input */}
        <div className="glass rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-[var(--text-primary)] flex items-center gap-2">
              <FileText className="w-4 h-4" style={{ color: 'var(--teal)' }} />Clinical Note Input
            </h2>
            <button onClick={() => setNote(SAMPLE_NOTE)}
              className="text-xs font-semibold transition-colors" style={{ color: 'var(--teal)' }}
              onMouseEnter={e => (e.currentTarget.style.opacity = '0.7')}
              onMouseLeave={e => (e.currentTarget.style.opacity = '1')}>
              Load Sample
            </button>
          </div>

          <textarea id="clinical-note-input" value={note} onChange={e => setNote(e.target.value)}
            placeholder="Enter clinical note here…&#10;&#10;E.g: Patient is a 58-year-old male presenting with chest pain..."
            rows={16}
            className="input-dark w-full p-4 mono text-sm leading-relaxed resize-none flex-1" />

          <div className="flex gap-3">
            <button id="btn-run-extraction" onClick={() => run(true)} disabled={loading || !note.trim()}
              className="btn-primary flex-1 flex items-center justify-center gap-2 py-3 text-sm">
              {loading ? <><InlineSpinner /><span>Running pipeline…</span></> : <><Brain className="w-4 h-4" /><span>Run AI Extraction</span></>}
            </button>
            <button id="btn-submit-patient" onClick={() => run(false)} disabled={loading || !note.trim()}
              className="btn-ghost flex-1 flex items-center justify-center gap-2 py-3 text-sm font-semibold">
              <Send className="w-4 h-4" /> Submit as Patient
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="glass rounded-2xl p-5 flex flex-col gap-4">
          <h2 className="font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Brain className="w-4 h-4" style={{ color: '#A78BFA' }} />AI Extraction Results
          </h2>

          {!result && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-[var(--text-dim)] gap-3 py-16">
              <Brain className="w-12 h-12 opacity-20" />
              <p className="text-sm">Extraction results will appear here</p>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center gap-5 py-12">
              <FullPageSpinner label="Multi-agent AI pipeline running…" />
              <div className="space-y-1.5 text-xs text-[var(--text-dim)] text-center">
                {['NER Agent', 'Disease Engine', 'Medication Engine', 'Evidence Engine', 'FHIR Generator'].map(a => (
                  <div key={a} className="flex items-center justify-center gap-2">
                    <InlineSpinner />
                    <span>{a}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-4 overflow-y-auto flex-1 fade-in">
              {/* Status */}
              <div className="flex items-center gap-2 p-3 rounded-xl"
                style={{ background: 'var(--success-dim)', border: '1px solid rgba(0,227,150,0.25)' }}>
                <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--success)' }} />
                <span className="text-sm font-semibold" style={{ color: 'var(--success)' }}>
                  {result.patient_message ?? 'Extraction Successful'}
                </span>
              </div>

              {/* Metrics from API */}
              {(result.entities || result.relations) && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl p-3 text-center" style={{ background: 'var(--teal-dim)', border: '1px solid var(--teal-border)' }}>
                    <div className="text-2xl font-black" style={{ color: 'var(--teal)' }}>{result.entities?.length ?? 0}</div>
                    <div className="text-xs text-[var(--text-muted)]">Entities Extracted</div>
                  </div>
                  <div className="rounded-xl p-3 text-center" style={{ background: 'var(--violet-dim)', border: '1px solid var(--violet-border)' }}>
                    <div className="text-2xl font-black" style={{ color: '#A78BFA' }}>{result.relations?.length ?? 0}</div>
                    <div className="text-xs text-[var(--text-muted)]">Relations Detected</div>
                  </div>
                </div>
              )}

              {/* Diseases */}
              {result.diseases && result.diseases.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Detected Diseases</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {result.diseases.map((d, i) => <span key={i} className="badge badge-danger">{renderStr(d)}</span>)}
                  </div>
                </div>
              )}

              {/* Medications */}
              {result.medications && result.medications.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Medications</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {result.medications.map((m, i) => <span key={i} className="badge badge-teal">{renderStr(m)}</span>)}
                  </div>
                </div>
              )}

              {/* Symptoms */}
              {result.symptoms && result.symptoms.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Symptoms</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {result.symptoms.map((s, i) => <span key={i} className="badge badge-warning">{renderStr(s)}</span>)}
                  </div>
                </div>
              )}

              {/* Structured summary from API */}
              {summary.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">AI Structured Summary</h3>
                  <div className="space-y-2">
                    {summary.map((s: any, i: number) => {
                      const disName = typeof s === 'string' ? s : (renderStr(s.disease) || renderStr(s.name) || 'Condition');
                      const syms = Array.isArray(s.symptoms) ? s.symptoms.map(renderStr).join(', ') : renderStr(s.symptoms);
                      return (
                        <div key={i} className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                          <div className="text-sm font-bold mb-1" style={{ color: '#FF8CA0' }}>{disName}</div>
                          {syms && <div className="text-xs text-[var(--text-muted)]">{syms}</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Clinical warnings */}
              {result.clinical_warnings && result.clinical_warnings.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Clinical Warnings</h3>
                  <div className="space-y-1.5">
                    {result.clinical_warnings.map((w, i) => (
                      <div key={i} className="flex items-start gap-2 p-2 rounded-xl text-xs"
                        style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.2)', color: '#FFD060' }}>
                        <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                        {w}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Triage */}
              {result.triage_info && (
                <div className="flex items-center gap-3 p-3 rounded-xl"
                  style={{ background: 'var(--danger-dim)', border: '1px solid rgba(255,69,96,0.2)' }}>
                  <span className="text-lg">{result.triage_info.badge ?? '🚨'}</span>
                  <div>
                    <div className="text-xs font-bold" style={{ color: 'var(--danger)' }}>Triage Level</div>
                    <div className="text-sm font-semibold text-[var(--text-primary)]">{result.triage_info.level}</div>
                  </div>
                </div>
              )}

              {/* Session ID */}
              {result.session_id && (
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1">Session ID</h3>
                  <div className="mono text-xs p-3 rounded-xl" style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', color: 'var(--teal)' }}>
                    {result.session_id}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
