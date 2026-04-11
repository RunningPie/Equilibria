import { useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
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
function UserProfileSection({ showName = true }: { showName?: boolean }) {
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
      {showName && <span className="text-sm text-gray-700 font-medium">{user.full_name}</span>}
      <ProfileAvatar seed={user.nim} size={36} />
    </button>
  );
}

/**
 * Header Component
 * Consistent header across all pages with Equilibria branding and user actions
 */
// Navigation menu items configuration
const navItems = [
  { path: '/dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6', label: 'Dashboard', color: 'blue' },
  { path: '/peer-hub', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z', label: 'Peer Hub', color: 'purple' },
  { path: '/leaderboard', icon: 'M8 21h8M12 17v4M7 4h10v5a5 5 0 01-10 0V4zm0 0H4a2 2 0 002 2h1m11-2h3a2 2 0 01-2 2h-1', label: 'Leaderboard', color: 'amber' },
  { path: '/faq', icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', label: 'FAQ', color: 'indigo' },
];

const colorClasses: Record<string, { hover: string; bg: string }> = {
  blue: { hover: 'hover:text-blue-600', bg: 'hover:bg-blue-50' },
  purple: { hover: 'hover:text-purple-600', bg: 'hover:bg-purple-50' },
  amber: { hover: 'hover:text-amber-600', bg: 'hover:bg-amber-50' },
  indigo: { hover: 'hover:text-indigo-600', bg: 'hover:bg-indigo-50' },
  green: { hover: 'hover:text-green-600', bg: 'hover:bg-green-50' },
  red: { hover: 'hover:text-red-600', bg: 'hover:bg-red-50' },
};

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const user = useUser();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 750);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close menu when route changes
  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

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

  const NavButton = ({ item, isMobileMenu = false }: { item: typeof navItems[0]; isMobileMenu?: boolean }) => {
    const colors = colorClasses[item.color];
    const baseClasses = isMobileMenu
      ? `flex items-center gap-3 w-full px-4 py-3 text-gray-700 ${colors.hover} ${colors.bg} rounded-lg transition-colors cursor-pointer`
      : `p-2 text-gray-600 ${colors.hover} ${colors.bg} rounded-lg transition-colors cursor-pointer`;

    return (
      <button
        onClick={() => navigate(item.path)}
        className={baseClasses}
        title={item.label}
      >
        <svg className={isMobileMenu ? 'w-5 h-5' : 'w-5 h-5'} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
        </svg>
        {isMobileMenu && <span className="font-medium">{item.label}</span>}
      </button>
    );
  };

  // Mobile Header (<= 375px)
  if (isMobile) {
    return (
      <>
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-4 py-3">
            <div className="flex items-center justify-between">
              {/* Hamburger Menu */}
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                title="Menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>

              {/* Profile Avatar Only */}
              {user && (
                <button
                  onClick={() => navigate('/profile')}
                  className="p-1 hover:bg-gray-100 rounded-full transition-colors cursor-pointer"
                  title="View Profile"
                >
                  <ProfileAvatar seed={user.nim} size={36} />
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Mobile Menu Dropdown */}
        {isMenuOpen && (
          <div className="fixed inset-0 top-14 bg-white shadow-lg z-50">
            <div className="p-4 space-y-2">
              {/* Logo in menu */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 mb-2">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="font-bold text-gray-900">Equilibria</span>
              </div>

              {/* Navigation Items */}
              {navItems.map((item) => (
                <NavButton key={item.path} item={item} isMobileMenu />
              ))}

              {/* Admin Button */}
              {user?.is_admin && (
                <button
                  onClick={() => navigate('/admin')}
                  className="flex items-center gap-3 w-full px-4 py-3 text-gray-700 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors cursor-pointer"
                  title="Admin Console"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="font-medium">Admin Console</span>
                </button>
              )}

              {/* Profile */}
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-3 w-full px-4 py-3 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="font-medium">Profile</span>
              </button>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-4 py-3 text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span className="font-medium">Logout</span>
              </button>

              {/* Close button at bottom */}
              <div className="pt-4 border-t border-gray-100 mt-4">
                <button
                  onClick={() => setIsMenuOpen(false)}
                  className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Close Menu
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Desktop Header (> 375px)
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
            {navItems.map((item) => (
              <NavButton key={item.path} item={item} />
            ))}

            {/* Admin Console - Only for admins */}
            <AdminButton />

            <div className="w-px h-6 bg-gray-300 mx-1" />

            <UserProfileSection showName />
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
