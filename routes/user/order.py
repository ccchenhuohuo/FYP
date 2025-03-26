"""
用户订单相关路由
包含创建订单、取消订单等功能
"""
from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Order, AccountBalance
from utils.order_utils import process_new_order

from . import user_bp

@user_bp.route('/api/create_order', methods=['POST'])
@login_required
def create_order():
    """
    创建订单API
    处理用户买入或卖出股票的请求
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        
        # 提取必要参数
        ticker = data.get('ticker')
        order_quantity = data.get('order_quantity')
        order_type = data.get('order_type')
        order_execution_type = data.get('order_execution_type')
        order_price = data.get('order_price')
        
        # 处理订单请求
        response_data, status_code = process_new_order(
            current_user.user_id,
            ticker,
            order_type,
            order_execution_type,
            order_quantity,
            order_price
        )
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({'error': f'处理订单请求时发生错误: {str(e)}'}), 500

@user_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """
    取消订单API
    处理用户取消未执行订单的请求
    """
    try:
        # 查找订单
        order = Order.query.get_or_404(order_id)
        
        # 检查订单是否属于当前用户
        if order.user_id != current_user.user_id:
            return jsonify({'error': '您没有权限取消此订单'}), 403
        
        # 检查订单状态是否为待处理
        if order.order_status != 'pending':
            return jsonify({'error': f'无法取消已{order.order_status}的订单'}), 400
        
        # 如果是买入限价单，需要解冻资金
        if order.order_type == 'buy' and order.order_execution_type == 'limit':
            # 计算被冻结的金额
            frozen_amount = order.order_price * order.order_quantity
            
            # 获取用户账户
            account = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if account:
                # 将冻结的金额转回可用余额
                account.frozen_balance -= frozen_amount
                account.available_balance += frozen_amount
                # 总余额保持不变
                print(f"已解冻用户 {order.user_id} 资金: ¥{frozen_amount:.2f} (取消限价单)")
        
        # 更新订单状态
        order.order_status = 'cancelled'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'已取消订单 #{order_id}',
            'order': {
                'id': order.order_id,
                'ticker': order.ticker,
                'quantity': order.order_quantity,
                'order_type': order.order_type,
                'status': order.order_status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取消订单失败: {str(e)}'}), 500

@user_bp.route('/api/orders', methods=['GET'])
@login_required
def get_user_orders():
    """
    获取用户订单列表
    支持过滤和分页
    """
    try:
        # 获取查询参数
        status = request.args.get('status')
        order_type = request.args.get('order_type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # 构建查询
        query = Order.query.filter_by(user_id=current_user.user_id)
        
        # 应用过滤
        if status:
            query = query.filter_by(order_status=status)
        if order_type:
            query = query.filter_by(order_type=order_type)
        
        # 按创建时间倒序排序
        query = query.order_by(Order.created_at.desc())
        
        # 分页
        paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应
        orders_data = []
        for order in paginated_orders.items:
            orders_data.append({
                'order_id': order.order_id,
                'ticker': order.ticker,
                'order_type': order.order_type,
                'order_execution_type': order.order_execution_type,
                'order_price': order.order_price,
                'order_quantity': order.order_quantity,
                'order_status': order.order_status,
                'created_at': order.created_at.isoformat(),
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
        return jsonify({'error': f'获取订单列表失败: {str(e)}'}), 500 