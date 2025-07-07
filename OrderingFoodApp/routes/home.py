#home.py
from flask import Blueprint, render_template, redirect
from flask_login import current_user
from OrderingFoodApp.models import UserRole

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home_page():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin')
        elif current_user.role == UserRole.OWNER:
            return redirect('/owner')
        elif current_user.role == UserRole.CUSTOMER:
            return redirect('/customer')
    return render_template('home.html')


