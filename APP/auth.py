from flask import Blueprint, render_template, url_for, redirect, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, login_required, logout_user
from . import db
from .models import User

auth = Blueprint('auth', __name__)

@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        print("🧾 SIGN UP ROUTE WAS TRIGGERED")

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered. Please log in.', category='error')
            return redirect(url_for('auth.login'))

        if password != confirm_password:
            flash('Passwords do not match.', category='error')
            return redirect(url_for('auth.sign_up'))

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', category='error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', category='error')
        elif len(email) < 4:
            flash('Email must be valid.', category='error')
        else:
            hashed_password = generate_password_hash(password, method='scrypt')
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! Please log in.', category='success')
            return redirect(url_for('auth.login'))

    return render_template('sign_up.html', user=current_user)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("🔐 LOGIN ROUTE WAS TRIGGERED")

        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if user.password is None:
                flash('User password not set. Please reset your password or sign up again.', category='error')
                return redirect(url_for('auth.login'))

            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Logged in successfully', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('Email does not exist. You can sign up!', category='error')
            return redirect(url_for('auth.sign_up')) # Redirect to signup if email doesn't exist

    return render_template("login.html", user=current_user)

@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('password')

        user_to_reset = User.query.filter_by(email=email).first()

        if user_to_reset:
            # Check if the new password (when hashed) matches any existing user's password
            hashed_new_password = generate_password_hash(new_password, method='scrypt')
            existing_user_with_same_password = User.query.filter(User.password == hashed_new_password).first()

            if existing_user_with_same_password:
                flash('This new password is already in use by another user. Please choose a different one.', category='error')
                return render_template('reset_password.html', user=current_user)
            elif user_to_reset.password and check_password_hash(user_to_reset.password, new_password):
                flash('New password cannot be the same as your old password.', category='error')
                return render_template('reset_password.html', user=current_user)
            else:
                user_to_reset.password = hashed_new_password
                db.session.commit()
                flash('Password has been reset successfully!', category='success')
                
        else:
            flash('Email not found. Please enter your registered email.', category='error')
            return render_template('reset_password.html', user=current_user)

    return render_template('reset_password.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))