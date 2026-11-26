// ── App.jsx ───────────────────────────────────────────────
// Root routing: public /auth, protected /dashboard and /documents.

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { PageLayout } from './components/layout/PageLayout';
import { AuthPage }      from './pages/auth/AuthPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { DocumentsPage } from './pages/documents/DocumentsPage';

/** Shown while the initial session check is running */
function FullScreenLoader() {
  return (
    <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh' }}>
      Loading...
    </div>
  );
}

/** Redirect unauthenticated users to /auth */
function ProtectedRoute({ children }) {
  const { isAuthenticated, initializing } = useAuth();
  if (initializing) return <FullScreenLoader />;
  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  return <PageLayout>{children}</PageLayout>;
}

/** Keep logged-in users away from /auth */
function PublicRoute({ children }) {
  const { isAuthenticated, initializing } = useAuth();
  if (initializing) return <FullScreenLoader />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return children;
}

/** Sends / and unknown URLs to the right place once we know the auth state */
function RootRedirect() {
  const { isAuthenticated, initializing } = useAuth();
  if (initializing) return <FullScreenLoader />;
  return <Navigate to={isAuthenticated ? '/dashboard' : '/auth'} replace />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Auth page */}
      <Route
        path="/auth"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />

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

      {/* Root redirect + catch-all */}
      <Route path="/" element={<RootRedirect />} />
      <Route path="*" element={<RootRedirect />} />
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