#auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from OrderingFoodApp.models import db, User, UserRole

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

# Đăng ký tài khoản
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # Expecting 'CUSTOMER', 'OWNER', 'ADMIN'

        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký!', 'danger')
            return redirect(url_for('auth.register'))

        hashed_pw = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_pw, role=UserRole[role])
        db.session.add(user)
        db.session.commit()
        flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# Đăng nhập
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            next_page = request.args.get('next')

            if user.role == UserRole.CUSTOMER:
                return redirect(next_page or url_for('customer.index'))
            elif user.role == UserRole.OWNER:
                return redirect(next_page or url_for('owner.index'))
            elif user.role == UserRole.ADMIN:
                return redirect(next_page or url_for('admin.index'))
        else:
            flash('Email hoặc mật khẩu không đúng.', 'danger')

    return render_template('auth/login.html')

# Đăng xuất
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.home_page'))
