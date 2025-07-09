#admin.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from OrderingFoodApp.models import *

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def index():
    admin = User.query.filter_by(id=current_user.id).first()
    return render_template('admin/index1.html', user=admin)
