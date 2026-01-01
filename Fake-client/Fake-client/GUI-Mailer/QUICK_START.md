# 🚀 QUICK START GUIDE - SENDING SYSTEMS

## ⚡ FAST OVERVIEW

### You have TWO sending systems:

**1. Check Froms Tab** = Test FROMs (1 email per FROM, then remove)
**2. Sending Tab** = Bulk campaigns (reuse senders, randomize everything)

---

## 🎯 Check Froms Tab (Testing FROMs)

### Purpose:
Test if FROM addresses work. Each FROM sends ONCE then is removed.

### Steps:
1. Load FROM addresses
2. Load recipients  
3. Load SMTP servers
4. Set template
5. Click "Start Sending"

### What happens:
```
FROM 1 → Recipient A
FROM 2 → Recipient B  
FROM 3 → Recipient C
FROM 4 → Recipient A (cycles back)
...etc
```

Each FROM is **REMOVED** after successful send.

---

## 📧 Sending Tab (Bulk Campaigns)

### Purpose:
Send many emails with rotation and randomization.

### Steps:
1. Select sender mode (Verified/Unverified/Both)
2. Add recipients (one per line)
3. Add subjects (one per line, will randomize)
4. Add names (one per line, will randomize)
5. Add template with tags:
   - `{RECIPIENT}` = recipient's email
   - `{NAME}` = random name from list
   - `{DATE}` = current date
   - `{TIME}` = current time
   - `{RAND:100-999}` = random number in range
6. Set threads (3-5 recommended)
7. Click "Start Sending"

### What happens:
```
Sender 1 → Recipient A (Subject: Random 1, Name: Random 1)
Sender 2 → Recipient B (Subject: Random 2, Name: Random 2)
Sender 3 → Recipient C (Subject: Random 3, Name: Random 3)
Sender 1 → Recipient D (Subject: Random 4, Name: Random 4)
...etc
```

Senders are **REUSED** (not removed).

---

## 🔧 Template Example

```html
Hello {RECIPIENT},

I'm {NAME} from our support team.

Your verification code is: {RAND:1000-9999}

Date: {DATE}
Time: {TIME}

Best regards,
{NAME}
```

All tags will be automatically replaced for each email!

---

## 🛡️ NEW FEATURES ADDED TODAY

✅ **SMTP Health Tracking** - Failed SMTPs auto-removed after 10 failures
✅ **SMTP Success Tracking** - 3 successes reduce failure count by 1
✅ **Thread Safety** - No more counter corruption
✅ **5 Retry Logic** - Each email tries 5 different SMTPs before giving up
✅ **Real-time Stats** - See Sent/Failed counts update live

---

## 📊 Console Output Explained

### Success:
```
✓ Sent FROM sender@domain.com TO recipient@domain.com
```

### Retry:
```
✓ Sent FROM sender@domain.com TO recipient@domain.com (retry 2)
```

### Failed:
```
✗ Failed FROM sender@domain.com TO recipient@domain.com (tried 5 times): error message
```

### SMTP Rotation:
```
🔄 Rotating SMTP: user@server.com:587
```

---

## ⚙️ Recommended Settings

### For Testing (Small):
- Threads: **3**
- FROMs: **5-10**
- Recipients: **5-10**

### For Production (Large):
- Threads: **10**
- FROMs: **50+**
- Recipients: **100+**

---

## 🚨 Troubleshooting

### "No SMTP available"
→ Load SMTP servers in SMTP Servers tab

### "No senders available"  
→ Load FROM addresses and verify them first

### "No recipients"
→ Add recipient emails (one per line, must have @)

### Emails not sending
→ Check console log for detailed error messages

### SMTP keeps failing
→ System will auto-remove after 10 failures, add good SMTPs

---

## ✅ READY TO GO!

Both systems verified working. Start with small test, then scale up!
