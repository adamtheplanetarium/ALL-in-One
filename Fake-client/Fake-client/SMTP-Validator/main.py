"""
SMTP Validator - Main GUI Application
Tests SMTP servers and verifies delivery via IMAP
Line count: ~590 lines
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from datetime import datetime

# Import our modules
from config_handler import ConfigHandler
from file_handler import FileHandler
from tracker import MessageTracker
from smtp_sender import SMTPSender
from imap_checker import IMAPChecker

class SMTPValidatorGUI:
    """Main GUI application for SMTP Validator"""
    
    def __init__(self, root):
        """Initialize GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("SMTP Validator - Test & Verify SMTP Delivery")
        self.root.geometry("1400x900")
        
        # Initialize modules
        self.config = ConfigHandler()
        self.file_handler = FileHandler(self.config)
        self.tracker = MessageTracker(self.config)
        self.smtp_sender = SMTPSender(self.config, self.file_handler, self.tracker)
        self.imap_checker = IMAPChecker(self.config, self.tracker)
        
        # State variables
        self.smtps_list = []
        self.smtps_file_path = ""
        self.recipients_list = []
        self.recipients_file_path = ""
        
        # Threads
        self.sending_thread = None
        self.checking_thread = None
        
        # Create sample files
        self.file_handler.create_sample_files()
        
        # Create GUI
        self.create_gui()
        
        # Protocol for closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_gui(self):
        """Create GUI layout"""
        # Main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_sending_tab()
        self.create_verification_tab()
        self.create_results_tab()
        self.create_settings_tab()
    
    def create_sending_tab(self):
        """Create SMTP Sending tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📤 SMTP Sending")
        
        # Top frame - SMTP Input
        top_frame = ttk.LabelFrame(tab, text="SMTP Servers", padding=10)
        top_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=False)
        
        # SMTP textarea and buttons
        smtp_header = ttk.Frame(top_frame)
        smtp_header.pack(fill=tk.X)
        ttk.Label(smtp_header, text="Enter SMTPs (one per line: username:password:host:port)").pack(side=tk.LEFT)
        ttk.Button(smtp_header, text="📁 Load File", command=self.load_smtps_file).pack(side=tk.RIGHT, padx=2)
        ttk.Button(smtp_header, text="✓ Parse SMTPs", command=self.parse_smtps).pack(side=tk.RIGHT, padx=2)
        
        self.smtp_text = scrolledtext.ScrolledText(top_frame, height=6, bg='#2b2b2b', fg='#ffffff', font=('Courier New', 9))
        self.smtp_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.smtps_label = ttk.Label(top_frame, text="0 SMTPs loaded", foreground='gray')
        self.smtps_label.pack()
        
        # Recipients frame
        recip_frame = ttk.LabelFrame(tab, text="Recipients", padding=10)
        recip_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=False)
        
        # Recipients textarea and buttons
        recip_header = ttk.Frame(recip_frame)
        recip_header.pack(fill=tk.X)
        ttk.Label(recip_header, text="Enter recipient emails (one per line)").pack(side=tk.LEFT)
        ttk.Button(recip_header, text="📁 Load File", command=self.load_recipients_file).pack(side=tk.RIGHT, padx=2)
        ttk.Button(recip_header, text="✓ Parse Recipients", command=self.parse_recipients).pack(side=tk.RIGHT, padx=2)
        
        self.recipients_text = scrolledtext.ScrolledText(recip_frame, height=4, bg='#2b2b2b', fg='#ffffff', font=('Courier New', 9))
        self.recipients_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.recipients_label = ttk.Label(recip_frame, text="0 recipients loaded", foreground='gray')
        self.recipients_label.pack()
        
        # Control frame
        control_frame = ttk.LabelFrame(tab, text="Sending Control", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Single row with all controls
        ttk.Label(control_frame, text="Threads:").pack(side=tk.LEFT, padx=5)
        self.threads_var = tk.IntVar(value=self.config.get('smtp', 'threads', default=50))
        ttk.Scale(control_frame, from_=1, to=100, variable=self.threads_var, orient=tk.HORIZONTAL, length=150).pack(side=tk.LEFT)
        ttk.Label(control_frame, textvariable=self.threads_var, width=3).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        self.send_btn = ttk.Button(control_frame, text="▶ Start Sending", command=self.start_sending)
        self.send_btn.pack(side=tk.LEFT, padx=10)
        self.stop_send_btn = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_sending, state=tk.DISABLED)
        self.stop_send_btn.pack(side=tk.LEFT, padx=2)
        
        # Status
        self.send_status_label = ttk.Label(control_frame, text="Ready")
        self.send_status_label.pack(side=tk.LEFT, padx=20)
        
        # Progress bar
        progress_frame = ttk.Frame(tab)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        self.send_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.send_progress.pack(fill=tk.X)
        
        # Log
        log_frame = ttk.LabelFrame(tab, text="Sending Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.send_log = scrolledtext.ScrolledText(log_frame, height=20, bg='#1e1e1e', fg='#00ff00', font=('Courier New', 9))
        self.send_log.pack(fill=tk.BOTH, expand=True)
    
    def create_verification_tab(self):
        """Create IMAP Verification tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📬 IMAP Verification")
        
        # IMAP Settings
        settings_frame = ttk.LabelFrame(tab, text="IMAP Settings (Thunderbird-style)", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Preset buttons
        preset_frame = ttk.Frame(settings_frame)
        preset_frame.grid(row=0, column=0, columnspan=4, pady=5)
        ttk.Label(preset_frame, text="Quick Setup:").pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="AT&T (Default)", command=lambda: self.set_imap_preset('att')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Gmail", command=lambda: self.set_imap_preset('gmail')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Outlook", command=lambda: self.set_imap_preset('outlook')).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Yahoo", command=lambda: self.set_imap_preset('yahoo')).pack(side=tk.LEFT, padx=2)
        
        # Host
        ttk.Label(settings_frame, text="Host:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.imap_host_var = tk.StringVar(value=self.config.get('imap', 'host', default=''))
        ttk.Entry(settings_frame, textvariable=self.imap_host_var, width=40).grid(row=1, column=1, padx=10, sticky=tk.EW)
        
        # Port & SSL
        ttk.Label(settings_frame, text="Port:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        self.imap_port_var = tk.IntVar(value=self.config.get('imap', 'port', default=993))
        ttk.Entry(settings_frame, textvariable=self.imap_port_var, width=10).grid(row=1, column=3, padx=10)
        
        self.imap_ssl_var = tk.BooleanVar(value=self.config.get('imap', 'use_ssl', default=True))
        ttk.Checkbutton(settings_frame, text="Use SSL", variable=self.imap_ssl_var, command=self.toggle_ssl).grid(row=1, column=4, padx=5)
        
        # Username
        ttk.Label(settings_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.imap_user_var = tk.StringVar(value=self.config.get('imap', 'username', default=''))
        ttk.Entry(settings_frame, textvariable=self.imap_user_var, width=40).grid(row=2, column=1, padx=10, sticky=tk.EW)
        
        # Password
        ttk.Label(settings_frame, text="Password:").grid(row=2, column=2, sticky=tk.W, padx=(20, 0))
        self.imap_pass_var = tk.StringVar(value=self.config.get('imap', 'password', default=''))
        ttk.Entry(settings_frame, textvariable=self.imap_pass_var, width=30, show='*').grid(row=2, column=3, columnspan=2, padx=10, sticky=tk.EW)
        
        # Buttons
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.grid(row=3, column=0, columnspan=5, pady=10)
        ttk.Button(btn_frame, text="💾 Save Settings", command=self.save_imap_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔌 Test Connection", command=self.test_imap_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📁 Detect Folders", command=self.detect_imap_folders).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❓ App Password Help", command=self.show_app_password_help).pack(side=tk.LEFT, padx=5)
        
        # Control frame
        control_frame = ttk.LabelFrame(tab, text="Verification Control", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(control_frame, text="Check Folders:").pack(side=tk.LEFT, padx=10)
        self.check_inbox_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="INBOX", variable=self.check_inbox_var).pack(side=tk.LEFT)
        self.check_junk_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Junk/Spam", variable=self.check_junk_var).pack(side=tk.LEFT, padx=10)
        
        self.check_btn = ttk.Button(control_frame, text="▶ Start Verification", command=self.start_verification)
        self.check_btn.pack(side=tk.LEFT, padx=20)
        self.stop_check_btn = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_verification, state=tk.DISABLED)
        self.stop_check_btn.pack(side=tk.LEFT)
        
        # Log
        log_frame = ttk.LabelFrame(tab, text="Verification Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.verify_log = scrolledtext.ScrolledText(log_frame, height=20, bg='#1e1e1e', fg='#00ffff', font=('Courier New', 9))
        self.verify_log.pack(fill=tk.BOTH, expand=True)
    
    def create_results_tab(self):
        """Create Results tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Results")
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(tab, text="Summary Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, bg='#f0f0f0', font=('Courier New', 10))
        self.stats_text.pack(fill=tk.X)
        
        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="📥 Export Verified SMTPs", command=self.export_verified_smtps).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📥 Export Failed SMTPs", command=self.export_failed_smtps).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Export CSV Report", command=self.export_csv_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh Results", command=self.refresh_results).pack(side=tk.LEFT, padx=20)
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self.clear_results).pack(side=tk.LEFT)
        
        # Results table
        table_frame = ttk.LabelFrame(tab, text="Detailed Results", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview
        columns = ('SMTP', 'Host', 'Port', 'Username', 'Status', 'Folder')
        self.results_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Column headings
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def create_settings_tab(self):
        """Create Settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Settings")
        
        settings_frame = ttk.LabelFrame(tab, text="Application Settings", padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # SMTP Timeout
        ttk.Label(settings_frame, text="SMTP Timeout (seconds):").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.smtp_timeout_var = tk.IntVar(value=self.config.get('smtp', 'timeout', default=10))
        ttk.Entry(settings_frame, textvariable=self.smtp_timeout_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Retry attempts
        ttk.Label(settings_frame, text="Retry Attempts:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.retry_var = tk.IntVar(value=self.config.get('smtp', 'retry_attempts', default=1))
        ttk.Entry(settings_frame, textvariable=self.retry_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Save button
        ttk.Button(settings_frame, text="💾 Save All Settings", command=self.save_all_settings).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Info
        info_text = """
SMTP Validator - Test & Verify SMTP Delivery

How to use:
1. Load your SMTP servers file (format: host:port:username:password)
2. Load recipient email addresses
3. Click 'Start Sending' to send test messages
4. Configure IMAP settings for recipient inbox
5. Click 'Start Verification' to check delivered messages
6. View results and export working SMTPs

Version: 1.0
        """
        info_label = ttk.Label(settings_frame, text=info_text, justify=tk.LEFT, font=('Arial', 9))
        info_label.grid(row=3, column=0, columnspan=2, pady=20, sticky=tk.W)
    
    # Event handlers
    def parse_smtps(self):
        """Parse SMTPs from textarea"""
        text = self.smtp_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter SMTP servers first!")
            return
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.smtps_list = []
        
        for line in lines:
            try:
                parts = line.split(':')
                if len(parts) == 4:
                    # Format: username:password:host:port
                    self.smtps_list.append({
                        'username': parts[0],
                        'password': parts[1],
                        'host': parts[2],
                        'port': int(parts[3])
                    })
            except:
                pass
        
        if self.smtps_list:
            self.smtps_label.config(text=f"✓ {len(self.smtps_list)} SMTPs loaded", foreground='green')
            self.log_to_sending(f"✓ Parsed {len(self.smtps_list)} SMTPs from textarea")
        else:
            self.smtps_label.config(text="✗ No valid SMTPs found", foreground='red')
            messagebox.showerror("Error", "No valid SMTPs found. Format: username:password:host:port")
    
    def parse_recipients(self):
        """Parse recipients from textarea"""
        text = self.recipients_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter recipient emails first!")
            return
        
        lines = [line.strip() for line in text.split('\n') if line.strip() and '@' in line]
        self.recipients_list = lines
        
        if self.recipients_list:
            self.recipients_label.config(text=f"✓ {len(self.recipients_list)} recipients loaded", foreground='green')
            self.log_to_sending(f"✓ Parsed {len(self.recipients_list)} recipients from textarea")
        else:
            self.recipients_label.config(text="✗ No valid emails found", foreground='red')
            messagebox.showerror("Error", "No valid email addresses found")
    
    def load_smtps_file(self):
        """Load SMTPs from file"""
        file_path = filedialog.askopenfilename(
            title="Select SMTP File",
            initialdir=self.config.get('paths', 'data_folder'),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            self.smtps_list = self.file_handler.load_smtps(file_path)
            self.smtps_file_path = file_path
            
            # Populate textarea with username:password:host:port format
            self.smtp_text.delete(1.0, tk.END)
            for smtp in self.smtps_list:
                self.smtp_text.insert(tk.END, f"{smtp['username']}:{smtp['password']}:{smtp['host']}:{smtp['port']}\n")
            
            self.smtps_label.config(text=f"✓ {len(self.smtps_list)} SMTPs loaded from file", foreground='green')
            self.log_to_sending(f"✓ Loaded {len(self.smtps_list)} SMTPs from file")
    
    def load_recipients_file(self):
        """Load recipients from file"""
        file_path = filedialog.askopenfilename(
            title="Select Recipients File",
            initialdir=self.config.get('paths', 'data_folder'),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            self.recipients_list = self.file_handler.load_recipients(file_path)
            self.recipients_file_path = file_path
            
            # Populate textarea
            self.recipients_text.delete(1.0, tk.END)
            for recipient in self.recipients_list:
                self.recipients_text.insert(tk.END, f"{recipient}\n")
            
            self.recipients_label.config(text=f"✓ {len(self.recipients_list)} recipients loaded from file", foreground='green')
            self.log_to_sending(f"✓ Loaded {len(self.recipients_list)} recipients from file")
    
    def start_sending(self):
        """Start sending test messages"""
        if not self.smtps_list:
            messagebox.showerror("Error", "Please load SMTP servers first!")
            return
        
        if not self.recipients_list:
            messagebox.showerror("Error", "Please load recipients first!")
            return
        
        # Update config
        self.config.set('smtp', 'threads', value=self.threads_var.get())
        
        # Disable button
        self.send_btn.config(state=tk.DISABLED)
        self.stop_send_btn.config(state=tk.NORMAL)
        
        # Clear log
        self.send_log.delete(1.0, tk.END)
        self.log_to_sending("="*60)
        self.log_to_sending("STARTING SMTP SENDING")
        self.log_to_sending(f"SMTPs: {len(self.smtps_list)}")
        self.log_to_sending(f"Recipients: {len(self.recipients_list)}")
        self.log_to_sending(f"Threads: {self.threads_var.get()}")
        self.log_to_sending("="*60)
        
        # Start thread
        self.sending_thread = threading.Thread(target=self._sending_thread, daemon=True)
        self.sending_thread.start()
    
    def _sending_thread(self):
        """Sending thread"""
        def progress_callback(current, total, status_msg):
            self.root.after(0, self._update_send_progress, current, total, status_msg)
        
        result = self.smtp_sender.send_batch(self.smtps_list, self.recipients_list, progress_callback)
        
        self.root.after(0, self._sending_complete, result)
    
    def _update_send_progress(self, current, total, status_msg):
        """Update sending progress"""
        self.send_progress['maximum'] = total
        self.send_progress['value'] = current
        # Extract counts from the message if available
        sent = self.smtp_sender.sent_count
        failed = self.smtp_sender.failed_count
        self.send_status_label.config(text=f"✓ {sent} sent | ✗ {failed} failed | {current}/{total}")
        self.log_to_sending(status_msg)
    
    def _sending_complete(self, result):
        """Sending completed"""
        self.send_btn.config(state=tk.NORMAL)
        self.stop_send_btn.config(state=tk.DISABLED)
        
        self.log_to_sending("="*60)
        self.log_to_sending("SENDING COMPLETE")
        self.log_to_sending(f"✓ Successfully Sent: {result['sent']}")
        self.log_to_sending(f"✗ Failed: {result['failed']}")
        self.log_to_sending(f"Total Processed: {result['completed']}/{result['total']}")
        self.log_to_sending("="*60)
        
        # Ask if user wants to verify delivery now
        if result['sent'] > 0:
            verify_now = messagebox.askyesno(
                "Sending Complete",
                f"Sending complete!\n\n✓ Successfully Sent: {result['sent']}\n✗ Failed: {result['failed']}\n\nWould you like to verify delivery via IMAP now?\n(Check which SMTPs went to INBOX vs JUNK)"
            )
            if verify_now:
                # Switch to verification tab
                self.notebook.select(1)  # Index 1 is verification tab
                self.log_to_verify("Auto-started verification after sending completed")
        else:
            messagebox.showinfo(
                "Sending Complete",
                f"Sending complete!\n\n✓ Successfully Sent: {result['sent']}\n✗ Failed: {result['failed']}"
            )
    
    def stop_sending(self):
        """Stop sending"""
        self.smtp_sender.stop()
        self.log_to_sending("⏹ Stop requested...")
    
    def set_imap_preset(self, provider):
        """Set IMAP preset for common providers"""
        presets = {
            'att': {'host': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True, 'user': 'boxer204@att.net', 'pass': 'lappbauhnrqhtpop'},
            'gmail': {'host': 'imap.gmail.com', 'port': 993, 'ssl': True},
            'outlook': {'host': 'outlook.office365.com', 'port': 993, 'ssl': True},
            'yahoo': {'host': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}
        }
        
        if provider in presets:
            preset = presets[provider]
            self.imap_host_var.set(preset['host'])
            self.imap_port_var.set(preset['port'])
            self.imap_ssl_var.set(preset['ssl'])
            if 'user' in preset:
                self.imap_user_var.set(preset['user'])
            if 'pass' in preset:
                self.imap_pass_var.set(preset['pass'])
            self.log_to_verify(f"✓ Applied {provider.upper()} IMAP preset")
    
    def toggle_ssl(self):
        """Toggle SSL and adjust port"""
        if self.imap_ssl_var.get():
            if self.imap_port_var.get() == 143:
                self.imap_port_var.set(993)
        else:
            if self.imap_port_var.get() == 993:
                self.imap_port_var.set(143)
    
    def detect_imap_folders(self):
        """Detect available IMAP folders (Thunderbird-style)"""
        self.save_imap_settings()
        
        success, msg = self.imap_checker.connect()
        if not success:
            messagebox.showerror("Connection Failed", msg)
            return
        
        try:
            folders = self.imap_checker.get_folders()
            self.imap_checker.disconnect()
            
            folder_list = "\n".join(folders[:20])  # Show first 20
            if len(folders) > 20:
                folder_list += f"\n... and {len(folders) - 20} more"
            
            messagebox.showinfo("Detected Folders", f"Found {len(folders)} folders:\n\n{folder_list}")
            self.log_to_verify(f"✓ Detected {len(folders)} IMAP folders")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect folders: {str(e)}")
    
    def show_app_password_help(self):
        """Show help for generating app passwords"""
        help_text = """🔐 AT&T/Yahoo App Password Setup

AT&T email uses Yahoo infrastructure and requires an APP PASSWORD (not your regular password).

📋 Steps to Generate App Password:

1. Go to: https://login.yahoo.com/account/security

2. Sign in with boxer204@att.net

3. Scroll to "Generate app password"

4. Select "Other App" → Enter "SMTP Validator"

5. Click "Generate" → Copy the 16-character password

6. Use that password in the IMAP settings (replace current password)

⚠️ Note: Regular passwords don't work with IMAP anymore.
You MUST use an app-specific password for security.

📧 Other Providers:
• Gmail: https://myaccount.google.com/apppasswords
• Outlook: https://account.microsoft.com/security
"""
        messagebox.showinfo("App Password Help", help_text)
        self.log_to_verify("ℹ️ Showed app password help")
    
    def save_imap_settings(self):
        """Save IMAP settings"""
        self.config.set('imap', 'host', value=self.imap_host_var.get())
        self.config.set('imap', 'port', value=self.imap_port_var.get())
        self.config.set('imap', 'username', value=self.imap_user_var.get())
        self.config.set('imap', 'password', value=self.imap_pass_var.get())
        self.config.set('imap', 'use_ssl', value=self.imap_ssl_var.get())
        self.config.save_config()
        
        self.log_to_verify(f"✓ IMAP settings saved")
    
    def test_imap_connection(self):
        """Test IMAP connection"""
        # Save first (without popup)
        self.config.set('imap', 'host', value=self.imap_host_var.get())
        self.config.set('imap', 'port', value=self.imap_port_var.get())
        self.config.set('imap', 'username', value=self.imap_user_var.get())
        self.config.set('imap', 'password', value=self.imap_pass_var.get())
        self.config.set('imap', 'use_ssl', value=self.imap_ssl_var.get())
        self.config.save_config()
        
        self.log_to_verify("="*60)
        self.log_to_verify("TESTING IMAP CONNECTION")
        self.log_to_verify(f"Host: {self.imap_host_var.get()}")
        self.log_to_verify(f"Port: {self.imap_port_var.get()}")
        self.log_to_verify(f"User: {self.imap_user_var.get()}")
        self.log_to_verify(f"SSL: {'Enabled' if self.imap_ssl_var.get() else 'Disabled'}")
        self.log_to_verify("Connecting...")
        
        # Test
        success, msg = self.imap_checker.connect()
        
        self.log_to_verify(msg)
        self.log_to_verify("="*60)
        
        if success:
            messagebox.showinfo("✅ Connection Successful", msg)
            self.imap_checker.disconnect()
        else:
            messagebox.showerror("❌ Connection Failed", msg)
    
    def start_verification(self):
        """Start IMAP verification"""
        # Check settings
        is_valid, error_msg = self.config.validate_imap_config()
        if not is_valid:
            messagebox.showerror("Error", f"Invalid IMAP settings:\n{error_msg}")
            return
        
        # Disable button
        self.check_btn.config(state=tk.DISABLED)
        self.stop_check_btn.config(state=tk.NORMAL)
        
        # Clear log
        self.verify_log.delete(1.0, tk.END)
        self.log_to_verify("="*60)
        self.log_to_verify("STARTING IMAP VERIFICATION")
        self.log_to_verify("="*60)
        
        # Start thread
        self.checking_thread = threading.Thread(target=self._verification_thread, daemon=True)
        self.checking_thread.start()
    
    def _verification_thread(self):
        """Verification thread"""
        def progress_callback(status_msg):
            self.root.after(0, self.log_to_verify, status_msg)
        
        result = self.imap_checker.verify_delivery(progress_callback)
        
        self.root.after(0, self._verification_complete, result)
    
    def _verification_complete(self, result):
        """Verification completed"""
        self.check_btn.config(state=tk.NORMAL)
        self.stop_check_btn.config(state=tk.DISABLED)
        
        if 'error' in result:
            self.log_to_verify(f"✗ Error: {result['error']}")
            messagebox.showerror("Error", result['error'])
        else:
            stats = result.get('statistics', {})
            inbox_count = stats.get('inbox_count', 0)
            junk_count = stats.get('junk_count', 0)
            
            self.log_to_verify("="*60)
            self.log_to_verify("VERIFICATION COMPLETE")
            self.log_to_verify(f"Total Matched: {result['total_matched']}")
            self.log_to_verify(f"✓ INBOX: {inbox_count} messages (Delivered successfully!)")
            self.log_to_verify(f"⚠ JUNK/SPAM: {junk_count} messages (Filtered as spam)")
            if inbox_count + junk_count > 0:
                inbox_rate = (inbox_count / (inbox_count + junk_count)) * 100
                self.log_to_verify(f"Inbox Rate: {inbox_rate:.1f}%")
            self.log_to_verify("="*60)
            
            # Refresh results
            self.refresh_results()
            
            messagebox.showinfo(
                "Verification Complete",
                f"Verification complete!\n\nTotal Matched: {result['total_matched']}\n✓ INBOX: {inbox_count}\n⚠ JUNK/SPAM: {junk_count}\n\nGo to Results tab to export verified SMTPs."
            )
    
    def stop_verification(self):
        """Stop verification"""
        self.imap_checker.stop()
        self.log_to_verify("⏹ Stop requested...")
    
    def refresh_results(self):
        """Refresh results display"""
        # Get statistics
        stats = self.tracker.get_summary_statistics()
        
        # Update stats text
        self.stats_text.delete(1.0, tk.END)
        stats_str = f"""
╔══════════════════════════════════════════════╗
║         SMTP VALIDATION RESULTS              ║
╠══════════════════════════════════════════════╣
║ Total Sent:          {stats['total_sent']:6d}                 ║
║ Total Delivered:     {stats['total_delivered']:6d}                 ║
║ Not Delivered:       {stats['not_delivered']:6d}                 ║
║ Inbox Count:         {stats['inbox_count']:6d}                 ║
║ Junk Count:          {stats['junk_count']:6d}                 ║
║ Delivery Rate:       {stats['delivery_rate']:6.2f}%               ║
║ Inbox Rate:          {stats['inbox_rate']:6.2f}%               ║
║ Junk Rate:           {stats['junk_rate']:6.2f}%               ║
╚══════════════════════════════════════════════╝
        """
        self.stats_text.insert(1.0, stats_str)
        
        # Update results table
        self.results_tree.delete(*self.results_tree.get_children())
        
        smtp_stats = self.tracker.get_smtp_statistics()
        for stat in smtp_stats:
            status = "✓ Delivered" if stat['delivered'] > 0 else "✗ Not Delivered"
            self.results_tree.insert('', tk.END, values=(
                stat['smtp'],
                stat['host'],
                stat['port'],
                stat['username'],
                status,
                stat['folder']
            ))
    
    def export_verified_smtps(self):
        """Export verified SMTPs"""
        verified = self.tracker.get_verified_smtps()
        
        if not verified:
            messagebox.showinfo("Info", "No verified SMTPs to export")
            return
        
        success = self.file_handler.save_verified_smtps(verified)
        
        if success:
            file_path = self.config.get_full_path('verified_smtps_file')
            messagebox.showinfo("Success", f"Exported {len(verified)} verified SMTPs to:\n{file_path}")
    
    def export_failed_smtps(self):
        """Export failed SMTPs"""
        failed = self.tracker.get_failed_smtps()
        
        if not failed:
            messagebox.showinfo("Info", "No failed SMTPs to export")
            return
        
        success = self.file_handler.save_failed_smtps(failed)
        
        if success:
            file_path = self.config.get_full_path('failed_smtps_file')
            messagebox.showinfo("Success", f"Exported {len(failed)} failed SMTPs to:\n{file_path}")
    
    def export_csv_report(self):
        """Export CSV report"""
        smtp_stats = self.tracker.get_smtp_statistics()
        
        if not smtp_stats:
            messagebox.showinfo("Info", "No data to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save CSV Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            success = self.file_handler.export_csv_report(smtp_stats, file_path)
            if success:
                messagebox.showinfo("Success", f"Exported CSV report to:\n{file_path}")
    
    def clear_results(self):
        """Clear all results"""
        if messagebox.askyesno("Confirm", "Clear all results and tracking data?"):
            self.tracker.clear_all()
            self.refresh_results()
            self.send_log.delete(1.0, tk.END)
            self.verify_log.delete(1.0, tk.END)
            messagebox.showinfo("Cleared", "All results cleared!")
    
    def save_all_settings(self):
        """Save all settings"""
        self.config.set('smtp', 'timeout', value=self.smtp_timeout_var.get())
        self.config.set('smtp', 'retry_attempts', value=self.retry_var.get())
        self.config.save_config()
        
        messagebox.showinfo("Saved", "All settings saved!")
    
    def log_to_sending(self, message):
        """Log to sending console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.send_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.send_log.see(tk.END)
    
    def log_to_verify(self, message):
        """Log to verification console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.verify_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.verify_log.see(tk.END)
    
    def on_closing(self):
        """Handle window close"""
        self.config.save_config()
        self.root.destroy()

# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = SMTPValidatorGUI(root)
    root.mainloop()
