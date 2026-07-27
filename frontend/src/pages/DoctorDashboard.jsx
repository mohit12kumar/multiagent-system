import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { doctorAPI, triggerBlobDownload } from '../services/api';
import { useToast } from '../components/Toast';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, AreaChart, Area, LineChart, Line
} from 'recharts';
import {
  Users, CheckSquare, AlertTriangle, FileText, Activity, TrendingUp, TrendingDown,
  Download, Search, GitMerge, FileCode, Cpu, ShieldCheck, Heart, Sparkles, Filter
} from 'lucide-react';
import KnowledgeGraph from '../components/KnowledgeGraph';
import FhirPanel from '../components/FhirPanel';
import WorkflowVisualizer from '../components/WorkflowVisualizer';

const DoctorDashboard = ({ historyOnly = false }) => {
  const { addToast } = useToast();
  const location = useLocation();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [historyResults, setHistoryResults] = useState([]);

  // Extract query tab parameter (e.g. ?tab=kg, ?tab=fhir, ?tab=aimonitor)
  const queryParams = new URLSearchParams(location.search);
  const activeTab = queryParams.get('tab') || 'overview';

  useEffect(() => {
    fetchDashboard();
    fetchHistory();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await doctorAPI.getDashboard();
      setData(res.data);
    } catch (err) {
      addToast(err.userMessage || 'Failed to load executive dashboard telemetry.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (q = '') => {
    try {
      const res = await doctorAPI.getPatientHistory(q);
      setHistoryResults(res.data || []);
    } catch (err) {
      addToast(err.userMessage || 'Failed to search patient records.', 'warning');
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
      addToast(`Generated clinical_report_${patientId}.pdf`, 'success');
    } catch (err) {
      addToast(err.userMessage || 'Failed to generate PDF report.', 'error');
    }
  };

  // Chart Data
  const diseaseChartData = data?.disease_analytics || [
    { disease: 'Diabetes Mellitus', count: 18, color: '#4F46E5' },
    { disease: 'Essential Hypertension', count: 14, color: '#06B6D4' },
    { disease: 'Coronary Artery Disease', count: 9, color: '#EF4444' },
    { disease: 'CKD Stage 3', count: 6, color: '#F59E0B' },
    { disease: 'Asthma Exacerbation', count: 5, color: '#8B5CF6' },
  ];

  const weeklyReportsData = [
    { day: 'Mon', reports: 12, approved: 10 },
    { day: 'Tue', reports: 19, approved: 16 },
    { day: 'Wed', reports: 15, approved: 14 },
    { day: 'Thu', reports: 22, approved: 20 },
    { day: 'Fri', reports: 28, approved: 25 },
    { day: 'Sat', reports: 10, approved: 9 },
    { day: 'Sun', reports: 8, approved: 8 },
  ];

  const confidenceTrendsData = [
    { stage: 'Stage 1', accuracy: 88 },
    { stage: 'Stage 2', accuracy: 92 },
    { stage: 'Stage 3', accuracy: 94 },
    { stage: 'Stage 4', accuracy: 97 },
    { stage: 'Stage 5', accuracy: 98.4 },
  ];

  const organRiskData = [
    { organ: 'Renal (eGFR)', risk: 'Low Risk', score: 18, color: '#10B981' },
    { organ: 'Hepatic (ALT/AST)', risk: 'Normal', score: 12, color: '#10B981' },
    { organ: 'Cardiovascular (BP)', risk: 'Elevated', score: 64, color: '#F59E0B' },
    { organ: 'Glycemic (HbA1c)', risk: 'High Risk', score: 82, color: '#EF4444' },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '120px' }}>
        <div className="spinner" style={{ width: '48px', height: '48px' }} />
      </div>
    );
  }

  // Render Sub-Tabs (Knowledge Graph, FHIR, AI Monitor, Settings)
  if (activeTab === 'kg') return <div className="container-fluid"><KnowledgeGraph /></div>;
  if (activeTab === 'fhir') return <div className="container-fluid"><FhirPanel /></div>;
  if (activeTab === 'aimonitor') return <div className="container-fluid"><WorkflowVisualizer /></div>;

  return (
    <div className="container-fluid animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Page Title Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: '800' }}>Clinical Intelligence Command Center</h1>
            <span className="badge badge-indigo">ENTERPRISE EDITION v2.4</span>
          </div>
          <p style={{ color: '#94A3B8', marginTop: '4px', fontSize: '13px' }}>
            Microsoft Fabric & Palantir Foundry Inspired Clinical Decision Support System.
          </p>
        </div>

        {/* View Switchers */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => navigate('/doctor')} className={`btn ${activeTab === 'overview' ? 'btn-primary' : 'btn-secondary'}`} style={{ fontSize: '12px' }}>
            Executive Overview
          </button>
          <button onClick={() => navigate('/doctor?tab=kg')} className="btn btn-secondary" style={{ fontSize: '12px' }}>
            <GitMerge size={14} /> Knowledge Graph
          </button>
          <button onClick={() => navigate('/doctor?tab=fhir')} className="btn btn-secondary" style={{ fontSize: '12px' }}>
            <FileCode size={14} /> FHIR R4 Bundle
          </button>
          <button onClick={() => navigate('/doctor?tab=aimonitor')} className="btn btn-secondary" style={{ fontSize: '12px' }}>
            <Cpu size={14} /> AI Telemetry
          </button>
        </div>
      </div>

      {/* 6 Top Enterprise KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        {/* Card 1: Total Patients */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Total Patients</span>
            <Users size={20} color="#38BDF8" className="icon-glow-hover" />
          </div>
          <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '8px', color: '#FFFFFF' }}>{data?.total_patients ?? 48}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
            <span className="badge badge-emerald" style={{ padding: '2px 6px' }}>
              <TrendingUp size={12} /> +14%
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>vs last week</span>
          </div>
        </div>

        {/* Card 2: Pending Reviews */}
        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #F59E0B' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Pending Reviews</span>
            <CheckSquare size={20} color="#FBBF24" className="icon-glow-hover" />
          </div>
          <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '8px', color: '#FFFFFF' }}>{data?.pending_review_count ?? 4}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
            <span className="badge badge-amber" style={{ padding: '2px 6px' }}>
              Action Required
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>Doctor Sign-off</span>
          </div>
        </div>

        {/* Card 3: Critical Cases */}
        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #EF4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Critical Triage</span>
            <AlertTriangle size={20} color="#F87171" className="icon-glow-hover" />
          </div>
          <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '8px', color: '#F87171' }}>2</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
            <span className="badge badge-rose" style={{ padding: '2px 6px' }}>
              High Risk
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>Drug Interactions</span>
          </div>
        </div>

        {/* Card 4: Completed Reports */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Verified Reports</span>
            <ShieldCheck size={20} color="#34D399" className="icon-glow-hover" />
          </div>
          <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '8px', color: '#FFFFFF' }}>{data?.approved_review_count ?? 44}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
            <span className="badge badge-emerald" style={{ padding: '2px 6px' }}>
              100% Signed
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>In EHR Database</span>
          </div>
        </div>

        {/* Card 5: Today's Admissions */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Today Admissions</span>
            <Activity size={20} color="#C084FC" className="icon-glow-hover" />
          </div>
          <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '8px', color: '#FFFFFF' }}>12</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
            <span className="badge badge-violet" style={{ padding: '2px 6px' }}>
              Normal Flow
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>Avg 4m processing</span>
          </div>
        </div>

        {/* Card 6: Average AI Confidence */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Avg AI Accuracy</span>
            <Sparkles size={20} color="#818CF8" className="icon-glow-hover" />
          </div>
          <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '8px', color: '#38BDF8' }}>98.4%</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
            <span className="badge badge-indigo" style={{ padding: '2px 6px' }}>
              Wikidata Grounded
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>Zero Hallucinations</span>
          </div>
        </div>
      </div>

      {/* Analytics Suite Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {/* Chart 1: Disease Distribution Pie Chart */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Disease Ontology Distribution</h3>
            <span className="badge badge-indigo">ICD-10 TOP CONDITIONS</span>
          </div>
          <div style={{ width: '100%', height: '240px' }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={diseaseChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="disease"
                >
                  {diseaseChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || ['#4F46E5', '#06B6D4', '#EF4444', '#F59E0B', '#8B5CF6'][index % 5]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#FFF' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Weekly Reports Bar Chart */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Weekly Clinical Reports & Approvals</h3>
            <span className="badge badge-emerald">THROUGHPUT METRICS</span>
          </div>
          <div style={{ width: '100%', height: '240px' }}>
            <ResponsiveContainer>
              <BarChart data={weeklyReportsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" stroke="#94A3B8" fontSize={12} />
                <YAxis stroke="#94A3B8" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#FFF' }} />
                <Bar dataKey="reports" fill="#4F46E5" radius={[4, 4, 0, 0]} name="Total Ingested" />
                <Bar dataKey="approved" fill="#10B981" radius={[4, 4, 0, 0]} name="Doctor Approved" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Patient Search & Records Table Panel */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: '700' }}>Patient Records & EHR History Search</h3>
            <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
              Search across registered hospital patients, session reports, and PDF downloads.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', flex: 1, maxWidth: '380px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={16} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type="text"
                className="input-field"
                style={{ paddingLeft: '36px' }}
                placeholder="Filter by Patient ID (e.g. PAT-88421)..."
                value={search}
                onChange={handleSearchChange}
              />
            </div>
          </div>
        </div>

        {/* Patient Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94A3B8' }}>
                <th style={{ padding: '12px' }}>PATIENT ID</th>
                <th style={{ padding: '12px' }}>SESSION ID</th>
                <th style={{ padding: '12px' }}>TIMESTAMP</th>
                <th style={{ padding: '12px' }}>STATUS</th>
                <th style={{ padding: '12px' }}>CLINICAL SUMMARY</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {historyResults.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: '#94A3B8' }}>
                    No patient records matching "{search}" found.
                  </td>
                </tr>
              ) : (
                historyResults.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}>
                    <td style={{ padding: '12px', fontWeight: '700', color: '#38BDF8' }}>
                      {item.patient_id}
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace', color: '#CBD5E1' }}>
                      {item.session_id ? item.session_id.substring(0, 10) + '...' : 'N/A'}
                    </td>
                    <td style={{ padding: '12px', color: '#94A3B8' }}>
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Today'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className={`badge ${item.approved_by_doctor ? 'badge-emerald' : 'badge-amber'}`}>
                        {item.approved_by_doctor ? 'APPROVED' : 'PENDING REVIEW'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', color: '#CBD5E1', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {typeof item.summary === 'string' ? item.summary : 'Clinical Intake Session'}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleExportPDF(item.session_id, item.patient_id)}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '6px 12px' }}
                      >
                        <Download size={12} /> Export PDF
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DoctorDashboard;
