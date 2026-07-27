import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Stethoscope, UserCheck, ShieldAlert, User, Key, ArrowRight, ShieldCheck } from 'lucide-react';

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
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        background: '#0B0F19',
        backgroundImage: 'radial-gradient(circle at 50% 30%, rgba(79, 70, 229, 0.15), transparent 45%)',
      }}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '40px',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)',
        }}
      >
        {/* Brand Logo Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              display: 'inline-flex',
              padding: '14px',
              background: 'linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)',
              borderRadius: '16px',
              color: '#FFFFFF',
              marginBottom: '14px',
              boxShadow: '0 0 20px rgba(79, 70, 229, 0.4)',
            }}
          >
            <Stethoscope size={36} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#FFFFFF', letterSpacing: '-0.02em' }}>
            Clinical Intelligence Platform
          </h2>
          <div style={{ display: 'inline-block', marginTop: '6px' }}>
            <span className="badge badge-indigo">MICROSOFT FABRIC / PALANTIR EDITION</span>
          </div>
        </div>

        {error && (
          <div
            style={{
              padding: '12px 16px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              color: '#F87171',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '20px',
            }}
          >
            <ShieldAlert size={18} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {isRegister && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#CBD5E1' }}>Full Name / Doctor Title</label>
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
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#CBD5E1' }}>Email Address</label>
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
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#CBD5E1' }}>Username / Patient ID</label>
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
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#CBD5E1' }}>Password</label>
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
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: '#CBD5E1' }}>Access Role</label>
              <select
                className="input-field"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                style={{ background: '#0B0F19' }}
              >
                <option value="doctor">Doctor / Clinician</option>
                <option value="patient">Patient</option>
              </select>
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ marginTop: '8px', padding: '12px' }}>
            {submitting ? <div className="spinner" /> : (isRegister ? 'Register Account' : 'Authenticate Credentials')}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '13px', color: '#94A3B8' }}>
          {isRegister ? 'Already registered?' : 'Need a new Doctor or Patient ID?'}{' '}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            style={{ background: 'none', border: 'none', color: '#38BDF8', fontWeight: '700', cursor: 'pointer' }}
          >
            {isRegister ? 'Sign In' : 'Register New ID'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
