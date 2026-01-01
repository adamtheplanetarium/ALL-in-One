# ALL-in-One Email Portal

A comprehensive React-based web portal for managing email campaigns with background processing capabilities. This system provides a modern GUI interface for the Python-based email sending system with real-time monitoring via WebSocket.

## 🚀 Features

- **Password-Protected Access**: Secure login with `@OLDISGOLD2026@`
- **Real-Time Dashboard**: Live statistics and progress monitoring
- **SMTP Management**: Add, test, and manage multiple SMTP servers
- **Email List Management**: Upload and manage recipient and sender email lists
- **Template Editor**: Rich HTML email template editor with variable support
- **Campaign Control**: Start/stop campaigns with background processing
- **Live Logs**: Real-time log viewer with color-coded messages
- **Background Processing**: Campaigns run independently after closing browser
- **WebSocket Updates**: Live statistics and log streaming

## 📁 Project Structure

```
ALL-in-One/
├── frontend/           # React frontend
├── backend/            # Node.js/Express backend
├── Basic/              # Original Python scripts
├── templates/          # Email templates
├── logs/               # Campaign logs
└── render.yaml         # Render deployment config
```

## 🛠️ Tech Stack

### Frontend
- React 18
- Ant Design UI
- Socket.io-client
- React Quill (Rich text editor)
- Recharts
- Axios

### Backend
- Node.js & Express
- Socket.io
- PM2 (Process management)
- INI parser
- Express Session

### Python
- Original mainnotall.py (unchanged)
- SMTP, colorama, gdshortener

## 🔧 Installation

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- Git

### Local Development

1. **Clone the repository**:
```bash
git clone https://github.com/adamtheplanetarium/ALL-in-One.git
cd ALL-in-One
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Setup Backend**:
```bash
cd backend
npm install
cp .env.example .env
# Edit .env if needed
npm run dev
```

4. **Setup Frontend** (in new terminal):
```bash
cd frontend
npm install
npm start
```

5. **Access the portal**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Login password: `@OLDISGOLD2026@`

## 🌐 Deployment on Render

### Automatic Deployment

1. Push code to GitHub
2. Connect repository to Render
3. Render will automatically detect `render.yaml`
4. Configure environment variables in Render dashboard:
   - `CORS_ORIGIN`: Your frontend URL
   - `PASSWORD`: `@OLDISGOLD2026@`

### Manual Deployment

**Backend Service**:
- Build Command: `cd backend && npm install && cd .. && pip install -r requirements.txt`
- Start Command: `cd backend && npm start`
- Environment: Node

**Frontend Service**:
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `./frontend/build`
- Environment: Static Site

## 📖 Usage Guide

### 1. Login
- Navigate to the portal
- Enter password: `@OLDISGOLD2026@`

### 2. Configure SMTP Servers
- Go to "SMTP Servers"
- Add your SMTP credentials
- Test connection before using

### 3. Upload Email Lists
- Go to "Email Lists"
- Upload recipient emails (.txt or .csv)
- Upload from emails for rotation

### 4. Create Template
- Go to "Template"
- Design your HTML email
- Use variables: LINKREDIRECT, RANDOM, CapitalS, etc.
- Save template

### 5. Configure Campaign
- Go to "Campaign" or "Settings"
- Set subject line, sender name
- Configure threads and sleep time
- Enable/disable test mode

### 6. Start Campaign
- Go to "Dashboard"
- Click "Start Campaign"
- Monitor real-time progress
- View live logs
- **Close browser** - campaign continues!

### 7. Reconnect Anytime
- Open portal again
- Login
- View current campaign status
- Monitor progress

## 🔒 Security

- Password authentication required
- Session management
- HTTPS on production (Render)
- CORS protection
- Input validation

## 📊 Campaign Variables

Use these in templates and subjects:

- `LINKREDIRECT` - URL to be shortened
- `IMGREDIRECT` - Image URL
- `RANDOM` - Random 6-digit number
- `CapitalS` - Capitalized domain from SMTP
- `randomchar` - Random 5-digit number
- `DATEX` - Current date

## 🎯 Important Notes

- **Python script logic unchanged**: The `mainnotall.py` file maintains its original sending strategy
- **Background processing**: Uses PM2 to keep campaigns running
- **SMTP rotation**: Automatically rotates through servers
- **Failure handling**: Disables servers after 2 failures
- **Test mode**: Prevents email removal for testing

## 🐛 Troubleshooting

**Campaign won't start**:
- Check SMTP servers are added
- Verify recipient emails uploaded
- Ensure Python is installed
- Check backend logs

**WebSocket not connecting**:
- Verify backend is running
- Check CORS settings
- Ensure firewall allows WebSocket

**SMTP errors**:
- Test SMTP connection
- Verify credentials
- Check port and host
- Enable/disable TLS

## 📝 Future Features (Phase 2)

- Inbox testing system
- Active/Inactive from email categorization
- Advanced analytics
- Campaign scheduling
- API access
- Webhook notifications

## 👨‍💻 Development

```bash
# Backend development
cd backend
npm run dev

# Frontend development
cd frontend
npm start

# Run with PM2
cd backend
npm run pm2:start
npm run pm2:logs
```

## 📄 License

MIT License

## 🤝 Support

For issues and questions, open a GitHub issue.

---

**Made with ❤️ for email campaign management**
