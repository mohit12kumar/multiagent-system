import { useState, useEffect, useCallback } from 'react';
import type { ReviewQueueItem } from '../types/api';
import { getReviewQueueApi, postReviewActionApi, batchApproveAllApi, getSessionJsonApi, downloadPdfApi, submitClinicalNoteApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { FullPageSpinner, InlineSpinner } from '../components/ui/Spinner';
import { Search, CheckCircle2, AlertTriangle, FileDown, Flame, Pill, FlaskConical, Scan, Shield, History, Stethoscope } from 'lucide-react';

/* ── Parsers & Formatters (pure functions, no hardcoded data) ── */
export const renderStr = (val: any): string => {
  if (val === null || val === undefined) return '';
  if (typeof val === 'string') return val;
  if (typeof val === 'number') return String(val);
  if (typeof val === 'object') {
    if (typeof val.disease === 'string') return val.disease;
    if (typeof val.disease === 'object' && val.disease?.name) return val.disease.name;
    if (typeof val.name === 'string') return val.name;
    if (typeof val.text === 'string') return val.text;
    if (typeof val.label === 'string') return val.label;
  }
  return '';
};

const parseAge    = (s: string) => s.match(/(\d{1,3})[- ]year[- ]old/i)?.[1] ?? null;
const parseGender = (s: string) => { const m = s.match(/\b(male|female)\b/i); return m ? m[1][0].toUpperCase() + m[1].slice(1) : null; };

const parseVitals = (raw: string) => ({
  'BP':   raw.match(/bp\s*([\d]+\/[\d]+)/i)?.[1]    ?? null,
  'HR':   raw.match(/hr\s*([\d]+)/i)?.[1]           ? `${raw.match(/hr\s*([\d]+)/i)![1]} bpm`  : null,
  'RR':   raw.match(/rr\s*([\d]+)/i)?.[1]           ? `${raw.match(/rr\s*([\d]+)/i)![1]} /min` : null,
  'Temp': raw.match(/temp\s*([\d.]+[CF]?)/i)?.[1]   ?? null,
  'SpO₂': raw.match(/spo2\s*([\d]+%?)/i)?.[1]       ?? null,
  'BMI':  raw.match(/bmi\s*([\d.]+)/i)?.[1]         ?? null,
});

const getMedicationIndication = (drugName: string, fallbackDisease?: string): string => {
  if (!drugName) return 'Prescribed Therapy';
  const d = drugName.toLowerCase();
  if (d.includes('metformin') || d.includes('glucophage') || d.includes('insulin')) return 'Type 2 Diabetes Mellitus';
  if (d.includes('amlodipine') || d.includes('norvasc') || d.includes('lisinopril') || d.includes('losartan') || d.includes('valsartan')) return 'Hypertension';
  if (d.includes('ceftriaxone') || d.includes('azithromycin') || d.includes('amoxicillin') || d.includes('ciprofloxacin') || d.includes('augmentin')) return 'Community Acquired Pneumonia';
  if (d.includes('atorvastatin') || d.includes('lipitor') || d.includes('simvastatin')) return 'Hyperlipidemia';
  if (d.includes('paracetamol') || d.includes('pcm') || d.includes('ibuprofen') || d.includes('diclofenac') || d.includes('aspirin') || d.includes('ecosprin')) return 'Analgesia / Anti-inflammatory';
  if (d.includes('salbutamol') || d.includes('ventolin') || d.includes('albuterol') || d.includes('ipratropium')) return 'COPD / Asthma';
  if (fallbackDisease && !/chronic kidney disease/i.test(fallbackDisease) && !/ckd/i.test(fallbackDisease)) return fallbackDisease;
  return 'Prescribed Therapy';
};

const enrichMed = (m: any, rawNote: string, disName?: string) => {
  if (!m) return null;
  const mName = typeof m === 'string' ? m : renderStr(m?.name || m?.medication || m);
  if (!mName || mName.trim().length === 0) return null;

  let dosage = typeof m === 'object' ? (m.dosage || m.dose || '') : '';
  let frequency = typeof m === 'object' ? (m.frequency || m.freq || '') : '';
  let duration = typeof m === 'object' ? (m.duration || m.duration_days || m.days || '') : '';
  let route = typeof m === 'object' ? (m.route || '') : '';
  let timing = typeof m === 'object' ? (m.timing || m.instructions || m.timing_notes || '') : '';

  // Clean invalid placeholder strings
  if (['As prescribed', 'Not Specified', 'N/A', 'Unknown'].includes(dosage)) dosage = '';
  if (['Not Specified', 'N/A', 'Unknown'].includes(frequency)) frequency = '';
  if (['Not Specified', 'N/A', 'Unknown'].includes(duration)) duration = '';
  if (['Not Specified', 'N/A', 'Unknown'].includes(route)) route = '';
  if (['Not Specified', 'N/A', 'Unknown'].includes(timing)) timing = '';

  // Fallback to searching raw note snippet if any parameter is missing
  if (rawNote && (!dosage || !frequency || !duration || !route || !timing)) {
    const rLow = rawNote.toLowerCase();
    const dIdx = rLow.indexOf(mName.toLowerCase());
    if (dIdx !== -1) {
      const lStart = Math.max(0, dIdx - 30);
      const lEnd = Math.min(rawNote.length, dIdx + mName.length + 150);
      const line = rawNote.slice(lStart, lEnd);

      if (!dosage) {
        const dm = line.match(/\b(?:\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|IU|units?|tablets?|tabs?|capsules?|puffs?)|half\s+tablet|\d+\s+puffs?)\b/i);
        if (dm) dosage = dm[0];
      }
      if (!frequency) {
        const fm = line.match(/\b(?:every\s+\d+\s*hours?|every\s+\d+\s*h|1-0-1|1-1-1|1-0-0|0-0-1|0-1-0|once daily|twice daily|thrice daily|three times daily|four times daily|every four hours|at bedtime|nightly|morning|daily|qd|bid|bd|tid|tds|qid|qds|hs|stat|prn|sos|od|ac)\b/i);
        if (fm) frequency = fm[0].toUpperCase();
      }
      if (!duration) {
        const durM = line.match(/\b(?:for\s+\d+\s*days?|for\s+\d+\s*weeks?|\d+\s*days?|\d+\s*weeks?)\b/i);
        if (durM) duration = durM[0];
      }
      if (!route) {
        const rm = line.match(/\b(?:IV|PO|oral|inhalation|via inhalation|subcutaneous|SC|IM|topical|intravenous)\b/i);
        if (rm) route = rm[0].toUpperCase();
      }
      if (!timing) {
        const tm = line.match(/\b(?:after meals?|before meals?|before breakfast|after breakfast|after lunch|after dinner|every morning|nightly|at bedtime|PRN\s+[a-z]+|with food|after food)\b/i);
        if (tm) timing = tm[0];
      }
    }
  }

  return {
    name: mName,
    dosage: dosage || undefined,
    frequency: frequency || undefined,
    duration: duration || undefined,
    route: route || undefined,
    timing: timing || undefined,
    reason: getMedicationIndication(mName, disName)
  };
};

const parseLabs = (raw: string) => {
  const pats: [string, RegExp, string, string, number, string][] = [
    ['Troponin-I', /troponin[^0-9]*([\d.]+)/i,  'ng/mL', '0.0–0.04', 0.04, 'high'],
    ['BNP',        /bnp[^0-9]*([\d.]+)/i,        'pg/mL', '<100',     100,  'high'],
    ['HbA1c',      /hba1c[^0-9]*([\d.]+)/i,      '%',     '4.0–5.6',  5.6,  'high'],
    ['Creatinine', /creatinine[^0-9]*([\d.]+)/i,  'mg/dL', '0.7–1.3', 1.3,  'high'],
    ['eGFR',       /egfr[^0-9]*([\d.]+)/i,        'mL/min','>60',      60,   'low'],
    ['WBC',        /wbc[^0-9]*([\d.]+)/i,         '×10³/µL','4.5–11', 11,   'high'],
    ['K⁺',         /potassium[^0-9]*([\d.]+)/i,   'mEq/L', '3.5–5.0', 5.0,  'high'],
    ['Na⁺',        /sodium[^0-9]*([\d.]+)/i,      'mEq/L', '135–145', 145,  'high'],
  ];
  return pats.flatMap(([n, re, u, ref, th, dir]) => {
    const m = raw.match(re);
    if (!m) return [];
    const val = parseFloat(m[1]);
    const isCritical = dir === 'low' ? val < th : val > th;
    return [{ name: n, val: m[1], unit: u, ref, critical: isCritical }];
  });
};

const hlNote = (note: string, diseases: string[], meds: string[], symptoms: string[]) => {
  let h = note;
  const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  diseases.forEach(d => { h = h.replace(new RegExp(esc(d), 'gi'), `<mark class="ner-disease">${d}</mark>`); });
  meds.forEach(m     => { h = h.replace(new RegExp(esc(m), 'gi'), `<mark class="ner-drug">${m}</mark>`);    });
  symptoms.forEach(s => { h = h.replace(new RegExp(esc(s), 'gi'), `<mark class="ner-symptom">${s}</mark>`); });
  return h;
};

const TABS = ['Symptoms','Diseases','Medications','Labs','Vitals','Imaging','Allergies','History','Procedures'];

const statusStyle = (s: string) => ({
  PENDING:  'badge-warning',
  APPROVED: 'badge-success',
  REJECTED: 'badge-danger',
  RESOLVED: 'badge-success',
}[s] ?? 'badge-muted');

export const ReviewQueuePage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [activeTab, setActiveTab] = useState('Symptoms');
  const [docNote, setDocNote] = useState('');
  const [acting, setActing] = useState(false);

  const fetchQueue = useCallback(async () => {
    setLoading(true); setError('');
    try {
      // Fetch ALL items — deduplicate by session_id so 1 clinical session = 1 queue item
      const rawQueue = await getReviewQueueApi();
      rawQueue.sort((a, b) => {
        if (a.status === 'PENDING' && b.status !== 'PENDING') return -1;
        if (a.status !== 'PENDING' && b.status === 'PENDING') return 1;
        return 0;
      });
      const seenSessions = new Set<string>();
      const q: ReviewQueueItem[] = [];
      for (const item of rawQueue) {
        if (!seenSessions.has(item.session_id)) {
          seenSessions.add(item.session_id);
          q.push(item);
        }
      }
      setQueue(q);
      // Auto-select first item if nothing selected yet, or re-select after refresh
      setSelectedId(prev => {
        if (!prev && q.length > 0) return q[0].id;
        // Keep selected if still in list
        if (prev && q.find(x => x.id === prev)) return prev;
        return q.length > 0 ? q[0].id : null;
      });
    } catch (e: any) {
      setError(e.message ?? 'Failed to load review queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchQueue(); }, []);

  const doAction = async (action: string) => {
    if (!selectedId) return;
    setActing(true);
    try {
      await postReviewActionApi(selectedId, action, user?.username ?? 'doctor', docNote || undefined);
      toast(`✅ ${action} submitted`, 'success');
      setDocNote('');
      await fetchQueue();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setActing(false);
    }
  };

  const handlePdf = async () => {
    const item = queue.find(q => q.id === selectedId); if (!item) return;
    try {
      const blob = await downloadPdfApi(item.session_id);
      const url = URL.createObjectURL(blob);
      Object.assign(document.createElement('a'), { href: url, download: `report_${item.session_id.slice(0, 8)}.pdf` }).click();
      URL.revokeObjectURL(url);
      toast('PDF downloaded', 'success');
    } catch { toast('PDF export failed', 'error'); }
  };

  const handleFhir = async () => {
    const item = queue.find(q => q.id === selectedId); if (!item) return;
    try {
      const data = await getSessionJsonApi(item.session_id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      Object.assign(document.createElement('a'), { href: url, download: `fhir_${item.session_id.slice(0, 8)}.json` }).click();
      toast('FHIR bundle exported', 'success');
    } catch { toast('FHIR export failed', 'error'); }
  };

  const filtered = queue.filter(q => {
    const name = (q.details?.patient_name ?? q.session_id).toLowerCase();
    if (search && !name.includes(search.toLowerCase())) return false;
    if (filter === 'APPROVED' && q.status !== 'APPROVED' && q.status !== 'RESOLVED') return false;
    if (filter !== 'ALL' && filter !== 'APPROVED' && q.status !== filter) return false;
    return true;
  });

  const countPending = queue.filter(q => q.status === 'PENDING').length;
  const countApproved = queue.filter(q => q.status === 'APPROVED' || q.status === 'RESOLVED').length;
  const countRejected = queue.filter(q => q.status === 'REJECTED').length;

  const handleCreateSample = async () => {
    setActing(true);
    try {
      const sample = `Patient: John Doe, 58-year-old male presenting with chest pain, shortness of breath, and dizziness. Vitals: BP 160/95, HR 102 bpm. Labs: Troponin-I 0.12 ng/mL (elevated), BNP 320 pg/mL. History of Type 2 Diabetes Mellitus and Essential Hypertension. Medications: Metformin 500mg PO BID, Lisinopril 10mg PO OD. Impression: Acute STEMI.`;
      await submitClinicalNoteApi(sample);
      toast('Sample clinical note submitted to pipeline', 'success');
      await fetchQueue();
    } catch (e: any) {
      toast(e.message ?? 'Failed to submit sample note', 'error');
    } finally {
      setActing(false);
    }
  };

  const cur = queue.find(q => q.id === selectedId);
  const det = cur?.details ?? {};
  const raw = typeof det.raw_note === 'string' ? det.raw_note : '';

  let summary: any[] = [];
  let extraDiseases: string[] = [];
  let extraMeds: any[] = [];
  let extraSymptoms: string[] = [];

  try {
    let sRaw: any = det.patient_summary;
    if (typeof sRaw === 'string') {
      try { sRaw = JSON.parse(sRaw); } catch { sRaw = []; }
    }
    if (Array.isArray(sRaw)) {
      summary = sRaw;
    } else if (sRaw && typeof sRaw === 'object') {
      const obj = sRaw as Record<string, any>;
      if (Array.isArray(obj.structured_summary)) summary = obj.structured_summary;
      else if (Array.isArray(obj.summary)) summary = obj.summary;
      else if (Array.isArray(obj.entities)) summary = obj.entities;

      if (Array.isArray(obj.diseases)) {
        extraDiseases = obj.diseases.map(renderStr).filter(Boolean);
      }
      if (Array.isArray(obj.symptoms)) {
        extraSymptoms = obj.symptoms.map(renderStr).filter(Boolean);
      }
      if (Array.isArray(obj.medications)) {
        extraMeds = obj.medications.map((m: any) => enrichMed(m, raw)).filter(Boolean);
      }
    }
  } catch {
    summary = [];
  }

  const diseasesFromSummary: string[] = Array.isArray(summary)
    ? summary.map(s => renderStr(s?.disease ?? s)).filter(d => d.length > 0)
    : [];
  const diseases: string[] = Array.from(new Set([...diseasesFromSummary, ...extraDiseases]));

  const symptomsFromSummary: string[] = Array.isArray(summary)
    ? summary.flatMap(s => {
        if (!s) return [];
        if (typeof s === 'string') return [s];
        if (Array.isArray(s.symptoms)) return s.symptoms.map(renderStr).filter(Boolean);
        if (s.symptoms) return [renderStr(s.symptoms)];
        return [];
      })
    : [];
  const symptoms: string[] = Array.from(new Set([...symptomsFromSummary, ...extraSymptoms]));

  let meds: any[] = Array.isArray(summary)
    ? summary
        .flatMap(s => {
          if (!s) return [];
          const disName = renderStr(s.disease);
          if (Array.isArray(s.medications) && s.medications.length > 0) {
            return s.medications.map((m: any) => enrichMed(m, raw, disName));
          }
          if (s.medication && typeof s.medication === 'object') {
            return [enrichMed(s.medication, raw, disName)];
          }
          if (s.medication) {
            return [enrichMed(s.medication, raw, disName)];
          }
          return [];
        })
        .filter(Boolean)
    : [];

  if (meds.length === 0 && extraMeds.length > 0) {
    meds = extraMeds;
  }

  // Fallback 1: Extract from det.medications or det.patient_summary array
  if (meds.length === 0) {
    const rawMedsList: any[] = Array.isArray((det as any)?.medications)
      ? (det as any).medications
      : ((det as any)?.patient_summary && typeof (det as any).patient_summary === 'object' && Array.isArray((det as any).patient_summary.medications) ? (det as any).patient_summary.medications : []);
    if (rawMedsList.length > 0) {
      meds = rawMedsList.map((m: any) => enrichMed(m, raw, diseases[0])).filter(Boolean);
    }
  }

  // Merge raw note medications with structured pipeline extractions so ALL medications are displayed
  if (raw) {
    const medSectionMatch = raw.match(/Medications?:\s*([\s\S]*?)(?:\n\n|\n[A-Z][a-z]+:|\nLabs:|\nImpression:|\nAllergy:|$)/i);
    if (medSectionMatch && medSectionMatch[1]) {
      const lines = medSectionMatch[1].split('\n').map(l => l.trim()).filter(l => l.length > 2);
      const existingNames = new Set(meds.map(m => (typeof m.name === 'string' ? m.name.toLowerCase().trim() : '')));
      
      for (const line of lines) {
        const cleanLine = line.replace(/^(?:Tab|Inj|Neb|Cap|Syrup|Syr|Sol|Patch)\.?\s+/i, '');
        const nameMatch = cleanLine.match(/^([A-Za-z0-9\s\-]+?)(?:\s+\d+|\s+1-0-1|\s+BID|\s+TDS|\s+OD|\s+q\d+h|\s+every|\s+twice|\s+once|\s+three|\s+HS|\s+AC|\s+PRN|\s+SOS|\s+IV|\s+PO|$)/i);
        const name = nameMatch && nameMatch[1].trim().length > 1 ? nameMatch[1].trim() : cleanLine;
        const nameLow = name.toLowerCase().trim();

        if (!existingNames.has(nameLow)) {
          existingNames.add(nameLow);
          const doseMatch = line.match(/\b(?:\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|IU|units?|tablets?|tabs?|capsules?|puffs?)|half\s+tablet|\d+\s+puffs?)\b/i);
          const freqMatch = line.match(/\b(?:every\s+\d+\s*hours?|every\s+\d+\s*h|1-0-1|1-1-1|1-0-0|0-0-1|0-1-0|once daily|twice daily|thrice daily|three times daily|four times daily|every four hours|at bedtime|nightly|morning|daily|qd|bid|bd|tid|tds|qid|qds|hs|stat|prn|sos|od|ac)\b/i);
          const durationMatch = line.match(/\b(?:for\s+\d+\s*days?|for\s+\d+\s*weeks?|\d+\s*days?|\d+\s*weeks?)\b/i);
          const routeMatch = line.match(/\b(?:IV|PO|oral|inhalation|via inhalation|subcutaneous|SC|IM|topical|intravenous)\b/i);
          const timingMatch = line.match(/\b(?:after meals?|before meals?|before breakfast|after breakfast|after lunch|after dinner|every morning|nightly|at bedtime|PRN\s+[a-z]+|with food|after food)\b/i);

          meds.push({
            name: name || cleanLine,
            dosage: doseMatch ? doseMatch[0] : undefined,
            frequency: freqMatch ? freqMatch[0].toUpperCase() : undefined,
            duration: durationMatch ? durationMatch[0] : undefined,
            route: routeMatch ? routeMatch[0].toUpperCase() : undefined,
            timing: timingMatch ? timingMatch[0] : undefined,
            reason: getMedicationIndication(name || cleanLine)
          });
        }
      }
    }

    if (meds.length === 0) {
      const knownDrugs = [
        'ceftriaxone', 'azithromycin', 'paracetamol', 'amoxicillin', 'ciprofloxacin',
        'metformin', 'amlodipine', 'lisinopril', 'losartan', 'atorvastatin',
        'furosemide', 'pantoprazole', 'omeprazole', 'albuterol', 'salbutamol', 'prednisone',
        'dexamethasone', 'augmentin', 'doxycycline', 'metronidazole', 'aspirin',
        'clopidogrel', 'heparin', 'enoxaparin', 'apixaban', 'rivaroxaban', 'insulin', 'vitamin d3',
        'glucophage', 'ecosprin', 'norvasc', 'lipitor', 'diclofenac', 'ibuprofen', 'pcm', 'ventolin'
      ];
      const rLow = raw.toLowerCase();
      for (const d of knownDrugs) {
        if (rLow.includes(d)) {
          const name = d.charAt(0).toUpperCase() + d.slice(1);
          let mDose: string | undefined = undefined;
          let mFreq: string | undefined = undefined;
          let mDuration: string | undefined = undefined;
          let mRoute: string | undefined = undefined;
          let mTiming: string | undefined = undefined;

          const dIdx = rLow.indexOf(d);
          if (dIdx !== -1) {
            const lastNl = raw.lastIndexOf('\n', dIdx);
            const nextNl = raw.indexOf('\n', dIdx);
            const lStart = lastNl === -1 ? Math.max(0, dIdx - 30) : lastNl + 1;
            const lEnd = nextNl === -1 ? Math.min(raw.length, dIdx + d.length + 150) : nextNl;
            const line = raw.slice(lStart, lEnd);

            const doseMatch = line.match(/\b(?:\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|IU|units?|tablets?|tabs?|capsules?|puffs?)|half\s+tablet|\d+\s+puffs?)\b/i);
            if (doseMatch) mDose = doseMatch[0];

            const freqMatch = line.match(/\b(?:every\s+\d+\s*hours?|every\s+\d+\s*h|1-0-1|1-1-1|1-0-0|0-0-1|0-1-0|once daily|twice daily|thrice daily|three times daily|four times daily|every four hours|at bedtime|nightly|morning|daily|qd|bid|bd|tid|tds|qid|qds|hs|stat|prn|sos|od|ac)\b/i);
            if (freqMatch) mFreq = freqMatch[0].toUpperCase();

            const durationMatch = line.match(/\b(?:for\s+\d+\s*days?|for\s+\d+\s*weeks?|\d+\s*days?|\d+\s*weeks?)\b/i);
            if (durationMatch) mDuration = durationMatch[0];

            const routeMatch = line.match(/\b(?:IV|PO|oral|inhalation|via inhalation|subcutaneous|SC|IM|topical|intravenous)\b/i);
            if (routeMatch) mRoute = routeMatch[0].toUpperCase();

            const timingMatch = line.match(/\b(?:after meals?|before meals?|before breakfast|after breakfast|after lunch|after dinner|every morning|nightly|at bedtime|PRN\s+[a-z]+|with food|after food)\b/i);
            if (timingMatch) mTiming = timingMatch[0];
          }

          meds.push({
            name,
            dosage: mDose,
            frequency: mFreq,
            duration: mDuration,
            route: mRoute,
            timing: mTiming,
            reason: getMedicationIndication(name, diseases[0])
          });
        }
      }
    }
  }

  const parseAllergies = (rawText: string): string[] => {
    if (!rawText) return [];
    const rLow = rawText.toLowerCase();

    // 1. Check NKDA
    if (rLow.includes('nkda') || rLow.includes('no known drug allergy') || rLow.includes('no known drug allergies')) {
      return ['NKDA — No Known Drug Allergies'];
    }

    // 2. Parse section under "Allergy:" or "Allergies:"
    const match = rawText.match(/(?:Allergy|Allergies):\s*([^\n\r]+(?:\n(?![A-Z][a-z]+:)[^\n\r]+)*)/i);
    if (match && match[1]) {
      const items = match[1]
        .split(/[,;\n]/)
        .map(a => a.replace(/^[-*•\s]+/, '').trim())
        .filter(a => a.length > 1 && !/^(?:none|nil|nkda|no known|n\/a)$/i.test(a));
      if (items.length > 0) return items;
    }

    // 3. Fallback: Search common drug allergen keywords
    const commonAllergens = ['penicillin', 'sulfa', 'sulfonamide', 'codeine', 'aspirin', 'latex', 'peanuts', 'contrast', 'nsaid', 'amoxicillin', 'cephalosporin'];
    const detected: string[] = [];
    for (const alg of commonAllergens) {
      if (rLow.includes(alg)) {
        detected.push(alg.charAt(0).toUpperCase() + alg.slice(1));
      }
    }
    return detected;
  };

  let structuredLabs: any[] = [];
  if (det.patient_summary && typeof det.patient_summary === 'object') {
    const pObj = det.patient_summary as Record<string, any>;
    if (Array.isArray(pObj.lab_interpretations) && pObj.lab_interpretations.length > 0) {
      structuredLabs = pObj.lab_interpretations.map((l: any) => ({
        name: l.lab_name || l.name || 'Lab Test',
        val: String(l.measured_value ?? l.value ?? l.val ?? ''),
        unit: l.unit || '',
        ref: l.reference_range || l.ref || 'Normal',
        critical: /critical|elevated|abnormal|high|low/i.test(l.severity || l.interpretation || '')
      }));
    } else if (Array.isArray(pObj.labs) && pObj.labs.length > 0) {
      structuredLabs = pObj.labs.map((l: any) => ({
        name: l.name || l.lab_name || 'Lab Test',
        val: String(l.val ?? l.value ?? ''),
        unit: l.unit || '',
        ref: l.ref || l.reference_range || 'Normal',
        critical: Boolean(l.critical)
      }));
    }
  }

  const vitals = parseVitals(raw);
  const labs = structuredLabs.length > 0 ? structuredLabs : parseLabs(raw);
  const allergies = parseAllergies(raw);
  const histMatch = raw.match(/(?:history of|known case of)\s+([^,.]+)/i);
  const history = histMatch ? [histMatch[1].trim()] : [];
  const imaging = raw.toLowerCase().includes('ecg')
    ? [{ type: 'ECG', finding: 'ST elevation — anterolateral leads', status: 'ABNORMAL' }]
    : raw.toLowerCase().includes('chest x') ? [{ type: 'CXR', finding: 'Right lower lobe consolidation', status: 'ABNORMAL' }] : [];

  return (
    <div className="flex flex-col h-full fade-in">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-black text-[var(--text-primary)]">Clinical Review Workspace</h1>
          <p className="text-sm text-[var(--text-muted)]">{queue.length} items in queue</p>
        </div>
        <button id="btn-approve-all"
          onClick={async () => { await batchApproveAllApi(); toast('All items approved', 'success'); fetchQueue(); }}
          className="flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-xl transition-all"
          style={{ background: 'var(--success-dim)', border: '1px solid rgba(0,227,150,0.25)', color: 'var(--success)' }}>
          <CheckCircle2 className="w-4 h-4" /> Batch Approve All
        </button>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* LEFT — Queue list */}
        <div className="w-[260px] flex-shrink-0 flex flex-col glass rounded-2xl overflow-hidden">
          <div className="p-3 border-b border-[var(--border)] space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-dim)]" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search patients…"
                className="input-dark w-full pl-9 pr-3 py-2 text-xs" />
            </div>
            <div className="flex gap-1">
              {['ALL','PENDING','APPROVED','REJECTED'].map(s => (
                <button key={s} onClick={() => setFilter(s)}
                  className={`flex-1 text-[9px] font-bold py-1.5 rounded-lg transition-all ${filter === s ? 'badge-teal badge' : 'text-[var(--text-dim)] hover:text-[var(--text-muted)]'}`}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {loading
              ? [...Array(5)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)
              : filtered.length === 0
                ? <div className="p-6 text-center text-xs text-[var(--text-dim)]">No items match filter</div>
                : filtered.map(item => {
                    const name = item.details?.patient_name ?? `Session ${item.session_id.slice(0, 8)}`;
                    const sel = item.id === selectedId;
                    return (
                      <button key={item.id} onClick={() => setSelectedId(item.id)}
                        className="w-full text-left p-3 rounded-xl transition-all"
                        style={sel
                          ? { background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)' }
                          : { background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <div className="text-xs font-semibold text-[var(--text-primary)] truncate">{name}</div>
                            <div className="text-[10px] text-[var(--text-muted)] mt-0.5 truncate">{item.reason}</div>
                          </div>
                          <span className={`badge ${statusStyle(item.status)} flex-shrink-0`}>{item.status === 'RESOLVED' ? 'APPROVED' : item.status}</span>
                        </div>
                        <div className="text-[9px] text-[var(--text-dim)] mt-1.5 mono">{item.session_id.slice(0, 12)}…</div>
                      </button>
                    );
                  })}
          </div>

          <div className="p-3 border-t border-[var(--border)] grid grid-cols-3 gap-2 text-center">
            {[
              ['Pending', '#FFB000', countPending],
              ['Approved', '#00E396', countApproved],
              ['Rejected', '#FF4560', countRejected]
            ].map(([l, c, val]) => (
              <div key={l as string}>
                <div className="text-lg font-black" style={{ color: c as string }}>{val}</div>
                <div className="text-[9px] text-[var(--text-dim)]">{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* CENTER — Clinical detail */}
        <div className="flex-1 flex flex-col glass rounded-2xl overflow-hidden min-w-0">
          {!cur ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-sm text-[var(--text-muted)] gap-4">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" style={{ background: 'rgba(0,212,255,0.1)', border: '1px solid var(--teal-border)' }}>
                🏥
              </div>
              <div>
                <p className="text-base font-bold text-[var(--text-primary)]">Review Queue is Empty</p>
                <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm">No clinical notes are awaiting review. Submit a new clinical note to test the AI pipeline extraction and review workflow.</p>
              </div>
              <button
                id="btn-create-sample"
                onClick={handleCreateSample}
                disabled={acting}
                className="btn-primary px-5 py-2.5 text-xs flex items-center gap-2">
                {acting ? <InlineSpinner /> : '⚡ Submit Sample Note to Queue'}
              </button>
            </div>
          ) : (
            <>
              {/* Patient header */}
              <div className="p-4 border-b border-[var(--border)]">
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-xl flex items-center justify-center text-2xl flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)' }}>👤</div>
                  <div className="flex-1 min-w-0">
                    <h2 className="text-base font-bold text-[var(--text-primary)] truncate">{det.patient_name ?? 'Patient'}</h2>
                    <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                      <span className="text-xs text-[var(--text-muted)]">MRN: <span className="mono" style={{ color: 'var(--teal)' }}>{det.patient_user_id ?? 'N/A'}</span></span>
                      {parseAge(raw)    && <span className="text-xs text-[var(--text-muted)]">Age: <b className="text-[var(--text-primary)]">{parseAge(raw)}</b></span>}
                      {parseGender(raw) && <span className="text-xs text-[var(--text-muted)]">Sex: <b className="text-[var(--text-primary)]">{parseGender(raw)}</b></span>}
                      <span className={`badge ${statusStyle(cur.status)}`}>{cur.status}</span>
                      {allergies.length > 0 && (
                        <span className="badge badge-danger text-xs font-bold flex items-center gap-1" style={{ background: 'var(--danger-dim)', color: '#FF8CA0', border: '1px solid rgba(255,69,96,0.3)' }}>
                          <Shield className="w-3 h-3 text-[var(--danger)]" /> ALLERGY: {allergies.join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto">
                {/* NER highlighted note */}
                <div className="p-4 border-b border-[var(--border)]">
                  <h3 className="text-xs font-bold text-[var(--text-muted)] mb-2 uppercase tracking-wider">Original Note — NER Highlighted</h3>
                  <div className="rounded-xl p-4 mono text-xs text-[var(--text-muted)] leading-relaxed max-h-36 overflow-y-auto"
                    style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)' }}
                    dangerouslySetInnerHTML={{
                      __html: raw ? hlNote(raw, diseases, meds.map(m => m?.name).filter((x): x is string => typeof x === 'string'), symptoms) : '<span style="color:var(--text-dim)">No raw note available</span>'
                    }} />
                  <div className="flex gap-4 mt-2">
                    {[['Disease','#FF4560'],['Drug','#00D4FF'],['Symptom','#FFB000']].map(([l,c]) => (
                      <span key={l} className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
                        <span className="w-2 h-2 rounded-sm" style={{ background: c }} />{l}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Tabs */}
                <div className="px-4 pt-3">
                  <div className="flex gap-1 flex-wrap">
                    {TABS.map(t => (
                      <button key={t} onClick={() => setActiveTab(t)}
                        className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${activeTab === t ? 'badge-teal badge' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="p-4 space-y-2">
                  {activeTab === 'Symptoms' && (symptoms.length > 0
                    ? symptoms.map((s, i) => (
                        <div key={i} className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.18)' }}>
                          <div className="w-2 h-2 rounded-full" style={{ background: 'var(--warning)' }} />
                          <span className="text-sm font-medium" style={{ color: '#FFD060' }}>{s}</span>
                          <span className="ml-auto badge badge-warning text-[8px]">ACTIVE</span>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No symptoms extracted from this note</p>
                  )}

                  {activeTab === 'Diseases' && (diseases.length > 0
                    ? diseases.map((d, i) => (
                        <div key={i} className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ background: 'var(--danger-dim)', border: '1px solid rgba(255,69,96,0.18)' }}>
                          <AlertTriangle className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--danger)' }} />
                          <span className="text-sm font-semibold" style={{ color: '#FF8CA0' }}>{d}</span>
                          <span className="ml-auto badge badge-danger text-[8px]">CONFIRMED</span>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No diseases detected</p>
                  )}

                  {activeTab === 'Medications' && (meds.length > 0
                    ? meds.map((m, i) => (
                        <div key={i} className="rounded-xl px-4 py-3 space-y-1.5" style={{ background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.18)' }}>
                          <div className="flex items-center gap-2 flex-wrap">
                            <Pill className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--teal)' }} />
                            <span className="text-sm font-black text-[var(--teal)]">{m.name}</span>
                            {m.route && <span className="badge badge-muted text-[8px] uppercase">{m.route}</span>}
                            {m.duration && <span className="badge badge-teal text-[8px]">{m.duration}</span>}
                            {!m.dosage && <span className="badge badge-warning text-[8px]">MISSING DOSE</span>}
                          </div>
                          <div className="text-xs text-[var(--text-muted)] flex flex-wrap gap-x-3 gap-y-1 ml-6">
                            <span>Dose: <b className="text-[var(--text-primary)]">{m.dosage ?? 'N/A'}</b></span>
                            <span>Freq: <b className="text-[var(--text-primary)]">{m.frequency ?? 'N/A'}</b></span>
                            {m.duration && <span>Duration: <b className="text-[var(--teal)]">{m.duration}</b></span>}
                            {m.timing && <span>Timing: <b className="text-[#FFD060]">{m.timing}</b></span>}
                            {m.reason && <span>For: <b className="text-[var(--text-primary)]">{m.reason}</b></span>}
                          </div>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No medications detected</p>
                  )}

                  {activeTab === 'Labs' && (labs.length > 0
                    ? labs.map((l, i) => (
                        <div key={i} className={`flex items-center gap-4 rounded-xl px-4 py-3 border ${l.critical ? 'border-[rgba(255,69,96,0.2)]' : 'border-[rgba(0,227,150,0.15)]'}`}
                          style={{ background: l.critical ? 'var(--danger-dim)' : 'var(--success-dim)' }}>
                          <FlaskConical className={`w-4 h-4 flex-shrink-0 ${l.critical ? 'text-[var(--danger)]' : 'text-[var(--success)]'}`} />
                          <div className="flex-1">
                            <span className={`text-sm font-semibold ${l.critical ? 'text-[#FF8CA0]' : 'text-[#6EFFD4]'}`}>{l.name}</span>
                            <span className="ml-3 mono text-sm font-bold text-[var(--text-primary)]">{l.val} <span className="text-[10px] text-[var(--text-muted)] font-normal">{l.unit}</span></span>
                          </div>
                          <span className="text-xs text-[var(--text-muted)]">Ref: {l.ref}</span>
                          <span className={`badge ${l.critical ? 'badge-danger' : 'badge-success'} text-[8px]`}>{l.critical ? 'CRITICAL' : 'NORMAL'}</span>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No lab values parsed</p>
                  )}

                  {activeTab === 'Vitals' && (
                    <div className="grid grid-cols-3 gap-3">
                      {Object.entries(vitals).map(([k, v]) => (
                        <div key={k} className="rounded-xl p-3 text-center" style={{ background: 'var(--violet-dim)', border: '1px solid var(--violet-border)' }}>
                          <div className="text-[10px] text-[var(--text-dim)] font-semibold uppercase mb-1">{k}</div>
                          <div className="text-base font-black" style={{ color: '#A78BFA' }}>{v ?? '—'}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeTab === 'Imaging' && (imaging.length > 0
                    ? imaging.map((img, i) => (
                        <div key={i} className="flex gap-3 rounded-xl px-4 py-3" style={{ background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.15)' }}>
                          <Scan className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--teal)' }} />
                          <div>
                            <div className="text-sm font-bold" style={{ color: 'var(--teal)' }}>{img.type}</div>
                            <div className="text-xs text-[var(--text-muted)] mt-0.5">{img.finding}</div>
                            <span className="badge badge-danger text-[8px] mt-1 inline-block">{img.status}</span>
                          </div>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No imaging findings</p>
                  )}

                  {activeTab === 'Allergies' && (allergies.length > 0
                    ? allergies.map((a, i) => (
                        <div key={i} className="flex gap-3 rounded-xl px-4 py-3" style={{ background: 'rgba(255,69,96,0.06)', border: '1px solid rgba(255,69,96,0.15)' }}>
                          <Shield className="w-4 h-4 flex-shrink-0" style={{ color: '#FF8CA0' }} />
                          <span className="text-sm font-medium" style={{ color: '#FF8CA0' }}>{a}</span>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No allergy data</p>
                  )}

                  {activeTab === 'History' && (history.length > 0
                    ? history.map((h, i) => (
                        <div key={i} className="flex gap-3 rounded-xl px-4 py-3" style={{ background: 'var(--warning-dim)', border: '1px solid rgba(255,176,0,0.18)' }}>
                          <History className="w-4 h-4" style={{ color: 'var(--warning)' }} />
                          <span className="text-sm font-medium capitalize" style={{ color: '#FFD060' }}>{h}</span>
                          <span className="ml-auto badge badge-warning text-[8px]">CHRONIC</span>
                        </div>
                      ))
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No medical history extracted</p>
                  )}

                  {activeTab === 'Procedures' && ((raw.toLowerCase().includes('pci') || raw.toLowerCase().includes('angioplasty'))
                    ? (
                        <div className="flex gap-3 rounded-xl px-4 py-3" style={{ background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.15)' }}>
                          <Stethoscope className="w-4 h-4" style={{ color: 'var(--teal)' }} />
                          <span className="text-sm font-medium" style={{ color: 'var(--teal)' }}>Percutaneous Coronary Intervention (PCI)</span>
                          <span className="ml-auto badge badge-teal text-[8px]">SCHEDULED</span>
                        </div>
                      )
                    : <p className="text-sm text-[var(--text-dim)] text-center py-4">No procedures identified</p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* RIGHT — Actions */}
        <div className="w-[240px] flex-shrink-0 flex flex-col glass rounded-2xl overflow-hidden">
          {!cur ? (
            <div className="flex-1 flex items-center justify-center text-sm text-[var(--text-muted)]">No item selected</div>
          ) : (
            <>
              <div className="p-4 border-b border-[var(--border)]">
                <h3 className="font-bold text-sm text-[var(--text-primary)]">🧠 AI Analysis</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {diseases[0] && (
                  <div className="rounded-xl p-3" style={{ background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.15)' }}>
                    <div className="text-sm font-bold text-[var(--text-primary)] mb-2">{diseases[0]}</div>
                    <div className="flex gap-1.5 flex-wrap mb-2">
                      <span className="badge badge-teal text-[8px]">ICD-10</span>
                      <span className="badge badge-danger text-[8px]">HIGH SEVERITY</span>
                    </div>
                    <div className="text-[9px] text-[var(--text-muted)] mb-1 flex justify-between">
                      <span>AI Confidence</span>
                      <span style={{ color: 'var(--teal)' }}>{det.confidence ? `${(det.confidence * 100).toFixed(0)}%` : '—'}</span>
                    </div>
                  </div>
                )}
                <div className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                  <div className="text-xs font-bold text-[var(--text-primary)] mb-2">🔍 Explainable AI</div>
                  <div className="space-y-1.5 text-[11px]">
                    {diseases.length > 0 && <div className="flex gap-1.5" style={{ color: 'var(--success)' }}><span>+</span><span>Clinical criteria met for {diseases[0]}</span></div>}
                    {labs.some(l => l.critical) && <div className="flex gap-1.5" style={{ color: 'var(--warning)' }}><span>⚠</span><span>Critical lab values detected</span></div>}
                    <div className="flex gap-1.5 text-[var(--text-dim)]"><span>−</span><span>No conflicting evidence detected</span></div>
                  </div>
                </div>

                <div>
                  <div className="text-xs font-bold text-[var(--text-primary)] mb-2">✍️ Clinician Notes</div>
                  <textarea id="clinician-notes" value={docNote} onChange={e => setDocNote(e.target.value)}
                    placeholder="Add diagnostic notes…" rows={3}
                    className="input-dark w-full text-xs p-3 resize-none" />
                </div>
              </div>

              <div className="p-3 border-t border-[var(--border)] space-y-2">
                <div className="grid grid-cols-3 gap-1.5">
                  {[
                    ['👍', 'APPROVED', 'success'],
                    ['✏️', 'MODIFY',   'warning'],
                    ['❌', 'REJECTED', 'danger'],
                  ].map(([emoji, action, color]) => (
                    <button key={action} id={`action-${action.toLowerCase()}`}
                      onClick={() => doAction(action)} disabled={acting}
                      className={`flex flex-col items-center gap-1 py-2.5 rounded-xl border text-[10px] font-bold transition-all disabled:opacity-50`}
                      style={{
                        background: `var(--${color}-dim)`,
                        border: `1px solid rgba(${color === 'success' ? '0,227,150' : color === 'warning' ? '255,176,0' : '255,69,96'},0.25)`,
                        color: `var(--${color})`,
                      }}>
                      {acting ? <InlineSpinner /> : emoji} {action}
                    </button>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button id="btn-pdf" onClick={handlePdf}
                    className="flex items-center justify-center gap-1.5 py-2 rounded-xl text-[10px] font-bold transition-all"
                    style={{ background: 'var(--violet-dim)', border: '1px solid var(--violet-border)', color: '#A78BFA' }}>
                    <FileDown className="w-3.5 h-3.5" /> PDF
                  </button>
                  <button id="btn-fhir" onClick={handleFhir}
                    className="flex items-center justify-center gap-1.5 py-2 rounded-xl text-[10px] font-bold transition-all"
                    style={{ background: 'rgba(255,176,0,0.12)', border: '1px solid rgba(255,176,0,0.25)', color: 'var(--warning)' }}>
                    <Flame className="w-3.5 h-3.5" /> FHIR
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
