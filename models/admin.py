"""\n管理员模型定义\n"""
from flask_login import UserMixin
from . import db
from datetime import datetime, timedelta
import re
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)

# 定义管理员相关的异常类型
class AdminError(Exception):
    """管理员模块基础异常类"""
    pass

class AdminAuthError(AdminError):
    """管理员认证相关异常"""
    pass

class AdminAccountLockedError(AdminAuthError):
    """管理员账户锁定异常"""
    def __init__(self, admin_name, locked_until):
        self.admin_name = admin_name
        self.locked_until = locked_until
        self.message = f"管理员账户 {admin_name} 已被锁定，解锁时间: {locked_until}"
        super().__init__(self.message)
        logger.warning(self.message)

class PasswordComplexityError(AdminError):
    """密码复杂度不符合要求异常"""
    def __init__(self, errors):
        self.errors = errors
        self.message = f"密码不符合复杂度要求: {', '.join(errors)}"
        super().__init__(self.message)
        logger.warning(self.message)

# 密码复杂度要求配置
PASSWORD_COMPLEXITY = {
    'min_length': 8,
    'require_upper': True,
    'require_lower': True,
    'require_digit': True,
    'require_special': True
}

def validate_password_complexity(password):
    """
    验证密码复杂度是否符合要求
    
    参数:
        password (str): 待验证的密码
        
    返回:
        tuple: (是否通过验证, 错误信息)
    """
    errors = []
    
    # 检查最小长度
    if len(password) < PASSWORD_COMPLEXITY['min_length']:
        errors.append(f"密码长度必须至少为{PASSWORD_COMPLEXITY['min_length']}个字符")
    
    # 检查是否包含大写字母
    if PASSWORD_COMPLEXITY['require_upper'] and not re.search(r'[A-Z]', password):
        errors.append("密码必须包含至少一个大写字母")
    
    # 检查是否包含小写字母
    if PASSWORD_COMPLEXITY['require_lower'] and not re.search(r'[a-z]', password):
        errors.append("密码必须包含至少一个小写字母")
    
    # 检查是否包含数字
    if PASSWORD_COMPLEXITY['require_digit'] and not re.search(r'\d', password):
        errors.append("密码必须包含至少一个数字")
    
    # 检查是否包含特殊字符
    if PASSWORD_COMPLEXITY['require_special'] and not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        errors.append("密码必须包含至少一个特殊字符")
    
    # 返回验证结果
    if errors:
        return False, errors
    return True, []

class Admin(db.Model, UserMixin):
    """
    管理员模型
    对应数据库中的admin表
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
        返回管理员ID（Flask-Login要求）
        为了区分普通用户和管理员，添加'admin_'前缀
        """
        return f"admin_{self.admin_id}"
    
    @property
    def is_admin(self):
        """
        判断是否为管理员
        用于Flask-Login和权限检查
        
        返回:
            bool: 始终返回True，因为这是管理员账户
        """
        return True
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Admin {self.admin_name}>' 
        
    def is_account_locked(self):
        """
        检查账户是否被锁定
        
        返回:
            bool: 如果账户被锁定返回True，否则返回False
        抛出:
            AdminAccountLockedError: 如果账户被锁定
        """
        if self.locked_until and self.locked_until > datetime.utcnow():
            logger.info(f"管理员账户 {self.admin_name} 被锁定，尝试登录被拒绝")
            raise AdminAccountLockedError(self.admin_name, self.locked_until)
        return False
    
    def increment_login_attempts(self):
        """
        增加登录尝试次数，如果超过限制则锁定账户
        
        返回:
            bool: 如果账户被锁定返回True，否则返回False
        """
        from flask import current_app
        
        # 从配置中获取最大尝试次数和锁定时间
        max_attempts = current_app.config.get('ADMIN_MAX_LOGIN_ATTEMPTS', 5)
        lockout_duration = current_app.config.get('ADMIN_LOCKOUT_DURATION', 2)
        
        self.login_attempts += 1
        logger.info(f"管理员 {self.admin_name} 登录失败，当前尝试次数: {self.login_attempts}/{max_attempts}")
        
        if self.login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration)
            self.login_attempts = 0
            logger.warning(f"管理员账户 {self.admin_name} 已被锁定，解锁时间: {self.locked_until}")
            return True
        return False
    
    def reset_login_attempts(self):
        """
        重置登录尝试次数，通常在登录成功后调用
        同时更新最后登录时间
        """
        self.login_attempts = 0
        self.last_login = datetime.utcnow()
        logger.info(f"管理员 {self.admin_name} 登录成功，重置登录尝试次数")
        return True
    
    @staticmethod
    def validate_new_password(password):
        """
        验证新密码是否符合复杂度要求
        
        参数:
            password (str): 待验证的密码
            
        返回:
            tuple: (是否通过验证, 错误信息)
            
        抛出:
            PasswordComplexityError: 如果密码不符合复杂度要求
        """
        try:
            return validate_password_complexity(password)
        except PasswordComplexityError as e:
            logger.warning(f"新密码验证失败: {e.message}")
            return False, e.errors