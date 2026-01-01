# SMTP Validator

**Test & Verify SMTP Delivery** - A professional tool to test SMTP servers and verify which ones successfully deliver emails using IMAP verification.

## 🎯 Purpose

Send test messages from each SMTP server, then verify via IMAP which messages were actually delivered. Extract only the working SMTP servers.

## ✨ Features

- ✅ **Batch Testing** - Send test messages from multiple SMTP servers simultaneously
- ✅ **IMAP Verification** - Connect to recipient inbox and verify delivered messages
- ✅ **Tracking System** - Unique tracking IDs match sent messages to delivered ones
- ✅ **Multi-folder Check** - Checks INBOX, Junk, Spam folders
- ✅ **Export Results** - Export verified SMTPs, failed SMTPs, or full CSV report
- ✅ **Thread-safe** - Parallel operations with configurable thread count
- ✅ **No Dependencies** - Pure Python stdlib (no pip install required)
- ✅ **Professional GUI** - Easy-to-use tkinter interface

## 📋 Requirements

- **Python 3.7+** (no external packages needed)
- **SMTP servers** in format: `host:port:username:password`
- **IMAP access** to recipient email account

## 🚀 Quick Start

### 1. Prepare Files

Create `smtps.txt` with your SMTP servers:
```
mail.example.com:587:user@example.com:password123
smtp.gmail.com:587:yourname@gmail.com:app_password
```

Create `recipients.txt` with test recipient emails:
```
testbox@gmail.com
verify@outlook.com
```

### 2. Run Application

```bash
python main.py
```

### 3. Send Test Messages

1. Go to **📤 SMTP Sending** tab
2. Click **Load SMTPs** and select `smtps.txt`
3. Click **Load Recipients** and select `recipients.txt`
4. Adjust thread count (default: 10)
5. Click **▶ Start Sending**

Messages are sent with unique tracking IDs like:
```
Subject: SMTP Test TRK-20240115143025123
```

### 4. Verify Delivery

1. Go to **📬 IMAP Verification** tab
2. Enter IMAP settings:
   - **Host**: `imap.gmail.com` (or your IMAP server)
   - **Port**: `993` (SSL) or `143` (non-SSL)
   - **Username**: `testbox@gmail.com`
   - **Password**: Your email password or app password
3. Click **💾 Save Settings**
4. Click **🔌 Test Connection** to verify IMAP works
5. Click **▶ Start Verification**

The tool will:
- Connect to IMAP server
- Search INBOX and Junk folders
- Extract tracking IDs from messages
- Match tracking IDs to sent messages
- Register which SMTPs successfully delivered

### 5. View Results

Go to **📊 Results** tab to see:
- **Summary Statistics**: Total sent, delivered, inbox rate, junk rate
- **Detailed Table**: Each SMTP's delivery status
- **Export Options**:
  - **Export Verified SMTPs** - Save working SMTPs to `data/verified_smtps.txt`
  - **Export Failed SMTPs** - Save non-working SMTPs to `data/failed_smtps.txt`
  - **Export CSV Report** - Detailed report with all statistics

## 📁 File Formats

### SMTP File (`smtps.txt`)
```
host:port:username:password
mail.example.com:587:user@example.com:pass123
smtp.gmail.com:587:name@gmail.com:app_password
```

### Recipients File (`recipients.txt`)
```
recipient1@gmail.com
recipient2@outlook.com
```

### Verified SMTPs Output
```
mail.example.com:587:user@example.com:pass123
smtp.another.com:25:sender@another.com:secret
```

## ⚙️ Configuration

Go to **⚙️ Settings** tab to adjust:

- **SMTP Timeout** (default: 30 seconds)
- **Retry Attempts** (default: 3)
- **Thread Count** (default: 10)

Settings are saved in `config.json`.

## 🔒 Gmail Setup

For Gmail IMAP verification:

1. **Enable IMAP** in Gmail settings:
   - Settings → Forwarding and POP/IMAP → Enable IMAP

2. **Create App Password** (if 2FA enabled):
   - Google Account → Security → 2-Step Verification → App passwords
   - Select "Mail" and "Other" → Copy password

3. **IMAP Settings**:
   - Host: `imap.gmail.com`
   - Port: `993`
   - Username: `your.email@gmail.com`
   - Password: Your app password (not regular password)

## 📊 Tracking System

Each sent message includes a unique tracking ID:

**Format**: `TRK-YYYYMMDDHHMMSSMMM`

**Example**: `TRK-20240115143025123`

This ID is embedded in:
- Email subject: `SMTP Test TRK-20240115143025123`
- Email body: `Tracking ID: TRK-20240115143025123`

When verifying via IMAP, the tool extracts these IDs and matches them to sent messages.

## 🗂️ Project Structure

```
SMTP-Validator/
├── main.py              # GUI application (590 lines)
├── config_handler.py    # Configuration management (280 lines)
├── file_handler.py      # File I/O operations (290 lines)
├── tracker.py           # Message tracking (390 lines)
├── smtp_sender.py       # SMTP sending logic (380 lines)
├── imap_checker.py      # IMAP verification (390 lines)
├── config.json          # Settings file (auto-generated)
├── data/                # Data folder
│   ├── smtps.txt        # SMTP servers
│   ├── recipients.txt   # Test recipients
│   ├── verified_smtps.txt
│   └── failed_smtps.txt
└── logs/                # Log folder
    ├── sent_log.json    # Sent messages log
    └── app.log          # Application log
```

## 🛠️ Troubleshooting

### "SMTP Authentication Failed"
- Verify SMTP username/password are correct
- Check if SMTP requires app password (Gmail, Outlook)
- Ensure SMTP port is correct (587 for STARTTLS, 465 for SSL)

### "IMAP Connection Failed"
- Verify IMAP is enabled in email settings
- Check firewall isn't blocking port 993/143
- Try with SSL enabled (port 993)
- For Gmail, use app password instead of account password

### "No Messages Found"
- Wait a few minutes for delivery
- Check if messages went to Spam/Junk
- Verify IMAP folders (some providers use different names)
- Check date range (default: 1 day back)

### "Tracking ID Not Found"
- Verify messages have tracking ID in subject
- Check email wasn't modified in transit
- Ensure IMAP search is working correctly

## 📈 Statistics Explained

- **Total Sent**: Number of messages sent from all SMTPs
- **Total Delivered**: Messages found in recipient inbox/junk
- **Not Delivered**: Messages not found (SMTP or network issue)
- **Delivery Rate**: Percentage of messages delivered
- **Inbox Rate**: Percentage delivered to INBOX
- **Junk Rate**: Percentage delivered to Junk/Spam

## 🔧 Advanced Usage

### Custom Message Template

Edit `config.json`:

```json
{
  "message": {
    "subject": "Custom Subject {tracking_id}",
    "body": "Custom body\nTracking: {tracking_id}\n\nYour content here"
  }
}
```

`{tracking_id}` is automatically replaced with unique ID.

### Multiple IMAP Folders

Edit [imap_checker.py](imap_checker.py#L200) to add custom folders:

```python
folders_to_check = ['INBOX', 'Junk', 'Spam', 'Custom Folder']
```

### Retry Logic

SMTP sending retries 3 times on connection errors (not authentication errors).

Edit [smtp_sender.py](smtp_sender.py#L50) to change retry count:

```python
max_retries = 3  # Change this value
```

## 📝 Logs

All operations are logged:

- **Sent Messages**: `logs/sent_log.json`
- **Application Log**: Console output in GUI

Sent log includes:
- Tracking ID
- SMTP server used
- Recipient
- Timestamp
- Status (success/failure)

## 🔐 Security Notes

- Configuration file stores IMAP password in plain text
- Keep `config.json` secure (don't share)
- Use app passwords instead of account passwords
- Clear results after use if needed

## 💡 Tips

1. **Start Small** - Test with 2-3 SMTPs first
2. **Use App Passwords** - More reliable than regular passwords
3. **Wait Before Verifying** - Allow 2-5 minutes for email delivery
4. **Check Multiple Folders** - Messages might go to Junk
5. **Export Results** - Save verified SMTPs for later use

## 🐛 Known Issues

- Gmail may rate-limit IMAP searches (wait between verifications)
- Some SMTP servers require specific auth methods (not supported)
- Very large SMTP lists (1000+) may take significant time

## 📜 License

Free to use and modify. No warranty provided.

## 🤝 Support

For issues or questions, check:
1. **Logs** in GUI
2. **Troubleshooting** section above
3. **SMTP/IMAP server documentation**

---

**Version**: 1.0  
**Python**: 3.7+  
**Dependencies**: None (stdlib only)
