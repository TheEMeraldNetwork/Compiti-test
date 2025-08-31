# 🚀 Deployment Checklist

**⚠️ FOR TESTING PURPOSES ONLY ⚠️**

## 🔐 Security-First Deployment

### ✅ Pre-Deployment Security Check

- [ ] `.env` file is in `.gitignore` 
- [ ] No actual credentials in any committed files
- [ ] Only template files (`env_example.txt`) contain placeholder values
- [ ] All sensitive data uses environment variables
- [ ] `SECURITY.md` guidelines are followed

### 📋 Deployment Steps

#### 1. **Get Your Credentials** (Do this FIRST)

**GitHub Token:**
```bash
# Go to: https://github.com/settings/tokens
# Create token with 'repo' scope only
# Copy the token (starts with ghp_)
```

**Gmail App Password:**
```bash
# Go to: https://myaccount.google.com/security
# Enable 2-factor authentication first
# Generate app password for "Mail"
# Copy the 16-character password
```

#### 2. **Secure Local Setup**

```bash
# Navigate to your project
cd /Users/davideconsiglio/Desktop/Compiti_Vittoria/automated_math_solver

# Activate virtual environment
source math_solver_venv/bin/activate

# Create your secure credentials file
cp env_example.txt .env

# Edit with your ACTUAL credentials (NEVER commit this file)
nano .env
```

Your `.env` should look like:
```bash
GITHUB_TOKEN=ghp_your_actual_github_token_here
EMAIL_SENDER=davideconsiglio1978@gmail.com
EMAIL_PASSWORD=your_actual_16_character_app_password
```

#### 3. **Test the System**

```bash
# Test GitHub connection
python app.py test --github

# Test email connection  
python app.py test --email

# Run comprehensive tests
python test_system.py

# Manual trigger test
python app.py trigger
```

#### 4. **Launch Production**

```bash
# Start with web interface
python app.py start --web --host 0.0.0.0 --port 5000

# Or just the scheduler
python app.py start
```

#### 5. **Verify Deployment**

- [ ] Web interface accessible at http://localhost:5000
- [ ] System status shows "is_running: true"
- [ ] GitHub repository accessible: [TheEMeraldNetwork/Compiti-test](https://github.com/TheEMeraldNetwork/Compiti-test)
- [ ] Email notifications working
- [ ] Upload test problem and verify processing

## 🌐 GitHub Repository Setup

### Repository Structure:
```
TheEMeraldNetwork/Compiti-test/
├── problems/           # Upload math problems here
├── solutions/          # Automated solutions appear here
└── README.md          # Will be auto-generated
```

### Upload Process:
1. Go to your repository: [TheEMeraldNetwork/Compiti-test](https://github.com/TheEMeraldNetwork/Compiti-test)
2. Create `problems` folder if it doesn't exist
3. Upload mathematical problem files (PDF, images, text)
4. System processes automatically every 30 minutes
5. Solutions appear in `solutions` folder
6. Email notifications sent to: davideconsiglio1978@gmail.com

## 📊 Monitoring & Maintenance

### System Health Checks:
```bash
# Check system status
python app.py status

# View logs
tail -f logs/math_solver.log

# Manual processing trigger
python app.py trigger
```

### Expected Behavior:
- ✅ Checks GitHub every 30 minutes
- ✅ Processes mathematical content only
- ✅ Generates solutions using SymPy
- ✅ Uploads solutions to GitHub
- ✅ Sends email notifications
- ✅ Updates web interface

## 🚨 Troubleshooting

### Common Issues:

**"GitHub authentication failed"**
```bash
# Check token in .env file
# Verify token has 'repo' permissions
# Test: python app.py test --github
```

**"Email connection failed"**
```bash
# Verify Gmail app password in .env
# Ensure 2-factor authentication enabled
# Test: python app.py test --email
```

**"No mathematical content found"**
```bash
# Ensure uploaded files contain math problems
# Check supported formats: PDF, JPG, PNG, TXT, MD
# Verify content has mathematical keywords
```

### Emergency Commands:
```bash
# Stop all processes
pkill -f "python app.py"

# Reset environment
cp env_example.txt .env

# View detailed logs
cat logs/math_solver.log | tail -50

# Test individual components
python test_system.py
```

## 📈 Scaling & Performance

### Current Limits:
- **File Size**: 50MB maximum
- **Check Frequency**: Every 30 minutes
- **Concurrent Processing**: 1 problem at a time
- **Supported Formats**: PDF, JPG, PNG, TXT, MD

### Performance Monitoring:
- Check processing times in logs
- Monitor memory usage during OCR
- Watch GitHub API rate limits
- Email delivery success rates

## 🔒 Security Maintenance

### Regular Security Tasks:
- [ ] Rotate GitHub tokens every 90 days
- [ ] Rotate Gmail app passwords every 90 days
- [ ] Review log files for security issues
- [ ] Update dependencies regularly
- [ ] Monitor for unauthorized access attempts

### Security Incident Response:
1. **If credentials compromised**: Immediately revoke and regenerate
2. **If system breached**: Stop all processes, review logs
3. **If inappropriate content processed**: Check validation rules

---

## ✅ Final Deployment Verification

Your system is ready when:
- [ ] All tests pass: `python test_system.py`
- [ ] GitHub connection works: `python app.py test --github`
- [ ] Email connection works: `python app.py test --email`
- [ ] Web interface loads: http://localhost:5000
- [ ] Manual trigger works: `python app.py trigger`
- [ ] No credentials in committed files
- [ ] `.env` file properly configured locally

**🎉 System is now ready for mathematical problem solving!**

**Repository**: [TheEMeraldNetwork/Compiti-test](https://github.com/TheEMeraldNetwork/Compiti-test)
**Email**: davideconsiglio1978@gmail.com
**Interface**: http://localhost:5000 (when running)

---

**Remember: This system is FOR TESTING PURPOSES ONLY! 🧪**
