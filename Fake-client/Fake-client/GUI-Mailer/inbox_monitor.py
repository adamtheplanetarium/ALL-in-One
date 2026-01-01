#!/usr/bin/env python3
"""
Thunderbird INBOX Monitor
Monitors all Yahoo email accounts for new messages and saves sender info to from.txt
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path
import hashlib


class ThunderbirdInboxMonitor:
    def __init__(self, imap_mail_path):
        self.imap_mail_path = Path(imap_mail_path)
        self.from_file = self.imap_mail_path / "from.txt"
        self.seen_emails = set()  # Track email hashes to detect new ones
        self.seen_emails_file = "seen_emails.json"  # Persistent storage
        self.accounts = []
        self._load_seen_emails()  # Load previously seen emails
        
    def find_all_inboxes(self):
        """Find all INBOX files in the ImapMail directory"""
        inboxes = []
        all_accounts = []
        
        # Search for all directories (accounts)
        for account_dir in self.imap_mail_path.iterdir():
            if account_dir.is_dir():
                # Skip Python cache and hidden folders
                if account_dir.name.startswith('__') or account_dir.name.startswith('.'):
                    continue
                
                inbox_file = account_dir / "INBOX"
                account_info = {
                    'account': account_dir.name,
                    'has_inbox': inbox_file.exists() and inbox_file.is_file(),
                    'path': inbox_file
                }
                
                all_accounts.append(account_info)
                
                if account_info['has_inbox']:
                    inboxes.append(account_info)
        
        return sorted(inboxes, key=lambda x: x['account']), sorted(all_accounts, key=lambda x: x['account'])
    
    def parse_email_from_mbox(self, content, start_pos=0):
        """Parse a single email from mbox format starting at position"""
        # Find the start of the email (From - line)
        from_line_pattern = re.compile(r'^From - ', re.MULTILINE)
        match = from_line_pattern.search(content, start_pos)
        
        if not match:
            return None
        
        email_start = match.start()
        
        # Find the next email start or end of file
        next_match = from_line_pattern.search(content, email_start + 1)
        if next_match:
            email_end = next_match.start()
        else:
            email_end = len(content)
        
        email_content = content[email_start:email_end]
        return email_content, email_end
    
    def extract_from_header(self, email_content):
        """Extract the From header from email content"""
        # Look for From: header (can span multiple lines)
        from_pattern = re.compile(r'^From:\s*(.+?)(?=\n[^\s]|\n\n)', re.MULTILINE | re.DOTALL)
        match = from_pattern.search(email_content)
        
        if match:
            from_value = match.group(1).strip()
            # Clean up multi-line headers
            from_value = re.sub(r'\s+', ' ', from_value)
            return from_value
        
        return None
    
    def extract_subject_header(self, email_content):
        """Extract the Subject header from email content"""
        subject_pattern = re.compile(r'^Subject:\s*(.+?)(?=\n[^\s]|\n\n)', re.MULTILINE | re.DOTALL)
        match = subject_pattern.search(email_content)
        
        if match:
            subject_value = match.group(1).strip()
            subject_value = re.sub(r'\s+', ' ', subject_value)
            return subject_value
        
        return "(No Subject)"
    
    def get_email_hash(self, email_content):
        """Generate a unique hash for an email to track if it's been seen"""
        # Use first 500 chars to create a unique identifier
        unique_part = email_content[:500]
        return hashlib.md5(unique_part.encode('utf-8', errors='ignore')).hexdigest()
    
    def _load_seen_emails(self):
        """Load previously seen email hashes from JSON file"""
        import json
        try:
            if os.path.exists(self.seen_emails_file):
                with open(self.seen_emails_file, 'r', encoding='utf-8') as f:
                    seen_list = json.load(f)
                    self.seen_emails = set(seen_list)
                    print(f"✅ Loaded {len(self.seen_emails)} previously seen emails")
        except Exception as e:
            print(f"⚠ Could not load seen emails: {e}")
            self.seen_emails = set()
    
    def _save_seen_emails(self):
        """Save seen email hashes to JSON file to prevent reprocessing"""
        import json
        try:
            with open(self.seen_emails_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.seen_emails), f)
        except Exception as e:
            print(f"⚠ Could not save seen emails: {e}")
    
    def extract_email_address(self, from_header):
        """Extract only the email address from From header"""
        if not from_header:
            return None
        
        # Pattern to match email in angle brackets: Name <email@domain.com>
        angle_bracket_pattern = re.compile(r'<([^>]+)>')
        match = angle_bracket_pattern.search(from_header)
        
        if match:
            return match.group(1).strip()
        
        # If no angle brackets, try to find email pattern directly
        email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        match = email_pattern.search(from_header)
        
        if match:
            return match.group(0).strip()
        
        # If nothing found, return the original (cleaned up)
        return from_header.strip()
    
    def parse_inbox_file(self, inbox_path):
        """Parse an INBOX file and return list of emails"""
        emails = []
        
        try:
            with open(inbox_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            position = 0
            while True:
                result = self.parse_email_from_mbox(content, position)
                if result is None:
                    break
                
                email_content, next_position = result
                
                from_header = self.extract_from_header(email_content)
                subject_header = self.extract_subject_header(email_content)
                email_hash = self.get_email_hash(email_content)
                
                if from_header:
                    emails.append({
                        'from': from_header,
                        'subject': subject_header,
                        'hash': email_hash,
                        'content_preview': email_content[:200]
                    })
                
                position = next_position
        
        except Exception as e:
            print(f"   ⚠ Error reading {inbox_path.name}: {e}")
        
        return emails
    
    def save_from_to_file(self, from_header, account_name):
        """Append From header to from.txt file"""
        try:
            # Ensure the file path exists and is writable
            with open(self.from_file, 'a', encoding='utf-8') as f:
                f.write(f"{from_header}\n")
                f.flush()  # Force write to disk immediately
                os.fsync(f.fileno())  # Ensure it's written to disk
            print(f"   ✓ Saved to from.txt: {from_header}")
        except Exception as e:
            print(f"   ⚠ Error writing to from.txt: {e}")
            import traceback
            traceback.print_exc()
    
    def initial_scan(self):
        """Perform initial scan of all inboxes"""
        print("=" * 80)
        print("🔍 THUNDERBIRD INBOX MONITOR - INITIAL SCAN")
        print("=" * 80)
        print(f"\n📁 Monitoring Path: {self.imap_mail_path}")
        print(f"💾 Output File: {self.from_file}\n")
        
        self.accounts, all_accounts = self.find_all_inboxes()
        
        print(f"📂 Found {len(all_accounts)} Email Account Folders:\n")
        
        # Show all accounts with their status
        active_count = 0
        inactive_count = 0
        for account in all_accounts:
            if account['has_inbox']:
                print(f"   ✓ {account['account']:30s} [Active]")
                active_count += 1
            else:
                print(f"   ✗ {account['account']:30s} [No INBOX file]")
                inactive_count += 1
        
        if not self.accounts:
            print("\n❌ No INBOX files found to monitor!")
            return False
        
        print(f"\n📬 Monitoring {active_count} Active Accounts (Skipping {inactive_count} without INBOX):\n")
        
        total_emails = 0
        for account in self.accounts:
            emails = self.parse_inbox_file(account['path'])
            account['email_count'] = len(emails)
            total_emails += len(emails)
            
            # Track all current emails as seen
            for email in emails:
                self.seen_emails.add(email['hash'])
            
            print(f"   {account['account']:30s} : {len(emails):3d} emails")
        
        print(f"\n📊 Total Emails in All INBOXes: {total_emails}")
        print(f"🔍 Tracking {len(self.seen_emails)} emails for change detection")
        print("\n" + "=" * 80)
        print("✅ Initial scan complete. Starting monitoring...")
        print("⏰ Checking for new emails every 1 minute")
        print("=" * 80 + "\n")
        
        return True
    
    def check_for_new_emails(self):
        """Check all inboxes for new emails"""
        new_emails_found = False
        
        for account in self.accounts:
            emails = self.parse_inbox_file(account['path'])
            
            # Check for new emails (not in seen_emails set)
            for email in emails:
                if email['hash'] not in self.seen_emails:
                    new_emails_found = True
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Extract only email address
                    email_address = self.extract_email_address(email['from'])
                    
                    print(f"\n🆕 [{timestamp}] NEW EMAIL DETECTED!")
                    print(f"   📧 Account: {account['account']}")
                    print(f"   👤 From: {email['from']}")
                    print(f"   📝 Subject: {email['subject']}")
                    print(f"   ✉️  Email: {email_address}")
                    
                    # Save only email address to from.txt
                    self.save_from_to_file(email_address, account['account'])
                    
                    # Mark as seen and persist to file
                    self.seen_emails.add(email['hash'])
                    self._save_seen_emails()  # Save after each new email
            
            # Update email count
            if len(emails) != account.get('email_count', 0):
                old_count = account.get('email_count', 0)
                account['email_count'] = len(emails)
                
                if len(emails) > old_count:
                    print(f"   📈 {account['account']}: {old_count} → {len(emails)} emails")
        
        return new_emails_found
    
    def monitor_loop(self, check_interval=60):
        """Main monitoring loop"""
        # Perform initial scan
        if not self.initial_scan():
            return
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                time.sleep(check_interval)
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] 🔄 Check #{check_count}: Scanning for new emails...")
                
                has_new = self.check_for_new_emails()
                
                if not has_new:
                    print(f"   ✓ No new emails detected")
        
        except KeyboardInterrupt:
            print("\n\n" + "=" * 80)
            print("🛑 Monitoring stopped by user")
            print(f"📊 Total checks performed: {check_count}")
            print(f"📧 Total emails tracked: {len(self.seen_emails)}")
            print(f"💾 From addresses saved to: {self.from_file}")
            print("=" * 80)


def main():
    # Configuration
    IMAP_MAIL_PATH = r"C:\Users\deshaz\AppData\Roaming\Thunderbird\Profiles\ryxodx96.default-release\ImapMail"
    CHECK_INTERVAL = 60  # seconds (1 minute)
    
    # Verify path exists
    if not os.path.exists(IMAP_MAIL_PATH):
        print(f"❌ Error: Path does not exist: {IMAP_MAIL_PATH}")
        return
    
    # Create monitor instance
    monitor = ThunderbirdInboxMonitor(IMAP_MAIL_PATH)
    
    # Start monitoring
    monitor.monitor_loop(check_interval=CHECK_INTERVAL)


if __name__ == "__main__":
    main()
