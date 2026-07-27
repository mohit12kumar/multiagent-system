import React, { useState, useEffect } from 'react';
import { patientAPI, triggerBlobDownload } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/Toast';
import { Send, Download, CheckCircle, Mic, MicOff, Sparkles, FileText, Activity, Clock, ShieldCheck, Heart, Pill } from 'lucide-react';
import WorkflowVisualizer from '../components/WorkflowVisualizer';

const PatientDashboard = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [noteText, setNoteText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [currentStage, setCurrentStage] = useState(7);

  const samplePresets = [
    { title: 'Diabetes & Hypertension Note', text: 'Patient reports persistent thirst, fatigue, and blood pressure readings of 142/88 mmHg. HbA1c lab result is 8.2%. Currently taking Metformin 500mg daily.' },
    { title: 'Chest Pain & ECG Note', text: '55 y/o patient presented with retrosternal chest pressure radiating to left arm. ECG demonstrates ST-segment elevation in leads V2-V4. Troponin I elevated at 4.2 ng/mL.' },
    { title: 'Asthma Exacerbation Note', text: 'Patient experiencing acute wheezing, shortness of breath, and night cough. PEFR at 65% of predicted. Using Albuterol MDI 2 puffs Q4H as needed.' },
  ];

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
      addToast('Voice dictation paused.', 'info');
      return;
    }

    recognition.onstart = () => {
      setIsListening(true);
      addToast('Listening... Speak clinical observations clearly.', 'info');
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setNoteText((prev) => (prev ? prev + ' ' + transcript : transcript));
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognition.start();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const res = await patientAPI.submitNote(noteText);
      setResult(res.data);
      addToast('Clinical note ingested! Multi-agent pipeline analysis complete.', 'success');
      loadHistory();
    } catch (err) {
      addToast(err.userMessage || 'Failed to analyze clinical note.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (sessionId) => {
    try {
      const res = await patientAPI.downloadPDF(sessionId);
      triggerBlobDownload(res, `clinical_report_${sessionId.substring(0, 8)}.pdf`);
    } catch (err) {
      addToast(err.userMessage || 'PDF download failed.', 'error');
    }
  };

  return (
    <div className="container-fluid animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={24} color="#38BDF8" />
            <h1 style={{ fontSize: '22px', fontWeight: '800' }}>Patient Clinical Portal & AI Intake</h1>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
            Submit clinical notes or dictate symptoms for automated multi-agent extraction and decision support.
          </p>
        </div>

        <span className="badge badge-emerald">
          <ShieldCheck size={12} /> HIPAA COMPLIANT ENCRYPTION
        </span>
      </div>

      {/* Main Dual Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', alignItems: 'start' }}>
        {/* LEFT COLUMN: NOTE INTAKE & VOICE DICTATION */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Clinical Note Dictation & Input</h3>
            <button
              onClick={handleVoiceDictation}
              className={`btn ${isListening ? 'btn-danger' : 'btn-secondary'}`}
              style={{ fontSize: '11px', padding: '6px 12px' }}
            >
              {isListening ? <MicOff size={14} /> : <Mic size={14} />}
              {isListening ? 'Stop Listening' : 'Voice Dictation'}
            </button>
          </div>

          {/* Quick Preset Chips */}
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
            {samplePresets.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => setNoteText(preset.text)}
                className="btn btn-secondary"
                style={{ fontSize: '10px', padding: '4px 10px', whiteSpace: 'nowrap' }}
              >
                <Sparkles size={12} color="#38BDF8" /> {preset.title}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <textarea
              className="input-field"
              rows={8}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Type clinical observations or click Voice Dictation..."
              style={{ lineHeight: '1.6', fontSize: '13px' }}
            />

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ padding: '12px' }}>
              {loading ? <div className="spinner" /> : <><Send size={16} /> Submit to AI Clinical Pipeline</>}
            </button>
          </form>
        </div>

        {/* RIGHT COLUMN: VERTICAL PATIENT CLINICAL TIMELINE */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Vertical Patient Clinical Timeline</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', paddingLeft: '20px', borderLeft: '2px stroke rgba(79, 70, 229, 0.4)' }}>
            {/* Step 1: Admission */}
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '-27px', top: '2px', width: '12px', height: '12px', borderRadius: '50%', background: '#38BDF8' }} />
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF' }}>1. Patient Intake & Registration</div>
              <div style={{ fontSize: '11px', color: '#94A3B8' }}>Identity verified: Patient PAT-88421</div>
            </div>

            {/* Step 2: Vitals & Labs */}
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '-27px', top: '2px', width: '12px', height: '12px', borderRadius: '50%', background: '#C084FC' }} />
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF' }}>2. Objective Lab & Vitals Ingestion</div>
              <div style={{ fontSize: '11px', color: '#94A3B8' }}>HbA1c 8.2%, Blood Pressure 142/88 mmHg</div>
            </div>

            {/* Step 3: AI Diagnosis */}
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '-27px', top: '2px', width: '12px', height: '12px', borderRadius: '50%', background: '#10B981' }} />
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF' }}>3. Multi-Agent Ontology Extraction</div>
              <div style={{ fontSize: '11px', color: '#94A3B8' }}>Type 2 Diabetes Mellitus (E11.9) & Essential Hypertension (I10)</div>
            </div>

            {/* Step 4: Medication Plan */}
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '-27px', top: '2px', width: '12px', height: '12px', borderRadius: '50%', background: '#F59E0B' }} />
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF' }}>4. Prescribed Medication & Doctor Sign-off</div>
              <div style={{ fontSize: '11px', color: '#94A3B8' }}>Metformin 1000mg BID oral (Safety Score 100%)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboard;
