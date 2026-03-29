import { useNavigate } from 'react-router-dom';
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
  const logout = useAuthStore((state) => state.logout);

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
              className="flex items-center gap-2 hover:opacity-80 transition-opacity"
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

          {/* Right side - User profile & Logout */}
          <div className="flex items-center gap-4">
            <UserProfileSection />
            <button
              onClick={handleLogout}
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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
