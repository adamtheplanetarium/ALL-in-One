"""
Email Templates API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.email import EmailTemplate

bp = Blueprint('templates', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_templates():
    """Get all templates"""
    try:
        user_id = get_jwt_identity()
        templates = EmailTemplate.query.filter_by(user_id=user_id).all()
        return jsonify([template.to_dict() for template in templates]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """Create new template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        template = EmailTemplate(
            user_id=user_id,
            name=data['name'],
            subject=data['subject'],
            html_content=data['html_content'],
            variables=data.get('variables', [])
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({'message': 'Template created', 'template': template.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
