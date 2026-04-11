import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../store/authStore';
import { adminService } from '../services/admin';
import { toast } from '../hooks/toastState';
import { Modal } from '../components/Modal';
import type { User, AdminUserCreateRequest, AdminUserUpdateRequest, LogEntry } from '../types';

type Tab = 'users' | 'logs';

// Helper to format date as YYYYMMDD
function formatDateYYYYMMDD(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
}

// Users Tab Component
function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [sortby, setSortby] = useState<'nim' | 'name' | undefined>(undefined);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await adminService.getUsers(1, 1000, sortby);
      setUsers(response.users);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  }, [sortby]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleDelete = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await adminService.deleteUser(userId);
      toast.success('User deleted successfully');
      fetchUsers();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to delete user');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-lg font-semibold text-gray-900">User Management</h2>
        <div className="flex gap-2 w-full sm:w-auto">
          {/* Sort Dropdown */}
          <select
            value={sortby || ''}
            onChange={(e) => setSortby(e.target.value as 'nim' | 'name' || undefined)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Sort by...</option>
            <option value="nim">NIM</option>
            <option value="name">Name</option>
          </select>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
          >
            + Create User
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200 rounded-lg">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    NIM
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Group
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Theta
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Admin
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Deleted
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((user: User) => (
                  <tr key={user.user_id} className={user.is_deleted ? 'bg-red-50' : ''}>
                    <td className="px-4 py-3 text-sm text-gray-900 font-mono">{user.nim}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{user.full_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{user.group_assignment}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{user.theta_individu.toFixed(0)}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                        user.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {user.is_admin && (
                        <span className="inline-flex px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                          Admin
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {user.is_deleted && (
                        <span className="inline-flex px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                          Deleted
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm space-x-2">
                      <button
                        onClick={() => setEditingUser(user)}
                        className="text-blue-600 hover:text-blue-800"
                        disabled={user.is_deleted}
                      >
                        Edit
                      </button>
                      {!user.is_deleted && (
                        <button
                          onClick={() => handleDelete(user.user_id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {users.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No users found
            </div>
          )}
        </>
      )}

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          setShowCreateModal(false);
          fetchUsers();
        }}
      />

      {/* Edit User Modal */}
      <EditUserModal
        isOpen={!!editingUser}
        user={editingUser}
        onClose={() => setEditingUser(null)}
        onSuccess={() => {
          setEditingUser(null);
          fetchUsers();
        }}
      />
    </div>
  );
}

// Create User Modal
function CreateUserModal({ isOpen, onClose, onSuccess }: { isOpen: boolean; onClose: () => void; onSuccess: () => void }) {
  const [formData, setFormData] = useState<AdminUserCreateRequest>({
    nim: '',
    full_name: '',
    password: '',
    group_assignment: 'B',
    is_admin: false,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await adminService.createUser(formData);
      toast.success('User created successfully');
      onSuccess();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const footer = (
    <>
      <button
        type="button"
        onClick={onClose}
        className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
      >
        Cancel
      </button>
      <button
        type="submit"
        form="create-user-form"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Creating...' : 'Create'}
      </button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New User" footer={footer}>
      <form id="create-user-form" onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">NIM</label>
          <input
            type="text"
            value={formData.nim}
            onChange={e => setFormData({ ...formData, nim: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Full Name</label>
          <input
            type="text"
            value={formData.full_name}
            onChange={e => setFormData({ ...formData, full_name: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password"
            value={formData.password}
            onChange={e => setFormData({ ...formData, password: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Group</label>
          <select
            value={formData.group_assignment}
            onChange={e => setFormData({ ...formData, group_assignment: e.target.value as 'A' | 'B' })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="A">A</option>
            <option value="B">B</option>
          </select>
        </div>
        <div className="flex items-center">
          <input
            type="checkbox"
            checked={formData.is_admin}
            onChange={e => setFormData({ ...formData, is_admin: e.target.checked })}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label className="ml-2 block text-sm text-gray-900">Is Admin</label>
        </div>
      </form>
    </Modal>
  );
}

// Edit User Modal
function EditUserModal({ isOpen, user, onClose, onSuccess }: { isOpen: boolean; user: User | null; onClose: () => void; onSuccess: () => void }) {
  const [formData, setFormData] = useState<AdminUserUpdateRequest>({
    full_name: user?.full_name || '',
    group_assignment: user?.group_assignment || 'B',
    status: user?.status || 'ACTIVE',
    is_admin: user?.is_admin || false,
    theta_individu: user?.theta_individu || 1300,
    theta_social: user?.theta_social || 1300,
  });
  const [loading, setLoading] = useState(false);

  // Update form when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name,
        group_assignment: user.group_assignment,
        status: user.status,
        is_admin: user.is_admin,
        theta_individu: user.theta_individu,
        theta_social: user.theta_social,
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      setLoading(true);
      // Only send fields that have values
      const updateData: AdminUserUpdateRequest = {};
      if (formData.full_name) updateData.full_name = formData.full_name;
      if (formData.password) updateData.password = formData.password;
      if (formData.group_assignment) updateData.group_assignment = formData.group_assignment;
      if (formData.status) updateData.status = formData.status;
      if (formData.is_admin !== undefined) updateData.is_admin = formData.is_admin;
      if (formData.theta_individu !== undefined) updateData.theta_individu = formData.theta_individu;
      if (formData.theta_social !== undefined) updateData.theta_social = formData.theta_social;
      
      await adminService.updateUser(user.user_id, updateData);
      toast.success('User updated successfully');
      onSuccess();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  const footer = (
    <>
      <button
        type="button"
        onClick={onClose}
        className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
      >
        Cancel
      </button>
      <button
        type="submit"
        form="edit-user-form"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Saving...' : 'Save'}
      </button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit User" footer={footer}>
      <form id="edit-user-form" onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Full Name</label>
          <input
            type="text"
            value={formData.full_name}
            onChange={e => setFormData({ ...formData, full_name: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">New Password (optional)</label>
          <input
            type="password"
            value={formData.password || ''}
            onChange={e => setFormData({ ...formData, password: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="Leave blank to keep current"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Group</label>
          <select
            value={formData.group_assignment}
            onChange={e => setFormData({ ...formData, group_assignment: e.target.value as 'A' | 'B' })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="A">A</option>
            <option value="B">B</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Status</label>
          <select
            value={formData.status}
            onChange={e => setFormData({ ...formData, status: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="ACTIVE">ACTIVE</option>
            <option value="NEEDS_PEER_REVIEW">NEEDS_PEER_REVIEW</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Theta Individu</label>
            <input
              type="number"
              value={formData.theta_individu}
              onChange={e => setFormData({ ...formData, theta_individu: Number(e.target.value) })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Theta Social</label>
            <input
              type="number"
              value={formData.theta_social}
              onChange={e => setFormData({ ...formData, theta_social: Number(e.target.value) })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="flex items-center">
          <input
            type="checkbox"
            checked={formData.is_admin}
            onChange={e => setFormData({ ...formData, is_admin: e.target.checked })}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label className="ml-2 block text-sm text-gray-900">Is Admin</label>
        </div>
      </form>
    </Modal>
  );
}

// Logs Tab Component
function LogsTab() {
  const [date, setDate] = useState(formatDateYYYYMMDD(new Date()));
  const [limit, setLimit] = useState(10);
  const [syslogs, setSyslogs] = useState<LogEntry[]>([]);
  const [asslogs, setAsslogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const [sysRes, assRes] = await Promise.all([
        adminService.getSyslogs(date, limit),
        adminService.getAsslogs(date, limit),
      ]);
      setSyslogs(sysRes.logs);
      setAsslogs(assRes.logs);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  }, [date, limit]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Date (YYYYMMDD)</label>
          <input
            type="text"
            value={date}
            onChange={e => setDate(e.target.value)}
            placeholder="20260411"
            className="block w-32 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono"
            maxLength={8}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Limit</label>
          <select
            value={limit}
            onChange={e => setLimit(Number(e.target.value))}
            className="block w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={100}>100</option>
          </select>
        </div>
        <button
          onClick={fetchLogs}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Terminal-like Display */}
      <div className="grid grid-cols-2 gap-4 h-[600px]">
        {/* Syslogs */}
        <div className="bg-gray-900 rounded-lg overflow-hidden flex flex-col">
          <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
            <span className="text-green-400 font-mono text-sm font-semibold">📋 System Logs</span>
            <span className="text-gray-500 text-xs">{syslogs.length} entries</span>
          </div>
          <div className="flex-1 overflow-auto p-4 font-mono text-sm">
            {syslogs.length === 0 ? (
              <div className="text-gray-500 italic">No system logs found</div>
            ) : (
              <div className="space-y-2">
                {syslogs.map((log, i) => (
                  <LogLine key={i} log={log} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Asslogs */}
        <div className="bg-gray-900 rounded-lg overflow-hidden flex flex-col">
          <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
            <span className="text-blue-400 font-mono text-sm font-semibold">📝 Assessment Logs</span>
            <span className="text-gray-500 text-xs">{asslogs.length} entries</span>
          </div>
          <div className="flex-1 overflow-auto p-4 font-mono text-sm">
            {asslogs.length === 0 ? (
              <div className="text-gray-500 italic">No assessment logs found</div>
            ) : (
              <div className="space-y-2">
                {asslogs.map((log, i) => (
                  <LogLine key={i} log={log} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Single Log Line Component
function LogLine({ log }: { log: LogEntry }) {
  const getLevelColor = (level?: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR': return 'text-red-400';
      case 'WARNING': return 'text-yellow-400';
      case 'INFO': return 'text-green-400';
      case 'DEBUG': return 'text-gray-400';
      default: return 'text-gray-300';
    }
  };

  const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--:--:--';

  return (
    <div className="break-words">
      <span className="text-gray-500">[{timestamp}]</span>{' '}
      <span className={getLevelColor(log.level)}>[{log.level || 'LOG'}]</span>{' '}
      <span className="text-gray-300">{log.message}</span>
      {log.extra && (
        <span className="text-gray-500 ml-2">{JSON.stringify(log.extra)}</span>
      )}
    </div>
  );
}

// Main Admin Dashboard Component
export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('users');
  const navigate = useNavigate();
  const user = useUser();

  // Redirect non-admins
  useEffect(() => {
    if (!user?.is_admin) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  if (!user?.is_admin) {
    return null;
  }

  return (
    <>
      {/* Back Button */}
      <button
        onClick={() => navigate('/dashboard')}
        className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Dashboard
      </button>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600">Manage users and monitor system logs</p>
      </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex gap-8">
            <button
              onClick={() => setActiveTab('users')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'users'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Users
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'logs'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Logs
            </button>
          </nav>
        </div>

      {/* Tab Content */}
      {activeTab === 'users' ? <UsersTab /> : <LogsTab />}
    </>
  );
}
