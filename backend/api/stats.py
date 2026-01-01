"""
Statistics API endpoints
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.campaign import Campaign
from models.smtp import SMTPServer
from models.email import FromAddress
from sqlalchemy import func

bp = Blueprint('stats', __name__)


@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        user_id = get_jwt_identity()
        
        # Campaign stats
        total_campaigns = Campaign.query.filter_by(user_id=user_id).count()
        active_campaigns = Campaign.query.filter_by(user_id=user_id, status='running').count()
        
        # Email stats
        total_sent = db.session.query(func.sum(Campaign.sent_count)).filter_by(user_id=user_id).scalar() or 0
        total_failed = db.session.query(func.sum(Campaign.failed_count)).filter_by(user_id=user_id).scalar() or 0
        
        # SMTP stats
        total_smtp = SMTPServer.query.filter_by(user_id=user_id).count()
        active_smtp = SMTPServer.query.filter_by(user_id=user_id, status='active').count()
        
        # FROM address stats
        verified_froms = FromAddress.query.filter_by(user_id=user_id, verified=True).count()
        unverified_froms = FromAddress.query.filter_by(user_id=user_id, verified=False).count()
        
        return jsonify({
            'campaigns': {
                'total': total_campaigns,
                'active': active_campaigns
            },
            'emails': {
                'sent': int(total_sent),
                'failed': int(total_failed)
            },
            'smtp': {
                'total': total_smtp,
                'active': active_smtp,
                'failed': total_smtp - active_smtp
            },
            'from_addresses': {
                'verified': verified_froms,
                'unverified': unverified_froms,
                'total': verified_froms + unverified_froms
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
