"""
欢迎界面和核心路由
包含网站根路径路由和通用重定向
"""
from flask import redirect, url_for, render_template

from . import main_bp

@main_bp.route('/')
def index():
    """首页"""
    return render_template('auth/login.html')

@main_bp.route('/about')
def about():
    """团队介绍页面"""
    return render_template('about.html')

@main_bp.route('/privacy')
def privacy():
    """隐私政策页面"""
    return render_template('privacy.html')

@main_bp.route('/logout')
def logout():
    """将根路径的登出请求重定向到auth.logout"""
    return redirect(url_for('auth.logout')) 