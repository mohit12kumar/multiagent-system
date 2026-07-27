import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('ner_token');
    if (token) {
      authAPI.getMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('ner_token');
          localStorage.removeItem('token');
          localStorage.removeItem('ner_role');
          localStorage.removeItem('user_role');
          localStorage.removeItem('ner_username');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const res = await authAPI.login(username, password);
    localStorage.setItem('ner_token', res.data.access_token);
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('ner_role', res.data.user.role);
    localStorage.setItem('user_role', res.data.user.role);
    localStorage.setItem('ner_username', res.data.user.username);
    setUser(res.data.user);
    return res.data.user;
  };

  const register = async (data) => {
    const res = await authAPI.register(data);
    localStorage.setItem('ner_token', res.data.access_token);
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('ner_role', res.data.user.role);
    localStorage.setItem('user_role', res.data.user.role);
    localStorage.setItem('ner_username', res.data.user.username);
    setUser(res.data.user);
    return res.data.user;
  };

  const logout = () => {
    localStorage.removeItem('ner_token');
    localStorage.removeItem('token');
    localStorage.removeItem('ner_role');
    localStorage.removeItem('user_role');
    localStorage.removeItem('ner_username');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
