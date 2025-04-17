"""
Welcome page and core routes
Contains website root path routing and general redirects
"""
from flask import redirect, url_for, render_template

from . import main_bp

@main_bp.route('/')
def index():
    """Homepage"""
    return render_template('auth/login.html')

@main_bp.route('/about')
def about():
    """Team introduction page"""
    return render_template('about.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/logout')
def logout():
    """Redirect root path logout request to auth.logout"""
    return redirect(url_for('auth.logout')) 