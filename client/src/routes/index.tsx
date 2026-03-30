import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { PretestGate } from '../components/PretestGate';
import { AuthGuard } from '../components/AuthGuard';
import { ToastContainer } from '../components/Toast';

// Pages
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import SessionPage from '../pages/SessionPage';
import PretestPage from '../pages/PretestPage';
import ProfilePage from '../pages/ProfilePage';
import InboxPage from '../pages/InboxPage';
import NotFound from '../pages/NotFound';

/**
 * AppRoutes Component
 * Main routing configuration for the application
 */
export function AppRoutes() {
  return (
    <>
      <ToastContainer position="top-right" />
      <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <AuthGuard redirectTo="/dashboard">
            <Login />
          </AuthGuard>
        }
      />

      {/* Protected routes - require authentication */}
      <Route element={<ProtectedRoute />}>
        {/* Routes that require pretest completion */}
        <Route element={<PretestGate />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/session/:sessionId" element={<SessionPage />} />
        </Route>

        {/* Pretest - only for users who haven't completed it */}
        <Route path="/pretest" element={<PretestPage />} />

        {/* Profile page */}
        <Route path="/profile" element={<ProfilePage />} />

        {/* Collaboration Inbox */}
        <Route path="/inbox" element={<InboxPage />} />
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 - Not Found */}
      <Route path="*" element={<NotFound />} />
    </Routes>
    </>
  );
}

export default AppRoutes;
