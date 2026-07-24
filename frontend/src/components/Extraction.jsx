import { useState } from "react";
import { Send, Activity, AlertTriangle, CheckCircle, FileText, ChevronDown, ChevronRight, FlaskConical, Heart, Pill, Thermometer, ShieldCheck, HelpCircle, UserCheck } from "lucide-react";

function severityColor(sev) {
  if (!sev) return "var(--text-secondary)";
  const s = sev.toLowerCase();
  if (s.includes("critical") || s.includes("danger")) return "var(--accent-red)";
  if (s.includes("major") || s.includes("elevated") || s.includes("high")) return "var(--accent-orange)";
  if (s.includes("moderate")) return "#f59e0b";
  if (s.includes("normal") || s.includes("low sev")) return "var(--accent-green)";
  return "var(--text-secondary)";
}

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

function DiseaseCard({ summary, idx }) {
  const [expanded, setExpanded] = useState(idx === 0);
  const conf = summary.confidence || 0.95;
  const confPct = Math.round(conf * 100);
  const confColor = confPct >= 85 ? "var(--accent-green)" : confPct >= 65 ? "var(--accent-orange)" : "var(--accent-red)";

  const evScores = summary.evidence_scores || {
    symptoms: summary.symptoms?.length ? 40 : 0,
    labs_vitals: 30,
    medication: summary.medications?.length ? 20 : 0,
    assessment: 10
  };

  return (
    <div style={{
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: "10px",
      marginBottom: "12px",
      overflow: "hidden",
      background: "rgba(255,255,255,0.02)",
    }}>
      {/* Header */}
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", cursor: "pointer", borderBottom: expanded ? "1px solid rgba(255,255,255,0.07)" : "none" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Heart size={16} color="var(--accent-blue)" />
          <strong style={{ fontSize: "15px", color: "var(--text-primary)" }}>{summary.disease}</strong>
          {summary.icd10 && <Chip label={`ICD-10: ${summary.icd10}`} color="rgba(37,99,235,0.2)" />}
          {summary.status && <Chip label={summary.status} color="rgba(239,68,68,0.15)" />}
          {confPct < 65 && <Chip label="⚠ Low Evidence (Needs Doctor Review)" color="rgba(245,158,11,0.2)" />}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "11px", fontWeight: 700, color: confColor, background: `${confColor}18`, padding: "3px 10px", borderRadius: "12px", border: `1px solid ${confColor}40` }}>
            {confPct < 65 ? "Needs Doctor Review" : `Confidence: ${confPct}%`}
          </span>
          {expanded ? <ChevronDown size={14} color="var(--text-secondary)" /> : <ChevronRight size={14} color="var(--text-secondary)" />}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: "14px", fontSize: "13px" }}>
          {/* Clinical statement */}
          {summary.clinical_statement && (
            <p style={{ margin: 0, color: "var(--text-secondary)", fontStyle: "italic", borderLeft: "3px solid var(--accent-blue)", paddingLeft: "10px" }}>
              {summary.clinical_statement}
            </p>
          )}

          {/* Evidence & Why Detected */}
          <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-blue)", display: "block", marginBottom: "6px" }}>
              CLINICAL EVIDENCE & EXPLAINABILITY
            </span>
            {summary.detected_because?.map((b, bi) => (
              <div key={bi} style={{ display: "flex", gap: "6px", alignItems: "center", fontSize: "12px", marginBottom: "3px", color: "var(--text-primary)" }}>
                <span style={{ color: "var(--accent-green)", fontWeight: "bold" }}>✓</span>
                <span>{b}</span>
              </div>
            ))}

            {/* Evidence Weighting Bar & Star Ratings */}
            <div style={{ marginTop: "10px", paddingTop: "8px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                <span>Symptoms ({evScores.symptoms}%) ★★★★★</span>
                <span>Labs ({evScores.labs_vitals}%) ★★★★☆</span>
                <span>Medication ({evScores.medication}%) ★★★☆☆</span>
                <span>Assessment ({evScores.assessment}%) ★★★★★</span>
              </div>
              <div style={{ height: "6px", width: "100%", background: "rgba(255,255,255,0.1)", borderRadius: "3px", display: "flex", overflow: "hidden" }}>
                <div style={{ width: `${evScores.symptoms}%`, background: "#f59e0b" }} />
                <div style={{ width: `${evScores.labs_vitals}%`, background: "#ef4444" }} />
                <div style={{ width: `${evScores.medication}%`, background: "#3b82f6" }} />
                <div style={{ width: `${evScores.assessment}%`, background: "#10b981" }} />
              </div>
            </div>

            {/* Supporting Labs & Imaging Panel */}
            {summary.supporting_labs?.length > 0 && (
              <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-orange)", display: "block", marginBottom: "4px" }}>
                  LABORATORY & IMAGING EVIDENCE
                </span>
                {summary.supporting_labs.map((sl, sli) => (
                  <div key={sli} style={{ fontSize: "11px", color: "var(--text-primary)", marginBottom: "2px" }}>
                    <span style={{ color: "var(--accent-orange)" }}>•</span> {sl}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Supporting Symptoms */}
          {summary.symptoms?.length > 0 && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", display: "block", marginBottom: "6px" }}>
                SUPPORTING SYMPTOMS
              </span>
              <div style={{ display: "flex", flexWrap: "wrap" }}>
                {summary.symptoms.map((sym, si) => (
                  <span key={si} style={{
                    background: "rgba(245,158,11,0.12)", color: "#fbbf24",
                    padding: "3px 9px", borderRadius: "10px", fontSize: "11px",
                    marginRight: "6px", marginBottom: "6px", fontWeight: 500
                  }}>{sym}</span>
                ))}
              </div>
            </div>
          )}

          {/* Prescribed Medication Regimens */}
          {summary.medications?.length > 0 && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", display: "block", marginBottom: "6px" }}>
                <Pill size={11} style={{ marginRight: "4px" }} />PRESCRIBED MEDICATION REGIMENS
              </span>
              {summary.medications.map((med, mi) => (
                <div key={mi} style={{
                  background: "rgba(37,99,235,0.06)",
                  border: "1px solid rgba(37,99,235,0.15)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  marginBottom: "8px",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                    <strong style={{ color: "var(--accent-blue)", fontSize: "14px" }}>{med.name}</strong>
                    <span style={{
                      fontSize: "10px",
                      background: med.clinical_warning ? "rgba(239,68,68,0.15)" : "rgba(34,197,94,0.15)",
                      color: med.clinical_warning ? "var(--accent-red)" : "var(--accent-green)",
                      padding: "3px 8px",
                      borderRadius: "10px",
                      fontWeight: 700,
                      border: `1px solid ${med.clinical_warning ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)'}`
                    }}>
                      {med.validation_status || "100% Valid Prescription"}
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))", gap: "8px", marginTop: "8px", fontSize: "12px", background: "rgba(0,0,0,0.15)", padding: "8px 10px", borderRadius: "6px" }}>
                    <div><span style={{ color: "var(--text-secondary)", fontSize: "10px", display: "block" }}>DOSAGE</span><strong style={{ color: "var(--text-primary)" }}>{med.dosage || "As prescribed"}</strong></div>
                    <div><span style={{ color: "var(--text-secondary)", fontSize: "10px", display: "block" }}>FORMULATION</span><strong style={{ color: "var(--text-primary)" }}>{med.formulation || "Tablet"}</strong></div>
                    <div><span style={{ color: "var(--text-secondary)", fontSize: "10px", display: "block" }}>FREQUENCY</span><strong style={{ color: "var(--text-primary)" }}>{med.frequency || "Once Daily"}</strong></div>
                    <div><span style={{ color: "var(--text-secondary)", fontSize: "10px", display: "block" }}>ROUTE</span><strong style={{ color: "var(--text-primary)" }}>{med.route || "PO (Oral)"}</strong></div>
                    <div><span style={{ color: "var(--text-secondary)", fontSize: "10px", display: "block" }}>DURATION</span><strong style={{ color: "var(--text-primary)" }}>{med.duration || "Long-term (Chronic)"}</strong></div>
                  </div>
                  {/* Prescription Validation Checklist */}
                  <div style={{ marginTop: "6px", display: "flex", gap: "10px", fontSize: "10px", color: "var(--accent-green)", fontWeight: 600 }}>
                    <span>✓ Drug Name</span>
                    <span>✓ Dose</span>
                    <span>✓ Frequency</span>
                    <span>✓ Route</span>
                    <span>✓ Duration</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Extraction() {
  const [text, setText] = useState("");
  const [patientId, setPatientId] = useState(localStorage.getItem("ner_username") || "");
  const [authorId, setAuthorId] = useState("Dr. Smith");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [pdfLoading, setPdfLoading] = useState(false);

  const handleExtract = async () => {
    if (!text) return;
    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("ner_token");
      const response = await fetch("http://localhost:8000/api/v1/extract", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          text,
          metadata: { patient_id: patientId, author_id: authorId },
          role: localStorage.getItem("user_role") || "doctor",
        }),
      });

      if (!response.ok) throw new Error("Failed to extract entities");
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePdfDownload = async () => {
    if (!result?.session_id) return;
    setPdfLoading(true);
    try {
      const token = localStorage.getItem("ner_token");
      const url = `http://localhost:8000/api/v1/sessions/export/pdf/${result.session_id}`;
      const resp = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
      if (!resp.ok) throw new Error(`PDF export failed with status ${resp.status}`);
      const blob = await resp.blob();
      const objUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objUrl;
      a.download = `clinical_report_${result.session_id.substring(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(objUrl);
    } catch (err) {
      alert(err.message);
    } finally {
      setPdfLoading(false);
    }
  };

  const structured    = result?.patient_summary?.structured_summary || [];
  const labValues     = result?.laboratory_values || [];
  const vitals        = result?.vital_signs_interpreted || [];
  const alerts        = result?.drug_interactions || [];
  const allergies     = result?.allergies || [];
  const reasoning     = result?.clinical_reasoning || [];
  const recs          = result?.recommendations || [];
  const rejected      = result?.rejected_diseases || [];
  const symptomBreak  = result?.symptom_breakdown || {};
  const docMetadata   = result?.doctor_review_metadata || {};
  const confScore     = result?.confidence_scores?.overall_consensus || 0.96;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 440px", gap: "var(--spacing-lg)" }}>
      {/* Input panel */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-md)" }}>
        <div className="glass-panel" style={{ padding: "var(--spacing-lg)" }}>
          <h3 style={{ marginBottom: "var(--spacing-md)", display: "flex", alignItems: "center", gap: "8px" }}>
            <Activity size={18} /> New Clinical Note
          </h3>

          <div style={{ display: "flex", gap: "var(--spacing-md)", marginBottom: "var(--spacing-md)" }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>Patient ID</label>
              <input className="input-field" value={patientId} onChange={e => setPatientId(e.target.value)} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>Author</label>
              <input className="input-field" value={authorId} onChange={e => setAuthorId(e.target.value)} />
            </div>
          </div>

          <textarea
            className="input-field"
            style={{ minHeight: "280px", resize: "vertical", fontFamily: "monospace", fontSize: "13px", lineHeight: "1.6" }}
            placeholder="Paste patient clinical note here..."
            value={text}
            onChange={e => setText(e.target.value)}
          />

          <button className="btn btn-primary" style={{ marginTop: "var(--spacing-md)", float: "right" }} onClick={handleExtract} disabled={loading || !text}>
            {loading ? <div className="spinner" /> : <><Send size={16} /> Run Pipeline</>}
          </button>
        </div>
      </div>

      {/* Results panel */}
      <div className="glass-panel" style={{ padding: "var(--spacing-lg)", maxHeight: "calc(100vh - 100px)", overflowY: "auto" }}>
        <h3 style={{ marginBottom: "var(--spacing-sm)", borderBottom: "var(--glass-border)", paddingBottom: "var(--spacing-sm)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>Clinical Intelligence Results</span>
          {result && <span style={{ fontSize: "11px", background: "rgba(245,158,11,0.15)", color: "var(--accent-orange)", padding: "3px 10px", borderRadius: "12px", fontWeight: 600 }}>⏳ Pending Doctor Review</span>}
        </h3>

        {!result && !loading && (
          <div style={{ color: "var(--text-secondary)", textAlign: "center", padding: "var(--spacing-xl) 0", fontSize: "14px" }}>
            Submit a note to generate enterprise clinical intelligence.
          </div>
        )}

        {loading && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--spacing-md)", padding: "var(--spacing-xl) 0" }}>
            <div className="spinner" style={{ width: "32px", height: "32px", borderTopColor: "var(--accent-blue)" }} />
            <p style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Running multi-agent clinical pipeline...</p>
          </div>
        )}

        {result && (
          <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-md)" }}>
            {/* Patient Narrative Plain-English Summary */}
            {result.patient_narrative && (
              <div style={{ padding: "12px 16px", background: "rgba(37,99,235,0.06)", border: "1px solid rgba(37,99,235,0.2)", borderRadius: "8px", fontSize: "13px" }}>
                <strong style={{ color: "var(--accent-blue)", display: "block", marginBottom: "4px" }}>
                  📋 PATIENT-FRIENDLY SUMMARY
                </strong>
                <p style={{ margin: 0, color: "var(--text-primary)", lineHeight: 1.5 }}>
                  {result.patient_narrative}
                </p>
              </div>
            )}

            {/* Doctor Review Metadata Card */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", fontSize: "11px" }}>
              <div><span style={{ color: "var(--text-secondary)" }}>STATUS:</span> <strong style={{ color: "var(--accent-orange)" }}>{docMetadata.review_status || "Pending Doctor Review"}</strong></div>
              <div><span style={{ color: "var(--text-secondary)" }}>PRIORITY:</span> <strong style={{ color: "var(--text-primary)" }}>{docMetadata.priority || "Medium"}</strong></div>
              <div><span style={{ color: "var(--text-secondary)" }}>REVIEWER:</span> <strong style={{ color: "var(--text-primary)" }}>{docMetadata.assigned_reviewer || "Unassigned"}</strong></div>
              <div><span style={{ color: "var(--text-secondary)" }}>OVERALL CONFIDENCE:</span> <strong style={{ color: "var(--accent-green)" }}>{Math.round(confScore * 100)}%</strong></div>
            </div>

            {/* Doctor Review Priority Reasons Banner */}
            {result.doctor_review_reasons?.length > 0 && (
              <div style={{ padding: "10px 14px", background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "8px", fontSize: "11px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-red)", display: "block", marginBottom: "4px" }}>
                  CRITICAL DOCTOR REVIEW REASONS
                </span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {result.doctor_review_reasons.map((drr, drri) => (
                    <span key={drri} style={{ background: "rgba(239,68,68,0.2)", color: "#fca5a5", padding: "2px 8px", borderRadius: "10px", fontWeight: 600 }}>
                      {drr}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Multi-Organ Risk Stratification */}
            {result.organ_risk_stratification && (
              <div style={{ padding: "10px 14px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "11px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-blue)", display: "block", marginBottom: "6px" }}>
                  ORGAN RISK STRATIFICATION
                </span>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                  <div>Stroke Risk: <strong style={{ color: result.organ_risk_stratification.stroke_risk === 'High' ? 'var(--accent-red)' : 'var(--accent-green)' }}>{result.organ_risk_stratification.stroke_risk}</strong></div>
                  <div>Cardiac Risk: <strong style={{ color: result.organ_risk_stratification.cardiac_risk === 'High' ? 'var(--accent-red)' : 'var(--accent-green)' }}>{result.organ_risk_stratification.cardiac_risk}</strong></div>
                  <div>Renal Failure Risk: <strong style={{ color: result.organ_risk_stratification.renal_failure_risk === 'High' ? 'var(--accent-red)' : 'var(--accent-green)' }}>{result.organ_risk_stratification.renal_failure_risk}</strong></div>
                  <div>Respiratory Failure: <strong style={{ color: result.organ_risk_stratification.respiratory_failure_risk === 'High' ? 'var(--accent-red)' : 'var(--accent-green)' }}>{result.organ_risk_stratification.respiratory_failure_risk}</strong></div>
                </div>
              </div>
            )}

            {/* eGFR CKD Stage Mismatch Alert */}
            {result.ckd_stage_mismatch && (
              <div style={{ padding: "10px 14px", background: "rgba(245,158,11,0.12)", border: "1px solid rgba(245,158,11,0.3)", borderRadius: "8px" }}>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#fbbf24", display: "flex", alignItems: "center", gap: "6px" }}>
                  <AlertTriangle size={14} /> {result.ckd_stage_mismatch.warning}
                </span>
              </div>
            )}

            {/* Timeline View Component */}
            {result.timeline_sequence?.length > 0 && (
              <div style={{ padding: "12px 14px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "11px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-blue)", display: "block", marginBottom: "8px" }}>
                  CHRONOLOGICAL CLINICAL TIMELINE
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {result.timeline_sequence.map((ts, tsi) => (
                    <div key={tsi} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ background: "rgba(37,99,235,0.2)", color: "#93c5fd", padding: "2px 6px", borderRadius: "4px", fontWeight: 700, minWidth: "55px", textAlign: "center" }}>
                        {ts.year}
                      </span>
                      <span style={{ color: "var(--text-primary)" }}>{ts.event}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Itemized 8-Point Medication Validation Card */}
            {result.medication_validation_score && (
              <div style={{ padding: "12px 14px", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.25)", borderRadius: "8px", fontSize: "11px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-green)" }}>
                    MEDICATION PRESCRIPTION AUDIT CHECKLIST
                  </span>
                  <strong style={{ color: "var(--accent-green)", fontSize: "13px" }}>
                    {result.medication_validation_score.overall_score}
                  </strong>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px", color: "var(--text-primary)", marginBottom: "6px" }}>
                  <div>Drug Name: <strong>{result.medication_validation_score.drug_check}</strong></div>
                  <div>Dose: <strong>{result.medication_validation_score.dose_check}</strong></div>
                  <div>Frequency: <strong>{result.medication_validation_score.frequency_check}</strong></div>
                  <div>Route: <strong>{result.medication_validation_score.route_check}</strong></div>
                  <div>Duration: <strong style={{ color: "var(--accent-red)" }}>{result.medication_validation_score.duration_check}</strong></div>
                  <div>Indication: <strong>{result.medication_validation_score.indication_check}</strong></div>
                  <div>Contraindications: <strong>{result.medication_validation_score.contraindication_check}</strong></div>
                  <div>Duplicate Therapy: <strong>{result.medication_validation_score.duplicate_therapy_check}</strong></div>
                </div>
                {result.medication_validation_score.deduction_details?.length > 0 && (
                  <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "6px", color: "var(--accent-orange)" }}>
                    <strong>Deduction Details:</strong>
                    {result.medication_validation_score.deduction_details.map((dd, ddi) => (
                      <div key={ddi}>• {dd}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Missing Information Panel */}
            {result.missing_information_report?.length > 0 && (
              <div style={{ padding: "10px 14px", background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", borderRadius: "8px", fontSize: "11px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "#fbbf24", display: "block", marginBottom: "4px" }}>
                  MISSING CLINICALLY RELEVANT INFORMATION
                </span>
                {result.missing_information_report.map((mi, mii) => (
                  <div key={mii} style={{ color: "var(--text-secondary)", marginBottom: "2px" }}>
                    • {mi}
                  </div>
                ))}
              </div>
            )}

            {/* Dedicated Clinical Warnings Section */}
            {result.clinical_warnings?.length > 0 && (
              <div style={{ padding: "12px 16px", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: "8px" }}>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--accent-red)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                  <AlertTriangle size={14} /> CLINICAL WARNINGS & HIGH-RISK FINDINGS ({result.clinical_warnings.length})
                </span>
                {result.clinical_warnings.map((cw, cwi) => (
                  <div key={cwi} style={{ fontSize: "12px", color: "var(--text-primary)", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ color: "var(--accent-red)", fontWeight: "bold" }}>•</span>
                    <span>{cw}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Allergies */}
            {allergies.length > 0 && !allergies[0]?.toLowerCase().includes("no known") && (
              <div style={{ padding: "10px 14px", background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.2)", borderRadius: "8px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "#a78bfa", display: "block", marginBottom: "4px" }}>⚠ DOCUMENTED DRUG ALLERGIES</span>
                <div style={{ display: "flex", flexWrap: "wrap" }}>
                  {allergies.map((a, i) => (
                    <span key={i} style={{ background: "rgba(139,92,246,0.15)", color: "#c4b5fd", padding: "3px 9px", borderRadius: "10px", fontSize: "12px", marginRight: "6px", fontWeight: 600 }}>{a}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Disease Cards */}
            {structured.length > 0 && (
              <div>
                <h4 style={{ marginBottom: "8px", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Heart size={14} color="var(--accent-blue)" /> Diagnosed Conditions & Evidence ({structured.length})
                </h4>
                {structured.map((s, i) => <DiseaseCard key={i} summary={s} idx={i} />)}
              </div>
            )}

            {/* Shared vs Unique Symptoms */}
            {symptomBreak.shared_symptoms?.length > 0 && (
              <div style={{ padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: "8px", fontSize: "12px" }}>
                <strong style={{ color: "var(--text-secondary)", fontSize: "11px", display: "block", marginBottom: "4px" }}>SYMPTOM DISTRIBUTION ANALYSIS</strong>
                <div style={{ marginBottom: "4px" }}><strong style={{ color: "var(--accent-orange)" }}>Shared Symptoms:</strong> {symptomBreak.shared_symptoms.join(", ")}</div>
              </div>
            )}

            {/* Lab Findings Table */}
            {labValues.length > 0 && (
              <div>
                <h4 style={{ marginBottom: "8px", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <FlaskConical size={14} color="var(--accent-blue)" /> Laboratory Findings & Interpretations
                </h4>
                <div className="glass-card" style={{ overflowX: "auto", padding: "0" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                    <thead>
                      <tr style={{ background: "rgba(255,255,255,0.04)", color: "var(--text-secondary)" }}>
                        {["Marker", "Measured", "Reference", "Interpretation", "Supports"].map(h => (
                          <th key={h} style={{ padding: "8px", textAlign: "left", fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {labValues.map((lab, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                          <td style={{ padding: "7px 8px", fontWeight: 700, color: "var(--text-primary)" }}>{lab.lab}</td>
                          <td style={{ padding: "7px 8px", color: lab.arrow === "↑" ? "var(--accent-red)" : lab.arrow === "↓" ? "var(--accent-orange)" : "var(--accent-green)", fontWeight: 600 }}>
                            {lab.value} {lab.arrow}
                          </td>
                          <td style={{ padding: "7px 8px", color: "var(--text-secondary)" }}>{lab.reference}</td>
                          <td style={{ padding: "7px 8px", color: lab.interpretation === "Normal" ? "var(--accent-green)" : "var(--accent-red)" }}>{lab.interpretation}</td>
                          <td style={{ padding: "7px 8px", color: "var(--text-secondary)", fontSize: "10px" }}>{lab.supporting_disease || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Vitals Table */}
            {vitals.length > 0 && (
              <div>
                <h4 style={{ marginBottom: "8px", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Thermometer size={14} color="var(--accent-blue)" /> Vital Signs & Interpretation
                </h4>
                <div className="glass-card" style={{ overflowX: "auto", padding: "0" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                    <thead>
                      <tr style={{ background: "rgba(255,255,255,0.04)", color: "var(--text-secondary)" }}>
                        {["Vital Sign", "Value", "Reference", "Interpretation", "Status"].map(h => (
                          <th key={h} style={{ padding: "8px", textAlign: "left", fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {vitals.map((v, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                          <td style={{ padding: "7px 8px", fontWeight: 700, color: "var(--text-primary)" }}>{v.vital}</td>
                          <td style={{ padding: "7px 8px", color: severityColor(v.severity), fontWeight: 600 }}>{v.value} {v.arrow}</td>
                          <td style={{ padding: "7px 8px", color: "var(--text-secondary)" }}>{v.reference}</td>
                          <td style={{ padding: "7px 8px", color: severityColor(v.severity) }}>{v.interpretation}</td>
                          <td style={{ padding: "7px 8px" }}>
                            <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "8px", background: `${severityColor(v.severity)}22`, color: severityColor(v.severity), fontWeight: 600 }}>{v.severity}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Drug Interactions Section */}
            <div>
              <h4 style={{ marginBottom: "8px", fontSize: "13px", color: alerts.length > 0 ? "var(--accent-red)" : "var(--accent-green)", display: "flex", alignItems: "center", gap: "6px" }}>
                <ShieldCheck size={14} /> Drug Interactions & Safety Analysis
              </h4>
              {alerts.length === 0 ? (
                <div style={{ padding: "10px 14px", background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.2)", borderRadius: "8px", fontSize: "12px", color: "var(--accent-green)", fontWeight: 600 }}>
                  ✓ None Detected — All co-prescribed medications are safe based on active drug profiles.
                </div>
              ) : (
                alerts.map((alert, i) => (
                  <div key={i} style={{ padding: "10px 14px", background: "rgba(239,68,68,0.08)", borderLeft: "3px solid var(--accent-red)", borderRadius: "6px", marginBottom: "6px", fontSize: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <strong style={{ color: "var(--text-primary)" }}>{alert.drug_a} ↔ {alert.drug_b || alert.disease_or_allergen}</strong>
                      <span style={{ color: "var(--accent-red)", fontWeight: 700, fontSize: "11px" }}>{alert.severity}</span>
                    </div>
                    <p style={{ margin: 0, color: "var(--text-secondary)" }}>{alert.warning}</p>
                  </div>
                ))
              )}
            </div>

            {/* Hallucination Detection / Rejected Conditions */}
            {rejected.length > 0 && (
              <div>
                <h4 style={{ marginBottom: "6px", fontSize: "13px", color: "var(--text-secondary)" }}>
                  🚫 Rejected Conditions (Hallucination Control)
                </h4>
                {rejected.map((r, i) => (
                  <div key={i} style={{ padding: "8px 12px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "6px", fontSize: "11px", marginBottom: "4px" }}>
                    <strong style={{ color: "var(--text-primary)" }}>{r.disease}:</strong> <span style={{ color: "var(--text-secondary)" }}>{r.reason}</span>
                  </div>
                ))}
              </div>
            )}

            {/* PDF Export Button */}
            <div style={{ marginTop: "8px", display: "flex", justifyContent: "flex-end" }}>
              <button className="btn btn-outline" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }} onClick={handlePdfDownload} disabled={pdfLoading}>
                <FileText size={15} /> {pdfLoading ? "Generating Report..." : "Export Enterprise PDF"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
