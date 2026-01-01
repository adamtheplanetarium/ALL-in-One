# 🚀 ALL-in-One Email Management Platform

A professional cloud-based email management system with real-time updates, SMTP rotation, and comprehensive verification features.

## 📋 Features

- ✅ **Multi-User Support** - JWT authentication with role-based access
- 📧 **SMTP Management** - Smart rotation with failure tracking and auto-recovery
- 🚀 **Campaign Management** - Test FROMs and Bulk sending modes
- ✅ **Email Verification** - IMAP-based verification with bounce detection
- 📊 **Real-Time Dashboard** - Live statistics via WebSocket
- 🔒 **Secure** - Encrypted password storage and JWT authentication
- ☁️ **Cloud-Ready** - Optimized for Render deployment

## 🏗️ Architecture

- **Backend**: Flask + SQLAlchemy + Flask-SocketIO
- **Database**: PostgreSQL
- **Cache & Queue**: Redis
- **Background Workers**: Celery
- **Deployment**: Render (with render.yaml configuration)

## 🚀 Quick Deploy to Render

### Option 1: Using render.yaml (Recommended)

1. **Fork/Clone this repository**
2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to create all services

3. **Services Created**:
   - ✅ Web Service (Flask API)
   - ✅ Background Worker (Celery)
   - ✅ PostgreSQL Database
   - ✅ Redis Instance

4. **Access your app**:
   - Your app will be available at: `https://allinone-email-platform.onrender.com`
   - API docs: `https://allinone-email-platform.onrender.com/`
   - Health check: `https://allinone-email-platform.onrender.com/health`

### Option 2: Manual Setup

#### 1. Create PostgreSQL Database
```
Service: PostgreSQL
Name: allinone-db
Plan: Starter ($7/month) or Free
Region: Oregon (US West)
```

#### 2. Create Redis Instance
```
Service: Redis
Name: allinone-redis
Plan: Starter ($10/month) or Free (25MB)
Region: Oregon (US West)
```

#### 3. Create Web Service
```
Service: Web Service
Name: allinone-email-platform
Environment: Python 3
Region: Oregon (US West)
Branch: main
Build Command: cd backend && pip install -r requirements.txt
Start Command: cd backend && gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
Plan: Starter ($7/month) or Free
```

**Environment Variables**:
```
FLASK_ENV=production
SECRET_KEY=(auto-generate)
JWT_SECRET_KEY=(auto-generate)
ENCRYPTION_KEY=(auto-generate)
DATABASE_URL=(from PostgreSQL service)
REDIS_URL=(from Redis service)
CORS_ORIGINS=*
```

#### 4. Create Background Worker
```
Service: Background Worker
Name: allinone-worker
Environment: Python 3
Region: Oregon (US West)
Branch: main
Build Command: cd backend && pip install -r requirements.txt
Start Command: cd backend && celery -A tasks.celery_app worker --loglevel=info --concurrency=4
Plan: Starter ($7/month)
```

**Environment Variables**: Same as Web Service

## 💻 Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/adamtheplanetarium/ALL-in-One.git
cd ALL-in-One
```

2. **Create virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. **Run the application**:
```bash
# Terminal 1: Flask API
python app.py

# Terminal 2: Celery Worker
celery -A tasks.celery_app worker --loglevel=info
```

7. **Access the application**:
- API: http://localhost:5000
- Health: http://localhost:5000/health

## 📚 API Documentation

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh access token

### SMTP Servers
- `GET /api/smtp` - List all SMTP servers
- `POST /api/smtp` - Create SMTP server
- `PUT /api/smtp/:id` - Update SMTP server
- `DELETE /api/smtp/:id` - Delete SMTP server
- `POST /api/smtp/:id/test` - Test SMTP connection
- `POST /api/smtp/bulk-import` - Bulk import SMTPs
- `POST /api/smtp/reset-failures` - Reset failure counts

### Campaigns
- `GET /api/campaigns` - List all campaigns
- `POST /api/campaigns` - Create campaign

### FROM Addresses
- `GET /api/from-addresses` - List FROM addresses
- `POST /api/from-addresses` - Create FROM address

### Templates
- `GET /api/templates` - List templates
- `POST /api/templates` - Create template

### Statistics
- `GET /api/stats/dashboard` - Get dashboard statistics

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | (required) |
| `JWT_SECRET_KEY` | JWT signing key | (required) |
| `DATABASE_URL` | PostgreSQL connection string | (required) |
| `REDIS_URL` | Redis connection string | (required) |
| `ENCRYPTION_KEY` | Password encryption key | (required) |
| `SMTP_FAILURE_THRESHOLD` | Failures before SMTP removal | 10 |
| `SMTP_SUCCESS_RESET_COUNT` | Successes to reduce failure count | 3 |
| `DEFAULT_RETRY_COUNT` | Email send retry attempts | 5 |
| `MAX_THREADS` | Maximum concurrent threads | 50 |
| `DEFAULT_THREADS` | Default thread count | 10 |
| `CORS_ORIGINS` | Allowed CORS origins | * |

## 🧪 Testing

```bash
pytest tests/
```

## 📦 Project Structure

```
ALL-in-One/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── requirements.txt       # Python dependencies
│   ├── models/                # Database models
│   │   ├── user.py
│   │   ├── smtp.py
│   │   ├── campaign.py
│   │   └── email.py
│   ├── api/                   # API endpoints
│   │   ├── auth.py
│   │   ├── smtp.py
│   │   ├── campaigns.py
│   │   ├── from_addresses.py
│   │   ├── templates.py
│   │   └── stats.py
│   ├── services/              # Business logic
│   ├── tasks/                 # Celery tasks
│   └── utils/                 # Utilities
│       └── encryption.py
├── render.yaml                # Render deployment config
├── PROJECT_PLAN.md            # Project plan
├── ARCHITECTURE.md            # Architecture documentation
└── README.md                  # This file
```

## 💰 Cost Estimate

### Free Tier (Limited)
- Web Service: Free (spins down after inactivity)
- Database: Free (limited storage)
- Redis: Free (25MB)
- **Total: $0/month**

### Starter Tier (Recommended)
- Web Service: $7/month
- Background Worker: $7/month
- PostgreSQL: $7/month
- Redis: Free or $10/month
- **Total: $21-31/month**

### Production Tier
- Web Service: $25/month (Standard)
- Background Worker: $25/month
- PostgreSQL: $7+/month
- Redis: $10+/month
- **Total: $67+/month**

## 🔒 Security

- All passwords encrypted at rest (AES-256)
- JWT authentication for API access
- HTTPS enforced on Render
- Rate limiting enabled
- CORS configured
- SQL injection prevention via ORM

## 📝 License

MIT License - see LICENSE file for details

## 👥 Support

For issues and questions:
- GitHub Issues: https://github.com/adamtheplanetarium/ALL-in-One/issues
- Email: support@example.com

## 🎯 Roadmap

- [ ] React frontend dashboard
- [ ] Advanced analytics
- [ ] Email scheduling
- [ ] A/B testing
- [ ] API rate limiting UI
- [ ] Webhook integrations

---

**Built with ❤️ for email marketing professionals**
