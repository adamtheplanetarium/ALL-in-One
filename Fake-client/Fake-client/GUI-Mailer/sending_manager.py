"""
Sending Manager Module
Handles bulk email sending with rotation and randomization
"""
import threading
import time
import smtplib
import random
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
from datetime import datetime
from colorama import Fore, Style

class SendingManager:
    """Manages bulk email sending with sender rotation"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.sending_thread = None
        self.is_sending = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        
        self.total_sent = 0
        self.total_failed = 0
        self.counter_lock = threading.Lock()  # Thread-safe counter updates
        
    def start_sending(self, sender_mode='verified', recipients_list=None, template='', subjects_list=None, names_list=None):
        """Start bulk sending process"""
        if self.is_sending:
            from tkinter import messagebox
            messagebox.showwarning("Already Running", "Sending is already in progress!")
            return
        
        # Validate inputs
        if not recipients_list:
            from tkinter import messagebox
            messagebox.showerror("No Recipients", "Please add recipient emails!")
            return
        
        if not template:
            from tkinter import messagebox
            messagebox.showerror("No Template", "Please add email template!")
            return
        
        if not self.gui.smtp_servers:
            from tkinter import messagebox
            messagebox.showerror("No SMTP", "Please load SMTP servers first!")
            return
        
        # Get sender list based on mode
        if sender_mode == 'verified':
            senders = self.gui.verified_froms.copy()
        elif sender_mode == 'unverified':
            senders = self.gui.unverified_froms.copy()
        else:  # both
            senders = self.gui.verified_froms.copy() + self.gui.unverified_froms.copy()
        
        if not senders:
            from tkinter import messagebox
            messagebox.showerror("No Senders", f"No {sender_mode} senders available!")
            return
        
        # Start sending thread
        self.is_sending = True
        self.is_paused = False
        self.pause_event.set()
        self.total_sent = 0
        self.total_failed = 0
        
        self.sending_thread = threading.Thread(
            target=self._sending_loop,
            args=(senders, recipients_list, template, subjects_list, names_list),
            daemon=True
        )
        self.sending_thread.start()
        
        self.gui.sending_log_print("="*60, 'info')
        self.gui.sending_log_print(f"📤 STARTING BULK SEND", 'success')
        self.gui.sending_log_print(f"Senders: {len(senders)} ({sender_mode})", 'info')
        self.gui.sending_log_print(f"Recipients: {len(recipients_list)}", 'info')
        self.gui.sending_log_print(f"Threads: {self.gui.thread_count.get()}", 'info')
        self.gui.sending_log_print("="*60, 'info')
    
    def pause_sending(self):
        """Pause sending"""
        if self.is_sending and not self.is_paused:
            self.is_paused = True
            self.pause_event.clear()
            self.gui.sending_log_print("⏸️ SENDING PAUSED", 'warning')
            print(f"{Fore.YELLOW}⏸️ Sending paused by user{Style.RESET_ALL}")
    
    def resume_sending(self):
        """Resume sending"""
        if self.is_sending and self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.gui.sending_log_print("▶️ SENDING RESUMED", 'success')
            print(f"{Fore.GREEN}▶️ Sending resumed{Style.RESET_ALL}")
    
    def stop_sending(self):
        """Stop sending completely"""
        if self.is_sending:
            self.is_sending = False
            self.is_paused = False
            self.pause_event.set()  # Unblock if paused
            self.gui.sending_log_print("⏹️ SENDING STOPPED", 'error')
            print(f"{Fore.RED}⏹️ Sending stopped by user{Style.RESET_ALL}")
    
    def _sending_loop(self, senders, recipients, template, subjects, names):
        """Main sending loop with rotation"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        try:
            sender_index = 0
            threads = self.gui.thread_count.get()
            
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = []
                
                for recipient in recipients:
                    if not self.is_sending:
                        break
                    
                    # Wait if paused
                    self.pause_event.wait()
                    
                    if not self.is_sending:
                        break
                    
                    # Rotate sender
                    sender = senders[sender_index % len(senders)]
                    sender_index += 1
                    
                    # Randomize subject
                    subject = random.choice(subjects) if subjects else "Important Message"
                    
                    # Randomize name
                    sender_name = random.choice(names) if names else "Team"
                    
                    # Randomize template
                    personalized_template = self._randomize_template(template, recipient, sender_name)
                    
                    # Submit send task
                    future = executor.submit(
                        self._send_single_email,
                        sender, recipient, subject, personalized_template, sender_name
                    )
                    futures.append(future)
                
                # Wait for completion
                for future in as_completed(futures):
                    if not self.is_sending:
                        break
                    future.result()
            
            # Summary
            self.gui.sending_log_print("\n" + "="*60, 'info')
            self.gui.sending_log_print("✅ SENDING COMPLETE!", 'success')
            self.gui.sending_log_print(f"   Total Sent: {self.total_sent} | Failed: {self.total_failed}", 'info')
            self.gui.sending_log_print("="*60, 'info')
            
        except Exception as e:
            self.gui.sending_log_print(f"❌ ERROR: {e}", 'error')
            print(f"{Fore.RED}Sending error: {e}{Style.RESET_ALL}")
        finally:
            self.is_sending = False
            self.is_paused = False
    
    def _send_single_email(self, sender, recipient, subject, template, sender_name):
        """Send single email with retry logic across different SMTP servers"""
        max_retries = 5
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Get SMTP server (rotate)
                smtp_config, server_key = self.gui.smtp_manager.get_next_smtp()
                if not smtp_config:
                    if attempt == 0:
                        with self.counter_lock:
                            self.total_failed += 1
                        self.gui.sending_log_print(f"   ✗ No SMTP available", 'error')
                    return False
                
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=30)
                
                try:
                    server.starttls()
                except:
                    pass
                
                server.login(smtp_config['username'], smtp_config['password'])
                
                msg = MIMEMultipart("alternative")
                msg['From'] = f'{sender_name} <{sender}>'
                msg['To'] = recipient
                msg['Subject'] = subject
                msg['Date'] = email.utils.formatdate(localtime=True)
                
                html_part = MIMEText(template, 'html')
                msg.attach(html_part)
                
                server.send_message(msg)
                server.quit()
                
                # Mark SMTP as successful (prevents premature removal)
                self.gui.smtp_manager.mark_smtp_success(server_key)
                
                with self.counter_lock:
                    self.total_sent += 1
                if attempt > 0:
                    self.gui.sending_log_print(f"   ✓ Sent FROM {sender} TO {recipient} (retry {attempt})", 'success')
                else:
                    self.gui.sending_log_print(f"   ✓ Sent FROM {sender} TO {recipient}", 'success')
                
                return True
                
            except Exception as e:
                last_error = e
                # Mark SMTP as failed for this attempt
                if smtp_config:
                    self.gui.smtp_manager.mark_smtp_failed(server_key)
                # Continue to next retry with different SMTP
                if attempt < max_retries - 1:
                    continue
        
        # All retries exhausted
        with self.counter_lock:
            self.total_failed += 1
        self.gui.sending_log_print(f"   ✗ Failed FROM {sender} TO {recipient} (tried {max_retries} times): {last_error}", 'error')
        return False
    
    def _randomize_template(self, template, recipient, sender_name):
        """Randomize email template with tags"""
        result = template
        
        # Replace tags
        result = result.replace('{RECIPIENT}', recipient)
        result = result.replace('{NAME}', sender_name)
        result = result.replace('{DATE}', datetime.now().strftime('%B %d, %Y'))
        result = result.replace('{TIME}', datetime.now().strftime('%I:%M %p'))
        
        # Random number tags
        result = re.sub(r'\{RAND:(\d+)-(\d+)\}', lambda m: str(random.randint(int(m.group(1)), int(m.group(2)))), result)
        
        return result
