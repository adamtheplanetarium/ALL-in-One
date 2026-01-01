# 🚀 Quick Start Guide - SMTP Validator

## 1️⃣ Launch Application

```bash
cd c:\Users\deshaz\Desktop\Projects\Fake-client\SMTP-Validator
python main.py
```

The GUI will open with 4 tabs.

---

## 2️⃣ Prepare Files

The application auto-creates sample files in the `data/` folder:

### `data/smtps.txt` (your SMTP servers)
```
mail.example.com:587:user@example.com:password123
smtp.gmail.com:587:your.email@gmail.com:app_password
```

### `data/recipients.txt` (test recipients)
```
testbox@gmail.com
```

**Edit these files with your real SMTP servers and recipient email!**

---

## 3️⃣ Send Test Messages

1. Go to **📤 SMTP Sending** tab
2. Click **"Load SMTPs"** → Select `data/smtps.txt`
3. Click **"Load Recipients"** → Select `data/recipients.txt`
4. Set thread count (default: 10)
5. Click **"▶ Start Sending"**

Watch the green console log for progress:
```
[14:30:25] ✓ Loaded 5 SMTPs from file
[14:30:28] ✓ Loaded 1 recipients from file
[14:30:35] ✓ mail.example.com:587 → testbox@gmail.com (TRK-20240115143035123)
[14:30:36] ✗ smtp.bad.com:25 - Connection timeout
```

Messages are sent with tracking IDs like `TRK-20240115143035123`.

---

## 4️⃣ Configure IMAP

1. Go to **📬 IMAP Verification** tab
2. Enter IMAP settings:
   - **Host**: `imap.gmail.com`
   - **Port**: `993`
   - **Username**: `testbox@gmail.com`
   - **Password**: Your app password (not regular password!)
3. Click **"💾 Save Settings"**
4. Click **"🔌 Test Connection"** to verify it works

### Gmail App Password Setup:
1. Enable 2-Factor Authentication
2. Go to: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Select "Mail" → "Other" → Generate
4. Use this 16-character password in the IMAP settings

---

## 5️⃣ Verify Delivery

**Wait 2-5 minutes** after sending for emails to arrive!

1. Stay on **📬 IMAP Verification** tab
2. Check boxes for:
   - ✅ INBOX
   - ✅ Junk/Spam
3. Click **"▶ Start Verification"**

Watch the cyan console log:
```
[14:35:10] ✓ Connected to IMAP server
[14:35:12] Checking folder: INBOX
[14:35:15] ✓ Found message: TRK-20240115143035123
[14:35:16] ✓ Matched 3/5 messages
```

The tool will:
- Search INBOX and Junk folders
- Extract tracking IDs from messages
- Match them to sent messages
- Mark SMTPs as verified or failed

---

## 6️⃣ View Results

1. Go to **📊 Results** tab
2. See summary statistics:
   ```
   Total Sent:        5
   Total Delivered:   3
   Delivery Rate:    60.00%
   Inbox Rate:       66.67%
   Junk Rate:        33.33%
   ```
3. View detailed table with each SMTP's status

---

## 7️⃣ Export Results

Click buttons in **📊 Results** tab:

- **📥 Export Verified SMTPs** → Saves to `data/verified_smtps.txt`
- **📥 Export Failed SMTPs** → Saves to `data/failed_smtps.txt`
- **📊 Export CSV Report** → Save custom CSV file

### `data/verified_smtps.txt` (working SMTPs)
```
mail.example.com:587:user@example.com:password123
smtp.another.com:25:sender@another.com:secret
```

**Use these verified SMTPs for your real campaigns!**

---

## 🎯 Full Workflow Summary

```
┌─────────────────┐
│ 1. Prepare Files│ (smtps.txt, recipients.txt)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 2. Send Messages│ (with tracking IDs)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 3. Wait 2-5 min │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 4. Configure    │ (IMAP settings)
│    IMAP         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 5. Verify       │ (check INBOX/Junk)
│    Delivery     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 6. Export       │ (verified_smtps.txt)
│    Results      │
└─────────────────┘
```

---

## 💡 Pro Tips

1. **Start Small** - Test with 2-3 SMTPs first to verify everything works
2. **Use App Passwords** - Never use regular email passwords
3. **Wait Before Verifying** - Give emails 2-5 minutes to arrive
4. **Check Multiple Folders** - Messages might land in Junk
5. **Export After Each Test** - Save verified SMTPs immediately

---

## ⚠️ Common Issues

### "Authentication Failed" when sending
- ✓ Check SMTP username/password
- ✓ Some SMTPs need app passwords (Gmail, Outlook)
- ✓ Verify SMTP port (587 for STARTTLS, 465 for SSL, 25 for plain)

### "IMAP Connection Failed"
- ✓ Enable IMAP in email settings (Gmail: Settings → Forwarding and POP/IMAP)
- ✓ Use app password instead of regular password
- ✓ Check firewall isn't blocking port 993

### "No Messages Found"
- ✓ Wait longer (2-5 minutes)
- ✓ Check Junk/Spam folders
- ✓ Verify SMTP actually sent (check sending log)
- ✓ Check date range (default: 1 day back)

### "Tracking ID Not Found"
- ✓ Verify message subject contains TRK-YYYYMMDDHHMMSSMMM
- ✓ Check if email was modified in transit
- ✓ View raw message to see actual subject

---

## 📊 Understanding Results

- **Verified SMTP** = Successfully sent AND delivered to inbox/junk
- **Failed SMTP** = Sent but NOT found in inbox/junk (network issue, blocked, etc.)
- **Inbox Rate** = % of delivered messages that went to INBOX (not junk)
- **Junk Rate** = % of delivered messages that went to Junk/Spam

**High inbox rate = Good sender reputation** 🎉  
**High junk rate = Needs IP/domain warming** ⚠️

---

## 🔒 Security Notes

- Configuration file stores IMAP password in plain text
- Keep `config.json` secure
- Use app passwords (more secure than regular passwords)
- Delete sensitive data after use if needed

---

## ✅ Success Checklist

- [ ] Prepared smtps.txt with your SMTP servers
- [ ] Prepared recipients.txt with test email
- [ ] Sent test messages successfully
- [ ] Configured IMAP settings
- [ ] Tested IMAP connection
- [ ] Verified delivery (found tracking IDs)
- [ ] Viewed results and statistics
- [ ] Exported verified SMTPs
- [ ] Ready to use verified SMTPs for real campaigns!

---

**Need Help?** Check the full [README.md](README.md) for detailed documentation.

**Version**: 1.0  
**Python**: 3.7+  
**No Dependencies**: Pure Python stdlib
