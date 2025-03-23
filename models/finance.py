"""
金融相关模型定义
包括账户余额和资金交易
"""
from . import db
from datetime import datetime

class AccountBalance(db.Model):
    """
    账户余额模型
    对应数据库中的account_balance表
    单独管理用户资金状态
    """
    __tablename__ = 'account_balance'
    
    balance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    available_balance = db.Column(db.Float, nullable=False, default=0.0)  # 可用余额
    frozen_balance = db.Column(db.Float, nullable=False, default=0.0)     # 冻结余额
    total_balance = db.Column(db.Float, nullable=False, default=0.0)      # 总余额 = 可用 + 冻结
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<AccountBalance {self.user_id}: available={self.available_balance}, frozen={self.frozen_balance}>'
        
    def __round__(self, precision=0):
        """
        实现四舍五入方法，使模板中的round过滤器可以正常工作
        
        参数:
        precision (int): 保留的小数位数
        
        返回:
        float: 四舍五入后的值
        """
        # 根据上下文决定要四舍五入的值
        # 默认返回总余额的四舍五入值
        return round(self.total_balance, precision)

class FundTransaction(db.Model):
    """
    资金交易模型
    对应数据库中的fund_transaction表
    统一管理充值、提现等资金操作记录
    """
    __tablename__ = 'fund_transaction'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    remark = db.Column(db.String(255), nullable=True)
    operator_id = db.Column(db.Integer, nullable=True)
    original_id = db.Column(db.Integer, nullable=True)  # 用于记录原始充值/提现ID，方便数据迁移后的参考
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<FundTransaction {self.transaction_id}: {self.transaction_type} {self.amount} ({self.status})>' 