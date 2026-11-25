// ── App.jsx ───────────────────────────────────────────────
// Root routing: public /auth, protected /dashboard and /documents.

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { PageLayout } from './components/layout/PageLayout';
import { AuthPage }      from './pages/auth/AuthPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { DocumentsPage } from './pages/documents/DocumentsPage';

/** Redirect unauthenticated users to /auth */
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  return <PageLayout>{children}</PageLayout>;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();
  return (
    <Routes>
      {/* Auth page */}
      <Route path="/auth" element={<AuthPage />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents"
        element={
          <ProtectedRoute>
            <DocumentsPage />
          </ProtectedRoute>
        }
      />

      {/* Root redirect */}
      <Route
        path="/"
        element={<Navigate to={isAuthenticated ? '/dashboard' : '/auth'} replace />}
      />

      {/* Catch-all */}
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? '/dashboard' : '/auth'} replace />}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
