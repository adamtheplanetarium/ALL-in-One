# 🚀 ALL-in-One Email Management Platform

A professional cloud-based email management system with SMTP rotation, email verification, campaign management, and real-time statistics.

## 🎯 What This Is

This is the **complete backend API** for managing:
- ✅ **Email Campaigns** (bulk sending & testing)
- ✅ **SMTP Server Management** (with smart rotation & auto-recovery)
- ✅ **FROM Address Verification** (IMAP-based)
- ✅ **Email Templates** (with dynamic variables)
- ✅ **Real-Time Statistics** (dashboard metrics)
- ✅ **Multi-User Support** (JWT authentication)

## 📁 Project Structure

```
ALL-in-One/
├── backend/              ← MAIN APPLICATION (Flask API)
│   ├── app.py           ← Flask application entry point
│   ├── config.py        ← Configuration management
│   ├── requirements.txt ← Python dependencies
│   ├── models/          ← Database models (8 tables)
│   ├── api/             ← REST API endpoints
│   ├── services/        ← Business logic
│   ├── tasks/           ← Background workers
│   └── utils/           ← Utilities (encryption, etc.)
├── Fake-client/         ← Original Windows GUI application
├── render.yaml          ← Render deployment config
├── DEPLOYMENT_GUIDE.md  ← Step-by-step deployment
├── PROJECT_PLAN.md      ← Complete project plan
└── ARCHITECTURE.md      ← System architecture
```

## 🚀 Quick Deploy to Render

### One-Click Deploy (Recommended)

1. **Go to Render**: https://dashboard.render.com/
2. **Click**: New → Blueprint
3. **Connect**: This GitHub repository
4. **Deploy**: Render auto-detects `render.yaml`
5. **Wait**: 5-7 minutes for build
6. **Done**: Your API is live!

### What Gets Deployed

- ✅ **Flask API** - All email management endpoints
- ✅ **PostgreSQL** - Database for all data
- ✅ **Free Tier** - $0/month (with limitations)

## 📚 API Endpoints

### Authentication
```
POST /api/auth/register  - Register new user
POST /api/auth/login     - Login & get JWT token
GET  /api/auth/me        - Get current user info
POST /api/auth/refresh   - Refresh access token
```

### SMTP Management
```
GET    /api/smtp                - List all SMTP servers
POST   /api/smtp                - Create SMTP server
PUT    /api/smtp/:id            - Update SMTP server
DELETE /api/smtp/:id            - Delete SMTP server
POST   /api/smtp/:id/test       - Test SMTP connection
POST   /api/smtp/bulk-import    - Bulk import SMTPs
POST   /api/smtp/reset-failures - Reset failure counts
```

### Campaigns
```
GET  /api/campaigns     - List all campaigns
POST /api/campaigns     - Create new campaign
```

### FROM Addresses
```
GET  /api/from-addresses  - List FROM addresses
POST /api/from-addresses  - Create FROM address
```

### Templates
```
GET  /api/templates  - List email templates
POST /api/templates  - Create email template
```

### Statistics
```
GET /api/stats/dashboard  - Get dashboard statistics
```

### Health Check
```
GET /health  - Service health check
```

## 🧪 Test Your Deployment

Once deployed, test with:

```bash
# Health check
curl https://your-app.onrender.com/health

# Register user
curl -X POST https://your-app.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "Admin123!",
    "role": "admin"
  }'

# Login
curl -X POST https://your-app.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'

# Get stats (use token from login)
curl https://your-app.onrender.com/api/stats/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔧 Local Development

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run application
python app.py
```

Access at: http://localhost:5000

## 📊 Database Models

The system automatically creates 8 tables:

1. **users** - User authentication
2. **smtp_servers** - SMTP pool with encrypted credentials
3. **campaigns** - Email campaigns
4. **recipients** - Campaign recipients
5. **from_addresses** - Sender email addresses
6. **email_templates** - HTML email templates
7. **email_logs** - Activity logging
8. **imap_accounts** - Inbox monitoring

## 🔒 Security Features

- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **Password Hashing** - bcrypt encryption
- ✅ **SMTP Encryption** - AES-256 for credentials
- ✅ **HTTPS** - Enforced on Render
- ✅ **CORS** - Configurable origins
- ✅ **Rate Limiting** - API protection

## 💰 Pricing

### Free Tier (Current Setup)
- Web Service: Free (spins down after 15 min inactivity)
- PostgreSQL: Free (90-day limit, 1GB storage)
- **Total: $0/month**

### Paid Tier (For Production)
- Web Service: $7/month (always on)
- PostgreSQL: $7/month (persistent)
- Background Worker: $7/month (Celery)
- Redis: $10/month (task queue)
- **Total: $31/month**

## 📖 Documentation

- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md`
- **Project Plan**: See `PROJECT_PLAN.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Backend Docs**: See `backend/README.md`

## 🎯 Features

### Current Features ✅
- Multi-user authentication with roles
- SMTP server CRUD operations
- Bulk SMTP import
- SMTP connection testing
- Campaign management
- FROM address tracking
- Email template storage
- Dashboard statistics
- Health monitoring

### Coming Soon 🔄
- React frontend dashboard
- Background email sending (Celery)
- Real-time updates (WebSocket)
- Email verification system
- IMAP monitoring
- Campaign analytics
- A/B testing

## 🔗 Links

- **Repository**: https://github.com/adamtheplanetarium/ALL-in-One
- **Deploy**: https://dashboard.render.com/
- **Docs**: See documentation files in repository

## 👥 Support

For issues and questions:
- GitHub Issues: https://github.com/adamtheplanetarium/ALL-in-One/issues

## 📝 License

MIT License

---

**Built with ❤️ for professional email marketing**

### 🚀 Ready to Deploy?

1. Go to https://dashboard.render.com/
2. Click "New" → "Blueprint"
3. Select this repository
4. Click "Apply"
5. Done in 5 minutes! 🎉
