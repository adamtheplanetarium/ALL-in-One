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
        
        # Email verification state
        self.collected_from_emails = []
        self.verified_froms = []
        self.unverified_froms = []
        self.verification_in_progress = False
        
        # Initialize config manager
        self.config_manager = ConfigManager(self.config_file)
        
        # Load saved config
        self.config_manager.load_config(self)
        
        self.setup_ui()
        
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
        
        # Tab 6: Send Control
        self.control_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.control_tab, text="🚀 Send Control")
        
        # Tab 7: Logs
        self.logs_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.logs_tab, text="📊 Logs & Statistics")
        
        # Tab 8: Console View
        self.console_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.console_tab, text="💻 Console View")
        
        # Tab 9: Get From (Inbox Monitor)
        self.getfrom_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.getfrom_tab, text="📬 Get From")
        
        self.setup_config_tab()
        self.setup_smtp_tab()
        self.setup_recipients_tab()
        self.setup_from_tab()
        self.setup_template_tab()
        self.setup_control_tab()
        self.setup_logs_tab()
        self.setup_console_tab()
        self.setup_getfrom_tab()
        
        # Apply saved config after UI is created
        self.apply_pending_config()
        
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
        ttk.Button(button_frame, text="🗑️ Clear", command=lambda: self.from_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        # From count label
        self.from_count_label = ttk.Label(from_frame, text="From addresses loaded: 0", font=('Arial', 10, 'bold'))
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
        
        ttk.Button(button_frame, text="📁 Load from File", command=self.load_template_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save to File", command=self.save_template_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Clear", command=lambda: self.template_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
    def setup_control_tab(self):
        # Send control and progress
        control_frame = ttk.LabelFrame(self.control_tab, text="Sending Control Panel", padding="20")
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
        
    # File operations
    def load_smtp_file(self):
        filename = filedialog.askopenfilename(title="Load SMTP Servers", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.smtp_text.delete(1.0, tk.END)
                self.smtp_text.insert(1.0, content)
                self.log_message(f"Loaded SMTP servers from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    def save_smtp_file(self):
        filename = filedialog.asksaveasfilename(title="Save SMTP Servers", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.smtp_text.get(1.0, tk.END))
                self.log_message(f"Saved SMTP servers to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    def load_recipients_file(self):
        filename = filedialog.askopenfilename(title="Load Recipients", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.recipients_text.delete(1.0, tk.END)
                self.recipients_text.insert(1.0, content)
                self.log_message(f"Loaded recipients from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    def save_recipients_file(self):
        filename = filedialog.asksaveasfilename(title="Save Recipients", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.recipients_text.get(1.0, tk.END))
                self.log_message(f"Saved recipients to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    def load_from_file(self):
        filename = filedialog.askopenfilename(title="Load From Addresses", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.from_text.delete(1.0, tk.END)
                self.from_text.insert(1.0, content)
                self.log_message(f"Loaded from addresses from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    def save_from_file(self):
        filename = filedialog.asksaveasfilename(title="Save From Addresses", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.from_text.get(1.0, tk.END))
                self.log_message(f"Saved from addresses to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    def load_template_file(self):
        filename = filedialog.askopenfilename(title="Load Email Template", 
                                             filetypes=[("HTML files", "*.html *.htm"), ("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.template_text.delete(1.0, tk.END)
                self.template_text.insert(1.0, content)
                self.log_message(f"Loaded template from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    def save_template_file(self):
        filename = filedialog.asksaveasfilename(title="Save Email Template", 
                                               defaultextension=".html",
                                               filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.template_text.get(1.0, tk.END))
                self.log_message(f"Saved template to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
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
                "Click 'Resume Sending' button in Send Control tab to continue."
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
        self.from_addresses = [line.strip() for line in content.split('\n') if line.strip() and '@' in line]
        
        self.from_count_label.config(text=f"From addresses loaded: {len(self.from_addresses)}")
        self.log_message(f"Parsed {len(self.from_addresses)} from addresses", 'success')
        self.update_stats()
                
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
        # Get From - Inbox Monitor Tab
        main_frame = ttk.Frame(self.getfrom_tab)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        self.getfrom_tab.columnconfigure(0, weight=1)
        self.getfrom_tab.rowconfigure(0, weight=1)
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="📁 Thunderbird Configuration", padding="15")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        main_frame.columnconfigure(0, weight=1)
        
        ttk.Label(config_frame, text="Thunderbird ImapMail Path:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(config_frame)
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(0, weight=1)
        
        self.thunderbird_path_var = tk.StringVar(value=self.thunderbird_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.thunderbird_path_var, width=70, font=('Courier New', 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(path_frame, text="📂 Browse", command=self.browse_thunderbird_path).pack(side=tk.LEFT)
        
        # Counter Section (Big Display)
        counter_frame = ttk.LabelFrame(main_frame, text="📊 Fake From Counter", padding="20")
        counter_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.fake_from_label = ttk.Label(counter_frame, text="0", font=('Arial', 72, 'bold'), 
                                         foreground='#00aa00')
        self.fake_from_label.pack(pady=20)
        
        ttk.Label(counter_frame, text="Total Emails Collected", font=('Arial', 14)).pack()
        
        # Control Buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, pady=15)
        
        self.start_monitor_btn = ttk.Button(control_frame, text="▶️ Start Monitoring", 
                                           command=self.start_monitoring, style='Green.TButton')
        self.start_monitor_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_monitor_btn = ttk.Button(control_frame, text="⏹️ Stop Monitoring", 
                                          command=self.stop_monitoring, state=tk.DISABLED, 
                                          style='Red.TButton')
        self.stop_monitor_btn.pack(side=tk.LEFT, padx=10)
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="📡 Monitor Status", padding="15")
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.monitor_status_label = ttk.Label(status_frame, text="⚫ Monitoring: STOPPED", 
                                             font=('Arial', 11, 'bold'), foreground='red')
        self.monitor_status_label.pack(anchor=tk.W, pady=5)
        
        self.monitor_check_label = ttk.Label(status_frame, text="Last Check: Never", font=('Arial', 10))
        self.monitor_check_label.pack(anchor=tk.W, pady=3)
        
        self.monitor_accounts_label = ttk.Label(status_frame, text="Active Accounts: 0", font=('Arial', 10))
        self.monitor_accounts_label.pack(anchor=tk.W, pady=3)
        
        # Activity Log
        log_frame = ttk.LabelFrame(main_frame, text="📝 Monitor Activity Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(4, weight=1)
        
        self.monitor_log = scrolledtext.ScrolledText(log_frame, height=12, width=100, 
                                                     wrap=tk.WORD, bg='#1e1e1e', fg='#00ff00', 
                                                     font=('Courier New', 9))
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored log output
        self.monitor_log.tag_config('info', foreground='#00ffff')
        self.monitor_log.tag_config('success', foreground='#00ff00')
        self.monitor_log.tag_config('warning', foreground='#ffff00')
        self.monitor_log.tag_config('error', foreground='#ff0000')
        
        # Verification Section
        verify_frame = ttk.LabelFrame(main_frame, text="📋 Email Verification", padding="15")
        verify_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(5, weight=1)
        
        # Collected emails display
        collected_label = ttk.Label(verify_frame, text="Collected From Addresses:", font=('Arial', 10, 'bold'))
        collected_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.collected_from_text = scrolledtext.ScrolledText(verify_frame, height=8, width=100, 
                                                             wrap=tk.WORD, bg='#2b2b2b', fg='#00ff00', 
                                                             font=('Courier New', 9))
        self.collected_from_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        verify_frame.rowconfigure(1, weight=1)
        verify_frame.columnconfigure(0, weight=1)
        
        # Verification buttons
        verify_btn_frame = ttk.Frame(verify_frame)
        verify_btn_frame.grid(row=2, column=0, pady=10)
        
        ttk.Button(verify_btn_frame, text="🔄 Recheck All", command=lambda: self.start_verification('all')).pack(side=tk.LEFT, padx=5)
        ttk.Button(verify_btn_frame, text="❌ Recheck Unverified", command=lambda: self.start_verification('unverified')).pack(side=tk.LEFT, padx=5)
        ttk.Button(verify_btn_frame, text="✅ Recheck Verified", command=lambda: self.start_verification('verified')).pack(side=tk.LEFT, padx=5)
        ttk.Button(verify_btn_frame, text="🔄 Refresh List", command=self.refresh_collected_froms).pack(side=tk.LEFT, padx=5)
        
        # Verification stats
        verify_stats_frame = ttk.Frame(verify_frame)
        verify_stats_frame.grid(row=3, column=0, pady=10)
        
        self.verify_stats_label = ttk.Label(verify_stats_frame, 
                                           text="Collected: 0 | Verified: 0 | Unverified: 0",
                                           font=('Arial', 10, 'bold'), foreground='#0000ff')
        self.verify_stats_label.pack()
        
        # Save buttons
        save_btn_frame = ttk.Frame(verify_frame)
        save_btn_frame.grid(row=4, column=0, pady=5)
        
        ttk.Button(save_btn_frame, text="💾 Save Verified Froms", command=self.save_verified_froms).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_btn_frame, text="💾 Save Unverified Froms", command=self.save_unverified_froms).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_btn_frame, text="📁 Load Verified", command=self.load_verified_froms).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_btn_frame, text="📁 Load Unverified", command=self.load_unverified_froms).pack(side=tk.LEFT, padx=5)
        
        # Info footer
        info_label = ttk.Label(main_frame, 
                              text="💡 Tip: Recheck sends test emails and waits for replies to verify from addresses actually work.",
                              font=('Arial', 9, 'italic'), foreground='#666666')
        info_label.grid(row=6, column=0, pady=10)
        
    def console_print(self, message, color='green'):
        """Print to console view with color"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.console_text.insert(tk.END, f"[{timestamp}] ", 'cyan')
        self.console_text.insert(tk.END, f"{message}\n", color)
        if self.autoscroll_enabled:
            self.console_text.see(tk.END)
        
    # Logging
    def log_message(self, message, tag='info'):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        
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
    
    def show_smtp_pause_warning(self):
        """Show warning when all SMTP servers fail and enable resume button"""
        self.status_label.config(text="⛔ PAUSED - All SMTP servers failed!", foreground='red')
        
        # Enable resume button if it exists
        if hasattr(self, 'resume_smtp_btn'):
            self.resume_smtp_btn.config(state=tk.NORMAL)
        
        # Show warning message
        messagebox.showwarning(
            "All SMTP Servers Failed",
            "⛔ All SMTP servers have failed!\n\n"
            "The sending process is PAUSED.\n\n"
            "Please:\n"
            "1. Go to SMTP Servers tab\n"
            "2. Update/add working SMTP servers\n"
            "3. Click 'Parse SMTP Servers'\n"
            "4. Click 'Resume Sending' button\n\n"
            "The script will NOT continue until you resume."
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
            
    def monitor_log_print(self, message, tag='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.monitor_log.see(tk.END)
        
    def start_monitoring(self):
        if self.is_monitoring:
            messagebox.showwarning("Already Running", "Monitoring is already active!")
            return
            
        path = self.thunderbird_path_var.get()
        if not os.path.exists(path):
            messagebox.showerror("Invalid Path", f"Path does not exist:\n{path}")
            print(f"{Fore.RED}[ERROR] Invalid path: {path}{Style.RESET_ALL}")
            return
            
        self.is_monitoring = True
        self.start_monitor_btn.config(state=tk.DISABLED)
        self.stop_monitor_btn.config(state=tk.NORMAL)
        self.monitor_status_label.config(text="🟢 Monitoring: ACTIVE", foreground='green')
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🚀 INBOX MONITOR STARTING...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[PATH] {path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        self.monitor_log_print("=" * 60, 'info')
        self.monitor_log_print("🚀 Starting Inbox Monitor...", 'success')
        self.monitor_log_print(f"📂 Path: {path}", 'info')
        
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
        check_interval = 60  # Check every 60 seconds
        check_count = 0
        
        try:
            # Initial scan
            print(f"{Fore.CYAN}🔍 Performing initial scan...{Style.RESET_ALL}")
            self.monitor_log_print("🔍 Performing initial scan...", 'info')
            accounts = self.find_all_inboxes()
            
            if not accounts:
                print(f"{Fore.RED}❌ No INBOX files found!{Style.RESET_ALL}")
                self.monitor_log_print("❌ No INBOX files found!", 'error')
                self.root.after(0, self.stop_monitoring)
                return
                
            print(f"{Fore.GREEN}✅ Found {len(accounts)} accounts{Style.RESET_ALL}")
            self.root.after(0, lambda: self.monitor_accounts_label.config(text=f"Active Accounts: {len(accounts)}"))
            self.monitor_log_print(f"✅ Found {len(accounts)} accounts", 'success')
            
            # Initial email scan
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
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
            
            self.monitor_log_print(f"📊 Total: {total_initial} emails tracked", 'success')
            self.monitor_log_print("⏰ Checking for new emails every 60 seconds", 'info')
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
                
                # Check for new emails
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
                            
                            # Save to from.txt and update counter
                            self.save_from_address(email_address)
                            
                            # Mark as seen
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
                
                if from_match:
                    from_header = from_match.group(1).strip()
                    subject = subject_match.group(1).strip() if subject_match else "(No Subject)"
                    
                    # Create hash for duplicate detection
                    email_hash = hashlib.md5(msg.encode('utf-8', errors='ignore')).hexdigest()
                    
                    emails.append({
                        'from': from_header,
                        'subject': subject,
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
        """Save email address to from.txt and update counter"""
        try:
            # Append to from.txt
            with open('from.txt', 'a', encoding='utf-8') as f:
                f.write(email_address + '\n')
                f.flush()
                os.fsync(f.fileno())
            
            # Update counter
            with self.monitor_lock:
                self.fake_from_counter += 1
                counter_value = self.fake_from_counter
            
            # Update GUI
            self.root.after(0, lambda: self.fake_from_label.config(text=str(counter_value)))
            self.root.after(0, self.reload_from_addresses)
            
            print(f"{Fore.GREEN}💾 Saved to from.txt | Counter: {counter_value}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
            
            self.monitor_log_print(f"💾 Saved to from.txt | Counter: {counter_value}", 'success')
            
            # Save config after each new email
            self.save_config()
            
        except Exception as e:
            print(f"{Fore.RED}❌ ERROR saving to file: {e}{Style.RESET_ALL}")
            self.monitor_log_print(f"Error saving: {e}", 'error')
            
    def reload_from_addresses(self):
        """Reload from addresses from file"""
        try:
            if os.path.exists('from.txt'):
                with open('from.txt', 'r', encoding='utf-8') as f:
                    addresses = [line.strip() for line in f if line.strip()]
                    # Update the from addresses list
                    if hasattr(self, 'from_text'):
                        current_content = self.from_text.get(1.0, tk.END).strip()
                        if '\n'.join(addresses) != current_content:
                            self.from_text.delete(1.0, tk.END)
                            self.from_text.insert(1.0, '\n'.join(addresses))
                    # Update collected list
                    self.collected_from_emails = addresses
                    if hasattr(self, 'collected_from_text'):
                        self.refresh_collected_froms()
        except Exception as e:
            self.log_message(f"Error reloading from addresses: {e}", 'error')
    
    def refresh_collected_froms(self):
        """Refresh the collected from emails display"""
        try:
            if hasattr(self, 'collected_from_text'):
                self.collected_from_text.delete(1.0, tk.END)
                for email in self.collected_from_emails:
                    status = ""
                    if email in self.verified_froms:
                        status = " ✅ VERIFIED"
                    elif email in self.unverified_froms:
                        status = " ❌ UNVERIFIED"
                    self.collected_from_text.insert(tk.END, f"{email}{status}\n")
                
                # Update stats
                total = len(self.collected_from_emails)
                verified = len(self.verified_froms)
                unverified = len(self.unverified_froms)
                self.verify_stats_label.config(text=f"Collected: {total} | Verified: {verified} | Unverified: {unverified}")
        except Exception as e:
            print(f"{Fore.RED}Error refreshing collected froms: {e}{Style.RESET_ALL}")
    
    def start_verification(self, mode='all'):
        """Start email verification - placeholder"""
        messagebox.showinfo("Coming Soon", f"Verification feature ({mode}) will be implemented in next update!")
    
    def save_verified_froms(self):
        """Save verified froms"""
        filename = filedialog.asksaveasfilename(title="Save Verified", defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(self.verified_froms))
            messagebox.showinfo("Saved", f"Saved {len(self.verified_froms)} verified emails")
    
    def save_unverified_froms(self):
        """Save unverified froms"""
        filename = filedialog.asksaveasfilename(title="Save Unverified", defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(self.unverified_froms))
            messagebox.showinfo("Saved", f"Saved {len(self.unverified_froms)} unverified emails")
    
    def load_verified_froms(self):
        """Load verified froms"""
        filename = filedialog.askopenfilename(title="Load Verified", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'r') as f:
                self.verified_froms = [line.strip() for line in f if line.strip()]
            self.refresh_collected_froms()
            messagebox.showinfo("Loaded", f"Loaded {len(self.verified_froms)} verified emails")
    
    def load_unverified_froms(self):
        """Load unverified froms"""
        filename = filedialog.askopenfilename(title="Load Unverified", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'r') as f:
                self.unverified_froms = [line.strip() for line in f if line.strip()]
            self.refresh_collected_froms()
            messagebox.showinfo("Loaded", f"Loaded {len(self.unverified_froms)} unverified emails")
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            config = {
                'thunderbird_path': self.thunderbird_path_var.get() if hasattr(self, 'thunderbird_path_var') else self.thunderbird_path,
                'fake_from_counter': self.fake_from_counter,
                'domain_from': self.domain_from_var.get() if hasattr(self, 'domain_from_var') else '',
                'domain_auth': self.domain_auth_var.get() if hasattr(self, 'domain_auth_var') else '',
                'sender_name': self.sender_name_var.get() if hasattr(self, 'sender_name_var') else '',
                'email_subject': self.subject_var.get() if hasattr(self, 'subject_var') else '',
                'threads': self.threads_var.get() if hasattr(self, 'threads_var') else 5,
                'delay_between': self.delay_var.get() if hasattr(self, 'delay_var') else 1,
                'verified_froms': self.verified_froms,
                'unverified_froms': self.unverified_froms,
                'collected_from_emails': self.collected_from_emails,
                'last_saved': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            print(f"{Fore.GREEN}💾 Configuration saved{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving config: {e}{Style.RESET_ALL}")
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Load values
                self.thunderbird_path = config.get('thunderbird_path', self.thunderbird_path)
                self.fake_from_counter = config.get('fake_from_counter', 0)
                self.verified_froms = config.get('verified_froms', [])
                self.unverified_froms = config.get('unverified_froms', [])
                self.collected_from_emails = config.get('collected_from_emails', [])
                
                print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[CONFIG] Configuration loaded successfully{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Thunderbird Path: {self.thunderbird_path}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Fake From Counter: {self.fake_from_counter}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Verified Froms: {len(self.verified_froms)}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Unverified Froms: {len(self.unverified_froms)}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   Last Saved: {config.get('last_saved', 'Unknown')}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
                
                # These will be set after UI is created
                self._pending_config = config
                
        except Exception as e:
            print(f"{Fore.YELLOW}[WARNING] No previous config found (first run){Style.RESET_ALL}")
    
    def apply_pending_config(self):
        """Apply config values to UI elements after they're created"""
        if hasattr(self, '_pending_config'):
            config = self._pending_config
            
            # Apply to UI elements
            if hasattr(self, 'domain_from_var'):
                self.domain_from_var.set(config.get('domain_from', 'charter.net'))
            if hasattr(self, 'domain_auth_var'):
                self.domain_auth_var.set(config.get('domain_auth', 'altona.fr'))
            if hasattr(self, 'sender_name_var'):
                self.sender_name_var.set(config.get('sender_name', ''))
            if hasattr(self, 'subject_var'):
                self.subject_var.set(config.get('email_subject', ''))
            if hasattr(self, 'threads_var'):
                self.threads_var.set(config.get('threads', 5))
            if hasattr(self, 'delay_var'):
                self.delay_var.set(config.get('delay_between', 1))
            if hasattr(self, 'fake_from_label'):
                self.fake_from_label.config(text=str(self.fake_from_counter))
            
            delattr(self, '_pending_config')
            print(f"{Fore.GREEN}✅ Configuration applied to UI{Style.RESET_ALL}")
        
    def send_emails_thread(self):
        """
        NEW ROUTING MODE:
        Iterate through all FROM addresses, rotating through the recipient pool
        """
        max_connections = self.threads_var.get()
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_connections) as executor:
                futures = []
                
                # Iterate through FROM addresses (main loop)
                for from_index, from_address in enumerate(self.from_addresses):
                    if not self.is_running:
                        break
                    
                    # Get recipient by rotating through the pool
                    recipient_index = from_index % len(self.recipient_email_list)
                    recipient = self.recipient_email_list[recipient_index]
                    
                    # Submit email sending task with specific from/to pair
                    future = executor.submit(self.send_email_routing, from_address, recipient, from_index)
                    futures.append(future)
                    
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
        NEW ROUTING MODE:
        Send email using specific from_address to specific recipient
        from_index: position in the from_addresses list (for tracking)
        """
        if not self.is_running:
            return
            
        # Initialize variables to prevent NameError in exception handler
        server = None
        current_smtp = None
        new_value = "Unknown"
        fromane = from_address  # Use the actual from address passed to this function
        
        try:
            # Select SMTP server from the list (skip servers with 2+ failures)
            # *** PRESERVED ORIGINAL SMTP LOCK LOGIC - DO NOT MODIFY ***
            max_failures_per_server = 2
            attempts = 0
            with self.smtp_server_lock:
                while attempts < len(self.smtp_servers):
                    if self.smtp_server_index >= len(self.smtp_servers):
                        self.smtp_server_index = 0
                    current_smtp = self.smtp_servers[self.smtp_server_index]
                    self.smtp_server_index += 1
                    
                    # Check if this server has failed 2 or more times - skip it
                    server_key = f"{current_smtp['host']}:{current_smtp['port']}"
                    current_failures = self.failed_servers.get(server_key, 0)
                    if current_failures < max_failures_per_server:
                        break
                    else:
                        self.log_message(f"Skipping {server_key} - already failed {current_failures} times", 'warning')
                    attempts += 1
                
                if attempts >= len(self.smtp_servers):
                    # All SMTP servers failed - pause and wait for user to update
                    self.smtp_paused = True
                    self.smtp_pause_event.clear()
                    self.root.after(0, self.show_smtp_pause_warning)
                    print(f"\n{Fore.RED}{'='*70}{Style.RESET_ALL}")
                    print(f"{Fore.RED}⛔ ALL SMTP SERVERS FAILED!{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}⏸️  Pausing email sending...{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}📝 Please update SMTP servers and click Resume{Style.RESET_ALL}")
                    print(f"{Fore.RED}{'='*70}{Style.RESET_ALL}\n")
                    
                    self.log_message("⛔ ALL SMTP SERVERS FAILED - Pausing operations", 'error')
                    self.console_print("⛔ ALL SMTP SERVERS FAILED - Waiting for SMTP update...", 'red')
                    
                    # Wait here until user resumes
                    self.smtp_pause_event.wait()
                    
                    # After resume, retry getting SMTP server
                    if not self.is_running:
                        return
                    
                    print(f"{Fore.GREEN}▶️  Resuming email sending...{Style.RESET_ALL}")
                    self.log_message("▶️ Resuming operations after SMTP update", 'success')
                    self.console_print("▶️ Resuming - retrying with updated SMTP servers", 'green')
                    
                    # Retry getting SMTP server after resume
                    with self.smtp_server_lock:
                        self.smtp_server_index = 0
                        if self.smtp_server_index >= len(self.smtp_servers):
                            raise Exception("No SMTP servers available")
                        current_smtp = self.smtp_servers[self.smtp_server_index]
                        self.smtp_server_index += 1
            # *** END OF PRESERVED SMTP LOCK LOGIC ***
            
            self.console_print(f"→ Sending #{from_index+1}/{len(self.from_addresses)} | From: {fromane} | To: {recipient_email}", 'white')
            self.console_print(f"  Using SMTP: {current_smtp['host']}:{current_smtp['port']} ({current_smtp['username']})", 'cyan')
            
            server = smtplib.SMTP(current_smtp['host'], current_smtp['port'], timeout=30)
            
            if self.debug_mode_var.get():
                server.set_debuglevel(1)
            
            # Enable STARTTLS for secure connection
            try:
                server.starttls()
            except Exception as tls_error:
                self.log_message(f"STARTTLS failed for {current_smtp['host']}: {tls_error}", 'warning')
            
            # Login
            try:
                server.login(current_smtp['username'], current_smtp['password'])
                self.console_print(f"  ✓ Authentication successful", 'green')
            except smtplib.SMTPAuthenticationError as auth_error:
                self.log_message(f"Auth failed for {current_smtp['username']}: {auth_error}", 'error')
                self.console_print(f"  ✗ Authentication FAILED: {auth_error}", 'red')
                raise auth_error
            
            # Generate random numbers
            random_number = random.randint(100000, 999999)
            random_number_str = random.randint(10000, 99999)
            
            # Process template
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
                    self.log_message(f"URL shortening failed: {e}", 'warning')
                    text_filek = text_filek.replace('LINKREDIRECT', self.link_redirect_var.get())
                    text_filek = text_filek.replace('IMGREDIRECT', self.link_redirect_var.get())
            else:
                text_filek = text_filek.replace('LINKREDIRECT', self.link_redirect_var.get())
                text_filek = text_filek.replace('IMGREDIRECT', self.link_redirect_var.get())
                
            text_filek = text_filek.replace('RANDOM', str(random_number))
            
            self.console_print(f"  Template processed (RANDOM: {random_number})", 'white')
            
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
            
            self.console_print(f"  Sending message...", 'yellow')
            server.sendmail(current_smtp['username'], [recipient_email], msg.as_string())
            
            self.console_print(f"  ✓✓✓ EMAIL SENT SUCCESSFULLY ✓✓✓", 'green')
            self.console_print(f"      Subject: {Newzepy}", 'white')
            
            server.quit()
            
            # Update counters
            with self.total_emails_lock:
                self.total_emails_sent += 1
            
            # Sleep if configured
            sleep_time = self.sleep_time_var.get()
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Log success
            if not self.test_mode_var.get():
                self.successfully_sent_emails.append(from_address)  # Track used from addresses
                
            self.log_message(f"✓ SENT #{self.total_emails_sent} | From: {fromane} → To: {recipient_email} via {current_smtp['host']}", 'success')
            self.console_print(f"", 'white')  # Blank line for readability
            
            # Update progress
            self.root.after(0, self.update_progress)
            
        except Exception as e:
            # Close server on error
            try:
                if server:
                    server.quit()
            except:
                pass
            
            # Track server failures (PRESERVED ORIGINAL LOCK LOGIC)
            if current_smtp:
                server_key = f"{current_smtp['host']}:{current_smtp['port']}"
                with self.failed_servers_lock:
                    self.failed_servers[server_key] = self.failed_servers.get(server_key, 0) + 1
                    if self.failed_servers[server_key] >= 2:
                        self.log_message(f"⚠ SMTP server {server_key} DISABLED after {self.failed_servers[server_key]} failures", 'warning')
            
            smtp_info = f"{current_smtp['host']}:{current_smtp['port']}" if current_smtp else "Unknown SMTP"
            self.log_message(f"✗ FAILED #{from_index+1} | From: {fromane} → To: {recipient_email} via {smtp_info}: {str(e)[:100]}", 'error')
            self.console_print(f"✗✗✗ SEND FAILED ✗✗✗", 'red')
            self.console_print(f"    From: {fromane}", 'red')
            self.console_print(f"    To: {recipient_email}", 'red')
            self.console_print(f"    Error: {str(e)[:150]}", 'red')
            self.console_print(f"", 'white')
            self.smtp_error_occurred = True
            
    def generate_random_boundary(self):
        characters = string.digits
        return ''.join(random.choice(characters) for _ in range(36))
        
    def update_progress(self):
        self.progress_bar['value'] = self.total_emails_sent
        self.progress_label.config(text=f"Progress: {self.total_emails_sent} / {len(self.from_addresses)}")
        self.console_info_label.config(text=f"Sent: {self.total_emails_sent}/{len(self.from_addresses)} | "
                                           f"Success: {len(self.successfully_sent_emails)} | "
                                           f"Failed Servers: {len(self.failed_servers)}")
        self.update_stats()
        self.console_print(f"Total emails sent: {self.total_emails_sent}/{len(self.from_addresses)}", 'white')
        self.console_print(f"Successfully sent: {len(self.successfully_sent_emails)}", 'green')
        self.console_print(f"Failed: {len(self.from_addresses) - len(self.successfully_sent_emails)}", 'red')
        
        # Show server statistics
        if self.failed_servers:
            self.log_message("\nSMTP SERVER FAILURE STATISTICS:", 'warning')
            self.console_print("\nSMTP SERVER FAILURE STATISTICS:", 'yellow')
            # Create a copy to avoid RuntimeError during iteration
            with self.failed_servers_lock:
                failed_servers_copy = dict(self.failed_servers)
            for server_key, failures in failed_servers_copy.items():
                status = "DISABLED" if failures >= 2 else "ACTIVE"
                self.log_message(f"  {server_key}: {failures} failures - {status}", 'warning')
                self.console_print(f"  {server_key}: {failures} failures - {status}", 'yellow')
        
        self.console_print("="*80, 'cyan')
        
        self.update_stats()
        
        # In routing mode, we track used FROM addresses, not recipients
        # Recipients stay the same - they're just a pool for routing
        if not self.test_mode_var.get() and self.successfully_sent_emails:
            # Remove successfully used from addresses from the list
            remaining = [addr for addr in self.from_addresses if addr not in self.successfully_sent_emails]
            self.from_text.delete(1.0, tk.END)
            self.from_text.insert(1.0, '\n'.join(remaining))
            self.parse_from_addresses()
            self.log_message(f"Removed {len(self.successfully_sent_emails)} used FROM addresses from list", 'info')
            self.console_print(f"Removed {len(self.successfully_sent_emails)} used FROM addresses from list", 'cyan')
            remaining = [email for email in self.recipient_email_list if email not in self.successfully_sent_emails]
            self.recipients_text.delete(1.0, tk.END)
            self.recipients_text.insert(1.0, '\n'.join(remaining))
            self.parse_recipients()
            self.log_message(f"Removed {len(self.successfully_sent_emails)} sent emails from list", 'info')
    
    def on_closing(self):
        """Handle window closing - save config and stop monitoring"""
        print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🛑 Shutting down Email Sender Pro...{Style.RESET_ALL}")
        
        # Stop monitoring if running
        if self.is_monitoring:
            print(f"{Fore.CYAN}   Stopping inbox monitor...{Style.RESET_ALL}")
            self.is_monitoring = False
        
        # Stop sending if running
        if self.is_running:
            print(f"{Fore.CYAN}   Stopping email sending...{Style.RESET_ALL}")
            self.is_running = False
        
        # Save configuration
        print(f"{Fore.CYAN}   Saving configuration...{Style.RESET_ALL}")
        self.save_config()
        
        print(f"{Fore.GREEN}✅ Configuration saved successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📊 Total emails collected: {self.fake_from_counter}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💾 All settings saved to: {self.config_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")
        
        self.root.destroy()

def main():
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    app = EmailSenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
