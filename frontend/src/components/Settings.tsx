import { useState, useEffect } from 'react';
import { ArrowLeft, Upload, CheckCircle, XCircle, AlertCircle, Trash2, Users, Shield, UserX } from 'lucide-react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';
import * as api from '@/services/api';
import type { UserInfo } from '@/types';

export default function Settings() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [folderId, setFolderId] = useState('');
  const [serviceAccountFile, setServiceAccountFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [activeTab, setActiveTab] = useState<'google-drive' | 'users'>('google-drive');

  useEffect(() => {
    loadSettings();
    loadUsers();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
      if (data.google_drive_folder_id) {
        setFolderId(data.google_drive_folder_id);
      }
      setShowInstructions(!data.google_drive_configured);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const data = await api.getAllUsers();
      setUsers(data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleToggleAdmin = async (userId: number, currentRole: string) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    const action = newRole === 'admin' ? t('settings.actionMakeAdmin') : t('settings.actionRemoveAdmin');
    
    if (!confirm(t('settings.confirmToggleAdmin', { action }))) {
      return;
    }

    try {
      await api.updateUserRole(userId, newRole);
      await loadUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(t('settings.confirmDeleteUser', { email: userEmail }))) {
      return;
    }

    try {
      await api.deleteUser(userId);
      await loadUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.json')) {
        setError(t('settings.jsonOnly'));
        return;
      }
      setServiceAccountFile(file);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!folderId || !serviceAccountFile) {
      setError(t('settings.missingFields'));
      return;
    }

    try {
      setUploading(true);
      setError(null);
      await api.configureGoogleDrive(folderId, serviceAccountFile);
      await loadSettings();
      setServiceAccountFile(null);
      setTestResult(null);
      alert(t('settings.saved'));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setError(null);
      const result = await api.testGoogleDriveConnection();
      setTestResult(result);
    } catch (err: any) {
      setError(err.message);
      setTestResult(null);
    } finally {
      setTesting(false);
    }
  };

  const handleRemove = async () => {
    if (!confirm(t('settings.confirmRemoveConfig'))) {
      return;
    }

    try {
      setLoading(true);
      await api.removeGoogleDriveConfig();
      await loadSettings();
      setTestResult(null);
      setFolderId('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-neutral-950 flex items-center justify-center p-6">
        <div className="text-neutral-600 dark:text-neutral-400">{t('settings.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-neutral-950 px-4 py-6 sm:px-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 overflow-hidden rounded-[2rem] border border-neutral-200 bg-neutral-50 p-5 dark:border-neutral-800 dark:bg-neutral-900 sm:p-7">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <button
                onClick={() => navigate('/')}
                className="mb-5 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:text-neutral-950 dark:bg-neutral-950 dark:text-neutral-300 dark:hover:text-white"
              >
                <ArrowLeft className="h-4 w-4" />
                {t('app.backToGallery')}
              </button>
              <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-white sm:text-4xl">{t('settings.title')}</h1>
              <p className="mt-3 max-w-2xl text-neutral-600 dark:text-neutral-400">{t('settings.subtitle')}</p>
            </div>
            <LanguageSwitcher />
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-3xl flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-800 dark:text-red-300 font-medium">{t('app.error')}</p>
              <p className="text-red-600 dark:text-red-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('google-drive')}
              className={`pb-3 px-1 border-b-2 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'google-drive'
                  ? 'border-neutral-900 dark:border-white text-neutral-900 dark:text-white'
                  : 'border-transparent text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300'
              }`}
            >
              <Upload className="w-4 h-4" />
              {t('settings.storage')}
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`pb-3 px-1 border-b-2 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'users'
                  ? 'border-neutral-900 dark:border-white text-neutral-900 dark:text-white'
                  : 'border-transparent text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300'
              }`}
            >
              <Users className="w-4 h-4" />
              {t('settings.admins')}
            </button>
          </div>
        </div>

        {activeTab === 'google-drive' && (
        <>
        {/* Status Card */}
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6 mb-6">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">{t('settings.googleStatus')}</h2>
          
          <div className="flex items-center gap-3 mb-4">
            {settings?.google_drive_configured ? (
              <>
                <CheckCircle className="w-6 h-6 text-green-500" />
                <div>
                  <p className="font-medium text-green-700 dark:text-green-400">{t('settings.connected')}</p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">Folder ID: {settings.google_drive_folder_id}</p>
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="w-6 h-6 text-orange-500" />
                <div>
                  <p className="font-medium text-orange-700 dark:text-orange-400">{t('settings.notConfigured')}</p>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('settings.configureBelow')}</p>
                </div>
              </>
            )}
          </div>

          {settings?.google_drive_configured && (
            <div className="flex gap-3">
              <button
                onClick={handleTest}
                disabled={testing}
                className="px-4 py-2.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 text-white dark:text-neutral-900 rounded-2xl font-medium disabled:opacity-50 transition-all"
              >
                {testing ? t('settings.testing') : t('settings.testConnection')}
              </button>
              <button
                onClick={handleRemove}
                className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-2xl font-medium flex items-center gap-2 transition-all"
              >
                <Trash2 className="w-4 h-4" />
                {t('settings.removeConfig')}
              </button>
            </div>
          )}

          {testResult && (
            <div className={`mt-4 p-4 rounded-2xl ${testResult.success ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'}`}>
              <p className={`font-medium ${testResult.success ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>
                {testResult.message}
              </p>
              {testResult.folder_name && (
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                  {t('settings.folder', { name: testResult.folder_name, canEdit: testResult.can_edit ? t('settings.yes') : t('settings.no') })}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Instructions */}
        {showInstructions && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-3xl p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-3">{t('settings.instructionsTitle')}</h3>
            <div className="space-y-3 text-sm text-blue-800 dark:text-blue-300">
              <div>
                <p className="font-medium">{t('settings.serviceStep')}</p>
                <ul className="list-disc ml-6 mt-1 space-y-1">
                  <li><a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline">{t('settings.service1')}</a></li>
                  <li>{t('settings.service2')}</li>
                  <li>{t('settings.service3')}</li>
                  <li>{t('settings.service4')}</li>
                  <li>{t('settings.service5')}</li>
                </ul>
              </div>
              <div>
                <p className="font-medium">{t('settings.folderStep')}</p>
                <ul className="list-disc ml-6 mt-1 space-y-1">
                  <li>{t('settings.folder1')}</li>
                  <li>{t('settings.folder2')}</li>
                  <li>{t('settings.folder3')}</li>
                  <li>{t('settings.folder4')}</li>
                </ul>
              </div>
              <div>
                <p className="font-medium">{t('settings.setupStep')}</p>
                <p className="ml-6 mt-1">{t('settings.setupText')}</p>
              </div>
            </div>
            <button
              onClick={() => setShowInstructions(false)}
              className="mt-4 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium"
            >
              {t('settings.hideInstructions')}
            </button>
          </div>
        )}

        {!showInstructions && !settings?.google_drive_configured && (
          <button
            onClick={() => setShowInstructions(true)}
            className="mb-6 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white text-sm font-medium"
          >
            {t('settings.showInstructions')}
          </button>
        )}

        {/* Configuration Form */}
        <div className="bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">
             {settings?.google_drive_configured ? t('settings.updateConfig') : t('settings.configureDrive')}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Folder ID
              </label>
              <input
                type="text"
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
                placeholder="1A2B3C4D5E6F..."
                className="w-full px-4 py-3 bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white rounded-2xl focus:border-neutral-900 dark:focus:border-white outline-none transition-all"
                required
              />
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                {t('settings.folderHint')}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                {t('settings.serviceJson')}
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileChange}
                  className="w-full px-4 py-3 bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white rounded-2xl file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-neutral-900 file:text-white dark:file:bg-white dark:file:text-neutral-900 hover:file:bg-neutral-800 dark:hover:file:bg-neutral-200 transition-all cursor-pointer"
                  required={!settings?.google_drive_configured}
                />
              </div>
              {serviceAccountFile && (
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                  {t('settings.fileSelected', { name: serviceAccountFile.name })}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={uploading}
              className="w-full py-3.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 text-white dark:text-neutral-900 rounded-2xl font-medium disabled:opacity-50 transition-all"
            >
              {uploading ? t('settings.saving') : t('settings.saveConfig')}
            </button>
          </form>
        </div>
        </>
        )}

        {activeTab === 'users' && (
          <div className="bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">{t('settings.usersTitle')}</h2>
            
            {loadingUsers ? (
              <p className="text-neutral-600 dark:text-neutral-400">{t('app.loading')}</p>
            ) : (
              <div className="space-y-3">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-4 bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-2xl"
                  >
                    <div className="flex items-center gap-3">
                      {user.role === 'admin' ? (
                        <Shield className="w-5 h-5 text-blue-500" />
                      ) : (
                        <Users className="w-5 h-5 text-neutral-400" />
                      )}
                      <div>
                        <p className="font-medium text-neutral-900 dark:text-white">{user.email}</p>
                        <p className="text-sm text-neutral-500 dark:text-neutral-400">
                          {user.role === 'admin' ? t('settings.admin') : t('settings.user')}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleToggleAdmin(user.id, user.role)}
                        className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                          user.role === 'admin'
                            ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50'
                            : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50'
                        }`}
                      >
                        {user.role === 'admin' ? t('settings.removeRights') : t('settings.makeAdmin')}
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user.id, user.email)}
                        className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-xl text-sm font-medium hover:bg-red-200 dark:hover:bg-red-900/50 transition-all flex items-center gap-1"
                      >
                        <UserX className="w-4 h-4" />
                        {t('settings.deleteUser')}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
