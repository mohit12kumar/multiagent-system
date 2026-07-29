import { useState } from 'react';
import { submitClinicalNoteApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { InlineSpinner } from '../components/ui/Spinner';
import { Send, FileText, CheckCircle2, Clock, Activity } from 'lucide-react';

export const PatientPortalPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!note.trim()) { toast('Please enter your symptoms or note', 'warning'); return; }
    setLoading(true); setResult(null);
    try {
      const r = await submitClinicalNoteApi(note);
      setResult(r); setNote('');
      toast('Note submitted successfully', 'success');
    } catch (e: any) {
      toast(e.message ?? 'Submission failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 fade-in">
      {/* Welcome card */}
      <div className="glass rounded-2xl p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>
          👤
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--text-primary)]">My Health Portal</h1>
          <p className="text-[var(--text-muted)] mt-0.5 text-sm">
            Welcome, <b style={{ color: 'var(--teal)' }}>{user?.full_name ?? user?.username}</b>.
            Describe your symptoms for AI-powered clinical review.
          </p>
        </div>
      </div>

      {/* Submission form */}
      <div className="glass rounded-2xl p-6">
        <h2 className="font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5" style={{ color: 'var(--teal)' }} />Submit Clinical Note
        </h2>
        <form id="patient-note-form" onSubmit={handleSubmit} className="space-y-4">
          <textarea
            id="patient-note-input"
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Describe your symptoms, current medications, and any relevant medical history…&#10;&#10;Example: I have been experiencing chest pain for the past 2 days, with shortness of breath when walking. I am currently taking Metformin 500mg twice daily for diabetes."
            rows={10}
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

      {/* Result */}
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
    </div>
  );
};
