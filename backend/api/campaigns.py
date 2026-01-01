"""
Complete Campaign API with Celery Background Task Integration
Handles campaign lifecycle: create, start, pause, resume, stop, stats
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.campaign import Campaign, Recipient
from models.smtp import SMTPServer
from models.email import FromAddress, EmailTemplate
from datetime import datetime
import uuid

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


@bp.route('/<campaign_id>', methods=['GET'])
@jwt_required()
def get_campaign(campaign_id):
    """Get specific campaign with details"""
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get campaign data with stats
        data = campaign.to_dict()
        data['smtp_count'] = campaign.smtp_servers.count()
        data['from_count'] = campaign.from_addresses.count()
        data['recipient_stats'] = {
            'total': campaign.recipients.count(),
            'pending': campaign.recipients.filter_by(status='pending').count(),
            'sent': campaign.recipients.filter_by(status='sent').count(),
            'failed': campaign.recipients.filter_by(status='failed').count()
        }
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_campaign():
    """
    Create new campaign with recipients, SMTPs, and FROM addresses
    
    Request body:
    {
        "name": "Campaign Name",
        "subject": "Email Subject {NAME} {DATE}",
        "template": "<html>Email body with {RECIPIENT}</html>",
        "sleep_interval": 1.0,
        "thread_count": 10,
        "recipients": ["email1@example.com", "email2@example.com"],
        "smtp_ids": ["smtp-id-1", "smtp-id-2"],
        "from_ids": ["from-id-1", "from-id-2"]
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Campaign name required'}), 400
        if not data.get('recipients'):
            return jsonify({'error': 'Recipients required'}), 400
        if not data.get('smtp_ids'):
            return jsonify({'error': 'SMTP servers required'}), 400
        if not data.get('from_ids'):
            return jsonify({'error': 'FROM addresses required'}), 400
        
        # Create campaign
        campaign = Campaign(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data['name'],
            campaign_type=data.get('campaign_type', 'bulk_sending'),
            subject=data.get('subject', 'Important Message'),
            template=data.get('template', '<p>Hello {RECIPIENT}</p>'),
            sleep_interval=data.get('sleep_interval', 1.0),
            thread_count=data.get('thread_count', 10),
            retry_count=data.get('retry_count', 5),
            status='pending'
        )
        
        db.session.add(campaign)
        db.session.flush()
        
        # Add recipients
        recipients_list = data['recipients']
        for email in recipients_list:
            recipient = Recipient(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                email=email.strip(),
                status='pending'
            )
            db.session.add(recipient)
        
        campaign.total_recipients = len(recipients_list)
        
        # Associate SMTP servers
        smtp_ids = data['smtp_ids']
        smtps = SMTPServer.query.filter(
            SMTPServer.id.in_(smtp_ids),
            SMTPServer.user_id == user_id
        ).all()
        campaign.smtp_servers.extend(smtps)
        
        # Associate FROM addresses
        from_ids = data['from_ids']
        froms = FromAddress.query.filter(
            FromAddress.id.in_(from_ids),
            FromAddress.user_id == user_id
        ).all()
        campaign.from_addresses.extend(froms)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Campaign created successfully',
            'campaign': campaign.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/start', methods=['POST'])
@jwt_required()
def start_campaign(campaign_id):
    """
    Start campaign - Queue to Celery background worker
    Campaign will run INDEPENDENTLY of browser session
    """
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status == 'running':
            return jsonify({'error': 'Campaign already running'}), 400
        
        if campaign.status == 'completed':
            return jsonify({'error': 'Campaign already completed'}), 400
        
        # Validate campaign has required data
        if campaign.smtp_servers.count() == 0:
            return jsonify({'error': 'No SMTP servers assigned'}), 400
        
        if campaign.from_addresses.count() == 0:
            return jsonify({'error': 'No FROM addresses assigned'}), 400
        
        if campaign.recipients.filter_by(status='pending').count() == 0:
            return jsonify({'error': 'No pending recipients'}), 400
        
        # Queue campaign to Celery (BACKGROUND TASK!)
        from tasks.campaign_tasks import bulk_send_campaign
        task = bulk_send_campaign.delay(campaign_id)
        
        # Update campaign
        campaign.status = 'queued'
        campaign.celery_task_id = task.id
        db.session.commit()
        
        return jsonify({
            'message': 'Campaign started in background',
            'campaign_id': campaign_id,
            'task_id': task.id,
            'status': 'queued'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/pause', methods=['POST'])
@jwt_required()
def pause_campaign(campaign_id):
    """Pause running campaign"""
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status != 'running':
            return jsonify({'error': f'Cannot pause campaign with status: {campaign.status}'}), 400
        
        # Queue pause task
        from tasks.campaign_tasks import pause_campaign as pause_task
        pause_task.delay(campaign_id)
        
        return jsonify({
            'message': 'Campaign pause requested',
            'campaign_id': campaign_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/resume', methods=['POST'])
@jwt_required()
def resume_campaign(campaign_id):
    """Resume paused campaign"""
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status != 'paused':
            return jsonify({'error': f'Cannot resume campaign with status: {campaign.status}'}), 400
        
        # Queue resume task
        from tasks.campaign_tasks import resume_campaign as resume_task
        resume_task.delay(campaign_id)
        
        return jsonify({
            'message': 'Campaign resume requested',
            'campaign_id': campaign_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/stop', methods=['POST'])
@jwt_required()
def stop_campaign(campaign_id):
    """Stop running campaign"""
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status not in ['running', 'paused', 'queued']:
            return jsonify({'error': f'Cannot stop campaign with status: {campaign.status}'}), 400
        
        # Queue stop task
        from tasks.campaign_tasks import stop_campaign as stop_task
        stop_task.delay(campaign_id)
        
        return jsonify({
            'message': 'Campaign stop requested',
            'campaign_id': campaign_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/stats', methods=['GET'])
@jwt_required()
def get_campaign_stats(campaign_id):
    """
    Get real-time campaign statistics
    This endpoint is polled by frontend for live updates
    """
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Calculate statistics
        total = campaign.recipients.count()
        sent = campaign.recipients.filter_by(status='sent').count()
        failed = campaign.recipients.filter_by(status='failed').count()
        pending = campaign.recipients.filter_by(status='pending').count()
        
        progress = (sent / total * 100) if total > 0 else 0
        
        # Get active SMTP info
        active_smtps = campaign.smtp_servers.filter_by(status='active').count()
        disabled_smtps = campaign.smtp_servers.filter(SMTPServer.failures >= 10).count()
        
        stats = {
            'campaign_id': campaign_id,
            'status': campaign.status,
            'total_recipients': total,
            'sent': sent,
            'failed': failed,
            'pending': pending,
            'progress': round(progress, 2),
            'started_at': campaign.started_at.isoformat() if campaign.started_at else None,
            'completed_at': campaign.completed_at.isoformat() if campaign.completed_at else None,
            'smtp_stats': {
                'active': active_smtps,
                'disabled': disabled_smtps,
                'total': campaign.smtp_servers.count()
            },
            'from_addresses': campaign.from_addresses.count(),
            'celery_task_id': campaign.celery_task_id,
            'error': campaign.error
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/logs', methods=['GET'])
@jwt_required()
def get_campaign_logs(campaign_id):
    """Get campaign email logs"""
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status_filter = request.args.get('status')  # 'sent', 'failed', or None
        
        # Query logs
        query = campaign.logs.order_by(db.desc('sent_at'))
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'logs': [log.to_dict() for log in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>', methods=['DELETE'])
@jwt_required()
def delete_campaign(campaign_id):
    """Delete campaign (only if not running)"""
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status in ['running', 'queued']:
            return jsonify({'error': 'Cannot delete running campaign. Stop it first.'}), 400
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({'message': 'Campaign deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<campaign_id>/recipients/bulk', methods=['POST'])
@jwt_required()
def bulk_import_recipients(campaign_id):
    """
    Bulk import recipients from text (one email per line)
    """
    try:
        user_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign.status == 'running':
            return jsonify({'error': 'Cannot add recipients to running campaign'}), 400
        
        data = request.get_json()
        text = data.get('text', '')
        
        # Parse emails
        lines = text.strip().split('\n')
        emails = [line.strip() for line in lines if line.strip() and '@' in line]
        
        added = 0
        for email in emails:
            # Check if already exists
            exists = Recipient.query.filter_by(
                campaign_id=campaign_id,
                email=email
            ).first()
            
            if not exists:
                recipient = Recipient(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign_id,
                    email=email,
                    status='pending'
                )
                db.session.add(recipient)
                added += 1
        
        campaign.total_recipients = campaign.recipients.count()
        db.session.commit()
        
        return jsonify({
            'message': f'Imported {added} recipients',
            'total_recipients': campaign.total_recipients
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
