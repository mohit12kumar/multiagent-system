import React, { useState, useEffect } from 'react';
import { doctorAPI, patientAPI, triggerBlobDownload } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/Toast';
import { Search, Download, History, FileText, User, Calendar, ShieldCheck, Activity } from 'lucide-react';

const PatientHistory = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [search, setSearch] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async (q = '') => {
    try {
      const res = user?.role === 'doctor'
        ? await doctorAPI.getPatientHistory(q)
        : await patientAPI.getHistory();
      setHistory(res.data || []);
    } catch (err) {
      addToast(err.userMessage || 'Failed to search patient history.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    fetchHistory(val);
  };

  const handleExportPDF = async (sessionId, patientId) => {
    try {
      const res = user?.role === 'doctor'
        ? await doctorAPI.exportPDF(sessionId)
        : await patientAPI.downloadPDF(sessionId);
      triggerBlobDownload(res, `clinical_report_${patientId}_${sessionId.substring(0, 8)}.pdf`);
      addToast(`Downloaded clinical_report_${patientId}.pdf`, 'success');
    } catch (err) {
      addToast(err.userMessage || 'Failed to download PDF.', 'error');
    }
  };

  return (
    <div className="container-fluid animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <History size={24} color="#38BDF8" />
            <h1 style={{ fontSize: '22px', fontWeight: '800' }}>Patient EHR & Clinical History Explorer</h1>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
            Query clinical records, review historical diagnoses, and download PDF reports.
          </p>
        </div>

        {/* Search Bar */}
        <div style={{ display: 'flex', gap: '12px', width: '320px' }}>
          <div style={{ position: 'relative', width: '100%' }}>
            <Search size={16} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              className="input-field"
              style={{ paddingLeft: '36px' }}
              placeholder="Search Patient ID or Disease..."
              value={search}
              onChange={handleSearchChange}
            />
          </div>
        </div>
      </div>

      {/* History Grid Cards */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '80px' }}>
          <div className="spinner" style={{ width: '40px', height: '40px' }} />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
          {history.length === 0 ? (
            <div className="glass-panel" style={{ padding: '32px', gridColumn: '1 / -1', textAlign: 'center', color: '#94A3B8' }}>
              No clinical records matching "{search}" found.
            </div>
          ) : (
            history.map((record, idx) => (
              <div key={idx} className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #4F46E5' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <User size={16} color="#38BDF8" />
                    <strong style={{ fontSize: '15px', color: '#FFFFFF' }}>{record.patient_id}</strong>
                  </div>
                  <span className={`badge ${record.approved_by_doctor ? 'badge-emerald' : 'badge-amber'}`}>
                    {record.approved_by_doctor ? 'VERIFIED' : 'PENDING'}
                  </span>
                </div>

                <div style={{ fontSize: '11px', color: '#94A3B8', fontFamily: 'monospace', marginBottom: '12px' }}>
                  Session: {record.session_id ? record.session_id.substring(0, 14) + '...' : 'N/A'}
                </div>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', fontSize: '12px', color: '#CBD5E1', marginBottom: '16px', lineHeight: '1.6' }}>
                  {typeof record.summary === 'string' ? record.summary : 'Clinical Intake & Entity Extraction Session'}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: '#64748B' }}>
                    <Calendar size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                    {record.created_at ? new Date(record.created_at).toLocaleDateString() : 'Recent'}
                  </span>

                  <button
                    onClick={() => handleExportPDF(record.session_id, record.patient_id)}
                    className="btn btn-primary"
                    style={{ fontSize: '11px', padding: '6px 12px' }}
                  >
                    <Download size={12} /> Download PDF
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default PatientHistory;
