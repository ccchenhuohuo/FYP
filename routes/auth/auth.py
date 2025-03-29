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
        
        print(f"接收到的登录信息 - 用户名: {user_name}")  # 调试信息，不打印密码
        
        if not user_name or not user_password:
            flash('请填写所有必填字段')
            return redirect(url_for('auth.login'))
        
        try:
            # 查询用户
            user = User.query.filter_by(user_name=user_name).first()
            print(f"查询到的用户: {user}")  # 调试信息
            
            if not user:
                print("用户不存在")  # 调试信息
                flash('用户名或密码错误')
                return redirect(url_for('auth.login'))
                
            # 验证密码
            if user.user_password == user_password:
                print("密码验证成功")  # 调试信息
                login_user(user)
                return redirect(url_for('user.account'))
            else:
                print("密码验证失败")  # 调试信息
                flash('用户名或密码错误')
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            print(f"登录过程发生错误: {str(e)}")  # 调试信息
            flash('登录失败，请稍后重试')
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
        # 打印整个表单数据以进行调试
        print("接收到的注册表单数据:", request.form)
        
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')
        user_password = request.form.get('user_password')
        confirm_password = request.form.get('confirm_password')
        
        print(f"用户名: {user_name}, 邮箱: {user_email}, 密码长度: {len(user_password) if user_password else 0}, 确认密码长度: {len(confirm_password) if confirm_password else 0}")
        
        if not user_name or not user_email or not user_password:
            print("缺少必填字段")
            flash('请填写所有必填字段')
            return redirect(url_for('auth.register'))
            
        if user_password != confirm_password:
            print("密码不匹配")
            flash('两次输入的密码不一致')
            return redirect(url_for('auth.register'))
        
        # 检查用户名或邮箱是否已存在
        existing_user = User.query.filter_by(user_email=user_email).first()
        
        if existing_user:
            print("邮箱已被注册")
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
            print("用户注册成功")
            flash('注册成功，请登录')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"注册失败: {str(e)}")
            flash('注册失败，请稍后重试')
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html')

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    # 导入日志记录器
    from models.admin import logger, AdminAccountLockedError
    
    # 如果用户已登录，重定向到管理员仪表板
    if current_user.is_authenticated:
        # 检查是否为管理员
        if hasattr(current_user, 'is_admin') and current_user.is_admin:
            logger.info(f"管理员 {current_user.admin_name} 已登录，重定向到管理员仪表板")
            return redirect(url_for('admin.admin_dashboard'))
    
    if request.method == 'POST':
        admin_name = request.form.get('username')
        admin_password = request.form.get('password')
        
        logger.info(f"接收到管理员登录请求 - 用户名: {admin_name}")
        
        if not admin_name or not admin_password:
            flash('请输入用户名和密码')
            logger.warning("管理员登录失败：用户名或密码为空")
            return render_template('auth/admin_login.html')
        
        try:
            # 查询管理员
            admin = Admin.query.filter_by(admin_name=admin_name).first()
            
            if not admin:
                flash('用户名或密码错误')
                logger.warning(f"管理员登录失败：用户名 {admin_name} 不存在")
                return render_template('auth/admin_login.html')
            
            try:
                # 检查账户是否被锁定
                admin.is_account_locked()
                
                if check_password_hash(admin.admin_password, admin_password):
                    # 登录成功，重置登录尝试次数
                    admin.reset_login_attempts()
                    db.session.commit()
                    login_user(admin)
                    logger.info(f"管理员 {admin_name} 登录成功")
                    return redirect(url_for('admin.admin_dashboard'))
                else:
                    # 登录失败，增加登录尝试次数
                    is_locked = admin.increment_login_attempts()
                    db.session.commit()
                    if is_locked:
                        flash('登录尝试次数过多，账户已被锁定')
                        logger.warning(f"管理员 {admin_name} 登录尝试次数过多，账户已被锁定")
                    else:
                        flash('用户名或密码错误')
                        logger.warning(f"管理员 {admin_name} 登录失败：密码错误")
                    return render_template('auth/admin_login.html')
            
            except AdminAccountLockedError as e:
                flash(f'账户已被锁定，请稍后再试')
                return render_template('auth/admin_login.html')
                
        except Exception as e:
            flash('登录过程中发生错误')
            logger.error(f"管理员登录过程中发生错误: {str(e)}")
            return render_template('auth/admin_login.html')
    
    return render_template('auth/admin_login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    用户登出路由
    登出当前用户并重定向到对应的登录页面
    """
    # 判断当前用户是否为管理员
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
    
    # 登出用户
    logout_user()
    
    # 根据用户类型重定向到不同的登录页面
    if is_admin:
        flash('您已成功登出管理员账户', 'success')
        return redirect(url_for('auth.admin_login'))
    else:
        flash('您已成功登出', 'success')
        return redirect(url_for('auth.login'))