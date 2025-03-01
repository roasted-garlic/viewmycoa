from flask import render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this area.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    # Only add login message if we have a 'next' parameter and user is not authenticated
    if request.args.get('next') and not current_user.is_authenticated:
        # Check if we already have this message
        messages = get_flashed_messages(with_categories=True, category_filter=['info'])
        has_login_message = any('Please log in' in message for category, message in messages)
        if not has_login_message:
            flash('Please log in to access this page.', 'info')

    error = None    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            app.logger.info(f"Login attempt for username: {username}")
            user = User.query.filter_by(username=username).first()

            if not user:
                app.logger.warning(f"Login failed: User {username} not found")
                error = "Invalid username or password"
            elif not user.check_password(password):
                app.logger.warning(f"Login failed: Incorrect password for {username}")
                error = "Invalid username or password"
            else:
                app.logger.info(f"Login successful for {username}")
                login_user(user)
                
                # Clear any "Please log in" messages after successful login
                messages = get_flashed_messages(with_categories=True)
                for category, message in messages:
                    if 'Please log in' not in message:
                        flash(message, category)
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('admin_dashboard'))
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}", exc_info=True)
            error = "An error occurred during login. Please try again."

    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/vmc-admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route('/vmc-admin/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('user_create.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('user_create.html')

        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('User created successfully', 'success')
        return redirect(url_for('manage_users'))

    return render_template('user_create.html')

@app.route('/vmc-admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        is_admin = 'is_admin' in request.form
        new_password = request.form.get('password')

        # Check if username is being changed and is already taken
        if user.username != username and User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('user_edit.html', user=user)

        # Check if email is being changed and is already taken
        if user.email != email and User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('user_edit.html', user=user)

        user.username = username
        user.email = email
        user.is_admin = is_admin

        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('manage_users'))

    return render_template('user_edit.html', user=user)

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot delete your own account'}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True})