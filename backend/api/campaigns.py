"""
Campaign API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.campaign import Campaign, Recipient

bp = Blueprint('campaigns', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_campaigns():
    """Get all campaigns for current user"""
    try:
        user_id = get_jwt_identity()
        campaigns = Campaign.query.filter_by(user_id=user_id).order_by(Campaign.created_at.desc()).all()
        return jsonify([campaign.to_dict() for campaign in campaigns]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_campaign():
    """Create new campaign"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        campaign = Campaign(
            user_id=user_id,
            name=data['name'],
            campaign_type=data.get('campaign_type', 'bulk_sending'),
            thread_count=data.get('thread_count', 10),
            delay_seconds=data.get('delay_seconds', 1.0),
            retry_count=data.get('retry_count', 5),
            template_id=data.get('template_id')
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({'message': 'Campaign created', 'campaign': campaign.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
