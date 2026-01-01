"""
FROM Addresses API endpoints with Celery verification
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.email import FromAddress
from models.smtp import SMTPServer

bp = Blueprint('from_addresses', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_from_addresses():
    """Get all FROM addresses"""
    try:
        user_id = get_jwt_identity()
        addresses = FromAddress.query.filter_by(user_id=user_id).all()
        return jsonify([addr.to_dict() for addr in addresses]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_from_address():
    """Create new FROM address"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        address = FromAddress(
            user_id=user_id,
            email=data['email'],
            status=data.get('status', 'unverified'),
            source=data.get('source', 'manual')
        )
        
        db.session.add(address)
        db.session.commit()
        
        return jsonify({'message': 'FROM address created', 'address': address.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/bulk-import', methods=['POST'])
@jwt_required()
def bulk_import_from_addresses():
    """Bulk import FROM addresses from text (one email per line)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'emails' not in data:
            return jsonify({'error': 'No emails provided'}), 400
        
        emails_text = data['emails']
        lines = [line.strip() for line in emails_text.split('\n') if line.strip()]
        
        created = 0
        skipped = 0
        
        for line in lines:
            # Basic email validation
            if '@' not in line or '.' not in line:
                skipped += 1
                continue
            
            # Check if already exists
            exists = FromAddress.query.filter_by(
                user_id=user_id,
                email=line
            ).first()
            
            if exists:
                skipped += 1
                continue
            
            # Create new
            address = FromAddress(
                user_id=user_id,
                email=line,
                status='unverified',
                source='bulk_import'
            )
            db.session.add(address)
            created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {created} addresses created, {skipped} skipped',
            'created': created,
            'skipped': skipped
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/verify', methods=['POST'])
@jwt_required()
def start_verification():
    """
    Start FROM address verification process (background task)
    
    Request body:
    {
        "from_ids": [1, 2, 3],  # FROM addresses to verify
        "smtp_id": 1,  # SMTP server to use for sending tests
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "imap_email": "test@example.com",
        "imap_password": "password",
        "wait_time": 300  # Seconds to wait before checking (default 5 minutes)
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required = ['from_ids', 'smtp_id', 'imap_host', 'imap_email', 'imap_password']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get SMTP server
        smtp = SMTPServer.query.get(data['smtp_id'])
        if not smtp or smtp.user_id != user_id:
            return jsonify({'error': 'SMTP server not found'}), 404
        
        # Prepare verification data
        from utils.encryption import decrypt_password
        
        verification_data = {
            'from_addresses': data['from_ids'],
            'smtp_server': {
                'host': smtp.host,
                'port': smtp.port,
                'username': smtp.username,
                'password': decrypt_password(smtp.password_encrypted)
            },
            'imap_account': {
                'host': data['imap_host'],
                'port': data.get('imap_port', 993),
                'email': data['imap_email'],
                'password': data['imap_password']
            },
            'subject_prefix': 'Verification Test',
            'wait_time': data.get('wait_time', 300)
        }
        
        # Queue verification task to Celery
        from tasks.verification_tasks import verify_from_addresses
        task = verify_from_addresses.delay(verification_data)
        
        return jsonify({
            'message': 'Verification started in background',
            'task_id': task.id,
            'from_count': len(data['from_ids']),
            'wait_time': verification_data['wait_time']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/extract-from-inbox', methods=['POST'])
@jwt_required()
def extract_from_inbox():
    """
    Extract FROM addresses from IMAP inbox (one-time extraction)
    
    Request body:
    {
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "imap_email": "test@example.com",
        "imap_password": "password",
        "lookback_hours": 24,
        "max_emails": 500
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required = ['imap_host', 'imap_email', 'imap_password']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Prepare IMAP config
        imap_config = {
            'host': data['imap_host'],
            'port': data.get('imap_port', 993),
            'email': data['imap_email'],
            'password': data['imap_password']
        }
        
        lookback_hours = data.get('lookback_hours', 24)
        max_emails = data.get('max_emails', 500)
        
        # Queue extraction task to Celery
        from tasks.monitor_tasks import extract_from_addresses_once
        task = extract_from_addresses_once.delay(imap_config, lookback_hours, max_emails)
        
        return jsonify({
            'message': 'Extraction started in background',
            'task_id': task.id,
            'lookback_hours': lookback_hours,
            'max_emails': max_emails
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
