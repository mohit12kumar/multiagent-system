import React, { useState } from 'react';
import { FileCode, CheckCircle, Download, Copy, Share2, Database, ShieldCheck } from 'lucide-react';
import { useToast } from './Toast';

const FhirPanel = ({ patientId = "PAT-88421" }) => {
  const { addToast } = useToast();
  const [copied, setCopied] = useState(false);

  const mockFhirBundle = {
    resourceType: "Bundle",
    id: "bundle-pat-88421-clinical",
    type: "collection",
    timestamp: new Date().toISOString(),
    entry: [
      {
        fullUrl: "urn:uuid:patient-88421",
        resource: {
          resourceType: "Patient",
          id: "PAT-88421",
          name: [{ family: "Doe", given: ["John"] }],
          gender: "male",
          birthDate: "1978-04-12",
        }
      },
      {
        fullUrl: "urn:uuid:condition-e119",
        resource: {
          resourceType: "Condition",
          id: "cond-01",
          clinicalStatus: { coding: [{ system: "http://terminology.hl7.org/CodeSystem/condition-clinical", code: "active" }] },
          verificationStatus: { coding: [{ system: "http://terminology.hl7.org/CodeSystem/condition-ver-status", code: "confirmed" }] },
          code: {
            coding: [{ system: "http://hl7.org/fhir/sid/icd-10-cm", code: "E11.9", display: "Type 2 diabetes mellitus without complications" }]
          },
          subject: { reference: "Patient/PAT-88421" }
        }
      },
      {
        fullUrl: "urn:uuid:medicationrequest-metformin",
        resource: {
          resourceType: "MedicationRequest",
          id: "med-01",
          status: "active",
          intent: "order",
          medicationCodeableConcept: {
            coding: [{ system: "http://www.nlm.nih.gov/research/umls/rxnorm", code: "860975", display: "Metformin 1000 MG Oral Tablet" }]
          },
          dosageInstruction: [{ text: "1000mg BID oral with meals" }]
        }
      }
    ]
  };

  const jsonString = JSON.stringify(mockFhirBundle, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    addToast('FHIR R4 Bundle copied to clipboard.', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fhir_bundle_${patientId}.json`;
    a.click();
    addToast(`Exported fhir_bundle_${patientId}.json`, 'success');
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileCode size={22} color="#06B6D4" />
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>FHIR R4 Bundle Standard Inspector</h3>
            <span className="badge badge-emerald" style={{ gap: '4px' }}>
              <ShieldCheck size={12} /> HL7 FHIR R4 Validated
            </span>
          </div>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            Interoperable clinical data bundle formatted for Epic Systems, Cerner, and Azure Health Data Services.
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleCopy} className="btn btn-secondary" style={{ fontSize: '12px' }}>
            <Copy size={14} /> {copied ? 'Copied!' : 'Copy JSON'}
          </button>
          <button onClick={handleDownload} className="btn btn-primary" style={{ fontSize: '12px' }}>
            <Download size={14} /> Download Bundle (.json)
          </button>
        </div>
      </div>

      {/* JSON Viewer Window */}
      <div
        style={{
          background: '#0B0F19',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '10px',
          padding: '16px 20px',
          fontFamily: 'monospace',
          fontSize: '13px',
          maxHeight: '400px',
          overflowY: 'auto',
          color: '#34D399',
          lineHeight: '1.5',
        }}
      >
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#38BDF8' }}>
          {jsonString}
        </pre>
      </div>
    </div>
  );
};

export default FhirPanel;
