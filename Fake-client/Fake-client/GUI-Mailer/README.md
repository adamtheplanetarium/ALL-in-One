# 📧 Email Sender Pro - GUI Edition

A professional GUI application for bulk email sending with advanced SMTP management.

## ✨ Features

- **🎨 Modern GUI Interface** - Easy-to-use tabbed interface
- **📧 SMTP Server Management** - Load, edit, and rotate SMTP servers
- **👥 Recipient Management** - Import and manage email lists
- **📝 HTML Template Editor** - Create custom email templates with placeholders
- **⚙️ Full Configuration Control** - All mainnotall.py options available in GUI
- **🔒 Thread-Safe SMTP Rotation** - Preserved original lock mechanism
- **📊 Real-time Statistics** - Live progress tracking and logs
- **🎯 Smart Server Disabling** - Automatically disables failing SMTP servers
- **💾 File Operations** - Load/save all data from files

## 🚀 Quick Start

### Installation

1. Install Python 3.7 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python gui_mailer.py
```

Or use the batch file:
```bash
START.bat
```

## 📖 Usage Guide

### Tab 1: Configuration ⚙️

Configure all email sending parameters:

- **Domain From**: Base domain for email sender
- **Domain Authentication**: Authentication domain
- **Sender Name**: Display name (supports `CapitalS`, `randomchar`)
- **Subject**: Email subject line (supports `CapitalS`, `randomchar`, `DATEX`)
- **Link Redirect URL**: URL for link shortening
- **Threads**: Number of concurrent sending threads (1-50)
- **Sleep Time**: Delay between emails (seconds)
- **Test Mode**: Enable to prevent removing sent emails from list
- **Debug Mode**: Enable SMTP debug output
- **Mark as Important**: Add high priority headers
- **Use URL Shortener**: Shorten URLs with is.gd

### Tab 2: SMTP Servers 📧

Manage your SMTP servers:

**Format**: `host,port,username,password` (one per line)

**Example**:
```
smtp.gmail.com,587,user@gmail.com,password123
mail.example.com,587,info@example.com,mypass456
```

**Features**:
- 📁 Load from file (smtp.txt)
- 💾 Save to file
- ✅ Parse & Validate (checks format)
- 🗑️ Clear all

### Tab 3: Recipients 📋

Manage recipient email addresses:

**Format**: One email per line

**Example**:
```
recipient1@example.com
recipient2@example.com
recipient3@example.com
```

**Features**:
- 📁 Load from file (emailx.txt)
- 💾 Save to file
- ✅ Parse & Validate (checks for @)
- 🗑️ Clear all

### Tab 4: From Addresses 👤

Manage "From" email addresses (rotates through list):

**Format**: One email per line

**Example**:
```
sender1@domain.com
sender2@domain.com
sender3@domain.com
```

### Tab 5: Email Template 📝

Edit your HTML email template:

**Available Placeholders**:
- `LINKREDIRECT` - Replaced with shortened URL
- `IMGREDIRECT` - Replaced with image redirect URL
- `RANDOM` - Replaced with random 6-digit number

**Example Template**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Email</title>
</head>
<body>
    <h1>Hello!</h1>
    <p>Click <a href="LINKREDIRECT">here</a></p>
    <p>Ref: RANDOM</p>
</body>
</html>
```

### Tab 6: Send Control 🚀

Control the sending process:

**Status Display**:
- Current status (Ready/Sending/Completed)
- Progress counter (X / Total)
- Progress bar
- Real-time statistics

**Controls**:
- 🚀 **START SENDING** - Begin campaign
- ⏹️ **STOP** - Stop after current operations

**Statistics Box**:
- SMTP Servers Loaded
- Recipients Loaded
- From Addresses Loaded
- Emails Sent
- Successfully Sent
- Failed Servers

### Tab 7: Logs & Statistics 📊

View real-time activity logs:

**Color Coding**:
- 🟢 Green - Success messages
- 🔴 Red - Error messages
- 🟠 Orange - Warning messages
- 🔵 Blue - Info messages

**Features**:
- 🗑️ Clear Logs
- 💾 Save Logs to file

## 🔧 Configuration Options Explained

### Sender Name Replacements

- **CapitalS** - Replaced with capitalized domain name
  - Example: `CapitalS Support` → `Gmail Support` (if SMTP is gmail.com)
- **randomchar** - Replaced with random 5-digit number
  - Example: `Support randomchar` → `Support 12345`

### Subject Replacements

- **CapitalS** - Replaced with capitalized domain name
- **randomchar** - Replaced with random 5-digit number
- **DATEX** - Replaced with current date (e.g., "Thursday, December 19, 2025")

**Example**:
```
Subject: Important update from CapitalS #randomchar
Result: Important update from Gmail #45678
```

## ⚙️ SMTP Lock Mechanism (Preserved)

The application uses the **exact same thread-safe SMTP rotation logic** from mainnotall.py:

- ✅ Thread-safe server selection with locks
- ✅ Automatic server rotation
- ✅ Failed server tracking (disables after 2 failures)
- ✅ Prevents all servers from being disabled simultaneously
- ✅ No modifications to core locking logic

## 🔒 Security Notes

- Never commit files containing SMTP credentials
- Use app-specific passwords for Gmail/Yahoo
- Test with small batches first (Test Mode enabled)
- Keep SMTP credentials secure

## 📝 Test Mode vs Production Mode

**Test Mode (Enabled)**:
- ✅ Emails are sent
- ✅ Progress is tracked
- ❌ Recipients NOT removed from list after sending
- Use for testing campaigns

**Production Mode (Disabled)**:
- ✅ Emails are sent
- ✅ Progress is tracked
- ✅ Successfully sent recipients removed from list
- Use for live campaigns

## 🎯 Workflow Example

1. **Load Configuration**
   - Go to Configuration tab
   - Set your sending parameters
   - Configure threads and sleep time

2. **Load SMTP Servers**
   - Go to SMTP Servers tab
   - Click "Load from File" or paste servers
   - Click "Parse & Validate"

3. **Load Recipients**
   - Go to Recipients tab
   - Click "Load from File" or paste emails
   - Click "Parse & Validate"

4. **Load From Addresses**
   - Go to From Addresses tab
   - Click "Load from File" or paste emails
   - Click "Parse & Validate"

5. **Edit Template**
   - Go to Email Template tab
   - Load or paste your HTML template
   - Use placeholders (LINKREDIRECT, RANDOM, etc.)

6. **Start Sending**
   - Go to Send Control tab
   - Review statistics
   - Click "START SENDING"
   - Monitor progress in Logs tab

7. **Monitor Progress**
   - Watch real-time logs in Logs & Statistics tab
   - Check progress bar and counter
   - View server failure statistics

## 🆘 Troubleshooting

### "All SMTP servers have been disabled"
- Some servers failed authentication
- Check credentials in SMTP Servers tab
- Reload with working servers

### "Please load and parse X first"
- You haven't loaded required data
- Go to respective tab and load data
- Click "Parse & Validate"

### Emails not sending
- Check Debug Mode to see SMTP errors
- Verify SMTP credentials are correct
- Check your internet connection
- Ensure SMTP server allows connections

### URL shortening fails
- Internet connection issue
- is.gd service temporarily unavailable
- Will fallback to original URL automatically

## 📊 Performance Tips

- **Threads**: Start with 5-10, increase gradually
- **Sleep Time**: Use 0.5-1 second to avoid rate limiting
- **SMTP Servers**: Load 10+ servers for better rotation
- **Test First**: Always test with 5-10 recipients first

## 🔄 Differences from mainnotall.py

### ✅ Improved
- Visual GUI interface (no command line)
- Real-time progress tracking
- Better error visibility
- File operations built-in
- Live statistics display

### 🔒 Preserved
- SMTP lock mechanism (unchanged)
- Server rotation logic (unchanged)
- Failure tracking (unchanged)
- Thread pool execution (unchanged)

### ➕ Added
- Tabbed interface
- File load/save dialogs
- Real-time colored logs
- Progress bar
- Validation buttons
- Optional URL shortening toggle

## 📄 License

For educational purposes only. Use responsibly and in compliance with email sending regulations.

## 👨‍💻 Author

GUI Edition - Built on mainnotall.py foundation
Original SMTP lock mechanism preserved

---

**Version**: 1.0  
**Created**: December 2025
