# How to Get Gmail API Credentials

Follow these steps to obtain your `credentials.json` file for Gmail API access.

## Step-by-Step Guide

### 1. Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 2. Create a New Project (or select existing)

1. Click on the project dropdown at the top
2. Click "New Project"
3. Name it: "AI Employee" or similar
4. Click "Create"

### 3. Enable Gmail API

1. In the search bar, type "Gmail API"
2. Click on "Gmail API"
3. Click "Enable"

### 4. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" (unless you have a Google Workspace)
3. Click "Create"
4. Fill in required fields:
   - App name: "AI Employee"
   - User support email: Your email
   - Developer contact: Your email
5. Click "Save and Continue"
6. On "Scopes" page, click "Add or Remove Scopes"
7. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` (read emails)
   - `https://www.googleapis.com/auth/gmail.send` (send emails)
8. Click "Update" then "Save and Continue"
9. On "Test users" page, add your email address
10. Click "Save and Continue"

### 5. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "AI Employee Desktop"
5. Click "Create"
6. Click "Download JSON" on the popup
7. Save the file as `credentials.json` in your project root

### 6. Move the File

```bash
# Move the downloaded file to your project directory
mv ~/Downloads/client_secret_*.json D:/vsCode/CLI/Hackathon-0/credentials.json
```

### 7. First-Time Authentication

When you run the gmail-watcher skill for the first time:

```bash
python .claude/skills/gmail-watcher/skill.py
```

It will:
1. Open a browser window
2. Ask you to log in to Google
3. Ask for permission to access Gmail
4. Save the token to `token.json`

### 8. Verify Setup

After authentication, you should have:
- `credentials.json` - Your OAuth client credentials
- `token.json` - Your access token (auto-generated)

Both files are in `.gitignore` and will NOT be committed to git.

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `credentials.json` to git
- Never share your credentials file
- Keep `token.json` private
- Both files are already in `.gitignore`

## Troubleshooting

**"Access blocked: This app's request is invalid"**
- Make sure you added your email as a test user in OAuth consent screen

**"The OAuth client was not found"**
- Re-download credentials.json from Google Cloud Console
- Make sure you selected "Desktop app" not "Web application"

**"Invalid grant" error**
- Delete `token.json` and re-authenticate
- Check system clock is correct

**"API has not been used in project"**
- Make sure Gmail API is enabled in your project
- Wait a few minutes after enabling

## Alternative: Service Account (Advanced)

For production/server use, consider using a Service Account instead of OAuth:
1. Create Service Account in Google Cloud Console
2. Download JSON key file
3. Use service account authentication in code

## Official Documentation

- Gmail API Quickstart: https://developers.google.com/gmail/api/quickstart/python
- OAuth 2.0 Setup: https://developers.google.com/identity/protocols/oauth2
- Gmail API Scopes: https://developers.google.com/gmail/api/auth/scopes

## Cost

Gmail API is free for:
- Up to 1 billion quota units per day
- Typical usage: ~5-10 units per email check
- Your usage will be well within free tier

## Next Steps

After obtaining credentials:
1. Run gmail-watcher skill to authenticate
2. Configure MCP server in Claude Code
3. Test email sending functionality
