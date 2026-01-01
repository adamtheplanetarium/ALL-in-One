# 📝 Textarea Input Guide

## New Features Added! 🎉

The SMTP Validator now supports **direct textarea input** for both SMTPs and recipients, plus **Thunderbird-style IMAP** presets.

---

## 📤 SMTP Sending Tab - New Interface

### Option 1: Type SMTPs Directly

1. In the **"SMTP Servers"** textarea, type your SMTP servers (one per line):
   ```
   mail.example.com:587:user@example.com:password123
   smtp.gmail.com:587:name@gmail.com:app_password
   smtp.another.com:25:sender@another.com:secret
   ```

2. Click **"✓ Parse SMTPs"** button

3. Status will show: `✓ X SMTPs loaded` (green text)

### Option 2: Load from File

1. Click **"📁 Load File"** button
2. Select your `smtps.txt` file
3. SMTPs will populate the textarea automatically
4. Already parsed and ready to send!

---

## 📧 Recipients - New Interface

### Option 1: Type Emails Directly

1. In the **"Recipients"** textarea, type email addresses (one per line):
   ```
   testbox@gmail.com
   verify@outlook.com
   check@yahoo.com
   ```

2. Click **"✓ Parse Recipients"** button

3. Status will show: `✓ X recipients loaded` (green text)

### Option 2: Load from File

1. Click **"📁 Load File"** button
2. Select your `recipients.txt` file
3. Emails will populate the textarea automatically
4. Already parsed and ready!

---

## 📬 IMAP Verification - Thunderbird Method

### Quick Setup Presets

Click one of the preset buttons for instant configuration:

- **Gmail** → `imap.gmail.com:993` (SSL)
- **Outlook** → `outlook.office365.com:993` (SSL)
- **Yahoo** → `imap.mail.yahoo.com:993` (SSL)

### Manual Setup

1. **Host**: Enter IMAP server (e.g., `imap.gmail.com`)
2. **Port**: Enter port number (993 for SSL, 143 for non-SSL)
3. **Use SSL**: Check/uncheck (auto-adjusts port)
4. **Username**: Your email address
5. **Password**: Your email password or app password

### New Buttons

- **💾 Save Settings** - Save IMAP configuration
- **🔌 Test Connection** - Verify IMAP works
- **📁 Detect Folders** - List all available folders (Thunderbird-style)

---

## 🎯 Complete Workflow Example

### Step 1: Enter SMTPs (Textarea)
```
mail.server1.com:587:user1@server1.com:pass1
smtp.server2.com:25:user2@server2.com:pass2
mail.server3.com:587:user3@server3.com:pass3
```
Click **✓ Parse SMTPs** → Shows `✓ 3 SMTPs loaded`

### Step 2: Enter Recipients (Textarea)
```
testbox@gmail.com
verify@outlook.com
```
Click **✓ Parse Recipients** → Shows `✓ 2 recipients loaded`

### Step 3: Send Messages
- Set threads to 10
- Click **▶ Start Sending**
- Watch green console log

### Step 4: Configure IMAP (Thunderbird-style)
- Click **Gmail** preset button
- Enter your Gmail address and app password
- Click **🔌 Test Connection** to verify
- Click **📁 Detect Folders** to see all folders

### Step 5: Verify Delivery
- Click **▶ Start Verification**
- Watch cyan console log
- See matched tracking IDs

### Step 6: View Results
- Go to **📊 Results** tab
- See delivery statistics
- Export verified SMTPs

---

## 💡 Pro Tips

### Textarea Benefits
- ✅ **No file needed** - Just paste and go!
- ✅ **Quick editing** - Edit directly in textarea
- ✅ **Copy/Paste** - Easy to copy from spreadsheets
- ✅ **Visual feedback** - See what you're sending
- ✅ **Still supports files** - Load button still works

### IMAP Presets
- ✅ **One-click setup** - Gmail/Outlook/Yahoo presets
- ✅ **Auto SSL detection** - Port changes with SSL checkbox
- ✅ **Folder detection** - See all available folders
- ✅ **Thunderbird-compatible** - Same settings as Thunderbird

### Mixing Both
You can:
1. Load file → Edit in textarea → Parse again
2. Type manually → Save for later use
3. Paste from clipboard → Parse immediately
4. Load file → Add more lines → Parse

---

## 📋 Format Examples

### SMTP Format (Required)
```
host:port:username:password
```

**Example:**
```
mail.example.com:587:user@example.com:password123
```

### Recipients Format
```
email@domain.com
```

**Example:**
```
testbox@gmail.com
verify@outlook.com
check@yahoo.com
```

---

## 🔧 Thunderbird-Style IMAP Settings

### Gmail
- **Host**: `imap.gmail.com`
- **Port**: `993`
- **SSL**: ✓ Yes
- **Folders**: INBOX, [Gmail]/Spam, [Gmail]/Sent, etc.

### Outlook/Office 365
- **Host**: `outlook.office365.com`
- **Port**: `993`
- **SSL**: ✓ Yes
- **Folders**: INBOX, Junk Email, Sent Items, etc.

### Yahoo
- **Host**: `imap.mail.yahoo.com`
- **Port**: `993`
- **SSL**: ✓ Yes
- **Folders**: INBOX, Bulk Mail, Sent, etc.

### Custom/Other
- **Host**: Your IMAP server
- **Port**: `993` (SSL) or `143` (non-SSL)
- **SSL**: Based on your server
- Click **📁 Detect Folders** to see available folders

---

## ⚠️ Common Issues

### "No valid SMTPs found"
- ✓ Check format: `host:port:username:password`
- ✓ Make sure port is a number
- ✓ No spaces around colons
- ✓ Each SMTP on separate line

### "No valid emails found"
- ✓ Each email on separate line
- ✓ Must contain `@` symbol
- ✓ No extra text on line

### "IMAP Connection Failed"
- ✓ Click preset button (Gmail/Outlook/Yahoo)
- ✓ Verify username/password
- ✓ Use app password (not regular password)
- ✓ Check SSL checkbox matches your server
- ✓ Click **🔌 Test Connection** first

### "Folders Not Detected"
- ✓ Test connection first
- ✓ Check IMAP is enabled in email settings
- ✓ Verify credentials are correct

---

## 🎨 Visual Indicators

### Status Colors
- **Green**: `✓ X items loaded` - Success!
- **Red**: `✗ Error message` - Fix required
- **Gray**: `0 items loaded` - Not loaded yet

### Console Logs
- **Green text**: Sending operations
- **Cyan text**: Verification operations
- **Timestamps**: `[HH:MM:SS]` format

---

## 🚀 Quick Start Examples

### Example 1: Test Single SMTP
```
Textarea Input:
mail.example.com:587:user@example.com:password123

Recipients:
testbox@gmail.com

Result: Tests 1 SMTP → 1 recipient
```

### Example 2: Test Multiple SMTPs
```
Textarea Input:
smtp1.example.com:587:user1@example.com:pass1
smtp2.example.com:587:user2@example.com:pass2
smtp3.example.com:587:user3@example.com:pass3

Recipients:
testbox@gmail.com
verify@outlook.com

Result: Tests 3 SMTPs → 2 recipients each (6 total messages)
```

### Example 3: Large Batch
```
- Paste 100 SMTPs from spreadsheet
- Click ✓ Parse SMTPs
- Enter 1 recipient
- Set threads to 20
- Start sending
- Result: Tests all 100 quickly
```

---

## 📊 Benefits Summary

| Feature | Old Way | New Way |
|---------|---------|---------|
| **SMTP Input** | File only | Textarea OR file |
| **Recipients** | File only | Textarea OR file |
| **IMAP Setup** | Manual entry | Presets + manual |
| **Folder Check** | Trial/error | Detect button |
| **Editing** | Edit file externally | Edit in textarea |
| **Quick Test** | Save file first | Paste & parse |

---

**Version**: 1.1  
**New Features**: Textarea input + Thunderbird-style IMAP  
**Compatibility**: Backwards compatible with file loading
