# Command-Line Output & Config Persistence - Quick Guide

## New Features Added

### 1. **Command-Line Printing** 
All monitoring activities now print to the terminal/console in real-time with color coding!

#### What You'll See:

**On Startup:**
```
======================================================================
📂 Configuration loaded successfully
   Thunderbird Path: C:\Users\...\ImapMail
   Fake From Counter: 45
   Last Saved: 2025-12-19 14:30:22
======================================================================
✅ Configuration applied to UI
```

**When Starting Monitor:**
```
======================================================================
🚀 INBOX MONITOR STARTING...
📂 Path: C:\Users\...\ImapMail
======================================================================

🔍 Performing initial scan...
✅ Found 3 accounts
  mail.yahoo.com                 :  45 emails
  yahoo.com-1                    :  23 emails  
  yahoo.com-2                    :  67 emails
📊 Total: 135 emails tracked
⏰ Checking for new emails every 60 seconds
======================================================================
```

**During Monitoring:**
```
[2025-12-19 14:35:22] 🔄 Check #1: Scanning for new emails...
   ✓ No new emails detected

[2025-12-19 14:36:22] 🔄 Check #2: Scanning for new emails...
```

**When New Email Detected:**
```
======================================================================
🆕 NEW EMAIL DETECTED!
   📧 Account: mail.yahoo.com
   👤 From: John Doe <john.doe@example.com>
   📝 Subject: RE: Your inquiry
   ✉️  Email: john.doe@example.com
💾 Saved to from.txt | Counter: 136
======================================================================
```

**When Stopping Monitor:**
```
======================================================================
🛑 INBOX MONITOR STOPPED
📊 Total emails collected: 136
======================================================================
```

**On Application Close:**
```
======================================================================
🛑 Shutting down Email Sender Pro...
   Stopping inbox monitor...
   Stopping email sending...
   Saving configuration...
✅ Configuration saved successfully
📊 Total emails collected: 136
💾 All settings saved to: gui_mailer_config.json
======================================================================
```

### 2. **Configuration Persistence**

Your settings are automatically saved and restored!

#### What Gets Saved:
- ✅ Thunderbird path
- ✅ Fake From counter value
- ✅ Domain From
- ✅ Domain Authentication
- ✅ Sender Name
- ✅ Email Subject
- ✅ Number of threads
- ✅ Delay between emails
- ✅ Last saved timestamp

#### When Config is Saved:
1. **Every time a new email is collected** (auto-save counter)
2. **When you change Thunderbird path**
3. **When you close the application** (saves all settings)

#### Config File:
- **Location**: `gui_mailer_config.json` (same folder as gui_mailer.py)
- **Format**: Human-readable JSON

**Example config file:**
```json
{
    "thunderbird_path": "C:\\Users\\deshaz\\AppData\\Roaming\\Thunderbird\\Profiles\\ryxodx96.default-release\\ImapMail",
    "fake_from_counter": 136,
    "domain_from": "charter.net",
    "domain_auth": "altona.fr",
    "sender_name": "Support Team",
    "email_subject": "Important Update",
    "threads": 5,
    "delay_between": 1,
    "last_saved": "2025-12-19 14:45:33"
}
```

## Color Coding

### Terminal Colors:
- 🟢 **Green**: Success, new emails, confirmations
- 🔵 **Cyan**: Information, details, paths
- 🟡 **Yellow**: Warnings, stops, shutdowns
- 🔴 **Red**: Errors, failures, critical issues

### GUI Activity Log Colors:
- **Cyan**: Info messages
- **Green**: Success messages
- **Yellow**: Warnings
- **Red**: Errors

## Usage Scenarios

### Scenario 1: First Time Use
```
1. Launch GUI → See "No previous config" message
2. Configure settings in tabs
3. Start monitoring
4. Close application → Settings saved!
```

### Scenario 2: Resuming Work
```
1. Launch GUI → Config auto-loads
   - Counter shows previous value
   - Thunderbird path restored
   - All settings restored
2. Continue where you left off!
```

### Scenario 3: Debugging Issues
```
1. Keep terminal/console visible
2. Start monitoring
3. Watch command-line output for:
   - Connection issues
   - File access errors
   - Path problems
   - Parse errors
4. See exactly what's happening in real-time!
```

### Scenario 4: Long-Running Collection
```
1. Start monitoring
2. Minimize GUI (keeps running)
3. Check terminal periodically
4. See new emails as they arrive:
   ======================================================================
   🆕 NEW EMAIL DETECTED!
   ...
   💾 Saved to from.txt | Counter: 150
   ======================================================================
```

## Troubleshooting with Command-Line Output

### Problem: "No INBOX files found!"
**Command-line shows:**
```
❌ No INBOX files found!
```
**Solution:** Check the path in config, browse to correct ImapMail folder

### Problem: Can't save to from.txt
**Command-line shows:**
```
❌ ERROR saving to file: [Errno 13] Permission denied: 'from.txt'
```
**Solution:** Check file permissions, close any programs using from.txt

### Problem: Parse errors
**Command-line shows:**
```
❌ MONITORING ERROR: invalid syntax...
```
**Solution:** Check INBOX file isn't corrupted, try different account

### Problem: Path issues
**Command-line shows:**
```
❌ Invalid path: C:\...
```
**Solution:** Verify Thunderbird profile path, check folder exists

## Benefits

### 1. **Never Lose Your Progress**
- Counter saves automatically
- Resume exactly where you left off
- Settings persist across restarts

### 2. **Debug Issues Easily**
- See real-time command-line output
- Color-coded messages
- Detailed error information
- Know exactly what's happening

### 3. **Monitor While Minimized**
- GUI can be minimized
- Terminal shows activity
- No need to keep GUI visible
- Background operation visible

### 4. **Quick Setup**
- First-time configuration saved
- Next time: instant startup
- No re-entering settings
- Fast workflow

## Advanced Usage

### Manual Config Edit
You can manually edit `gui_mailer_config.json`:
```json
{
    "thunderbird_path": "D:\\CustomPath\\ImapMail",
    "fake_from_counter": 0,
    ...
}
```
Save and restart → Changes applied!

### Reset Everything
Delete `gui_mailer_config.json` → Fresh start on next launch

### Backup Your Progress
Copy `gui_mailer_config.json` to backup folder → Restore anytime

### Multiple Profiles
```
gui_mailer_config.json       → Main profile
gui_mailer_config_work.json  → Work profile (rename to use)
gui_mailer_config_test.json  → Test profile
```

## Command-Line Arguments (Future)
Currently the config file handles all persistence, but you could extend to:
```bash
python gui_mailer.py --config=custom_config.json
python gui_mailer.py --reset-counter
python gui_mailer.py --verbose
```

## Files Generated
- `gui_mailer_config.json` - Main configuration
- `from.txt` - Collected email addresses
- (GUI also creates log files if you save logs)

## Tips

1. **Keep Terminal Visible**: See what's happening in real-time
2. **Check Config File**: Verify settings saved correctly
3. **Backup Regularly**: Copy config + from.txt to safe location
4. **Watch Counter**: Auto-increments and saves on each new email
5. **Debug Mode**: Terminal output is your friend for troubleshooting

---

**🎉 Now you can see everything happening and never lose your progress!**
