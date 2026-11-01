import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { api, getToken, setToken } from './api.js';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return getToken() ? JSON.parse(sessionStorage.getItem('sn-user')) : null;
    } catch {
      return null;
    }
  });

  const finish = useCallback(data => {
    setToken(data.token);
    sessionStorage.setItem('sn-user', JSON.stringify(data.user));
    setUser(data.user);
  }, []);

  const value = useMemo(
    () => ({
      user,
      login: async (email, password) => finish(await api('/auth/login', { method: 'POST', body: { email, password } })),
      register: async (name, email, password) => finish(await api('/auth/register', { method: 'POST', body: { name, email, password } })),
      logout: () => {
        setToken(null);
        sessionStorage.removeItem('sn-user');
        setUser(null);
      },
    }),
    [user, finish]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
