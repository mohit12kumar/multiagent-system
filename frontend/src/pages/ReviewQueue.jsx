import React, { useState, useEffect } from 'react';
import { doctorAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/Toast';
import { CheckSquare, Check, X, Edit2, Sparkles, Stethoscope, Clock, Zap, Heart, Pill, ChevronDown, ChevronRight, FileText, AlertTriangle, Activity, ShieldCheck } from 'lucide-react';

function Chip({ label, color }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "12px",
      fontSize: "11px",
      fontWeight: 600,
      background: color || "rgba(255,255,255,0.08)",
      color: "var(--text-primary)",
      border: "1px solid rgba(255,255,255,0.12)",
      marginRight: "4px",
      marginBottom: "4px",
    }}>{label}</span>
  );
}

function RichDiseaseCard({ summary, idx }) {
  const [expanded, setExpanded] = useState(idx === 0);
  const diseaseName = summary.disease || summary.name || summary.canonical_name || "Extracted Diagnosis";
  const conf = summary.confidence_score || summary.confidence || 0.95;
  const confPct = Math.round(conf > 1 ? conf : conf * 100);
  const confColor = confPct >= 85 ? "var(--accent-green)" : confPct >= 65 ? "var(--accent-orange)" : "var(--accent-red)";
  const sev = summary.severity || "Moderate";
  const icd10 = summary.icd10 || summary.icd10_code;
  const snomed = summary.snomed || summary.snomed_code;

  return (
    <div style={{
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: "10px",
      marginBottom: "10px",
      overflow: "hidden",
      background: "#0f172a",
    }}>
      {/* Card Header */}
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", cursor: "pointer", borderBottom: expanded ? "1px solid rgba(255,255,255,0.07)" : "none" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <Heart size={16} color="var(--accent-blue)" />
          <strong style={{ fontSize: "15px", color: "#38bdf8" }}>{diseaseName}</strong>
          {icd10 && <Chip label={`ICD-10: ${icd10}`} color="rgba(37,99,235,0.2)" />}
          {snomed && <Chip label={`SNOMED: ${snomed}`} color="rgba(16,185,129,0.15)" />}
          {sev && <Chip label={`Severity: ${sev}`} color={sev.includes("Critical") ? "rgba(239,68,68,0.2)" : "rgba(245,158,11,0.2)"} />}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", fontWeight: 700, color: confColor, background: `${confColor}18`, padding: "3px 10px", borderRadius: "12px", border: `1px solid ${confColor}40` }}>
            Confidence: {confPct}%
          </span>
          {expanded ? <ChevronDown size={14} color="#94a3b8" /> : <ChevronRight size={14} color="#94a3b8" />}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px" }}>
          {/* Detected Because / Clinical Evidence Checklist */}
          {summary.detected_because?.length > 0 && (
            <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-blue)", display: "block", marginBottom: "6px" }}>
                DETECTED BECAUSE (CLINICAL EVIDENCE CHECKLIST)
              </span>
              {summary.detected_because.map((b, bi) => (
                <div key={bi} style={{ display: "flex", gap: "6px", alignItems: "center", fontSize: "12px", marginBottom: "3px", color: "#f8fafc" }}>
                  <span style={{ color: "#10b981", fontWeight: "bold" }}>✓</span>
                  <span>{b}</span>
                </div>
              ))}
            </div>
          )}

          {/* Objective Clinical Findings (Labs, Vitals, Imaging) */}
          {(summary.supporting_evidence?.labs?.length > 0 || summary.supporting_evidence?.vitals?.length > 0 || summary.supporting_labs?.length > 0 || summary.supporting_imaging?.length > 0) && (
            <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-orange)", display: "block", marginBottom: "4px" }}>
                OBJECTIVE CLINICAL EVIDENCE (LABS, VITALS, IMAGING)
              </span>
              {summary.supporting_evidence?.labs?.map((l, li) => (
                <div key={`lab_${li}`} style={{ fontSize: "12px", color: "#f8fafc", marginBottom: "2px" }}>
                  <span style={{ color: "var(--accent-orange)" }}>• Lab:</span> <strong>{l.name}</strong>: {l.value} ({l.status})
                </div>
              ))}
              {summary.supporting_evidence?.vitals?.map((v, vi) => (
                <div key={`vital_${vi}`} style={{ fontSize: "12px", color: "#f8fafc", marginBottom: "2px" }}>
                  <span style={{ color: "var(--accent-orange)" }}>• Vital:</span> <strong>{v.name}</strong>: {v.value} ({v.status})
                </div>
              ))}
              {summary.supporting_evidence?.imaging?.map((img, imi) => (
                <div key={`img_${imi}`} style={{ fontSize: "12px", color: "#f8fafc", marginBottom: "2px" }}>
                  <span style={{ color: "var(--accent-orange)" }}>• Imaging/ECG:</span> <strong>{img.name}</strong>: {img.value}
                </div>
              ))}
              {!summary.supporting_evidence?.labs?.length && summary.supporting_labs?.map((sl, sli) => (
                <div key={sli} style={{ fontSize: "12px", color: "#f8fafc", marginBottom: "2px" }}>
                  <span style={{ color: "var(--accent-orange)" }}>• Lab:</span> {sl.name || sl} {sl.value ? `: ${sl.value}` : ''}
                </div>
              ))}
            </div>
          )}

          {/* Disease-Specific Supporting Symptoms */}
          {(summary.symptoms?.length > 0 || summary.supporting_symptoms?.length > 0) && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                DISEASE-SPECIFIC SUPPORTING SYMPTOMS
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {(summary.symptoms || summary.supporting_symptoms).map((sym, si) => (
                  <span key={si} style={{
                    background: "rgba(245,158,11,0.12)", color: "#fbbf24",
                    padding: "3px 9px", borderRadius: "10px", fontSize: "11px", fontWeight: 500
                  }}>{sym}</span>
                ))}
              </div>
            </div>
          )}

          {/* Prescribed Medications & Quality Audit */}
          {summary.medications?.length > 0 && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                <Pill size={11} style={{ marginRight: "4px" }} />PRESCRIBED MEDICATIONS & QUALITY AUDIT
              </span>
              {summary.medications.map((med, mi) => (
                <div key={mi} style={{
                  background: "rgba(37,99,235,0.06)",
                  border: "1px solid rgba(37,99,235,0.15)",
                  borderRadius: "8px",
                  padding: "8px 12px",
                  marginBottom: "6px",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "4px" }}>
                    <strong style={{ color: "#60a5fa", fontSize: "13px" }}>{med.name || med}</strong>
                    <span style={{ fontSize: "11px", color: "#34d399", fontWeight: 600 }}>
                      Score: {med.audit?.completeness_score || "100%"} ({med.audit?.quality_rating || "High Quality"})
                    </span>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "4px", fontSize: "12px", color: "#94a3b8" }}>
                    {med.dosage && <span><strong style={{ color: "#f8fafc" }}>Dose:</strong> {med.dosage}</span>}
                    {med.frequency && <span><strong style={{ color: "#f8fafc" }}>Freq:</strong> {med.frequency}</span>}
                    {med.route && <span><strong style={{ color: "#f8fafc" }}>Route:</strong> {med.route}</span>}
                    {med.duration && <span><strong style={{ color: "#f8fafc" }}>Duration:</strong> {med.duration}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Prioritized Clinical Action Recommendations */}
          {summary.prioritized_recommendations?.length > 0 && (
            <div style={{ background: "rgba(16,185,129,0.05)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(16,185,129,0.15)" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#10b981", display: "block", marginBottom: "6px" }}>
                PRIORITIZED CLINICAL ACTION RECOMMENDATIONS
              </span>
              {summary.prioritized_recommendations.map((rec, ri) => (
                <div key={ri} style={{ fontSize: "12px", color: "#f8fafc", marginBottom: "4px", display: "flex", gap: "6px", alignItems: "flex-start" }}>
                  <span style={{
                    background: rec.timeframe?.includes("Immediate") ? "rgba(239,68,68,0.2)" : "rgba(37,99,235,0.2)",
                    color: rec.timeframe?.includes("Immediate") ? "#ef4444" : "#60a5fa",
                    padding: "1px 6px", borderRadius: "8px", fontSize: "10px", fontWeight: 700, whiteSpace: "nowrap"
                  }}>
                    {rec.timeframe}
                  </span>
                  <span>{rec.action}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const ReviewQueue = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const reviewerName = user?.full_name || (user?.username ? `Dr. ${user.username}` : 'Doctor Reviewer');
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modifyingId, setModifyingId] = useState(null);
  const [newValue, setNewValue] = useState('');

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const res = await doctorAPI.getReviewQueue();
      setQueue(res.data || []);
    } catch (err) {
      addToast(err.userMessage || 'Failed to load review queue.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (id, action, modVal = null) => {
    try {
      await doctorAPI.takeReviewAction(id, action, reviewerName, modVal);
      const labels = { APPROVED: 'approved ✅', REJECTED: 'rejected ❌', MODIFIED: 'modified ✏️' };
      addToast(`Review item ${labels[action] || action} — patient results released.`, 'success');
      fetchQueue();
      setModifyingId(null);
      setNewValue('');
    } catch (err) {
      addToast(err.userMessage || `Failed to ${action.toLowerCase()} item.`, 'error');
    }
  };

  const parseSummary = (details) => {
    if (!details) return [];
    let target = details;
    if (typeof details === 'string') {
      try { target = JSON.parse(details); } catch (e) { return []; }
    }

    if (Array.isArray(target.patient_summary)) return target.patient_summary;
    if (Array.isArray(target.structured_summary)) return target.structured_summary;
    if (Array.isArray(target.knowledge_graph?.nodes)) return target.knowledge_graph.nodes;
    if (Array.isArray(target.nodes)) return target.nodes;
    if (Array.isArray(target)) return target;

    return [];
  };

  const handleApproveAll = async () => {
    try {
      const res = await doctorAPI.approveAll(reviewerName);
      addToast(`Approved all ${res.data?.approved_count ?? ''} pending items — patients can now view their results.`, 'success');
      fetchQueue();
    } catch (err) {
      addToast(err.userMessage || 'Approve All failed. Please try again.', 'error');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
        <div className="spinner" style={{ width: '40px', height: '40px' }} />
      </div>
    );
  }

  return (
    <div className="container animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: '700' }}>Doctor Review Queue & Triage Command</h1>
          <p style={{ color: '#94a3b8', marginTop: '4px' }}>
            Smart AI Prioritized Patient Review Queue — Approve or modify to release health reports to patients.
          </p>
        </div>
        {queue.length > 0 && (
          <button onClick={handleApproveAll} className="btn btn-success">
            <Sparkles size={16} /> Approve All ({queue.length})
          </button>
        )}
      </div>

      {/* Empty state */}
      {queue.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <CheckSquare size={48} color="#10b981" style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '20px' }}>Review Queue Clear!</h3>
          <p style={{ marginTop: '6px', color: '#94a3b8' }}>All patient submissions have been reviewed and released.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {queue.map((item) => {
            const details = item.details || {};
            const patientSummary = parseSummary(details.patient_summary || details.structured_summary || details);
            const rawNote = details.raw_text || details.text || details.clinical_note || details.note || "";

            return (
              <div
                key={item.id}
                className="glass-panel"
                style={{
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  borderLeft: '4px solid #3b82f6',
                }}
              >
                {/* Top Bar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="badge badge-primary">
                        {details.type || item.type || 'Patient Note Submission'}
                      </span>
                      <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                        Session: <code style={{ color: '#38bdf8' }}>{(item.session_id || 'Session').substring(0, 8)}...</code>
                      </span>
                      <span style={{
                        fontSize: '11px',
                        fontWeight: '700',
                        backgroundColor: 'rgba(220, 38, 38, 0.2)',
                        color: '#ef4444',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <Zap size={12} /> High Priority (Review within 1h)
                      </span>
                    </div>

                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#f8fafc', marginTop: '4px' }}>
                      {item.reason || "Patient-submitted clinical note — awaiting doctor pre-check"}
                    </h3>
                  </div>

                  {/* Quick Action buttons */}
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleAction(item.id, 'APPROVED')}
                      className="btn btn-success"
                      style={{ fontSize: '13px', padding: '8px 16px', gap: '6px' }}
                    >
                      <Check size={16} /> Approve & Release to Patient
                    </button>
                    <button
                      onClick={() => { setModifyingId(modifyingId === item.id ? null : item.id); setNewValue(''); }}
                      className="btn btn-secondary"
                      style={{ fontSize: '13px', padding: '8px 12px', gap: '6px' }}
                    >
                      <Edit2 size={15} /> Modify
                    </button>
                    <button
                      onClick={() => handleAction(item.id, 'REJECTED')}
                      className="btn btn-danger"
                      style={{ fontSize: '13px', padding: '8px 12px', gap: '6px' }}
                    >
                      <X size={15} /> Reject
                    </button>
                  </div>
                </div>

                {/* Inline Modify input */}
                {modifyingId === item.id && (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px', backgroundColor: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                    <input
                      type="text"
                      className="input-field"
                      placeholder="Enter corrected value or doctor notes..."
                      value={newValue}
                      onChange={(e) => setNewValue(e.target.value)}
                      style={{ flex: 1, margin: 0 }}
                    />
                    <button
                      onClick={() => handleAction(item.id, 'MODIFIED', newValue)}
                      className="btn btn-primary"
                      disabled={!newValue.trim()}
                    >
                      Save Correction
                    </button>
                  </div>
                )}

                {/* Submitted Clinical Note Text */}
                {rawNote && (
                  <div style={{ background: "rgba(15,23,42,0.8)", padding: "12px 16px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#94a3b8", display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                      <FileText size={14} color="#38bdf8" /> Submitted Clinical Note Text:
                    </div>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: "13px", color: "#e2e8f0", maxHeight: "160px", overflowY: "auto" }}>
                      {rawNote}
                    </pre>
                  </div>
                )}

                {/* Patient Summary & Enterprise Disease Cards */}
                {patientSummary.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Stethoscope size={16} color="#3b82f6" /> AI-Extracted Clinical Conditions & Prescription Quality Audit:
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {patientSummary.map((s, idx) => (
                        <RichDiseaseCard key={idx} summary={s} idx={idx} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ReviewQueue;
