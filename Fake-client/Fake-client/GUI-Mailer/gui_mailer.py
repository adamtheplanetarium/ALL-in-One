import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import smtplib
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
from datetime import datetime
import os
import time
import uuid
from colorama import Fore, Style, init
import concurrent.futures
import hashlib
import re
import json

# Import our modules
from config_manager import ConfigManager
from file_operations import FileOperations
from smtp_manager import SMTPManager
from verification_manager import VerificationManager
from sending_manager import SendingManager

init(autoreset=True)

class EmailSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Sender Pro - GUI Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        # Save config on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Thread safety - Keep original SMTP lock logic
        self.smtp_server_index = 0
        self.smtp_server_lock = threading.Lock()
        self.failed_servers = {}
        self.failed_servers_lock = threading.Lock()
        self.total_emails_lock = threading.Lock()
        self.current_indexs_lock = threading.Lock()
        
        # State variables
        self.smtp_servers = []
        self.recipient_email_list = []
        self.from_addresses = []
        self.from_addresses_lock = threading.Lock()  # Thread-safe from address removal
        self.connection_retry_count = 0
        self.max_connection_retries = 10  # Max retries before giving up
        self.global_connection_lost = False  # Global flag for VPN recovery
        self.connection_recovery_event = threading.Event()  # Pauses all threads during recovery
        self.connection_recovery_event.set()  # Start with connection OK
        self.connection_recovery_lock = threading.Lock()  # Prevents multiple recovery attempts
        
        # Rapid failure detection for VPN drops
        self.recent_failures = []  # List of (timestamp, error_type) tuples
        self.rapid_failure_threshold = 10  # Number of failures to trigger VPN recovery
        self.rapid_failure_window = 3  # Time window in seconds
        self.failure_tracking_lock = threading.Lock()
        self.html_template = ""
        self.is_running = False
        self.total_emails_sent = 0
        self.successfully_sent_emails = []
        self.current_index = 0
        self.smtp_error_occurred = False
        self.smtp_paused = False
        self.smtp_pause_event = threading.Event()
        self.smtp_pause_event.set()  # Not paused initially
        
        # Inbox monitor state
        self.monitor_thread = None
        self.is_monitoring = False
        self.monitor_lock = threading.Lock()
        self.fake_from_counter = 0
        self.seen_emails = set()
        self.thunderbird_path = r"C:\Users\deshaz\AppData\Roaming\Thunderbird\Profiles\ryxodx96.default-release\ImapMail"
        self.config_file = 'gui_mailer_config.json'
        
        # IMAP monitoring state
        self.monitor_mode = 'thunderbird'  # 'thunderbird' or 'imap'
        self.imap_accounts = []
        self.imap_seen_message_ids = set()  # Track seen IMAP message IDs
        
        # Email verification state
        self.collected_from_emails = []
        self.verified_froms = []
        self.unverified_froms = []
        self.verification_in_progress = False
        
        # Update throttling to prevent GUI freezing
        self.last_progress_update = 0
        self.progress_update_interval = 0.5  # Update GUI every 0.5 seconds max
        
        # Message queue for batched GUI updates (prevents freezing)
        self.log_queue = []
        self.console_queue = []
        self.last_gui_flush = 0
        self.gui_flush_interval = 0.3  # Flush queues every 0.3 seconds
        
        # URL shortening error tracking (prevent spam)
        self.url_shortener_error_logged = False
        
        # Initialize config manager
        self.config_manager = ConfigManager(self.config_file)
        
        # Initialize SMTP manager (handles auto-cleanup)
        self.smtp_manager = SMTPManager(self)
        
        # Initialize verification manager (handles pause/resume/stop)
        self.verification_manager = VerificationManager(self)
        self.sending_manager = SendingManager(self)
        
        # Create thread_count attribute (wrapper for threads_var used by sending_manager)
        class ThreadCountWrapper:
            def __init__(self, parent):
                self.parent = parent
            def get(self):
                return self.parent.threads_var.get()
        
        self.thread_count = ThreadCountWrapper(self)
        
        # Load saved config
        self.config_manager.load_config(self)
        
        self.setup_ui()
        
        # Load saved verified emails on startup
        try:
            if os.path.exists('verified_from.txt'):
                with open('verified_from.txt', 'r', encoding='utf-8') as f:
                    saved_verified = [line.strip() for line in f if line.strip()]
                    self.verified_froms = saved_verified
                    if hasattr(self, 'verified_from_text'):
                        for email in saved_verified:
                            self.verified_from_text.insert(tk.END, f"{email}\n")
                    print(f"{Fore.GREEN}[STARTUP] Loaded {len(saved_verified)} verified emails{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}[STARTUP] Could not load verified emails: {e}{Style.RESET_ALL}")
        
        # Load saved unverified emails on startup
        try:
            if os.path.exists('unverified_from.txt'):
                with open('unverified_from.txt', 'r', encoding='utf-8') as f:
                    saved_unverified = [line.strip() for line in f if line.strip()]
                    self.unverified_froms = saved_unverified
                    if hasattr(self, 'unverified_from_text'):
                        for email in saved_unverified:
                            self.unverified_from_text.insert(tk.END, f"{email}\n")
                    print(f"{Fore.GREEN}[STARTUP] Loaded {len(saved_unverified)} unverified emails{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}[STARTUP] Could not load unverified emails: {e}{Style.RESET_ALL}")
        
        # Start periodic GUI queue flush (prevents freezing)
        self.periodic_flush()
        
    def setup_ui(self):
        # Main container with notebook (tabs)
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Tab 1: Configuration
        self.config_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.config_tab, text="⚙️ Configuration")
        
        # Tab 2: SMTP Servers
        self.smtp_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.smtp_tab, text="📧 SMTP Servers")
        
        # Tab 3: Recipients
        self.recipients_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.recipients_tab, text="📋 Recipients")
        
        # Tab 4: From Addresses
        self.from_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.from_tab, text="👤 From Addresses")
        
        # Tab 5: Email Template
        self.template_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.template_tab, text="📝 Email Template")
        
        # Tab 6: Check Froms
        self.control_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.control_tab, text="✅ Check Froms")
        
        # Tab 7: Logs
        self.logs_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.logs_tab, text="📊 Logs & Statistics")
        
        # Tab 8: Console View
        self.console_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.console_tab, text="💻 Console View")
        
        # Tab 9: Get From (Inbox Monitor)
        self.getfrom_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.getfrom_tab, text="📬 Get From")
        
        # Tab 10: Sending (Bulk Email Sender)
        self.sending_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.sending_tab, text="📤 Sending")
        
        self.setup_config_tab()
        self.setup_smtp_tab()
        self.setup_recipients_tab()
        self.setup_from_tab()
        self.setup_template_tab()
        self.setup_control_tab()
        self.setup_logs_tab()
        self.setup_console_tab()
        self.setup_getfrom_tab()
        self.setup_sending_tab()
        
        # Apply saved config after UI is created
        self.apply_pending_config()
        
        # Parse loaded data to populate lists
        if self.smtp_text.get(1.0, 'end-1c').strip():
            self.parse_smtp_servers()
        if self.recipients_text.get(1.0, 'end-1c').strip():
            self.parse_recipients()
        if self.from_text.get(1.0, 'end-1c').strip():
            self.parse_from_addresses()
        
        # Add welcome message to verification log
        self.verification_log_print("=" * 60, 'info')
        self.verification_log_print("Email Verification System Ready", 'success')
        self.verification_log_print("Click 'Recheck All/Verified/Unverified' to start verification", 'info')
        self.verification_log_print("=" * 60, 'info')
        
    def setup_config_tab(self):
        # Configuration options frame
        config_frame = ttk.LabelFrame(self.config_tab, text="Email Configuration", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        row = 0
        
        # Domain From
        ttk.Label(config_frame, text="Domain From:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.domain_from_var = tk.StringVar(value="charter.net")
        ttk.Entry(config_frame, textvariable=self.domain_from_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Domain Authentication
        ttk.Label(config_frame, text="Domain Authentication:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.domain_auth_var = tk.StringVar(value="altona.fr")
        ttk.Entry(config_frame, textvariable=self.domain_auth_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Sender Name
        ttk.Label(config_frame, text="Sender Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sender_name_var = tk.StringVar(value="Support")
        ttk.Entry(config_frame, textvariable=self.sender_name_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(config_frame, text="Use 'CapitalS' for domain capital, 'randomchar' for numbers", font=('Arial', 8), foreground='gray').grid(row=row, column=2, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # Subject
        ttk.Label(config_frame, text="Subject:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.subject_var = tk.StringVar(value="Important Message")
        ttk.Entry(config_frame, textvariable=self.subject_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(config_frame, text="Use 'CapitalS', 'randomchar', 'DATEX' for replacements", font=('Arial', 8), foreground='gray').grid(row=row, column=2, sticky=tk.W, pady=5, padx=5)
        row += 1
        
        # Link Redirect
        ttk.Label(config_frame, text="Link Redirect URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.link_redirect_var = tk.StringVar(value="https://flexidesk.cloud/auth/direct_invoice")
        ttk.Entry(config_frame, textvariable=self.link_redirect_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Threads
        ttk.Label(config_frame, text="Threads:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.threads_var = tk.IntVar(value=10)
        ttk.Spinbox(config_frame, from_=1, to=50, textvariable=self.threads_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Sleep Time
        ttk.Label(config_frame, text="Sleep Time (seconds):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sleep_time_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(config_frame, from_=0, to=10, increment=0.1, textvariable=self.sleep_time_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Test Mode
        ttk.Label(config_frame, text="Test Mode:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.test_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable (emails won't be removed from list)", variable=self.test_mode_var).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Debug Mode
        ttk.Label(config_frame, text="Debug Mode:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.debug_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text="Enable SMTP debug output", variable=self.debug_mode_var).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Important Flag
        ttk.Label(config_frame, text="Mark as Important:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.important_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text="Add high priority headers", variable=self.important_var).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # URL Shortener
        ttk.Label(config_frame, text="Use URL Shortener:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.use_shortener_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Shorten URLs with is.gd", variable=self.use_shortener_var).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Apply & Save Configuration Button
        apply_save_frame = ttk.Frame(config_frame)
        apply_save_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(apply_save_frame, text="✅ Apply & Save Configuration", 
                  command=self.apply_and_save_config,
                  style='Accent.TButton').pack(padx=5)
        
        ttk.Label(apply_save_frame, 
                 text="Click this after changing any settings to apply them immediately",
                 font=('Arial', 9, 'italic'), 
                 foreground='#666666').pack(pady=5)
        row += 1
        
        config_frame.columnconfigure(1, weight=1)
        
    def setup_smtp_tab(self):
        # SMTP Servers management
        smtp_frame = ttk.LabelFrame(self.smtp_tab, text="SMTP Server Management", padding="10")
        smtp_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.smtp_tab.columnconfigure(0, weight=1)
        self.smtp_tab.rowconfigure(0, weight=1)
        
        # Instructions
        ttk.Label(smtp_frame, text="Format: username:password:host:port (one per line)", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(smtp_frame, text="Example: user@domain.com:pass123:smtp.domain.com:587", 
                 font=('Arial', 9, 'italic'), foreground='#666666').grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(25, 5), padx=5)
        
        # Text area for SMTP servers
        smtp_text_frame = ttk.Frame(smtp_frame)
        smtp_text_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        smtp_frame.rowconfigure(1, weight=1)
        smtp_frame.columnconfigure(0, weight=1)
        
        self.smtp_text = scrolledtext.ScrolledText(smtp_text_frame, height=20, width=80, wrap=tk.WORD)
        self.smtp_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(smtp_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="📁 Load from File", command=self.load_smtp_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save to File", command=self.save_smtp_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ Parse & Validate", command=self.parse_smtp_servers).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Clear", command=lambda: self.smtp_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🚫 Remove Failed SMTPs", command=self.remove_failed_smtps).pack(side=tk.LEFT, padx=5)
        
        # Server count label
        self.smtp_count_label = ttk.Label(smtp_frame, text="Servers loaded: 0", font=('Arial', 10, 'bold'))
        self.smtp_count_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
    def setup_recipients_tab(self):
        # Recipients management
        recipients_frame = ttk.LabelFrame(self.recipients_tab, text="Recipient Pool (Routing Mode)", padding="10")
        recipients_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.recipients_tab.columnconfigure(0, weight=1)
        self.recipients_tab.rowconfigure(0, weight=1)
        
        # Instructions
        instruction_text = """🔄 ROUTING MODE: Enter 5-10 recipient emails
The system will ROTATE through these recipients until all FROM addresses are used.
Example: 100 from addresses + 5 recipients = 100 emails sent (rotating through 5 recipients)"""
        ttk.Label(recipients_frame, text=instruction_text, 
                 font=('Arial', 9), justify=tk.LEFT, foreground='#0066cc').grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Text area for recipients
        recipients_text_frame = ttk.Frame(recipients_frame)
        recipients_text_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        recipients_frame.rowconfigure(1, weight=1)
        recipients_frame.columnconfigure(0, weight=1)
        
        self.recipients_text = scrolledtext.ScrolledText(recipients_text_frame, height=20, width=80, wrap=tk.WORD)
        self.recipients_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(recipients_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="📁 Load from File", command=self.load_recipients_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save to File", command=self.save_recipients_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ Parse & Validate", command=self.parse_recipients).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Clear", command=lambda: self.recipients_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        # Recipient count label
        self.recipient_count_label = ttk.Label(recipients_frame, text="Recipients loaded: 0", font=('Arial', 10, 'bold'))
        self.recipient_count_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
    def setup_from_tab(self):
        # From addresses management
        from_frame = ttk.LabelFrame(self.from_tab, text="From Email Addresses", padding="10")
        from_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.from_tab.columnconfigure(0, weight=1)
        self.from_tab.rowconfigure(0, weight=1)
        
        # Instructions
        ttk.Label(from_frame, text="Enter one email address per line (will rotate through these)", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Text area for from addresses
        from_text_frame = ttk.Frame(from_frame)
        from_text_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        from_frame.rowconfigure(1, weight=1)
        from_frame.columnconfigure(0, weight=1)
        
        self.from_text = scrolledtext.ScrolledText(from_text_frame, height=20, width=80, wrap=tk.WORD)
        self.from_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(from_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="📁 Load from File", command=self.load_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save to File", command=self.save_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ Parse & Validate", command=self.parse_from_addresses).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Clear", command=self.clear_from_addresses).pack(side=tk.LEFT, padx=5)
        
        # From count label
        self.from_count_label = ttk.Label(from_frame, text="From addresses remaining: 0", font=('Arial', 10, 'bold'))
        self.from_count_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
    def setup_template_tab(self):
        # Email template management
        template_frame = ttk.LabelFrame(self.template_tab, text="HTML Email Template", padding="10")
        template_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.template_tab.columnconfigure(0, weight=1)
        self.template_tab.rowconfigure(0, weight=1)
        
        # Instructions
        instructions = """Available placeholders:
• LINKREDIRECT - Will be replaced with shortened URL
• IMGREDIRECT - Will be replaced with image redirect URL
• RANDOM - Will be replaced with random 6-digit number"""
        
        ttk.Label(template_frame, text=instructions, 
                 font=('Arial', 9), justify=tk.LEFT).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Text area for template
        template_text_frame = ttk.Frame(template_frame)
        template_text_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        template_frame.rowconfigure(1, weight=1)
        template_frame.columnconfigure(0, weight=1)
        
        self.template_text = scrolledtext.ScrolledText(template_text_frame, height=25, width=100, wrap=tk.WORD)
        self.template_text.pack(fill=tk.BOTH, expand=True)
        
        # Default template
        default_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email</title>
</head>
<body>
    <h1>Sample Email</h1>
    <p>This is a sample email template.</p>
    <p><a href="LINKREDIRECT">Click here</a></p>
    <p>Reference: RANDOM</p>
</body>
</html>"""
        self.template_text.insert(1.0, default_template)
        
        # Buttons
        button_frame = ttk.Frame(template_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="✅ Apply Message", command=self.apply_message_template, style='Accent.TButton').pack(side=tk.LEFT, padx=5, ipadx=10)
        ttk.Button(button_frame, text="📁 Load from File", command=self.load_template_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save to File", command=self.save_template_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Clear", command=lambda: self.template_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
    def setup_control_tab(self):
        # Check Froms control and progress
        control_frame = ttk.LabelFrame(self.control_tab, text="Check Froms Control Panel", padding="20")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.control_tab.columnconfigure(0, weight=1)
        self.control_tab.rowconfigure(0, weight=1)
        
        # Status display
        status_frame = ttk.LabelFrame(control_frame, text="Current Status", padding="15")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        control_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready", font=('Arial', 14, 'bold'), foreground='green')
        self.status_label.pack(pady=5)
        
        self.progress_label = ttk.Label(status_frame, text="Progress: 0 / 0", font=('Arial', 12))
        self.progress_label.pack(pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate', length=500)
        self.progress_bar.pack(pady=10, fill=tk.X, padx=20)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding="15")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Real-time FROM counter at the top
        self.remaining_from_label = ttk.Label(stats_frame, text="Remaining FROM: 0", 
                                             font=('Arial', 12, 'bold'), foreground='#0066cc')
        self.remaining_from_label.pack(pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=10, width=70, state=tk.DISABLED, bg='#f0f0f0')
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="🚀 START SENDING", 
                                       command=self.start_sending, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=10)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ STOP", 
                                      command=self.stop_sending, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=10)
        
        self.resume_smtp_btn = ttk.Button(button_frame, text="▶️ RESUME SENDING", 
                                         command=self.resume_smtp_sending, state=tk.DISABLED)
        self.resume_smtp_btn.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=10)
        
        # Info label for pause state
        self.pause_info_label = ttk.Label(control_frame, 
                                         text="💡 If all SMTP servers fail, sending will pause until you update SMTPs",
                                         font=('Arial', 9, 'italic'), foreground='#666666')
        self.pause_info_label.grid(row=3, column=0, pady=10)
        
        self.update_stats()
        
    def setup_logs_tab(self):
        # Logs and statistics
        logs_frame = ttk.LabelFrame(self.logs_tab, text="Activity Logs", padding="10")
        logs_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.logs_tab.columnconfigure(0, weight=1)
        self.logs_tab.rowconfigure(0, weight=1)
        
        # Log text area
        log_text_frame = ttk.Frame(logs_frame)
        log_text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.rowconfigure(0, weight=1)
        logs_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_text_frame, height=30, width=120, wrap=tk.WORD, bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.log_text.tag_config('success', foreground='#00ff00')
        self.log_text.tag_config('error', foreground='#ff0000')
        self.log_text.tag_config('warning', foreground='#ffaa00')
        self.log_text.tag_config('info', foreground='#00aaff')
        
        # Button frame
        button_frame = ttk.Frame(logs_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="🗑️ Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
    def setup_console_tab(self):
        # Console view for real-time detailed output
        console_frame = ttk.LabelFrame(self.console_tab, text="Real-Time Console Output", padding="10")
        console_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.console_tab.columnconfigure(0, weight=1)
        self.console_tab.rowconfigure(0, weight=1)
        
        # Console text area with dark theme
        console_text_frame = ttk.Frame(console_frame)
        console_text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_frame.rowconfigure(0, weight=1)
        console_frame.columnconfigure(0, weight=1)
        
        self.console_text = scrolledtext.ScrolledText(console_text_frame, height=35, width=140, 
                                                     wrap=tk.WORD, bg='#0a0a0a', fg='#00ff00', 
                                                     font=('Courier New', 9))
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored console output
        self.console_text.tag_config('green', foreground='#00ff00')
        self.console_text.tag_config('red', foreground='#ff0000')
        self.console_text.tag_config('yellow', foreground='#ffff00')
        self.console_text.tag_config('cyan', foreground='#00ffff')
        self.console_text.tag_config('magenta', foreground='#ff00ff')
        self.console_text.tag_config('white', foreground='#ffffff')
        
        # Info frame with stats
        info_frame = ttk.Frame(console_frame)
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.console_info_label = ttk.Label(info_frame, text="Waiting to start...", 
                                           font=('Courier New', 10, 'bold'), foreground='#00aa00')
        self.console_info_label.pack(side=tk.LEFT, padx=10)
        
        # Button frame
        button_frame = ttk.Frame(console_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(button_frame, text="🗑️ Clear Console", command=self.clear_console).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save Console", command=self.save_console).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⏸️ Pause Auto-Scroll", command=self.toggle_autoscroll).pack(side=tk.LEFT, padx=5)
        
        self.autoscroll_enabled = True
        
    # File operations (delegated to FileOperations module)
    def load_smtp_file(self): FileOperations.load_smtp_file(self)
    def save_smtp_file(self): FileOperations.save_smtp_file(self)
    def load_recipients_file(self): FileOperations.load_recipients_file(self)
    def save_recipients_file(self): FileOperations.save_recipients_file(self)
    def load_from_file(self): FileOperations.load_from_file(self)
    def save_from_file(self): FileOperations.save_from_file(self)
    def apply_message_template(self):
        """Apply the message template changes"""
        from tkinter import messagebox
        try:
            # Get current template
            template_content = self.template_text.get(1.0, tk.END).strip()
            
            if not template_content:
                messagebox.showwarning("Empty Template", "Message template is empty!")
                return
            
            # Update the message body (stored in memory)
            self.email_body = template_content
            
            # Also save to file for persistence
            try:
                with open('ma.html', 'w', encoding='utf-8') as f:
                    f.write(template_content)
                messagebox.showinfo("✅ Applied", "Message template applied successfully!\n\nChanges will be used for all new emails.")
                self.console_print(f"[INFO] Message template applied and saved to ma.html", 'info')
            except Exception as e:
                messagebox.showwarning("Applied (Save Failed)", f"Template applied but couldn't save to file:\n{str(e)}\n\nChanges will be used but not persisted.")
                self.console_print(f"[WARNING] Template applied but save failed: {str(e)}", 'warning')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply template:\n{str(e)}")
            self.console_print(f"[ERROR] Failed to apply template: {str(e)}", 'error')
    
    def load_template_file(self): FileOperations.load_template_file(self)
    def save_template_file(self): FileOperations.save_template_file(self)
                
    # Parsing and validation
    def parse_smtp_servers(self):
        content = self.smtp_text.get(1.0, tk.END).strip()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        self.smtp_servers = []
        for line in lines:
            # Support both formats:
            # New format: username:password:host:port
            # Old format: host,port,username,password
            
            if ':' in line and line.count(':') >= 3:
                # New format: username:password:host:port
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        self.smtp_servers.append({
                            'username': parts[0].strip(),
                            'password': parts[1].strip(),
                            'host': parts[2].strip(),
                            'port': int(parts[3].strip())
                        })
                    except ValueError:
                        self.log_message(f"Warning: Invalid port in line: {line}", 'warning')
            elif ',' in line:
                # Old format: host,port,username,password
                parts = line.split(',')
                if len(parts) >= 4:
                    try:
                        self.smtp_servers.append({
                            'host': parts[0].strip(),
                            'port': int(parts[1].strip()),
                            'username': parts[2].strip(),
                            'password': parts[3].strip()
                        })
                    except ValueError:
                        self.log_message(f"Warning: Invalid port in line: {line}", 'warning')
                    
        self.smtp_count_label.config(text=f"Servers loaded: {len(self.smtp_servers)}")
        self.log_message(f"Parsed {len(self.smtp_servers)} SMTP servers", 'success')
        
        print(f"{Fore.GREEN}✅ SMTP Servers Updated: {len(self.smtp_servers)} servers loaded{Style.RESET_ALL}")
        
        # If paused and new SMTPs added, show hint
        if self.smtp_paused and len(self.smtp_servers) > 0:
            print(f"{Fore.YELLOW}💡 You have {len(self.smtp_servers)} SMTP servers ready. Click 'Resume Sending' to continue.{Style.RESET_ALL}")
            messagebox.showinfo(
                "SMTP Servers Updated",
                f"✅ {len(self.smtp_servers)} SMTP servers loaded!\\n\\n"
                "Email sending is currently PAUSED.\\n\\n"
                "Click 'Resume Sending' button in Check Froms tab to continue."
            )
        
        self.update_stats()
        
    def parse_recipients(self):
        content = self.recipients_text.get(1.0, tk.END).strip()
        self.recipient_email_list = [line.strip() for line in content.split('\n') if line.strip() and '@' in line]
        
        self.recipient_count_label.config(text=f"Recipients loaded: {len(self.recipient_email_list)}")
        self.log_message(f"Parsed {len(self.recipient_email_list)} recipients", 'success')
        self.update_stats()
        
    def parse_from_addresses(self):
        content = self.from_text.get(1.0, tk.END).strip()
        all_addresses = [line.strip() for line in content.split('\n') if line.strip() and '@' in line]
        
        # SAFETY LIMIT: Max 500K addresses to prevent UI freeze (increased from 100K)
        MAX_FROM = 500000
        if len(all_addresses) > MAX_FROM:
            messagebox.showwarning(
                "Too Many Addresses",
                f"Found {len(all_addresses):,} addresses!\n\n"
                f"Limiting to first {MAX_FROM:,} to prevent freeze.\n\n"
                f"Tip: Process in batches or clear old addresses."
            )
            self.from_addresses = all_addresses[:MAX_FROM]
            self.console_print(f"[WARNING] Limited FROM addresses: {len(all_addresses):,} -> {MAX_FROM:,}", 'yellow')
        else:
            self.from_addresses = all_addresses
            if len(all_addresses) > 200000:
                self.console_print(f"[INFO] Loaded {len(all_addresses):,} addresses - Large collection!", 'cyan')
        
        self.from_count_label.config(text=f"From addresses remaining: {len(self.from_addresses)}")
        self.log_message(f"Parsed {len(self.from_addresses)} from addresses", 'success')
        self.update_stats()
    
    def clear_from_addresses(self):
        """Properly clear FROM addresses from UI and memory"""
        self.from_text.delete(1.0, tk.END)
        self.from_addresses = []
        self.from_count_label.config(text="From addresses remaining: 0")
        # Save empty state to config
        self.config_manager.save_config(self)
        self.log_message("✅ FROM addresses cleared", 'success')
        self.console_print("🗑️ FROM addresses cleared from memory and config", 'yellow')
                
    def clear_console(self):
        self.console_text.delete(1.0, tk.END)
        
    def save_console(self):
        filename = filedialog.asksaveasfilename(title="Save Console Output", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "Console output saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save console: {e}")
                
    def toggle_autoscroll(self):
        self.autoscroll_enabled = not self.autoscroll_enabled
        status = "ENABLED" if self.autoscroll_enabled else "DISABLED"
        self.log_message(f"Auto-scroll {status}", 'info')
        
    def setup_getfrom_tab(self):
        # Main container with left-right layout (NO SCROLLING)
        main_container = ttk.Frame(self.getfrom_tab, padding="5")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.getfrom_tab.columnconfigure(0, weight=1)
        self.getfrom_tab.rowconfigure(0, weight=1)
        
        # Configure 2-column layout
        main_container.columnconfigure(0, weight=1)  # Left column
        main_container.columnconfigure(1, weight=1)  # Right column
        main_container.rowconfigure(0, weight=1)     # Make both expand
        
        # ============= LEFT COLUMN =============
        left_column = ttk.Frame(main_container)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 3))
        left_column.columnconfigure(0, weight=1)
        left_column.rowconfigure(4, weight=1)  # Monitor log expands
        
        # Mode Selection (Thunderbird vs IMAP)
        mode_frame = ttk.LabelFrame(left_column, text="📡 Monitor Mode", padding="8")
        mode_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        self.monitor_mode_var = tk.StringVar(value='thunderbird')
        ttk.Radiobutton(mode_frame, text="📂 Thunderbird (Local)", variable=self.monitor_mode_var, 
                       value='thunderbird', command=self.switch_monitor_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="📧 IMAP (Remote)", variable=self.monitor_mode_var, 
                       value='imap', command=self.switch_monitor_mode).pack(side=tk.LEFT, padx=5)
        
        # Thunderbird Path (Compact)
        self.thunderbird_frame = ttk.LabelFrame(left_column, text="📂 Thunderbird Path", padding="8")
        self.thunderbird_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        self.thunderbird_frame.columnconfigure(0, weight=1)
        
        self.thunderbird_path_var = tk.StringVar(value=self.thunderbird_path)
        path_display = ttk.Label(self.thunderbird_frame, textvariable=self.thunderbird_path_var, 
                                relief=tk.SUNKEN, padding=4, font=('Courier New', 8),
                                foreground='#0066cc', cursor='hand2')
        path_display.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(self.thunderbird_frame, text="✏️", command=self.edit_thunderbird_path, width=3).grid(row=0, column=1)
        
        # IMAP Accounts Section
        self.imap_frame = ttk.LabelFrame(left_column, text="📧 IMAP Accounts", padding="8")
        self.imap_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        self.imap_frame.columnconfigure(0, weight=1)
        self.imap_frame.rowconfigure(0, weight=1)
        
        ttk.Label(self.imap_frame, text="Format: email:password (one per line)", 
                 font=('Arial', 8), foreground='gray').grid(row=0, column=0, sticky=tk.W, pady=(0, 2))
        
        self.imap_accounts_text = scrolledtext.ScrolledText(self.imap_frame, wrap=tk.WORD, height=6,
                                                            bg='#2b2b2b', fg='#00ff00', 
                                                            font=('Courier New', 8))
        self.imap_accounts_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        # Pre-populate with provided accounts
        default_imap = """bendox21@currently.com:hedgpttaqjzcrjgq
bootonmat2@att.net:ywaghiyybvvhvkyo
vbvflain232@att.net:wmgunfdbvhhbjitq
lovelyking1@att.net:dindfcdgqdbkdxsm
zingabora55@att.net:lxykvslveektzbkx
boxingo32@att.net:yxwonodvnummhpel
bndr5665@att.net:psgvjppmywzvcmlo
zringso23@att.net:ntyfqjslluwgaljj"""
        self.imap_accounts_text.insert(1.0, default_imap)
        
        imap_btn_frame = ttk.Frame(self.imap_frame)
        imap_btn_frame.grid(row=2, column=0, pady=(5, 0))
        ttk.Button(imap_btn_frame, text="✅ Parse Accounts", command=self.parse_imap_accounts).pack(side=tk.LEFT, padx=2)
        ttk.Button(imap_btn_frame, text="🔍 Manual Check", command=self.manual_imap_check).pack(side=tk.LEFT, padx=2)
        
        self.imap_accounts_label = ttk.Label(self.imap_frame, text="0 accounts loaded", 
                                            font=('Arial', 8), foreground='gray')
        self.imap_accounts_label.grid(row=3, column=0, pady=(5, 0))
        
        # Hide IMAP frame by default (Thunderbird is default)
        self.imap_frame.grid_remove()
        
        # Counter Section (Compact)
        counter_frame = ttk.LabelFrame(left_column, text="📊 FROM Addresses Collected", padding="12")
        counter_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        self.fake_from_label = ttk.Label(counter_frame, text="0", font=('Arial', 42, 'bold'), 
                                         foreground='#00aa00')
        self.fake_from_label.pack()
        
        # Buttons for collected emails
        collected_btn_frame = ttk.Frame(counter_frame)
        collected_btn_frame.pack(pady=(8, 0))
        
        ttk.Button(collected_btn_frame, text="➕ Add All to Verified", 
                  command=self.add_all_collected_to_verified).pack(side=tk.LEFT, padx=3)
        ttk.Button(collected_btn_frame, text="🗑️ Clear All", 
                  command=self.clear_all_collected).pack(side=tk.LEFT, padx=3)
        
        # Monitor Controls
        control_frame = ttk.LabelFrame(left_column, text="🎛️ Monitor Controls", padding="8")
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        btn_container = ttk.Frame(control_frame)
        btn_container.pack(fill=tk.X)
        
        self.start_monitor_btn = ttk.Button(btn_container, text="▶️ Start", 
                                           command=self.start_monitoring)
        self.start_monitor_btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        self.stop_monitor_btn = ttk.Button(btn_container, text="⏹️ Stop", 
                                          command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_monitor_btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        # Status
        self.monitor_status_label = ttk.Label(control_frame, text="⚫ Monitoring: STOPPED", 
                                             font=('Arial', 9, 'bold'), foreground='red')
        self.monitor_status_label.pack(pady=(8, 3))
        
        self.monitor_check_label = ttk.Label(control_frame, text="Last Check: Never", font=('Arial', 8))
        self.monitor_check_label.pack(pady=2)
        
        self.monitor_accounts_label = ttk.Label(control_frame, text="Active Accounts: 0", font=('Arial', 8))
        self.monitor_accounts_label.pack(pady=2)
        
        # Monitor Log (Expandable)
        log_frame = ttk.LabelFrame(left_column, text="📝 Activity Log", padding="5")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_column.rowconfigure(4, weight=1)
        
        self.monitor_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                     bg='#1e1e1e', fg='#00ff00', 
                                                     font=('Courier New', 8))
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored log output
        self.monitor_log.tag_config('info', foreground='#00ffff')
        self.monitor_log.tag_config('success', foreground='#00ff00')
        self.monitor_log.tag_config('warning', foreground='#ffff00')
        self.monitor_log.tag_config('error', foreground='#ff0000')
        
        # ============= RIGHT COLUMN =============
        right_column = ttk.Frame(main_container)
        right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(3, 0))
        right_column.columnconfigure(0, weight=1)
        right_column.rowconfigure(0, weight=1)  # Verification section expands
        
        # Verification Section
        verify_frame = ttk.LabelFrame(right_column, text="📋 Email Verification", padding="8")
        verify_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_column.rowconfigure(0, weight=1)
        
        # Create 2-column layout for verified and unverified
        verify_frame.columnconfigure(0, weight=1)
        verify_frame.columnconfigure(1, weight=1)
        verify_frame.rowconfigure(0, weight=1)
        
        # VERIFIED COLUMN
        verified_frame = ttk.Frame(verify_frame)
        verified_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 3))
        verified_frame.columnconfigure(0, weight=1)
        verified_frame.rowconfigure(1, weight=1)
        
        self.verified_label = ttk.Label(verified_frame, text="✅ Verified (0)", font=('Arial', 11, 'bold'), foreground='#228b22')
        self.verified_label.grid(row=0, column=0, pady=(0, 5))
        
        self.verified_from_text = scrolledtext.ScrolledText(verified_frame, wrap=tk.WORD, 
                                                            bg='#1a3d1a', fg='#66cdaa', 
                                                            font=('Courier New', 9))
        self.verified_from_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Verified buttons (compact)
        verified_btn_frame = ttk.Frame(verified_frame)
        verified_btn_frame.grid(row=2, column=0, pady=(5, 0))
        ttk.Button(verified_btn_frame, text="✅", command=self.apply_verified_textarea, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(verified_btn_frame, text="🔄", command=lambda: self.start_verification('verified'), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(verified_btn_frame, text="💾", command=self.save_verified_froms_to_file, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(verified_btn_frame, text="📁", command=self.load_verified_froms_from_file, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(verified_btn_frame, text="🗑️", command=self.clear_verified_emails, width=3).pack(side=tk.LEFT, padx=1)
        
        # UNVERIFIED COLUMN
        unverified_frame = ttk.Frame(verify_frame)
        unverified_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(3, 0))
        unverified_frame.columnconfigure(0, weight=1)
        unverified_frame.rowconfigure(1, weight=1)
        
        self.unverified_label = ttk.Label(unverified_frame, text="❌ Unverified (0)", font=('Arial', 11, 'bold'), foreground='#ff0000')
        self.unverified_label.grid(row=0, column=0, pady=(0, 5))
        
        self.unverified_from_text = scrolledtext.ScrolledText(unverified_frame, wrap=tk.WORD, 
                                                              bg='#3d1a1a', fg='#ff6666', 
                                                              font=('Courier New', 8))
        self.unverified_from_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Unverified buttons (compact)
        unverified_btn_frame = ttk.Frame(unverified_frame)
        unverified_btn_frame.grid(row=2, column=0, pady=(5, 0))
        ttk.Button(unverified_btn_frame, text="✅", command=self.apply_unverified_textarea, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(unverified_btn_frame, text="🔄", command=lambda: self.start_verification('unverified'), width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(unverified_btn_frame, text="💾", command=self.save_unverified_froms_to_file, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(unverified_btn_frame, text="📁", command=self.load_unverified_froms_from_file, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(unverified_btn_frame, text="🗑️", command=self.clear_unverified_emails, width=3).pack(side=tk.LEFT, padx=1)
        
        # Action buttons
        action_btn_frame = ttk.Frame(verify_frame)
        action_btn_frame.grid(row=1, column=0, columnspan=2, pady=(8, 5))
        
        ttk.Button(action_btn_frame, text="🔄 All", command=lambda: self.start_verification('all'), width=8).pack(side=tk.LEFT, padx=2)
        self.pause_verify_btn = ttk.Button(action_btn_frame, text="⏸️ Pause", command=self.pause_verification, width=10)
        self.pause_verify_btn.pack(side=tk.LEFT, padx=2)
        self.resume_verify_btn = ttk.Button(action_btn_frame, text="▶️ Resume", command=self.resume_verification, width=10, state=tk.DISABLED)
        self.resume_verify_btn.pack(side=tk.LEFT, padx=2)
        self.stop_verify_btn = ttk.Button(action_btn_frame, text="⏹️ Stop", command=self.stop_verification, width=10)
        self.stop_verify_btn.pack(side=tk.LEFT, padx=2)
        
        # Verification stats
        self.verify_stats_label = ttk.Label(verify_frame, 
                                           text="Total: 0 | Verified: 0 | Unverified: 0",
                                           font=('Arial', 8, 'bold'), foreground='#0000ff')
        self.verify_stats_label.grid(row=2, column=0, columnspan=2, pady=(5, 8))
        
        # Verification Progress Log
        progress_frame = ttk.LabelFrame(verify_frame, text="Verification Progress", padding="5")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        verify_frame.rowconfigure(3, weight=1)
        
        self.verification_log = scrolledtext.ScrolledText(progress_frame, height=8, wrap=tk.WORD, 
                                                          bg='#1e1e1e', fg='#00ff00', 
                                                          font=('Courier New', 8))
        self.verification_log.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.verification_log.tag_config('success', foreground='#00ff00')
        self.verification_log.tag_config('error', foreground='#ff0000')
        self.verification_log.tag_config('warning', foreground='#ffff00')
        self.verification_log.tag_config('info', foreground='#00ffff')
        
        # Auto-start monitoring after UI is ready
        self.root.after(1000, self.auto_start_monitoring)
    
    def verification_log_print(self, message, tag='info'):
        """Print to verification log with color"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.verification_log.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.verification_log.see(tk.END)
        except:
            pass
        
    def console_print(self, message, color='green'):
        """Print to console view with color - queued for batch processing"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.console_queue.append((timestamp, message, color))
            
            # Auto-flush if queue gets too large or if enough time has passed
            current_time = time.time()
            if len(self.console_queue) > 10 or (current_time - self.last_gui_flush > self.gui_flush_interval):
                self.flush_gui_queues()
        except:
            pass
        
    # Logging
    def log_message(self, message, tag='info'):
        """Log message - queued for batch processing"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.append((timestamp, message, tag))
        
        # Auto-flush if queue gets too large
        if len(self.log_queue) > 10:
            self.flush_gui_queues()
    
    def flush_gui_queues(self):
        """Flush all queued messages to GUI - prevents freezing from too many updates"""
        try:
            current_time = time.time()
            self.last_gui_flush = current_time
            
            # Flush console queue (batch insert)
            if self.console_queue:
                for timestamp, message, color in self.console_queue:
                    self.console_text.insert(tk.END, f"[{timestamp}] ", 'cyan')
                    self.console_text.insert(tk.END, f"{message}\n", color)
                if self.autoscroll_enabled:
                    self.console_text.see(tk.END)
                self.console_queue.clear()
            
            # Flush log queue (batch insert)
            if self.log_queue:
                for timestamp, message, tag in self.log_queue:
                    self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
                self.log_text.see(tk.END)
                self.log_queue.clear()
                
        except Exception as e:
            pass
    
    def periodic_flush(self):
        """Periodically flush GUI queues to keep display updated"""
        try:
            if self.console_queue or self.log_queue:
                self.flush_gui_queues()
        except:
            pass
        # Schedule next flush
        self.root.after(300, self.periodic_flush)  # Every 300ms
        
    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        
    def save_logs(self):
        filename = filedialog.asksaveasfilename(title="Save Logs", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "Logs saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")
                
    def update_stats(self):
        stats = f"""
╔══════════════════════════════════════════════╗
║           SENDING STATISTICS                 ║
╠══════════════════════════════════════════════╣
║ SMTP Servers Loaded:    {len(self.smtp_servers):>5}             ║
║ Recipient Pool Size:    {len(self.recipient_email_list):>5}             ║
║ From Addresses (Total): {len(self.from_addresses):>5}             ║
║ Emails Sent:            {self.total_emails_sent:>5}             ║
║ Successfully Sent:      {len(self.successfully_sent_emails):>5}             ║
║ Failed Servers:         {len(self.failed_servers):>5}             ║
║ MODE: Route through {len(self.recipient_email_list)} recipients      ║
╚══════════════════════════════════════════════╝
        """
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
        
    # Email sending logic (preserves original SMTP lock mechanism)
    def start_sending(self):
        # Validate inputs
        if not self.smtp_servers:
            messagebox.showerror("Error", "Please load and parse SMTP servers first")
            return
        if not self.recipient_email_list:
            messagebox.showerror("Error", "Please load and parse recipients first")
            return
        if not self.from_addresses:
            messagebox.showerror("Error", "Please load and parse from addresses first")
            return
            
        # Get template
        self.html_template = self.template_text.get(1.0, tk.END).strip()
        if not self.html_template:
            messagebox.showerror("Error", "Please enter an email template")
            return
            
        # Reset state
        self.total_emails_sent = 0
        self.successfully_sent_emails = []
        self.current_index = 0
        self.smtp_error_occurred = False
        self.failed_servers = {}
        self.smtp_server_index = 0
        self.is_running = True
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Sending...", foreground='orange')
        self.progress_bar['maximum'] = len(self.from_addresses)  # Progress based on from addresses
        self.progress_bar['value'] = 0
        
        self.log_message("="*60, 'info')
        self.log_message("STARTING EMAIL SENDING CAMPAIGN - ROUTING MODE", 'success')
        self.log_message(f"Will send {len(self.from_addresses)} emails rotating through {len(self.recipient_email_list)} recipients", 'info')
        self.log_message("="*60, 'info')
        
        self.console_print("="*80, 'cyan')
        self.console_print("EMAIL SENDING CAMPAIGN STARTED", 'yellow')
        self.console_print(f"Total FROM addresses: {len(self.from_addresses)}", 'white')
        self.console_print(f"Recipient pool size: {len(self.recipient_email_list)}", 'white')
        self.console_print(f"SMTP servers: {len(self.smtp_servers)}", 'white')
        self.console_print(f"Threads: {self.threads_var.get()}", 'white')
        self.console_print("="*80, 'cyan')
        
        # Start sending in a separate thread
        thread = threading.Thread(target=self.send_emails_thread, daemon=True)
        thread.start()
        
    def stop_sending(self):
        self.is_running = False
        self.status_label.config(text="Status: Stopping...", foreground='red')
        self.log_message("Stop requested - finishing current operations...", 'warning')
        
        # Unpause if paused
        if self.smtp_paused:
            self.smtp_pause_event.set()
    
    def finish_sending(self):
        """Called when sending completes or stops"""
        self.is_running = False
        self.status_label.config(text="Status: Idle", foreground='green')
        
        # Save configuration
        self.config_manager.save_config(self)
        
        # Log completion
        self.log_message(f"✅ Sending completed. Total sent: {self.total_emails_sent}", 'success')
        self.console_print("="*80, 'cyan')
        self.console_print(f"📊 CAMPAIGN COMPLETE", 'green')
        self.console_print(f"   Total emails sent: {self.total_emails_sent}", 'white')
        self.console_print(f"   FROM addresses used: {len(self.successfully_sent_emails)}", 'white')
        self.console_print("="*80, 'cyan')
    
    def show_smtp_pause_warning(self):
        """Show warning when max connection retries are exhausted"""
        self.status_label.config(text="⛔ PAUSED - Max connection retries exhausted!", foreground='red')
        
        # Enable resume button if it exists
        if hasattr(self, 'resume_smtp_btn'):
            self.resume_smtp_btn.config(state=tk.NORMAL)
        
        # Show warning message (only after max retries)
        messagebox.showwarning(
            "Connection Failed",
            "⛔ Connection failed after 10 automatic retries!\n\n"
            "The sending process is PAUSED.\n\n"
            "Please check:\n"
            "1. Your VPN/Internet connection\n"
            "2. SMTP server availability\n"
            "3. Firewall/Network settings\n\n"
            "Click 'Resume Sending' when ready to continue."
        )
    
    def resume_smtp_sending(self):
        """Resume sending after SMTP servers are updated"""
        if not self.smtp_paused:
            messagebox.showinfo("Not Paused", "Email sending is not currently paused.")
            return
        
        # Check if SMTP servers are available
        if not self.smtp_servers:
            messagebox.showerror(
                "No SMTP Servers",
                "Please add SMTP servers before resuming!\n\n"
                "Go to SMTP Servers tab and add servers."
            )
            return
        
        # Reset failed servers counter
        with self.failed_servers_lock:
            self.failed_servers = {}
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}▶️  RESUMING EMAIL SENDING{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔄 Reset failed servers counter{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📧 Available SMTP servers: {len(self.smtp_servers)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        self.log_message(f"▶️ Resuming operations with {len(self.smtp_servers)} SMTP servers", 'success')
        self.console_print(f"▶️ RESUMED - Using {len(self.smtp_servers)} SMTP servers", 'green')
        
        # Unpause
        self.smtp_paused = False
        self.smtp_pause_event.set()
        
        # Disable resume button
        if hasattr(self, 'resume_smtp_btn'):
            self.resume_smtp_btn.config(state=tk.DISABLED)
        
        self.status_label.config(text="Status: Running", foreground='green')
        
    # Inbox Monitoring Functions
    def browse_thunderbird_path(self):
        path = filedialog.askdirectory(title="Select Thunderbird ImapMail Directory")
        if path:
            self.thunderbird_path_var.set(path)
            self.thunderbird_path = path
            self.monitor_log_print("📁 Path updated: " + path, 'info')
            print(f"{Fore.CYAN}[CONFIG] Thunderbird path updated: {path}{Style.RESET_ALL}")
            self.save_config()
    
    def edit_thunderbird_path(self):
        """Edit Thunderbird path via popup dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Thunderbird Path")
        dialog.geometry("600x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Thunderbird ImapMail Path:", font=('Arial', 10, 'bold')).pack(pady=(20, 5))
        
        path_var = tk.StringVar(value=self.thunderbird_path_var.get())
        path_entry = ttk.Entry(dialog, textvariable=path_var, width=70, font=('Courier New', 9))
        path_entry.pack(pady=10, padx=20)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save_path():
            new_path = path_var.get()
            if new_path:
                self.thunderbird_path_var.set(new_path)
                self.thunderbird_path = new_path
                self.monitor_log_print("✏️ Path edited: " + new_path, 'info')
                print(f"{Fore.CYAN}[CONFIG] Thunderbird path updated: {new_path}{Style.RESET_ALL}")
                self.save_config()
                dialog.destroy()
        
        def browse_path():
            path = filedialog.askdirectory(title="Select Thunderbird ImapMail Directory")
            if path:
                path_var.set(path)
        
        ttk.Button(btn_frame, text="📂 Browse", command=browse_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✅ Save", command=save_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def switch_monitor_mode(self):
        """Switch between Thunderbird and IMAP monitoring modes"""
        mode = self.monitor_mode_var.get()
        
        if self.is_monitoring:
            messagebox.showwarning("Stop First", "Please stop monitoring before switching modes!")
            # Revert to previous mode
            self.monitor_mode_var.set(self.monitor_mode)
            return
        
        self.monitor_mode = mode
        
        if mode == 'thunderbird':
            self.thunderbird_frame.grid()
            self.imap_frame.grid_remove()
            self.monitor_log_print("📂 Switched to Thunderbird mode", 'info')
        else:
            self.thunderbird_frame.grid_remove()
            self.imap_frame.grid()
            self.monitor_log_print("📧 Switched to IMAP mode", 'info')
            # Parse accounts if not already done
            if not self.imap_accounts:
                self.parse_imap_accounts()
    
    def parse_imap_accounts(self):
        """Parse IMAP accounts from textarea"""
        content = self.imap_accounts_text.get(1.0, tk.END).strip()
        lines = [line.strip() for line in content.split('\n') if line.strip() and ':' in line]
        
        self.imap_accounts = []
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                email, password = parts
                if '@' in email:
                    # Determine IMAP server from email domain
                    domain = email.split('@')[1].lower()
                    if 'att.net' in domain or 'yahoo' in domain:
                        imap_server = 'imap.mail.yahoo.com'
                    elif 'gmail' in domain:
                        imap_server = 'imap.gmail.com'
                    elif 'outlook' in domain or 'hotmail' in domain:
                        imap_server = 'outlook.office365.com'
                    elif 'currently.com' in domain:
                        imap_server = 'imap.mail.yahoo.com'  # Currently.com uses Yahoo
                    else:
                        imap_server = f'imap.{domain}'
                    
                    self.imap_accounts.append({
                        'email': email,
                        'password': password,
                        'server': imap_server,
                        'port': 993
                    })
        
        self.imap_accounts_label.config(text=f"✓ {len(self.imap_accounts)} accounts loaded", 
                                       foreground='green' if self.imap_accounts else 'red')
        self.monitor_log_print(f"✅ Parsed {len(self.imap_accounts)} IMAP accounts", 'success')
        print(f"{Fore.GREEN}[IMAP] Loaded {len(self.imap_accounts)} accounts{Style.RESET_ALL}")
    
    def manual_imap_check(self):
        """Manually trigger IMAP check"""
        if not self.imap_accounts:
            messagebox.showwarning("No Accounts", "Please parse IMAP accounts first!")
            return
        
        self.monitor_log_print("🔍 Manual IMAP check started...", 'info')
        print(f"{Fore.CYAN}[IMAP] Manual check initiated{Style.RESET_ALL}")
        
        # Run check in background thread
        check_thread = threading.Thread(target=self.check_imap_accounts, daemon=True)
        check_thread.start()
    
    def check_imap_accounts(self):
        """Check all IMAP accounts for new emails"""
        import imaplib
        import email
        from email.header import decode_header
        
        new_found = 0
        
        for account in self.imap_accounts:
            if not self.is_monitoring and self.monitor_mode != 'imap':
                break
            
            try:
                self.monitor_log_print(f"📧 Checking {account['email']}...", 'info')
                
                # Connect to IMAP
                mail = imaplib.IMAP4_SSL(account['server'], account['port'], timeout=30)
                mail.login(account['email'], account['password'])
                mail.select('INBOX')
                
                # Search for all messages
                status, message_ids = mail.search(None, 'ALL')
                if status != 'OK':
                    continue
                
                message_id_list = message_ids[0].split()
                
                for msg_id in message_id_list:
                    if not self.is_monitoring and self.monitor_mode != 'imap':
                        break
                    
                    # Create unique message ID for tracking
                    unique_msg_id = f"{account['email']}:{msg_id.decode()}"
                    
                    # Skip if already seen
                    if unique_msg_id in self.imap_seen_message_ids:
                        continue
                    
                    # Fetch message
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Get FROM header
                    from_header = msg.get('From', '')
                    if from_header:
                        from_header = self.decode_mime_header(from_header)
                        email_address = self.extract_email_address(from_header)
                        
                        # Check if it's a recipient - only save FROM addresses
                        is_recipient = email_address in self.recipient_email_list
                        
                        if is_recipient:
                            self.monitor_log_print(f"   ⚠️  SKIPPED: {email_address} (recipient)", 'warning')
                        else:
                            # New FROM address found!
                            subject = msg.get('Subject', '(No Subject)')
                            subject = self.decode_mime_header(subject)
                            
                            print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
                            print(f"{Fore.GREEN}🆕 NEW EMAIL FROM IMAP!{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}   📧 Account: {account['email']}{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}   👤 From: {from_header}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}   📝 Subject: {subject[:50]}{Style.RESET_ALL}")
                            print(f"{Fore.GREEN}   ✉️  Email: {email_address}{Style.RESET_ALL}")
                            
                            self.monitor_log_print(f"🆕 NEW: {email_address}", 'success')
                            self.monitor_log_print(f"   From account: {account['email']}", 'info')
                            
                            # Save FROM address
                            self.save_from_address(email_address)
                            new_found += 1
                        
                        # Mark as seen
                        self.imap_seen_message_ids.add(unique_msg_id)
                
                mail.close()
                mail.logout()
                
                self.monitor_log_print(f"   ✓ {account['email']}: {len(message_id_list)} messages checked", 'info')
                
            except Exception as e:
                error_msg = str(e)
                self.monitor_log_print(f"   ✗ Error checking {account['email']}: {error_msg[:50]}", 'error')
                print(f"{Fore.RED}[IMAP] Error: {account['email']} - {error_msg}{Style.RESET_ALL}")
        
        if new_found > 0:
            self.monitor_log_print(f"✅ Found {new_found} new FROM addresses from IMAP", 'success')
        else:
            self.monitor_log_print("✓ No new emails found", 'info')
    
    def decode_mime_header(self, header_text):
        """Decode MIME encoded header"""
        from email.header import decode_header
        decoded_parts = []
        for part, encoding in decode_header(header_text):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)
    
    def auto_start_monitoring(self):
        """Auto-start monitoring when GUI loads"""
        if not self.is_monitoring:
            # Parse IMAP accounts on startup
            if self.monitor_mode == 'imap':
                self.parse_imap_accounts()
            self.start_monitoring()
            self.monitor_log_print("🚀 Auto-started monitoring on GUI load", 'success')
            print(f"{Fore.GREEN}[AUTO-START] Monitoring started automatically{Style.RESET_ALL}")
            
    def monitor_log_print(self, message, tag='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.monitor_log.see(tk.END)
        
    def start_monitoring(self):
        if self.is_monitoring:
            messagebox.showwarning("Already Running", "Monitoring is already active!")
            return
        
        # Validate based on mode
        if self.monitor_mode == 'thunderbird':
            path = self.thunderbird_path_var.get()
            if not os.path.exists(path):
                messagebox.showerror("Invalid Path", f"Path does not exist:\n{path}")
                print(f"{Fore.RED}[ERROR] Invalid path: {path}{Style.RESET_ALL}")
                return
        else:
            # IMAP mode
            if not self.imap_accounts:
                messagebox.showwarning("No Accounts", "Please parse IMAP accounts first!")
                return
            
        self.is_monitoring = True
        self.start_monitor_btn.config(state=tk.DISABLED)
        self.stop_monitor_btn.config(state=tk.NORMAL)
        self.monitor_status_label.config(text="🟢 Monitoring: ACTIVE", foreground='green')
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🚀 INBOX MONITOR STARTING...{Style.RESET_ALL}")
        if self.monitor_mode == 'thunderbird':
            print(f"{Fore.CYAN}[MODE] Thunderbird (Local){Style.RESET_ALL}")
            print(f"{Fore.CYAN}[PATH] {path}{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}[MODE] IMAP (Remote){Style.RESET_ALL}")
            print(f"{Fore.CYAN}[ACCOUNTS] {len(self.imap_accounts)} accounts{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        self.monitor_log_print("=" * 60, 'info')
        self.monitor_log_print(f"🚀 Starting Inbox Monitor ({self.monitor_mode.upper()})...", 'success')
        if self.monitor_mode == 'thunderbird':
            self.monitor_log_print(f"📂 Path: {path}", 'info')
        else:
            self.monitor_log_print(f"📧 Accounts: {len(self.imap_accounts)}", 'info')
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        self.start_monitor_btn.config(state=tk.NORMAL)
        self.stop_monitor_btn.config(state=tk.DISABLED)
        self.monitor_status_label.config(text="⚫ Monitoring: STOPPED", foreground='red')
        
        print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🛑 INBOX MONITOR STOPPED{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Total emails collected: {self.fake_from_counter}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")
        
        self.monitor_log_print("🛑 Monitoring stopped by user", 'warning')
        self.monitor_log_print("=" * 60, 'info')
        
    def monitoring_loop(self):
        """Main monitoring loop - runs in background thread"""
        check_interval = 300 if self.monitor_mode == 'imap' else 60  # IMAP: 5 mins, Thunderbird: 1 min
        check_count = 0
        
        try:
            if self.monitor_mode == 'thunderbird':
                # Thunderbird mode - initial scan
                print(f"{Fore.CYAN}🔍 Performing initial scan...{Style.RESET_ALL}")
                self.monitor_log_print("🔍 Performing initial scan...", 'info')
                accounts = self.find_all_inboxes()
            else:
                # IMAP mode - initial check
                print(f"{Fore.CYAN}🔍 Performing initial IMAP check...{Style.RESET_ALL}")
                self.monitor_log_print("🔍 Initial IMAP check...", 'info')
                self.check_imap_accounts()
                accounts = self.imap_accounts
            
            if not accounts:
                if self.monitor_mode == 'thunderbird':
                    print(f"{Fore.RED}❌ No INBOX files found!{Style.RESET_ALL}")
                    self.monitor_log_print("❌ No INBOX files found!", 'error')
                else:
                    print(f"{Fore.RED}❌ No IMAP accounts configured!{Style.RESET_ALL}")
                    self.monitor_log_print("❌ No IMAP accounts!", 'error')
                self.root.after(0, self.stop_monitoring)
                return
                
            print(f"{Fore.GREEN}✅ Found {len(accounts)} accounts{Style.RESET_ALL}")
            self.root.after(0, lambda: self.monitor_accounts_label.config(text=f"Active Accounts: {len(accounts)}"))
            self.monitor_log_print(f"✅ Found {len(accounts)} accounts", 'success')
            
            if self.monitor_mode == 'thunderbird':
                # Initial email scan for Thunderbird
                total_initial = 0
                for account in accounts:
                    emails = self.parse_inbox_file(account['path'])
                    account['email_count'] = len(emails)
                    total_initial += len(emails)
                    
                    # Mark all as seen
                    for email in emails:
                        self.seen_emails.add(email['hash'])
                    
                    print(f"{Fore.CYAN}  {account['account'][:30]:30s} : {len(emails):3d} emails{Style.RESET_ALL}")
                    self.monitor_log_print(f"  {account['account'][:30]:30s} : {len(emails):3d} emails", 'info')
                
                print(f"{Fore.GREEN}📊 Total: {total_initial} emails tracked{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⏰ Checking for new emails every 60 seconds{Style.RESET_ALL}")
                
                self.monitor_log_print(f"📊 Total: {total_initial} emails tracked", 'success')
                self.monitor_log_print("⏰ Checking for new emails every 60 seconds", 'info')
            else:
                # IMAP mode
                print(f"{Fore.GREEN}📧 {len(accounts)} IMAP accounts ready{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⏰ Checking for new emails every 5 minutes (300 seconds){Style.RESET_ALL}")
                
                self.monitor_log_print(f"📧 {len(accounts)} IMAP accounts initialized", 'success')
                self.monitor_log_print("⏰ Checking for new emails every 5 minutes", 'info')
            
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
            self.monitor_log_print("=" * 60, 'info')
            
            # Monitoring loop
            while self.is_monitoring:
                check_count += 1
                time.sleep(check_interval)
                
                if not self.is_monitoring:
                    break
                    
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.root.after(0, lambda t=timestamp: self.monitor_check_label.config(text=f"Last Check: {t}"))
                
                print(f"{Fore.CYAN}[{timestamp}] 🔄 Check #{check_count}: Scanning for new emails...{Style.RESET_ALL}")
                self.monitor_log_print(f"🔄 Check #{check_count}: Scanning for new emails...", 'info')
                
                # Check for new emails based on mode
                if self.monitor_mode == 'imap':
                    # IMAP mode - check all accounts
                    self.check_imap_accounts()
                    new_found = False  # Already handled in check_imap_accounts
                else:
                    # Thunderbird mode - check local files
                    new_found = False
                    for account in accounts:
                        emails = self.parse_inbox_file(account['path'])
                        
                        for email in emails:
                            if email['hash'] not in self.seen_emails:
                                new_found = True
                                
                                # Extract email address
                                email_address = self.extract_email_address(email['from'])
                                
                                print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
                                print(f"{Fore.GREEN}🆕 NEW EMAIL DETECTED!{Style.RESET_ALL}")
                                print(f"{Fore.CYAN}   📧 Account: {account['account']}{Style.RESET_ALL}")
                                print(f"{Fore.CYAN}   👤 From: {email['from']}{Style.RESET_ALL}")
                                print(f"{Fore.YELLOW}   📝 Subject: {email['subject'][:50]}{Style.RESET_ALL}")
                                print(f"{Fore.GREEN}   ✉️  Email: {email_address}{Style.RESET_ALL}")
                                
                                self.monitor_log_print(f"🆕 NEW EMAIL DETECTED!", 'success')
                                self.monitor_log_print(f"   📧 Account: {account['account']}", 'info')
                                self.monitor_log_print(f"   👤 From: {email['from']}", 'info')
                                self.monitor_log_print(f"   ✉️  Email: {email_address}", 'success')
                                
                                # Check if it's a recipient - only save FROM addresses
                                is_recipient = email_address in self.recipient_email_list
                                
                                if is_recipient:
                                    print(f"{Fore.YELLOW}   ⚠️  SKIPPED: This is a recipient, not a FROM address{Style.RESET_ALL}")
                                    self.monitor_log_print(f"   ⚠️  SKIPPED: Recipient email, not FROM address", 'warning')
                                else:
                                    # Save to from.txt and update counter (only FROM addresses)
                                    self.save_from_address(email_address)
                                    print(f"{Fore.GREEN}   ✅ Saved FROM address{Style.RESET_ALL}")
                                
                                # Mark as seen (even if skipped)
                                self.seen_emails.add(email['hash'])
                    
                    if not new_found:
                        print(f"{Fore.CYAN}   ✓ No new emails detected{Style.RESET_ALL}")
                        self.monitor_log_print("   ✓ No new emails detected", 'info')
                    
        except Exception as e:
            print(f"{Fore.RED}❌ MONITORING ERROR: {str(e)}{Style.RESET_ALL}")
            self.monitor_log_print(f"❌ ERROR: {str(e)}", 'error')
        finally:
            self.root.after(0, self.stop_monitoring)
            
    def find_all_inboxes(self):
        """Find all INBOX files in Thunderbird ImapMail directory"""
        accounts = []
        path = self.thunderbird_path_var.get()
        
        try:
            for root_dir, dirs, files in os.walk(path):
                if 'INBOX' in files:
                    inbox_path = os.path.join(root_dir, 'INBOX')
                    account_name = os.path.basename(root_dir)
                    accounts.append({
                        'account': account_name,
                        'path': inbox_path,
                        'email_count': 0
                    })
        except Exception as e:
            self.monitor_log_print(f"Error scanning path: {e}", 'error')
            
        return accounts
        
    def parse_inbox_file(self, inbox_path):
        """Parse mbox format INBOX file"""
        emails = []
        
        try:
            with open(inbox_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Split by mbox "From " delimiter
            messages = re.split(r'\n(?=From - )', content)
            
            for msg in messages:
                if not msg.strip():
                    continue
                    
                # Extract From header
                from_match = re.search(r'^From:\s*(.+?)$', msg, re.MULTILINE | re.IGNORECASE)
                subject_match = re.search(r'^Subject:\s*(.+?)$', msg, re.MULTILINE | re.IGNORECASE)
                date_match = re.search(r'^Date:\s*(.+?)$', msg, re.MULTILINE | re.IGNORECASE)
                
                if from_match:
                    from_header = from_match.group(1).strip()
                    subject = subject_match.group(1).strip() if subject_match else "(No Subject)"
                    date_header = date_match.group(1).strip() if date_match else None
                    
                    # Create hash for duplicate detection
                    email_hash = hashlib.md5(msg.encode('utf-8', errors='ignore')).hexdigest()
                    
                    emails.append({
                        'from': from_header,
                        'subject': subject,
                        'date': date_header,
                        'hash': email_hash
                    })
                    
        except Exception as e:
            self.monitor_log_print(f"Error parsing {inbox_path}: {e}", 'error')
            
        return emails
        
    def extract_email_address(self, from_header):
        """Extract clean email address from 'Name <email>' format"""
        match = re.search(r'<(.+?)>', from_header)
        if match:
            return match.group(1).strip()
        return from_header.strip()
        
    def save_from_address(self, email_address):
        """Save FROM address and auto-add to verified textarea - Filter recipients"""
        # CRITICAL: Skip if this is a recipient (prevent contamination)
        if email_address in self.recipient_email_list:
            self.console_print(f"⚠️ BLOCKED recipient from being saved: {email_address}", 'red')
            return
        
        # CRITICAL: Prevent memory overflow - Limit to 500K emails (increased from 100K)
        MAX_COLLECTED = 500000
        if len(self.collected_from_emails) >= MAX_COLLECTED:
            self.console_print(f"⚠️ LIMIT REACHED: {MAX_COLLECTED:,} emails collected. Add to verified and clear to continue.", 'red')
            return
        
        # Save to from.txt file
        FileOperations.save_from_address(self, email_address)
        
        # Save to collected_from.txt (dedicated file for collected FROM addresses)
        try:
            import os
            # Read existing collected addresses
            existing = set()
            if os.path.exists('collected_from.txt'):
                with open('collected_from.txt', 'r', encoding='utf-8') as f:
                    existing = set([line.strip() for line in f if line.strip()])
            
            # Add new address if not already present
            if email_address not in existing:
                with open('collected_from.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{email_address}\n")
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as e:
            self.console_print(f"⚠️ Error saving to collected_from.txt: {e}", 'yellow')
        
        # Add to collected emails list (persistent) - ONLY FROM addresses, verified recipient check
        if email_address not in self.collected_from_emails and email_address not in self.recipient_email_list:
            self.collected_from_emails.append(email_address)
        elif email_address in self.recipient_email_list:
            self.console_print(f"⚠️ BLOCKED recipient from collected list: {email_address}", 'red')
            return
        
        # Auto-add to verified list and textarea if not already there (remove duplicates)
        if email_address not in self.verified_froms:
            self.verified_froms.append(email_address)
            
            # Add to textarea (check for duplicates)
            current_content = self.verified_from_text.get(1.0, tk.END).strip()
            existing_emails = set([line.strip() for line in current_content.split('\n') if line.strip() and '@' in line])
            
            if email_address not in existing_emails:
                self.verified_from_text.insert(tk.END, f"{email_address}\n")
                self.console_print(f"✅ Auto-added to verified: {email_address}", 'green')
                
                # Update stats
                self.update_verification_stats()
                
                # Save verified list to file for persistence
                try:
                    with open('verified_from.txt', 'w', encoding='utf-8') as f:
                        f.write('\n'.join(self.verified_froms))
                        f.flush()
                        os.fsync(f.fileno())
                except Exception as e:
                    self.log_message(f"Error saving verified list: {e}", 'warning')
    
    def update_verification_stats(self):
        """Update verification statistics display"""
        try:
            verified_count = len(self.verified_froms)
            unverified_count = len(self.unverified_froms)
            total_count = verified_count + unverified_count
            
            stats_text = f"Total: {total_count} | Verified: {verified_count} | Unverified: {unverified_count}"
            self.verify_stats_label.config(text=stats_text)
        except Exception as e:
            pass
    
    def reload_from_addresses(self): FileOperations.reload_from_addresses(self)
    def refresh_collected_froms(self): FileOperations.refresh_collected_froms(self)
    
    def add_all_collected_to_verified(self):
        """Add all collected FROM addresses from collected_from.txt to verified textarea"""
        # Load from collected_from.txt (dedicated file for collected FROM addresses)
        import os
        all_from_emails = set()
        
        if not os.path.exists('collected_from.txt'):
            messagebox.showinfo("No File", "collected_from.txt not found!\n\nStart monitoring to collect FROM addresses.")
            return
        
        try:
            with open('collected_from.txt', 'r', encoding='utf-8') as f:
                # Create recipient set for filtering
                recipient_set = set(self.recipient_email_list)
                
                for line in f:
                    email = line.strip()
                    if email and '@' in email:
                        # Filter out recipients
                        if email not in recipient_set:
                            all_from_emails.add(email)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading collected_from.txt: {e}")
            return
        
        if not all_from_emails:
            messagebox.showinfo("No Emails", "No FROM addresses in collected_from.txt!\n\nAll may be recipients (filtered).")
            return
        
        # Get current verified emails from textarea
        current_content = self.verified_from_text.get(1.0, tk.END).strip()
        existing_emails = set([line.strip() for line in current_content.split('\n') if line.strip() and '@' in line])
        
        # Add all FROM emails (already filtered, no recipients)
        new_count = 0
        for email in all_from_emails:
            if email not in existing_emails:
                existing_emails.add(email)
                if email not in self.verified_froms:
                    self.verified_froms.append(email)
                new_count += 1
        
        # Remove from unverified if present
        for email in all_from_emails:
            if email in self.unverified_froms:
                self.unverified_froms.remove(email)
        
        # Update textarea with sorted unique emails
        self.verified_from_text.delete(1.0, tk.END)
        for email in sorted(existing_emails):
            self.verified_from_text.insert(tk.END, f"{email}\n")
        
        # Update stats
        self.update_verification_stats()
        
        # Save to file
        try:
            with open('verified_from.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(existing_emails)))
        except Exception as e:
            pass
        
        # Clear collected_from.txt after adding (start fresh)
        try:
            with open('collected_from.txt', 'w', encoding='utf-8') as f:
                f.write('')  # Clear file
        except:
            pass
        
        # Clear the collected counter
        old_collected = len(self.collected_from_emails)
        self.collected_from_emails.clear()
        self.fake_from_counter = 0
        self.fake_from_label.config(text="0")
        
        messagebox.showinfo("Success", 
            f"✅ Added {new_count} new FROM addresses to Verified!\n\n"
            f"Source: collected_from.txt\n"
            f"Total Verified: {len(existing_emails)}\n\n"
            f"🗑️ Auto-cleared collected_from.txt"
        )
        self.console_print(f"✅ Added {new_count} FROM addresses to Verified from collected_from.txt", 'green')
        self.console_print(f"🗑️ Auto-cleared collected_from.txt", 'yellow')
    
    def clear_verified_emails(self):
        """Properly clear verified emails from UI and memory"""
        if not self.verified_froms and self.verified_from_text.get(1.0, tk.END).strip() == "":
            messagebox.showinfo("Already Empty", "Verified list is already empty!")
            return
        
        result = messagebox.askyesno(
            "Clear Verified Emails",
            f"⚠️ Clear {len(self.verified_froms)} verified emails?\n\nThis will clear them from memory and config."
        )
        
        if result:
            self.verified_from_text.delete(1.0, tk.END)
            self.verified_froms.clear()
            self.update_verification_stats()
            self.config_manager.save_config(self)
            # Also clear the file
            try:
                with open('verified_from.txt', 'w', encoding='utf-8') as f:
                    f.write('')
            except:
                pass
            self.console_print("🗑️ Verified emails cleared", 'yellow')
    
    def clear_unverified_emails(self):
        """Properly clear unverified emails from UI and memory"""
        if not self.unverified_froms and self.unverified_from_text.get(1.0, tk.END).strip() == "":
            messagebox.showinfo("Already Empty", "Unverified list is already empty!")
            return
        
        result = messagebox.askyesno(
            "Clear Unverified Emails",
            f"⚠️ Clear {len(self.unverified_froms)} unverified emails?\n\nThis will clear them from memory and config."
        )
        
        if result:
            self.unverified_from_text.delete(1.0, tk.END)
            self.unverified_froms.clear()
            self.update_verification_stats()
            self.config_manager.save_config(self)
            # Also clear the file
            try:
                with open('unverified_from.txt', 'w', encoding='utf-8') as f:
                    f.write('')
            except:
                pass
            self.console_print("🗑️ Unverified emails cleared", 'yellow')
    
    def clear_all_collected(self):
        """Clear all collected emails counter and list"""
        if not self.collected_from_emails:
            messagebox.showinfo("Already Empty", "No collected emails to clear!")
            return
        
        result = messagebox.askyesno(
            "Clear Collected Emails", 
            f"⚠️ Are you sure you want to clear all {len(self.collected_from_emails)} collected emails?\n\n"
            "This will reset the counter but keep verified/unverified lists intact."
        )
        
        if result:
            old_count = len(self.collected_from_emails)
            self.collected_from_emails.clear()
            self.fake_from_counter = 0
            self.fake_from_label.config(text="0")
            self.config_manager.save_config(self)
            
            # Also clear collected_from.txt
            try:
                with open('collected_from.txt', 'w', encoding='utf-8') as f:
                    f.write('')
            except:
                pass
            
            self.console_print(f"🗑️ Cleared {old_count} collected emails", 'yellow')
            messagebox.showinfo("Cleared", f"✅ Cleared {old_count} collected emails!")
    
    def apply_verified_textarea(self):
        """Parse and apply emails from verified textarea - Adds to verified_froms list for recheck"""
        content = self.verified_from_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Empty", "Verified textarea is empty!")
            return
        
        # Parse emails from textarea
        emails = set([line.strip() for line in content.split('\n') if line.strip() and '@' in line])
        
        if not emails:
            messagebox.showwarning("No Emails", "No valid email addresses found in textarea!")
            return
        
        # Update verified_froms list with unique emails (for recheck)
        old_count = len(self.verified_froms)
        self.verified_froms = list(emails)
        
        # Remove from unverified if present
        for email in emails:
            if email in self.unverified_froms:
                self.unverified_froms.remove(email)
        
        # Update textarea with clean sorted list
        self.verified_from_text.delete(1.0, tk.END)
        for email in sorted(emails):
            self.verified_from_text.insert(tk.END, f"{email}\n")
        
        # Update label with count
        if hasattr(self, 'verified_label'):
            self.verified_label.config(text=f"✅ Verified ({len(self.verified_froms)})")
        
        # Update stats
        self.update_verification_stats()
        
        # Save to file (for persistence)
        try:
            with open('verified_from.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(emails)))
        except Exception as e:
            pass
        
        new_count = len(self.verified_froms)
        added_to_list = len(emails - set(self.verified_froms[:old_count])) if old_count > 0 else new_count
        
        messagebox.showinfo("Applied", f"✅ Applied {new_count} verified emails!\n\n✓ Added to verified_froms list\n✓ Ready for recheck\n\nPrevious: {old_count}\nCurrent: {new_count}\nDuplicates removed: {len(content.split('\n')) - new_count}")
        self.console_print(f"✅ Applied {new_count} verified emails to verified_froms list", 'green')
        self.console_print(f"✓ Emails ready for recheck with 🔄 button", 'cyan')
    
    def apply_unverified_textarea(self):
        """Parse and apply emails from unverified textarea - Adds to unverified_froms list for recheck"""
        content = self.unverified_from_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Empty", "Unverified textarea is empty!")
            return
        
        # Parse emails from textarea
        emails = set([line.strip() for line in content.split('\n') if line.strip() and '@' in line])
        
        if not emails:
            messagebox.showwarning("No Emails", "No valid email addresses found in textarea!")
            return
        
        # Update unverified_froms list with unique emails (for recheck)
        old_count = len(self.unverified_froms)
        self.unverified_froms = list(emails)
        
        # Remove from verified if present
        for email in emails:
            if email in self.verified_froms:
                self.verified_froms.remove(email)
        
        # Update textarea with clean sorted list
        self.unverified_from_text.delete(1.0, tk.END)
        for email in sorted(emails):
            self.unverified_from_text.insert(tk.END, f"{email}\n")
        
        # Update label with count
        if hasattr(self, 'unverified_label'):
            self.unverified_label.config(text=f"❌ Unverified ({len(self.unverified_froms)})")
        
        # Update stats
        self.update_verification_stats()
        
        # Save to file (for persistence)
        try:
            with open('unverified_from.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(emails)))
        except Exception as e:
            pass
        
        new_count = len(self.unverified_froms)
        messagebox.showinfo("Applied", f"✅ Applied {new_count} unverified emails!\n\n✓ Added to unverified_froms list\n✓ Ready for recheck\n\nPrevious: {old_count}\nCurrent: {new_count}\nDuplicates removed: {len(content.split('\n')) - new_count}")
        self.console_print(f"✅ Applied {new_count} unverified emails to unverified_froms list", 'yellow')
        self.console_print(f"✓ Emails ready for recheck with 🔄 button", 'cyan')
    
    # New verification manager methods
    def start_verification(self, mode='all'):
        self.verification_manager.start_verification(mode)
        # Enable pause button when verification starts
        self.pause_verify_btn.config(state=tk.NORMAL)
        self.resume_verify_btn.config(state=tk.DISABLED)
    def pause_verification(self):
        self.verification_manager.pause_verification()
        self.pause_verify_btn.config(state=tk.DISABLED)
        self.resume_verify_btn.config(state=tk.NORMAL)
        self.verification_log_print("⏸️ Verification PAUSED - Click Resume to continue", 'warning')
    def resume_verification(self):
        self.verification_manager.resume_verification()
        self.resume_verify_btn.config(state=tk.DISABLED)
        self.pause_verify_btn.config(state=tk.NORMAL)
        self.verification_log_print("▶️ Verification RESUMED", 'success')
    def stop_verification(self):
        self.verification_manager.stop_verification()
        self.pause_verify_btn.config(state=tk.NORMAL)
        self.resume_verify_btn.config(state=tk.DISABLED)
    
    def save_verified_froms(self): FileOperations.save_verified_froms(self)
    def save_unverified_froms(self): FileOperations.save_unverified_froms(self)
    def load_verified_froms(self): FileOperations.load_verified_froms(self)
    def load_unverified_froms(self): FileOperations.load_unverified_froms(self)
    
    # New methods for individual textarea save/load
    def save_verified_froms_to_file(self): FileOperations.save_verified_froms_to_file(self)
    def load_verified_froms_from_file(self): FileOperations.load_verified_froms_from_file(self)
    def save_unverified_froms_to_file(self): FileOperations.save_unverified_froms_to_file(self)
    def load_unverified_froms_from_file(self): FileOperations.load_unverified_froms_from_file(self)
    
    def remove_failed_smtps(self):
        """Remove SMTP servers that have failed from the textarea"""
        if not self.failed_servers:
            messagebox.showinfo("No Failed Servers", "There are no failed SMTP servers to remove.")
            return
        
        # Get current SMTP text
        current_text = self.smtp_text.get(1.0, tk.END).strip()
        lines = [line.strip() for line in current_text.split('\n') if line.strip()]
        
        # Parse and filter out failed servers
        cleaned_lines = []
        removed_count = 0
        
        for line in lines:
            is_failed = False
            
            # Parse line to get host:port
            if ':' in line and line.count(':') >= 3:
                # New format: username:password:host:port
                parts = line.split(':')
                if len(parts) >= 4:
                    server_key = f"{parts[2].strip()}:{parts[3].strip()}"
                    if server_key in self.failed_servers:
                        is_failed = True
                        removed_count += 1
            elif ',' in line:
                # Old format: host,port,username,password
                parts = line.split(',')
                if len(parts) >= 4:
                    server_key = f"{parts[0].strip()}:{parts[1].strip()}"
                    if server_key in self.failed_servers:
                        is_failed = True
                        removed_count += 1
            
            if not is_failed:
                cleaned_lines.append(line)
        
        # Update textarea
        self.smtp_text.delete(1.0, tk.END)
        self.smtp_text.insert(1.0, '\\n'.join(cleaned_lines))
        
        # Clear failed servers dict
        with self.failed_servers_lock:
            self.failed_servers = {}
        
        # Reparse
        self.parse_smtp_servers()
        
        messagebox.showinfo("SMTPs Cleaned", f"Removed {removed_count} failed SMTP server(s).\\n\\n"
                                              f"Remaining: {len(cleaned_lines)} servers")
    
    def save_config(self): self.config_manager.save_config(self)
    def load_config(self): self.config_manager.load_config(self)
    def apply_pending_config(self): self.config_manager.apply_pending_config(self)
    
    def apply_and_save_config(self):
        """Apply and save all configuration changes immediately"""
        try:
            # Force apply all settings
            threads = self.threads_var.get()
            sleep_time = self.sleep_time_var.get()
            test_mode = self.test_mode_var.get()
            debug_mode = self.debug_mode_var.get()
            
            # Log what's being applied
            self.console_print("="*60, 'cyan')
            self.console_print("✅ APPLYING CONFIGURATION", 'green')
            self.console_print(f"   Threads: {threads}", 'white')
            self.console_print(f"   Sleep Time: {sleep_time}s", 'white')
            self.console_print(f"   Test Mode: {test_mode}", 'white')
            self.console_print(f"   Debug Mode: {debug_mode}", 'white')
            self.console_print(f"   Sender Name: {self.sender_name_var.get()}", 'white')
            self.console_print(f"   Subject: {self.subject_var.get()}", 'white')
            self.console_print("="*60, 'cyan')
            
            # Save to config file
            self.config_manager.save_config(self)
            
            # Show confirmation
            messagebox.showinfo(
                "Configuration Applied",
                f"✅ Configuration applied and saved!\n\n"
                f"Threads: {threads}\n"
                f"Sleep Time: {sleep_time}s\n"
                f"Test Mode: {test_mode}\n"
                f"Debug Mode: {debug_mode}\n\n"
                f"Changes will take effect on next send."
            )
            
            self.log_message("✅ Configuration applied and saved", 'success')
            
        except Exception as e:
            messagebox.showerror("Configuration Error", f"Error applying config: {e}")
            self.log_message(f"❌ Config error: {e}", 'error')
        
    def remove_sent_from_address(self, from_address):
        """Remove sent FROM address from list and update ALL displays in real-time"""
        removed = False
        try:
            with self.from_addresses_lock:
                if from_address in self.from_addresses:
                    self.from_addresses.remove(from_address)
                    removed = True
                else:
                    # Address not in list - might be a format mismatch or already removed
                    pass
                    
                # Update the textarea in GUI thread
                def update_ui():
                    try:
                        # Get current content
                        current_content = self.from_text.get(1.0, tk.END)
                        lines = [line.strip() for line in current_content.split('\n') if line.strip()]
                        
                        # Remove the sent address
                        if from_address in lines:
                            lines.remove(from_address)
                        
                        # Update textarea
                        self.from_text.delete(1.0, tk.END)
                        self.from_text.insert(1.0, '\n'.join(lines))
                        
                        # Update counter with CURRENT list size
                        remaining_count = len(self.from_addresses)
                        self.from_count_label.config(text=f"From addresses remaining: {remaining_count}")
                        
                        # Update stats panel if it exists
                        if hasattr(self, 'remaining_from_label'):
                            self.remaining_from_label.config(text=f"Remaining FROM: {remaining_count}")
                        
                        # Force immediate stats update
                        if hasattr(self, 'update_verification_stats'):
                            self.update_verification_stats()
                        
                        # Force stats update
                        if hasattr(self, 'update_stats'):
                            self.update_stats()
                        
                        # Force update
                        self.from_text.update_idletasks()
                        self.from_count_label.update_idletasks()
                    except Exception as e:
                        pass  # Fail silently if GUI update fails
                
                # Schedule UI update on main thread
                self.root.after(0, update_ui)
        except Exception as e:
            pass  # Fail silently
        
        return removed
    
    def check_for_vpn_drop(self, error_message):
        """Check if rapid failures indicate VPN drop - returns True if VPN recovery should trigger"""
        current_time = time.time()
        
        # Check if error is connection-related
        if not ("getaddrinfo failed" in str(error_message) or 
                "Connection" in str(error_message) or 
                "timed out" in str(error_message)):
            return False
        
        with self.failure_tracking_lock:
            # Add current failure
            self.recent_failures.append(current_time)
            
            # Remove old failures outside time window
            self.recent_failures = [t for t in self.recent_failures 
                                   if current_time - t <= self.rapid_failure_window]
            
            # Check if we've exceeded threshold
            if len(self.recent_failures) >= self.rapid_failure_threshold:
                # Clear failures list (recovery will handle it)
                self.recent_failures = []
                return True
        
        return False
    
    def send_emails_thread(self):
        """
        NEW ROUTING MODE:
        Iterate through all FROM addresses, rotating through the recipient pool
        """
        max_connections = self.threads_var.get()
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Starting ThreadPoolExecutor with {max_connections} threads{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_connections) as executor:
                futures = []
                
                # Create a copy of FROM addresses to iterate through (list will be modified during iteration)
                with self.from_addresses_lock:
                    from_addresses_snapshot = list(self.from_addresses)
                
                # Iterate through FROM addresses (main loop)
                for from_index, from_address in enumerate(from_addresses_snapshot):
                    if not self.is_running:
                        break
                    
                    # Get recipient by rotating through the pool
                    recipient_index = from_index % len(self.recipient_email_list)
                    recipient = self.recipient_email_list[recipient_index]
                    
                    # Submit email sending task with specific from/to pair
                    future = executor.submit(self.send_email_routing, from_address, recipient, from_index)
                    futures.append(future)
                    
                    # Small delay to allow thread pool to distribute work
                    # This helps ensure all threads are utilized
                    if len(futures) >= max_connections:
                        time.sleep(0.1)
                    
                # Wait for all to complete
                for future in concurrent.futures.as_completed(futures):
                    if not self.is_running:
                        break
                    try:
                        future.result()
                    except Exception as e:
                        self.log_message(f"Thread error: {e}", 'error')
                        self.console_print(f"ERROR - Thread exception: {str(e)[:100]}", 'red')
                        
        except Exception as e:
            self.log_message(f"Executor error: {e}", 'error')
            self.console_print(f"CRITICAL ERROR - Executor failed: {e}", 'red')
        finally:
            self.finish_sending()
            
    def send_email_routing(self, from_address, recipient_email, from_index):
        """
        NEW ROUTING MODE with 5-RETRY LOGIC:
        Send email using specific from_address to specific recipient
        Will retry up to 5 times with different SMTP servers before giving up
        from_index: position in the from_addresses list (for tracking)
        """
        if not self.is_running:
            return False
        
        # Wait if global connection recovery is in progress
        self.connection_recovery_event.wait()
        
        if not self.is_running:
            return False
            
        # Initialize variables
        max_retries = 5
        last_error = None
        fromane = from_address
        
        # Retry loop - try up to 5 times with different SMTP servers
        for attempt in range(max_retries):
            if not self.is_running:
                return False
                
            # Wait if paused
            self.connection_recovery_event.wait()
            
            server = None
            current_smtp = None
            new_value = "Unknown"
            
            try:
                # Use SMTP manager to get next available server (rotate to different one each attempt)
                current_smtp, server_key = self.smtp_manager.get_next_smtp()
                
                if current_smtp is None:
                    # All SMTP servers failed - trigger GLOBAL connection recovery (only on first attempt)
                    if attempt == 0:
                        with self.connection_recovery_lock:
                            if not self.global_connection_lost:
                                # First thread to detect connection loss - trigger recovery
                                self.global_connection_lost = True
                                self.connection_recovery_event.clear()  # Pause ALL threads
                                
                                print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                                print(f"{Fore.YELLOW}⚠️  GLOBAL CONNECTION LOSS DETECTED (VPN Change?){Style.RESET_ALL}")
                                print(f"{Fore.CYAN}🛑  Pausing ALL sending threads...{Style.RESET_ALL}")
                                print(f"{Fore.CYAN}💤 Sleeping 30 seconds for VPN/network recovery...{Style.RESET_ALL}")
                                print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")
                                
                                self.log_message("⚠️ Global connection lost - Pausing all threads for 30s recovery", 'warning')
                                self.console_print("🛑 Connection lost - ALL threads paused for 30s...", 'yellow')
                                
                                # Sleep 30 seconds for VPN recovery
                                time.sleep(30)
                                
                                if not self.is_running:
                                    self.connection_recovery_event.set()
                                    return False
                                
                                # Reset all SMTP failure counters (VPN change not server fault)
                                self.smtp_manager.reset_failures()
                                
                                print(f"{Fore.GREEN}🔄 Connection recovery complete - Resuming all threads...{Style.RESET_ALL}")
                                self.log_message("✅ Connection recovered - Resuming all threads", 'success')
                                self.console_print("✅ Connection recovered - Resuming all threads", 'green')
                                
                                # Resume all threads
                                self.global_connection_lost = False
                                self.connection_recovery_event.set()
                        
                        # Wait for recovery to complete
                        self.connection_recovery_event.wait()
                        
                        if not self.is_running:
                            return False
                        
                        # After recovery, retry getting SMTP
                        current_smtp, server_key = self.smtp_manager.get_next_smtp()
                    
                    if current_smtp is None:
                        # Still no SMTP available - skip this attempt
                        if attempt < max_retries - 1:
                            continue
                        else:
                            self.console_print(f"   ✗ FAILED: No SMTP available after {max_retries} attempts | FROM {from_address}", 'red')
                            return False
                
                # Reduced console spam - only show SMTP info every 10th email or on errors
                show_debug = (from_index + 1) % 10 == 0 or attempt > 0
                
                if show_debug and attempt == 0:
                    self.console_print(f"\n🔌 SMTP: {current_smtp['host']}:{current_smtp['port']} | User: {current_smtp['username']}", 'cyan')
                elif attempt > 0:
                    self.console_print(f"   🔄 Retry #{attempt+1}: {current_smtp['host']}:{current_smtp['port']}", 'yellow')
                
                server = smtplib.SMTP(current_smtp['host'], current_smtp['port'], timeout=30)
                
                # Connection successful - reset retry counter
                if self.connection_retry_count > 0:
                    self.connection_retry_count = 0
                
                # Enable STARTTLS for secure connection
                try:
                    server.starttls()
                    if show_debug and attempt == 0:
                        self.console_print(f"   🔒 STARTTLS: OK", 'green')
                except Exception as tls_error:
                    if show_debug:
                        self.console_print(f"   ⚠️ STARTTLS failed: {tls_error}", 'yellow')
                
                # Login
                try:
                    login_response = server.login(current_smtp['username'], current_smtp['password'])
                    if show_debug and attempt == 0:
                        self.console_print(f"   🔑 LOGIN: OK", 'green')
                except smtplib.SMTPAuthenticationError as auth_error:
                    # Mark SMTP as failed and log
                    self.console_print(f"   ❌ AUTH FAILED: {current_smtp['host']} - {auth_error}", 'red')
                    self.log_message(f"Auth failed for {current_smtp['username']}", 'error')
                    self.smtp_manager.mark_smtp_failed(server_key)
                    raise auth_error
                
                # Generate random numbers
                random_number = random.randint(100000, 999999)
                random_number_str = random.randint(10000, 99999)
                
                # Process template (NO LOGGING - reduces spam)
                text_filek = self.html_template
                
                # URL shortening (if enabled)
                if self.use_shortener_var.get():
                    try:
                        import gdshortener
                        s = gdshortener.ISGDShortener()
                        link_url = self.link_redirect_var.get()
                        url, _ = s.shorten(url=f'{link_url}?{random_number}={random_number}')
                        img_url, _ = s.shorten(url=link_url)
                        text_filek = text_filek.replace('LINKREDIRECT', url)
                        text_filek = text_filek.replace('IMGREDIRECT', img_url)
                    except Exception as e:
                        # Only log error once to prevent spam
                        if not self.url_shortener_error_logged:
                            self.log_message(f"URL shortening disabled: {e}", 'warning')
                            self.console_print(f"[WARNING] URL shortener failed - using direct links", 'yellow')
                            self.url_shortener_error_logged = True
                        text_filek = text_filek.replace('LINKREDIRECT', self.link_redirect_var.get())
                        text_filek = text_filek.replace('IMGREDIRECT', self.link_redirect_var.get())
                else:
                    text_filek = text_filek.replace('LINKREDIRECT', self.link_redirect_var.get())
                    text_filek = text_filek.replace('IMGREDIRECT', self.link_redirect_var.get())
                    
                text_filek = text_filek.replace('RANDOM', str(random_number))
                
                    # NO CONSOLE LOG for template processing - too much spam
                
                # Process sender name
                smtp_domain = current_smtp['username'].split('@')[-1] if '@' in current_smtp['username'] else self.domain_from_var.get()
                capitalized_domain = smtp_domain.split('.')[0].capitalize()
                
                sendernox = self.sender_name_var.get()
                if 'CapitalS' in sendernox:
                    new_value = sendernox.replace('CapitalS', capitalized_domain)
                    new_value = new_value.replace('randomchar', str(random_number_str))
                elif 'randomchar' in sendernox:
                    new_value = sendernox.replace('randomchar', str(random_number_str))
                else:
                    new_value = sendernox
                
                # Build message
                msg = MIMEMultipart("alternative")
                msg.set_boundary(self.generate_random_boundary())
                msg['From'] = f'{new_value} <{fromane}>'
                msg['Date'] = email.utils.formatdate(localtime=True)
                msg['To'] = recipient_email
                msg["Message-ID"] = f"<{str(uuid.uuid4())}@mta-2d57c4b7.i>"
                
                if self.important_var.get():
                    msg['Importance'] = "high"
                    msg['X-Priority'] = "1"
                
                # Process subject
                current_datetime = datetime.now()
                formatted_date = current_datetime.strftime("%A, %B %d, %Y")
                subject = self.subject_var.get()
                
                if 'CapitalS' in subject:
                    Newzepy = subject.replace('CapitalS', capitalized_domain)
                    Newzepy = Newzepy.replace('randomchar', str(random_number_str))
                    Newzepy = Newzepy.replace('DATEX', formatted_date)
                elif 'randomchar' in subject:
                    Newzepy = subject.replace('randomchar', str(random_number_str))
                    Newzepy = Newzepy.replace('DATEX', formatted_date)
                elif 'DATEX' in subject:
                    Newzepy = subject.replace('DATEX', formatted_date)
                else:
                    Newzepy = subject
                
                msg['Subject'] = Newzepy
                
                # Clean HTML and attach to message
                message_html_cleaned = ''.join(char if 32 <= ord(char) < 128 else ' ' for char in text_filek)
                letterx = MIMEText(message_html_cleaned, "html")
                msg.attach(letterx)
                
                # Send email and capture SMTP response
                send_response = server.sendmail(current_smtp['username'], [recipient_email], msg.as_string())
                
                # Analyze SMTP send response
                if send_response:
                    # If send_response has data, there were immediate rejections
                    for failed_recipient, (code, error_msg) in send_response.items():
                        error_text = error_msg.decode('utf-8', errors='ignore')[:150]
                        self.console_print(f"   ❌ SMTP {code}: {failed_recipient} - {error_text}", 'red')
                        self.log_message(f"SMTP Rejection {code}: {fromane} → {failed_recipient} - {error_text}", 'error')
                    # Mark as failed and retry
                    self.smtp_manager.mark_smtp_failed(server_key)
                    raise Exception(f"SMTP rejection: {send_response}")
                else:
                    # Message accepted by SMTP server (250 OK) - SUCCESS!
                    # Mark SMTP as successful to prevent premature removal
                    self.smtp_manager.mark_smtp_success(server_key)
                    
                    # Only show success every 5th email or on retry
                    if (from_index + 1) % 5 == 0 or attempt > 0:
                        retry_msg = f" (retry {attempt})" if attempt > 0 else ""
                        self.console_print(f"   ✅ SENT{retry_msg}: {fromane} → {recipient_email}", 'green')
                
                server.quit()
                
                # Update counters
                with self.total_emails_lock:
                    self.total_emails_sent += 1
                
                # Remove sent FROM address from list (ALWAYS remove after successful send)
                self.successfully_sent_emails.append(from_address)
                removal_success = self.remove_sent_from_address(from_address)
                
                # Show statistics every 5th email
                if self.total_emails_sent % 5 == 0:
                    with self.from_addresses_lock:
                        remaining = len(self.from_addresses)
                    self.console_print(
                        f"✅ Sent #{self.total_emails_sent}: FROM [{from_address}] → TO [{recipient_email}] | Remaining: {remaining}",
                        'green'
                    )
                
                # Show progress milestone every 50 emails
                if (from_index + 1) % 50 == 0:
                    self.console_print(f"→ Progress: {from_index+1} emails processed", 'cyan')
                
                # Sleep if configured
                sleep_time = self.sleep_time_var.get()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
                # Log milestone every 50th email
                if self.total_emails_sent % 50 == 0:
                    self.log_message(f"✓ Milestone: {self.total_emails_sent} emails sent", 'success')
                
                # Update progress
                self.root.after(0, self.update_progress)
                
                # EMAIL SENT SUCCESSFULLY - Return True
                return True
                
            except Exception as e:
                # Close server on error
                last_error = e
                try:
                    if server:
                        server.quit()
                except:
                    pass
                
                # Mark SMTP as failed
                if current_smtp:
                    self.smtp_manager.mark_smtp_failed(server_key)
                
                # Check if this is part of a rapid failure pattern (VPN drop)
                if self.check_for_vpn_drop(str(e)):
                    print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}⚠️  RAPID FAILURE PATTERN DETECTED - VPN Drop Suspected{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}🛑 Triggering global recovery...{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")
                    
                    # Trigger global connection recovery
                    with self.connection_recovery_lock:
                        if not self.global_connection_lost:
                            self.global_connection_lost = True
                            self.connection_recovery_event.clear()
                            
                            self.log_message("⚠️ Rapid failures detected - Triggering VPN recovery", 'warning')
                            self.console_print("🛑 VPN drop detected - Pausing all threads for 30s...", 'yellow')
                            
                            time.sleep(30)
                            
                            if not self.is_running:
                                self.connection_recovery_event.set()
                                return False
                            
                            self.smtp_manager.reset_failures()
                            
                            print(f"{Fore.GREEN}✅ VPN recovery complete{Style.RESET_ALL}")
                            self.log_message("✅ VPN recovery complete - All SMTP counters reset", 'success')
                            self.console_print("✅ VPN recovered - Resuming", 'green')
                            
                            self.global_connection_lost = False
                            self.connection_recovery_event.set()
                    
                    # Wait for recovery
                    self.connection_recovery_event.wait()
                
                # Log errors only on first attempt or connection errors
                error_str = str(e)
                if not self.global_connection_lost:
                    smtp_info = f"{current_smtp['host']}:{current_smtp['port']}" if current_smtp else "No SMTP"
                    
                    if "Connection" in error_str or "timed out" in error_str or "Errno" in error_str:
                        self.console_print(f"⚠️ Connection failed to {smtp_info}: {error_str[:100]}", 'yellow')
                    elif "Authentication" in error_str or "535" in error_str or "auth" in error_str.lower():
                        self.console_print(f"   ❌ AUTH FAILED: {smtp_info.split(':')[0]} - {error_str[:80]}", 'red')
                        self.log_message(f"✗ Auth failed: {smtp_info} - {error_str[:100]}", 'error')
                    else:
                        # Other SMTP errors (rate limits, blacklists, etc.)
                        smtp_error_code = error_str.split(',')[0] if ',' in error_str else error_str[:100]
                        self.console_print(f"❌ SMTP Error ({smtp_info}): {smtp_error_code}", 'red')
                
                # RETRY LOGIC: Continue to next attempt with different SMTP
                if attempt < max_retries - 1:
                    if attempt == 0:
                        # First retry - show we're retrying
                        self.console_print(f"   🔄 Retrying with different SMTP server...", 'yellow')
                    continue
                else:
                    # All retries exhausted - email failed
                    self.console_print(f"   ✗ FAILED after {max_retries} attempts: FROM {from_address} → TO {recipient_email}", 'red')
                    self.log_message(f"✗ Failed after {max_retries} attempts: {from_address} → {recipient_email} - {last_error}", 'error')
                    return False
        
        # Should not reach here, but return False if we do
        return False
    
    def generate_random_boundary(self):
        characters = string.digits
        return ''.join(random.choice(characters) for _ in range(36))
        
    def update_progress(self):
        """Throttled progress update to prevent GUI freezing"""
        current_time = time.time()
        
        # Only update GUI every 0.5 seconds to prevent freezing
        if current_time - self.last_progress_update < self.progress_update_interval:
            return
        
        self.last_progress_update = current_time
        
        try:
            # Essential updates only
            remaining_from = len(self.from_addresses)
            initial_count = self.progress_bar['maximum']
            
            self.progress_bar['value'] = self.total_emails_sent
            self.progress_label.config(text=f"Progress: {self.total_emails_sent} / {initial_count} | Remaining: {remaining_from}")
            self.console_info_label.config(text=f"Sent: {self.total_emails_sent}/{initial_count} | "
                                               f"Remaining: {remaining_from} | "
                                               f"Success: {len(self.successfully_sent_emails)} | "
                                               f"Failed Servers: {len(self.failed_servers)}")
            self.update_stats()
            
            # Flush queued messages
            self.flush_gui_queues()
        except:
            pass
    
    def on_closing(self):
        """Handle window closing - save all state and stop all processes"""
        print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🛑 Shutting down Email Sender Pro...{Style.RESET_ALL}")
        
        # Stop monitoring if running
        if self.is_monitoring:
            print(f"{Fore.CYAN}   Stopping inbox monitor...{Style.RESET_ALL}")
            self.is_monitoring = False
            # Give monitor thread time to stop
            import time
            time.sleep(0.5)
        
        # Stop sending if running
        if self.is_running:
            print(f"{Fore.CYAN}   Stopping email sending...{Style.RESET_ALL}")
            self.is_running = False
            # Signal all threads to stop
            self.connection_recovery_event.set()
            self.smtp_pause_event.set()
            time.sleep(0.5)
        
        # Save current sending progress
        print(f"{Fore.CYAN}   Saving sending progress...{Style.RESET_ALL}")
        try:
            # Save FROM addresses state
            with self.from_addresses_lock:
                remaining_from = list(self.from_addresses)
            
            if remaining_from:
                with open('from.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(remaining_from))
                print(f"{Fore.GREEN}   ✓ Saved {len(remaining_from)} remaining FROM addresses{Style.RESET_ALL}")
            
            # Save verified emails
            if hasattr(self, 'verified_froms') and self.verified_froms:
                with open('verified_from.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.verified_froms))
                print(f"{Fore.GREEN}   ✓ Saved {len(self.verified_froms)} verified emails{Style.RESET_ALL}")
            
            # Save unverified emails
            if hasattr(self, 'unverified_froms') and self.unverified_froms:
                with open('unverified_from.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.unverified_froms))
            
        except Exception as e:
            print(f"{Fore.RED}   ✗ Error saving progress: {e}{Style.RESET_ALL}")
        
        # Save configuration
        print(f"{Fore.CYAN}   Saving configuration...{Style.RESET_ALL}")
        try:
            self.config_manager.save_config(self)
            print(f"{Fore.GREEN}   ✓ Configuration saved{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}   ✗ Config save error: {e}{Style.RESET_ALL}")
        
        # Print summary
        print(f"\n{Fore.GREEN}📊 SESSION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Emails sent this session: {self.total_emails_sent}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Emails collected: {self.fake_from_counter}{Style.RESET_ALL}")
        with self.from_addresses_lock:
            print(f"{Fore.GREEN}   FROM addresses remaining: {len(self.from_addresses)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Verified emails: {len(self.verified_froms)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💾 All progress saved - Ready to resume!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")
        
        self.root.destroy()

    
    def setup_sending_tab(self):
        """Setup Sending tab - Compact all-in-one view"""
        # Main container with grid
        main_container = ttk.Frame(self.sending_tab)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.sending_tab.columnconfigure(0, weight=1)
        self.sending_tab.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # TOP - Controls (moved to top right for visibility)
        top_controls_frame = ttk.Frame(main_container)
        top_controls_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,5))
        
        # Control buttons on the right
        btn_frame = ttk.Frame(top_controls_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        self.sending_start_btn = ttk.Button(btn_frame, text="▶️ Start", command=self.start_bulk_sending, width=12)
        self.sending_start_btn.pack(side=tk.LEFT, padx=2)
        
        self.sending_pause_btn = ttk.Button(btn_frame, text="⏸️ Pause", command=self.pause_bulk_sending, width=10)
        self.sending_pause_btn.pack(side=tk.LEFT, padx=2)
        
        self.sending_resume_btn = ttk.Button(btn_frame, text="▶️ Resume", command=self.resume_bulk_sending, width=10)
        self.sending_resume_btn.pack(side=tk.LEFT, padx=2)
        
        self.sending_stop_btn = ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_bulk_sending, width=10)
        self.sending_stop_btn.pack(side=tk.LEFT, padx=2)
        
        # Stats on the left
        self.sending_stats_label = ttk.Label(top_controls_frame, text="Ready | Sent: 0 | Failed: 0", 
                                            font=('Arial', 10, 'bold'), foreground='#0000ff')
        self.sending_stats_label.pack(side=tk.LEFT, padx=5)
        
        # LEFT COLUMN - Configuration
        left_frame = ttk.Frame(main_container)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0,5))
        
        # Sender Selection
        sender_frame = ttk.LabelFrame(left_frame, text="📧 Sender Selection", padding="5")
        sender_frame.pack(fill=tk.X, pady=(0,5))
        
        self.sender_mode = tk.StringVar(value='verified')
        ttk.Radiobutton(sender_frame, text="✅ Verified Only", variable=self.sender_mode, value='verified', command=self.update_sender_counts).pack(anchor=tk.W)
        ttk.Radiobutton(sender_frame, text="❌ Unverified Only", variable=self.sender_mode, value='unverified', command=self.update_sender_counts).pack(anchor=tk.W)
        ttk.Radiobutton(sender_frame, text="🔄 Both (All)", variable=self.sender_mode, value='both', command=self.update_sender_counts).pack(anchor=tk.W)
        
        # Sender counts display
        self.sender_counts_label = ttk.Label(sender_frame, text="Verified: 0 | Unverified: 0 | Total: 0", 
                                            font=('Arial', 8, 'bold'), foreground='#0000ff')
        self.sender_counts_label.pack(pady=(5,0))
        
        # Update counts on load
        self.root.after(100, self.update_sender_counts)
        
        # Recipients List
        recip_frame = ttk.LabelFrame(left_frame, text="📋 Recipients (one per line)", padding="5")
        recip_frame.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        
        self.sending_recipients_text = scrolledtext.ScrolledText(recip_frame, wrap=tk.WORD, height=5, font=('Courier New', 9))
        self.sending_recipients_text.pack(fill=tk.BOTH, expand=True)
        
        # Subjects List
        subj_frame = ttk.LabelFrame(left_frame, text="📝 Subjects (random selection)", padding="5")
        subj_frame.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        
        self.sending_subjects_text = scrolledtext.ScrolledText(subj_frame, wrap=tk.WORD, height=3, font=('Courier New', 9))
        self.sending_subjects_text.pack(fill=tk.BOTH, expand=True)
        self.sending_subjects_text.insert(1.0, "Important Update\nSpecial Offer\nFollow Up")
        
        # Names List
        names_frame = ttk.LabelFrame(left_frame, text="👤 Sender Names (random selection)", padding="5")
        names_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sending_names_text = scrolledtext.ScrolledText(names_frame, wrap=tk.WORD, height=3, font=('Courier New', 9))
        self.sending_names_text.pack(fill=tk.BOTH, expand=True)
        self.sending_names_text.insert(1.0, "Support Team\nCustomer Service\nNotifications")
        
        # RIGHT COLUMN - Template & Console
        right_frame = ttk.Frame(main_container)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5,0))
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Email Template
        template_frame = ttk.LabelFrame(right_frame, text="📝 Email Template (HTML)", padding="5")
        template_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0,5))
        template_frame.rowconfigure(0, weight=1)
        template_frame.columnconfigure(0, weight=1)
        
        self.sending_template_text = scrolledtext.ScrolledText(template_frame, wrap=tk.WORD, font=('Courier New', 9))
        self.sending_template_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.sending_template_text.insert(1.0, """<html>
<body>
<h2>Hello!</h2>
<p>This is a test message from {NAME}.</p>
<p>Date: {DATE}</p>
<p>Random: {RAND:100-999}</p>
</body>
</html>""")
        
        # Template Help
        help_label = ttk.Label(template_frame, text="Tags: {RECIPIENT} {NAME} {DATE} {TIME} {RAND:min-max}", 
                              font=('Arial', 7), foreground='blue')
        help_label.grid(row=1, column=0, sticky=tk.W, pady=(2,0))
        
        # Console Log
        console_frame = ttk.LabelFrame(right_frame, text="📊 Sending Log", padding="5")
        console_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_frame.rowconfigure(0, weight=1)
        console_frame.columnconfigure(0, weight=1)
        
        self.sending_log_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, bg='#1a1a1a', fg='#00ff00', 
                                                          font=('Courier New', 8), state='disabled')
        self.sending_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def update_sender_counts(self):
        """Update sender counts display"""
        try:
            verified_count = len(self.verified_froms)
            unverified_count = len(self.unverified_froms)
            total_count = verified_count + unverified_count
            
            self.sender_counts_label.config(
                text=f"Verified: {verified_count} | Unverified: {unverified_count} | Total: {total_count}"
            )
        except Exception as e:
            pass
    
    def sending_log_print(self, message, msg_type='info'):
        """Print to sending log"""
        def append():
            self.sending_log_text.config(state='normal')
            
            timestamp = datetime.now().strftime('[%H:%M:%S]')
            
            if msg_type == 'success':
                color = '#00ff00'
            elif msg_type == 'error':
                color = '#ff0000'
            elif msg_type == 'warning':
                color = '#ffff00'
            else:
                color = '#00ffff'
            
            self.sending_log_text.insert(tk.END, f"{timestamp} ", 'timestamp')
            self.sending_log_text.insert(tk.END, f"{message}\n", msg_type)
            
            self.sending_log_text.tag_config('timestamp', foreground='#888888')
            self.sending_log_text.tag_config('success', foreground='#00ff00')
            self.sending_log_text.tag_config('error', foreground='#ff0000')
            self.sending_log_text.tag_config('warning', foreground='#ffff00')
            self.sending_log_text.tag_config('info', foreground='#00ffff')
            
            self.sending_log_text.see(tk.END)
            self.sending_log_text.config(state='disabled')
        
        self.root.after(0, append)
    
    def start_bulk_sending(self):
        """Start bulk sending"""
        # Get recipients
        recipients_content = self.sending_recipients_text.get(1.0, tk.END).strip()
        recipients = [line.strip() for line in recipients_content.split('\n') if line.strip() and '@' in line]
        
        # Get subjects
        subjects_content = self.sending_subjects_text.get(1.0, tk.END).strip()
        subjects = [line.strip() for line in subjects_content.split('\n') if line.strip()]
        
        # Get names
        names_content = self.sending_names_text.get(1.0, tk.END).strip()
        names = [line.strip() for line in names_content.split('\n') if line.strip()]
        
        # Get template
        template = self.sending_template_text.get(1.0, tk.END).strip()
        
        # Get sender mode
        sender_mode = self.sender_mode.get()
        
        # Start sending
        self.sending_manager.start_sending(
            sender_mode=sender_mode,
            recipients_list=recipients,
            template=template,
            subjects_list=subjects,
            names_list=names
        )
    
    def pause_bulk_sending(self):
        """Pause bulk sending"""
        self.sending_manager.pause_sending()
    
    def resume_bulk_sending(self):
        """Resume bulk sending"""
        self.sending_manager.resume_sending()
    
    def stop_bulk_sending(self):
        """Stop bulk sending"""
        self.sending_manager.stop_sending()

def main():
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    app = EmailSenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
