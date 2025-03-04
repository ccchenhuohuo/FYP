"""
管理员相关路由
包含管理员仪表盘和页面2-4的路由
"""
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from . import admin_bp
from models import User, Admin

def admin_required(func):
    """
    管理员权限检查装饰器
    确保只有管理员可以访问被装饰的路由
    """
    @login_required
    def decorated_view(*args, **kwargs):
        if not isinstance(current_user, Admin):
            return redirect(url_for('user.stock_chart'))
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view

@admin_bp.route('/')
@admin_required
def dashboard():
    """
    管理员仪表盘路由
    显示用户列表等管理功能
    需要管理员权限
    """
    # 获取所有用户列表
    users = User.query.all()
    return render_template('admin/page1.html', users=users)

@admin_bp.route('/page2')
@admin_required
def page2():
    """
    管理员页面2路由
    需要管理员权限
    """
    return render_template('admin/page2.html')

@admin_bp.route('/page3')
@admin_required
def page3():
    """
    管理员页面3路由
    需要管理员权限
    """
    return render_template('admin/page3.html')

@admin_bp.route('/page4')
@admin_required
def page4():
    """
    管理员页面4路由
    需要管理员权限
    """
    return render_template('admin/page4.html') 