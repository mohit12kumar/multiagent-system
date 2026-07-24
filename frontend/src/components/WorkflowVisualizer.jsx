import React, { useState } from 'react';
import { X, ChevronDown, ChevronUp, Zap, CheckCircle, Bell } from 'lucide-react';

const STAGES = [
  { id: 1, name: 'OCR / Image Input', icon: '🖼️' },
  { id: 2, name: 'Text Cleaning & Preprocessing', icon: '🧹' },
  { id: 3, name: 'Medical Spell Correction', icon: '📝' },
  { id: 4, name: 'Abbreviation & Hinglish Expansion', icon: '🌐' },
  { id: 5, name: 'PHI Redaction Agent', icon: '🔒' },
  { id: 6, name: 'Multi-Model NER Extraction', icon: '⚡' },
  { id: 7, name: 'Consensus Aggregation Agent', icon: '🗳️' },
  { id: 8, name: 'Taxonomy & Threshold Validation', icon: '🎯' },
  { id: 9, name: 'Semantic Relation Extraction', icon: '🔗' },
  { id: 10, name: 'Lab & Vital Sign Interpreter', icon: '🧪' },
  { id: 11, name: 'Drug Interaction & Safety Check', icon: '⚠️' },
  { id: 12, name: 'ChromaDB RAG Guideline Retrieval', icon: '📚' },
  { id: 13, name: 'Differential Diagnosis & Hallucination Audit', icon: '🔬' },
  { id: 14, name: 'Evidence-Based Confidence Engine', icon: '📊' },
  { id: 15, name: 'Doctor Triage & Patient Summary', icon: '🩺' },
  { id: 16, name: 'Explainable PDF Report Generator', icon: '📄' }
];

export default function WorkflowVisualizer({ currentStage = 16, isOpen = true, onClose }) {
  const [minimized, setMinimized] = useState(false);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        width: minimized ? '340px' : '420px',
        maxHeight: minimized ? '60px' : '520px',
        backgroundColor: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: '16px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
      }}
    >
      {/* Notification Header */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#1e293b',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          borderBottom: minimized ? 'none' : '1px solid #334155'
        }}
        onClick={() => setMinimized(!minimized)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={18} color="#38bdf8" />
          <div>
            <span style={{ fontSize: '13px', fontWeight: '700', color: '#f8fafc', display: 'block' }}>
              ⚡ 16-Agent Pipeline Notification
            </span>
            <span style={{ fontSize: '11px', color: '#34d399' }}>
              {currentStage >= 16 ? 'All 16 Stages Completed ✓' : `Stage ${currentStage}/16 Running...`}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={(e) => { e.stopPropagation(); setMinimized(!minimized); }}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}
          >
            {minimized ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {onClose && (
            <button
              onClick={(e) => { e.stopPropagation(); onClose(); }}
              style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Expanded Stages Body */}
      {!minimized && (
        <div style={{ padding: '12px 16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <p style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
            Real-time execution telemetry & reasoning telemetry:
          </p>

          {STAGES.map((stage) => {
            const isDone = stage.id <= currentStage;
            const isCurrent = stage.id === currentStage;

            return (
              <div
                key={stage.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justify: 'space-between',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  backgroundColor: isCurrent ? 'rgba(37,99,235,0.2)' : isDone ? 'rgba(30,41,59,0.8)' : 'rgba(15,23,42,0.4)',
                  border: isCurrent ? '1px solid #3b82f6' : '1px solid #1e293b',
                  fontSize: '12px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '14px' }}>{stage.icon}</span>
                  <span style={{ fontWeight: isCurrent ? '700' : '500', color: isDone ? '#f1f5f9' : '#64748b' }}>
                    Step {stage.id}: {stage.name}
                  </span>
                </div>

                <span style={{
                  fontSize: '10px',
                  fontWeight: '600',
                  color: isDone ? '#34d399' : '#64748b',
                  backgroundColor: isDone ? 'rgba(16,185,129,0.1)' : 'transparent',
                  padding: '2px 6px',
                  borderRadius: '4px'
                }}>
                  {isDone ? '✓ Completed' : 'Pending'}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
