import { Navigate, Outlet } from 'react-router-dom';
import { useIsAuthenticated } from '../store/authStore';

/**
 * ProtectedRoute Component
 * Redirects to /login if user is not authenticated
 * Usage: Wrap routes that require authentication
 */
export function ProtectedRoute() {
  const isAuthenticated = useIsAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
