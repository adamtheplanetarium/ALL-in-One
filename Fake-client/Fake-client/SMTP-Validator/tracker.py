"""
Message Tracker Module
Tracks sent messages and matches with delivered ones
Line count: ~390 lines
"""

import re
import time
from datetime import datetime
from collections import defaultdict

class MessageTracker:
    """Track and match sent/delivered messages"""
    
    def __init__(self, config_handler):
        """Initialize message tracker
        
        Args:
            config_handler: ConfigHandler instance
        """
        self.config = config_handler
        self.sent_messages = {}  # tracking_id -> message_info
        self.delivered_messages = {}  # tracking_id -> delivery_info
        self.smtp_stats = defaultdict(lambda: {
            'sent': 0,
            'delivered': 0,
            'folder': None
        })
    
    def generate_tracking_id(self):
        """Generate unique tracking ID
        
        Returns:
            str: Tracking ID (TRK-YYYYMMDDHHMMSSMMM)
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        millis = str(int(time.time() * 1000) % 1000).zfill(3)
        return f"TRK-{timestamp}{millis}"
    
    def register_sent_message(self, tracking_id, smtp_config, recipient, timestamp, smtp_response):
        """Register a sent message
        
        Args:
            tracking_id: Unique tracking identifier
            smtp_config: Dict with SMTP details
            recipient: Recipient email address
            timestamp: ISO timestamp
            smtp_response: SMTP response code/message
        """
        smtp_key = self._get_smtp_key(smtp_config)
        
        self.sent_messages[tracking_id] = {
            'tracking_id': tracking_id,
            'smtp_host': smtp_config['host'],
            'smtp_port': smtp_config['port'],
            'smtp_username': smtp_config['username'],
            'smtp_password': smtp_config.get('password', ''),  # Store password
            'smtp_key': smtp_key,
            'recipient': recipient,
            'timestamp': timestamp,
            'smtp_response': smtp_response,
            'delivered': False,
            'delivery_folder': None
        }
        
        self.smtp_stats[smtp_key]['sent'] += 1
    
    def register_delivered_message(self, tracking_id, sender_email, folder, headers=None):
        """Register a delivered message
        
        Args:
            tracking_id: Tracking ID extracted from message
            sender_email: Sender email from headers
            folder: Folder where message was found (INBOX/Junk)
            headers: Optional full headers dict
        """
        if tracking_id in self.sent_messages:
            # Mark as delivered
            self.sent_messages[tracking_id]['delivered'] = True
            self.sent_messages[tracking_id]['delivery_folder'] = folder
            
            smtp_key = self.sent_messages[tracking_id]['smtp_key']
            self.smtp_stats[smtp_key]['delivered'] += 1
            self.smtp_stats[smtp_key]['folder'] = folder
        
        self.delivered_messages[tracking_id] = {
            'tracking_id': tracking_id,
            'sender_email': sender_email,
            'folder': folder,
            'headers': headers or {}
        }
    
    def _get_smtp_key(self, smtp_config):
        """Generate unique key for SMTP
        
        Args:
            smtp_config: SMTP configuration dict
            
        Returns:
            str: Unique SMTP key
        """
        return f"{smtp_config['host']}:{smtp_config['port']}:{smtp_config['username']}"
    
    def extract_tracking_id(self, text):
        """Extract tracking ID from text (subject or body)
        
        Args:
            text: Text to search
            
        Returns:
            str or None: Tracking ID if found
        """
        if not text:
            return None
        
        pattern = self.config.get_tracking_id_pattern()
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def get_sent_count(self):
        """Get total sent messages count
        
        Returns:
            int: Number of sent messages
        """
        return len(self.sent_messages)
    
    def get_delivered_count(self):
        """Get total delivered messages count
        
        Returns:
            int: Number of delivered messages
        """
        return len(self.delivered_messages)
    
    def get_delivery_rate(self):
        """Calculate delivery rate percentage
        
        Returns:
            float: Delivery rate (0-100)
        """
        total = len(self.sent_messages)
        if total == 0:
            return 0.0
        delivered = len(self.delivered_messages)
        return (delivered / total) * 100.0
    
    def get_inbox_count(self):
        """Count messages delivered to INBOX
        
        Returns:
            int: Number in INBOX
        """
        return sum(1 for msg in self.sent_messages.values() 
                   if msg['delivered'] and msg['delivery_folder'] == 'INBOX')
    
    def get_junk_count(self):
        """Count messages delivered to Junk
        
        Returns:
            int: Number in Junk
        """
        return sum(1 for msg in self.sent_messages.values() 
                   if msg['delivered'] and msg['delivery_folder'] and 'junk' in msg['delivery_folder'].lower())
    
    def get_verified_smtps(self):
        """Get list of verified (delivered) SMTPs
        
        Returns:
            list: List of tuples (smtp_config, folder)
        """
        verified = []
        seen_smtps = set()
        
        for msg in self.sent_messages.values():
            if msg['delivered']:
                smtp_key = msg['smtp_key']
                if smtp_key not in seen_smtps:
                    smtp_config = {
                        'host': msg['smtp_host'],
                        'port': msg['smtp_port'],
                        'username': msg['smtp_username'],
                        'password': msg.get('smtp_password', '')
                    }
                    verified.append((smtp_config, msg['delivery_folder']))
                    seen_smtps.add(smtp_key)
        
        return verified
    
    def get_failed_smtps(self):
        """Get list of failed (not delivered) SMTPs
        
        Returns:
            list: List of tuples (smtp_config, reason)
        """
        failed = []
        seen_smtps = set()
        
        for msg in self.sent_messages.values():
            smtp_key = msg['smtp_key']
            if not msg['delivered'] and smtp_key not in seen_smtps:
                smtp_config = {
                    'host': msg['smtp_host'],
                    'port': msg['smtp_port'],
                    'username': msg['smtp_username'],
                    'password': msg.get('smtp_password', '')
                }
                reason = "Not delivered"
                failed.append((smtp_config, reason))
                seen_smtps.add(smtp_key)
        
        return failed
    
    def get_smtp_statistics(self):
        """Get detailed statistics per SMTP
        
        Returns:
            list: List of dicts with SMTP stats
        """
        stats_list = []
        
        for smtp_key, stats in self.smtp_stats.items():
            delivery_rate = (stats['delivered'] / stats['sent'] * 100) if stats['sent'] > 0 else 0
            
            parts = smtp_key.split(':', 2)
            if len(parts) >= 3:
                stats_list.append({
                    'smtp': smtp_key,
                    'host': parts[0],
                    'port': parts[1],
                    'username': parts[2],
                    'sent': stats['sent'],
                    'delivered': stats['delivered'],
                    'delivery_rate': round(delivery_rate, 2),
                    'folder': stats['folder'] or 'N/A'
                })
        
        # Sort by delivery rate descending
        stats_list.sort(key=lambda x: x['delivery_rate'], reverse=True)
        return stats_list
    
    def get_summary_statistics(self):
        """Get summary statistics
        
        Returns:
            dict: Summary statistics
        """
        total_sent = len(self.sent_messages)
        total_delivered = len(self.delivered_messages)
        inbox_count = self.get_inbox_count()
        junk_count = self.get_junk_count()
        
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        inbox_rate = (inbox_count / total_delivered * 100) if total_delivered > 0 else 0
        junk_rate = (junk_count / total_delivered * 100) if total_delivered > 0 else 0
        
        return {
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'not_delivered': total_sent - total_delivered,
            'inbox_count': inbox_count,
            'junk_count': junk_count,
            'delivery_rate': round(delivery_rate, 2),
            'inbox_rate': round(inbox_rate, 2),
            'junk_rate': round(junk_rate, 2),
            'unique_smtps': len(self.smtp_stats)
        }
    
    def export_to_dict_list(self):
        """Export all messages to list of dicts (for JSON/CSV)
        
        Returns:
            list: List of message dicts
        """
        messages = []
        
        for tracking_id, msg in self.sent_messages.items():
            messages.append({
                'tracking_id': tracking_id,
                'smtp_host': msg['smtp_host'],
                'smtp_port': msg['smtp_port'],
                'smtp_username': msg['smtp_username'],
                'recipient': msg['recipient'],
                'timestamp': msg['timestamp'],
                'smtp_response': msg['smtp_response'],
                'delivered': msg['delivered'],
                'delivery_folder': msg['delivery_folder'] or 'Not Delivered'
            })
        
        return messages
    
    def import_from_dict_list(self, messages):
        """Import messages from list of dicts
        
        Args:
            messages: List of message dicts
        """
        for msg in messages:
            tracking_id = msg['tracking_id']
            
            smtp_config = {
                'host': msg['smtp_host'],
                'port': msg['smtp_port'],
                'username': msg['smtp_username'],
                'password': ''  # Not stored
            }
            
            self.register_sent_message(
                tracking_id,
                smtp_config,
                msg['recipient'],
                msg['timestamp'],
                msg['smtp_response']
            )
            
            if msg.get('delivered', False):
                self.register_delivered_message(
                    tracking_id,
                    msg['smtp_username'],
                    msg.get('delivery_folder', 'Unknown')
                )
    
    def clear_all(self):
        """Clear all tracking data"""
        self.sent_messages.clear()
        self.delivered_messages.clear()
        self.smtp_stats.clear()
    
    def __str__(self):
        return f"MessageTracker(sent={self.get_sent_count()}, delivered={self.get_delivered_count()})"
    
    def __repr__(self):
        return self.__str__()
