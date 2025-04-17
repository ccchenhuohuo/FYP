"""
Financial related model definitions
Include account balance and fund transactions
"""
from . import db
from datetime import datetime
from sqlalchemy.orm import validates
from sqlalchemy import CheckConstraint, event

class AccountBalance(db.Model):
    """
    Account balance model
    Corresponds to the account_balance table in the database
    Manage user's fund status separately
    """
    __tablename__ = 'account_balance'
    
    balance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    available_balance = db.Column(db.Float, nullable=False, default=0.0)  # Available balance
    frozen_balance = db.Column(db.Float, nullable=False, default=0.0)     # Frozen balance
    total_balance = db.Column(db.Float, nullable=False, default=0.0)      # Total balance = available + frozen
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Add validation constraint: total balance must equal available balance plus frozen balance
    __table_args__ = (
        CheckConstraint('total_balance = available_balance + frozen_balance', name='check_balance_sum'),
    )
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<AccountBalance {self.user_id}: available={self.available_balance}, frozen={self.frozen_balance}>'
        
    def __round__(self, precision=0):
        """
        Implement the rounding method, so that the round filter in the template can work normally
        
        Parameters:
        precision (int): Number of decimal places to keep
        
        Returns:
        float: The rounded value
        """
        # Determine the value to round based on context
        # Default return the rounded value of total balance
        return round(self.total_balance, precision)

# Define event listener function
def before_account_balance_save(mapper, connection, target):
    """Automatically calculate total balance before saving (insert or update) AccountBalance object to database"""
    if target.available_balance is not None and target.frozen_balance is not None:
        # Perform necessary checks, e.g. balance cannot be negative
        if target.available_balance < 0:
             raise ValueError(f"Available balance ({target.available_balance}) cannot be negative")
        if target.frozen_balance < 0:
             raise ValueError(f"Frozen balance ({target.frozen_balance}) cannot be negative")
             
        # Calculate total balance
        target.total_balance = target.available_balance + target.frozen_balance
        print(f"Event triggered: update user {target.user_id} total balance to {target.total_balance}") # Add log/print
    else:
        # Handle the case where the initial creation may not have default values (even though the model has default=0.0)
        if target.available_balance is None: target.available_balance = 0.0
        if target.frozen_balance is None: target.frozen_balance = 0.0
        target.total_balance = target.available_balance + target.frozen_balance
        print(f"Event triggered (initialization): update user {target.user_id} total balance to {target.total_balance}") # Add log/print

# Register event listener
# Trigger before insert
event.listen(AccountBalance, 'before_insert', before_account_balance_save)
# Trigger before update
event.listen(AccountBalance, 'before_update', before_account_balance_save)

class FundTransaction(db.Model):
    """
    Fund transaction model
    Corresponds to the fund_transaction table in the database
    Manage fund operations such as deposit and withdrawal
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
    original_id = db.Column(db.Integer, nullable=True)  # Used to record the original deposit/withdrawal ID, for reference after data migration
    
    # Add validation constraint: amount must be greater than 0
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_positive_amount'),
    )
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate that the transaction amount must be greater than 0"""
        if value <= 0:
            raise ValueError(f"Transaction amount must be greater than 0, current value: {value}")
        return value
    
    @validates('transaction_type')
    def validate_transaction_type(self, key, value):
        """Validate that the transaction type must be a valid value"""
        valid_types = ['deposit', 'withdrawal']
        if value not in valid_types:
            raise ValueError(f"Invalid transaction type: {value}, valid types: {', '.join(valid_types)}")
        return value
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<FundTransaction {self.transaction_id}: {self.transaction_type} {self.amount} ({self.status})>'