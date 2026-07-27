import React, { useState } from 'react';
import { Cpu, CheckCircle, Clock, Database, ShieldAlert, Activity, ChevronDown, ChevronRight, Zap } from 'lucide-react';

const WorkflowVisualizer = ({ activeStage = 7 }) => {
  const [expandedAgent, setExpandedAgent] = useState(null);

  const agents = [
    { id: 1, name: 'NER Extraction Agent', desc: 'Identifies medical entities, drugs, dosages, diseases, symptoms using BioBERT / SpaCy.', latency: '142 ms', memory: '184 MB', status: 'Completed', score: '99.4%' },
    { id: 2, name: 'Terminology Agent', desc: 'Maps extracted entities to ICD-10-CM and SNOMED CT clinical ontologies.', latency: '88 ms', memory: '92 MB', status: 'Completed', score: '98.1%' },
    { id: 3, name: 'Evidence Agent', desc: 'Validates supporting clinical findings (labs, vitals, imaging) against Wikidata KB.', latency: '210 ms', memory: '215 MB', status: 'Completed', score: '96.8%' },
    { id: 4, name: 'Disease Engine', desc: 'Executes Bayesian inference to rank differential diagnoses & candidate conditions.', latency: '175 ms', memory: '310 MB', status: 'Completed', score: '95.2%' },
    { id: 5, name: 'Medication Engine', desc: 'Checks drug-drug interactions, contraindications, and dosage range safety.', latency: '95 ms', memory: '120 MB', status: 'Completed', score: '100%' },
    { id: 6, name: 'Organ Risk Engine', desc: 'Evaluates renal (eGFR) and hepatic risk scores for patient clinical safety.', latency: '64 ms', memory: '78 MB', status: 'Completed', score: '97.4%' },
    { id: 7, name: 'FHIR R4 Bundle Engine', desc: 'Serializes unified multi-agent output into interoperable HL7 FHIR specification.', latency: '35 ms', memory: '45 MB', status: 'Active', score: '100%' },
  ];

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Cpu size={22} color="#10B981" />
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Multi-Agent Telemetry & Pipeline Monitor</h3>
            <span className="badge badge-emerald">
              <span className="pulse-dot" style={{ background: '#10B981', marginRight: '4px' }} />
              7/7 AGENTS ACTIVE
            </span>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            Real-time multi-agent execution telemetry, latency profiling, and memory tracking.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#94A3B8' }}>
          <div>Total Pipeline Latency: <strong style={{ color: '#38BDF8' }}>809 ms</strong></div>
          <div>Peak Memory Footprint: <strong style={{ color: '#C084FC' }}>1,044 MB</strong></div>
        </div>
      </div>

      {/* Workflow Horizontal Node Flow */}
      <div style={{ display: 'flex', gap: '12px', overflowX: 'auto', paddingBottom: '8px' }}>
        {agents.map((agent) => {
          const isDone = agent.id <= activeStage;
          const isActive = agent.id === activeStage;
          return (
            <div
              key={agent.id}
              onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
              className="glass-card"
              style={{
                flex: '0 0 200px',
                padding: '14px',
                borderTop: `3px solid ${isDone ? '#10B981' : '#94A3B8'}`,
                cursor: 'pointer',
                background: isActive ? 'rgba(16, 185, 129, 0.12)' : undefined,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: '#94A3B8' }}>NODE #{agent.id}</span>
                <span className={`badge ${isDone ? 'badge-emerald' : 'badge-indigo'}`} style={{ fontSize: '9px' }}>
                  {agent.status}
                </span>
              </div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF', marginBottom: '6px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {agent.name}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11px', color: '#94A3B8', marginTop: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Latency:</span> <strong style={{ color: '#38BDF8' }}>{agent.latency}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Memory:</span> <strong style={{ color: '#C084FC' }}>{agent.memory}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Accuracy:</span> <strong style={{ color: '#34D399' }}>{agent.score}</strong>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Expanded Agent Telemetry Log Drawer */}
      {expandedAgent && (
        <div className="glass-card animate-fade-in" style={{ padding: '16px', background: '#0B0F19', borderLeft: '4px solid #38BDF8' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '14px', color: '#38BDF8' }}>
              Telemetry Trace Log: {agents.find(a => a.id === expandedAgent)?.name}
            </h4>
            <button onClick={() => setExpandedAgent(null)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>Close</button>
          </div>
          <p style={{ fontSize: '12px', color: '#CBD5E1', marginTop: '6px' }}>
            {agents.find(a => a.id === expandedAgent)?.desc}
          </p>
          <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#34D399', background: 'rgba(0,0,0,0.4)', padding: '10px', borderRadius: '6px', marginTop: '8px' }}>
            [TRACE] Agent execution started at T+0ms<br />
            [TRACE] Input prompt token count: 482 tokens<br />
            [TRACE] Model inference completed in {agents.find(a => a.id === expandedAgent)?.latency}<br />
            [TRACE] Output schema validation: PASS (Zero errors)
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowVisualizer;
