import React, { useState } from 'react';
import { GitMerge, Activity, Pill, Heart, AlertCircle, Eye, Filter, Zap } from 'lucide-react';

const KnowledgeGraph = ({ patientId = "PAT-88421" }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterCategory, setFilterCategory] = useState('ALL');

  // Interactive Graph Node Network
  const nodes = [
    { id: 'patient', label: `Patient: ${patientId}`, type: 'patient', cx: 350, cy: 220, color: '#38BDF8', size: 28 },
    { id: 'dis_1', label: 'Type 2 Diabetes (E11.9)', type: 'disease', cx: 200, cy: 110, color: '#EF4444', size: 22, confidence: 98, icd10: 'E11.9' },
    { id: 'dis_2', label: 'Essential Hypertension (I10)', type: 'disease', cx: 500, cy: 110, color: '#EF4444', size: 22, confidence: 94, icd10: 'I10' },
    { id: 'drug_1', label: 'Metformin 1000mg BID', type: 'drug', cx: 120, cy: 220, color: '#34D399', size: 20, dose: '1000mg BID' },
    { id: 'drug_2', label: 'Lisinopril 10mg QD', type: 'drug', cx: 580, cy: 220, color: '#34D399', size: 20, dose: '10mg QD' },
    { id: 'sym_1', label: 'Polydipsia & Fatigue', type: 'symptom', cx: 220, cy: 330, color: '#FBBF24', size: 18 },
    { id: 'lab_1', label: 'HbA1c 8.2% (Elevated)', type: 'lab', cx: 350, cy: 350, color: '#C084FC', size: 20, val: '8.2%' },
    { id: 'lab_2', label: 'eGFR 72 mL/min (Mild Risk)', type: 'lab', cx: 480, cy: 330, color: '#C084FC', size: 18, val: '72' },
  ];

  const links = [
    { source: 'patient', target: 'dis_1', label: 'Diagnosed' },
    { source: 'patient', target: 'dis_2', label: 'Diagnosed' },
    { source: 'dis_1', target: 'drug_1', label: 'Indicated Rx' },
    { source: 'dis_2', target: 'drug_2', label: 'Indicated Rx' },
    { source: 'dis_1', target: 'sym_1', label: 'Manifests' },
    { source: 'dis_1', target: 'lab_1', label: 'Corroborated by' },
    { source: 'dis_2', target: 'lab_2', label: 'Monitored by' },
    { source: 'patient', target: 'lab_1', label: 'Recent Lab Result' },
  ];

  const getNodePos = (id) => nodes.find((n) => n.id === id) || { cx: 0, cy: 0 };

  const filteredNodes = nodes.filter((n) => {
    if (filterCategory === 'ALL') return true;
    if (filterCategory === 'DISEASE') return n.type === 'disease' || n.type === 'patient';
    if (filterCategory === 'DRUG') return n.type === 'drug' || n.type === 'patient';
    if (filterCategory === 'LAB') return n.type === 'lab' || n.type === 'patient';
    return true;
  });

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Graph Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <GitMerge size={22} color="#818CF8" />
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Clinical Knowledge Graph & Ontology Network</h3>
            <span className="badge badge-indigo">SNOMED CT / ICD-10 Mapped</span>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            Interactive medical graph showing patient entity relationships, drug indications, and lab evidence.
          </p>
        </div>

        {/* Filter Categories */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'DISEASE', 'DRUG', 'LAB'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`btn ${filterCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '11px', padding: '5px 12px', borderRadius: '16px' }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Graph Canvas + Inspector Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 280px' : '1fr', gap: '20px', alignItems: 'start' }}>
        <div
          style={{
            background: 'rgba(11, 15, 25, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '12px',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <svg width="100%" height="420" viewBox="0 0 700 420" style={{ display: 'block' }}>
            <defs>
              <linearGradient id="lineGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4F46E5" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.8" />
              </linearGradient>
              <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Connecting Animated Lines */}
            {links.map((link, idx) => {
              const src = getNodePos(link.source);
              const tgt = getNodePos(link.target);
              return (
                <g key={idx}>
                  <line
                    x1={src.cx}
                    y1={src.cy}
                    x2={tgt.cx}
                    y2={tgt.cy}
                    stroke="rgba(255, 255, 255, 0.15)"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                  />
                  <line
                    x1={src.cx}
                    y1={src.cy}
                    x2={tgt.cx}
                    y2={tgt.cy}
                    stroke="url(#lineGlow)"
                    strokeWidth="1.5"
                    opacity="0.7"
                  />
                </g>
              );
            })}

            {/* Nodes */}
            {filteredNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <g
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                >
                  <circle
                    cx={node.cx}
                    cy={node.cy}
                    r={node.size}
                    fill={node.color}
                    opacity={isSelected ? 1 : 0.85}
                    filter="url(#glowEffect)"
                    stroke={isSelected ? '#FFFFFF' : 'rgba(255,255,255,0.4)'}
                    strokeWidth={isSelected ? 3 : 1.5}
                  />
                  <text
                    x={node.cx}
                    y={node.cy + node.size + 14}
                    textAnchor="middle"
                    fill="#F8FAFC"
                    fontSize="11"
                    fontWeight="600"
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Selected Node Detail Inspector Drawer */}
        {selectedNode && (
          <div className="glass-card animate-fade-in" style={{ padding: '18px', borderLeft: `4px solid ${selectedNode.color}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span className="badge badge-indigo" style={{ fontSize: '10px' }}>{selectedNode.type.toUpperCase()} NODE</span>
              <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: '12px' }}>Close</button>
            </div>
            <h4 style={{ fontSize: '15px', color: '#FFFFFF', marginBottom: '8px' }}>{selectedNode.label}</h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: '#94A3B8' }}>
              {selectedNode.confidence && (
                <div>
                  Confidence Score: <strong style={{ color: '#34D399' }}>{selectedNode.confidence}%</strong>
                </div>
              )}
              {selectedNode.icd10 && (
                <div>
                  ICD-10 Code: <strong style={{ color: '#38BDF8' }}>{selectedNode.icd10}</strong>
                </div>
              )}
              {selectedNode.dose && (
                <div>
                  Dosage Schedule: <strong style={{ color: '#FBBF24' }}>{selectedNode.dose}</strong>
                </div>
              )}
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <strong>Linked Evidence:</strong>
                <ul style={{ paddingLeft: '16px', marginTop: '4px', lineHeight: '1.6' }}>
                  <li>Wikidata Concept ID: Q{Math.floor(10000 + Math.random() * 90000)}</li>
                  <li>SNOMED CT Semantic Tag: Finding</li>
                  <li>Directly connected to Patient PAT-88421</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraph;
