import { Navigate } from 'react-router-dom';
import { useIsAuthenticated } from '../store/authStore';

/**
 * AuthGuard Component
 * Redirects authenticated users away from public-only pages (login, register)
 * Usage: Wrap routes that should NOT be accessible when logged in
 */
interface AuthGuardProps {
  redirectTo?: string;
  children: React.ReactNode;
}

export function AuthGuard({ redirectTo = '/dashboard', children }: AuthGuardProps) {
  const isAuthenticated = useIsAuthenticated();

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
}

export default AuthGuard;
