import imaplib
import email
from email.header import decode_header
import re

# Configuration
EMAIL = "boxer204@att.net"
PASSWORD = "lappbauhnrqhtpop"
IMAP_SERVER = "imap.mail.att.net"
IMAP_PORT = 993
MAILBOX = "Inbox"
OUTPUT_FILE = "fresh_from.txt"

def extract_email(from_header):
    """Extract email address from From header"""
    # Pattern to match email addresses
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    match = re.search(email_pattern, from_header)
    if match:
        return match.group(0)
    return None

def decode_mime_words(s):
    """Decode MIME encoded words"""
    decoded_parts = []
    for part, encoding in decode_header(s):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)

def main():
    print(f"Connecting to {IMAP_SERVER}...")
    
    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        print("Connected successfully!")
        
        # Login
        print(f"Logging in as {EMAIL}...")
        mail.login(EMAIL, PASSWORD)
        print("Logged in successfully!")
        
        # Select the mailbox
        print(f"Selecting mailbox: {MAILBOX}")
        status, messages = mail.select(MAILBOX)
        
        if status != "OK":
            print(f"Failed to select mailbox '{MAILBOX}'")
            print("Available mailboxes:")
            status, mailboxes = mail.list()
            for mailbox in mailboxes:
                print(f"  {mailbox.decode()}")
            return
        
        # Search for all messages
        print("Searching for all messages (read and unread)...")
        status, message_ids = mail.search(None, 'ALL')
        
        if status != "OK":
            print("Failed to search for messages")
            return
        
        message_id_list = message_ids[0].split()
        message_count = len(message_id_list)
        print(f"\n{'='*50}")
        print(f"TOTAL MESSAGES COUNT: {message_count}")
        print(f"{'='*50}\n")
        
        if message_count == 0:
            print("No messages found")
            with open(OUTPUT_FILE, 'w') as f:
                f.write("")
            print(f"Created empty {OUTPUT_FILE}")
            return
        
        # Extract email addresses
        email_addresses = []
        
        for msg_id in message_id_list:
            print(f"Processing message {msg_id.decode()}...")
            
            # Fetch the message
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            
            if status != "OK":
                print(f"Failed to fetch message {msg_id.decode()}")
                continue
            
            # Parse the email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Get the From header
            from_header = msg.get('From', '')
            
            if from_header:
                # Decode if necessary
                from_header = decode_mime_words(from_header)
                print(f"  Sender: {from_header}")
                
                # Check if "Support" is in the from header (case-sensitive)
                if 'Support' in from_header:
                    # Extract email address
                    email_addr = extract_email(from_header)
                    
                    if email_addr:
                        print(f"  ✓ Extracted: {email_addr}")
                        email_addresses.append(email_addr)
                    else:
                        print(f"  ✗ Could not extract email")
                    
                    # Mark the message as read
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    print(f"  ✓ Marked as read")
                else:
                    print(f"  ⊗ Skipped (no 'Support' in sender name)")
        
        # Remove duplicates while preserving order
        unique_emails = []
        seen = set()
        for email_addr in email_addresses:
            if email_addr.lower() not in seen:
                seen.add(email_addr.lower())
                unique_emails.append(email_addr)
        
        # Write to file
        with open(OUTPUT_FILE, 'w') as f:
            for email_addr in unique_emails:
                f.write(email_addr + '\n')
        
        print(f"\n✓ Successfully extracted {len(unique_emails)} unique email addresses")
        print(f"✓ Saved to {OUTPUT_FILE}")
        
        # Logout
        mail.logout()
        print("Disconnected from server")
        
    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
