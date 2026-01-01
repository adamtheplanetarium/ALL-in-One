"""
FROM Address Verification Background Tasks
Port from: Fake-client/GUI-Mailer/verification_manager.py
"""
from celery import current_task
from tasks.celery_app import celery_app, db, app
from models.email import FromAddress, IMAPAccount
from models.associations import verification_froms
import smtplib
import imaplib
import email
import time
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy import update


@celery_app.task(bind=True)
def verify_from_addresses(self, verification_data):
    """
    Verify FROM addresses by sending test emails and checking IMAP inbox
    
    Args:
        verification_data: {
            'from_addresses': [list of from address IDs],
            'smtp_server': {smtp connection details},
            'imap_account': {imap connection details},
            'subject_prefix': 'Verification Test',
            'wait_time': 300  # 5 minutes in seconds
        }
    
    Returns:
        {
            'verified': [list of verified email addresses],
            'failed': [list of failed email addresses],
            'errors': {email: error_message}
        }
    """
    with app.app_context():
        from_ids = verification_data.get('from_addresses', [])
        smtp_config = verification_data.get('smtp_server')
        imap_config = verification_data.get('imap_account')
        subject_prefix = verification_data.get('subject_prefix', 'Verification Test')
        wait_time = verification_data.get('wait_time', 300)
        
        results = {
            'verified': [],
            'failed': [],
            'errors': {}
        }
        
        # Get FROM addresses from database
        from_addresses = db.session.query(FromAddress).filter(
            FromAddress.id.in_(from_ids)
        ).all()
        
        if not from_addresses:
            return {'error': 'No FROM addresses found'}
        
        # Generate unique tracking IDs for each email
        tracking_ids = {}
        for from_addr in from_addresses:
            tracking_ids[from_addr.email] = str(uuid.uuid4())
        
        # Step 1: Send test emails
        print(f'Sending {len(from_addresses)} verification emails...')
        sent_emails = []
        
        try:
            # Connect to SMTP
            smtp = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            smtp.starttls()
            smtp.login(smtp_config['username'], smtp_config['password'])
            
            for from_addr in from_addresses:
                try:
                    tracking_id = tracking_ids[from_addr.email]
                    
                    # Create test email
                    msg = MIMEMultipart()
                    msg['From'] = from_addr.email
                    if from_addr.name:
                        msg['From'] = f'"{from_addr.name}" <{from_addr.email}>'
                    msg['To'] = imap_config['email']
                    msg['Subject'] = f'{subject_prefix} - {tracking_id}'
                    
                    body = f"""
                    This is a verification test email.
                    
                    FROM Address: {from_addr.email}
                    Tracking ID: {tracking_id}
                    Sent at: {datetime.utcnow().isoformat()}
                    
                    If you receive this email, the FROM address is valid and deliverable.
                    """
                    
                    msg.attach(MIMEText(body, 'plain'))
                    
                    # Send email
                    smtp.send_message(msg)
                    sent_emails.append(from_addr.email)
                    print(f'Sent test email from {from_addr.email}')
                    
                    # Update status to verifying
                    from_addr.status = 'verifying'
                    db.session.commit()
                    
                    # Small delay between sends
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f'Failed to send from {from_addr.email}: {error_msg}')
                    results['errors'][from_addr.email] = error_msg
                    from_addr.status = 'dead'
                    from_addr.last_error = error_msg
                    db.session.commit()
            
            smtp.quit()
            
        except Exception as e:
            print(f'SMTP connection error: {e}')
            for from_addr in from_addresses:
                if from_addr.email not in results['errors']:
                    results['errors'][from_addr.email] = f'SMTP Error: {str(e)}'
                    from_addr.status = 'dead'
                    from_addr.last_error = str(e)
            db.session.commit()
            return results
        
        # Step 2: Wait for emails to arrive
        print(f'Waiting {wait_time} seconds for emails to arrive...')
        self.update_state(
            state='WAITING',
            meta={'message': f'Waiting {wait_time} seconds for emails...', 'sent': len(sent_emails)}
        )
        time.sleep(wait_time)
        
        # Step 3: Check IMAP inbox for verification emails
        print('Checking IMAP inbox...')
        try:
            # Connect to IMAP
            imap = imaplib.IMAP4_SSL(imap_config['host'], imap_config.get('port', 993))
            imap.login(imap_config['email'], imap_config['password'])
            imap.select('INBOX')
            
            # Search for emails with subject prefix from the last 10 minutes
            since_date = (datetime.utcnow() - timedelta(minutes=10)).strftime('%d-%b-%Y')
            search_criteria = f'(SINCE {since_date} SUBJECT "{subject_prefix}")'
            
            status, messages = imap.search(None, search_criteria)
            if status != 'OK':
                raise Exception('IMAP search failed')
            
            message_ids = messages[0].split()
            print(f'Found {len(message_ids)} emails in inbox')
            
            # Check each email for tracking IDs
            found_tracking_ids = set()
            
            for msg_id in message_ids:
                try:
                    status, msg_data = imap.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    subject = email_message['Subject']
                    
                    # Extract tracking ID from subject
                    for email_addr, tracking_id in tracking_ids.items():
                        if tracking_id in subject:
                            found_tracking_ids.add(tracking_id)
                            print(f'Found verification email for {email_addr}')
                            break
                    
                except Exception as e:
                    print(f'Error processing email {msg_id}: {e}')
                    continue
            
            imap.close()
            imap.logout()
            
            # Step 4: Update FROM address statuses
            for from_addr in from_addresses:
                if from_addr.email in sent_emails:
                    tracking_id = tracking_ids[from_addr.email]
                    
                    if tracking_id in found_tracking_ids:
                        # Verified!
                        from_addr.status = 'verified'
                        from_addr.verified_at = datetime.utcnow()
                        from_addr.last_error = None
                        results['verified'].append(from_addr.email)
                        print(f'✓ Verified: {from_addr.email}')
                    else:
                        # Not found - mark as dead
                        from_addr.status = 'dead'
                        from_addr.last_error = 'Verification email not received'
                        results['failed'].append(from_addr.email)
                        results['errors'][from_addr.email] = 'Verification email not received'
                        print(f'✗ Failed: {from_addr.email}')
            
            db.session.commit()
            
        except Exception as e:
            print(f'IMAP error: {e}')
            # Mark all unprocessed as failed
            for from_addr in from_addresses:
                if from_addr.email in sent_emails and from_addr.status == 'verifying':
                    from_addr.status = 'unverified'
                    from_addr.last_error = f'IMAP Error: {str(e)}'
                    results['failed'].append(from_addr.email)
                    results['errors'][from_addr.email] = str(e)
            db.session.commit()
        
        print(f'Verification complete: {len(results["verified"])} verified, {len(results["failed"])} failed')
        return results


@celery_app.task(bind=True)
def verify_single_from_address(self, from_address_id, smtp_config, imap_config):
    """
    Verify a single FROM address (convenience wrapper)
    """
    verification_data = {
        'from_addresses': [from_address_id],
        'smtp_server': smtp_config,
        'imap_account': imap_config,
        'subject_prefix': 'Verification Test',
        'wait_time': 300
    }
    return verify_from_addresses(verification_data)
