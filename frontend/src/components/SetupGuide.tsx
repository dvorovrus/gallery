import { ArrowLeft, ExternalLink, Check } from 'lucide-react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';

export default function SetupGuide() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-white dark:bg-neutral-950 px-4 py-6 sm:px-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 overflow-hidden rounded-[2rem] border border-neutral-200 bg-neutral-50 p-5 dark:border-neutral-800 dark:bg-neutral-900 sm:p-7">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <button
                onClick={() => navigate('/setting')}
                className="mb-5 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:text-neutral-950 dark:bg-neutral-950 dark:text-neutral-300 dark:hover:text-white"
              >
                <ArrowLeft className="h-4 w-4" />
                {t('app.backToSettings')}
              </button>
              <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-white sm:text-4xl">
                Google Drive OAuth Setup Guide
              </h1>
              <p className="mt-3 max-w-2xl text-neutral-600 dark:text-neutral-400">
                Complete step-by-step guide to configure Google Drive API access for the Gallery application
              </p>
            </div>
            <LanguageSwitcher />
          </div>
        </div>

        {/* Table of Contents */}
        <div className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-4">Table of Contents</h2>
          <ol className="space-y-2 text-sm text-neutral-600 dark:text-neutral-400">
            <li><a href="#prerequisites" className="hover:text-neutral-900 dark:hover:text-white">Prerequisites</a></li>
            <li><a href="#step1" className="hover:text-neutral-900 dark:hover:text-white">Step 1: Access Google Cloud Console</a></li>
            <li><a href="#step2" className="hover:text-neutral-900 dark:hover:text-white">Step 2: Accept Terms and Continue</a></li>
            <li><a href="#step3" className="hover:text-neutral-900 dark:hover:text-white">Step 3: Create or Select a Project</a></li>
            <li><a href="#step4" className="hover:text-neutral-900 dark:hover:text-white">Step 4: Enable 2-Step Verification (if required)</a></li>
            <li><a href="#step5" className="hover:text-neutral-900 dark:hover:text-white">Step 5: Create New Project</a></li>
            <li><a href="#step6" className="hover:text-neutral-900 dark:hover:text-white">Step 6: Enable Google Drive API</a></li>
            <li><a href="#step7" className="hover:text-neutral-900 dark:hover:text-white">Step 7: Configure OAuth Consent Screen</a></li>
            <li><a href="#step8" className="hover:text-neutral-900 dark:hover:text-white">Step 8: Create OAuth Client JSON</a></li>
            <li><a href="#step9" className="hover:text-neutral-900 dark:hover:text-white">Step 9: Create Google Drive Folder</a></li>
            <li><a href="#step10" className="hover:text-neutral-900 dark:hover:text-white">Step 10: Connect Your Google Account</a></li>
            <li><a href="#step11" className="hover:text-neutral-900 dark:hover:text-white">Step 11: Get Folder ID</a></li>
            <li><a href="#step12" className="hover:text-neutral-900 dark:hover:text-white">Step 12: Configure Your Application</a></li>
          </ol>
        </div>

        {/* Prerequisites */}
        <section id="prerequisites" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Prerequisites</h2>
          <ul className="list-disc ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Google account</li>
            <li>Access to Google Cloud Console</li>
            <li>Permission to create OAuth clients in Google Cloud</li>
          </ul>
        </section>

        {/* Step 1 */}
        <section id="step1" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 1: Access Google Cloud Console</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>
              Go to{' '}
              <a
                href="https://console.cloud.google.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
              >
                Google Cloud Console
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
            <li>Sign in with your Google account</li>
            <li>You will see a welcome dialog</li>
          </ol>
        </section>

        {/* Step 2 */}
        <section id="step2" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 2: Accept Terms and Continue</h2>
          <p className="text-neutral-700 dark:text-neutral-300 mb-3">
            When you first access Google Cloud Console, you'll see a welcome dialog:
          </p>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Select your <strong>Country</strong> from the dropdown (e.g., "Ukraine")</li>
            <li>Check the box: "I agree to the Google Cloud Platform Terms of Service"</li>
            <li>(Optional) Check the box for email updates if you want to receive news and offers</li>
            <li>Click <strong>"Agree and continue"</strong> button at the bottom right</li>
          </ol>
        </section>

        {/* Step 3 */}
        <section id="step3" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 3: Create or Select a Project</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Look at the top left, next to "Google Cloud" logo - you'll see a button <strong>"Select a project"</strong></li>
            <li>Click on <strong>"Select a project"</strong> button</li>
          </ol>
        </section>

        {/* Step 4 */}
        <section id="step4" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 4: Enable 2-Step Verification (if required)</h2>
          <p className="text-neutral-700 dark:text-neutral-300 mb-3">
            If you see a message "Google Cloud access blocked" requiring 2-Step Verification:
          </p>

          <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mt-4 mb-2">4.1. Access Security Settings</h3>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300 mb-4">
            <li>Click <strong>"Go to settings"</strong> button</li>
            <li>You'll be redirected to the 2-Step Verification setup page</li>
          </ol>

          <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mt-4 mb-2">4.2. Set Up Authenticator App</h3>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300 mb-4">
            <li>Click on <strong>"Authenticator"</strong> option</li>
            <li>Click <strong>"Set up authenticator"</strong> button</li>
            <li>A QR code will be displayed on screen</li>
            <li>Scan the QR code with your authenticator app (Google Authenticator, Microsoft Authenticator, Authy, etc.)</li>
            <li>Click <strong>"Next"</strong> button</li>
          </ol>

          <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mt-4 mb-2">4.3. Verify Authenticator Setup</h3>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300 mb-4">
            <li>Enter the 6-digit code from your authenticator app</li>
            <li>Click <strong>"Verify"</strong> button</li>
            <li>Click <strong>"Turn on"</strong> button</li>
          </ol>

          <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mt-4 mb-2">4.4. Add Phone Number (Required)</h3>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300 mb-4">
            <li>Click <strong>"Add phone number"</strong> button</li>
            <li>Verify the phone number and click <strong>"Save"</strong></li>
            <li>Click <strong>"Approve"</strong> button</li>
          </ol>

          <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mt-4 mb-2">4.5. Enable 2-Step Verification</h3>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Click <strong>"Turn on 2-Step Verification"</strong> button</li>
            <li>Return to Google Cloud Console and refresh the page</li>
          </ol>
        </section>

        {/* Step 5 */}
        <section id="step5" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 5: Create New Project</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>In the "Select a project" dialog, click <strong>"New project"</strong> button in the top right</li>
            <li>In the <strong>"Project name"</strong> field, enter a meaningful name (e.g., "Gallery App")</li>
            <li>The <strong>Project ID</strong> will be automatically generated</li>
            <li>Leave <strong>"Parent resource"</strong> as <strong>"No organization"</strong></li>
            <li>Click <strong>"Create"</strong> button</li>
          </ol>
        </section>

        {/* Step 6 */}
        <section id="step6" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 6: Enable Google Drive API</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>
              Go to:{' '}
              <a
                href="https://console.cloud.google.com/apis/library/drive.googleapis.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
              >
                Google Drive API
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
            <li>Click the blue <strong>"Enable"</strong> button</li>
            <li>Wait for the API to be enabled</li>
          </ol>
        </section>

        {/* Step 7 */}
        <section id="step7" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 7: Configure OAuth Consent Screen</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Open <strong>"APIs & Services"</strong> → <strong>"OAuth consent screen"</strong></li>
            <li>Select <strong>"External"</strong> if this is a personal Google account</li>
            <li>Enter the app name, support email, and developer contact email</li>
            <li>Add the scope <strong>Google Drive API / .../auth/drive</strong></li>
            <li>Add your Google account as a test user if the app is in testing mode</li>
            <li>Save the consent screen</li>
          </ol>
        </section>

        {/* Step 8 */}
        <section id="step8" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 8: Create OAuth Client JSON</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Open <strong>"APIs & Services"</strong> → <strong>"Credentials"</strong></li>
            <li>Click <strong>"+ Create credentials"</strong> → <strong>"OAuth client ID"</strong></li>
            <li>Select <strong>"Web application"</strong></li>
            <li>Add this authorized redirect URI: <code className="bg-neutral-200 dark:bg-neutral-800 px-2 py-1 rounded text-xs">https://gallery.fatbox.org/api/settings/google-drive/oauth/callback</code></li>
            <li>Click <strong>"Create"</strong></li>
            <li>Download the OAuth Client JSON file</li>
          </ol>
          <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-2xl">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">
              <strong>Important:</strong> Upload this OAuth Client JSON on the Settings page. Do not upload a Service Account JSON file.
            </p>
          </div>
        </section>

        {/* Step 9 */}
        <section id="step9" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 9: Create Google Drive Folder</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>
              Go to{' '}
              <a
                href="https://drive.google.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
              >
                Google Drive
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
            <li>Click <strong>"New"</strong> button</li>
            <li>Select <strong>"New folder"</strong></li>
            <li>Enter a folder name (e.g., "Gallery Photos")</li>
            <li>Click <strong>"Create"</strong></li>
          </ol>
        </section>

        {/* Step 10 */}
        <section id="step10" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 10: Connect Your Google Account</h2>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Go back to the Gallery settings page</li>
            <li>Paste the Folder ID</li>
            <li>Upload the OAuth Client JSON file</li>
            <li>Click <strong>"Connect Google Drive"</strong></li>
            <li>Choose your Google account and allow Drive access</li>
            <li>You will be redirected back to Gallery settings</li>
          </ol>
        </section>

        {/* Step 11 */}
        <section id="step11" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 11: Get Folder ID</h2>
          <p className="text-neutral-700 dark:text-neutral-300 mb-3">
            The Folder ID is in the URL of your folder:
          </p>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li>Look at the browser URL bar while inside the folder</li>
            <li>
              The URL format is: <code className="bg-neutral-200 dark:bg-neutral-800 px-2 py-1 rounded text-xs">https://drive.google.com/drive/folders/FOLDER_ID</code>
            </li>
            <li>Copy the <strong>FOLDER_ID</strong> part from the URL</li>
          </ol>
          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              <strong>Example:</strong><br />
              URL: <code className="text-xs">https://drive.google.com/drive/folders/1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu</code><br />
              Folder ID: <code className="text-xs">1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu</code>
            </p>
          </div>
        </section>

        {/* Step 12 */}
        <section id="step12" className="mb-8 bg-neutral-50 dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">Step 12: Configure Your Application</h2>
          <p className="text-neutral-700 dark:text-neutral-300 mb-4">
            Now you have everything needed:
          </p>
          <ol className="list-decimal ml-6 space-y-2 text-neutral-700 dark:text-neutral-300">
            <li><strong>OAuth Client JSON File</strong> - The downloaded file</li>
            <li><strong>Folder ID</strong> - The ID from the URL</li>
          </ol>
          <div className="mt-6">
            <button
              onClick={() => navigate('/setting')}
              className="w-full py-3.5 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-200 text-white dark:text-neutral-900 rounded-2xl font-medium transition-all"
            >
              Go to Settings to Configure
            </button>
          </div>
        </section>

        {/* Summary */}
        <section className="mb-8 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-3xl p-6">
          <h2 className="text-2xl font-bold text-green-900 dark:text-green-300 mb-4">Summary</h2>
          <p className="text-green-800 dark:text-green-300 mb-3">You have successfully:</p>
          <ul className="space-y-2 text-green-700 dark:text-green-400">
            <li className="flex items-start gap-2">
              <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Created a Google Cloud project</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Enabled Google Drive API</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Configured OAuth consent screen</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Generated and downloaded OAuth Client JSON file</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Created Google Drive folder</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>Obtained Folder ID</span>
            </li>
          </ul>
        </section>

        {/* Security Reminder */}
        <section className="mb-8 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-3xl p-6">
          <h2 className="text-xl font-bold text-red-900 dark:text-red-300 mb-3">⚠️ Security Reminders</h2>
          <ul className="list-disc ml-6 space-y-2 text-red-800 dark:text-red-300">
            <li>Never commit the JSON key file to Git</li>
            <li>Never share it publicly</li>
            <li>Store it encrypted in production</li>
            <li>Rotate keys periodically</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
