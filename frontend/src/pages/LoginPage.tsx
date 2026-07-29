import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { Eye, EyeOff, Lock, User, Mail, Activity } from 'lucide-react';
import { InlineSpinner } from '../components/ui/Spinner';

export const LoginPage: React.FC = () => {
  const { login, register } = useAuth();
  const { toast } = useToast();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'doctor' | 'patient'>('doctor');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === 'login') {
        await login(username, password);
        toast('Signed in successfully', 'success');
      } else {
        await register(username, email, password, role, fullName);
        toast('Account created successfully', 'success');
      }
    } catch (err: any) {
      toast(err.message || 'Authentication failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (u: string, p: string) => { setUsername(u); setPassword(p); setMode('login'); };

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-base)' }}>
      {/* Left — Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center px-16 relative overflow-hidden">
        {/* Glow orbs */}
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%)' }} />
        <div className="absolute bottom-[-10%] right-[-10%] w-[400px] h-[400px] rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%)' }} />

        {/* Grid overlay */}
        <div className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }} />

        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-14">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl"
              style={{ background: 'linear-gradient(135deg, var(--teal), #7C3AED)', boxShadow: '0 8px 24px rgba(0,212,255,0.3)' }}>
              🏥
            </div>
            <div>
              <h1 className="text-xl font-bold text-[var(--text-primary)]">Enterprise Clinical AI</h1>
              <p className="text-xs font-semibold" style={{ color: 'var(--teal)' }}>Intelligence Platform v8.0</p>
            </div>
          </div>

          <h2 className="text-5xl font-black leading-[1.1] mb-5">
            <span className="text-[var(--text-primary)]">Hospital-Grade</span><br />
            <span className="gradient-brand">AI Intelligence</span><br />
            <span className="text-[var(--text-primary)]">Platform</span>
          </h2>
          <p className="text-[var(--text-muted)] text-base mb-10 max-w-md leading-relaxed">
            Powered by Multi-Agent AI, Medical NER, Disease Detection, FHIR R4, and Explainable AI.
          </p>

          <div className="grid grid-cols-2 gap-4">
            {[
              { emoji: '🧠', label: 'Multi-Agent Pipeline', desc: 'NER + Disease + Medication' },
              { emoji: '🔬', label: 'Evidence Engine',      desc: 'ICD-10 + SNOMED Validated' },
              { emoji: '🔥', label: 'FHIR R4 Export',       desc: 'HL7 Bundle Compliant' },
              { emoji: '🛡️', label: 'Human Review Queue',   desc: 'Doctor Oversight Workflow' },
            ].map(f => (
              <div key={f.label} className="glass glass-hover p-4 rounded-2xl">
                <div className="text-2xl mb-2">{f.emoji}</div>
                <div className="text-sm font-semibold text-[var(--text-primary)]">{f.label}</div>
                <div className="text-xs text-[var(--text-muted)] mt-0.5">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right — Login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-[420px]">
          <div className="glass rounded-3xl p-8" style={{ border: '1px solid var(--border-bright)' }}>
            {/* Mode switch */}
            <div className="flex rounded-xl p-1 mb-7" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)' }}>
              {(['login', 'register'] as const).map(m => (
                <button key={m} id={`auth-tab-${m}`} onClick={() => setMode(m)}
                  className="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
                  style={mode === m
                    ? { background: 'linear-gradient(135deg, var(--teal), #0099BB)', color: '#060B14', boxShadow: '0 4px 12px rgba(0,212,255,0.25)' }
                    : { color: 'var(--text-muted)' }}>
                  {m === 'login' ? '🔑 Sign In' : '➕ Register'}
                </button>
              ))}
            </div>

            <h2 className="text-2xl font-extrabold text-[var(--text-primary)] mb-1">
              {mode === 'login' ? 'Welcome back' : 'Create account'}
            </h2>
            <p className="text-sm text-[var(--text-muted)] mb-6">
              {mode === 'login' ? 'Access the Clinical Intelligence Platform' : 'Join as clinician or patient'}
            </p>

            <form id="auth-form" onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <>
                  <div>
                    <label className="text-xs font-semibold text-[var(--text-muted)] mb-1.5 block">Full Name</label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-dim)]" />
                      <input id="input-fullname" value={fullName} onChange={e => setFullName(e.target.value)} type="text"
                        placeholder="Dr. Sarah Jenkins" required
                        className="input-dark w-full pl-10 pr-4 py-3 text-sm" />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-[var(--text-muted)] mb-1.5 block">Email</label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-dim)]" />
                      <input id="input-email" value={email} onChange={e => setEmail(e.target.value)} type="email"
                        placeholder="doctor@hospital.com" required
                        className="input-dark w-full pl-10 pr-4 py-3 text-sm" />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-[var(--text-muted)] mb-1.5 block">Role</label>
                    <div className="grid grid-cols-2 gap-2">
                      {(['doctor', 'patient'] as const).map(r => (
                        <button key={r} type="button" id={`role-${r}`} onClick={() => setRole(r)}
                          className="py-2.5 rounded-xl text-sm font-semibold transition-all"
                          style={role === r
                            ? { background: 'var(--teal-dim)', border: '1px solid var(--teal-border)', color: 'var(--teal)' }
                            : { background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                          {r === 'doctor' ? '👨‍⚕️ Doctor' : '🏥 Patient'}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <div>
                <label className="text-xs font-semibold text-[var(--text-muted)] mb-1.5 block">Username</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-dim)]" />
                  <input id="input-username" value={username} onChange={e => setUsername(e.target.value)} type="text"
                    placeholder="dr_jenkins" required autoComplete="username"
                    className="input-dark w-full pl-10 pr-4 py-3 text-sm" />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[var(--text-muted)] mb-1.5 block">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-dim)]" />
                  <input id="input-password" value={password} onChange={e => setPassword(e.target.value)}
                    type={showPass ? 'text' : 'password'} placeholder="••••••••" required autoComplete="current-password"
                    className="input-dark w-full pl-10 pr-12 py-3 text-sm" />
                  <button type="button" onClick={() => setShowPass(!showPass)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button id="btn-submit" type="submit" disabled={loading}
                className="btn-primary w-full py-3.5 text-sm flex items-center justify-center gap-2 mt-2">
                {loading ? <><InlineSpinner /><span>Please wait…</span></> : <><Activity className="w-4 h-4" /><span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span></>}
              </button>
            </form>

            {/* Demo credentials */}
            <div className="mt-5 p-4 rounded-2xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
              <p className="text-xs font-bold text-[var(--text-muted)] mb-3 text-center uppercase tracking-wide">Demo Credentials</p>
              <div className="grid grid-cols-2 gap-2">
                <button id="demo-doctor" onClick={() => fillDemo('dr_jenkins', 'password123')}
                  className="btn-ghost text-xs py-2 px-3 rounded-xl text-left">
                  <div className="text-[var(--teal)] font-semibold">👨‍⚕️ Doctor</div>
                  <div className="mono text-[10px] text-[var(--text-dim)] mt-0.5">dr_jenkins</div>
                </button>
                <button id="demo-patient" onClick={() => fillDemo('patient_john', 'password123')}
                  className="btn-ghost text-xs py-2 px-3 rounded-xl text-left">
                  <div className="text-[var(--violet-border)] font-semibold" style={{ color: '#A78BFA' }}>🏥 Patient</div>
                  <div className="mono text-[10px] text-[var(--text-dim)] mt-0.5">patient_john</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
