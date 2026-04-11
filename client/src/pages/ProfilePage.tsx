import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ProfileAvatar } from '../components/Header';
import { useUser, useAuthStore } from '../store/authStore';
import { profileService } from '../services/profile';
import { authService } from '../services/auth';
import type { ProfileStats } from '../types';
import { calculateThetaDisplay } from '../types';

/**
 * ProfilePage
 * User profile view with stats, avatar, and account management
 */
export function ProfilePage() {
  const navigate = useNavigate();
  const user = useUser();
  const logout = useAuthStore((state) => state.logout);

  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await profileService.getStats();
        setStats(data);
      } catch {
        // Fallback to user data
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (newPassword && newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword && newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      await authService.updateMe({
        full_name: fullName,
        ...(oldPassword && newPassword ? { old_password: oldPassword, new_password: newPassword } : {}),
      });
      setMessage('Profile updated successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setIsEditing(false);
    } catch {
      setError('Failed to update profile');
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
    } finally {
      logout();
      navigate('/login', { replace: true });
    }
  };

  if (!user) return null;

  const thetaDisplay = stats?.theta_display ?? calculateThetaDisplay(user.theta_individu, user.theta_social);
  const thetaPercentage = Math.min(100, Math.max(0, (thetaDisplay / 2000) * 100));

  return (
    <>
      {/* Back button */}
      <button
        onClick={() => navigate('/dashboard')}
        className="mb-6 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </button>

        {message && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            {message}
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Profile Header Card */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <div className="flex items-center gap-6">
            <ProfileAvatar seed={user.nim} size={120} />
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{user.full_name}</h1>
              <p className="text-gray-600">{user.nim}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  user.status === 'ACTIVE'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {user.status === 'ACTIVE' ? 'Active' : 'Needs Peer Review'}
                </span>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  Group {user.group_assignment}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-3xl font-bold text-blue-600">{thetaDisplay.toFixed(0)}</div>
            <div className="text-sm text-gray-600">Overall Score</div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${thetaPercentage}%` }}
              />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-2xl font-semibold text-gray-800">
              {stats?.theta_individu.toFixed(0) ?? user.theta_individu.toFixed(0)}
            </div>
            <div className="text-sm text-gray-600">Individual θ</div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-2xl font-semibold text-gray-800">
              {stats?.theta_social.toFixed(0) ?? user.theta_social.toFixed(0)}
            </div>
            <div className="text-sm text-gray-600">Social θ</div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="text-2xl font-semibold text-gray-800">
              {isLoading ? '...' : (stats?.accuracy_rate ? (stats.accuracy_rate * 100).toFixed(0) + '%' : 'N/A')}
            </div>
            <div className="text-sm text-gray-600">Accuracy</div>
          </div>
        </div>

        {/* Additional Stats */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <span className="text-gray-600 text-sm">Total Attempts</span>
              <p className="text-xl font-semibold">{stats?.total_attempts ?? user.total_attempts}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">K-Factor</span>
              <p className="text-xl font-semibold">{(stats?.k_factor ?? user?.k_factor)?.toFixed(1) ?? '-'}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">Pretest</span>
              <p className="text-xl font-semibold">{user.has_completed_pretest ? 'Completed' : 'Pending'}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">Member Since</span>
              <p className="text-lg font-semibold">{new Date(user.created_at).toLocaleDateString()}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">Stagnation Detected</span>
              <p className="text-xl font-semibold">{user.stagnation_ever_detected ? 'Yes' : 'No'}</p>
            </div>
          </div>
        </div>

        {/* Edit Profile Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Edit Profile</h2>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              {isEditing ? 'Cancel' : 'Edit'}
            </button>
          </div>

          {isEditing && (
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="border-t border-gray-200 pt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Change Password (optional)</h3>
                <div className="space-y-3">
                  <input
                    type="password"
                    placeholder="Current password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="password"
                    placeholder="New password (min 8 chars)"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="password"
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
            </form>
          )}
        </div>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        className="w-full bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 transition-colors"
      >
        Logout
      </button>
    </>
  );
}

export default ProfilePage;
