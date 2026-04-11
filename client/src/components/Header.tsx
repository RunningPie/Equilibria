import { useNavigate, useLocation } from 'react-router-dom';
import { useUser, useAuthStore } from '../store/authStore';
import { authService } from '../services/auth';

interface ProfileAvatarProps {
  seed: string;
  size?: number;
  className?: string;
}

/**
 * ProfileAvatar Component
 * Generates a unique avatar using DiceBear API based on username seed
 */
export function ProfileAvatar({ seed, size = 40, className = '' }: ProfileAvatarProps) {
  const avatarUrl = `https://api.dicebear.com/9.x/thumbs/svg?seed=${encodeURIComponent(seed)}&shapeColor=CFFF24&shapeOffsetX=-5,5&backgroundColor=6f1abc&backgroundType=gradientLinear,solid`;

  return (
    <img
      src={avatarUrl}
      alt={`Avatar for ${seed}`}
      width={size}
      height={size}
      className={`rounded-full border-2 border-white shadow-sm ${className}`}
    />
  );
}

/**
 * AdminButton Component
 * Shows console icon for admin users only
 */
function AdminButton() {
  const navigate = useNavigate();
  const user = useUser();

  if (!user?.is_admin) return null;

  return (
    <button
      onClick={() => navigate('/admin')}
      className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors cursor-pointer"
      title="Admin Console"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    </button>
  );
}

/**
 * UserProfileSection Component
 * Shows username + avatar, clickable to navigate to profile page
 */
function UserProfileSection() {
  const navigate = useNavigate();
  const user = useUser();

  if (!user) return null;

  const handleClick = () => {
    navigate('/profile');
  };

  return (
    <button
      onClick={handleClick}
      className="flex items-center gap-2 hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors cursor-pointer"
      title="View Profile"
    >
      <span className="text-sm text-gray-700 font-medium">{user.full_name}</span>
      <ProfileAvatar seed={user.nim} size={36} />
    </button>
  );
}

/**
 * Header Component
 * Consistent header across all pages with Equilibria branding and user actions
 */
export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);

  // Don't show header on login page
  if (location.pathname === '/login') return null;

  const handleLogout = async () => {
    try {
      await authService.logout();
    } finally {
      logout();
      navigate('/login', { replace: true });
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Brand */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
              title="Go to Dashboard"
            >
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Equilibria</h1>
                <p className="text-xs text-gray-500 -mt-1">Adaptive SQL Assessment</p>
              </div>
            </button>
          </div>

          {/* Right side - Navigation, User profile & Logout */}
          <div className="flex items-center gap-2">
            {/* Home/Dashboard Navigation */}
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
              title="Home - Dashboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </button>

            {/* Peer Hub */}
            <button
              onClick={() => navigate('/peer-hub')}
              className="p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors cursor-pointer"
              title="Peer Hub"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </button>

            {/* Leaderboard */}
            <button
              onClick={() => navigate('/leaderboard')}
              className="p-2 text-gray-600 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
              title="Leaderboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 21h8M12 17v4M7 4h10v5a5 5 0 01-10 0V4zm0 0H4a2 2 0 002 2h1m11-2h3a2 2 0 01-2 2h-1" />
              </svg>
            </button>

            {/* Admin Console - Only for admins */}
            <AdminButton />

            <div className="w-px h-6 bg-gray-300 mx-1" />

            <UserProfileSection />
            <button
              onClick={handleLogout}
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
              title="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
