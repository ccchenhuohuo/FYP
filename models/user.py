"""
User model definition
"""
from flask_login import UserMixin
from . import db
from datetime import datetime
from .enums import AccountStatus

class User(db.Model, UserMixin):
    """
    User model
    Corresponds to the user table in the database
    """
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), unique=True, nullable=False)
    user_email = db.Column(db.String(120), unique=True, nullable=False)
    user_password = db.Column(db.String(200), nullable=False)
    account_status = db.Column(db.Enum(AccountStatus), default=AccountStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Relationship
    balance = db.relationship('AccountBalance', backref='user', uselist=False, lazy=True)
    fund_transactions = db.relationship('FundTransaction', backref='user', lazy=True)
    
    def get_id(self):
        """
        Return user ID (Flask-Login requirement)
        """
        return str(self.user_id)
    
    @property
    def is_admin(self):
        """
        Determine if the user is an administrator
        Used for Flask-Login and permission checks
        
        Returns:
            bool: Always return False, because this is a normal user
        """
        return False
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<User {self.user_name}>'