"""
Main Flask Application
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from config import config
from models import db
from models.user import User
from models.smtp import SMTPServer
from models.campaign import Campaign, Recipient
from models.email import FromAddress, EmailTemplate, EmailLog, IMAPAccount
import os


# Initialize extensions
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
jwt = JWTManager()


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    jwt.init_app(app)
    socketio.init_app(app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from api import auth, smtp, campaigns, from_addresses, templates, stats
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(smtp.bp, url_prefix='/api/smtp')
    app.register_blueprint(campaigns.bp, url_prefix='/api/campaigns')
    app.register_blueprint(from_addresses.bp, url_prefix='/api/from-addresses')
    app.register_blueprint(templates.bp, url_prefix='/api/templates')
    app.register_blueprint(stats.bp, url_prefix='/api/stats')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'ALL-in-One Email Platform'}), 200
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'service': 'ALL-in-One Email Platform API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth',
                'smtp': '/api/smtp',
                'campaigns': '/api/campaigns',
                'from_addresses': '/api/from-addresses',
                'templates': '/api/templates',
                'stats': '/api/stats'
            }
        }), 200
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
