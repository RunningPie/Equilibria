import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser, useAuthStore } from '../store/authStore';
import { authService } from '../services/auth';
import { sessionService } from '../services/session';
import { profileService } from '../services/profile';
import { modulesService, type ModuleWithStatus } from '../services/modules';
import type { ProfileStats, ActiveSessionCheck } from '../types';
import { calculateThetaDisplay } from '../types';

/**
 * Dashboard Page
 * Full implementation with theta stats, module progress, and session management
 */
export function Dashboard() {
  const navigate = useNavigate();
  const user = useUser();
  const logout = useAuthStore((state) => state.logout);

  // Data states
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [modules, setModules] = useState<ModuleWithStatus[]>([]);
  const [activeSession, setActiveSession] = useState<ActiveSessionCheck | null>(null);

  // Loading states
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [isLoadingModules, setIsLoadingModules] = useState(true);
  const [isLoadingSession, setIsLoadingSession] = useState(true);

  // Error states
  const [error, setError] = useState('');

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch all data in parallel
        const [statsData, modulesData, sessionData] = await Promise.all([
          profileService.getStats().catch(() => null),
          modulesService.listModules().catch(() => []),
          sessionService.getActiveSession().catch(() => null),
        ]);

        if (statsData) setStats(statsData);
        setModules(modulesData);
        if (sessionData) setActiveSession(sessionData);
      } catch {
        setError('Failed to load dashboard data');
      } finally {
        setIsLoadingStats(false);
        setIsLoadingModules(false);
        setIsLoadingSession(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Handle logout
  const handleLogout = async () => {
    try {
      await authService.logout();
    } finally {
      logout();
      navigate('/login', { replace: true });
    }
  };

  // Resume active session
  const handleResumeSession = () => {
    if (activeSession) {
      navigate(`/session/${activeSession.session_id}`);
    }
  };

  // Start new session
  const handleStartSession = async (moduleId: string) => {
    try {
      const result = await sessionService.startSession({ module_id: moduleId });
      navigate(`/session/${result.session_id}`);
    } catch (_err) {
      setError('Failed to start session');
    }
  };

  // Calculate theta display if stats not loaded yet
  const thetaDisplay = stats?.theta_display ?? (user ? calculateThetaDisplay(user.theta_individu, user.theta_social) : 0);
  const thetaPercentage = Math.min(100, Math.max(0, (thetaDisplay / 2000) * 100));

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Equilibria</h1>
            <p className="text-sm text-gray-600">Adaptive SQL Assessment</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700">{user?.full_name}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-red-600 hover:text-red-800 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Theta Stats Card */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Your Progress</h2>
          <div className="bg-white rounded-lg shadow-md p-6">
            {isLoadingStats ? (
              <div className="animate-pulse flex space-x-4">
                <div className="flex-1 space-y-4 py-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Theta Display (Main) */}
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{thetaDisplay.toFixed(0)}</div>
                  <div className="text-sm text-gray-600">Overall Score</div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${thetaPercentage}%` }}
                    ></div>
                  </div>
                </div>

                {/* Individual Theta */}
                <div className="text-center">
                  <div className="text-2xl font-semibold text-gray-800">
                    {stats?.theta_individu.toFixed(0) ?? user?.theta_individu.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Individual (80%)</div>
                </div>

                {/* Social Theta */}
                <div className="text-center">
                  <div className="text-2xl font-semibold text-gray-800">
                    {stats?.theta_social.toFixed(0) ?? user?.theta_social.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Social (20%)</div>
                </div>
              </div>
            )}

            {/* Additional Stats */}
            {!isLoadingStats && stats && (
              <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-lg font-semibold text-gray-800">{stats.total_attempts}</div>
                  <div className="text-xs text-gray-600">Total Attempts</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-gray-800">{stats.k_factor?.toFixed(1) ?? '-'}</div>
                  <div className="text-xs text-gray-600">K-Factor</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-gray-800">
                    {(stats.accuracy_rate ? stats.accuracy_rate * 100 : 0).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-600">Accuracy</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-gray-800">
                    {user?.status === 'ACTIVE' ? 'Active' : 'Peer Review'}
                  </div>
                  <div className="text-xs text-gray-600">Status</div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Active Session Alert */}
        {!isLoadingSession && activeSession && (
          <section className="mb-8">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-amber-800">Active Session</h3>
                <p className="text-sm text-amber-700">
                  You have an ongoing session in module {activeSession.module_id}
                </p>
              </div>
              <button
                onClick={handleResumeSession}
                className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
              >
                Resume Session
              </button>
            </div>
          </section>
        )}

        {/* Modules List */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoadingModules ? (
              // Skeleton loading
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))
            ) : (
              modules.map((module) => (
                <div
                  key={module.module_id}
                  className={`bg-white rounded-lg shadow-md p-6 ${
                    module.is_locked ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">{module.title}</h3>
                    {module.is_locked && (
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{module.description}</p>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      Difficulty: {module.difficulty_range[0]}-{module.difficulty_range[1]}
                    </span>

                    {module.is_locked ? (
                      <span className="text-xs text-gray-500">Locked</span>
                    ) : (
                      <button
                        onClick={() => handleStartSession(module.module_id)}
                        className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                      >
                        Start
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
