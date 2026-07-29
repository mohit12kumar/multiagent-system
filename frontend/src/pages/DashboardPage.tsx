import { useState, useEffect } from 'react';
import type { DashboardData } from '../types/api';
import { getDashboardApi } from '../services/api';
import { FullPageSpinner } from '../components/ui/Spinner';
import { TrendingUp, TrendingDown, Users, ClipboardList, AlertTriangle, CheckCircle2, Brain, Zap, BarChart3, Activity } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';

const TOOLTIP_STYLE = {
  backgroundColor: '#0D1421', border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '12px', color: '#EDF2F7', fontSize: '12px'
};

const CHART_COLORS = ['#00D4FF', '#7C3AED', '#00E396', '#FFB000', '#FF4560', '#A78BFA'];

interface KpiProps {
  title: string; value: string | number; icon: React.ReactNode;
  color: string; trend?: string; trendUp?: boolean; subtitle?: string;
}

const KpiCard = ({ title, value, icon, color, trend, trendUp, subtitle }: KpiProps) => (
  <div className="glass glass-hover rounded-2xl p-5 flex flex-col gap-3 fade-in">
    <div className="flex items-start justify-between">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
        style={{ background: `${color}18`, border: `1px solid ${color}30` }}>
        <div style={{ color }}>{icon}</div>
      </div>
      {trend && (
        <div className={`flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-full badge ${trendUp ? 'badge-success' : 'badge-danger'}`}>
          {trendUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {trend}
        </div>
      )}
    </div>
    <div>
      <div className="text-3xl font-black text-[var(--text-primary)] tracking-tight tabular-nums">{value}</div>
      <div className="text-xs font-semibold text-[var(--text-muted)] mt-0.5">{title}</div>
      {subtitle && <div className="text-[10px] text-[var(--text-dim)] mt-0.5">{subtitle}</div>}
    </div>
  </div>
);

const EmptyChart = ({ label }: { label: string }) => (
  <div className="flex flex-col items-center justify-center h-full text-[var(--text-dim)] gap-2">
    <BarChart3 className="w-8 h-8 opacity-30" />
    <p className="text-xs">{label}</p>
  </div>
);

export const DashboardPage = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getDashboardApi()
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <FullPageSpinner label="Loading dashboard…" />;
  if (error) return (
    <div className="glass rounded-2xl p-8 text-center">
      <AlertTriangle className="w-10 h-10 text-[var(--danger)] mx-auto mb-3" />
      <p className="text-[var(--danger)] font-semibold">{error}</p>
      <p className="text-sm text-[var(--text-muted)] mt-1">Check that the backend is running on port 8080.</p>
    </div>
  );

  const diseaseChart = (data?.most_common_diseases ?? []).slice(0, 8).map(d => ({
    name: d.name.length > 14 ? d.name.slice(0, 12) + '…' : d.name,
    count: d.count,
  }));

  const medChart = (data?.most_common_medications ?? []).slice(0, 6).map(d => ({
    name: d.name.length > 12 ? d.name.slice(0, 10) + '…' : d.name,
    count: d.count,
  }));

  const reviewPie = [
    { name: 'Pending',   value: data?.pending_review_count   ?? 0 },
    { name: 'Approved',  value: data?.approved_review_count  ?? 0 },
    { name: 'Completed', value: data?.completed_sessions     ?? 0 },
  ];

  const pieColors = ['#FFB000', '#00E396', '#00D4FF'];

  const avgConf = parseFloat((data?.average_confidence ?? '0').toString().replace('%', ''));

  return (
    <div className="space-y-5 fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-[var(--text-primary)]">Executive Dashboard</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Real-time clinical intelligence telemetry</p>
        </div>
        <div className="badge badge-success flex items-center gap-1.5">
          <Activity className="w-3 h-3 animate-pulse" /> LIVE DATA
        </div>
      </div>

      {/* KPI grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard title="Total Patients"   value={data?.total_patients ?? '—'}    icon={<Users className="w-5 h-5" />}         color="#00D4FF"  subtitle="All registered patients" />
        <KpiCard title="Pending Reviews"  value={data?.pending_review_count ?? '—'} icon={<ClipboardList className="w-5 h-5" />} color="#FFB000"  subtitle="Awaiting clinician action" />
        <KpiCard title="Diseases Found"   value={data?.diseases_detected ?? '—'}  icon={<AlertTriangle className="w-5 h-5" />}  color="#FF4560"  subtitle="Entity mentions detected" />
        <KpiCard title="Completed"        value={data?.completed_sessions ?? '—'} icon={<CheckCircle2 className="w-5 h-5" />}   color="#00E396"  subtitle="Processed sessions" />
        <KpiCard title="AI Confidence"    value={`${isNaN(avgConf) ? '—' : avgConf.toFixed(1)}%`}  icon={<Brain className="w-5 h-5" />}         color="#7C3AED"  subtitle="Avg model confidence" />
        <KpiCard title="Avg Latency"      value={data?.average_processing_time?.slice(0, 6) ?? '—'} icon={<Zap className="w-5 h-5" />}   color="#A78BFA"  subtitle="Pipeline processing time" />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Disease bar */}
        <div className="lg:col-span-2 glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" style={{ color: 'var(--teal)' }} />
            Disease Distribution
            {diseaseChart.length === 0 && <span className="badge badge-muted ml-2">No data yet</span>}
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            {diseaseChart.length > 0 ? (
              <BarChart data={diseaseChart} barSize={28}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(0,212,255,0.06)' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {diseaseChart.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Bar>
              </BarChart>
            ) : (
              <EmptyChart label="Submit clinical notes to populate disease data" />
            )}
          </ResponsiveContainer>
        </div>

        {/* Review queue pie */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-[var(--teal)]" /> Review Status
          </h3>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={reviewPie} cx="50%" cy="50%" innerRadius={45} outerRadius={68} paddingAngle={4} dataKey="value">
                {reviewPie.map((_, i) => <Cell key={i} fill={pieColors[i]} />)}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-3">
            {reviewPie.map((s, i) => (
              <div key={s.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: pieColors[i] }} />
                  <span className="text-[var(--text-muted)]">{s.name}</span>
                </div>
                <span className="font-bold text-[var(--text-primary)] tabular-nums">{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Top medications */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4">Top Medications Detected</h3>
          <ResponsiveContainer width="100%" height={180}>
            {medChart.length > 0 ? (
              <BarChart data={medChart} barSize={18} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} width={80} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {medChart.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Bar>
              </BarChart>
            ) : (
              <EmptyChart label="No medication data yet" />
            )}
          </ResponsiveContainer>
        </div>

        {/* Stats summary */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold text-[var(--text-primary)] mb-4">Platform Statistics</h3>
          <div className="space-y-3">
            {[
              { label: 'Total Extractions',    value: data?.total_extractions ?? 0,     color: 'var(--teal)' },
              { label: 'Total Entities',       value: data?.total_entities ?? 0,         color: '#A78BFA' },
              { label: 'Medication Accuracy',  value: `${data?.medication_accuracy ?? 0}%`, color: 'var(--success)' },
              { label: 'Review Approval Rate', value: data?.review_approval_rate ?? '—', color: 'var(--warning)' },
            ].map(s => (
              <div key={s.label} className="flex items-center justify-between py-2.5 border-b border-[var(--border)] last:border-0">
                <span className="text-sm text-[var(--text-muted)]">{s.label}</span>
                <span className="text-sm font-bold tabular-nums" style={{ color: s.color }}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
