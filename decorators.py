from functools import wraps
from flask import flash, redirect, url_for, get_flashed_messages
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            # Clear any existing flashed messages
            _ = get_flashed_messages()
            # Then add our admin required message
            flash('You need admin privileges to access this area.', 'danger')
            # Redirect to login page
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function