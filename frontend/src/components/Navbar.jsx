import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Stethoscope, User, LogOut, CheckSquare, BarChart2, FileText, History } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (!user) return null;

  const isDoctor = user.role === 'doctor';

  return (
    <nav className="header-nav glass-panel">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Stethoscope size={28} color="#3b82f6" />
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#f8fafc' }}>
            Clinical Multi-Agent System
          </h2>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
            AI Decision Support Portal ({isDoctor ? 'Doctor Access' : 'Patient Access'})
          </span>
        </div>
      </div>

      <div className="nav-links">
        {isDoctor ? (
          <>
            <Link to="/doctor" className={`nav-link ${location.pathname === '/doctor' ? 'active' : ''}`}>
              <BarChart2 size={16} /> Dashboard
            </Link>
            <Link to="/doctor/review" className={`nav-link ${location.pathname === '/doctor/review' ? 'active' : ''}`}>
              <CheckSquare size={16} /> Review Queue
            </Link>
            <Link to="/doctor/history" className={`nav-link ${location.pathname === '/doctor/history' ? 'active' : ''}`}>
              <History size={16} /> Patient History
            </Link>
          </>
        ) : (
          <>
            <Link to="/patient" className={`nav-link ${location.pathname === '/patient' ? 'active' : ''}`}>
              <FileText size={16} /> Portal & Submit Note
            </Link>
            <Link to="/patient/history" className={`nav-link ${location.pathname === '/patient/history' ? 'active' : ''}`}>
              <History size={16} /> Medical History
            </Link>
          </>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#f8fafc' }}>
            {user.full_name || user.username}
          </div>
          <span className={`badge ${isDoctor ? 'badge-drug' : 'badge-dosage'}`}>
            {user.role.toUpperCase()}
          </span>
        </div>
        <button onClick={logout} className="btn btn-outline" title="Log Out">
          <LogOut size={16} />
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
