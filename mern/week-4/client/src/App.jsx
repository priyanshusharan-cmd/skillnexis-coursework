import { Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';
import AuthPage from './pages/AuthPage.jsx';
import Feed from './pages/Feed.jsx';

function Protected({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <>
      <header className="bar">
        <strong>Social Feed</strong>
        {user && (
          <nav>
            <span className="who">{user.name}</span>
            <button onClick={() => { logout(); navigate('/login'); }}>Log out</button>
          </nav>
        )}
      </header>
      <main>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <AuthPage mode="login" />} />
          <Route path="/register" element={user ? <Navigate to="/" replace /> : <AuthPage mode="register" />} />
          <Route path="/" element={<Protected><Feed /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
