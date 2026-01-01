"""
Configuration Manager Module
Handles saving/loading configuration to/from JSON
"""
import json
import os
from datetime import datetime
from colorama import Fore, Style

class ConfigManager:
    """Manages configuration persistence for GUI Mailer"""
    
    def __init__(self, config_file='gui_mailer_config.json'):
        self.config_file = config_file
        self._pending_config = None
        
    def save_config(self, gui_instance):
        """Save configuration to JSON file - LIMITED to prevent bloat"""
        try:
            # CRITICAL: Limit collections to prevent 200MB+ config files
            MAX_EMAILS = 500000  # Max 500K emails (increased from 100K)
            
            verified_froms = gui_instance.verified_froms[:MAX_EMAILS] if gui_instance.verified_froms else []
            unverified_froms = gui_instance.unverified_froms[:MAX_EMAILS] if gui_instance.unverified_froms else []
            collected_from = gui_instance.collected_from_emails[:MAX_EMAILS] if gui_instance.collected_from_emails else []
            
            # Warn if truncating
            if len(gui_instance.verified_froms) > MAX_EMAILS:
                print(f"{Fore.YELLOW}⚠ WARNING: Truncating verified_froms from {len(gui_instance.verified_froms)} to {MAX_EMAILS}{Style.RESET_ALL}")
            if len(gui_instance.unverified_froms) > MAX_EMAILS:
                print(f"{Fore.YELLOW}⚠ WARNING: Truncating unverified_froms from {len(gui_instance.unverified_froms)} to {MAX_EMAILS}{Style.RESET_ALL}")
            if len(gui_instance.collected_from_emails) > MAX_EMAILS:
                print(f"{Fore.YELLOW}⚠ WARNING: Truncating collected_from_emails from {len(gui_instance.collected_from_emails)} to {MAX_EMAILS}{Style.RESET_ALL}")
            
            config = {
                'thunderbird_path': gui_instance.thunderbird_path_var.get() if hasattr(gui_instance, 'thunderbird_path_var') else gui_instance.thunderbird_path,
                'fake_from_counter': gui_instance.fake_from_counter,
                'domain_from': gui_instance.domain_from_var.get() if hasattr(gui_instance, 'domain_from_var') else '',
                'domain_auth': gui_instance.domain_auth_var.get() if hasattr(gui_instance, 'domain_auth_var') else '',
                'sender_name': gui_instance.sender_name_var.get() if hasattr(gui_instance, 'sender_name_var') else '',
                'email_subject': gui_instance.subject_var.get() if hasattr(gui_instance, 'subject_var') else '',
                'threads': gui_instance.threads_var.get() if hasattr(gui_instance, 'threads_var') else 5,
                'delay_between': gui_instance.delay_var.get() if hasattr(gui_instance, 'delay_var') else 1,
                'verified_froms': verified_froms,
                'unverified_froms': unverified_froms,
                'collected_from_emails': collected_from,
                # DON'T save textarea contents - causes 200MB+ files
                # Users can use Load/Save buttons per textarea instead
                'last_saved': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            print(f"{Fore.GREEN}[SAVE] Configuration saved{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Failed saving config: {e}{Style.RESET_ALL}")
    
    def load_config(self, gui_instance):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Load values
                gui_instance.thunderbird_path = config.get('thunderbird_path', gui_instance.thunderbird_path)
                gui_instance.fake_from_counter = config.get('fake_from_counter', 0)
                gui_instance.verified_froms = config.get('verified_froms', [])
                gui_instance.unverified_froms = config.get('unverified_froms', [])
                gui_instance.collected_from_emails = config.get('collected_from_emails', [])
                
                print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[CONFIG] Configuration loaded successfully{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Thunderbird Path: {gui_instance.thunderbird_path}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Fake From Counter: {gui_instance.fake_from_counter}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Verified Froms: {len(gui_instance.verified_froms)}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Unverified Froms: {len(gui_instance.unverified_froms)}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Last Saved: {config.get('last_saved', 'Unknown')}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
                
                # Store for later application to UI
                self._pending_config = config
                
        except Exception as e:
            print(f"{Fore.YELLOW}[WARNING] No previous config found (first run){Style.RESET_ALL}")
    
    def apply_pending_config(self, gui_instance):
        """Apply config values to UI elements after they're created"""
        if self._pending_config:
            config = self._pending_config
            
            # Apply to UI elements
            if hasattr(gui_instance, 'domain_from_var'):
                gui_instance.domain_from_var.set(config.get('domain_from', 'charter.net'))
            if hasattr(gui_instance, 'domain_auth_var'):
                gui_instance.domain_auth_var.set(config.get('domain_auth', 'altona.fr'))
            if hasattr(gui_instance, 'sender_name_var'):
                gui_instance.sender_name_var.set(config.get('sender_name', ''))
            if hasattr(gui_instance, 'subject_var'):
                gui_instance.subject_var.set(config.get('email_subject', ''))
            if hasattr(gui_instance, 'threads_var'):
                gui_instance.threads_var.set(config.get('threads', 5))
            if hasattr(gui_instance, 'delay_var'):
                gui_instance.delay_var.set(config.get('delay_between', 1))
            if hasattr(gui_instance, 'fake_from_label'):
                gui_instance.fake_from_label.config(text=str(gui_instance.fake_from_counter))
            
            # Restore textarea contents
            if hasattr(gui_instance, 'smtp_text') and config.get('smtp_servers_text'):
                gui_instance.smtp_text.delete(1.0, 'end')
                gui_instance.smtp_text.insert(1.0, config.get('smtp_servers_text'))
            
            if hasattr(gui_instance, 'recipients_text') and config.get('recipients_text'):
                gui_instance.recipients_text.delete(1.0, 'end')
                gui_instance.recipients_text.insert(1.0, config.get('recipients_text'))
            
            # DON'T load from_addresses_text - prevents loading millions of emails
            # Users should use "Load from File" button if needed
            
            if hasattr(gui_instance, 'template_text') and config.get('email_template'):
                gui_instance.template_text.delete(1.0, 'end')
                gui_instance.template_text.insert(1.0, config.get('email_template'))
            
            self._pending_config = None
            print(f"{Fore.GREEN}[APPLY] Configuration and data restored{Style.RESET_ALL}")
