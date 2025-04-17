"""
User account related routes
Includes account management, fund deposit/withdrawal, and order management features
"""
from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Order, Transaction, User, Portfolio, AccountBalance, FundTransaction
from decimal import Decimal
import json
from utils.number_utils import RoundableDict
from utils.datetime_utils import safe_date_format

from . import user_bp

@user_bp.route('/account')
@login_required
def account():
    """
    User account page
    Displays account balance, portfolio, and transaction history
    """
    # Get user account information
    account_balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
    
    # If the user does not have an account balance record, create one
    if not account_balance:
        account_balance = AccountBalance(
            user_id=current_user.user_id,
            available_balance=0.0,
            frozen_balance=0.0,
            total_balance=0.0
        )
        db.session.add(account_balance)
        db.session.commit()
    
    # Get user portfolio
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.user_id).all()
    
    # Calculate total portfolio value
    portfolio_value = 0
    portfolio_data = []
    
    # Process portfolio data
    for item in portfolio_items:
        # Add market price and current value
        # Assume current_price is fetched elsewhere or default to average_price
        market_price = item.current_price if hasattr(item, 'current_price') else item.average_price 
        current_value = market_price * item.quantity
        portfolio_value += current_value
        
        # Calculate profit/loss and percentage
        profit_loss = (market_price - item.average_price) * item.quantity
        pnl_percentage = 0
        if item.average_price > 0:
            pnl_percentage = (market_price - item.average_price) / item.average_price * 100
        
        # Build template data
        portfolio_data.append({
            'ticker': item.ticker,
            'quantity': item.quantity,
            'average_price': item.average_price,
            'current_price': market_price,
            'current_value': current_value,
            'market_value': current_value,  # Add market value field
            'profit_loss': profit_loss,
            'pnl': profit_loss,  # Add pnl field
            'pnl_percentage': pnl_percentage  # Add P&L percentage
        })
    
    # Get user's transaction history (limit 10)
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.transaction_time.desc()).limit(10).all()
    
    # Get user's order history (limit 10)
    orders = Order.query.filter_by(user_id=current_user.user_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # Format order data to match template expectations
    order_data = []
    for order in orders:
        # Debugging info
        print(f"Order ID: {order.order_id}, Status: {order.order_status}, Price: {order.order_price}")
        order_data.append({
            'order_id': order.order_id,  # Keep original field name
            'id': order.order_id,        # Add id field for the template
            'ticker': order.ticker,
            'order_type': order.order_type,
            'type': order.order_type,    # Add type field for the template 
            'order_execution_type': order.order_execution_type,
            'execution_type': order.order_execution_type, # Add execution_type field for the template
            'order_price': order.order_price,
            'price': order.order_price,  # Add price field for the template
            'order_quantity': order.order_quantity,
            'quantity': order.order_quantity,  # Add quantity field for the template
            'order_status': order.order_status,
            'status': order.order_status,  # Add status field for the template
            'created_at': safe_date_format(order.created_at),
            'updated_at': safe_date_format(order.updated_at),
            'executed_at': safe_date_format(order.executed_at)
        })
    
    # Get user fund transaction history (limit 5)
    fund_transactions = FundTransaction.query.filter_by(user_id=current_user.user_id).order_by(FundTransaction.created_at.desc()).limit(5).all()
    
    # Process fund transaction records, ensuring correct field names
    fund_tx_data = []
    for fund_tx in fund_transactions:
        fund_tx_data.append({
            'transaction_id': fund_tx.transaction_id,
            'user_id': fund_tx.user_id,
            'transaction_type': fund_tx.transaction_type,
            'amount': fund_tx.amount,
            'status': fund_tx.status,
            'created_at': safe_date_format(fund_tx.created_at),
            'updated_at': safe_date_format(fund_tx.updated_at),
            'remark': fund_tx.remark
        })
    
    # Process transaction records, ensuring correct field names
    transaction_data = []
    for tx in transactions:
        transaction_data.append({
            'transaction_id': tx.transaction_id,
            'order_id': tx.order_id,
            'user_id': tx.user_id,
            'ticker': tx.ticker,
            'transaction_type': tx.transaction_type,
            'transaction_price': tx.transaction_price,
            'transaction_quantity': tx.transaction_quantity,
            'transaction_amount': tx.transaction_amount,
            'transaction_time': safe_date_format(tx.transaction_time),
            'transaction_status': tx.transaction_status
        })
    
    # Render account page
    return render_template(
        'user/account.html',
        user=current_user,
        balance=account_balance,
        portfolio=portfolio_data,
        portfolio_value=portfolio_value,
        transactions=transaction_data,
        orders=order_data,
        fund_transactions=fund_tx_data
    )

@user_bp.route('/api/deposit', methods=['POST'])
@login_required
def deposit():
    """
    Fund Deposit API
    Handles user deposit requests
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'error': 'Missing amount parameter'}), 400
    
    try:
        # Validate amount
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Deposit amount must be greater than 0'}), 400
        
        # Create deposit transaction record
        fund_transaction = FundTransaction(
            user_id=current_user.user_id,
            amount=amount,
            transaction_type='deposit',
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(fund_transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Deposit request submitted, pending administrator approval',
            'transaction_id': fund_transaction.transaction_id
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Deposit request failed: {str(e)}'}), 500

@user_bp.route('/api/withdraw', methods=['POST'])
@login_required
def withdraw():
    """
    Fund Withdrawal API
    Handles user withdrawal requests
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'error': 'Missing amount parameter'}), 400
    
    try:
        # Validate amount
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Withdrawal amount must be greater than 0'}), 400
        
        # Check user account balance
        account = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
        
        if not account:
            return jsonify({'error': 'Account information not found'}), 404
        
        # Validate if balance is sufficient
        if account.available_balance < amount:
            return jsonify({'error': 'Insufficient account balance'}), 400
        
        # Create withdrawal transaction record
        fund_transaction = FundTransaction(
            user_id=current_user.user_id,
            amount=amount,
            transaction_type='withdrawal',
            status='pending',
            created_at=datetime.utcnow()
        )
        
        # Transfer amount from available balance to frozen balance
        account.available_balance -= amount
        account.frozen_balance += amount
        # Total balance remains unchanged as it's just a transfer between balances
        
        db.session.add(fund_transaction)
        db.session.add(account)
        db.session.commit()
        
        return jsonify({
            'message': 'Withdrawal request submitted, pending administrator approval',
            'transaction_id': fund_transaction.transaction_id
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Withdrawal request failed: {str(e)}'}), 500 