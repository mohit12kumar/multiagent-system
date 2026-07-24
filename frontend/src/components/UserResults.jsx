import { useState, useEffect } from "react";
import { CheckCircle, Activity, FileText, Clock, AlertCircle, Heart, FlaskConical, Thermometer, AlertTriangle, Pill, ChevronDown, ChevronRight } from "lucide-react";

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

function severityColor(sev) {
  if (!sev) return "var(--text-secondary)";
  const s = sev.toLowerCase();
  if (s.includes("critical") || s.includes("danger")) return "var(--accent-red)";
  if (s.includes("major") || s.includes("elevated") || s.includes("high")) return "var(--accent-orange)";
  if (s.includes("moderate")) return "#f59e0b";
  if (s.includes("normal") || s.includes("low sev")) return "var(--accent-green)";
  return "var(--text-secondary)";
}

function DiseaseCard({ summary, idx }) {
  const [expanded, setExpanded] = useState(idx === 0);
  const conf = summary.confidence || 0.9;
  const confPct = Math.round(conf * 100);
  const confColor = confPct >= 85 ? "var(--accent-green)" : confPct >= 65 ? "var(--accent-orange)" : "var(--accent-red)";

  return (
    <div style={{
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: "10px",
      marginBottom: "10px",
      overflow: "hidden",
      background: "rgba(255,255,255,0.02)",
    }}>
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", cursor: "pointer", borderBottom: expanded ? "1px solid rgba(255,255,255,0.07)" : "none" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Heart size={16} color="var(--accent-blue)" />
          <strong style={{ fontSize: "14px", color: "var(--text-primary)" }}>{summary.disease}</strong>
          {summary.status && <Chip label={summary.status} color="rgba(239,68,68,0.15)" />}
          {summary.history && <Chip label={summary.history} color="rgba(255,255,255,0.07)" />}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", fontWeight: 700, color: confColor }}>{confPct}%</span>
          {expanded ? <ChevronDown size={14} color="var(--text-secondary)" /> : <ChevronRight size={14} color="var(--text-secondary)" />}
        </div>
      </div>

      {expanded && (
        <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px" }}>
          {summary.clinical_statement && (
            <p style={{ margin: 0, color: "var(--text-secondary)", fontStyle: "italic", borderLeft: "3px solid var(--accent-blue)", paddingLeft: "10px" }}>
              {summary.clinical_statement}
            </p>
          )}

          {summary.symptoms?.length > 0 && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", display: "block", marginBottom: "6px" }}>
                SUPPORTING SYMPTOMS
              </span>
              <div style={{ display: "flex", flexWrap: "wrap" }}>
                {summary.symptoms.map((sym, si) => (
                  <span key={si} style={{
                    background: "rgba(245,158,11,0.12)", color: "#fbbf24",
                    padding: "2px 8px", borderRadius: "10px", fontSize: "11px",
                    marginRight: "5px", marginBottom: "5px", fontWeight: 500
                  }}>{sym}</span>
                ))}
              </div>
            </div>
          )}

          {summary.medications?.length > 0 && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", display: "block", marginBottom: "6px" }}>
                <Pill size={11} style={{ marginRight: "4px" }} />PRESCRIBED MEDICATIONS
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
                    <strong style={{ color: "var(--accent-blue)", fontSize: "13px" }}>{med.name}</strong>
                    <span style={{
                      fontSize: "10px",
                      color: med.validation_status?.toLowerCase().includes("correct") || med.validation_status?.toLowerCase().includes("verified")
                        ? "var(--accent-green)" : "var(--accent-orange)",
                      fontWeight: 600,
                    }}>{med.validation_status || "Verified"}</span>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "4px", fontSize: "12px", color: "var(--text-secondary)" }}>
                    {med.dosage && <span><strong style={{ color: "var(--text-primary)" }}>Dose:</strong> {med.dosage}</span>}
                    {med.frequency && <span><strong style={{ color: "var(--text-primary)" }}>Freq:</strong> {med.frequency}</span>}
                    {med.route && <span><strong style={{ color: "var(--text-primary)" }}>Route:</strong> {med.route}</span>}
                    {med.duration && <span><strong style={{ color: "var(--text-primary)" }}>Duration:</strong> {med.duration}</span>}
                  </div>
                  {med.validation_reason && (
                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "3px" }}>{med.validation_reason}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {summary.labs?.length > 0 && (
            <div>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                SUPPORTING LABS
              </span>
              <div style={{ display: "flex", flexWrap: "wrap" }}>
                {summary.labs.map((lab, li) => (
                  <span key={li} style={{ background: "rgba(239,68,68,0.1)", color: "var(--accent-red)", padding: "2px 8px", borderRadius: "10px", fontSize: "11px", marginRight: "5px", marginBottom: "4px" }}>{lab}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function UserResults() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pdfLoading, setPdfLoading] = useState({});
  const [pdfError, setPdfError] = useState({});

  const patientId = localStorage.getItem("ner_username") || "";

  useEffect(() => {
    const fetchSessions = async () => {
      if (!patientId) {
        setError("No patient ID found. Please log in again.");
        setLoading(false);
        return;
      }
      try {
        const token = localStorage.getItem("ner_token");
        const response = await fetch(`http://localhost:8000/api/v1/sessions/user/${patientId}?role=user`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) throw new Error("Failed to retrieve history");
        const data = await response.json();
        setSessions(data.sessions || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchSessions();
  }, [patientId]);

  const handlePdfDownload = async (sessionId) => {
    setPdfLoading(prev => ({ ...prev, [sessionId]: true }));
    setPdfError(prev => ({ ...prev, [sessionId]: "" }));
    try {
      const token = localStorage.getItem("ner_token");
      const url = `http://localhost:8000/api/v1/sessions/export/pdf/${sessionId}`;
      const resp = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(`PDF error ${resp.status}: ${errText.substring(0, 80)}`);
      }
      const blob = await resp.blob();
      const objUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objUrl;
      a.download = `clinical_report_${sessionId.substring(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(objUrl);
    } catch (err) {
      setPdfError(prev => ({ ...prev, [sessionId]: err.message }));
    } finally {
      setPdfLoading(prev => ({ ...prev, [sessionId]: false }));
    }
  };

  return (
    <div style={{ maxWidth: "850px", margin: "0 auto" }}>
      <div style={{ marginBottom: "var(--spacing-xl)" }}>
        <h2 style={{ marginBottom: "var(--spacing-sm)" }}>My Results ({patientId})</h2>
        <p style={{ color: "var(--text-secondary)" }}>A history of your submitted clinical notes and structured AI extraction.</p>
      </div>

      {error && (
        <div style={{ marginBottom: "var(--spacing-md)", color: "var(--accent-red)", fontSize: "14px", background: "rgba(239, 68, 68, 0.1)", padding: "var(--spacing-sm)", borderRadius: "8px" }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: "40px" }}>
          <div className="spinner" style={{ margin: "0 auto" }} />
          <p style={{ marginTop: "16px", color: "var(--text-secondary)" }}>Loading history...</p>
        </div>
      ) : sessions.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
          <FileText size={48} style={{ margin: "0 auto var(--spacing-md)", opacity: 0.5 }} />
          <p>You have not submitted any clinical notes yet.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-xl)" }}>
          {sessions.map((session) => {
            const structured = session.patient_summary?.structured_summary || [];
            const labValues = session.laboratory_values || [];
            const vitals = session.vital_signs_interpreted || [];
            const alerts = session.drug_interactions || [];
            const allergies = session.allergies || [];

            return (
              <div key={session.session_id} className="glass-panel animate-fade-in" style={{ padding: "var(--spacing-xl)" }}>
                {/* Session Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--spacing-md)", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "var(--spacing-md)" }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
                      <Clock size={16} color="var(--accent-blue)" />
                      {new Date(session.created_at).toLocaleString()}
                    </h3>
                    <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
                      Session ID: <strong style={{ fontFamily: "monospace", color: "var(--text-primary)" }}>{session.session_id}</strong>
                    </div>
                  </div>

                  {session.status === "COMPLETED" ? (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent-green)", background: "rgba(34, 197, 94, 0.1)", padding: "4px 10px", borderRadius: "20px", fontSize: "12px", fontWeight: "500" }}>
                      <CheckCircle size={14} /> Processed
                    </div>
                  ) : session.status === "FAILED" ? (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent-red)", background: "rgba(239, 68, 68, 0.1)", padding: "4px 10px", borderRadius: "20px", fontSize: "12px", fontWeight: "500" }}>
                      <AlertCircle size={14} /> Failed
                    </div>
                  ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent-orange)", background: "rgba(245, 158, 11, 0.1)", padding: "4px 10px", borderRadius: "20px", fontSize: "12px", fontWeight: "500" }}>
                      <Activity size={14} /> Processing ({session.current_stage})
                    </div>
                  )}
                </div>

                {session.original_text && (
                  <div style={{ marginBottom: "var(--spacing-md)", fontSize: "13px", color: "var(--text-secondary)", background: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "8px", fontStyle: "italic" }}>
                    &quot;{session.original_text.substring(0, 150)}{session.original_text.length > 150 ? "..." : ""}&quot;
                  </div>
                )}

                {session.status !== "COMPLETED" ? (
                  <div style={{ fontSize: "14px", color: "var(--text-secondary)", fontStyle: "italic" }}>
                    Clinical note analysis is in progress. Results will be displayed once completed.
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-md)" }}>
                    {/* Patient Summary Overview */}
                    {session.patient_summary?.clinical_notes_overview && (
                      <div className="glass-card" style={{ padding: "var(--spacing-md)", background: "rgba(59, 130, 246, 0.05)" }}>
                        <h4 style={{ color: "var(--accent-blue)", marginBottom: "8px", fontSize: "13px" }}>Patient Summary Overview</h4>
                        <p style={{ fontSize: "13px", margin: 0, color: "var(--text-secondary)" }}>{session.patient_summary.clinical_notes_overview}</p>
                      </div>
                    )}

                    {/* Allergies */}
                    {allergies.length > 0 && !allergies[0]?.toLowerCase().includes("no known") && (
                      <div style={{ padding: "10px 14px", background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.2)", borderRadius: "8px" }}>
                        <span style={{ fontSize: "11px", fontWeight: 700, color: "#a78bfa", display: "block", marginBottom: "4px" }}>⚠ DOCUMENTED DRUG ALLERGIES</span>
                        <div style={{ display: "flex", flexWrap: "wrap" }}>
                          {allergies.map((a, i) => (
                            <span key={i} style={{ background: "rgba(139,92,246,0.15)", color: "#c4b5fd", padding: "2px 8px", borderRadius: "10px", fontSize: "12px", marginRight: "5px", marginBottom: "4px", fontWeight: 600 }}>{a}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Grouped Disease Cards */}
                    {structured.length > 0 && (
                      <div>
                        <h4 style={{ marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}>
                          <Heart size={14} color="var(--accent-blue)" /> Diagnosed Conditions & Regimens ({structured.length})
                        </h4>
                        {structured.map((summary, idx) => (
                          <DiseaseCard key={idx} summary={summary} idx={idx} />
                        ))}
                      </div>
                    )}

                    {/* Lab Findings Table */}
                    {labValues.length > 0 && (
                      <div>
                        <h4 style={{ marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}>
                          <FlaskConical size={14} color="var(--accent-blue)" /> Laboratory Findings
                        </h4>
                        <div className="glass-card" style={{ overflowX: "auto", padding: "0" }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                            <thead>
                              <tr style={{ background: "rgba(255,255,255,0.04)", color: "var(--text-secondary)", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                                {["Marker", "Value", "Reference", "Interpretation", "Supports"].map(h => (
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
                        <h4 style={{ marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}>
                          <Thermometer size={14} color="var(--accent-blue)" /> Vital Signs
                        </h4>
                        <div className="glass-card" style={{ overflowX: "auto", padding: "0" }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                            <thead>
                              <tr style={{ background: "rgba(255,255,255,0.04)", color: "var(--text-secondary)", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                                {["Vital", "Value", "Reference", "Interpretation", "Status"].map(h => (
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

                    {/* Drug Alerts */}
                    {alerts.length > 0 && (
                      <div>
                        <h4 style={{ marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "var(--accent-red)" }}>
                          <AlertTriangle size={14} /> Safety & Drug Alerts ({alerts.length})
                        </h4>
                        {alerts.map((alert, idx) => (
                          <div key={idx} style={{ padding: "var(--spacing-sm) var(--spacing-md)", background: alert.severity === "Critical" || alert.severity === "Major" ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.1)", borderLeft: alert.severity === "Critical" || alert.severity === "Major" ? "4px solid var(--accent-red)" : "4px solid var(--accent-orange)", borderRadius: "6px", fontSize: "13px", marginBottom: "6px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: "600", marginBottom: "4px" }}>
                              <span style={{ color: "var(--text-primary)" }}>{alert.drug_a} ↔ {alert.drug_b}</span>
                              <span style={{ color: alert.severity === "Critical" || alert.severity === "Major" ? "var(--accent-red)" : "var(--accent-orange)" }}>
                                {alert.severity}
                              </span>
                            </div>
                            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>{alert.warning}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* PDF Download Link */}
                    <div style={{ marginTop: "var(--spacing-md)", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
                      {pdfError[session.session_id] && (
                        <div style={{ fontSize: "12px", color: "var(--accent-red)", padding: "4px 8px" }}>
                          {pdfError[session.session_id]}
                        </div>
                      )}
                      <button
                        className="btn btn-outline"
                        style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                        onClick={() => handlePdfDownload(session.session_id)}
                        disabled={pdfLoading[session.session_id]}
                      >
                        {pdfLoading[session.session_id] ? <div className="spinner" style={{ width: "14px", height: "14px" }} /> : <FileText size={16} />}
                        {pdfLoading[session.session_id] ? "Generating PDF..." : "Download PDF Health Report"}
                      </button>
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
}
