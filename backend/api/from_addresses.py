"""
FROM Addresses API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.email import FromAddress

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
        "from_ids": ["id1", "id2"],  # FROM addresses to verify
        "test_recipient": "test@example.com",  # Where to send test emails
        "smtp_id": "smtp-id",  # SMTP to use for sending tests
        "imap_host": "imap.example.com",
        "imap_username": "test@example.com",
        "imap_password": "password",
        "wait_time": 300  # Seconds to wait before checking (default 5 minutes)
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required = ['from_ids', 'test_recipient', 'smtp_id', 'imap_host', 'imap_username', 'imap_password']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # TODO: Queue verification task to Celery
        # For now, return success message
        # from tasks.verification_tasks import verify_from_addresses
        # task = verify_from_addresses.delay(verification_id)
        
        return jsonify({
            'message': 'Verification started (feature in progress)',
            'from_count': len(data['from_ids']),
            'wait_time': data.get('wait_time', 300)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
