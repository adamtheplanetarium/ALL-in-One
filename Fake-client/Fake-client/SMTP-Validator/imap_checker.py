"""
IMAP Checker Module
Verifies delivered messages via IMAP
Line count: ~390 lines
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta

class IMAPChecker:
    """Check IMAP for delivered messages"""
    
    def __init__(self, config_handler, tracker):
        """Initialize IMAP checker
        
        Args:
            config_handler: ConfigHandler instance
            tracker: MessageTracker instance
        """
        self.config = config_handler
        self.tracker = tracker
        
        self.connection = None
        self.is_checking = False
        self.stop_requested = False
        self.progress_callback = None
    
    def connect(self):
        """Connect to IMAP server
        
        Returns:
            tuple: (success, message)
        """
        # Validate config
        is_valid, error_msg = self.config.validate_imap_config()
        if not is_valid:
            return False, f"❌ Configuration Error: {error_msg}"
        
        host = self.config.get('imap', 'host')
        port = self.config.get('imap', 'port')
        username = self.config.get('imap', 'username')
        password = self.config.get('imap', 'password')
        use_ssl = self.config.get('imap', 'use_ssl', default=True)
        
        try:
            # Connect
            if use_ssl:
                self.connection = imaplib.IMAP4_SSL(host, port, timeout=15)
            else:
                self.connection = imaplib.IMAP4(host, port, timeout=15)
            
            # Login
            result = self.connection.login(username, password)
            
            # Get folder count
            try:
                folders = self.get_folders()
                folder_count = len(folders)
                return True, f"✅ Connected Successfully!\n\nServer: {host}:{port}\nUser: {username}\nFolders: {folder_count} available\nStatus: Ready to verify"
            except:
                return True, f"✅ Connected Successfully!\n\nServer: {host}:{port}\nUser: {username}\nStatus: Ready to verify"
            
        except imaplib.IMAP4.error as e:
            self.connection = None
            error_str = str(e).lower()
            if 'authentication' in error_str or 'login' in error_str or 'password' in error_str:
                return False, f"❌ Authentication Failed!\n\nServer: {host}:{port}\nUser: {username}\nError: Invalid username or password\n\nPlease check your credentials."
            else:
                return False, f"❌ IMAP Error: {e}"
        except ConnectionRefusedError:
            self.connection = None
            return False, f"❌ Connection Refused!\n\nServer: {host}:{port}\nError: Server refused connection\n\nCheck if IMAP is enabled in your email settings."
        except TimeoutError:
            self.connection = None
            return False, f"❌ Connection Timeout!\n\nServer: {host}:{port}\nError: Server not responding\n\nCheck your internet connection or firewall."
        except Exception as e:
            self.connection = None
            error_type = type(e).__name__
            return False, f"❌ Connection Failed!\n\nServer: {host}:{port}\nError Type: {error_type}\nDetails: {str(e)}"
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None
    
    def get_folders(self):
        """Get list of available folders
        
        Returns:
            list: List of folder names
        """
        if not self.connection:
            return []
        
        try:
            status, folders = self.connection.list()
            if status != 'OK':
                return []
            
            folder_names = []
            for folder in folders:
                # Parse folder name from response
                parts = folder.decode().split(' "/" ')
                if len(parts) >= 2:
                    folder_name = parts[1].strip('"')
                    folder_names.append(folder_name)
            
            return folder_names
            
        except Exception as e:
            print(f"Error getting folders: {e}")
            return []
    
    def search_messages(self, folder, date_filter=None):
        """Search for messages in folder
        
        Args:
            folder: Folder name to search
            date_filter: Date filter (default: today)
            
        Returns:
            list: List of message IDs
        """
        if not self.connection:
            return []
        
        try:
            # Select folder
            status, _ = self.connection.select(folder, readonly=True)
            if status != 'OK':
                return []
            
            # Build search criteria
            search_criteria = []
            
            # Date filter (default: today)
            if date_filter is None and self.config.get('verification', 'check_today_only', default=True):
                days_back = self.config.get('verification', 'date_range_days', default=1)
                since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
                search_criteria.append(f'SINCE {since_date}')
            
            # Search
            if search_criteria:
                search_string = ' '.join(search_criteria)
            else:
                search_string = 'ALL'
            
            status, message_ids = self.connection.search(None, search_string)
            
            if status != 'OK':
                return []
            
            # Parse message IDs
            ids = message_ids[0].split()
            return [mid.decode() for mid in ids]
            
        except Exception as e:
            print(f"Error searching {folder}: {e}")
            return []
    
    def fetch_message(self, message_id):
        """Fetch and parse message
        
        Args:
            message_id: Message ID
            
        Returns:
            dict: Parsed message or None
        """
        if not self.connection:
            return None
        
        try:
            # Fetch message
            status, msg_data = self.connection.fetch(message_id, '(RFC822)')
            
            if status != 'OK' or not msg_data or not msg_data[0]:
                return None
            
            # Parse email
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            return email_message
            
        except Exception as e:
            print(f"Error fetching message {message_id}: {e}")
            return None
    
    def extract_message_info(self, email_message):
        """Extract information from email message
        
        Args:
            email_message: email.message.Message object
            
        Returns:
            dict: Extracted information
        """
        info = {
            'subject': '',
            'from': '',
            'to': '',
            'tracking_id': None,
            'return_path': '',
            'received': []
        }
        
        try:
            # Subject
            subject = email_message.get('Subject', '')
            if subject:
                # Decode if encoded
                decoded = decode_header(subject)
                subject_parts = []
                for part, encoding in decoded:
                    if isinstance(part, bytes):
                        subject_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                    else:
                        subject_parts.append(part)
                info['subject'] = ''.join(subject_parts)
            
            # Extract tracking ID from subject
            info['tracking_id'] = self.tracker.extract_tracking_id(info['subject'])
            
            # From
            info['from'] = email_message.get('From', '')
            
            # To
            info['to'] = email_message.get('To', '')
            
            # Return-Path
            info['return_path'] = email_message.get('Return-Path', '')
            
            # Received headers
            received_headers = email_message.get_all('Received', [])
            info['received'] = received_headers
            
        except Exception as e:
            print(f"Error extracting message info: {e}")
        
        return info
    
    def check_folder(self, folder, progress_callback=None):
        """Check single folder for delivered messages
        
        Args:
            folder: Folder name
            progress_callback: Optional callback(status_msg)
            
        Returns:
            int: Number of matched messages
        """
        matched = 0
        
        if progress_callback:
            progress_callback(f"Searching {folder}...")
        
        # Search messages
        message_ids = self.search_messages(folder)
        
        if not message_ids:
            if progress_callback:
                progress_callback(f"No messages found in {folder}")
            return 0
        
        if progress_callback:
            progress_callback(f"Found {len(message_ids)} messages in {folder}, checking...")
        
        # Check each message
        for i, msg_id in enumerate(message_ids):
            if self.stop_requested:
                break
            
            # Fetch and parse
            email_message = self.fetch_message(msg_id)
            if not email_message:
                continue
            
            # Extract info
            info = self.extract_message_info(email_message)
            
            # Check if has tracking ID
            if info['tracking_id']:
                # Register as delivered
                self.tracker.register_delivered_message(
                    info['tracking_id'],
                    info['from'],
                    folder,
                    info
                )
                matched += 1
                
                if progress_callback:
                    progress_callback(f"✓ Matched: {info['tracking_id']} in {folder}")
            
            # Progress update
            if progress_callback and (i + 1) % 10 == 0:
                progress_callback(f"Checked {i + 1}/{len(message_ids)} in {folder}")
        
        return matched
    
    def verify_delivery(self, progress_callback=None):
        """Verify delivery by checking configured folders
        
        Args:
            progress_callback: Optional callback(status_msg)
            
        Returns:
            dict: Verification results
        """
        self.is_checking = True
        self.stop_requested = False
        self.progress_callback = progress_callback
        
        # Connect if not connected
        if not self.connection:
            success, error_msg = self.connect()
            if not success:
                return {'error': error_msg}
        
        # Get folders to check
        folders_to_check = self.config.get('verification', 'search_folders', 
                                           default=['INBOX', 'Junk'])
        
        total_matched = 0
        folder_results = {}
        
        try:
            for folder in folders_to_check:
                if self.stop_requested:
                    break
                
                try:
                    matched = self.check_folder(folder, progress_callback)
                    folder_results[folder] = matched
                    total_matched += matched
                    
                    # Log folder summary
                    if matched > 0 and progress_callback:
                        if 'inbox' in folder.lower():
                            progress_callback(f"✓ {folder}: {matched} messages (INBOX - Good!)")
                        elif 'junk' in folder.lower() or 'spam' in folder.lower():
                            progress_callback(f"⚠ {folder}: {matched} messages (JUNK/SPAM - Warning!)")
                        else:
                            progress_callback(f"📧 {folder}: {matched} messages")
                    
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"⚠ Error in {folder}: {e}")
                    folder_results[folder] = 0
        
        finally:
            self.is_checking = False
        
        # Get statistics
        stats = self.tracker.get_summary_statistics()
        
        return {
            'total_matched': total_matched,
            'folder_results': folder_results,
            'statistics': stats,
            'stopped': self.stop_requested
        }
    
    def stop(self):
        """Stop checking"""
        self.stop_requested = True
    
    def get_status(self):
        """Get current checking status
        
        Returns:
            dict: Status information
        """
        return {
            'is_checking': self.is_checking,
            'is_connected': self.connection is not None
        }
    
    def __str__(self):
        return f"IMAPChecker(connected={self.connection is not None})"
    
    def __repr__(self):
        return self.__str__()
