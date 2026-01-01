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
