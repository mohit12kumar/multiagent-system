import { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, Edit3, CheckCircle2 } from 'lucide-react';

export default function ReviewQueue() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({ new_type: '', new_text: '' });

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('ner_token');
      const response = await fetch('http://localhost:8000/api/v1/review/queue', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch review queue');
      const data = await response.json();
      setSessions(data.pending_sessions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchQueue();
  }, [fetchQueue]);

  const handleFeedback = async (mentionId, action, overrides = null) => {
    try {
      const token = localStorage.getItem('ner_token');
      const payload = { entity_mention_id: mentionId, action };
      if (overrides) {
        if (overrides.new_type) payload.new_type = overrides.new_type;
        if (overrides.new_text) payload.new_text = overrides.new_text;
      }

      const response = await fetch('http://localhost:8000/api/v1/review/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Failed to submit feedback');
      
      setEditingId(null);
      fetchQueue();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleApproveAll = async (session) => {
    try {
      const token = localStorage.getItem('ner_token');
      const mentionIds = session.entities.map(e => e.entity_mention_id);
      
      const payload = {
        entity_mention_ids: mentionIds,
        action: 'APPROVED'
      };

      const response = await fetch('http://localhost:8000/api/v1/review/feedback/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Failed to approve all');
      
      fetchQueue();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  if (loading && sessions.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--spacing-xl)' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', borderTopColor: 'var(--accent-blue)' }} />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
        <h2>Pending Review ({sessions.length} Sessions)</h2>
        <button className="btn btn-outline" onClick={fetchQueue} disabled={loading}>
          {loading ? <div className="spinner" /> : 'Refresh'}
        </button>
      </div>

      {error && (
        <div style={{ padding: 'var(--spacing-md)', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--accent-red)', borderRadius: 'var(--border-radius)', marginBottom: 'var(--spacing-lg)' }}>
          {error}
        </div>
      )}

      {sessions.length === 0 && !loading && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--text-secondary)' }}>
          <CheckCircle size={48} color="var(--accent-green)" style={{ margin: '0 auto var(--spacing-md)' }} />
          <h3>Queue is empty</h3>
          <p>All clinical notes have been reviewed!</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
        {sessions.map((session) => (
          <div key={session.session_id} className="glass-panel animate-fade-in" style={{ padding: 'var(--spacing-lg)' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)', borderBottom: 'var(--glass-border)', paddingBottom: 'var(--spacing-sm)' }}>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Session ID:</span>
                <div style={{ fontFamily: 'monospace', fontSize: '14px' }}>{session.session_id}</div>
              </div>
              <button className="btn btn-success" onClick={() => handleApproveAll(session)}>
                <CheckCircle2 size={16} /> Approve All Entities
              </button>
            </div>
            
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: 'var(--spacing-md)', borderRadius: '8px', marginBottom: 'var(--spacing-lg)', fontFamily: 'monospace', fontSize: '14px', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
              {session.original_text || "No original text available."}
            </div>

            <h4 style={{ marginBottom: 'var(--spacing-sm)', color: 'var(--text-primary)' }}>Pending Entities</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              {[...session.entities].sort((a, b) => {
                const sortOrder = { 'DISEASE': 1, 'SYMPTOM': 2, 'DRUG': 3, 'DOSAGE': 4, 'FREQUENCY': 5 };
                return (sortOrder[a.type] || 99) - (sortOrder[b.type] || 99);
              }).map((item) => (
                <div key={item.queue_id} className="glass-card" style={{ padding: 'var(--spacing-md)' }}>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Extracted Text</div>
                      <strong style={{ fontSize: '16px', color: 'var(--accent-blue)' }}>&quot;{item.text}&quot;</strong>
                    </div>
                    
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Confidence</div>
                      <span style={{ fontWeight: '600', color: item.confidence > 0.5 ? 'var(--accent-blue)' : 'var(--accent-red)' }}>
                        {(item.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {editingId === item.queue_id ? (
                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: 'var(--spacing-md)', borderRadius: '8px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Entity Type</label>
                          <select 
                            className="input-field" 
                            value={editData.new_type} 
                            onChange={e => setEditData({...editData, new_type: e.target.value})}
                          >
                            <option value="DRUG">DRUG</option>
                            <option value="DOSAGE">DOSAGE</option>
                            <option value="DISEASE">DISEASE</option>
                            <option value="FREQUENCY">FREQUENCY</option>
                          </select>
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Extracted Text (Modify)</label>
                          <input 
                            className="input-field" 
                            value={editData.new_text} 
                            onChange={e => setEditData({...editData, new_text: e.target.value})}
                          />
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'flex-end' }}>
                        <button className="btn btn-outline" onClick={() => setEditingId(null)}>Cancel</button>
                        <button className="btn btn-primary" onClick={() => handleFeedback(item.entity_mention_id, 'MODIFIED', editData)}>Save</button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: '24px', marginBottom: '16px', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                      <div>
                        <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block' }}>Predicted Type</span>
                        <span style={{ fontWeight: '500' }}>{item.type}</span>
                      </div>
                    </div>
                  )}

                  {!editingId && (
                    <div style={{ display: 'flex', gap: '12px', borderTop: 'var(--glass-border)', paddingTop: 'var(--spacing-md)' }}>
                      <button 
                        className="btn btn-success" 
                        style={{ flex: 1 }} 
                        onClick={() => handleFeedback(item.entity_mention_id, 'APPROVED')}
                      >
                        <CheckCircle size={16} /> Approve
                      </button>
                      <button 
                        className="btn btn-outline" 
                        style={{ flex: 1 }} 
                        onClick={() => {
                          setEditingId(item.queue_id);
                          setEditData({ new_type: item.type, new_text: item.text });
                        }}
                      >
                        <Edit3 size={16} /> Modify
                      </button>
                      <button 
                        className="btn btn-danger" 
                        style={{ flex: 1 }} 
                        onClick={() => handleFeedback(item.entity_mention_id, 'REJECTED')}
                      >
                        <XCircle size={16} /> Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
          </div>
        ))}
      </div>
    </div>
  );
}
