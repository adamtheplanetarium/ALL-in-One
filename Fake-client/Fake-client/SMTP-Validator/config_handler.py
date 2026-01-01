"""
Configuration Handler Module
Manages application settings and configuration
Line count: ~280 lines
"""

import json
import os
from datetime import datetime

class ConfigHandler:
    """Handle application configuration"""
    
    DEFAULT_CONFIG = {
        "imap": {
            "host": "imap.mail.yahoo.com",
            "port": 993,
            "username": "boxer204@att.net",
            "password": "lappbauhnrqhtpop",
            "use_ssl": True
        },
        "smtp": {
            "timeout": 30,
            "threads": 10,
            "retry_attempts": 3,
            "rate_limit_delay": 0,
            "retry_delay": 5
        },
        "message": {
            "subject_template": "Email Delivery Test #{TRACKING_ID}",
            "body_template": """------------------------------------
SMTP DELIVERY VERIFICATION TEST
------------------------------------

This is an automated test message.

Test ID: {TRACKING_ID}
Sent From: {SMTP_HOST}:{SMTP_PORT}
Sender: {SMTP_USER}
Timestamp: {TIMESTAMP}

If you received this message, the SMTP server is working correctly.

------------------------------------
Automated by SMTP Validator v1.0
------------------------------------"""
        },
        "verification": {
            "search_folders": ["INBOX", "Junk", "Spam", "[Gmail]/Spam", "Bulk Mail"],
            "match_sender": True,
            "check_today_only": True,
            "date_range_days": 1
        },
        "ui": {
            "auto_check_after_send": False,
            "show_detailed_logs": True,
            "window_width": 1400,
            "window_height": 900
        },
        "paths": {
            "data_folder": "data",
            "logs_folder": "logs",
            "smtps_file": "data/smtps.txt",
            "recipients_file": "data/recipients.txt",
            "sent_log_file": "data/sent_log.json",
            "verified_smtps_file": "data/verified_smtps.txt",
            "failed_smtps_file": "data/failed_smtps.txt"
        }
    }
    
    def __init__(self, config_file="config.json"):
        """Initialize config handler
        
        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file or create default
        
        Returns:
            dict: Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults (in case new keys added)
                    config = self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded_config)
                    return config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default, loaded):
        """Recursively merge loaded config with defaults
        
        Args:
            default: Default config dictionary
            loaded: Loaded config dictionary
            
        Returns:
            dict: Merged configuration
        """
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    default[key] = self._merge_configs(default[key], value)
                else:
                    default[key] = value
        return default
    
    def save_config(self, config=None):
        """Save configuration to file
        
        Args:
            config: Configuration dict to save (default: self.config)
        """
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, *keys, default=None):
        """Get config value by nested keys
        
        Args:
            *keys: Nested keys to traverse
            default: Default value if key not found
            
        Returns:
            Config value or default
            
        Example:
            config.get('imap', 'host') -> 'imap.gmail.com'
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *keys, value):
        """Set config value by nested keys
        
        Args:
            *keys: Nested keys to traverse
            value: Value to set
            
        Returns:
            bool: True if successful
            
        Example:
            config.set('imap', 'host', value='imap.outlook.com')
        """
        if len(keys) == 0:
            return False
            
        # Navigate to parent
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set value
        target[keys[-1]] = value
        return True
    
    def validate_imap_config(self):
        """Validate IMAP configuration
        
        Returns:
            tuple: (is_valid, error_message)
        """
        host = self.get('imap', 'host')
        port = self.get('imap', 'port')
        username = self.get('imap', 'username')
        password = self.get('imap', 'password')
        
        if not host:
            return False, "IMAP host is required"
        if not port or not isinstance(port, int):
            return False, "IMAP port must be a valid integer"
        if not username:
            return False, "IMAP username is required"
        if not password:
            return False, "IMAP password is required"
            
        return True, "Valid"
    
    def validate_smtp_entry(self, smtp_line):
        """Validate single SMTP entry format
        
        Supports two formats:
        - username:password:host:port (NEW)
        - host:port:username:password (OLD - for backward compatibility)
        
        Args:
            smtp_line: SMTP string
            
        Returns:
            tuple: (is_valid, parsed_dict or error_message)
        """
        parts = smtp_line.strip().split(':')
        if len(parts) != 4:
            return False, "Invalid format. Expected: username:password:host:port"
        
        # Detect format by checking if second part is a number (port)
        try:
            port_test = int(parts[1])
            # OLD format: host:port:username:password
            host, port, username, password = parts
        except ValueError:
            # NEW format: username:password:host:port
            username, password, host, port = parts
        
        if not host:
            return False, "Host cannot be empty"
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return False, "Port must be between 1-65535"
        except ValueError:
            return False, "Port must be a valid integer"
        
        if not username:
            return False, "Username cannot be empty"
        
        if not password:
            return False, "Password cannot be empty"
        
        return True, {
            'host': host,
            'port': port,
            'username': username,
            'password': password
        }
    
    def get_message_template(self, tracking_id, smtp_config, timestamp=None):
        """Generate message from template
        
        Args:
            tracking_id: Unique tracking identifier
            smtp_config: Dict with SMTP details
            timestamp: ISO timestamp (default: now)
            
        Returns:
            tuple: (subject, body)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        subject_template = self.get('message', 'subject_template')
        body_template = self.get('message', 'body_template')
        
        # Replace placeholders
        subject = subject_template.replace('{TRACKING_ID}', tracking_id)
        
        body = body_template.replace('{TRACKING_ID}', tracking_id)
        body = body.replace('{SMTP_HOST}', smtp_config.get('host', ''))
        body = body.replace('{SMTP_PORT}', str(smtp_config.get('port', '')))
        body = body.replace('{SMTP_USER}', smtp_config.get('username', ''))
        body = body.replace('{TIMESTAMP}', timestamp)
        
        return subject, body
    
    def get_tracking_id_pattern(self):
        """Get regex pattern for tracking ID
        
        Returns:
            str: Regex pattern to match tracking IDs
        """
        return r'TRK-\d{17}'
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        data_folder = self.get('paths', 'data_folder')
        logs_folder = self.get('paths', 'logs_folder')
        
        os.makedirs(data_folder, exist_ok=True)
        os.makedirs(logs_folder, exist_ok=True)
    
    def get_full_path(self, path_key):
        """Get full file path from config
        
        Args:
            path_key: Key in paths section
            
        Returns:
            str: Full file path
        """
        return self.get('paths', path_key, default='')
    
    def __str__(self):
        """String representation"""
        return f"ConfigHandler(file='{self.config_file}')"
    
    def __repr__(self):
        return self.__str__()
