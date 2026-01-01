# Get From Feature - Inbox Monitor

## Overview
The "Get From" tab has been added as the 9th tab in the GUI Email Sender application. This feature automatically monitors your Thunderbird email inbox and extracts "From" addresses from incoming emails, adding them to your fake from address list in real-time.

## How It Works

### 1. **Background Monitoring**
- Runs in a separate background thread
- Continuously scans your Thunderbird INBOX files
- Detects new emails every 60 seconds
- Works alongside the main email sending process without interference

### 2. **Email Detection**
- Monitors all Yahoo (and other) accounts configured in Thunderbird
- Parses mbox format INBOX files
- Extracts "From" headers from new emails
- Uses MD5 hashing to detect only NEW emails (no duplicates)

### 3. **Automatic Collection**
- Extracts clean email addresses from "Name <email>" format
- Appends to `from.txt` file automatically
- Updates the "Fake From" counter in real-time
- Auto-reloads the From Addresses tab with new entries

## Features

### Big Counter Display
- Shows total number of emails collected
- Updates in real-time as new emails are detected
- Large 72pt font for easy viewing

### Monitor Controls
- **Start Monitoring**: Begin scanning for new emails
- **Stop Monitoring**: Halt the monitoring process
- **Browse Button**: Select your Thunderbird ImapMail directory

### Status Display
Shows:
- Monitoring status (Active/Stopped)
- Last check timestamp
- Number of active accounts being monitored

### Activity Log
- Real-time console showing all monitoring activity
- Color-coded messages:
  - 🟢 Green: Success/New emails found
  - 🔵 Cyan: Information
  - 🟡 Yellow: Warnings
  - 🔴 Red: Errors

## Configuration

### Thunderbird Path
Default path:
```
C:\Users\deshaz\AppData\Roaming\Thunderbird\Profiles\ryxodx96.default-release\ImapMail
```

You can change this path:
1. Click the "📂 Browse" button
2. Navigate to your Thunderbird profile folder
3. Select the `ImapMail` directory

### Finding Your Thunderbird Profile Path
1. Open Thunderbird
2. Go to: Help → Troubleshooting Information
3. Under "Application Basics", find "Profile Folder"
4. Click "Open Folder"
5. Look for the `ImapMail` subdirectory

## Usage Instructions

### Starting the Monitor

1. **Go to "Get From" tab** (Tab 9)
2. **Verify Thunderbird path** is correct
3. **Click "▶️ Start Monitoring"**
4. Monitor will:
   - Perform initial scan
   - Display all accounts found
   - Show count of existing emails
   - Begin checking for new emails every 60 seconds

### While Monitoring

The monitor will:
- ✅ Run continuously in the background
- ✅ Check for new emails every 60 seconds
- ✅ Display new email details when found
- ✅ Automatically save to `from.txt`
- ✅ Update the counter
- ✅ Auto-reload the From Addresses tab

### Stopping the Monitor

1. **Click "⏹️ Stop Monitoring"**
2. Monitoring will stop gracefully
3. All collected emails remain in `from.txt`
4. Counter retains the count

## Use Cases

### 1. **Continuous Collection**
Leave the monitor running 24/7 to continuously harvest from addresses from all incoming emails across all your Yahoo accounts.

### 2. **Bulk Import**
- Set up Thunderbird with multiple Yahoo accounts
- Import old emails
- Start monitoring
- Initial scan will collect all from addresses at once

### 3. **While Sending**
Run monitoring and sending simultaneously:
- Monitor tab: Collecting new from addresses
- Send Control tab: Sending emails
- Both operate independently without conflicts

## Technical Details

### Thread Safety
- Uses `threading.Lock()` for thread-safe counter updates
- Separate monitoring thread (daemon) runs independently
- Won't block or interfere with email sending thread

### File Operations
- Appends to `from.txt` with immediate flush (`fsync`)
- Auto-reloads From Addresses tab when new entries added
- Preserves existing addresses

### Duplicate Prevention
- Uses MD5 hash of full email content
- Tracks all seen emails in memory (`seen_emails` set)
- Only processes truly new emails

### Email Parsing
- Regex-based mbox format parsing
- Pattern: `^From - ` to detect message boundaries
- Extracts: From header, Subject, and calculates hash
- Handles encoding errors gracefully

## Example Output

### Initial Scan
```
============================================================
🚀 Starting Inbox Monitor...
📂 Path: C:\Users\...\ImapMail
🔍 Performing initial scan...
✅ Found 3 accounts

  mail.yahoo.com                 :  45 emails
  yahoo.com-1                    :  23 emails  
  yahoo.com-2                    :  67 emails

📊 Total: 135 emails tracked
⏰ Checking for new emails every 60 seconds
============================================================
```

### New Email Detected
```
🔄 Check #5: Scanning for new emails...
🆕 NEW EMAIL DETECTED!
   📧 Account: mail.yahoo.com
   👤 From: John Doe <john.doe@example.com>
   ✉️  Email: john.doe@example.com
💾 Saved to from.txt | Counter: 136
```

## Troubleshooting

### "No INBOX files found!"
- Check Thunderbird path is correct
- Ensure Thunderbird is using IMAP (not POP3)
- Verify the ImapMail folder exists

### "Path does not exist"
- Browse to correct Thunderbird profile folder
- Make sure path includes `ImapMail` directory
- Check folder permissions

### Not Detecting New Emails
- Wait 60 seconds between checks
- Verify new emails are in Thunderbird INBOX
- Check Activity Log for errors
- Restart monitoring

### Counter Not Updating
- Check if `from.txt` is writable
- Verify no permission issues
- Check Activity Log for save errors

## Benefits

1. **Automated**: No manual copy/paste needed
2. **Real-time**: Updates as emails arrive
3. **Continuous**: Runs 24/7 in background
4. **Multi-account**: Monitors all Yahoo accounts simultaneously
5. **Smart**: Only collects unique, new addresses
6. **Safe**: Thread-safe, won't interfere with sending
7. **Visual**: Big counter shows progress at a glance

## Integration with Main Workflow

### Recommended Workflow:
```
Step 1: Start monitoring (Get From tab)
  ↓
Step 2: Let it collect addresses (runs in background)
  ↓
Step 3: Configure SMTP, recipients, template
  ↓
Step 4: Start sending emails (Send Control tab)
  ↓
Monitoring continues collecting while sending!
```

## Files Modified

- `gui_mailer.py`: Added Get From tab and monitoring functions
- `from.txt`: Auto-updated by monitoring process

## Dependencies

All required modules already included:
- `threading`: Background monitoring
- `hashlib`: MD5 hashing for duplicate detection
- `re`: Regex for email parsing
- `os`: File operations
- `time`: Sleep intervals

No additional pip installs needed!

---

**Happy Collecting! 📬**
