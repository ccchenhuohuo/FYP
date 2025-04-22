"""
Admin routes module
Contains routes related to admin functions
"""
from flask import Blueprint

# Create the admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin') 