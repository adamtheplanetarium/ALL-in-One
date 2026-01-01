import smtplib
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
from datetime import datetime
import os
import socks
import socket
import time
import gdshortener
from colorama import Fore, Style, init
import pyfiglet
import concurrent.futures
import threading
import uuid
import configparser
import dkim

config = configparser.ConfigParser()
config.read('config.ini')

init(autoreset=True)

def clr():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

clr()

name = "BASSEMTOZ"
font = "banner"

ascii_art = pyfiglet.figlet_format(name, font=font)

print(ascii_art)
print(Fore.RED + Style.BRIGHT + f"Telegram: @voxebk")

current_datetime = datetime.now()
formatted_date = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
formatted_date_3 = current_datetime.strftime("%A, %B %d, %Y")

# Read SMTP servers from smtp.txt file
smtp_servers = []
with open('smtp.txt', 'r') as file:
    lines = file.readlines()[1:]  # Skip header line
    for line in lines:
        if line.strip():
            parts = line.strip().split(',')
            if len(parts) >= 4:
                smtp_servers.append({
                    'host': parts[0].strip(),
                    'port': int(parts[1].strip()),
                    'username': parts[2].strip(),
                    'password': parts[3].strip()
                })

# Get other settings from config.ini
domainx = config['Settings']['domainfrom']
domainauth = config['Settings']['DOMAIN_AUTHENTICATION']
sleeptime = config['Settings']['SLEEPTIME']

print(f"Loaded {len(smtp_servers)} SMTP servers from smtp.txt")
print(f"SMTP servers will be disabled after 2 failed attempts")
with open(config['Settings']['emailspath'], 'r') as file:
    recipient_email_list = [line.strip() for line in file]

email_list_copy = recipient_email_list.copy()

successfully_sent_emails = []

email_count = 0
max_connections = int(config['Settings']['threads'])
total_emails_sent = 0
total_emails_lock = threading.Lock()
current_index = 0
current_indexs = 0
current_indexs_lock = threading.Lock()
# Index for SMTP server rotation
smtp_server_index = 0
smtp_server_lock = threading.Lock()

# Track failed SMTP servers
failed_servers = {}
failed_servers_lock = threading.Lock()

smtp_error_occurred = False

def generate_random_boundary():
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(36))

def send_email(recipient_email):
    global total_emails_sent
    global current_index
    global current_indexs
    global smtp_server_index
    
    # Initialize variables to prevent NameError in exception handler
    server = None
    current_smtp = None
    new_value = "Unknown"
    fromane = "unknown@domain.com"
    
    try:
        def generate_random_string(length):
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for _ in range(length))

        # Select SMTP server from the list (skip servers with 2+ failures)
        max_failures_per_server = 2
        attempts = 0
        with smtp_server_lock:
            while attempts < len(smtp_servers):
                if smtp_server_index >= len(smtp_servers):
                    smtp_server_index = 0
                current_smtp = smtp_servers[smtp_server_index]
                smtp_server_index += 1
                
                # Check if this server has failed 2 or more times - skip it
                server_key = f"{current_smtp['host']}:{current_smtp['port']}"
                current_failures = failed_servers.get(server_key, 0)
                if current_failures < max_failures_per_server:
                    break
                else:
                    print(f"Skipping {server_key} - already failed {current_failures} times")
                attempts += 1
            
            if attempts >= len(smtp_servers):
                raise Exception("All SMTP servers have been disabled due to failures")
        
        server = smtplib.SMTP(current_smtp['host'], current_smtp['port'], 'localhost')
        
        debug = config['Settings']['DEBUG']
        if debug == "1":
            server.set_debuglevel(1)
        
        # Enable STARTTLS for secure connection (required by most modern SMTP servers)
        try:
            server.starttls()
        except Exception as tls_error:
            print(f"STARTTLS failed for {current_smtp['host']}: {tls_error}")
            # Continue without STARTTLS - some servers don't support it
        
        # Use SMTP credentials from smtp.txt with enhanced error handling
        try:
            server.login(current_smtp['username'], current_smtp['password'])
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"Authentication failed for {current_smtp['username']} on {current_smtp['host']}: {auth_error}")
            raise auth_error
        except smtplib.SMTPException as smtp_error:
            print(f"SMTP error for {current_smtp['host']}: {smtp_error}")
            raise smtp_error

        random_number = random.randint(100000, 999999)
        lastxdd = config['Settings']['LETTERPATH']
        s = gdshortener.ISGDShortener()
        url, _ = s.shorten(url=f'https://flexidesk.cloud/auth/direct_invoice?{random_number}={random_number}')
        img_url, _ = s.shorten(url=f'https://flexidesk.cloud/auth/direct_invoice')
        with open(lastxdd, 'rb') as file:
            text_filek = file.read().decode('utf-8')
        text_filek = text_filek.replace('LINKREDIRECT',url)
        text_filek = text_filek.replace('IMGREDIRECT', img_url)
        text_filek = text_filek.replace('RANDOM', str(random_number))
        # Use current SMTP username as sender
        fromxd = current_smtp['username']
        sender_email = fromxd
        sendernox = config['Settings']['SENDERNAME']
        random_number_str = random.randint(10000, 99999)
        # Extract domain from SMTP username for capitalization
        smtp_domain = current_smtp['username'].split('@')[-1] if '@' in current_smtp['username'] else domainx
        capitalized_domain = smtp_domain.split('.')[0].capitalize()
        
        if 'CapitalS' in sendernox:
            new_value = sendernox.replace('CapitalS', capitalized_domain)
            new_value = new_value.replace('randomchar', str(random_number_str))
        elif 'randomchar' in sendernox:
            new_value = sendernox.replace('randomchar', str(random_number_str))
        else:
            new_value = sendernox

        msg = MIMEMultipart("alternative")
        msg.set_boundary(generate_random_boundary())
        frompath = config['Settings']['FROMPATH']

        with open(frompath, 'r') as file:
            email_addresses = file.readlines()

        with current_indexs_lock:
            if current_index >= len(email_addresses):
                current_index = 0
            fromane = email_addresses[current_index].strip()
            current_index += 1

        msg['From'] = f'{new_value} <{fromane}>'
        msg['Date'] = email.utils.formatdate(localtime=True)
        msg['To'] = recipient_email
        custom_message_id = f"<{str(uuid.uuid4())}@mta-2d57c4b7.i>"
        msg["Message-ID"] = custom_message_id

        if config['Settings']['important'] == '1':
            msg['Importance'] = "high"
            msg['X-Priority'] = "1"

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        subject = config['Settings']['subject']
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
        message_html_cleaned = ''.join(char if 32 <= ord(char) < 128 else ' '
                                       for char in text_filek)
        letterx = MIMEText(message_html_cleaned, "html")
        msg.attach(letterx)

        with total_emails_lock:
            total_emails_sent += 1

        signed_message = msg.as_string()

        server.sendmail(current_smtp['username'], [recipient_email], signed_message)
        server.quit()  # Properly close the SMTP connection
        
        # Add sleep time if configured
        sleep_time = float(sleeptime)
        if sleep_time > 0:
            time.sleep(sleep_time)
            
        outputsucess = f"""
===========================================
SENT {recipient_email}
From : {new_value} <{fromane}>
USER SENT FROM SMTP: {current_smtp['username']}
SMTP SERVER: {current_smtp['host']}:{current_smtp['port']}
Subject: {Newzepy}
{total_emails_sent}/{len(email_list_copy)}
===========================================
        """
        testmode = config['Settings']['TESTMODE']
        if testmode == '0':
            successfully_sent_emails.append(recipient_email)
        print(Fore.GREEN + Style.BRIGHT + outputsucess)
    except Exception as e:
        # Ensure server connection is closed on error
        try:
            if server:
                server.quit()
        except:
            pass
        
        # Track server failures
        if current_smtp:
            server_key = f"{current_smtp['host']}:{current_smtp['port']}"
            with failed_servers_lock:
                failed_servers[server_key] = failed_servers.get(server_key, 0) + 1
                if failed_servers[server_key] >= 2:
                    print(f"WARNING: SMTP server {server_key} DISABLED after {failed_servers[server_key]} failures - will be skipped")
        
        print(e)
        smtp_info = f"{current_smtp['host']}:{current_smtp['port']}" if current_smtp else "Unknown SMTP"
        failedsent = f"""
===========================================
Failed {recipient_email}
Reason: {e}
From : {new_value} <{fromane}>
SMTP SERVER: {smtp_info}
{total_emails_sent}/{len(recipient_email_list)}
===========================================
"""
        print(Fore.RED + Style.BRIGHT + failedsent)
        smtp_error_occurred = True

with concurrent.futures.ThreadPoolExecutor(max_connections) as executor:
    executor.map(send_email, recipient_email_list)
    if smtp_error_occurred:
        executor._threads.clear()
        executor.shutdown(wait=True)

for sent_email in successfully_sent_emails:
    recipient_email_list.remove(sent_email)

with open(config['Settings']['emailspath'], 'w') as file:
    for recipient_email in recipient_email_list:
        file.write(f"{recipient_email}\n")

print(f"Total emails sent: {total_emails_sent}")

# Print server failure statistics
if failed_servers:
    print("\n" + "="*50)
    print("SMTP SERVER FAILURE STATISTICS:")
    print("="*50)
    for server_key, failures in failed_servers.items():
        status = "DISABLED" if failures >= 2 else "ACTIVE"
        print(f"{server_key}: {failures} failures - {status}")
    print("="*50)
