# ALL-in-One Email Portal - Project Plan

## 🎯 Project Overview
A React-based web GUI for the email mass-sending system with background processing capabilities, deployable on Render.

## 🔐 Authentication
- **Login Password**: `@OLDISGOLD2026@`
- Simple authentication middleware
- Session management for security

## 🏗️ Architecture

### Frontend (React)
- **Technology Stack**:
  - React 18+ with Hooks
  - Material-UI / Ant Design for UI components
  - Axios for API calls
  - React Router for navigation
  - Socket.io-client for real-time updates

### Backend (Node.js + Express)
- **Technology Stack**:
  - Node.js with Express
  - Socket.io for real-time communication
  - Child Process for Python script execution
  - File System for data management
  - PM2 for process management (background execution)

### Python Integration
- Keep existing `mainnotall.py` logic **UNCHANGED**
- Execute via Node.js child process
- Monitor and control from web interface

## 📋 Core Features

### 1. **Dashboard**
- Real-time statistics:
  - Total emails sent
  - Success rate
  - Failed attempts
  - Active SMTP servers
  - Emails remaining
- Live progress bar
- Current sending status
- System health indicators

### 2. **SMTP Management**
- **Active SMTP Servers Table**:
  - Host, Port, Username
  - Status (Active/Disabled)
  - Success/Failure count
  - Last used timestamp
  - Actions: Test, Enable/Disable, Delete
  
- **Inactive SMTP Servers**:
  - Servers disabled after 2 failures
  - Option to re-enable manually
  - Failure reason display

- **Add New SMTP**:
  - Form to add new SMTP credentials
  - Validation and testing before adding
  - Bulk import from CSV

### 3. **Email List Management**
- **Recipient Emails** (`emailx.txt`):
  - Upload new list (CSV/TXT)
  - View total count
  - Clear list
  - Download remaining emails
  
- **From Emails** (`from.txt`):
  - Upload sender email list
  - Rotation indicator
  - View current rotation index

### 4. **From Email Analysis** (Future Implementation)
- **Inbox Testing Section**:
  - Test "From" emails to check inbox delivery
  - Categorize as "Active" (goes to inbox) or "Inactive" (spam/blocked)
  - Display lists of:
    - ✅ Active Froms (verified inbox delivery)
    - ❌ Inactive Froms (spam/blocked)
  - Export active/inactive lists

### 5. **Message Template Editor**
- Rich text editor for HTML email templates
- Variable support:
  - `LINKREDIRECT` - Link to be shortened
  - `IMGREDIRECT` - Image link to be shortened
  - `RANDOM` - Random number
  - `CapitalS` - Capitalized domain
  - `randomchar` - Random characters
  - `DATEX` - Current date
- Preview mode
- Save/Load templates
- File upload for existing HTML

### 6. **Campaign Configuration**
- **Subject Line**:
  - Text input with variable support
  - Preview with variables replaced
  
- **Sender Name**:
  - Customizable sender name
  - Variable support (CapitalS, randomchar)
  
- **Settings**:
  - Threads (1-10)
  - Sleep time between emails
  - Importance flag (High priority)
  - Test mode toggle
  - Debug mode toggle

### 7. **Campaign Control**
- **Start Campaign**:
  - Validation before starting
  - Confirmation modal
  - Background process initiation
  
- **Stop Campaign**:
  - Graceful shutdown
  - Save progress
  
- **Pause/Resume**:
  - Temporary pause
  - Resume from last position

### 8. **Real-Time Logs**
- Live log viewer with:
  - Success messages (green)
  - Error messages (red)
  - Info messages (blue)
  - Timestamps
  - Filterable by type
  - Auto-scroll option
  - Export logs

### 9. **Background Processing**
- Campaign runs independently of browser
- Can close portal while campaign continues
- Reconnect to view live status
- Multi-day execution support
- Auto-restart on failure
- Process monitoring

## 📁 Project Structure

```
ALL-in-One/
├── frontend/                    # React Frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth/
│   │   │   │   └── Login.jsx
│   │   │   ├── Dashboard/
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── Statistics.jsx
│   │   │   │   └── ProgressBar.jsx
│   │   │   ├── SMTP/
│   │   │   │   ├── SMTPList.jsx
│   │   │   │   ├── SMTPForm.jsx
│   │   │   │   └── SMTPStatus.jsx
│   │   │   ├── EmailLists/
│   │   │   │   ├── RecipientList.jsx
│   │   │   │   ├── FromList.jsx
│   │   │   │   └── FileUpload.jsx
│   │   │   ├── Template/
│   │   │   │   ├── TemplateEditor.jsx
│   │   │   │   └── TemplatePreview.jsx
│   │   │   ├── Campaign/
│   │   │   │   ├── CampaignConfig.jsx
│   │   │   │   └── CampaignControl.jsx
│   │   │   ├── Logs/
│   │   │   │   └── LogViewer.jsx
│   │   │   └── Layout/
│   │   │       ├── Navbar.jsx
│   │   │       └── Sidebar.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── socket.js
│   │   ├── context/
│   │   │   └── AppContext.jsx
│   │   ├── utils/
│   │   │   └── helpers.js
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── .env
│
├── backend/                     # Node.js Backend
│   ├── src/
│   │   ├── controllers/
│   │   │   ├── authController.js
│   │   │   ├── smtpController.js
│   │   │   ├── emailController.js
│   │   │   ├── campaignController.js
│   │   │   └── templateController.js
│   │   ├── services/
│   │   │   ├── pythonService.js    # Execute mainnotall.py
│   │   │   ├── fileService.js      # Read/Write files
│   │   │   └── processManager.js   # Background process management
│   │   ├── middleware/
│   │   │   ├── auth.js
│   │   │   └── errorHandler.js
│   │   ├── routes/
│   │   │   ├── auth.js
│   │   │   ├── smtp.js
│   │   │   ├── emails.js
│   │   │   ├── campaign.js
│   │   │   └── template.js
│   │   ├── sockets/
│   │   │   └── campaignSocket.js   # Real-time updates
│   │   ├── config/
│   │   │   └── constants.js
│   │   └── server.js
│   ├── package.json
│   ├── ecosystem.config.js         # PM2 config
│   └── .env
│
├── Basic/                          # Existing Python files
│   ├── mainnotall.py              # UNCHANGED - original logic
│   ├── config.ini
│   ├── smtp.txt
│   ├── working_smtp.txt
│   ├── emailx.txt
│   └── from.txt
│
├── templates/                      # Email templates
│   └── default.html
│
├── logs/                          # Campaign logs
│   └── campaign.log
│
├── .gitignore
├── README.md
└── PROJECT_PLAN.md
```

## 🔄 Workflow

### Normal Operation Flow:
1. User logs in with password
2. Configure SMTP servers (or use existing)
3. Upload recipient emails and from emails
4. Create/edit email template
5. Configure campaign settings
6. Start campaign
7. Monitor real-time progress
8. **Close browser** - campaign continues in background
9. Reopen portal anytime to check status
10. Campaign completes or stop manually

### Background Processing:
- Backend uses PM2 to keep processes alive
- Python script runs as child process
- WebSocket maintains state even after reconnect
- Progress saved to file system
- Logs stored for history

## 🚀 Deployment on Render

### Requirements:
1. **Web Service** (for backend):
   - Node.js environment
   - PM2 for process management
   - Python 3.x installed
   - Environment variables configured

2. **Static Site** (for frontend):
   - Build React app
   - Serve static files
   - Configure API endpoint

### Render Configuration:
```yaml
services:
  - type: web
    name: email-portal-backend
    env: node
    buildCommand: cd backend && npm install && pip install -r requirements.txt
    startCommand: cd backend && npm start
    envVars:
      - key: PORT
        value: 10000
      - key: PASSWORD
        value: @OLDISGOLD2026@
      - key: NODE_ENV
        value: production

  - type: web
    name: email-portal-frontend
    env: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: ./frontend/build
```

## 📦 Dependencies

### Frontend:
```json
{
  "react": "^18.2.0",
  "react-router-dom": "^6.20.0",
  "axios": "^1.6.0",
  "socket.io-client": "^4.6.0",
  "antd": "^5.12.0",
  "@ant-design/icons": "^5.2.6",
  "react-quill": "^2.0.0",
  "recharts": "^2.10.0"
}
```

### Backend:
```json
{
  "express": "^4.18.2",
  "socket.io": "^4.6.0",
  "cors": "^2.8.5",
  "dotenv": "^16.3.1",
  "express-session": "^1.17.3",
  "multer": "^1.4.5-lts.1",
  "ini": "^4.1.1",
  "pm2": "^5.3.0"
}
```

### Python (requirements.txt):
```
colorama
pyfiglet
gdshortener
dkim
```

## 🔒 Security Considerations
- Password-protected access
- Session management
- HTTPS on Render
- Environment variables for sensitive data
- Input validation
- File upload restrictions

## ⚙️ Configuration Management
- All settings stored in `config.ini`
- Web UI updates config file
- Python script reads from config.ini
- No changes to Python logic

## 📊 Real-Time Updates via WebSocket

### Events:
- `campaign:started` - Campaign begins
- `campaign:progress` - Email sent update
- `campaign:stopped` - Campaign ends
- `smtp:disabled` - SMTP server disabled
- `log:new` - New log entry
- `stats:update` - Statistics update

## 🎨 UI/UX Design
- Modern, clean interface
- Responsive design (desktop-first)
- Dark/Light theme support
- Intuitive navigation
- Real-time feedback
- Loading states
- Error handling with notifications

## 🧪 Testing Strategy
- Test mode to prevent actual sending
- SMTP connection testing
- Email validation
- Template variable validation
- File format validation

## 📈 Future Enhancements (Phase 2)
- **Inbox Testing System**:
  - Send test emails to check inbox delivery
  - Categorize "From" emails as Active/Inactive
  - Machine learning for spam detection patterns
  - Auto-remove inactive froms
  
- **Analytics Dashboard**:
  - Delivery rates over time
  - Best performing SMTP servers
  - Optimal sending times
  
- **Scheduling**:
  - Schedule campaigns for specific times
  - Recurring campaigns
  
- **API Access**:
  - RESTful API for integration
  - Webhook notifications

## 🛠️ Development Timeline

### Phase 1 (Core Features):
1. **Day 1-2**: Backend setup + Authentication
2. **Day 3-4**: Frontend structure + Dashboard
3. **Day 5-6**: SMTP Management + Email Lists
4. **Day 7-8**: Template Editor + Campaign Config
5. **Day 9-10**: Campaign Control + Background Processing
6. **Day 11-12**: Real-time Logs + WebSocket
7. **Day 13-14**: Testing + Bug fixes
8. **Day 15**: Deployment on Render

### Phase 2 (Future Features):
- Inbox testing system
- Advanced analytics
- Additional features as needed

## 📝 Notes
- **DO NOT** modify `mainnotall.py` logic
- Maintain the existing trick/strategy for email rotation
- All Python dependencies must be installed on Render
- Use PM2 ecosystem config for production
- Keep frontend files small and modular
- Git push after each major milestone

## 🎯 Success Criteria
✅ Web portal accessible with password  
✅ All features from Python script available in GUI  
✅ Campaign runs in background after closing browser  
✅ Can run for days without stopping  
✅ Real-time monitoring works correctly  
✅ SMTP rotation and failure handling works  
✅ Successfully deployed on Render  
✅ No changes to mainnotall.py sending logic  

---

**Ready to start implementation!** 🚀
