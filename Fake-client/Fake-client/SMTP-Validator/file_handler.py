"""
File Handler Module
Manages all file I/O operations
Line count: ~290 lines
"""

import os
import json
import csv
from datetime import datetime

class FileHandler:
    """Handle file operations for SMTP Validator"""
    
    def __init__(self, config_handler):
        """Initialize file handler
        
        Args:
            config_handler: ConfigHandler instance
        """
        self.config = config_handler
        self.config.ensure_directories()
    
    def load_smtps(self, file_path=None):
        """Load SMTP servers from file
        
        Args:
            file_path: Path to SMTP file (default: from config)
            
        Returns:
            list: List of SMTP dicts [{host, port, username, password}]
        """
        if file_path is None:
            file_path = self.config.get_full_path('smtps_file')
        
        if not os.path.exists(file_path):
            return []
        
        smtps = []
        seen = set()  # Track duplicates
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Validate format
                    is_valid, result = self.config.validate_smtp_entry(line)
                    if is_valid:
                        # Check for duplicates
                        smtp_key = f"{result['host']}:{result['port']}:{result['username']}"
                        if smtp_key not in seen:
                            smtps.append(result)
                            seen.add(smtp_key)
                    else:
                        print(f"Line {line_num}: {result}")
            
            return smtps
        except Exception as e:
            print(f"Error loading SMTPs: {e}")
            return []
    
    def load_recipients(self, file_path=None):
        """Load recipient emails from file
        
        Args:
            file_path: Path to recipients file (default: from config)
            
        Returns:
            list: List of email addresses
        """
        if file_path is None:
            file_path = self.config.get_full_path('recipients_file')
        
        if not os.path.exists(file_path):
            return []
        
        recipients = []
        seen = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    email = line.strip()
                    
                    # Skip empty lines and comments
                    if not email or email.startswith('#'):
                        continue
                    
                    # Basic email validation
                    if '@' in email and '.' in email.split('@')[1]:
                        if email.lower() not in seen:
                            recipients.append(email)
                            seen.add(email.lower())
            
            return recipients
        except Exception as e:
            print(f"Error loading recipients: {e}")
            return []
    
    def save_sent_log(self, sent_messages):
        """Save sent messages log to JSON
        
        Args:
            sent_messages: List of sent message dicts
            
        Returns:
            bool: True if successful
        """
        file_path = self.config.get_full_path('sent_log_file')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sent_messages, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving sent log: {e}")
            return False
    
    def load_sent_log(self):
        """Load sent messages log from JSON
        
        Returns:
            list: List of sent message dicts
        """
        file_path = self.config.get_full_path('sent_log_file')
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sent log: {e}")
            return []
    
    def save_verified_smtps(self, verified_smtps):
        """Save verified (working) SMTPs to file
        
        Args:
            verified_smtps: List of tuples (smtp_dict, folder)
            
        Returns:
            bool: True if successful
        """
        file_path = self.config.get_full_path('verified_smtps_file')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Verified SMTP Servers - Successfully Delivered\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# Format: username:password:host:port\n")
                f.write(f"# Total: {len(verified_smtps)}\n\n")
                
                for smtp, folder in verified_smtps:
                    # Format: username:password:host:port
                    line = f"{smtp['username']}:{smtp['password']}:{smtp['host']}:{smtp['port']}"
                    f.write(f"{line}\n")
            
            return True
        except Exception as e:
            print(f"Error saving verified SMTPs: {e}")
            return False
    
    def save_failed_smtps(self, failed_smtps):
        """Save failed SMTPs to file
        
        Args:
            failed_smtps: List of tuples (smtp_dict, reason)
            
        Returns:
            bool: True if successful
        """
        file_path = self.config.get_full_path('failed_smtps_file')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Failed SMTP Servers - Not Delivered\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# Format: username:password:host:port\n")
                f.write(f"# Total: {len(failed_smtps)}\n\n")
                
                for smtp, reason in failed_smtps:
                    # Format: username:password:host:port
                    line = f"{smtp['username']}:{smtp['password']}:{smtp['host']}:{smtp['port']}"
                    f.write(f"{line}\n")
            
            return True
        except Exception as e:
            print(f"Error saving failed SMTPs: {e}")
            return False
    
    def export_csv_report(self, results, file_path):
        """Export results to CSV file
        
        Args:
            results: List of result dicts
            file_path: Output CSV file path
            
        Returns:
            bool: True if successful
        """
        if not results:
            return False
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
    
    def backup_file(self, file_path):
        """Create backup of existing file
        
        Args:
            file_path: File to backup
            
        Returns:
            str: Backup file path or None if failed
        """
        if not os.path.exists(file_path):
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.backup_{timestamp}"
        
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def get_log_file_path(self):
        """Get application log file path
        
        Returns:
            str: Log file path
        """
        logs_folder = self.config.get('paths', 'logs_folder')
        date_str = datetime.now().strftime('%Y%m%d')
        return os.path.join(logs_folder, f'validator_{date_str}.log')
    
    def create_sample_files(self):
        """Create sample SMTP and recipient files"""
        # Sample SMTPs
        smtps_file = self.config.get_full_path('smtps_file')
        if not os.path.exists(smtps_file):
            with open(smtps_file, 'w', encoding='utf-8') as f:
                f.write("# SMTP Server List\n")
                f.write("# Format: username:password:host:port\n")
                f.write("# Example:\n")
                f.write("# your-email@gmail.com:your-password:smtp.gmail.com:587\n\n")
        
        # Sample recipients
        recipients_file = self.config.get_full_path('recipients_file')
        if not os.path.exists(recipients_file):
            with open(recipients_file, 'w', encoding='utf-8') as f:
                f.write("# Recipient Email List\n")
                f.write("# One email per line\n")
                f.write("# Default tester email:\n")
                f.write("boxer204@att.net\n")
    
    def __str__(self):
        return "FileHandler"
    
    def __repr__(self):
        return self.__str__()
