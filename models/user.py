"""
用户模型定义
"""
from flask_login import UserMixin
from . import db
from datetime import datetime
from .enums import AccountStatus

class User(db.Model, UserMixin):
    """
    用户模型
    对应数据库中的user表
    """
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), unique=True, nullable=False)
    user_email = db.Column(db.String(120), unique=True, nullable=False)
    user_password = db.Column(db.String(200), nullable=False)
    account_status = db.Column(db.Enum(AccountStatus), default=AccountStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # 关联关系
    balance = db.relationship('AccountBalance', backref='user', uselist=False, lazy=True)
    fund_transactions = db.relationship('FundTransaction', backref='user', lazy=True)
    
    def get_id(self):
        """
        返回用户ID（Flask-Login要求）
        """
        return str(self.user_id)
    
    @property
    def is_admin(self):
        """
        判断是否为管理员
        用于Flask-Login和权限检查
        
        返回:
            bool: 始终返回False，因为这是普通用户
        """
        return False
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<User {self.user_name}>'