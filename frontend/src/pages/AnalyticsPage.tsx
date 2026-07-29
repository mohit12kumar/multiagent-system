import { useState, useEffect } from 'react';
import { getDashboardApi } from '../services/api';
import { useToast } from '../components/ui/Toast';
import { FullPageSpinner } from '../components/ui/Spinner';
import { BarChart3, TrendingUp, AlertTriangle } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import type { DashboardData } from '../types/api';

const TOOLTIP_STYLE = {
  backgroundColor: '#0D1421', border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '12px', color: '#EDF2F7', fontSize: '12px'
};
const COLORS = ['#00E396', '#FFB000', '#FF4560'];

const EmptyChart = ({ label }: { label: string }) => (
  <div className="flex flex-col items-center justify-center h-full text-[var(--text-dim)] gap-2">
    <BarChart3 className="w-8 h-8 opacity-20" />
    <p className="text-xs">{label}</p>
  </div>
);

export const AnalyticsPage = () => {
  const { toast } = useToast();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardApi()
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { toast(e.message, 'error'); setLoading(false); });
  }, []);

  if (loading) return <FullPageSpinner label="Loading analytics…" />;

  if (!data) return (
    <div className="glass rounded-2xl p-8 text-center">
      <AlertTriangle className="w-10 h-10 text-[var(--danger)] mx-auto mb-3" />
      <p className="text-sm text-[var(--text-muted)]">Could not load analytics. Ensure the backend is running.</p>
    </div>
  );

  const diseaseChart = (data.most_common_diseases ?? []).slice(0, 6).map(d => ({
    name: d.name.length > 12 ? d.name.slice(0, 10) + '…' : d.name,
    count: d.count,
  }));

  const medChart = (data.most_common_medications ?? []).slice(0, 8).map(d => ({
    name: d.name.length > 12 ? d.name.slice(0, 10) + '…' : d.name,
    count: d.count,
  }));

  const reviewPie = [
    { name: 'Approved', value: data.approved_review_count ?? 0 },
    { name: 'Pending',  value: data.pending_review_count  ?? 0 },
    { name: 'Other',    value: Math.max(0, (data.completed_sessions ?? 0) - (data.approved_review_count ?? 0)) },
  ].filter(s => s.value > 0);

  const avgConf = parseFloat((data.average_confidence ?? '0').toString().replace('%', ''));

  const kpis = [
    { label: 'Total Extractions',    value: data.total_extractions ?? 0,    color: '#00D4FF' },
    { label: 'AI Confidence',        value: `${isNaN(avgConf) ? '—' : avgConf.toFixed(1)}%`, color: '#00E396' },
    { label: 'Approval Rate',        value: data.review_approval_rate ?? '—', color: '#A78BFA' },
    { label: 'Diseases Detected',    value: data.diseases_detected ?? 0,    color: '#FF4560' },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-black text-[var(--text-primary)] flex items-center gap-2">
          <BarChart3 className="w-6 h-6" style={{ color: 'var(--teal)' }} />Clinical Analytics
        </h1>
        <p className="text-sm text-[var(--text-muted)] mt-0.5">Performance metrics derived from real pipeline data</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map(k => (
          <div key={k.label} className="glass glass-hover rounded-2xl p-5">
            <div className="text-3xl font-black tabular-nums" style={{ color: k.color }}>{k.value}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1">{k.label}</div>
            <div className="flex items-center gap-1 mt-2 text-[10px] font-semibold" style={{ color: 'var(--success)' }}>
              <TrendingUp className="w-3 h-3" />Live from API
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Disease bar */}
        <div className="lg:col-span-2 glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4">Disease Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            {diseaseChart.length > 0 ? (
              <BarChart data={diseaseChart} barSize={30}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {diseaseChart.map((_, i) => <Cell key={i} fill={['#00D4FF','#7C3AED','#00E396','#FFB000','#FF4560','#A78BFA'][i % 6]} />)}
                </Bar>
              </BarChart>
            ) : <EmptyChart label="No disease data — submit clinical notes" />}
          </ResponsiveContainer>
        </div>

        {/* Review pie */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4">Review Outcomes</h3>
          <ResponsiveContainer width="100%" height={180}>
            {reviewPie.length > 0 ? (
              <PieChart>
                <Pie data={reviewPie} cx="50%" cy="50%" innerRadius={45} outerRadius={68} paddingAngle={4} dataKey="value">
                  {reviewPie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </PieChart>
            ) : <EmptyChart label="No review data yet" />}
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-3">
            {reviewPie.map((s, i) => (
              <div key={s.name} className="flex justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                  <span className="text-[var(--text-muted)]">{s.name}</span>
                </div>
                <span className="font-bold text-[var(--text-primary)] tabular-nums">{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Medication chart */}
      <div className="glass rounded-2xl p-5">
        <h3 className="font-bold text-[var(--text-primary)] mb-4">Top Medications — Frequency</h3>
        <ResponsiveContainer width="100%" height={200}>
          {medChart.length > 0 ? (
            <BarChart data={medChart} barSize={24} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} fill="#00D4FF" />
            </BarChart>
          ) : <EmptyChart label="No medication data — submit clinical notes to see patterns" />}
        </ResponsiveContainer>
      </div>

      {/* Stats table */}
      <div className="glass rounded-2xl p-5">
        <h3 className="font-bold text-[var(--text-primary)] mb-4">Pipeline Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { label: 'Total Patients',      value: data.total_patients ?? 0,      color: 'var(--teal)'    },
            { label: 'Total Entities',      value: data.total_entities ?? 0,       color: '#A78BFA'        },
            { label: 'Completed Sessions',  value: data.completed_sessions ?? 0,   color: 'var(--success)' },
            { label: 'Approved Reviews',    value: data.approved_review_count ?? 0, color: 'var(--success)'},
            { label: 'Pending Reviews',     value: data.pending_review_count ?? 0, color: 'var(--warning)' },
            { label: 'Medication Accuracy', value: `${data.medication_accuracy ?? 0}%`, color: 'var(--teal)' },
          ].map(s => (
            <div key={s.label} className="rounded-xl p-4 text-center" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
              <div className="text-2xl font-black tabular-nums" style={{ color: s.color }}>{s.value}</div>
              <div className="text-xs text-[var(--text-muted)] mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
