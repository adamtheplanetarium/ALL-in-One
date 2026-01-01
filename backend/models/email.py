"""
FROM Address and Email Template models
"""
from models import db, generate_uuid
from datetime import datetime


class FromAddress(db.Model):
    """FROM Address model for sender emails"""
    
    __tablename__ = 'from_addresses'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255))  # Display name for FROM header
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)  # When verification succeeded
    verification_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='unverified')  # 'verified', 'unverified', 'verifying', 'dead', 'collected', 'bounced'
    last_checked = db.Column(db.DateTime)
    last_error = db.Column(db.Text)  # Last error message
    source = db.Column(db.String(100))  # 'manual', 'imported', 'monitored', 'bulk_import', 'inbox_monitor', 'inbox_extraction'
    extracted_at = db.Column(db.DateTime)  # When extracted from inbox
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'verified': self.verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'status': self.status,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'last_error': self.last_error,
            'source': self.source,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<FromAddress {self.email}>'


class EmailTemplate(db.Model):
    """Email Template model"""
    
    __tablename__ = 'email_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    variables = db.Column(db.JSON)  # Array of supported variables
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='template', lazy='dynamic')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'subject': self.subject,
            'html_content': self.html_content,
            'variables': self.variables or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'


class EmailLog(db.Model):
    """Email Log model for activity logging"""
    
    __tablename__ = 'email_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), index=True)
    level = db.Column(db.String(20), nullable=False)  # 'info', 'success', 'warning', 'error'
    message = db.Column(db.Text, nullable=False)
    smtp_server_id = db.Column(db.String(36), db.ForeignKey('smtp_servers.id'))
    from_address = db.Column(db.String(255))
    to_address = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'level': self.level,
            'message': self.message,
            'smtp_server_id': self.smtp_server_id,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<EmailLog {self.level}: {self.message[:50]}>'


class IMAPAccount(db.Model):
    """IMAP Account model for inbox monitoring"""
    
    __tablename__ = 'imap_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password_encrypted = db.Column(db.Text, nullable=False)
    use_ssl = db.Column(db.Boolean, default=True)
    folders = db.Column(db.JSON)  # Array of folders to monitor
    poll_interval = db.Column(db.Integer, default=60)  # seconds
    status = db.Column(db.String(20), default='inactive')  # 'active', 'inactive', 'error'
    last_check = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Encrypt and set password"""
        from utils.encryption import encrypt_password
        self.password_encrypted = encrypt_password(password)
    
    def get_password(self):
        """Decrypt and return password"""
        from utils.encryption import decrypt_password
        return decrypt_password(self.password_encrypted)
    
    def to_dict(self, include_password=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'use_ssl': self.use_ssl,
            'folders': self.folders or ['INBOX'],
            'poll_interval': self.poll_interval,
            'status': self.status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_password:
            data['password'] = self.get_password()
        return data
    
    def __repr__(self):
        return f'<IMAPAccount {self.username}@{self.host}>'
