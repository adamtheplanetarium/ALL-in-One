# ALL-in-One Email Portal

A powerful Python Flask-based web application for managing and running email campaigns with real-time monitoring.

## Features

- 🔐 **Secure Login** - Password-protected access (@OLDISGOLD2026@)
- 📊 **Live Dashboard** - Real-time campaign statistics and monitoring
- 📧 **SMTP Management** - Configure multiple SMTP servers with rotation
- 👥 **Email List Management** - Manage recipient email addresses
- 📝 **Template Editor** - Configure email templates and sender addresses
- ⚙️ **Campaign Settings** - Adjust threading, delays, and other parameters
- 🔄 **Background Processing** - Run campaigns in the background for days
- 📡 **Real-time WebSocket Updates** - Live logs and statistics via Socket.IO

## Technology Stack

- **Backend**: Python 3.11 + Flask
- **Real-time Communication**: Flask-SocketIO
- **Frontend**: HTML5 + Bootstrap 5 + Vanilla JavaScript
- **Deployment**: Gunicorn + Eventlet (Production-ready)

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/adamtheplanetarium/ALL-in-One.git
   cd ALL-in-One
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the portal**
   Open your browser to `http://localhost:10000`
   Login with password: `@OLDISGOLD2026@`

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml` and configure everything

3. **Access your deployed app**
   - Your app will be available at: `https://your-app-name.onrender.com`

## Project Structure

```
ALL-in-One/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── .env                  # Environment variables (local)
├── Basic/                # Original email campaign scripts
│   ├── mainnotall.py    # Main campaign script (UNCHANGED)
│   ├── config.ini       # Campaign configuration
│   ├── smtp.txt         # SMTP server list
│   └── emailx.txt       # Recipient email list
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── login.html       # Login page
│   ├── dashboard.html   # Main dashboard
│   ├── smtp.html        # SMTP management
│   ├── emails.html      # Email list management
│   ├── template.html    # Template editor
│   └── campaign.html    # Campaign settings
└── static/              # Static assets
    ├── css/
    │   └── style.css    # Custom styles
    └── js/
        └── main.js      # JavaScript utilities
```

## Usage

### 1. Configure SMTP Servers
- Navigate to "SMTP" page
- Add your SMTP server details (host, port, username, password)
- Save configuration

### 2. Upload Email Lists
- Go to "Email Lists" page
- Paste email addresses (one per line)
- Save the list

### 3. Configure Campaign Settings
- Visit "Campaign" page
- Set domain, sleep time, threads, etc.
- Save configuration

### 4. Start Campaign
- Open "Dashboard"
- Click "Start Campaign"
- Monitor real-time logs and statistics
- Campaign runs in background even if you close the browser

### 5. Stop Campaign
- Click "Stop Campaign" button anytime
- View final statistics

## Environment Variables

- `SECRET_KEY`: Flask secret key for sessions
- `PASSWORD`: Login password (default: @OLDISGOLD2026@)
- `PORT`: Application port (default: 10000)

## Features in Detail

### Real-time Monitoring
- Live campaign statistics (sent, failed, status)
- Real-time log streaming via WebSocket
- Uptime tracking

### SMTP Rotation
- Automatic SMTP server rotation
- Failed server tracking and disabling
- Working SMTP server preservation

### Background Processing
- Campaigns run independently in background
- Process continues even after closing browser
- Multi-threaded email sending

## Security

- Session-based authentication
- Password-protected access
- Secure environment variable handling
- Session timeout after 24 hours

## Original Script

The `Basic/mainnotall.py` script remains **UNCHANGED** and includes all original features:
- Multi-threaded email sending
- SMTP server rotation
- DKIM signing support
- GD URL shortening
- Colorful console output
- Failed server tracking

## Support

For issues or questions:
- GitHub: [@adamtheplanetarium](https://github.com/adamtheplanetarium)
- Telegram: @voxebk

## License

Private project - All rights reserved

---

**Built with ❤️ using Python Flask**
