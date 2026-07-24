import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Stethoscope, UserCheck, ShieldAlert, User, Key, UserPlus } from 'lucide-react';

const Login = () => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [role, setRole] = useState('doctor');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const setDemoDoctor = () => {
    setIsRegister(false);
    setUsername('dr_jenkins');
    setPassword('password123');
    setError('');
  };

  const setDemoPatient = () => {
    setIsRegister(false);
    setUsername('patient_john');
    setPassword('password123');
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (isRegister) {
        await register({ username, email, password, role, full_name: fullName });
      } else {
        await login(username, password);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div className="glass-panel animate-fade-in" style={{ width: '100%', maxWidth: '460px', padding: '36px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ display: 'inline-flex', padding: '12px', background: 'rgba(59, 130, 246, 0.15)', borderRadius: '16px', color: '#3b82f6', marginBottom: '12px' }}>
            <Stethoscope size={38} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#f8fafc' }}>Clinical Multi-Agent System</h2>
          <p style={{ fontSize: '14px', marginTop: '6px', color: '#94a3b8' }}>
            {isRegister ? 'Register new Doctor or Patient ID' : 'Sign in to access your clinical dashboard'}
          </p>
        </div>

        {/* Quick Demo Selectors */}
        {!isRegister && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '24px' }}>
            <button
              type="button"
              onClick={setDemoDoctor}
              className={`btn ${username === 'dr_jenkins' ? 'btn-primary' : 'btn-outline'}`}
              style={{ fontSize: '12px', padding: '8px' }}
            >
              <UserCheck size={14} /> Doctor Account
            </button>
            <button
              type="button"
              onClick={setDemoPatient}
              className={`btn ${username === 'patient_john' ? 'btn-success' : 'btn-outline'}`}
              style={{ fontSize: '12px', padding: '8px' }}
            >
              <User size={14} /> Patient (PAT-88421)
            </button>
          </div>
        )}

        {error && (
          <div style={{ padding: '12px 16px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#f87171', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <ShieldAlert size={18} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {isRegister && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '6px' }}>Full Name / Doctor Title</label>
                <input
                  type="text"
                  className="input-field"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Dr. John Doe / Patient John"
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '6px' }}>Email Address</label>
                <input
                  type="email"
                  className="input-field"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@hospital.org"
                  required
                />
              </div>
            </>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '6px' }}>Username / Patient ID</label>
            <input
              type="text"
              className="input-field"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username or Patient ID"
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '6px' }}>Password</label>
            <input
              type="password"
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {isRegister && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: '500', marginBottom: '6px' }}>Access Role</label>
              <select
                className="input-field"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                style={{ background: '#0f172a' }}
              >
                <option value="doctor">Doctor / Clinician</option>
                <option value="patient">Patient</option>
              </select>
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ marginTop: '8px', padding: '12px' }}>
            {submitting ? <div className="spinner" /> : (isRegister ? 'Register Account' : 'Sign In')}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px', color: '#94a3b8' }}>
          {isRegister ? 'Already have an account?' : "Need a new Doctor or Patient account?"}{' '}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            style={{ background: 'none', border: 'none', color: '#3b82f6', fontWeight: '600', cursor: 'pointer' }}
          >
            {isRegister ? 'Sign In' : 'Register New'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
