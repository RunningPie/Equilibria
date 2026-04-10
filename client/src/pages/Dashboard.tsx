import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../store/authStore';
import { sessionService } from '../services/session';
import { profileService } from '../services/profile';
import { authService } from '../services/auth';
import { modulesService, type ModuleWithStatus } from '../services/modules';
import { leaderboardService } from '../services/leaderboard';
import { Header } from '../components/Header';
import type { ProfileStats, ActiveSessionCheck, User, LeaderboardEntry } from '../types';
import { calculateThetaDisplay } from '../types';

/**
 * Dashboard Page
 * Full implementation with theta stats, module progress, and session management
 */
export function Dashboard() {
  const navigate = useNavigate();
  const user = useUser();

  // Data states
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [modules, setModules] = useState<ModuleWithStatus[]>([]);
  const [activeSession, setActiveSession] = useState<ActiveSessionCheck | null>(null);
  const [userData, setUserData] = useState<User | null>(null);
  const [leaderboardEntries, setLeaderboardEntries] = useState<LeaderboardEntry[]>([]);

  // Loading states
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [isLoadingModules, setIsLoadingModules] = useState(true);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(true);

  // Error states
  const [error, setError] = useState('');

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch all data in parallel
        const [statsData, modulesData, sessionData, userDataResult, leaderboardData] = await Promise.all([
          profileService.getStats().catch(() => null),
          modulesService.listModules().catch(() => []),
          sessionService.getActiveSession().catch(() => null),
          authService.getMe().catch(() => null),
          leaderboardService.getLeaderboard(5, 0).catch(() => null),
        ]);

        if (statsData) setStats(statsData);
        setModules(modulesData);
        if (sessionData) setActiveSession(sessionData);
        if (userDataResult) setUserData(userDataResult);
        if (leaderboardData) setLeaderboardEntries(leaderboardData.entries);
      } catch {
        setError('Failed to load dashboard data');
      } finally {
        setIsLoadingStats(false);
        setIsLoadingModules(false);
        setIsLoadingSession(false);
        setIsLoadingUser(false);
        setIsLoadingLeaderboard(false);
      }
    };

    fetchDashboardData();
  }, []);

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
    } catch {
      setError('Failed to start session');
    }
  };

  // Calculate theta display if stats not loaded yet
  const thetaDisplay = stats?.theta_display ?? (userData ? calculateThetaDisplay(userData.theta_individu, userData.theta_social) : (user ? calculateThetaDisplay(user.theta_individu, user.theta_social) : 0));
  const thetaPercentage = Math.min(100, Math.max(0, (thetaDisplay / 2000) * 100));

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

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
                    {stats?.theta_individu.toFixed(0) ?? userData?.theta_individu.toFixed(0) ?? user?.theta_individu.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Individual (80%)</div>
                </div>

                {/* Social Theta */}
                <div className="text-center">
                  <div className="text-2xl font-semibold text-gray-800">
                    {stats?.theta_social.toFixed(0) ?? userData?.theta_social.toFixed(0) ?? user?.theta_social.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Social (20%)</div>
                </div>
              </div>
            )}

            {/* Additional Stats */}
            {(!isLoadingStats || !isLoadingUser) && (stats || userData) && (
              <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-lg font-semibold text-gray-800">{userData?.total_attempts ?? user?.total_attempts ?? '-'}</div>
                  <div className="text-xs text-gray-600">Total Attempts</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-gray-800">{userData?.k_factor ?? user?.k_factor ?? '-'}</div>
                  <div className="text-xs text-gray-600">K-Factor</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-gray-800">
                    {userData?.status === 'ACTIVE' || user?.status === 'ACTIVE' ? 'Active' : 'Peer Review'}
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

        {/* Leaderboard Preview */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Leaderboard</h2>
            <button
              onClick={() => navigate('/leaderboard')}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
            >
              View Full Leaderboard
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            {isLoadingLeaderboard ? (
              <div className="animate-pulse space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 h-4 bg-gray-200 rounded"></div>
                    <div className="w-16 h-4 bg-gray-200 rounded"></div>
                  </div>
                ))}
              </div>
            ) : leaderboardEntries.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                <p>No leaderboard entries yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {leaderboardEntries.map((entry) => (
                  <div
                    key={entry.user_id}
                    className={`flex items-center gap-4 p-3 rounded-lg ${
                      entry.is_self ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
                    }`}
                  >
                    {/* Rank */}
                    <div className="w-8 text-center">
                      {entry.rank === 1 ? (
                        <span className="text-xl">🥇</span>
                      ) : entry.rank === 2 ? (
                        <span className="text-xl">🥈</span>
                      ) : entry.rank === 3 ? (
                        <span className="text-xl">🥉</span>
                      ) : (
                        <span className="text-sm font-semibold text-gray-600">{entry.rank}</span>
                      )}
                    </div>
                    {/* Name */}
                    <div className="flex-1">
                      <span className={`font-medium ${entry.is_self ? 'text-blue-900' : 'text-gray-900'}`}>
                        {entry.display_name}
                      </span>
                      {entry.is_self && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                          You
                        </span>
                      )}
                    </div>
                    {/* Score */}
                    <div className="text-right">
                      <span className={`font-bold ${entry.is_self ? 'text-blue-700' : 'text-gray-700'}`}>
                        {Math.round(entry.theta_display).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

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
                      <div className="flex gap-2">
                        <button
                          onClick={() => navigate(`/materials/${module.module_id}`)}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 transition-colors flex items-center gap-1"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                          Read Materials
                        </button>
                        <button
                          onClick={() => handleStartSession(module.module_id)}
                          className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Start Assessment
                        </button>
                      </div>
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
