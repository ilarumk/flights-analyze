# 🔐 Secrets Setup Guide

## Local Development

### 1. Create Secrets File

Copy the template:
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

### 2. Add Your API Keys

Edit `.streamlit/secrets.toml`:
```toml
# Google Gemini API Key
GEMINI_API_KEY = "your-actual-api-key-here"
```

### 3. Get API Keys

**Gemini API:**
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key to your secrets.toml

### 4. Verify

The file `.streamlit/secrets.toml` is in `.gitignore` and will **NEVER be committed**.

---

## Streamlit Cloud Deployment

### 1. Go to App Settings

1. Open your app on Streamlit Cloud
2. Click "⚙️ Settings" (bottom right)
3. Select "Secrets"

### 2. Add Secrets

Paste this into the secrets editor:
```toml
GEMINI_API_KEY = "your-actual-api-key-here"
```

### 3. Save

Click "Save" - your app will restart with the secrets available.

---

## Using Secrets in Code

```python
import streamlit as st

# Access secrets
api_key = st.secrets["GEMINI_API_KEY"]

# Or with fallback to environment variable
import os
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
```

---

## Security Best Practices

✅ **DO:**
- Use `.streamlit/secrets.toml` for local development
- Use Streamlit Cloud Secrets for deployment
- Add secrets files to `.gitignore`
- Use environment variables as fallback
- Rotate API keys regularly

❌ **DON'T:**
- Commit secrets to git
- Share secrets in chat/email
- Hardcode API keys in source code
- Use the same key for dev and production

---

## Troubleshooting

### "KeyError: GEMINI_API_KEY"

**Cause:** Secrets file missing or key not set

**Fix (Local):**
```bash
# Check if file exists
ls -la .streamlit/secrets.toml

# If not, copy template and add your key
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit the file and add your key
```

**Fix (Streamlit Cloud):**
1. Go to app settings → Secrets
2. Add the GEMINI_API_KEY
3. Save and restart

### "API key not working"

**Check:**
1. Key is valid and not expired
2. No extra spaces in the secret value
3. Quotes are properly formatted in TOML
4. App has been restarted after adding secrets

---

## Files Overview

```
.streamlit/
├── secrets.toml.template  ← Template (safe to commit)
└── secrets.toml           ← Your actual keys (NEVER commit!)
```

`.gitignore` includes:
```
.streamlit/secrets.toml
*.env
.env
```

This ensures secrets are never committed to git.
