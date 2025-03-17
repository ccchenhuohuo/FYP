"""
认证相关路由
包含登录、注册、管理员登录等功能
"""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp
from models import db, User, Admin

@auth_bp.route('/')
def index():
    """
    首页路由
    已登录用户重定向到股票历史走势页面，未登录用户重定向到登录页面
    """
    if current_user.is_authenticated:
        return redirect(url_for('user.stock_chart'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录路由
    处理登录表单提交和页面渲染
    """
    if current_user.is_authenticated:
        return redirect(url_for('user.stock_chart'))
        
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        user_password = request.form.get('user_password')
        
        print(f"接收到的登录信息 - 用户名: {user_name}, 密码: {user_password}")  # 调试信息
        
        if not user_name or not user_password:
            flash('请填写所有必填字段')
            return redirect(url_for('auth.login'))
        
        # 查询用户
        user = User.query.filter_by(user_name=user_name).first()
        print(f"查询到的用户: {user}")  # 调试信息
        
        if user:
            print(f"数据库中的密码: {user.user_password}")  # 调试信息
            
        # 直接比较明文密码
        if user and user.user_password == user_password:
            print("密码验证成功")  # 调试信息
            login_user(user)
            return redirect(url_for('user.account'))
        else:
            print("密码验证失败")  # 调试信息
            flash('用户名或密码错误')
            return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册路由
    处理注册表单提交和页面渲染
    """
    if current_user.is_authenticated:
        return redirect(url_for('user.stock_chart'))
        
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')
        user_password = request.form.get('user_password')
        
        if not user_name or not user_email or not user_password:
            flash('请填写所有必填字段')
            return redirect(url_for('auth.register'))
        
        # 检查用户名或邮箱是否已存在
        existing_user = User.query.filter_by(user_email=user_email).first()
        
        if existing_user:
            flash('该邮箱已被注册')
            return redirect(url_for('auth.register'))
        
        # 创建新用户 - 直接存储明文密码
        new_user = User(
            user_name=user_name,
            user_email=user_email,
            user_password=user_password  # 直接存储明文密码
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请稍后重试')
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html')

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """
    管理员登录路由
    处理管理员登录表单提交和页面渲染
    """
    if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
        
    if request.method == 'POST':
        admin_name = request.form.get('username')
        admin_password = request.form.get('password')
        
        if not admin_name or not admin_password:
            flash('请填写所有必填字段')
            return render_template('auth/admin_login.html')
        
        # 验证管理员
        admin = Admin.query.filter_by(admin_name=admin_name).first()
        
        # 直接比较明文密码
        if admin and admin.admin_password == admin_password:
            login_user(admin)
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('用户名或密码错误，请重试', 'danger')
            return render_template('auth/admin_login.html')
        
    return render_template('auth/admin_login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    用户登出路由
    登出当前用户并重定向到登录页面
    """
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login')) 