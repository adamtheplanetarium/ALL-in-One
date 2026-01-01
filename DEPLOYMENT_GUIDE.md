# Deployment Guide - Render.com

## 🚀 Quick Deploy to Render

### Prerequisites
- GitHub account with repository access
- Render.com account (free tier works)

### Step 1: Connect Repository

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account if not already connected
4. Select the `ALL-in-One` repository
5. Render will automatically detect the `render.yaml` file

### Step 2: Configure Environment Variables

The `render.yaml` has most settings, but you need to configure:

#### For Backend Service:
- `CORS_ORIGIN`: Set to your frontend URL (will be provided after frontend deploys)
- `PASSWORD`: Already set to `@OLDISGOLD2026@`
- Other variables are auto-configured

### Step 3: Deploy

1. Click **"Apply"** to deploy both services
2. Wait 5-10 minutes for:
   - Backend: Node.js + Python dependencies installation
   - Frontend: React build process

### Step 4: Update CORS

After both services deploy:

1. Copy your frontend URL (e.g., `https://email-portal-frontend.onrender.com`)
2. Go to backend service settings
3. Update `CORS_ORIGIN` environment variable with frontend URL
4. Backend will auto-restart

### Step 5: Access Portal

1. Visit your frontend URL
2. Login with password: `@OLDISGOLD2026@`
3. Start configuring your campaign!

## 📋 Manual Deployment (Alternative)

### Backend Service

**Service Type**: Web Service  
**Environment**: Node  
**Region**: Oregon (or closest to you)  

**Build Command**:
```bash
cd backend && npm install && cd .. && pip install -r requirements.txt
```

**Start Command**:
```bash
cd backend && npm start
```

**Environment Variables**:
```
NODE_ENV=production
PORT=10000
PASSWORD=@OLDISGOLD2026@
SESSION_SECRET=<auto-generate>
PYTHON_PATH=python3
BASIC_FOLDER_PATH=../Basic
CORS_ORIGIN=<your-frontend-url>
```

**Health Check Path**: `/api/health`

### Frontend Service

**Service Type**: Static Site  
**Environment**: Static  
**Region**: Oregon (or closest to you)  

**Build Command**:
```bash
cd frontend && npm install && npm run build
```

**Publish Directory**: `./frontend/build`

**Redirects/Rewrites**:
```
/* → /index.html (SPA)
```

## 🔧 Post-Deployment Configuration

### 1. Test Backend API

Visit: `https://your-backend-url.onrender.com/api/health`

Should return:
```json
{
  "status": "ok",
  "timestamp": "...",
  "uptime": 123.456
}
```

### 2. Test Frontend

Visit: `https://your-frontend-url.onrender.com`

You should see the login page.

### 3. Configure SMTP Servers

1. Login to portal
2. Go to "SMTP Servers"
3. Add your SMTP credentials from `smtp.txt`
4. Test each server connection

### 4. Upload Email Lists

1. Go to "Email Lists"
2. Upload recipient emails
3. Upload from emails for rotation

### 5. Create Template

1. Go to "Template"
2. Create or upload your HTML email template
3. Use variables: LINKREDIRECT, RANDOM, CapitalS, etc.

### 6. Configure Campaign Settings

1. Go to "Settings"
2. Set subject line, sender name
3. Configure threads (3-5 recommended)
4. Set sleep time (1-2 seconds)
5. **Disable test mode** for production

## 🐛 Troubleshooting

### Backend Won't Start

**Error**: `Python not found`
- Solution: Check Python installation in build logs
- Alternative: Use `python3` instead of `python` in env vars

**Error**: `Cannot find module`
- Solution: Check all dependencies in package.json
- Run: Clear build cache and redeploy

### Frontend Shows 404

**Error**: React Router not working
- Solution: Add SPA redirect rule: `/* → /index.html`

### CORS Errors

**Error**: `Access-Control-Allow-Origin`
- Solution: Update backend `CORS_ORIGIN` to match exact frontend URL
- Include protocol (https://) in the URL

### WebSocket Not Connecting

**Error**: WebSocket connection failed
- Solution: Ensure backend URL is correct in frontend `.env`
- Check: Both services are running
- Verify: No firewall blocking WebSocket

### Campaign Won't Start

**Error**: Campaign fails to start
- Check: Python dependencies installed (`requirements.txt`)
- Check: `mainnotall.py` file exists in `Basic/` folder
- Check: SMTP servers configured
- Check: Recipient emails uploaded

### SMTP Authentication Fails

**Error**: SMTP auth error
- Solution: Verify credentials in SMTP list
- Test: Use "Test" button on each server
- Check: Port and host are correct
- Verify: TLS/SSL settings

## 📊 Monitoring

### View Logs

**Backend Logs**:
- Go to backend service in Render dashboard
- Click "Logs" tab
- View real-time output

**Frontend Logs**:
- Frontend is static, check browser console
- Use browser DevTools → Console tab

### Check Service Health

Monitor these endpoints:
- Backend: `/api/health`
- Frontend: Main page should load

### Campaign Monitoring

Use the portal's built-in monitoring:
- Dashboard: Real-time statistics
- Logs tab: Live campaign output
- SMTP page: Server status

## 🔄 Updates and Redeployment

### Auto-Deploy (Recommended)

Render auto-deploys on git push:

```bash
git add .
git commit -m "your changes"
git push origin main
```

Render will automatically:
1. Pull latest code
2. Rebuild services
3. Deploy updates
4. Zero-downtime rollout

### Manual Deploy

1. Go to Render dashboard
2. Select service
3. Click "Manual Deploy"
4. Choose branch
5. Click "Deploy"

## 🔒 Security Best Practices

### Production Checklist

- [ ] Change default password from `@OLDISGOLD2026@`
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS (automatic on Render)
- [ ] Set strong SESSION_SECRET
- [ ] Disable DEBUG mode
- [ ] Restrict CORS to your domain only
- [ ] Regular password rotation
- [ ] Monitor access logs

### Environment Variables

**Never commit**:
- `.env` files
- Passwords or API keys
- Session secrets

**Always use**:
- Render environment variables
- Secrets management
- Encrypted credentials

## 📈 Scaling on Render

### Free Tier Limitations

- Backend: Sleeps after 15 min inactivity
- Backend: 750 hours/month
- Shared CPU/RAM

### Upgrade Benefits

**Starter ($7/month)**:
- No sleep mode
- Better performance
- Custom domains

**Pro ($25/month)**:
- Dedicated resources
- Better uptime
- Auto-scaling

### Performance Tips

1. **Use PM2**: Already configured in `ecosystem.config.js`
2. **Optimize threads**: Start with 3, increase carefully
3. **Monitor memory**: Check Render dashboard
4. **Sleep time**: 1-2 seconds recommended
5. **Connection pooling**: Handled automatically

## 🎯 Success Checklist

After deployment:

- [ ] Backend health check returns OK
- [ ] Frontend loads without errors
- [ ] Login works with password
- [ ] SMTP servers added and tested
- [ ] Email lists uploaded
- [ ] Template created/uploaded
- [ ] Settings configured
- [ ] Test campaign runs successfully
- [ ] Real-time logs working
- [ ] WebSocket connected (green indicator)
- [ ] Campaign runs in background
- [ ] Can reconnect after closing browser

## 🆘 Support Resources

- **Render Docs**: https://render.com/docs
- **GitHub Issues**: Open issue in your repository
- **Render Community**: https://community.render.com

---

**🎉 Congratulations! Your Email Portal is now live on Render!**
