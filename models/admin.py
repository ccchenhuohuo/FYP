"""\nAdmin model definition\n"""
from flask_login import UserMixin
from . import db
from datetime import datetime, timedelta
import re
import logging

# Get logger
logger = logging.getLogger(__name__)

# Define admin related exception types
class AdminError(Exception):
    """Base exception class for admin module"""
    pass

class AdminAuthError(AdminError):
    """Exception related to admin authentication"""
    pass

class AdminAccountLockedError(AdminAuthError):
    """Exception related to admin account locking"""
    def __init__(self, admin_name, locked_until):
        self.admin_name = admin_name
        self.locked_until = locked_until
        self.message = f"Admin account {admin_name} is locked, unlock time: {locked_until}"
        super().__init__(self.message)
        logger.warning(self.message)

class PasswordComplexityError(AdminError):
    """Exception related to password complexity"""
    def __init__(self, errors):
        self.errors = errors
        self.message = f"Password does not meet complexity requirements: {', '.join(errors)}"
        super().__init__(self.message)
        logger.warning(self.message)

# Password complexity requirements configuration
PASSWORD_COMPLEXITY = {
    'min_length': 8,
    'require_upper': True,
    'require_lower': True,
    'require_digit': True,
    'require_special': True
}

def validate_password_complexity(password):
    """
    Validate that the password complexity meets the requirements
    
    Parameters:
        password (str): The password to be validated
        
    Returns:
        tuple: (是否通过验证, 错误信息)
    """
    errors = []
    
    # Check minimum length
    if len(password) < PASSWORD_COMPLEXITY['min_length']:
        errors.append(f"Password must be at least {PASSWORD_COMPLEXITY['min_length']} characters long")
    
    # Check if it contains uppercase letters
    if PASSWORD_COMPLEXITY['require_upper'] and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check if it contains lowercase letters
    if PASSWORD_COMPLEXITY['require_lower'] and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check if it contains digits
    if PASSWORD_COMPLEXITY['require_digit'] and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    # Check if it contains special characters
    if PASSWORD_COMPLEXITY['require_special'] and not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Return validation result
    if errors:
        return False, errors
    return True, []

class Admin(db.Model, UserMixin):
    """
    Admin model
    Corresponds to the admin table in the database
    """
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(80), unique=True, nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    def get_id(self):
        """
        Return admin ID (Flask-Login requirement)
        To distinguish between normal users and admins, add 'admin_' prefix
        """
        return f"admin_{self.admin_id}"
    
    @property
    def is_admin(self):
        """
        Determine if it is an admin
        Used for Flask-Login and permission checks
        
        Returns:
            bool: Always return True, because this is an admin account
        """
        return True
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<Admin {self.admin_name}>' 
        
    def is_account_locked(self):
        """
        Check if the account is locked
        
        Returns:
            bool: If the account is locked, return True, otherwise return False
        Raises:
            AdminAccountLockedError: If the account is locked
        """
        if self.locked_until and self.locked_until > datetime.utcnow():
            logger.info(f"Admin account {self.admin_name} is locked, login attempt rejected")
            raise AdminAccountLockedError(self.admin_name, self.locked_until)
        return False
    
    def increment_login_attempts(self):
        """
        Increment login attempts, if exceeds limit then lock the account
        
        Returns:
            bool: If the account is locked, return True, otherwise return False
        """
        from flask import current_app
        
        # Get maximum attempts and lockout duration from configuration
        max_attempts = current_app.config.get('ADMIN_MAX_LOGIN_ATTEMPTS', 5)
        lockout_duration = current_app.config.get('ADMIN_LOCKOUT_DURATION', 2)
        
        self.login_attempts += 1
        logger.info(f"Admin {self.admin_name} login failed, current attempt: {self.login_attempts}/{max_attempts}")
        
        if self.login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration)
            self.login_attempts = 0
            logger.warning(f"Admin account {self.admin_name} is locked, unlock time: {self.locked_until}")
            return True
        return False
    
    def reset_login_attempts(self):
        """
        Reset login attempts, usually called after successful login
        Also update the last login time
        """
        self.login_attempts = 0
        self.last_login = datetime.utcnow()
        logger.info(f"Admin {self.admin_name} login successfully, reset login attempts")
        return True
    
    @staticmethod
    def validate_new_password(password):
        """
        Validate that the new password meets the complexity requirements
        
        Parameters:
            password (str): The password to be validated
            
        Returns:
            tuple: (是否通过验证, 错误信息)
        Raises:
            PasswordComplexityError: If the password does not meet the complexity requirements
        """
        try:
            return validate_password_complexity(password)
        except PasswordComplexityError as e:
            logger.warning(f"New password validation failed: {e.message}")
            return False, e.errors