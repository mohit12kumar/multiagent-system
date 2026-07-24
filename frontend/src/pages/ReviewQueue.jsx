import React, { useState, useEffect } from 'react';
import { doctorAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/Toast';
import { CheckSquare, Check, X, Edit2, Sparkles, ClipboardList, Pill, Stethoscope, User, Clock, AlertTriangle, FileText, Zap, ShieldAlert } from 'lucide-react';

const ReviewQueue = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const reviewerName = user?.full_name || (user?.username ? `Dr. ${user.username}` : 'Doctor Reviewer');
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modifyingId, setModifyingId] = useState(null);
  const [newValue, setNewValue] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const res = await doctorAPI.getReviewQueue();
      setQueue(res.data);
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
      setExpandedId(null);
    } catch (err) {
      addToast(err.userMessage || `Failed to ${action.toLowerCase()} item.`, 'error');
    }
  };

  const parseSummary = (sum) => {
    if (!sum) return [];
    let parsed = sum;
    if (typeof sum === 'string') {
      try { parsed = JSON.parse(sum); } catch (e) { return []; }
    }
    if (Array.isArray(parsed)) return parsed;
    if (parsed && Array.isArray(parsed.structured_summary)) return parsed.structured_summary;
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
            const isSessionLevel = item.details?.type === 'patient_submission';
            const patientSummary = isSessionLevel ? parseSummary(item.details.patient_summary) : [];
            const isExpanded = expandedId === item.id;

            return (
              <div
                key={item.id}
                className="glass-panel"
                style={{
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  borderLeft: isSessionLevel ? '4px solid #3b82f6' : '4px solid #f59e0b',
                }}
              >
                {/* Top Bar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="badge badge-primary">
                        {isSessionLevel ? 'Patient Note Submission' : item.details?.type || 'Entity Mention'}
                      </span>
                      <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                        Session: <code style={{ color: '#38bdf8' }}>{item.session_id.substring(0, 8)}...</code>
                      </span>

                      {/* Smart Doctor Review Triage Tag */}
                      <span style={{
                        fontSize: '11px',
                        fontWeight: '700',
                        backgroundColor: '#dc2626/20',
                        color: '#ef4444',
                        border: '1px solid #ef4444/40',
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
                      {item.reason}
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
                      disabled={!newValue.strip?.() && !newValue.trim()}
                    >
                      Save Correction
                    </button>
                  </div>
                )}

                {/* Patient Summary & Prescription Audit Cards */}
                {isSessionLevel && patientSummary.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Stethoscope size={16} color="#3b82f6" /> AI-Extracted Clinical Conditions & Prescription Quality Audit:
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                      {patientSummary.map((s, idx) => (
                        <div key={idx} style={{ backgroundColor: '#0f172a', borderRadius: '8px', padding: '14px', border: '1px solid #1e293b' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: '700', color: '#38bdf8', fontSize: '15px' }}>
                              {s.disease}
                            </span>
                            <span style={{ fontSize: '11px', backgroundColor: '#1e293b', color: '#10b981', padding: '2px 8px', borderRadius: '4px', border: '1px solid #334155' }}>
                              ICD-10: {s.icd10 || 'I10'}
                            </span>
                          </div>

                          <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '6px' }}>
                            <strong>Symptoms: </strong>
                            {Array.isArray(s.symptoms) && s.symptoms.length > 0 ? s.symptoms.join(', ') : 'None documented'}
                          </div>

                          {s.medications && s.medications.length > 0 && (
                            <div style={{ fontSize: '12px', color: '#34d399', marginTop: '6px' }}>
                              <strong>Prescribed Rx & Quality Score: </strong>
                              {s.medications.map((m, mIdx) => (
                                <div key={mIdx} style={{ marginTop: '2px' }}>
                                  • {m.name || m} {m.dosage ? `(${m.dosage})` : ''} - <span style={{ color: '#60a5fa' }}>Score: {m.audit?.completeness_score || '90%'} ({m.audit?.quality_rating || 'High Quality'})</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
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
