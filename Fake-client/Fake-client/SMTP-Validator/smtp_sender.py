"""
SMTP Sender Module
Sends test messages via SMTP servers
Line count: ~380 lines
"""

import smtplib
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class SMTPSender:
    """Send test messages via SMTP"""
    
    def __init__(self, config_handler, file_handler, tracker):
        """Initialize SMTP sender
        
        Args:
            config_handler: ConfigHandler instance
            file_handler: FileHandler instance
            tracker: MessageTracker instance
        """
        self.config = config_handler
        self.file_handler = file_handler
        self.tracker = tracker
        
        # State variables
        self.is_sending = False
        self.stop_requested = False
        self.pause_requested = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        
        # Counters (thread-safe)
        self.sent_count = 0
        self.failed_count = 0
        self.counter_lock = threading.Lock()
        
        # Progress callback
        self.progress_callback = None
    
    def send_single_message(self, smtp_config, recipient, smtp_password):
        """Send single test message via SMTP
        
        Args:
            smtp_config: Dict with SMTP configuration
            recipient: Recipient email address
            smtp_password: SMTP password (not stored in config)
            
        Returns:
            dict: Result with success status and details
        """
        result = {
            'success': False,
            'tracking_id': None,
            'smtp': f"{smtp_config['host']}:{smtp_config['port']}",
            'recipient': recipient,
            'error': None,
            'smtp_response': None
        }
        
        # Generate tracking ID
        tracking_id = self.tracker.generate_tracking_id()
        result['tracking_id'] = tracking_id
        
        # Get message template
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        subject, body = self.config.get_message_template(tracking_id, smtp_config, timestamp)
        
        # Retry logic
        max_retries = self.config.get('smtp', 'retry_attempts', default=3)
        retry_delay = self.config.get('smtp', 'retry_delay', default=5)
        timeout = self.config.get('smtp', 'timeout', default=30)
        
        last_error = None
        
        for attempt in range(max_retries):
            if self.stop_requested:
                result['error'] = 'Stopped by user'
                return result
            
            # Wait if paused
            self.pause_event.wait()
            
            try:
                # Connect to SMTP server with reduced timeout for faster failure detection
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=timeout)
                
                try:
                    # STARTTLS
                    server.starttls()
                except:
                    pass  # Some servers don't support STARTTLS
                
                # Login
                server.login(smtp_config['username'], smtp_password)
                
                # Build message
                msg = MIMEMultipart()
                msg['From'] = smtp_config['username']
                msg['To'] = recipient
                msg['Subject'] = subject
                msg['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
                
                # Attach body
                msg.attach(MIMEText(body, 'plain'))
                
                # Send
                send_response = server.sendmail(smtp_config['username'], [recipient], msg.as_string())
                
                server.quit()
                
                # Check response
                if send_response:
                    # Some recipients rejected
                    result['error'] = f"Rejected: {send_response}"
                    result['smtp_response'] = str(send_response)
                else:
                    # Success (250 OK)
                    result['success'] = True
                    result['smtp_response'] = '250 OK'
                    
                    # Register in tracker
                    self.tracker.register_sent_message(
                        tracking_id,
                        smtp_config,
                        recipient,
                        timestamp,
                        '250 OK'
                    )
                    
                    with self.counter_lock:
                        self.sent_count += 1
                
                break  # Success, exit retry loop
                
            except smtplib.SMTPAuthenticationError as e:
                last_error = f"Authentication failed: {e}"
                result['error'] = last_error
                break  # Don't retry auth errors - fail fast
                
            except (ConnectionRefusedError, OSError) as e:
                # Connection errors - don't retry, fail fast
                last_error = f"Connection error: {e}"
                result['error'] = last_error
                break
                
            except smtplib.SMTPException as e:
                last_error = f"SMTP error: {e}"
                result['error'] = last_error
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                
            except Exception as e:
                last_error = f"Connection error: {e}"
                result['error'] = last_error
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
        
        # If we got here without success, mark as failed
        if not result['success']:
            with self.counter_lock:
                self.failed_count += 1
            result['error'] = last_error or 'Unknown error'
        
        return result
    
    def send_batch(self, smtps_list, recipients_list, progress_callback=None):
        """Send test messages to all SMTPs
        
        Args:
            smtps_list: List of SMTP config dicts (with passwords)
            recipients_list: List of recipient emails
            progress_callback: Optional callback(current, total, status_msg)
            
        Returns:
            dict: Summary statistics
        """
        self.is_sending = True
        self.stop_requested = False
        self.sent_count = 0
        self.failed_count = 0
        self.progress_callback = progress_callback
        
        if not smtps_list:
            return {'error': 'No SMTPs provided'}
        
        if not recipients_list:
            return {'error': 'No recipients provided'}
        
        # Get thread count
        max_workers = self.config.get('smtp', 'threads', default=10)
        
        # Use first recipient (or round-robin if multiple)
        recipient_index = 0
        
        total = len(smtps_list)
        completed = 0
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                futures = {}
                
                for smtp_config in smtps_list:
                    if self.stop_requested:
                        break
                    
                    # Get recipient (round-robin)
                    recipient = recipients_list[recipient_index % len(recipients_list)]
                    recipient_index += 1
                    
                    # Submit task
                    future = executor.submit(
                        self.send_single_message,
                        smtp_config,
                        recipient,
                        smtp_config['password']
                    )
                    futures[future] = smtp_config
                
                # Process completed tasks
                for future in as_completed(futures):
                    if self.stop_requested:
                        break
                    
                    completed += 1
                    
                    try:
                        result = future.result()
                        
                        # Progress update with counters
                        if self.progress_callback:
                            status = "✓ Sent" if result['success'] else "✗ Failed"
                            smtp_info = result['smtp']
                            progress_msg = f"[{self.sent_count} sent / {self.failed_count} failed / {completed}/{total}] {status}: {smtp_info}"
                            self.progress_callback(completed, total, progress_msg)
                        
                    except Exception as e:
                        with self.counter_lock:
                            self.failed_count += 1
                        
                        if self.progress_callback:
                            self.progress_callback(completed, total, f"✗ Error: {e}")
        
        finally:
            self.is_sending = False
        
        # Save sent log
        messages = self.tracker.export_to_dict_list()
        self.file_handler.save_sent_log(messages)
        
        return {
            'total': total,
            'sent': self.sent_count,
            'failed': self.failed_count,
            'completed': completed,
            'stopped': self.stop_requested
        }
    
    def stop(self):
        """Stop sending"""
        self.stop_requested = True
        self.pause_event.set()  # Unpause if paused
    
    def pause(self):
        """Pause sending"""
        self.pause_requested = True
        self.pause_event.clear()
    
    def resume(self):
        """Resume sending"""
        self.pause_requested = False
        self.pause_event.set()
    
    def get_status(self):
        """Get current sending status
        
        Returns:
            dict: Status information
        """
        return {
            'is_sending': self.is_sending,
            'is_paused': self.pause_requested,
            'sent': self.sent_count,
            'failed': self.failed_count
        }
    
    def __str__(self):
        return f"SMTPSender(sent={self.sent_count}, failed={self.failed_count})"
    
    def __repr__(self):
        return self.__str__()
