# 📬 ALL-in-One Email Campaign Management Platform

**🎉 100% COMPLETE & PRODUCTION READY!**

A complete cloud-based email campaign management system with **background persistence** - your campaigns keep running even when you close the browser!

## ✨ Key Features

- **🔄 Background Persistence** - Campaigns run 24/7 in Celery workers (close browser, they keep running!)
- **⚡ Real-time Updates** - WebSocket integration for live campaign monitoring
- **🔌 SMTP Pool Management** - Auto-rotate, test, and auto-disable failing servers
- **📤 FROM Address Management** - Bulk import, IMAP extraction, and verification
- **📝 Template Engine** - Personalization with {RECIPIENT}, {NAME}, {DATE}, {RAND}
- **📊 Live Dashboard** - Real-time statistics and campaign monitoring
- **🔒 Secure** - JWT auth, bcrypt passwords, AES-256 SMTP encryption
- **☁️ Cloud Ready** - One-click deployment to Render.com

## 🚀 Quick Start

### Deploy to Render (Recommended)

1. **Fork this repository** to your GitHub account

2. **Create Render account** at https://render.com

3. **Deploy via Blueprint:**
   - Dashboard → "New" → "Blueprint"
   - Connect your GitHub repo
   - Select this repository
   - Render reads `render.yaml` and creates all services automatically

4. **Wait 10-15 minutes** for deployment

5. **Access your app** at the provided URL!

**Cost:** $31/month (Web $7 + Worker $7 + PostgreSQL $7 + Redis $10)

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run

# Celery Worker (separate terminal)
cd backend
celery -A tasks.celery_app worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## 📖 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide (Render.com + VPS)
- **[COMPLETE_SYSTEM.md](COMPLETE_SYSTEM.md)** - System overview and architecture
- **[WEB_ARCHITECTURE.md](WEB_ARCHITECTURE.md)** - Technical architecture details
- **[FRONTEND_STRUCTURE.md](FRONTEND_STRUCTURE.md)** - UI design and components

## 🏗️ Architecture

```
┌─────────────────┐
│   React App     │  ← User Interface (Dashboard, Campaigns, etc.)
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/WebSocket
         ↓
┌─────────────────┐
│  Flask API      │  ← REST API + WebSocket events
│   (Backend)     │
└────────┬────────┘
         │
    ┌────┴────┬─────────────┐
    ↓         ↓             ↓
┌─────────┐ ┌───────┐ ┌──────────┐
│  Redis  │ │ Celery│ │PostgreSQL│
│ (Queue) │ │Worker │ │   (DB)   │
└─────────┘ └───────┘ └──────────┘
              ↓
    📧 Background Email Sending
    (Runs independently!)
```

## 🎯 What Makes This Special?

### Background Persistence
Unlike typical web apps, campaigns run in **Celery workers**, not the web server:
1. User starts campaign → queued to Celery
2. Celery worker picks up task → starts sending
3. **User closes browser** → campaign keeps running! ✨
4. User reopens → sees live progress

### Intelligent SMTP Rotation
- Redis-locked rotation (thread-safe across workers)
- Auto-disable after 10 failures
- Auto-reset after 3 successes
- Real-time failure tracking

### FROM Address Management
- Extract from IMAP inbox automatically
- Verification system (send test → check delivery)
- Track status: verified, unverified, dead

## 🛠️ Tech Stack

**Backend:**
- Flask 3.0 (Web framework)
- Celery 5.4 (Background tasks)
- SQLAlchemy (ORM)
- PostgreSQL 15 (Database)
- Redis 7 (Task queue + locks)
- Socket.IO (Real-time)
- JWT + bcrypt (Auth)

**Frontend:**
- React 18
- Vite 5
- Tailwind CSS 3.3
- Recharts 2.10
- Socket.IO Client 4.7
- Axios

**Deployment:**
- Render.com Blueprint
- Gunicorn + Eventlet
- Nginx (VPS option)

## 📊 System Status

| Component | Status | Details |
|-----------|--------|---------|
| Backend API | ✅ 100% | 8 blueprints, all endpoints working |
| Background Tasks | ✅ 100% | Campaign, verification, monitoring |
| Frontend UI | ✅ 100% | 6 pages, WebSocket, auth |
| Database | ✅ 100% | 8 tables, relationships configured |
| Deployment | ✅ 100% | render.yaml ready |
| Documentation | ✅ 100% | 4 comprehensive guides |

## 🧪 Testing

### Backend API Test
```bash
# Health check
curl https://your-app.onrender.com/health

# Register
curl -X POST https://your-app.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

### Background Persistence Test
1. Create campaign with 100 recipients
2. Start campaign
3. **Close browser** 🔥
4. Wait 5 minutes
5. **Reopen browser**
6. Verify emails_sent increased → **Background persistence works!** ✨

## 📦 Repository Structure

```
ALL-in-One/
├── backend/
│   ├── api/              # REST API endpoints
│   ├── models/           # Database models
│   ├── tasks/            # Celery background tasks
│   ├── utils/            # Encryption, helpers
│   ├── app.py           # Flask application
│   ├── config.py        # Configuration
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/       # React pages (6 pages)
│   │   ├── components/  # Layout, UI components
│   │   ├── services/    # API client
│   │   └── App.jsx      # Main app
│   ├── package.json
│   └── vite.config.js
│
├── Fake-client/         # Original Windows GUI (reference)
│   ├── GUI-Mailer/
│   └── SMTP-Validator/
│
├── render.yaml          # Render.com deployment config
├── DEPLOYMENT.md        # Deployment guide
├── COMPLETE_SYSTEM.md   # System overview
└── README.md           # This file
```

## 🔧 Configuration

Key environment variables:

```bash
# Flask
SECRET_KEY=<random-32-chars>
JWT_SECRET_KEY=<random-32-chars>
ENCRYPTION_KEY=<random-32-bytes-base64>

# Database
DATABASE_URL=postgresql://user:pass@host/db

# Redis
REDIS_URL=redis://host:6379/0

# Campaign Settings
SMTP_FAILURE_THRESHOLD=10
SMTP_SUCCESS_RESET_COUNT=3
DEFAULT_RETRY_COUNT=5
MAX_THREADS=50
```

## 🆚 Windows GUI vs Web Platform

| Feature | Windows GUI | Web Platform |
|---------|-------------|--------------|
| Deployment | Local only | Cloud, anywhere |
| Persistence | ❌ Must stay open | ✅ Background 24/7 |
| Multi-user | ❌ | ✅ |
| Remote Access | ❌ | ✅ |
| Scalability | Limited | Unlimited |
| Cost | Free | $31/month |

## 📞 Support

- **Documentation:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues:** GitHub Issues
- **Repository:** https://github.com/adamtheplanetarium/ALL-in-One

## 📝 License

This project is built for demonstration and learning purposes.

---

**Built with ❤️ - 100% Complete & Production Ready! 🚀**
