"""
SMTP Server API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.smtp import SMTPServer
import smtplib

bp = Blueprint('smtp', __name__)


@bp.route('', methods=['GET'])
@jwt_required()
def get_smtp_servers():
    """Get all SMTP servers for current user"""
    try:
        user_id = get_jwt_identity()
        servers = SMTPServer.query.filter_by(user_id=user_id).all()
        
        return jsonify([server.to_dict() for server in servers]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_smtp_server():
    """Create new SMTP server"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['host', 'port', 'username', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create server
        server = SMTPServer(
            user_id=user_id,
            host=data['host'],
            port=data['port'],
            username=data['username']
        )
        server.set_password(data['password'])
        
        db.session.add(server)
        db.session.commit()
        
        return jsonify({
            'message': 'SMTP server created successfully',
            'server': server.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<server_id>', methods=['PUT'])
@jwt_required()
def update_smtp_server(server_id):
    """Update SMTP server"""
    try:
        user_id = get_jwt_identity()
        server = SMTPServer.query.filter_by(id=server_id, user_id=user_id).first()
        
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'host' in data:
            server.host = data['host']
        if 'port' in data:
            server.port = data['port']
        if 'username' in data:
            server.username = data['username']
        if 'password' in data:
            server.set_password(data['password'])
        if 'status' in data:
            server.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'message': 'SMTP server updated successfully',
            'server': server.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<server_id>', methods=['DELETE'])
@jwt_required()
def delete_smtp_server(server_id):
    """Delete SMTP server"""
    try:
        user_id = get_jwt_identity()
        server = SMTPServer.query.filter_by(id=server_id, user_id=user_id).first()
        
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        db.session.delete(server)
        db.session.commit()
        
        return jsonify({'message': 'SMTP server deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<server_id>/test', methods=['POST'])
@jwt_required()
def test_smtp_server(server_id):
    """Test SMTP server connection"""
    try:
        user_id = get_jwt_identity()
        server = SMTPServer.query.filter_by(id=server_id, user_id=user_id).first()
        
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        # Try to connect
        try:
            smtp = smtplib.SMTP(server.host, server.port, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(server.username, server.get_password())
            smtp.quit()
            
            # Update status
            server.status = 'active'
            db.session.commit()
            
            return jsonify({
                'message': 'Connection successful',
                'status': 'success'
            }), 200
            
        except Exception as conn_error:
            # Update status
            server.status = 'failed'
            server.failure_count += 1
            db.session.commit()
            
            return jsonify({
                'message': 'Connection failed',
                'status': 'failed',
                'error': str(conn_error)
            }), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/bulk-import', methods=['POST'])
@jwt_required()
def bulk_import_smtp():
    """Bulk import SMTP servers"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'servers' not in data:
            return jsonify({'error': 'No servers provided'}), 400
        
        servers_text = data['servers']
        lines = [line.strip() for line in servers_text.split('\n') if line.strip()]
        
        created = 0
        errors = []
        
        for line in lines:
            try:
                # Support both formats: host,port,username,password and username:password:host:port
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 4:
                        host, port, username, password = parts[0], int(parts[1]), parts[2], parts[3]
                    else:
                        errors.append(f"Invalid format: {line}")
                        continue
                elif ':' in line and line.count(':') >= 3:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        username, password, host, port = parts[0], parts[1], parts[2], int(parts[3])
                    else:
                        errors.append(f"Invalid format: {line}")
                        continue
                else:
                    errors.append(f"Invalid format: {line}")
                    continue
                
                server = SMTPServer(
                    user_id=user_id,
                    host=host,
                    port=port,
                    username=username
                )
                server.set_password(password)
                db.session.add(server)
                created += 1
                
            except Exception as parse_error:
                errors.append(f"Error parsing '{line}': {str(parse_error)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {created} servers created',
            'created': created,
            'errors': errors
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reset-failures', methods=['POST'])
@jwt_required()
def reset_failures():
    """Reset all SMTP failure counts"""
    try:
        user_id = get_jwt_identity()
        servers = SMTPServer.query.filter_by(user_id=user_id).all()
        
        for server in servers:
            server.failure_count = 0
            server.success_count = 0
            if server.status == 'failed':
                server.status = 'active'
        
        db.session.commit()
        
        return jsonify({
            'message': 'All SMTP failure counts reset successfully',
            'count': len(servers)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
