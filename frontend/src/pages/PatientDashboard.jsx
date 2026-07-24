import React, { useState, useEffect } from 'react';
import { patientAPI, triggerBlobDownload } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/Toast';
import { Send, Download, CheckCircle, ShieldCheck, Pill, Stethoscope, UserCheck, Clock, Bell, HourglassIcon, Mic, MicOff, Sparkles } from 'lucide-react';
import WorkflowVisualizer from '../components/WorkflowVisualizer';

const PatientDashboard = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [noteText, setNoteText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [currentStage, setCurrentStage] = useState(16);

  const loadHistory = async () => {
    try {
      const res = await patientAPI.getHistory();
      setHistory(res.data || []);
    } catch (err) {
      addToast(err.userMessage || 'Failed to load medical history.', 'warning');
    }
  };

  useEffect(() => {
    if (user?.id) {
      loadHistory();
    }
  }, [user?.id]);

  // Voice Dictation (Speech-to-Text) using Web Speech API
  const handleVoiceDictation = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      addToast('Voice Speech-to-Text is not supported in this browser. Please use Chrome or Edge.', 'warning');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    if (isListening) {
      recognition.stop();
      setIsListening(false);
      addToast('Voice dictation stopped.', 'info');
      return;
    }

    recognition.onstart = () => {
      setIsListening(true);
      addToast('Listening... Speak your clinical notes now.', 'info');
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setNoteText((prev) => (prev ? prev + ' ' + transcript : transcript));
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const handleDownloadPDF = async (sessionId) => {
    try {
      const res = await patientAPI.downloadPDF(sessionId);
      triggerBlobDownload(res, `patient_clinical_report_${sessionId.substring(0, 8)}.pdf`);
    } catch (err) {
      addToast(err.userMessage || 'Failed to download PDF. Please try again.', 'error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setLoading(true);
    setResult(null);
    setShowNotification(true);
    setCurrentStage(1);

    // Simulate stage progress telemetry in notification popup
    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev >= 16) {
          clearInterval(interval);
          return 16;
        }
        return prev + 3;
      });
    }, 400);

    try {
      const res = await patientAPI.submitNote(noteText);
      setResult(res.data);
      setCurrentStage(16);
      if (res.data?.status === 'PENDING_REVIEW') {
        addToast('⚡ 16-Agent Workflow Complete! Submitted to your doctor for review.', 'info');
      } else {
        addToast('⚡ 16-Agent Workflow Complete! Processed and approved.', 'success');
      }
      setNoteText('');
      loadHistory();
    } catch (err) {
      addToast(err.userMessage || 'Failed to submit clinical note. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: '700' }}>Patient Clinical Portal</h1>
          <p style={{ color: '#94a3b8', marginTop: '4px' }}>
            Submit clinical notes or dictate using AI voice speech-to-text for extraction.
          </p>
        </div>
        <div className="glass-card" style={{ padding: '12px 18px', textAlign: 'right' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8', display: 'block' }}>Active Patient Record</span>
          <strong style={{ fontSize: '15px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <UserCheck size={16} /> Patient ID: {user?.username?.toUpperCase() || 'PATIENT'}
          </strong>
        </div>
      </div>

      {/* Notification Toast Popup for 16-Agent Pipeline */}
      <WorkflowVisualizer
        currentStage={currentStage}
        isOpen={showNotification}
        onClose={() => setShowNotification(false)}
      />

      {/* Note Submission Form */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Submit Clinical Note or Dictate</h3>
          <button
            type="button"
            onClick={handleVoiceDictation}
            className={`btn ${isListening ? 'btn-danger' : 'btn-secondary'}`}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '6px 14px' }}
          >
            {isListening ? <MicOff size={16} className="animate-pulse" /> : <Mic size={16} />}
            {isListening ? 'Stop Listening' : 'Voice Dictation'}
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <textarea
            className="input-field"
            rows={5}
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Type, paste, or dictation: 'Patient presents with fever and cough...'"
            required
            style={{ resize: 'vertical' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldCheck size={16} /> HIPAA PHI Redaction & Standardized Medical Coding Active
            </span>
            <button type="submit" className="btn btn-primary" disabled={loading || !noteText.trim()}>
              {loading ? <div className="spinner" /> : <><Send size={16} /> Run Multi-Agent Extraction</>}
            </button>
          </div>
        </form>
      </div>

      {/* Immediate submission result banner */}
      {result && (
        <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', itemsCenter: 'center', gap: '10px', marginBottom: '8px' }}>
            <HourglassIcon size={20} color="#f59e0b" />
            <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f59e0b' }}>
              Submission Received — Awaiting Doctor Review
            </h3>
          </div>
          <p style={{ fontSize: '14px', color: '#cbd5e1' }}>{result.patient_message}</p>
        </div>
      )}

      {/* Patient Health History */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px' }}>My Verified Medical History</h2>
        {history.length === 0 ? (
          <p style={{ color: '#94a3b8' }}>No clinical notes submitted yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {history.map((h) => {
              const isApproved = h.review_status === 'APPROVED';
              const summary = h.summary;

              return (
                <div key={h.history_id} style={{ backgroundColor: '#0f172a', borderRadius: '12px', padding: '20px', border: '1px solid #1e293b' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                      <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                        Submitted on {h.created_at ? new Date(h.created_at).toLocaleDateString() : 'Recent'}
                      </span>
                      <div style={{ marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {isApproved ? (
                          <span className="badge badge-success" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle size={12} /> Approved & Released by Doctor
                          </span>
                        ) : (
                          <span className="badge badge-warning" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <HourglassIcon size={12} /> Pending Doctor Review
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => handleDownloadPDF(h.session_id)}
                      className="btn btn-secondary"
                      style={{ fontSize: '13px', padding: '6px 12px', gap: '6px' }}
                    >
                      <Download size={14} /> Download PDF Report
                    </button>
                  </div>

                  {isApproved && summary ? (
                    <div style={{ marginTop: '16px', borderTop: '1px solid #1e293b', paddingTop: '16px' }}>
                      <p style={{ fontSize: '14px', color: '#e2e8f0', lineHeight: '1.6' }}>
                        {summary.clinical_notes_overview || 'Your clinical note has been verified by your physician.'}
                      </p>
                    </div>
                  ) : !isApproved ? (
                    <div style={{ marginTop: '12px', fontSize: '13px', color: '#94a3b8', fontStyle: 'italic' }}>
                      🔒 Full summary will be unlocked once your physician completes the clinical pre-check review.
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDashboard;
