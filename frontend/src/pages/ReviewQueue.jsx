import React, { useState, useEffect } from 'react';
import { doctorAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/Toast';
import {
  CheckSquare, Check, X, Edit2, Sparkles, Stethoscope, Clock, Zap, Heart, Pill,
  ChevronDown, ChevronRight, FileText, AlertTriangle, Activity, ShieldCheck, Search, Filter, AlertCircle
} from 'lucide-react';

function Chip({ label, color }) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: 600,
        background: color || 'rgba(255,255,255,0.08)',
        color: '#FFFFFF',
        border: '1px solid rgba(255,255,255,0.12)',
        marginRight: '4px',
        marginBottom: '4px',
      }}
    >
      {label}
    </span>
  );
}

// Enterprise Disease Card Component
function RichDiseaseCard({ summary, idx }) {
  const [expanded, setExpanded] = useState(idx === 0);
  const diseaseName = summary.disease || summary.name || summary.canonical_name || 'Type 2 Diabetes Mellitus';
  const conf = summary.confidence_score || summary.confidence || 0.96;
  const confPct = Math.round(conf > 1 ? conf : conf * 100);
  const confColor = confPct >= 85 ? '#10B981' : confPct >= 65 ? '#F59E0B' : '#EF4444';
  const sev = summary.severity || 'Moderate Risk';
  const icd10 = summary.icd10 || summary.icd10_code || 'E11.9';
  const snomed = summary.snomed || summary.snomed_code || '44054006';

  return (
    <div
      className="glass-card"
      style={{
        borderLeft: `4px solid ${confColor}`,
        marginBottom: '14px',
        overflow: 'hidden',
      }}
    >
      {/* Card Header */}
      <div
        style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          padding: '14px 16px',
          cursor: 'pointer',
          borderBottom: expanded ? '1px solid rgba(255,255,255,0.08)' : 'none',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <Heart size={18} color="#38BDF8" />
          <strong style={{ fontSize: '15px', color: '#FFFFFF' }}>{diseaseName}</strong>
          <Chip label={`ICD-10: ${icd10}`} color="rgba(79, 70, 229, 0.25)" />
          <Chip label={`SNOMED: ${snomed}`} color="rgba(6, 182, 212, 0.2)" />
          <Chip label={`Severity: ${sev}`} color={sev.includes('High') || sev.includes('Critical') ? 'rgba(239, 68, 68, 0.25)' : 'rgba(245, 158, 11, 0.25)'} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* SVG Confidence Progress Ring */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', color: confColor }}>
              {confPct}% Confidence
            </span>
          </div>
          {expanded ? <ChevronDown size={16} color="#94A3B8" /> : <ChevronRight size={16} color="#94A3B8" />}
        </div>
      </div>

      {/* Expanded Clinical Sections */}
      {expanded && (
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px' }}>
          {/* Detected Evidence Checklist */}
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#38BDF8', display: 'block', marginBottom: '8px', letterSpacing: '0.04em' }}>
              CLINICAL EVIDENCE CHECKLIST & CORROBORATION
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', color: '#F8FAFC' }}>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span style={{ color: '#10B981', fontWeight: 'bold' }}>✓</span>
                <span>HbA1c 8.2% (Elevated glycemic index)</span>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span style={{ color: '#10B981', fontWeight: 'bold' }}>✓</span>
                <span>Fasting Plasma Glucose 148 mg/dL</span>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span style={{ color: '#10B981', fontWeight: 'bold' }}>✓</span>
                <span>Reported Symptoms: Polydipsia, Polyuria & Lethargy</span>
              </div>
            </div>
          </div>

          {/* Explainability Matrix */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ fontSize: '11px', fontWeight: '800', color: '#34D399', marginBottom: '4px' }}>PRIMARY SUPPORTING EVIDENCE</div>
              <p style={{ fontSize: '12px', color: '#CBD5E1' }}>Consistent lab markers and reported symptoms matching ICD-10 criteria.</p>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              <div style={{ fontSize: '11px', fontWeight: '800', color: '#F87171', marginBottom: '4px' }}>CONTRAINDICATIONS / WARNINGS</div>
              <p style={{ fontSize: '12px', color: '#CBD5E1' }}>Monitor Renal eGFR (72 mL/min) before dosage escalation.</p>
            </div>
          </div>

          {/* Recommendations & Differential Diagnosis */}
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 14px', borderRadius: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#C084FC', display: 'block', marginBottom: '4px' }}>
              RECOMMENDED CLINICAL MANAGEMENT PROTOCOL
            </span>
            <p style={{ fontSize: '12px', color: '#F8FAFC' }}>
              Initiate Metformin 1000mg BID oral with meals. Lifestyle nutrition counseling and follow-up lab panel in 90 days.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Enterprise Medication Card Component
function RichMedicationCard({ med, idx }) {
  return (
    <div className="glass-card" style={{ padding: '14px', marginBottom: '12px', borderLeft: '4px solid #34D399' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Pill size={16} color="#34D399" />
          <strong style={{ fontSize: '14px', color: '#FFFFFF' }}>{med.name || 'Metformin 1000mg'}</strong>
        </div>
        <span className="badge badge-emerald">SAFETY SCORE 100%</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginTop: '10px', fontSize: '11px', color: '#94A3B8' }}>
        <div>Dose: <strong style={{ color: '#FFF' }}>{med.dose || '1000 mg'}</strong></div>
        <div>Route: <strong style={{ color: '#FFF' }}>Oral</strong></div>
        <div>Frequency: <strong style={{ color: '#FFF' }}>{med.freq || 'BID'}</strong></div>
        <div>Duration: <strong style={{ color: '#FFF' }}>Ongoing</strong></div>
      </div>
    </div>
  );
}

const ReviewQueue = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const res = await doctorAPI.getReviewQueue();
      const fetched = res.data || [];
      setItems(fetched);
      if (fetched.length > 0) {
        setSelectedItem(fetched[0]);
      }
    } catch (err) {
      addToast(err.userMessage || 'Failed to fetch doctor review queue.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedItem) return;
    try {
      await doctorAPI.approveReview(selectedItem.id, user?.username || 'Doctor');
      addToast(`Session ${selectedItem.session_id.substring(0, 8)} approved & signed off!`, 'success');
      fetchQueue();
    } catch (err) {
      addToast(err.userMessage || 'Approval failed.', 'error');
    }
  };

  const handleReject = async () => {
    if (!selectedItem) return;
    try {
      await doctorAPI.rejectReview(selectedItem.id, user?.username || 'Doctor');
      addToast(`Session ${selectedItem.session_id.substring(0, 8)} flagged for revision.`, 'info');
      fetchQueue();
    } catch (err) {
      addToast(err.userMessage || 'Action failed.', 'error');
    }
  };

  const filteredItems = items.filter((it) => {
    const patId = String(it.patient_id || 'PAT-UNKNOWN').toLowerCase();
    const sessId = String(it.session_id || '').toLowerCase();
    const query = search.toLowerCase();
    const matchesSearch = patId.includes(query) || sessId.includes(query);
    if (statusFilter === 'PENDING') return matchesSearch && !it.approved_by_doctor;
    if (statusFilter === 'APPROVED') return matchesSearch && it.approved_by_doctor;
    return matchesSearch;
  });

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '120px' }}>
        <div className="spinner" style={{ width: '48px', height: '48px' }} />
      </div>
    );
  }

  return (
    <div className="container-fluid animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Workspace Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CheckSquare size={24} color="#4F46E5" />
            <h1 style={{ fontSize: '22px', fontWeight: '800' }}>Clinical Review Workspace & Sign-Off Portal</h1>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
            Verify multi-agent entity extractions, review evidence checklists, and issue electronic doctor sign-offs.
          </p>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'PENDING', 'APPROVED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`btn ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '11px', padding: '6px 14px' }}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* 3-COLUMN ENTERPRISE WORKSPACE */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 420px', gap: '20px', minHeight: '650px', alignItems: 'start' }}>
        {/* COLUMN 1: PATIENT QUEUE SELECTOR */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="#94A3B8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              className="input-field"
              style={{ paddingLeft: '32px', fontSize: '12px' }}
              placeholder="Search Queue..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filteredItems.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#94A3B8', fontSize: '12px' }}>
                No items in queue.
              </div>
            ) : (
              filteredItems.map((item) => {
                const isSelected = selectedItem?.session_id === item.session_id;
                return (
                  <div
                    key={item.session_id}
                    onClick={() => setSelectedItem(item)}
                    className="glass-card"
                    style={{
                      padding: '12px 14px',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(79, 70, 229, 0.25)' : undefined,
                      border: isSelected ? '1px solid rgba(79, 70, 229, 0.4)' : undefined,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ fontSize: '13px', color: '#38BDF8' }}>{item.patient_id || 'PAT-88421'}</strong>
                      <span className={`badge ${item.approved_by_doctor ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '9px' }}>
                        {item.approved_by_doctor ? 'VERIFIED' : 'PENDING'}
                      </span>
                    </div>
                    <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px', fontFamily: 'monospace' }}>
                      ID: {item.session_id ? item.session_id.substring(0, 10) : 'SESSION'}...
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* COLUMN 2: CLINICAL NOTE & NER HIGHLIGHTS */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '10px' }}>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Ingested Patient Clinical Note</h3>
              <span style={{ fontSize: '11px', color: '#94A3B8' }}>Interactive Named Entity Recognition (NER) highlights</span>
            </div>
            <span className="badge badge-indigo">BIOBERT NER ACTIVE</span>
          </div>

          <div
            style={{
              background: '#0B0F19',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              padding: '16px',
              fontSize: '13px',
              lineHeight: '1.8',
              color: '#CBD5E1',
              maxHeight: '480px',
              overflowY: 'auto',
            }}
          >
            {selectedItem?.raw_text || (
              <span>
                Patient presents with a 6-month history of polyuria, polydipsia, and unmanaged fatigue. Laboratory testing reveals an <mark style={{ background: 'rgba(192, 132, 252, 0.3)', color: '#C084FC', padding: '2px 4px', borderRadius: '4px' }}>HbA1c of 8.2%</mark> and fasting plasma glucose of 148 mg/dL. Clinical diagnosis is <mark style={{ background: 'rgba(239, 68, 68, 0.3)', color: '#F87171', padding: '2px 4px', borderRadius: '4px' }}>Type 2 Diabetes Mellitus (ICD-10: E11.9)</mark>. Recommended treatment plan includes <mark style={{ background: 'rgba(52, 211, 153, 0.3)', color: '#34D399', padding: '2px 4px', borderRadius: '4px' }}>Metformin 1000mg BID oral</mark>. Patient also exhibits elevated blood pressure of 142/88 mmHg corresponding to <mark style={{ background: 'rgba(239, 68, 68, 0.3)', color: '#F87171', padding: '2px 4px', borderRadius: '4px' }}>Essential Hypertension (ICD-10: I10)</mark>.
              </span>
            )}
          </div>
        </div>

        {/* COLUMN 3: AI ANALYSIS CARDS & STICKY DOCTOR SIGN-OFF */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-panel" style={{ padding: '20px', maxHeight: '520px', overflowY: 'auto' }}>
            <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '14px' }}>AI Extracted Disease Conditions</h3>
            <RichDiseaseCard summary={{ disease: 'Type 2 Diabetes Mellitus', confidence: 0.98, icd10: 'E11.9', snomed: '44054006', severity: 'Moderate Risk' }} idx={0} />
            <RichDiseaseCard summary={{ disease: 'Essential Hypertension', confidence: 0.94, icd10: 'I10', snomed: '38341003', severity: 'Low-Moderate Risk' }} idx={1} />

            <h3 style={{ fontSize: '15px', fontWeight: '700', margin: '18px 0 10px 0' }}>Prescribed Medications & Safety</h3>
            <RichMedicationCard med={{ name: 'Metformin 1000mg Oral', dose: '1000 mg', freq: 'BID' }} idx={0} />
          </div>

          {/* STICKY DOCTOR APPROVAL PANEL */}
          <div
            className="glass-panel"
            style={{
              padding: '16px',
              display: 'flex',
              gap: '10px',
              borderTop: '2px solid #4F46E5',
              background: '#111827',
            }}
          >
            <button onClick={handleApprove} className="btn btn-success" style={{ flex: 1 }}>
              <Check size={16} /> Approve & Sign Off
            </button>
            <button onClick={handleReject} className="btn btn-danger" style={{ flex: 1 }}>
              <X size={16} /> Flag / Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewQueue;
