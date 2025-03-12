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
    GET: 显示登录页面
    POST: 处理登录表单提交
    """
    # 如果用户已登录，直接跳转到股票历史走势页面
    if current_user.is_authenticated:
        return redirect(url_for('user.stock_chart'))
    
    # 处理POST请求（表单提交）
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 查询用户并验证密码
        user = User.query.filter_by(user_name=username).first()
        
        if user and check_password_hash(user.user_password, password):
            # 登录成功
            login_user(user)
            # 获取next参数，如果有的话
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('user.stock_chart'))
        else:
            # 登录失败
            flash('登录失败，请检查用户名和密码')
    
    # GET请求或登录失败，显示登录页面
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册路由
    GET: 显示注册页面
    POST: 处理注册表单提交
    """
    # 如果用户已登录，直接跳转到股票历史走势页面
    if current_user.is_authenticated:
        return redirect(url_for('user.stock_chart'))
    
    # 处理POST请求（表单提交）
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户名是否已存在
        user_exists = User.query.filter_by(user_name=username).first()
        if user_exists:
            flash('用户名已存在')
            return redirect(url_for('auth.register'))
        
        # 检查邮箱是否已被注册
        email_exists = User.query.filter_by(user_email=email).first()
        if email_exists:
            flash('邮箱已被注册')
            return redirect(url_for('auth.register'))
        
        # 创建新用户
        new_user = User(
            user_name=username,
            user_email=email,
            user_password=generate_password_hash(password)
        )
        
        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    # GET请求，显示注册页面
    return render_template('auth/register.html')

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """
    管理员登录路由
    GET: 显示管理员登录页面
    POST: 处理管理员登录表单提交
    """
    # 如果用户已登录，根据用户类型重定向
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            return redirect(url_for('admin.admin_dashboard'))
        else:
            return redirect(url_for('user.stock_chart'))
    
    # 处理POST请求（表单提交）
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 查询管理员并验证密码
        admin = Admin.query.filter_by(admin_name=username).first()
        
        if admin and check_password_hash(admin.admin_password, password):
            # 登录成功
            login_user(admin)
            return redirect(url_for('admin.admin_dashboard'))
        else:
            # 登录失败
            flash('管理员登录失败，请检查用户名和密码')
    
    # GET请求或登录失败，显示管理员登录页面
    return render_template('auth/admin_login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    登出路由
    结束用户会话并重定向到登录页面
    需要登录才能访问
    """
    logout_user()
    return redirect(url_for('auth.login')) 