# Google Drive Service Account Setup Guide

This guide will walk you through setting up a Google Cloud Service Account for the Gallery application to access Google Drive.

## Prerequisites

- Google account
- Access to Google Cloud Console
- Admin rights to create Service Accounts

## Step 1: Access Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. You will see a welcome dialog

## Step 2: Accept Terms and Continue

When you first access Google Cloud Console, you'll see a welcome dialog:

1. Select your **Country** from the dropdown (e.g., "Ukraine")
2. Check the box: "I agree to the Google Cloud Platform Terms of Service"
3. (Optional) Check the box for email updates if you want to receive news and offers
4. Click **"Agree and continue"** button at the bottom right

## Step 3: Create or Select a Project

Now you're on the Google Cloud Console main page.

1. Look at the top left, next to "Google Cloud" logo - you'll see a button **"Select a project"**
2. Click on **"Select a project"** button

A dialog will appear showing existing projects (if any).

## Step 4: Enable 2-Step Verification (if required)

If you see a message "Google Cloud access blocked" requiring 2-Step Verification:

### 4.1. Access Security Settings

1. Click **"Go to settings"** button
2. You'll be redirected to the 2-Step Verification setup page

### 4.2. Set Up Authenticator App

1. Click on **"Authenticator"** option
2. Click **"Set up authenticator"** button
3. A dialog "Set up authenticator app" will appear with instructions:
   - In the Google Authenticator app tap the **+** button
   - Choose **"Scan a QR code"**
4. A QR code will be displayed on screen
5. Scan the QR code with your authenticator app (Google Authenticator, Microsoft Authenticator, Authy, etc.)
6. If you can't scan the QR code, click **"Can't scan it?"** to get a manual setup key
7. Click **"Next"** button

### 4.3. Verify Authenticator Setup

1. After clicking "Next", you'll see a dialog: "Enter the 6-digit code you see in the app"
2. Open your authenticator app and find the 6-digit code for your Google account
3. Enter the code in the **"Enter Code"** field
4. Click **"Verify"** button
5. You'll see a confirmation message "Authenticator app has been set up"
6. Click **"Turn on"** button (blue button in the top right)

### 4.4. Add Additional Second Step (Required)

A dialog "Add second steps to your account" will appear:

1. Click **"Go back"** button (this will close the dialog)
2. You'll see the 2-Step Verification page showing:
   - **Authenticator** - marked with green checkmark "Added 1 minute ago"
   - **2-Step Verification is off** status at the bottom
3. Note: The current page shows "2-Step Verification is off" but this will change in the next step

> **Note:** Google requires at least two different second-step methods before enabling 2-Step Verification. You can add a phone number or passkey later if needed, but for now we'll proceed to enable it.

### 4.5. Add Phone Number (Required)

Google requires a backup phone number before enabling 2-Step Verification:

1. On the "2-Step Verification phones" page, click **"Add phone number"** button
2. A dialog "Confirm your phone number" will appear showing your number
3. Verify the phone number is correct and click **"Save"** button
4. You'll see the phone number listed with a prompt: "Approve this phone for 2-Step Verification?"
5. Click **"Approve"** button

### 4.6. Verify Your Identity

After clicking "Approve", Google will ask you to verify your identity:

1. You'll see a page: "To continue, first verify it's you"
2. Enter your Google account password
3. Click **"Next"** button
4. If you see "We couldn't verify it's you" message, follow the suggestions:
   - Use a device and browser you've signed in on before
   - Use a familiar Wi-Fi network, such as at home or work
   - If you've already tried these, change your recovery phone in your settings

> **Note:** This verification step ensures security. You may need to use a trusted device or network for verification to succeed.

### 4.7. Enable 2-Step Verification (Final Step)

1. Navigate to the "2-Step Verification" main page
2. Click the **"Turn on 2-Step Verification"** button
3. You'll see a confirmation dialog: "You're now protected with 2-Step Verification"
   - **Authenticator** - marked with green checkmark "Added 5 minutes ago"
   - **Phone number** - shows your phone number with green checkmark
4. Click **"Done"** button
5. 2-Step Verification is now enabled!

### 4.8. Return to Google Cloud Console

1. Open a new browser tab or click on the existing Google Cloud Console tab
2. Go to: **https://console.cloud.google.com/**
3. The "Google Cloud access blocked" message should now be gone
4. You can now proceed with creating a project

## Step 5: Create New Project

Now that 2-Step Verification is enabled, you can create a Google Cloud project:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** in the top left (next to Google Cloud logo)
3. In the dialog, click **"New project"** button in the top right
4. You'll see the "New Project" form with:
   - **Project name** - a default name like "My Project 81122" (you can change it)
   - **Project ID** - automatically generated (e.g., "apt-philosophy-499815-n0")
   - **Parent resource** - set to "No organization" (leave as is)

### 5.1. Configure Project Details

1. In the **"Project name"** field, enter a meaningful name for your project (e.g., "Gallery App", "Photo Gallery", or "My Gallery Project")
2. The **Project ID** will be automatically generated based on your project name
   - You can click **"Edit"** to customize it if needed
   - Note: Project ID cannot be changed later
3. Leave **"Parent resource"** as **"No organization"**
4. Click **"Create"** button
5. You'll see a notification "Create Project: Gallery App" with a **"Select Project"** link
6. The project is now created and you're back at the Google Cloud Console home page

## Step 6: Enable Google Drive API

Now you need to enable the Google Drive API for your project:

1. Click on **"Select a project"** button at the top left
2. Click **"Select Project"** in the notification panel (top right), OR select your project from the list
3. Once your project is selected, go to: **https://console.cloud.google.com/apis/library/drive.googleapis.com**
4. You'll see the "Google Drive API" page with:
   - API description: "Create and manage resources in Google Drive"
   - Two buttons: **"Enable"** and **"Try this API"**
5. Click the blue **"Enable"** button
6. Wait for the API to be enabled (this may take a few seconds)
7. You'll be redirected to the "API/Service Details" page showing:
   - **Status: Enabled** ✓
   - Message: "To call this API from your own applications, you may need to create credentials"

## Step 7: Create Service Account

Now you need to create a Service Account to access Google Drive programmatically:

1. On the left sidebar, click **"Credentials"**
2. You'll see the Credentials page with three sections:
   - **API Keys** - No API keys to display
   - **OAuth 2.0 Client IDs** - No OAuth clients to display
   - **Service Accounts** - No service accounts to display
3. Click the **"+ Create credentials"** button at the top
4. A dropdown menu will appear with options:
   - API key
   - OAuth client ID
   - **Service account** ← Select this option
5. Click **"Service account"**

### 7.1. Fill Service Account Details

You'll see a form with three sections:

**Section 1: Create service account**

1. **Service account name** - Enter a descriptive name (e.g., "gallery-drive-access" or "gallery-service-account")
2. **Service account ID** - Automatically generated based on the name (you can edit it)
3. **Email address** - Automatically shown (e.g., `<id>@gallery-app-499816.iam.gserviceaccount.com`)
4. **Service account description** (optional) - Enter a description like "Service account for Gallery app to access Google Drive"
5. Click **"Create and continue"** button

**Section 2: Permissions (optional)**

- You can skip this step by clicking **"Continue"** or leave it and proceed to the next section

**Section 3: Principals with access (optional)**

- You can skip this step as well

6. Click **"Create and close"** button at the bottom (or **"Done"** if you went through all sections)
7. You'll see a notification "Service account created"
8. The new service account will appear in the **Service Accounts** list with:
   - **Email**: `gallery-drive-access@gallery-app-499816.iam.gserviceaccount.com`
   - **Name**: `gallery-drive-access`

## Step 8: Create and Download JSON Key

Now you need to create a JSON key file for the Service Account:

1. In the **Service Accounts** section, click on the service account email link (e.g., `gallery-drive-access@gallery-app-499816.iam.gserviceaccount.com`)
2. This will open the Service Account details page showing:
   - **Name**: gallery-drive-access
   - **Email**: gallery-drive-access@gallery-app-499816.iam.gserviceaccount.com
   - **Unique ID**: 111868126562252699761
   - **Service account status**: Enabled ✓

### 8.1. Generate JSON Key

1. Click on the **"Keys"** tab at the top (between "Permissions" and "Metrics")
2. You'll see the Keys management page with:
   - A warning about service account key security
   - Information about automatic key disabling in public repositories
   - **"Add key"** button with a dropdown
3. Click on **"Add key"** dropdown button
4. Select **"Create new key"** from the dropdown menu
5. A dialog "Create private key for 'gallery-drive-access'" will appear with key type options:
   - **JSON** (Recommended) - selected by default
   - P12 - For backward compatibility
6. Make sure **JSON** is selected
7. Click **"Create"** button
8. The JSON key file will be automatically downloaded to your computer (e.g., `gallery-app-499816-a310d2aec05b.json`)
9. A dialog "Private key saved to your computer" will appear with a warning to store it securely
10. Click **"Close"** button
11. The new key will appear in the Keys list with:
    - **Status**: Active ✓
    - **Key ID**: a310d2aec05b45d2097d81c11dcffbe4c7208efe
    - **Creation date**: Jun 18, 2026
    - **Expiration date**: Jan 1, 10000

> **Important**: Keep this JSON file secure! It contains credentials to access your Google Drive. Never commit it to version control or share it publicly.

## Step 9: Create Google Drive Folder

Now you need to create a folder in Google Drive and share it with the Service Account:

1. Go to [Google Drive](https://drive.google.com/) (redirects to https://drive.google.com/drive/home)
2. Click **"New"** button (or **"+ New"** in the left sidebar)
3. Select **"New folder"** (or **"Folder"**)
4. Enter a folder name (e.g., "Gallery Photos", "Gallery Storage")
5. Click **"Create"**
6. The folder will be created and opened

## Step 10: Share Folder with Service Account

Now you need to give the Service Account access to this folder:

1. Click on the folder name dropdown **"Gallery Photos"** at the top (with the arrow)
2. Select **"Share"** from the dropdown menu
3. A dialog **"Share 'Gallery Photos'"** will appear with:
   - A text field: "Add people, groups, spaces, and calendar events"
   - **People with access** section showing you as Owner
   - **General access** section set to "Restricted"

### 10.1. Add Service Account Email

1. In the text field "Add people, groups, spaces, and calendar events", paste the Service Account email address
   - The email is: `gallery-drive-access@gallery-app-499816.iam.gserviceaccount.com`
   - You can find it in the downloaded JSON file under the `client_email` field
   - Or copy it from the Google Cloud Console Service Account page
2. Press Enter or click the suggested email
3. A permission dropdown will appear - select **"Editor"** (this gives read and write access)
4. Click **"Send"** or **"Share"** button
5. You may see a notification that the Service Account doesn't have a Google Account - click **"Share anyway"**
6. The Service Account will now appear in the **"People with access"** section with **"Editor"** role
7. Click **"Done"** button

## Step 11: Get Folder ID

The Folder ID is in the URL of your folder:

1. Look at the browser URL bar while inside the "Gallery Photos" folder
2. The URL format is: `https://drive.google.com/drive/folders/FOLDER_ID`
3. Copy the **FOLDER_ID** part from the URL
   - Example from your URL: `1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu`
   - This is the Folder ID you'll use in your application configuration

> **Example URL**: `https://drive.google.com/drive/folders/1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu`  
> **Folder ID**: `1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu`

## Step 12: Configure Your Application

Now you have everything needed to configure your Gallery application:

1. **Service Account JSON Key File**: The file you downloaded (e.g., `gallery-app-499816-a310d2aec05b.json`)
2. **Folder ID**: The ID from the URL (e.g., `1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu`)

### Configuration Steps:

1. Store the JSON key file securely in your application
   - Never commit it to version control
   - Add `*.json` to your `.gitignore` file
   - Or use environment variables to store the credentials

2. Use the Folder ID in your application settings
   - This tells your app which folder to use for storing/retrieving photos

3. Test the connection:
   - Your application should now be able to access the Google Drive folder
   - Upload a test file to verify it works

---

## Summary

You have successfully:

✅ **Step 1-2**: Accepted Google Cloud Terms and created a Google Cloud project  
✅ **Step 3-4**: Enabled 2-Step Verification with Authenticator app  
✅ **Step 5**: Created a new Google Cloud project "Gallery App"  
✅ **Step 6**: Enabled Google Drive API  
✅ **Step 7**: Created a Service Account "gallery-drive-access"  
✅ **Step 8**: Generated and downloaded JSON key file  
✅ **Step 9**: Created "Gallery Photos" folder in Google Drive  
✅ **Step 10**: Shared the folder with Service Account (Editor access)  
✅ **Step 11**: Obtained Folder ID from URL  

### Important Information:

- **Service Account Email**: `gallery-drive-access@gallery-app-499816.iam.gserviceaccount.com`
- **JSON Key File**: `gallery-app-499816-a310d2aec05b.json`
- **Folder ID**: `1wcqxhgLNTR-9hJTnxPKJFzYSTNQsBPHu`
- **Folder Name**: Gallery Photos
- **Access Level**: Editor (read/write)

### Security Reminders:

⚠️ **Keep your JSON key file secure!**
- Never commit it to Git
- Never share it publicly
- Store it encrypted in production
- Rotate keys periodically

---

*Last updated: 2026-06-18*

## Step 5: Create New Project

1. After 2-Step Verification is enabled, return to Google Cloud Console
2. Click **"Select a project"** → **"New project"**

**⏳ Waiting for next screenshot...**

---

## Step 3: Enable Google Drive API

**⏳ Waiting for instructions...**

---

## Step 4: Create Service Account

**⏳ Waiting for instructions...**

---

## Step 5: Generate and Download JSON Key

**⏳ Waiting for instructions...**

---

## Step 6: Create Google Drive Folder

**⏳ Waiting for instructions...**

---

## Step 7: Share Folder with Service Account

**⏳ Waiting for instructions...**

---

## Step 8: Get Folder ID

**⏳ Waiting for instructions...**

---

## Step 9: Configure Application

**⏳ Waiting for instructions...**

---

## Troubleshooting

Common issues and solutions will be added here.

---

*Last updated: 2026-06-18*
