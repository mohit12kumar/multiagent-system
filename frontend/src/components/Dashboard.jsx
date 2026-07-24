import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Activity, LogOut, FileText, CheckSquare } from 'lucide-react';
import Extraction from './Extraction';
import ReviewQueue from './ReviewQueue';
import UserResults from './UserResults';

export default function Dashboard({ setAuthToken }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('ner_token');
    setAuthToken(null);
    navigate('/');
  };

  const role = localStorage.getItem('user_role') || 'doctor';

  const navItems = role === 'doctor' ? [
    { path: '/dashboard', label: 'Extract Entities', icon: FileText },
    { path: '/dashboard/queue', label: 'Review Queue', icon: CheckSquare }
  ] : [
    { path: '/dashboard', label: 'Submit Clinical Note', icon: FileText },
    { path: '/dashboard/results', label: 'My Results', icon: CheckSquare }
  ];

  return (
    <div>
      <nav className="header-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Activity color="var(--accent-blue)" />
          <h2 style={{ fontSize: '18px', margin: 0 }}>Clinical NER</h2>
        </div>
        
        <div className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                className={`nav-link ${isActive ? 'active' : ''}`}
                style={{ 
                  background: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontFamily: 'Inter, sans-serif'
                }}
                onClick={() => navigate(item.path)}
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
          
          <button 
            className="btn btn-outline" 
            style={{ padding: '6px 12px', marginLeft: 'var(--spacing-md)' }}
            onClick={handleLogout}
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </nav>

      <main className="container animate-fade-in">
        <Routes>
          <Route path="/" element={<Extraction />} />
          <Route path="/queue" element={role === 'doctor' ? <ReviewQueue /> : <div style={{textAlign: 'center', padding: '40px'}}>Access Denied</div>} />
          <Route path="/results" element={role === 'user' ? <UserResults /> : <div style={{textAlign: 'center', padding: '40px'}}>Access Denied</div>} />
        </Routes>
      </main>
    </div>
  );
}
