#customer.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from OrderingFoodApp.models import *

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/')
@login_required
def index():
    customer = User.query.filter_by(id=current_user.id).first()
    return render_template('customer/index1.html', user=customer)

