import { Navigate, Outlet } from 'react-router-dom';
import { useUser, useIsAuthenticated } from '../store/authStore';

/**
 * PretestGate Component
 * Redirects to /pretest if user hasn't completed pretest yet
 * Only applies to authenticated users
 * Usage: Wrap routes that require pretest completion
 */
export function PretestGate() {
  const isAuthenticated = useIsAuthenticated();
  const user = useUser();

  // Not authenticated - let ProtectedRoute handle it
  if (!isAuthenticated) {
    return <Outlet />;
  }

  // User hasn't completed pretest - redirect to pretest page
  if (user && !user.has_completed_pretest) {
    return <Navigate to="/pretest" replace />;
  }

  // User has completed pretest - allow access
  return <Outlet />;
}

export default PretestGate;
