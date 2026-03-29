import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { PretestGate } from '../components/PretestGate';
import { AuthGuard } from '../components/AuthGuard';

// Pages
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Session from '../pages/Session';
import NotFound from '../pages/NotFound';

/**
 * AppRoutes Component
 * Main routing configuration for the application
 */
export function AppRoutes() {
  return (
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
          <Route path="/session/:sessionId" element={<Session />} />
        </Route>

        {/* TODO: Pretest route - will be implemented later */}
        {/* <Route path="/pretest" element={<Pretest />} /> */}
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 - Not Found */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default AppRoutes;
