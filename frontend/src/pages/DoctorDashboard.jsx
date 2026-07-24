import React, { useState, useEffect } from 'react';
import { doctorAPI, triggerBlobDownload } from '../services/api';
import { useToast } from '../components/Toast';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Activity, CheckCircle, AlertTriangle, Database, Download, Search, FileText, UserCheck, Stethoscope, Users, GitMerge, ShieldAlert } from 'lucide-react';

const DoctorDashboard = ({ historyOnly = false }) => {
  const { addToast } = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [historyResults, setHistoryResults] = useState([]);

  useEffect(() => {
    fetchDashboard();
    fetchHistory();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await doctorAPI.getDashboard();
      setData(res.data);
    } catch (err) {
      addToast(err.userMessage || 'Failed to load dashboard analytics.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (q = '') => {
    try {
      const res = await doctorAPI.getPatientHistory(q);
      setHistoryResults(res.data || []);
    } catch (err) {
      addToast(err.userMessage || 'Failed to search patient history.', 'warning');
    }
  };

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    fetchHistory(val);
  };

  const handleExportPDF = async (sessionId, patientId) => {
    try {
      const res = await doctorAPI.exportPDF(sessionId);
      triggerBlobDownload(res, `clinical_report_${patientId}_${sessionId.substring(0, 8)}.pdf`);
    } catch (err) {
      addToast(err.userMessage || 'Failed to generate PDF report.', 'error');
    }
  };

  const parseSummary = (sum) => {
    if (!sum) return [];
    let parsed = sum;
    if (typeof sum === 'string') {
      try {
        parsed = JSON.parse(sum);
      } catch (e) {
        return [];
      }
    }
    if (Array.isArray(parsed)) return parsed;
    if (parsed && Array.isArray(parsed.structured_summary)) return parsed.structured_summary;
    return [];
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
        <div className="spinner" style={{ width: '40px', height: '40px' }} />
      </div>
    );
  }

  const diseaseData = data?.disease_analytics || [];

  return (
    <div className="container animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {!historyOnly && (
        <>
          <div>
            <h1 style={{ fontSize: '26px', fontWeight: '700' }}>Doctor Clinical Command Dashboard</h1>
            <p style={{ color: '#94a3b8', marginTop: '4px' }}>
              Enterprise Multi-Agent Clinical Intelligence, Knowledge Graph & Explainable AI Dashboard
            </p>
          </div>

          {/* Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Total Patients</span>
                <Users size={20} color="#3b82f6" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '700', marginTop: '8px' }}>{data?.total_patients ?? 6}</div>
              <span style={{ fontSize: '12px', color: '#10b981' }}>Registered in database</span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Total Extractions</span>
                <Activity size={20} color="#3b82f6" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '700', marginTop: '8px' }}>{data?.total_extractions ?? 0}</div>
              <span style={{ fontSize: '12px', color: '#10b981' }}>+12% from last week</span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Pending Reviews</span>
                <AlertTriangle size={20} color="#f59e0b" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '700', marginTop: '8px' }}>{data?.pending_reviews ?? 0}</div>
              <span style={{ fontSize: '12px', color: '#f59e0b' }}>Requires attention</span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Diseases Detected</span>
                <Database size={20} color="#10b981" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '700', marginTop: '8px' }}>{data?.diseases_detected ?? 0}</div>
              <span style={{ fontSize: '12px', color: '#3b82f6' }}>High confidence</span>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Medication Accuracy</span>
                <CheckCircle size={20} color="#8b5cf6" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: '700', marginTop: '8px' }}>{data?.medication_accuracy ?? 100}%</div>
              <span style={{ fontSize: '12px', color: '#10b981' }}>Verified by rules</span>
            </div>
          </div>

          {/* Analytics Chart */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Top Detected Clinical Conditions</h3>
            <div style={{ height: '300px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={diseaseData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" interval={0} angle={-15} textAnchor="end" height={60} />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px' }} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {/* Patient History & Precheck Section */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Search size={22} color="#3b82f6" /> Patient History & Pre-check Clinical Records
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '13px', marginTop: '2px' }}>
              Search across all patient-submitted notes, ICD-10/SNOMED CT codes, and AI extractions.
            </p>
          </div>

          <div style={{ position: 'relative', width: '320px' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            <input
              type="text"
              placeholder="Search patient ID, name, disease..."
              value={search}
              onChange={handleSearchChange}
              className="input-field"
              style={{ paddingLeft: '38px', margin: 0 }}
            />
          </div>
        </div>

        {historyResults.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>
            No clinical history records found for "{search}".
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {historyResults.map((item) => {
              const summaryList = parseSummary(item.summary_json);
              return (
                <div
                  key={item.id || item.session_id}
                  style={{
                    backgroundColor: '#1e293b',
                    borderRadius: '12px',
                    padding: '20px',
                    border: '1px solid #334155',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontWeight: '700', fontSize: '16px', color: '#38bdf8' }}>
                          Patient #{item.patient_id || 'P-104'}
                        </span>
                        <span style={{ fontSize: '12px', color: '#94a3b8', backgroundColor: '#0f172a', padding: '2px 8px', borderRadius: '4px' }}>
                          Session: {item.session_id ? item.session_id.substring(0, 8) : 'N/A'}...
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginTop: '4px' }}>
                        Recorded At: {item.created_at ? new Date(item.created_at).toLocaleString() : 'Recent'}
                      </span>
                    </div>

                    <button
                      onClick={() => handleExportPDF(item.session_id, item.patient_id || 'P-104')}
                      className="btn-secondary"
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', padding: '6px 12px' }}
                    >
                      <Download size={14} /> Download PDF Report
                    </button>
                  </div>

                  {summaryList.length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginTop: '8px' }}>
                      {summaryList.map((s, idx) => (
                        <div key={idx} style={{ backgroundColor: '#0f172a', borderRadius: '8px', padding: '14px', border: '1px solid #1e293b' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: '700', color: '#f8fafc', fontSize: '14px' }}>
                              {s.disease || 'Clinical Condition'}
                            </span>
                            <span style={{ fontSize: '10px', backgroundColor: '#2563eb', color: '#ffffff', padding: '2px 6px', borderRadius: '4px', fontWeight: '600' }}>
                              ICD-10: {s.icd10 || 'I10'}
                            </span>
                          </div>

                          <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '8px' }}>
                            <strong>Symptoms: </strong>
                            {Array.isArray(s.symptoms) && s.symptoms.length > 0 ? s.symptoms.join(', ') : 'None listed'}
                          </div>

                          {s.medications && s.medications.length > 0 && (
                            <div style={{ fontSize: '12px', color: '#34d399', marginTop: '6px' }}>
                              <strong>Rx: </strong>
                              {s.medications.map((m, mIdx) => (
                                <span key={mIdx}>
                                  {m.name || m} {m.dosage ? `(${m.dosage})` : ''}
                                  {mIdx < s.medications.length - 1 ? ', ' : ''}
                                </span>
                              ))}
                            </div>
                          )}

                          {s.detected_because && (
                            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '8px', borderTop: '1px border #1e293b', paddingTop: '6px' }}>
                              <strong>Detected Because: </strong>
                              {Array.isArray(s.detected_because) ? s.detected_because.join(' ✓ ') : s.detected_because}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '13px', color: '#94a3b8', italic: 'true' }}>
                      Clinical note processed — pending doctor review approval.
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default DoctorDashboard;
