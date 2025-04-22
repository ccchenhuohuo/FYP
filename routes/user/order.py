"""
User order related routes
Includes creating orders, canceling orders, etc.
"""
from flask import jsonify, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Order, AccountBalance
from utils.order_utils import process_new_order, simplified_process_order
from models.enums import OrderStatus, OrderType, OrderExecutionType
from decimal import Decimal

from . import user_bp

@user_bp.route('/api/create_order', methods=['POST'])
@login_required
def create_order():
    """
    Create Order API
    Handles user requests to buy or sell stocks
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        # Extract necessary parameters
        ticker = data.get('ticker')
        order_quantity = data.get('order_quantity')
        order_type = data.get('order_type')
        order_execution_type = data.get('order_execution_type')
        order_price = data.get('order_price')
        
        # Use the simplified order processing function
        result = simplified_process_order(
            current_user.user_id,
            ticker,
            order_type,
            order_execution_type,
            order_quantity,
            order_price
        )
        
        # Return different HTTP status codes based on order status
        if result.get('status') == 'valid': # Check if 'status' key exists
            order_status_value = result.get('order_status') # Check if 'order_status' key exists
            if order_status_value == OrderStatus.EXECUTED.value:
                # Executed order
                return jsonify(result), 200
            else:
                # Valid but pending order
                return jsonify(result), 201
        else:
            # Invalid order (e.g., insufficient funds, validation fail)
            # Return 200 OK because the request was processed, but the business logic failed
            return jsonify(result), 200 
        
    except Exception as e:
        # Log the exception for debugging
        current_app.logger.error(f'Error processing create_order request: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error processing order request: {str(e)}'}), 500

@user_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """
    Cancel Order API
    Handles user requests to cancel pending orders
    """
    try:
        # Find the order
        order = Order.query.get_or_404(order_id)
        
        # Check if the order belongs to the current user
        if order.user_id != current_user.user_id:
            return jsonify({'error': 'You do not have permission to cancel this order'}), 403
        
        # Check if the order status is pending
        if order.order_status != OrderStatus.PENDING:
            return jsonify({'error': f'Cannot cancel an order with status {order.order_status}'}), 400
        
        # If it's a buy limit order, unfreeze the funds
        if order.order_type == OrderType.BUY and order.order_execution_type == OrderExecutionType.LIMIT:
            # Calculate the frozen amount - 确保数据类型一致
            order_price = float(order.order_price) if order.order_price else 0.0
            order_quantity = float(order.order_quantity) if order.order_quantity else 0.0
            frozen_amount = order_price * order_quantity
            
            # Get user account
            account = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if account:
                # 确保使用浮点数计算
                account.frozen_balance = float(account.frozen_balance) - frozen_amount
                account.available_balance = float(account.available_balance) + frozen_amount
                # Total balance remains unchanged
                print(f"Unfrozen funds for user {order.user_id}: ¥{frozen_amount:.2f} (Limit order cancelled)")
        
        # Update order status
        order.order_status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Check if it's an AJAX request
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'message': f'Order #{order_id} has been cancelled',
                'order': {
                    'id': order.order_id,
                    'ticker': order.ticker,
                    'quantity': order.order_quantity,
                    'order_type': str(order.order_type),
                    'status': str(order.order_status)
                }
            })
        else:
            # For regular form submission, redirect back to account page
            flash(f'Order #{order_id} has been cancelled successfully', 'success')
            return redirect(url_for('user.account'))
        
    except Exception as e:
        db.session.rollback()
        # Log the exception
        current_app.logger.error(f'Error cancelling order {order_id}: {str(e)}', exc_info=True)
        
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({'error': f'Failed to cancel order: {str(e)}'}), 500
        else:
            flash(f'Failed to cancel order: {str(e)}', 'error')
            return redirect(url_for('user.account'))

@user_bp.route('/api/orders', methods=['GET'])
@login_required
def get_user_orders():
    """
    Get user order list
    Supports filtering and pagination
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        order_type = request.args.get('order_type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Build query
        query = Order.query.filter_by(user_id=current_user.user_id)
        
        # Apply filters
        if status:
            query = query.filter(Order.order_status == status) # Compare with string value
        if order_type:
            query = query.filter(Order.order_type == order_type) # Compare with string value
        
        # Sort by creation time descending
        query = query.order_by(Order.created_at.desc())
        
        # Paginate
        paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format response
        orders_data = []
        for order in paginated_orders.items:
            orders_data.append({
                'order_id': order.order_id,
                'ticker': order.ticker,
                'order_type': str(order.order_type), # Return string representation
                'order_execution_type': str(order.order_execution_type), # Return string representation
                'order_price': order.order_price,
                'order_quantity': order.order_quantity,
                'order_status': str(order.order_status), # Return string representation
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'executed_at': order.executed_at.isoformat() if order.executed_at else None
            })
        
        return jsonify({
            'orders': orders_data,
            'total': paginated_orders.total,
            'pages': paginated_orders.pages,
            'current_page': page
        })
        
    except Exception as e:
        # Log the exception
        current_app.logger.error(f'Error fetching user orders: {str(e)}', exc_info=True)
        return jsonify({'error': f'Failed to get order list: {str(e)}'}), 500 