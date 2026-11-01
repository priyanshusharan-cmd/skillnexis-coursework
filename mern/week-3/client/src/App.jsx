import { Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';
import AuthPage from './pages/AuthPage.jsx';
import Tasks from './pages/Tasks.jsx';
import Uploads from './pages/Uploads.jsx';

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
        <strong>Task Manager</strong>
        {user && (
          <nav>
            <Link to="/">Tasks</Link>
            <Link to="/images">Images</Link>
            <span className="who">{user.name}</span>
            <button onClick={() => { logout(); navigate('/login'); }}>Log out</button>
          </nav>
        )}
      </header>
      <main>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <AuthPage mode="login" />} />
          <Route path="/register" element={user ? <Navigate to="/" replace /> : <AuthPage mode="register" />} />
          <Route path="/" element={<Protected><Tasks /></Protected>} />
          <Route path="/images" element={<Protected><Uploads /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
