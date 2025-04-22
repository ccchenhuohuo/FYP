"""
认证相关路由
包含登录、注册、管理员登录等功能
"""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

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
        
        print(f"Received login information - Username: {user_name}")  # Debug info, do not print password
        
        if not user_name or not user_password:
            flash('Please fill in all required fields')
            return redirect(url_for('auth.login'))
        
        try:
            # Query user
            user = User.query.filter_by(user_name=user_name).first()
            print(f"Query user: {user}")  # Debug info
            
            if not user:
                print("User does not exist") # Debug info
                flash('Invalid username or password', 'error')
                return redirect(url_for('auth.login'))
                
            # Verify password
            if user.user_password == user_password:
                print("Password verification successful") # Debug info
                # 更新最后登录时间
                user.last_login_at = datetime.now()
                db.session.commit()
                login_user(user)
                return redirect(url_for('user.account'))
            else:
                print("Password verification failed") # Debug info
                flash('Invalid username or password', 'error')
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            print(f"Error during login process: {str(e)}") # Debug info
            flash('An error occurred during the login process.', 'error')
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
        # Print entire form data for debugging
        print("Received registration form data:", request.form)
        
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')
        user_password = request.form.get('user_password')
        confirm_password = request.form.get('confirm_password')
        
        print(f"Username: {user_name}, Email: {user_email}, Password length: {len(user_password) if user_password else 0}, Confirm password length: {len(confirm_password) if confirm_password else 0}")
        
        if not user_name or not user_email or not user_password:
            print("Missing required fields")
            flash('Please fill in all required fields')
            return redirect(url_for('auth.register'))
            
        if user_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.register'))
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.user_name == user_name) | (User.user_email == user_email)).first()
        
        if existing_user:
            if existing_user.user_name == user_name:
                flash('Username already exists.', 'error')
            if existing_user.user_email == user_email:
                flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))
        
        # Create new user - directly store plaintext password
        new_user = User(
            user_name=user_name,
            user_email=user_email,
            user_password=user_password  # Directly store plaintext password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            print("User registration successful") # Debug info
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'error')
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html')

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    # Import logger and AdminAccountLockedError
    from models.admin import logger, AdminAccountLockedError
    
    # If user is already logged in, redirect to admin dashboard
    if current_user.is_authenticated:
        # Check if user is admin
        if hasattr(current_user, 'is_admin') and current_user.is_admin:
            logger.info(f"Admin {current_user.admin_name} logged in, redirecting to admin dashboard")
            return redirect(url_for('admin.admin_dashboard'))
    
    if request.method == 'POST':
        admin_name = request.form.get('username')
        admin_password = request.form.get('password')
        
        logger.info(f"Received admin login request - Username: {admin_name}")
        
        if not admin_name or not admin_password:
            flash('Please enter username and password')
            logger.warning("Admin login failed: Username or password is empty")
            return render_template('auth/admin_login.html')
        
        try:
            # Query admin
            admin = Admin.query.filter_by(admin_name=admin_name).first()
            
            if not admin:
                flash('Invalid username or password', 'error')
                logger.warning(f"Admin login failed: Username {admin_name} does not exist")
                return render_template('auth/admin_login.html')
            
            try:
                # Check if account is locked
                admin.is_account_locked()
                
                if check_password_hash(admin.admin_password, admin_password):
                    # Login successful, reset login attempts
                    admin.reset_login_attempts()
                    db.session.commit()
                    login_user(admin)
                    logger.info(f"Admin {admin_name} logged in successfully")
                    return redirect(url_for('admin.admin_dashboard'))
                else:
                    # Login failed, increment login attempts
                    is_locked = admin.increment_login_attempts()
                    db.session.commit()
                    if is_locked:
                        flash('Too many login attempts. Account locked until {admin.lockout_until.strftime("%Y-%m-%d %H:%M:%S UTC")}.', 'error')
                        logger.warning(f"Admin {admin_name} account locked due to too many failed login attempts.")
                    else:
                        flash('Invalid username or password', 'error')
                        logger.warning(f"Admin {admin_name} login failed: Incorrect password.")
                    return render_template('auth/admin_login.html')
            
            except AdminAccountLockedError as e:
                flash(f'Account is locked. Please try again later. Lock duration: {admin.lockout_until - datetime.utcnow()}.', 'error')
                return render_template('auth/admin_login.html')
                
        except Exception as e:
            flash('An error occurred during login.', 'error')
            logger.error(f"Error during admin login process: {str(e)}")
            return render_template('auth/admin_login.html')
    
    # For GET request, render the login page
    # Check if the admin is already locked out when rendering the page initially
    admin_for_get = Admin.query.filter_by(admin_name=request.form.get('username')).first() # Check if username exists
    locked_until_get = None
    if admin_for_get and admin_for_get.lockout_until and admin_for_get.lockout_until > datetime.utcnow():
        locked_until_get = admin_for_get.lockout_until
        flash(f'Account is locked. Please try again later.', 'error') # Re-display lock message on GET if still locked

    return render_template('auth/admin_login.html', locked_until=locked_until_get)

@auth_bp.route('/admin/logout')
@login_required # Ensure only logged-in admins can logout
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have successfully logged out as admin.', 'success')
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """
    用户登出路由
    登出当前用户并重定向到对应的登录页面
    """
    # Check if current user is admin
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
    
    # Logout user
    logout_user()
    
    # Redirect based on user type
    if is_admin:
        flash('You have successfully logged out as admin.', 'success')
        return redirect(url_for('auth.admin_login'))
    else:
        flash('You have successfully logged out.', 'success')
        return redirect(url_for('auth.login'))