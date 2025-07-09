#owner.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from OrderingFoodApp.models import *

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

@owner_bp.route('/')
@login_required
def index():
    owner = User.query.filter_by(id=current_user.id).first()
    return render_template('owner/index1.html', user=owner)