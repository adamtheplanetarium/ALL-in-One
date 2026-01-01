# SMTP Validator - Project Plan

## 📋 Project Overview
**Purpose:** Test SMTP servers by sending 1 message from each SMTP, then use IMAP to verify which messages were delivered to extract working SMTPs.

## 🎯 Core Functionality

### Phase 1: SMTP Sending
1. Load SMTP servers from file
2. Load recipient email(s)
3. Send 1 unique test message from each SMTP
4. Track which SMTPs sent successfully (250 OK response)
5. Save sending results

### Phase 2: IMAP Verification
1. Connect to recipient inbox via IMAP
2. Check both INBOX and Junk/Spam folders
3. Search for test messages sent
4. Extract sender information from delivered messages
5. Identify which SMTPs actually delivered

### Phase 3: Results & Export
1. Compare sent vs delivered SMTPs
2. Export working SMTPs (actually delivered)
3. Export failed SMTPs (250 OK but not delivered)
4. Generate detailed report

## 📁 Project Structure

```
SMTP-Validator/
├── main.py                 # Main GUI application (~600 lines)
├── smtp_sender.py          # SMTP sending logic (~400 lines)
├── imap_checker.py         # IMAP verification logic (~400 lines)
├── config_handler.py       # Configuration management (~300 lines)
├── file_handler.py         # File I/O operations (~300 lines)
├── tracker.py              # Message tracking & matching (~400 lines)
├── requirements.txt        # Python dependencies
├── README.md               # User documentation
├── config.json             # Configuration file
├── data/                   # Data folder
│   ├── smtps.txt          # Input: SMTP servers
│   ├── recipients.txt     # Input: Test recipients
│   ├── sent_log.json      # Output: Sent messages log
│   ├── verified_smtps.txt # Output: Working SMTPs
│   └── failed_smtps.txt   # Output: Failed SMTPs
└── logs/                   # Log files folder
    └── app.log            # Application logs
```

## 🔧 Technical Stack

- **GUI Framework:** tkinter (built-in Python)
- **SMTP:** smtplib (built-in)
- **IMAP:** imaplib (built-in)
- **Email Parsing:** email library (built-in)
- **Threading:** concurrent.futures
- **Logging:** logging module
- **Config:** json

## 📝 Detailed TODO List

### ✅ Module 1: config_handler.py (~300 lines)
**Purpose:** Manage application configuration

- [ ] ConfigHandler class
  - [ ] Load/save config.json
  - [ ] Default configuration structure
  - [ ] IMAP settings (host, port, username, password)
  - [ ] SMTP timeout settings
  - [ ] Test message template
  - [ ] Tracking ID generation
  - [ ] Validate configuration values

**Key Features:**
- JSON-based configuration
- Validation of IMAP/SMTP settings
- Default values for first-time setup
- Auto-save on changes

---

### ✅ Module 2: file_handler.py (~300 lines)
**Purpose:** Handle all file operations

- [ ] FileHandler class
  - [ ] Load SMTP servers from file
    - [ ] Parse format: host:port:username:password
    - [ ] Validate SMTP format
    - [ ] Remove duplicates
  - [ ] Load recipients from file
  - [ ] Save sent messages log (JSON)
  - [ ] Save verified SMTPs
  - [ ] Save failed SMTPs
  - [ ] Export CSV reports
  - [ ] Create data directories if missing
  - [ ] Log file management

**Key Features:**
- Multiple format support (TXT, CSV)
- Error handling for missing files
- Auto-create directories
- Backup old results before overwrite

---

### ✅ Module 3: tracker.py (~400 lines)
**Purpose:** Track sent messages and match with delivered

- [ ] MessageTracker class
  - [ ] Generate unique tracking ID per message
  - [ ] Store sent message metadata:
    - [ ] Tracking ID
    - [ ] SMTP used (host:port:username)
    - [ ] Recipient email
    - [ ] Timestamp sent
    - [ ] Subject with tracking ID
    - [ ] SMTP response code
  - [ ] Match delivered messages:
    - [ ] Parse email headers
    - [ ] Extract tracking ID from subject
    - [ ] Extract sender from headers
    - [ ] Match tracking ID → SMTP
  - [ ] Generate statistics:
    - [ ] Total sent
    - [ ] Total delivered
    - [ ] Delivery rate per SMTP
    - [ ] Inbox vs Junk distribution

**Key Features:**
- Unique tracking ID in subject (e.g., "Test #TRK-12345678")
- Store full SMTP details for matching
- Handle edge cases (multiple deliveries, missing IDs)
- Performance metrics

---

### ✅ Module 4: smtp_sender.py (~400 lines)
**Purpose:** Send test messages via SMTP

- [ ] SMTPSender class
  - [ ] Send single message via SMTP
    - [ ] Connect with timeout
    - [ ] STARTTLS support
    - [ ] Login with credentials
    - [ ] Build MIME message with tracking ID
    - [ ] Send and capture response
    - [ ] Handle errors gracefully
  - [ ] Batch sending from SMTP list
    - [ ] ThreadPoolExecutor for parallel sending
    - [ ] Progress tracking
    - [ ] Pause/Resume/Stop controls
    - [ ] Rate limiting (optional)
  - [ ] Template processing:
    - [ ] Insert tracking ID in subject
    - [ ] Insert SMTP info in body (for verification)
    - [ ] Recipient name personalization
  - [ ] Error handling:
    - [ ] Connection errors
    - [ ] Authentication errors
    - [ ] Rate limiting errors
    - [ ] Timeout handling
  - [ ] Logging:
    - [ ] Success: SMTP → Recipient (250 OK)
    - [ ] Failure: SMTP error details

**Key Features:**
- Concurrent sending (configurable threads)
- Auto-retry on connection errors (3 attempts)
- Detailed error categorization
- Real-time progress updates
- Stop/pause functionality

---

### ✅ Module 5: imap_checker.py (~400 lines)
**Purpose:** Connect to IMAP and verify delivered messages

- [ ] IMAPChecker class
  - [ ] Connect to IMAP server
    - [ ] Support IMAP/IMAPS
    - [ ] Login with credentials
    - [ ] List available folders
  - [ ] Search messages:
    - [ ] Search INBOX folder
    - [ ] Search Junk/Spam folder (multiple names)
    - [ ] Filter by date range (today's messages)
    - [ ] Filter by subject pattern (tracking ID)
  - [ ] Parse delivered messages:
    - [ ] Extract email headers
    - [ ] Extract subject → tracking ID
    - [ ] Extract From address
    - [ ] Extract Return-Path
    - [ ] Extract X-Originating-IP (if available)
    - [ ] Determine folder (Inbox vs Junk)
  - [ ] Match messages to SMTPs:
    - [ ] Use MessageTracker to match tracking ID
    - [ ] Verify sender matches SMTP username
    - [ ] Handle multiple matches
  - [ ] Statistics:
    - [ ] Total messages found
    - [ ] Inbox count vs Junk count
    - [ ] Matched SMTPs vs unmatched
  - [ ] Error handling:
    - [ ] Connection failures
    - [ ] Authentication errors
    - [ ] Folder not found
    - [ ] Parsing errors

**Key Features:**
- Support multiple Junk folder names (Junk, Spam, Bulk)
- Date-based filtering (today only)
- Header analysis for verification
- Folder location tracking (Inbox vs Junk)
- Progress updates during checking

---

### ✅ Module 6: main.py (~600 lines)
**Purpose:** Main GUI application

- [ ] EmailValidatorGUI class
  - [ ] GUI Layout:
    - [ ] Notebook/Tabs:
      - [ ] Tab 1: SMTP Sending
        - [ ] Load SMTPs button + file path display
        - [ ] Load recipients button + file path display
        - [ ] SMTP count label
        - [ ] Recipient count label
        - [ ] Send button (Start/Stop)
        - [ ] Progress bar
        - [ ] Status label
        - [ ] Sending log (ScrolledText)
      - [ ] Tab 2: IMAP Verification
        - [ ] IMAP settings (host, port, username, password)
        - [ ] Test Connection button
        - [ ] Check Messages button
        - [ ] Folder selection (Inbox/Junk/Both)
        - [ ] Verification log (ScrolledText)
        - [ ] Statistics display
      - [ ] Tab 3: Results
        - [ ] Summary statistics
        - [ ] Verified SMTPs list (with delivery rate)
        - [ ] Failed SMTPs list
        - [ ] Export buttons (TXT, CSV)
        - [ ] Detailed results table
      - [ ] Tab 4: Settings
        - [ ] Thread count slider
        - [ ] SMTP timeout setting
        - [ ] Test message template editor
        - [ ] IMAP auto-check option
        - [ ] Save settings button
  - [ ] Event Handlers:
    - [ ] Load SMTP file dialog
    - [ ] Load recipients file dialog
    - [ ] Start sending (threaded)
    - [ ] Stop sending
    - [ ] Start IMAP check (threaded)
    - [ ] Test IMAP connection
    - [ ] Export results
    - [ ] Save configuration
  - [ ] Integration:
    - [ ] Use SMTPSender for sending
    - [ ] Use IMAPChecker for verification
    - [ ] Use MessageTracker for matching
    - [ ] Use FileHandler for I/O
    - [ ] Use ConfigHandler for settings
  - [ ] Status Updates:
    - [ ] Real-time log updates
    - [ ] Progress bar updates
    - [ ] Statistics updates
    - [ ] Thread-safe GUI updates

**Key Features:**
- Clean, intuitive tabbed interface
- Real-time progress tracking
- Thread-safe operations
- Auto-save settings
- Comprehensive logging

---

## 🚀 Implementation Order

### Sprint 1: Foundation (Days 1-2)
1. **config_handler.py** - Configuration management
2. **file_handler.py** - File operations
3. **tracker.py** - Message tracking system

### Sprint 2: Core Functionality (Days 3-4)
4. **smtp_sender.py** - SMTP sending logic
5. **imap_checker.py** - IMAP verification logic

### Sprint 3: GUI & Integration (Days 5-6)
6. **main.py** - GUI application
7. Integration testing
8. Bug fixes and refinement

### Sprint 4: Polish & Documentation (Day 7)
9. Error handling improvements
10. User documentation (README.md)
11. Final testing
12. Release preparation

---

## 📊 Message Format

### Test Message Structure:
```
Subject: Email Delivery Test #TRK-12345678

Body:
------------------------------------
SMTP DELIVERY VERIFICATION TEST
------------------------------------

This is an automated test message.

Test ID: TRK-12345678
Sent From: smtp.example.com:587
Sender: user@domain.com
Timestamp: 2025-12-22 14:30:45 UTC

If you received this message, the SMTP server is working correctly.

------------------------------------
Automated by SMTP Validator v1.0
------------------------------------
```

### Tracking ID Format:
- Pattern: `TRK-[TIMESTAMP][RANDOM]`
- Example: `TRK-20251222143045789`
- Embedded in subject and body
- Used to match sent → delivered

---

## 🔍 Verification Logic

### Matching Process:
1. **Send Phase:**
   - Generate unique tracking ID
   - Send message with tracking ID in subject
   - Log: TrackingID → SMTP details
   
2. **Verify Phase:**
   - Connect to IMAP
   - Search messages by date
   - Extract tracking ID from subject
   - Lookup tracking ID → get expected SMTP
   - Verify sender matches SMTP username
   
3. **Results:**
   - **Verified SMTP:** Message found in inbox/junk with matching tracking ID
   - **Failed SMTP:** 250 OK response but message not found
   - **Error SMTP:** Did not get 250 OK response

---

## 📈 Statistics & Reports

### Generated Reports:

1. **verified_smtps.txt** (Working SMTPs)
   ```
   # Working SMTP Servers - Verified Delivery
   # Format: host:port:username:password | Folder
   smtp.example.com:587:user@domain.com:password | INBOX
   mail.test.com:587:test@mail.com:pass123 | JUNK
   ```

2. **failed_smtps.txt** (Not Delivered)
   ```
   # Failed SMTP Servers - No Delivery Confirmation
   # Format: host:port:username:password | Reason
   smtp.bad.com:587:user@bad.com:pass | Message not found in inbox/junk
   ```

3. **Statistics Summary:**
   ```
   Total SMTPs Tested: 342
   Sent Successfully (250 OK): 320
   Delivered to Inbox: 280
   Delivered to Junk: 30
   Not Delivered: 10
   SMTP Errors: 22
   
   Delivery Rate: 96.9% (310/320)
   Inbox Rate: 87.5% (280/320)
   Junk Rate: 9.4% (30/320)
   ```

---

## 🛡️ Error Handling

### Robust Error Management:

1. **SMTP Errors:**
   - Connection timeout → Retry 3 times
   - Authentication failure → Log and skip
   - Rate limiting → Wait and retry
   - Network errors → Log and continue

2. **IMAP Errors:**
   - Connection failure → Show error, allow retry
   - Authentication failure → Prompt for credentials
   - Folder not found → Search alternative names
   - Parsing errors → Skip message, log error

3. **File Errors:**
   - File not found → Show file picker
   - Invalid format → Show error, highlight issue
   - Permission denied → Show error message

---

## 🎨 GUI Design Principles

1. **Simplicity:** Clear workflow (Load → Send → Verify → Export)
2. **Feedback:** Real-time progress and status updates
3. **Safety:** Confirm before overwriting files
4. **Flexibility:** Configurable settings for advanced users
5. **Stability:** Thread-safe operations, proper error handling

---

## 🔧 Configuration File (config.json)

```json
{
  "imap": {
    "host": "imap.gmail.com",
    "port": 993,
    "username": "your-email@gmail.com",
    "password": "",
    "use_ssl": true
  },
  "smtp": {
    "timeout": 30,
    "threads": 10,
    "retry_attempts": 3,
    "rate_limit_delay": 0
  },
  "message": {
    "subject_template": "Email Delivery Test #{TRACKING_ID}",
    "body_template": "...(see above)..."
  },
  "verification": {
    "search_folders": ["INBOX", "Junk", "Spam", "[Gmail]/Spam"],
    "match_sender": true,
    "check_today_only": true
  },
  "ui": {
    "auto_check_after_send": false,
    "show_detailed_logs": true
  }
}
```

---

## 📦 Dependencies (requirements.txt)

```
# No external dependencies required!
# Uses only Python built-in libraries:
# - tkinter (GUI)
# - smtplib (SMTP)
# - imaplib (IMAP)
# - email (email parsing)
# - threading, concurrent.futures
# - json, logging
```

---

## ✅ Success Criteria

1. ✅ All files under 800 lines
2. ✅ Modular, maintainable code structure
3. ✅ Thread-safe operations
4. ✅ Comprehensive error handling
5. ✅ Real-time progress tracking
6. ✅ Accurate SMTP verification
7. ✅ Easy to use GUI
8. ✅ Detailed logging and reports
9. ✅ Stable, no crashes
10. ✅ Well-documented

---

## 🚀 Ready to Build!

This plan provides:
- Clear module separation (<800 lines each)
- Comprehensive functionality
- Robust error handling
- User-friendly GUI
- Accurate verification logic

**Start with Sprint 1 - Foundation modules!**
