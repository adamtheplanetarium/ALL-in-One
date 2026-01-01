"""
SMTP Manager Module
Handles SMTP server rotation, failure tracking, and automatic cleanup
"""
import threading
from colorama import Fore, Style

class SMTPManager:
    """Manages SMTP servers with automatic failure cleanup"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        # Use GUI instance's existing locks and variables for compatibility
        self.failed_servers = gui_instance.failed_servers
        self.failed_servers_lock = gui_instance.failed_servers_lock
        self.smtp_server_lock = gui_instance.smtp_server_lock
        self.max_failures_per_server = 10  # Increased from 2 to 10 - only remove consistently failing SMTPs
        self.success_counters = {}  # Track successful sends per server
        
    def get_next_smtp(self):
        """Get next available SMTP server, auto-removing failed ones"""
        attempts = 0
        with self.smtp_server_lock:
            while attempts < len(self.gui.smtp_servers):
                if self.gui.smtp_server_index >= len(self.gui.smtp_servers):
                    self.gui.smtp_server_index = 0
                    
                current_smtp = self.gui.smtp_servers[self.gui.smtp_server_index]
                self.gui.smtp_server_index += 1
                
                # Check if this server has failed too many times
                server_key = f"{current_smtp['host']}:{current_smtp['port']}"
                current_failures = self.failed_servers.get(server_key, 0)
                
                if current_failures < self.max_failures_per_server:
                    return current_smtp, server_key
                else:
                    # Auto-remove from list
                    self._auto_remove_failed_server(server_key)
                    attempts += 1
            
            # All servers failed
            return None, None
    
    def mark_smtp_failed(self, server_key):
        """Mark SMTP server as failed and auto-remove if threshold reached"""
        with self.failed_servers_lock:
            self.failed_servers[server_key] = self.failed_servers.get(server_key, 0) + 1
            
            if self.failed_servers[server_key] >= self.max_failures_per_server:
                self.gui.log_message(f"⚠ SMTP {server_key} AUTO-REMOVED after {self.failed_servers[server_key]} failures", 'warning')
                self.gui.console_print(f"⚠ AUTO-REMOVING FAILED SMTP: {server_key}", 'red')
                self._auto_remove_failed_server(server_key)
    
    def mark_smtp_success(self, server_key):
        """Mark SMTP server as successful - reset failure count after consecutive successes"""
        if not server_key:
            return
        
        with self.failed_servers_lock:
            # Track success
            self.success_counters[server_key] = self.success_counters.get(server_key, 0) + 1
            
            # Reset failures after 3 consecutive successes
            if self.success_counters[server_key] >= 3 and server_key in self.failed_servers:
                if self.failed_servers[server_key] > 0:
                    self.failed_servers[server_key] = max(0, self.failed_servers[server_key] - 1)
                    self.success_counters[server_key] = 0  # Reset success counter
    
    def _auto_remove_failed_server(self, server_key):
        """Automatically remove failed server from SMTP list"""
        try:
            # Parse server_key (format: "host:port")
            host, port = server_key.split(':')
            
            # Get current SMTP text
            current_text = self.gui.smtp_text.get(1.0, 'end').strip()
            lines = [line.strip() for line in current_text.split('\n') if line.strip()]
            
            # Filter out the failed server
            cleaned_lines = []
            for line in lines:
                should_keep = True
                
                if ':' in line and line.count(':') >= 3:
                    # New format: username:password:host:port
                    parts = line.split(':')
                    if len(parts) >= 4:
                        line_host = parts[2].strip()
                        line_port = parts[3].strip()
                        if line_host == host and line_port == port:
                            should_keep = False
                            print(f"{Fore.RED}[SMTP-CLEANUP] Removed: {line}{Style.RESET_ALL}")
                            
                elif ',' in line:
                    # Old format: host,port,username,password
                    parts = line.split(',')
                    if len(parts) >= 4:
                        line_host = parts[0].strip()
                        line_port = parts[1].strip()
                        if line_host == host and line_port == port:
                            should_keep = False
                            print(f"{Fore.RED}[SMTP-CLEANUP] Removed: {line}{Style.RESET_ALL}")
                
                if should_keep:
                    cleaned_lines.append(line)
            
            # Update textarea in main thread
            def update_ui():
                self.gui.smtp_text.delete(1.0, 'end')
                self.gui.smtp_text.insert(1.0, '\n'.join(cleaned_lines))
                self.gui.parse_smtp_servers()
            
            self.gui.root.after(0, update_ui)
            
        except Exception as e:
            print(f"{Fore.RED}[SMTP-CLEANUP] Error removing failed server: {e}{Style.RESET_ALL}")
    
    def reset_failures(self):
        """Reset all failure and success counters"""
        with self.failed_servers_lock:
            self.failed_servers = {}
            self.success_counters = {}  # Also reset success counters
