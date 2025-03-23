"""
管理员模型定义
"""
from flask_login import UserMixin
from . import db
from datetime import datetime

class Admin(db.Model, UserMixin):
    """
    管理员模型
    对应数据库中的admin表
    """
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(80), unique=True, nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    
    def get_id(self):
        """
        返回管理员ID（Flask-Login要求）
        为了区分普通用户和管理员，添加'admin_'前缀
        """
        return f"admin_{self.admin_id}"
    
    @property
    def is_admin(self):
        """
        判断是否为管理员
        """
        return True
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Admin {self.admin_name}>' 