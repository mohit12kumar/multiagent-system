import React, { useState, useEffect } from 'react';
import { patientAPI } from '../services/api';
import { History, Download, FileText } from 'lucide-react';

const PatientHistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await patientAPI.getHistory();
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to fetch patient history:', err);
    } finally {
      setLoading(false);
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
      <div>
        <h1 style={{ fontSize: '26px', fontWeight: '700' }}>Patient Clinical History</h1>
        <p>Your past submitted clinical notes and structured health summaries.</p>
      </div>

      {history.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <History size={48} color="#94a3b8" style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '20px' }}>No Medical Records Yet</h3>
          <p style={{ marginTop: '6px' }}>Submit a clinical note on your portal page to generate your first report.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {history.map((item) => (
            <div key={item.history_id} className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: '600', fontSize: '16px', color: '#f8fafc' }}>
                  Clinical Session #{item.session_id.substring(0, 8)}
                </div>
                <div style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                  Submitted on: {new Date(item.created_at).toLocaleString()}
                </div>
              </div>

              <a
                href={patientAPI.downloadPDF(item.session_id)}
                target="_blank"
                rel="noreferrer"
                className="btn btn-primary"
              >
                <Download size={16} /> Download PDF
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PatientHistoryPage;
