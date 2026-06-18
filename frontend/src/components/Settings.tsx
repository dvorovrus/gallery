import { useState, useEffect } from 'react';
import { Upload, CheckCircle, XCircle, AlertCircle, Trash2 } from 'lucide-react';
import * as api from '@/services/api';

export default function Settings() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [folderId, setFolderId] = useState('');
  const [serviceAccountFile, setServiceAccountFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);

  useEffect(() => {
    loadSettings();
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.json')) {
        setError('Please select a JSON file');
        return;
      }
      setServiceAccountFile(file);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!folderId || !serviceAccountFile) {
      setError('Please provide both Folder ID and service account JSON file');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      await api.configureGoogleDrive(folderId, serviceAccountFile);
      await loadSettings();
      setServiceAccountFile(null);
      setTestResult(null);
      alert('Google Drive configured successfully!');
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
    if (!confirm('Are you sure you want to remove Google Drive configuration?')) {
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
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">Loading settings...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-2">Configure Google Drive storage for your gallery</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-800 font-medium">Error</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Status Card */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Google Drive Status</h2>
          
          <div className="flex items-center gap-3 mb-4">
            {settings?.google_drive_configured ? (
              <>
                <CheckCircle className="w-6 h-6 text-green-500" />
                <div>
                  <p className="font-medium text-green-700">Connected</p>
                  <p className="text-sm text-gray-600">Folder ID: {settings.google_drive_folder_id}</p>
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="w-6 h-6 text-orange-500" />
                <div>
                  <p className="font-medium text-orange-700">Not Configured</p>
                  <p className="text-sm text-gray-600">Please configure Google Drive below</p>
                </div>
              </>
            )}
          </div>

          {settings?.google_drive_configured && (
            <div className="flex gap-3">
              <button
                onClick={handleTest}
                disabled={testing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </button>
              <button
                onClick={handleRemove}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Remove Configuration
              </button>
            </div>
          )}

          {testResult && (
            <div className={`mt-4 p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <p className={`font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                {testResult.message}
              </p>
              {testResult.folder_name && (
                <p className="text-sm text-gray-600 mt-2">
                  Folder: {testResult.folder_name} (Can edit: {testResult.can_edit ? 'Yes' : 'No'})
                </p>
              )}
            </div>
          )}
        </div>

        {/* Instructions */}
        {showInstructions && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">Setup Instructions</h3>
            <div className="space-y-3 text-sm text-blue-800">
              <div>
                <p className="font-medium">1. Create a Google Cloud Service Account</p>
                <ul className="list-disc ml-6 mt-1 space-y-1">
                  <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline">Google Cloud Console</a></li>
                  <li>Create a new project or select existing</li>
                  <li>Enable Google Drive API</li>
                  <li>Go to IAM & Admin → Service Accounts → Create Service Account</li>
                  <li>Create and download JSON key</li>
                </ul>
              </div>
              <div>
                <p className="font-medium">2. Create Google Drive Folder</p>
                <ul className="list-disc ml-6 mt-1 space-y-1">
                  <li>Create a folder in Google Drive</li>
                  <li>Share the folder with the service account email (found in JSON: client_email)</li>
                  <li>Give "Editor" permissions</li>
                  <li>Copy the Folder ID from the URL: drive.google.com/drive/folders/FOLDER_ID</li>
                </ul>
              </div>
              <div>
                <p className="font-medium">3. Configure Below</p>
                <p className="ml-6 mt-1">Upload the service account JSON file and paste the Folder ID</p>
              </div>
            </div>
            <button
              onClick={() => setShowInstructions(false)}
              className="mt-4 text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Hide Instructions
            </button>
          </div>
        )}

        {!showInstructions && !settings?.google_drive_configured && (
          <button
            onClick={() => setShowInstructions(true)}
            className="mb-6 text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Show Setup Instructions
          </button>
        )}

        {/* Configuration Form */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">
            {settings?.google_drive_configured ? 'Update Configuration' : 'Configure Google Drive'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="folderId" className="block text-sm font-medium text-gray-700 mb-1">
                Google Drive Folder ID
              </label>
              <input
                type="text"
                id="folderId"
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
                placeholder="e.g., 1a2b3c4d5e6f7g8h9i"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Found in the folder URL: drive.google.com/drive/folders/FOLDER_ID
              </p>
            </div>

            <div>
              <label htmlFor="serviceAccount" className="block text-sm font-medium text-gray-700 mb-1">
                Service Account JSON File
              </label>
              <div className="flex items-center gap-3">
                <label className="flex-1 cursor-pointer">
                  <div className="w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 transition-colors flex items-center justify-center gap-2 bg-gray-50">
                    <Upload className="w-5 h-5 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {serviceAccountFile ? serviceAccountFile.name : 'Choose file...'}
                    </span>
                  </div>
                  <input
                    type="file"
                    id="serviceAccount"
                    accept=".json"
                    onChange={handleFileChange}
                    className="hidden"
                    required={!settings?.google_drive_configured}
                  />
                </label>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Upload the JSON key file from Google Cloud Console
              </p>
            </div>

            <button
              type="submit"
              disabled={uploading || !folderId || (!serviceAccountFile && !settings?.google_drive_configured)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {uploading ? 'Configuring...' : 'Save Configuration'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
