# Quick Start Guide

## 🚀 Local Development Setup

### Prerequisites
```bash
# Required:
- Node.js 16+ and npm
- Python 3.8+
- Git
```

### 1. Clone Repository
```bash
git clone https://github.com/adamtheplanetarium/ALL-in-One.git
cd ALL-in-One
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Backend
```bash
cd backend
npm install
npm run dev
```
Backend runs on: http://localhost:5000

### 4. Start Frontend (New Terminal)
```bash
cd frontend
npm install
npm start
```
Frontend runs on: http://localhost:3000

### 5. Login
- Open: http://localhost:3000
- Password: `@OLDISGOLD2026@`

---

## 📝 Quick Usage

### Add SMTP Servers
1. Go to **SMTP Servers** page
2. Click **Add SMTP Server**
3. Enter: Host, Port, Username, Password
4. Click **Test** to verify
5. Click **Add Server**

### Upload Email Lists
1. Go to **Email Lists** page
2. **Recipients**: Upload target emails (.txt or .csv)
3. **From Emails**: Upload sender rotation list
4. Each file should have one email per line

### Create Template
1. Go to **Template** page
2. Write/paste HTML email content
3. Use variables:
   - `LINKREDIRECT` - Your redirect URL
   - `RANDOM` - Random number
   - `CapitalS` - Capitalized domain
   - `DATEX` - Current date
4. Click **Save Template**

### Configure Campaign
1. Go to **Settings** page
2. Set **Subject** line
3. Set **Sender Name**
4. Configure **Threads** (3-5 recommended)
5. Set **Sleep Time** (1-2 seconds)
6. Toggle **Test Mode** (ON for testing)
7. Click **Save Settings**

### Start Campaign
1. Go to **Dashboard**
2. Click **Start Campaign**
3. Watch real-time progress
4. Monitor live logs
5. **Close browser** - campaign continues!

### Reconnect Anytime
1. Open portal again
2. Login
3. Dashboard shows current status
4. Live logs continue streaming

---

## 🔥 Common Commands

### Backend
```bash
# Development mode with auto-reload
npm run dev

# Production mode
npm start

# With PM2 (background)
npm run pm2:start
npm run pm2:logs
npm run pm2:stop
```

### Frontend
```bash
# Development server
npm start

# Build for production
npm run build

# Test build locally
npm install -g serve
serve -s build
```

### Python Script (Direct)
```bash
cd Basic
python mainnotall.py
```

---

## 📊 File Structure

```
Basic/
├── mainnotall.py      # Main Python script (DON'T MODIFY)
├── config.ini         # Configuration file
├── smtp.txt           # SMTP servers list
├── emailx.txt         # Recipient emails
├── from.txt           # Sender emails (rotation)
├── ma.html            # Email template
└── working_smtp.txt   # SMTP with connection details
```

---

## 🎯 Tips & Best Practices

### Testing
- Always use **Test Mode** initially
- Test with small recipient list first
- Verify SMTP connections before campaign
- Check logs for errors

### Performance
- Start with 3 threads
- Use 1-2 second sleep time
- Monitor system resources
- Don't exceed 10 threads

### SMTP Management
- Test each server before using
- Monitor failure count
- Servers auto-disable after 2 failures
- Re-enable manually if needed

### Email Lists
- Validate email format
- Remove duplicates
- Keep separate backup files
- Track sent emails

### Templates
- Test variables before campaign
- Use inline CSS for emails
- Keep HTML simple
- Preview in email client

---

## 🐛 Quick Troubleshooting

### Backend Won't Start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Mac/Linux

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Mac/Linux
```

### Frontend Won't Start
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install

# Clear npm cache
npm cache clean --force
```

### Python Script Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check Python path
python --version
which python  # Mac/Linux
where python  # Windows
```

### SMTP Authentication Failed
- Verify credentials are correct
- Check if port 587 (TLS) or 465 (SSL)
- Some servers require app passwords
- Test with email client first

### Campaign Not Starting
- Ensure recipient emails uploaded
- Check SMTP servers configured
- Verify template exists
- Look at backend logs

---

## 📚 Documentation

- **Full Documentation**: README.md
- **Project Plan**: PROJECT_PLAN.md
- **Deployment**: DEPLOYMENT_GUIDE.md
- **Fake Client Analysis**: FAKE_CLIENT_ANALYSIS.md

---

## 🎉 You're Ready!

Start your email campaign journey with ALL-in-One Portal!

**Need Help?** Check the full README.md or open a GitHub issue.
