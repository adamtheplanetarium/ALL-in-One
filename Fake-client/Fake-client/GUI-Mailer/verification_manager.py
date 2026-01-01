"""
Verification Manager Module
Handles email verification with pause/resume/stop controls
"""
import threading
import time
import smtplib
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
from datetime import datetime
import uuid
from colorama import Fore, Style

class VerificationManager:
    """Manages email verification with advanced controls"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.verification_thread = None
        self.is_verifying = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        self.sent_test_emails = {}
        self.wait_time = 300  # 5 minutes = 300 seconds
        
    def start_verification(self, mode='all'):
        """Start verification process - Verifies emails based on mode"""
        if self.is_verifying:
            from tkinter import messagebox
            messagebox.showwarning("Already Running", "Verification is already in progress!")
            return
        
        # Check prerequisites FIRST
        if not self.gui.smtp_servers:
            from tkinter import messagebox
            messagebox.showerror("No SMTP", "Please load and parse SMTP servers first!")
            return
        
        if not self.gui.recipient_email_list:
            from tkinter import messagebox
            messagebox.showerror("No Recipients", "Please load and parse recipients first!")
            return
        
        # Get emails to verify based on mode
        if mode == 'all':
            # ALL mode: Wait for NEW emails during monitoring
            verified_content = self.gui.verified_from_text.get(1.0, 'end').strip()
            unverified_content = self.gui.unverified_from_text.get(1.0, 'end').strip()
            
            existing_verified = set([line.strip() for line in verified_content.split('\n') if line.strip() and '@' in line])
            existing_unverified = set([line.strip() for line in unverified_content.split('\n') if line.strip() and '@' in line])
            existing_all = existing_verified | existing_unverified
            
            self.gui.verification_log_print("="*60, 'info')
            self.gui.verification_log_print(f"🔍 STARTING VERIFICATION ({mode.upper()})", 'success')
            self.gui.verification_log_print(f"📸 Snapshot: {len(existing_all)} existing emails (will be ignored)", 'info')
            self.gui.verification_log_print(f"⏳ Monitoring for NEW emails during verification...", 'info')
            self.gui.verification_log_print(f"Recipients pool: {len(self.gui.recipient_email_list)}", 'info')
            
            # Start verification thread with snapshot
            self.is_verifying = True
            self.is_paused = False
            self.pause_event.set()
            self.verification_thread = threading.Thread(
                target=self._verification_loop_monitor_new,
                args=(existing_all,),
                daemon=True
            )
            self.verification_thread.start()
            
        elif mode in ['verified', 'unverified']:
            # VERIFIED/UNVERIFIED mode: Verify CURRENT emails in textarea
            if mode == 'verified':
                content = self.gui.verified_from_text.get(1.0, 'end').strip()
            else:
                content = self.gui.unverified_from_text.get(1.0, 'end').strip()
            
            emails_to_verify = [line.strip() for line in content.split('\n') if line.strip() and '@' in line]
            
            if not emails_to_verify:
                from tkinter import messagebox
                messagebox.showinfo("No Emails", f"No emails to verify in {mode} textarea!")
                return
            
            # CRITICAL: Temporarily remove these emails from file BEFORE verification
            # This allows real-time detection of dead emails
            # Live emails will be re-added during verification, dead ones won't
            self._temporarily_remove_from_file(emails_to_verify, mode)
            
            self.gui.verification_log_print("="*60, 'info')
            self.gui.verification_log_print(f"🔍 STARTING VERIFICATION ({mode.upper()})", 'success')
            self.gui.verification_log_print(f"Emails to verify: {len(emails_to_verify)}", 'info')
            self.gui.verification_log_print(f"Recipients pool: {len(self.gui.recipient_email_list)}", 'info')
            self.gui.verification_log_print(f"🗑️ Temporarily removed from file - will re-add if still live", 'warning')
            
            # Start verification thread with emails list
            self.is_verifying = True
            self.is_paused = False
            self.pause_event.set()
            self.verification_thread = threading.Thread(
                target=self._verification_loop_direct,
                args=(emails_to_verify,),
                daemon=True
            )
            self.verification_thread.start()
    
    def pause_verification(self):
        """Pause verification"""
        if self.is_verifying and not self.is_paused:
            self.is_paused = True
            self.pause_event.clear()
            self.gui.verification_log_print("⏸️ VERIFICATION PAUSED", 'warning')
            print(f"{Fore.YELLOW}⏸️ Verification paused by user{Style.RESET_ALL}")
    
    def resume_verification(self):
        """Resume verification"""
        if self.is_verifying and self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.gui.verification_log_print("▶️ VERIFICATION RESUMED", 'success')
            print(f"{Fore.GREEN}▶️ Verification resumed{Style.RESET_ALL}")
    
    def stop_verification(self):
        """Stop verification completely"""
        if self.is_verifying:
            self.is_verifying = False
            self.is_paused = False
            self.pause_event.set()  # Unblock if paused
            self.gui.verification_log_print("⏹️ VERIFICATION STOPPED", 'error')
            print(f"{Fore.RED}⏹️ Verification stopped by user{Style.RESET_ALL}")
    
    def _temporarily_remove_from_file(self, emails_to_remove, mode):
        """
        Temporarily remove emails from verified_from.txt or unverified_from.txt
        This allows real-time detection of dead emails during recheck
        Live emails will be re-added during verification, dead ones won't
        """
        import os
        
        if mode == 'verified':
            filepath = 'verified_from.txt'
        else:
            filepath = 'unverified_from.txt'
        
        if not os.path.exists(filepath):
            return
        
        # Read current file content
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_emails = set([line.strip() for line in f if line.strip() and '@' in line])
        
        # Remove emails that are being verified
        emails_to_remove_set = set(emails_to_remove)
        updated_emails = existing_emails - emails_to_remove_set
        
        # Write back to file (without the emails being verified)
        with open(filepath, 'w', encoding='utf-8') as f:
            for email in sorted(updated_emails):
                f.write(email + '\n')
        
        print(f"{Fore.YELLOW}🗑️ Temporarily removed {len(emails_to_remove_set)} emails from {filepath}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   They will be re-added if still live during verification{Style.RESET_ALL}")
    
    def _verification_loop_monitor_new(self, existing_emails_snapshot):
        """Verification loop for monitoring NEW emails during session (ALL mode)"""
        try:
            # Phase 1: Wait and collect NEW emails (no sending yet)
            self.gui.verification_log_print("\n⏳ PHASE 1: Waiting 300 seconds and monitoring for NEW emails...", 'warning')
            
            for remaining in range(self.wait_time, 0, -30):
                if not self.is_verifying:
                    break
                
                self.pause_event.wait()
                
                if not self.is_verifying:
                    break
                
                self.gui.verification_log_print(f"   ⏱️  {remaining} seconds remaining...", 'info')
                time.sleep(30)
            
            if not self.is_verifying:
                return
            
            # Phase 2: Find NEW emails that were added during the wait
            self.gui.verification_log_print("\n📊 PHASE 2: Comparing emails...", 'success')
            
            verified_content = self.gui.verified_from_text.get(1.0, 'end').strip()
            unverified_content = self.gui.unverified_from_text.get(1.0, 'end').strip()
            
            current_verified = set([line.strip() for line in verified_content.split('\n') if line.strip() and '@' in line])
            current_unverified = set([line.strip() for line in unverified_content.split('\n') if line.strip() and '@' in line])
            current_all = current_verified | current_unverified
            
            # Find NEW emails (emails in current but NOT in snapshot)
            new_emails = current_all - existing_emails_snapshot
            
            self.gui.verification_log_print(f"   📸 Before: {len(existing_emails_snapshot)} emails", 'info')
            self.gui.verification_log_print(f"   📥 After: {len(current_all)} emails", 'info')
            self.gui.verification_log_print(f"   🆕 NEW: {len(new_emails)} emails to verify", 'success')
            
            if not new_emails:
                self.gui.verification_log_print("\n❌ No new emails extracted during verification!", 'error')
                self.is_verifying = False
                return
            
            # Phase 3: Send test emails for NEW emails only
            self.gui.verification_log_print("\n📤 PHASE 3: Sending test emails for NEW emails...", 'success')
            
            self.sent_test_emails = {}
            new_emails_list = list(new_emails)
            
            for idx, from_email in enumerate(new_emails_list):
                if not self.is_verifying:
                    break
                
                self.pause_event.wait()
                
                if not self.is_verifying:
                    break
                
                # Pick recipient (rotate)
                recipient = self.gui.recipient_email_list[idx % len(self.gui.recipient_email_list)]
                
                # Send test email
                success = self._send_test_email(from_email, recipient, idx+1, len(new_emails_list))
                
                if success:
                    self.sent_test_emails[from_email] = {
                        'sent_time': time.time(),
                        'recipient': recipient
                    }
                    self.gui.verification_log_print(f"   ✓ Sent FROM {from_email} TO {recipient}", 'success')
                else:
                    self.gui.verification_log_print(f"   ✗ Failed FROM {from_email}", 'error')
                
                time.sleep(2)  # Delay between sends
            
            if not self.sent_test_emails:
                self.gui.verification_log_print("❌ No test emails sent!", 'error')
                self.is_verifying = False
                return
            
            # Phase 4: Wait for replies
            self.gui.verification_log_print(f"\n⏳ PHASE 4: Waiting {self.wait_time} seconds for replies...", 'warning')
            
            for remaining in range(self.wait_time, 0, -30):
                if not self.is_verifying:
                    break
                
                self.pause_event.wait()
                
                if not self.is_verifying:
                    break
                
                self.gui.verification_log_print(f"   ⏱️  {remaining} seconds remaining...", 'info')
                time.sleep(30)
            
            if not self.is_verifying:
                return
            
            # Phase 5: Check inbox for bounce/failure messages + INSTANT classification
            self.gui.verification_log_print("\n📥 PHASE 5: Checking inbox and classifying...", 'success')
            
            from email.utils import parsedate_to_datetime
            
            bounced_emails = set()  # Dead emails that bounced
            received_emails = set()  # Live emails that were received
            accounts = self.gui.find_all_inboxes()
            
            # Find bounce messages from Mailer-Daemon or system
            bounce_keywords = ['mailer-daemon', 'mail delivery', 'postmaster', 'failure notice', 
                             'delivery status notification', 'undelivered', 'returned mail',
                             'mail delivery failed', 'delivery failure']
            
            for account in accounts:
                emails = self.gui.parse_inbox_file(account['path'])
                for email_data in emails:
                    from_addr = self.gui.extract_email_address(email_data['from']).lower()
                    subject = email_data.get('subject', '').lower()
                    
                    # Check if this is a bounce message
                    is_bounce = any(keyword in from_addr or keyword in subject for keyword in bounce_keywords)
                    
                    if is_bounce:
                        # Parse email body/subject to find which test email bounced
                        # Check for any of our test emails mentioned in the bounce
                        for test_email in self.sent_test_emails.keys():
                            if test_email.lower() in email_data.get('subject', '').lower():
                                bounced_emails.add(test_email)
                                self.gui.verification_log_print(f"   🔴 Bounce detected for {test_email}", 'error')
                    else:
                        # Check if this is a regular email FROM one of our test addresses
                        # Only count it if it was received AFTER we sent the test
                        clean_from = self.gui.extract_email_address(email_data['from'])
                        if clean_from in self.sent_test_emails:
                            # Check if email was received after we sent it
                            sent_info = self.sent_test_emails[clean_from]
                            sent_time = sent_info['sent_time']
                            
                            # Parse email date
                            try:
                                if email_data.get('date'):
                                    email_datetime = parsedate_to_datetime(email_data['date'])
                                    email_timestamp = email_datetime.timestamp()
                                    
                                    # Only count if received after we sent it (with 10 second buffer for clock differences)
                                    if email_timestamp >= (sent_time - 10):
                                        received_emails.add(clean_from)
                                        self.gui.verification_log_print(f"   ✅ Received email from {clean_from}", 'success')
                            except:
                                # If we can't parse date, assume it's recent
                                received_emails.add(clean_from)
            
            # Phase 6: INSTANT classification with real-time updates
            self.gui.verification_log_print("\n📊 PHASE 6: Classification Results", 'info')
            
            for from_email in self.sent_test_emails.keys():
                if from_email in bounced_emails:
                    # Email BOUNCED = NOT RESPONDING - Move to UNVERIFIED
                    if from_email not in self.gui.unverified_froms:
                        self.gui.unverified_froms.append(from_email)
                    if from_email in self.gui.verified_froms:
                        self.gui.verified_froms.remove(from_email)
                    
                    self.gui.verification_log_print(f"   ❌ {from_email} - NOT RESPONDING (bounce)", 'error')
                    self.gui.console_print(f"❌ FROM: {from_email} - NOT RESPONDING", 'red')
                elif from_email in received_emails:
                    # Email RECEIVED = STILL LIVE - Move to VERIFIED
                    if from_email not in self.gui.verified_froms:
                        self.gui.verified_froms.append(from_email)
                    if from_email in self.gui.unverified_froms:
                        self.gui.unverified_froms.remove(from_email)
                    
                    self.gui.verification_log_print(f"   ✅ {from_email} - STILL LIVE", 'success')
                    self.gui.console_print(f"✅ FROM: {from_email} - STILL LIVE", 'green')
                else:
                    # No bounce AND no receipt = NOT RESPONDING - Move to UNVERIFIED
                    if from_email not in self.gui.unverified_froms:
                        self.gui.unverified_froms.append(from_email)
                    if from_email in self.gui.verified_froms:
                        self.gui.verified_froms.remove(from_email)
                    
                    self.gui.verification_log_print(f"   ❌ {from_email} - NOT RESPONDING (not received)", 'error')
                    self.gui.console_print(f"❌ FROM: {from_email} - NOT RESPONDING", 'red')
                
                # INSTANT UPDATE: Refresh textareas and counts after EACH classification
                self.gui.root.after(0, lambda: self.gui.refresh_collected_froms())
            
            # Summary
            total = len(self.sent_test_emails)
            bounced = len(bounced_emails)
            received = len(received_emails)
            not_received = total - received - bounced
            verified = received
            unverified = bounced + not_received
            
            self.gui.verification_log_print("\n" + "="*60, 'info')
            self.gui.verification_log_print(f"✅ VERIFICATION COMPLETE!", 'success')
            self.gui.verification_log_print(f"   Total: {total} | Still Live: {verified} | Not Responding: {unverified}", 'info')
            self.gui.verification_log_print(f"   (Bounced: {bounced}, Not Received: {not_received})", 'info')
            self.gui.verification_log_print("="*60, 'info')
            
            # Save config
            self.gui.config_manager.save_config(self.gui)
            
        except Exception as e:
            self.gui.verification_log_print(f"❌ ERROR: {e}", 'error')
            print(f"{Fore.RED}Verification error: {e}{Style.RESET_ALL}")
        finally:
            self.is_verifying = False
            self.is_paused = False
    
    def _verification_loop_direct(self, emails_to_verify):
        """Verification loop for DIRECT email list (VERIFIED/UNVERIFIED modes)"""
        try:
            # Phase 1: Send test emails for provided list (NO countdown during sending)
            self.gui.verification_log_print("\n📤 PHASE 1: Sending test emails...", 'success')
            
            self.sent_test_emails = {}
            
            for idx, from_email in enumerate(emails_to_verify):
                if not self.is_verifying:
                    break
                
                self.pause_event.wait()
                
                if not self.is_verifying:
                    break
                
                # Pick recipient (rotate)
                recipient = self.gui.recipient_email_list[idx % len(self.gui.recipient_email_list)]
                
                # Send test email
                success = self._send_test_email(from_email, recipient, idx+1, len(emails_to_verify))
                
                if success:
                    self.sent_test_emails[from_email] = {
                        'sent_time': time.time(),
                        'recipient': recipient
                    }
                    self.gui.verification_log_print(f"   ✓ Sent FROM {from_email} TO {recipient}", 'success')
                else:
                    self.gui.verification_log_print(f"   ✗ Failed FROM {from_email}", 'error')
                
                time.sleep(2)  # Delay between sends
            
            if not self.sent_test_emails:
                self.gui.verification_log_print("❌ No test emails sent!", 'error')
                self.is_verifying = False
                return
            
            # Phase 2: Wait for replies (countdown ONLY here, after all emails sent)
            self.gui.verification_log_print(f"\n⏳ PHASE 2: Waiting {self.wait_time} seconds for replies...", 'warning')
            
            for remaining in range(self.wait_time, 0, -30):
                if not self.is_verifying:
                    break
                
                self.pause_event.wait()
                
                if not self.is_verifying:
                    break
                
                self.gui.verification_log_print(f"   ⏱️  {remaining} seconds remaining...", 'info')
                time.sleep(30)
            
            if not self.is_verifying:
                return
            
            # Phase 3: Check inbox for bounce/failure messages
            self.gui.verification_log_print("\n📥 PHASE 3: Checking inbox and classifying...", 'success')
            
            from email.utils import parsedate_to_datetime
            
            bounced_emails = set()  # Dead emails that bounced
            received_emails = set()  # Live emails that were received
            accounts = self.gui.find_all_inboxes()
            
            # Find bounce messages from Mailer-Daemon or system
            bounce_keywords = ['mailer-daemon', 'mail delivery', 'postmaster', 'failure notice', 
                             'delivery status notification', 'undelivered', 'returned mail',
                             'mail delivery failed', 'delivery failure']
            
            for account in accounts:
                emails = self.gui.parse_inbox_file(account['path'])
                for email_data in emails:
                    from_addr = self.gui.extract_email_address(email_data['from']).lower()
                    subject = email_data.get('subject', '').lower()
                    
                    # Check if this is a bounce message
                    is_bounce = any(keyword in from_addr or keyword in subject for keyword in bounce_keywords)
                    
                    if is_bounce:
                        # Parse email body/subject to find which test email bounced
                        # Check for any of our test emails mentioned in the bounce
                        for test_email in self.sent_test_emails.keys():
                            if test_email.lower() in email_data.get('subject', '').lower():
                                bounced_emails.add(test_email)
                                self.gui.verification_log_print(f"   🔴 Bounce detected for {test_email}", 'error')
                    else:
                        # Check if this is a regular email FROM one of our test addresses
                        # Only count it if it was received AFTER we sent the test
                        clean_from = self.gui.extract_email_address(email_data['from'])
                        if clean_from in self.sent_test_emails:
                            # Check if email was received after we sent it
                            sent_info = self.sent_test_emails[clean_from]
                            sent_time = sent_info['sent_time']
                            
                            # Parse email date
                            try:
                                if email_data.get('date'):
                                    email_datetime = parsedate_to_datetime(email_data['date'])
                                    email_timestamp = email_datetime.timestamp()
                                    
                                    # Only count if received after we sent it (with 10 second buffer for clock differences)
                                    if email_timestamp >= (sent_time - 10):
                                        received_emails.add(clean_from)
                                        self.gui.verification_log_print(f"   ✅ Received email from {clean_from}", 'success')
                            except:
                                # If we can't parse date, assume it's recent
                                received_emails.add(clean_from)
            
            # Phase 4: Classification with real-time updates
            self.gui.verification_log_print("\n📊 PHASE 4: Classification Results", 'info')
            
            for from_email in self.sent_test_emails.keys():
                if from_email in bounced_emails:
                    # Email BOUNCED = NOT RESPONDING - Move to UNVERIFIED
                    if from_email not in self.gui.unverified_froms:
                        self.gui.unverified_froms.append(from_email)
                    if from_email in self.gui.verified_froms:
                        self.gui.verified_froms.remove(from_email)
                    
                    self.gui.verification_log_print(f"   ❌ {from_email} - NOT RESPONDING (bounce)", 'error')
                    self.gui.console_print(f"❌ FROM: {from_email} - NOT RESPONDING", 'red')
                elif from_email in received_emails:
                    # Email RECEIVED = STILL LIVE - Move to VERIFIED
                    if from_email not in self.gui.verified_froms:
                        self.gui.verified_froms.append(from_email)
                    if from_email in self.gui.unverified_froms:
                        self.gui.unverified_froms.remove(from_email)
                    
                    self.gui.verification_log_print(f"   ✅ {from_email} - STILL LIVE", 'success')
                    self.gui.console_print(f"✅ FROM: {from_email} - STILL LIVE", 'green')
                else:
                    # No bounce AND no receipt = NOT RESPONDING - Move to UNVERIFIED
                    if from_email not in self.gui.unverified_froms:
                        self.gui.unverified_froms.append(from_email)
                    if from_email in self.gui.verified_froms:
                        self.gui.verified_froms.remove(from_email)
                    
                    self.gui.verification_log_print(f"   ❌ {from_email} - NOT RESPONDING (not received)", 'error')
                    self.gui.console_print(f"❌ FROM: {from_email} - NOT RESPONDING", 'red')
                
                # INSTANT UPDATE: Refresh textareas and counts after EACH classification
                self.gui.root.after(0, lambda: self.gui.refresh_collected_froms())
            
            # Summary
            total = len(self.sent_test_emails)
            bounced = len(bounced_emails)
            received = len(received_emails)
            not_received = total - received - bounced
            verified = received
            unverified = bounced + not_received
            
            self.gui.verification_log_print("\n" + "="*60, 'info')
            self.gui.verification_log_print(f"✅ VERIFICATION COMPLETE!", 'success')
            self.gui.verification_log_print(f"   Total: {total} | Still Live: {verified} | Not Responding: {unverified}", 'info')
            self.gui.verification_log_print(f"   (Bounced: {bounced}, Not Received: {not_received})", 'info')
            self.gui.verification_log_print("="*60, 'info')
            
            # Save config
            self.gui.config_manager.save_config(self.gui)
            
        except Exception as e:
            self.gui.verification_log_print(f"❌ ERROR: {e}", 'error')
            print(f"{Fore.RED}Verification error: {e}{Style.RESET_ALL}")
        finally:
            self.is_verifying = False
            self.is_paused = False
    
    def _send_test_email(self, from_email, recipient, index, total):
        """Send single test email"""
        try:
            smtp_config = self.gui.smtp_servers[0] if self.gui.smtp_servers else None
            if not smtp_config:
                return False
            
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=30)
            
            try:
                server.starttls()
            except:
                pass
            
            server.login(smtp_config['username'], smtp_config['password'])
            
            msg = MIMEMultipart("alternative")
            msg['From'] = f'Verification Test <{from_email}>'
            msg['To'] = recipient
            msg['Subject'] = f'Test Email - Please Reply #{index}'
            msg['Date'] = email.utils.formatdate(localtime=True)
            msg['Message-ID'] = f"<{str(uuid.uuid4())}@verification.test>"
            
            html_body = f"""
            <html>
            <body>
                <h2>Email Verification Test</h2>
                <p>Testing if <strong>{from_email}</strong> can receive replies.</p>
                <p><strong>Please reply to complete verification.</strong></p>
                <p>Test #{index} of {total}</p>
                <p>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, "html"))
            server.sendmail(smtp_config['username'], [recipient], msg.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            return False
