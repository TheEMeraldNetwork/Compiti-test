# 🔐 Security Guidelines

**⚠️ IMPORTANT: NEVER COMMIT SENSITIVE CREDENTIALS TO GITHUB ⚠️**

## 🚨 Critical Security Rules

### ❌ NEVER commit these files:
- `.env` (contains passwords and tokens)
- Any file with actual credentials
- Log files with sensitive information

### ✅ ALWAYS use:
- Environment variables for sensitive data
- `.gitignore` to exclude sensitive files
- Template files (like `env_example.txt`) for structure

## 🔑 Secure Credential Management

### 1. **Local Development Setup**

```bash
# Copy template and add YOUR credentials locally
cp env_example.txt .env

# Edit .env with your actual credentials (NEVER commit this file)
nano .env
```

### 2. **Your .env file should contain:**
```bash
# GitHub API Token (get from: https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_your_actual_github_token_here

# Email Configuration  
EMAIL_SENDER=davideconsiglio1978@gmail.com
EMAIL_PASSWORD=your_actual_16_character_app_password
```

### 3. **Production Deployment**

For production servers, set environment variables directly:

```bash
# On your server
export GITHUB_TOKEN="ghp_your_actual_token"
export EMAIL_SENDER="davideconsiglio1978@gmail.com"
export EMAIL_PASSWORD="your_actual_app_password"
```

Or use your hosting platform's environment variable settings.

## 📋 Security Checklist

Before committing to GitHub:

- [ ] `.env` file is in `.gitignore`
- [ ] No actual passwords in any committed files
- [ ] Only template files (`env_example.txt`) are committed
- [ ] All sensitive data uses environment variables
- [ ] Documentation explains how to set up credentials locally

## 🛡️ Additional Security Measures

### Content Validation
- ✅ Only processes mathematical content
- ✅ Blocks forbidden/inappropriate content
- ✅ File size limits (50MB max)
- ✅ Safe file format restrictions
- ✅ Source validation (only designated GitHub repo)

### Access Control
- ✅ GitHub token with minimal required permissions (`repo` scope only)
- ✅ Gmail app password (not main account password)
- ✅ Local-only credential storage

### Logging Security
- ✅ No passwords logged
- ✅ Sanitized error messages
- ✅ Log rotation to prevent disk filling

## 🔧 How to Get Your Credentials

### GitHub Token:
1. Go to [GitHub Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select **only** `repo` scope (full control of repositories)
4. Copy token and add to your local `.env` file
5. **NEVER share or commit this token**

### Gmail App Password:
1. Enable 2-factor authentication on your Gmail
2. Go to [Google Account Security](https://myaccount.google.com/security)
3. Under "2-Step Verification" → "App passwords"
4. Generate password for "Mail" application
5. Copy 16-character password to your local `.env` file
6. **NEVER share or commit this password**

## 🚨 If Credentials Are Compromised

### If GitHub Token is exposed:
1. Immediately revoke the token at [GitHub Settings](https://github.com/settings/tokens)
2. Generate a new token
3. Update your local `.env` file

### If Gmail App Password is exposed:
1. Revoke the app password in [Google Account Settings](https://myaccount.google.com/security)
2. Generate a new app password
3. Update your local `.env` file

## ✅ Safe Repository Structure

```
automated_math_solver/
├── .env                    # ❌ NEVER COMMIT (in .gitignore)
├── .gitignore             # ✅ Protects sensitive files
├── env_example.txt        # ✅ Safe template file
├── config.yaml            # ✅ Public configuration only
└── ...other files
```

## 📖 For Team Development

If working with others:

1. **Share**: Template files, documentation, public config
2. **DON'T share**: Your personal `.env` file, tokens, passwords
3. **Each person**: Gets their own GitHub token and Gmail app password
4. **Communication**: Use secure channels (not Slack/email) for credential sharing if absolutely necessary

---

**Remember: Security is everyone's responsibility! 🛡️**

**When in doubt, ask: "Would I be comfortable if this appeared on the public internet?" If no, don't commit it!**
