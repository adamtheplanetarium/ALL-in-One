"""
Inbox Monitoring Background Tasks
Port from: Fake-client/GUI-Mailer/inbox_monitor.py
"""
from celery import current_task
from tasks.celery_app import celery_app, db, app
from models.email import FromAddress, IMAPAccount
import imaplib
import email
import re
import time
from datetime import datetime, timedelta
from email.utils import parseaddr


@celery_app.task(bind=True)
def monitor_inbox_continuous(self, monitor_config):
    """
    Continuously monitor IMAP inbox for new emails and extract FROM addresses
    
    Args:
        monitor_config: {
            'imap_account': {imap connection details},
            'poll_interval': 60,  # seconds between checks
            'max_emails': 100,  # max emails to process per check
            'extract_patterns': ['.*@.*'],  # regex patterns for extraction
            'auto_verify': False  # auto-verify extracted addresses
        }
    
    This task runs continuously until manually stopped.
    """
    with app.app_context():
        imap_config = monitor_config.get('imap_account')
        poll_interval = monitor_config.get('poll_interval', 60)
        max_emails = monitor_config.get('max_emails', 100)
        extract_patterns = monitor_config.get('extract_patterns', ['.*@.*'])
        auto_verify = monitor_config.get('auto_verify', False)
        
        # Compile regex patterns
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in extract_patterns]
        
        print(f'Starting inbox monitor for {imap_config["email"]}')
        print(f'Poll interval: {poll_interval} seconds')
        print(f'Patterns: {extract_patterns}')
        
        total_extracted = 0
        last_check_time = datetime.utcnow() - timedelta(minutes=5)  # Start from 5 minutes ago
        
        while True:
            try:
                # Update task state
                self.update_state(
                    state='MONITORING',
                    meta={
                        'message': 'Monitoring inbox...',
                        'total_extracted': total_extracted,
                        'last_check': last_check_time.isoformat()
                    }
                )
                
                # Connect to IMAP
                imap = imaplib.IMAP4_SSL(imap_config['host'], imap_config.get('port', 993))
                imap.login(imap_config['email'], imap_config['password'])
                imap.select('INBOX')
                
                # Search for emails since last check
                since_date = last_check_time.strftime('%d-%b-%Y')
                search_criteria = f'(SINCE {since_date})'
                
                status, messages = imap.search(None, search_criteria)
                if status != 'OK':
                    raise Exception('IMAP search failed')
                
                message_ids = messages[0].split()
                
                # Limit to max_emails
                if len(message_ids) > max_emails:
                    message_ids = message_ids[-max_emails:]
                
                print(f'Found {len(message_ids)} new emails')
                
                extracted_addresses = set()
                
                # Process each email
                for msg_id in message_ids:
                    try:
                        status, msg_data = imap.fetch(msg_id, '(RFC822)')
                        if status != 'OK':
                            continue
                        
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract FROM address
                        from_header = email_message.get('From', '')
                        from_name, from_email = parseaddr(from_header)
                        
                        if from_email and self._is_valid_email(from_email):
                            # Check if matches patterns
                            for pattern in compiled_patterns:
                                if pattern.match(from_email):
                                    extracted_addresses.add((from_email, from_name))
                                    break
                        
                        # Also extract from Reply-To
                        reply_to = email_message.get('Reply-To', '')
                        if reply_to:
                            reply_name, reply_email = parseaddr(reply_to)
                            if reply_email and self._is_valid_email(reply_email):
                                for pattern in compiled_patterns:
                                    if pattern.match(reply_email):
                                        extracted_addresses.add((reply_email, reply_name))
                                        break
                    
                    except Exception as e:
                        print(f'Error processing email {msg_id}: {e}')
                        continue
                
                imap.close()
                imap.logout()
                
                # Save extracted addresses to database
                if extracted_addresses:
                    print(f'Extracted {len(extracted_addresses)} unique addresses')
                    
                    for email_addr, name in extracted_addresses:
                        # Check if already exists
                        existing = db.session.query(FromAddress).filter_by(
                            email=email_addr
                        ).first()
                        
                        if not existing:
                            # Create new FROM address
                            new_from = FromAddress(
                                email=email_addr,
                                name=name if name else None,
                                status='unverified',
                                source='inbox_monitor',
                                extracted_at=datetime.utcnow()
                            )
                            db.session.add(new_from)
                            total_extracted += 1
                            print(f'Added new FROM: {email_addr}')
                        elif existing.status == 'dead' and auto_verify:
                            # Update existing dead address status
                            existing.status = 'unverified'
                            existing.extracted_at = datetime.utcnow()
                            print(f'Updated dead FROM: {email_addr}')
                    
                    db.session.commit()
                
                # Update last check time
                last_check_time = datetime.utcnow()
                
                # Wait for next poll
                print(f'Sleeping {poll_interval} seconds...')
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f'Monitor error: {e}')
                # Wait before retrying
                time.sleep(poll_interval)
                continue
    
    def _is_valid_email(self, email_addr):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email_addr) is not None


@celery_app.task(bind=True)
def extract_from_addresses_once(self, imap_config, lookback_hours=24, max_emails=500):
    """
    Extract FROM addresses from inbox once (not continuous)
    
    Args:
        imap_config: IMAP connection details
        lookback_hours: How many hours back to search
        max_emails: Max emails to process
    
    Returns:
        {
            'extracted': [list of extracted email addresses],
            'total_count': int,
            'new_count': int
        }
    """
    with app.app_context():
        print(f'Extracting FROM addresses from {imap_config["email"]}')
        print(f'Lookback: {lookback_hours} hours, Max emails: {max_emails}')
        
        results = {
            'extracted': [],
            'total_count': 0,
            'new_count': 0
        }
        
        try:
            # Connect to IMAP
            imap = imaplib.IMAP4_SSL(imap_config['host'], imap_config.get('port', 993))
            imap.login(imap_config['email'], imap_config['password'])
            imap.select('INBOX')
            
            # Search for emails
            since_date = (datetime.utcnow() - timedelta(hours=lookback_hours)).strftime('%d-%b-%Y')
            search_criteria = f'(SINCE {since_date})'
            
            status, messages = imap.search(None, search_criteria)
            if status != 'OK':
                raise Exception('IMAP search failed')
            
            message_ids = messages[0].split()
            
            # Limit to max_emails
            if len(message_ids) > max_emails:
                message_ids = message_ids[-max_emails:]
            
            print(f'Processing {len(message_ids)} emails...')
            
            extracted_addresses = set()
            
            # Process each email
            for i, msg_id in enumerate(message_ids):
                try:
                    # Update progress
                    if i % 10 == 0:
                        self.update_state(
                            state='PROCESSING',
                            meta={'processed': i, 'total': len(message_ids)}
                        )
                    
                    status, msg_data = imap.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract FROM
                    from_header = email_message.get('From', '')
                    from_name, from_email = parseaddr(from_header)
                    
                    if from_email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', from_email):
                        extracted_addresses.add((from_email, from_name))
                    
                    # Extract Reply-To
                    reply_to = email_message.get('Reply-To', '')
                    if reply_to:
                        reply_name, reply_email = parseaddr(reply_to)
                        if reply_email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', reply_email):
                            extracted_addresses.add((reply_email, reply_name))
                
                except Exception as e:
                    print(f'Error processing email {msg_id}: {e}')
                    continue
            
            imap.close()
            imap.logout()
            
            results['total_count'] = len(extracted_addresses)
            
            # Save to database
            for email_addr, name in extracted_addresses:
                existing = db.session.query(FromAddress).filter_by(email=email_addr).first()
                
                if not existing:
                    new_from = FromAddress(
                        email=email_addr,
                        name=name if name else None,
                        status='unverified',
                        source='inbox_extraction',
                        extracted_at=datetime.utcnow()
                    )
                    db.session.add(new_from)
                    results['new_count'] += 1
                    results['extracted'].append(email_addr)
            
            db.session.commit()
            
            print(f'Extraction complete: {results["total_count"]} total, {results["new_count"]} new')
            return results
            
        except Exception as e:
            print(f'Extraction error: {e}')
            return {'error': str(e)}
