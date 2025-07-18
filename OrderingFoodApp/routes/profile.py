from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from OrderingFoodApp import db
from OrderingFoodApp.models import Address, Gender
from datetime import datetime

profile_bp = Blueprint('profile', __name__, url_prefix='')

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # 1. Lấy dữ liệu
        name         = request.form.get('name', '').strip()
        email        = request.form.get('email', '').strip()
        dob_str      = request.form.get('dob', '').strip()
        gender_value = request.form.get('gender', '').strip()
        phone        = request.form.get('phone', '').strip()

        # 2. Validate cơ bản
        if not name or not email:
            flash('Tên và email là bắt buộc.', 'danger')
            return redirect(url_for('profile.profile'))

        # 3. Gán vào current_user
        current_user.name  = name
        current_user.email = email

        # 4. Xử lý ngày sinh
        if dob_str:
            try:
                current_user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d')
            except ValueError:
                flash('Định dạng Ngày sinh không hợp lệ.', 'danger')
                return redirect(url_for('profile.profile'))
        else:
            current_user.date_of_birth = None

        # 5. Xử lý giới tính (Enum)
        if gender_value in [g.value for g in Gender]:
            current_user.gender = Gender(gender_value)
        else:
            current_user.gender = None

        # 6. Số điện thoại
        current_user.phone = phone or None

        # 7. Lưu vào DB
        try:
            db.session.commit()
            flash('Cập nhật thông tin cá nhân thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Lỗi khi lưu thông tin: ' + str(e), 'danger')

        return redirect(url_for('profile.profile'))

    # Với GET, chỉ render form
    return render_template('profile.html', user=current_user)

# ───────────────────────────────────────────
# Thêm địa chỉ
@profile_bp.route('/address/add', methods=['POST'])
@login_required
def add_address():
    line = request.form.get('address_line','').strip()
    is_def = request.form.get('is_default') == '1'
    if not line:
        flash('Địa chỉ không được để trống.', 'danger')
    else:
        if is_def:
            # bỏ default cũ
            for a in current_user.addresses:
                a.is_default = False
        addr = Address(user_id=current_user.id, address_line=line, is_default=is_def)
        db.session.add(addr)
        db.session.commit()
        flash('Thêm địa chỉ thành công!', 'success')
    return redirect(url_for('profile.profile'))

# Sửa địa chỉ
@profile_bp.route('/address/edit', methods=['POST'])
@login_required
def edit_address():
    addr = Address.query.get(request.form.get('address_id'))
    if not addr or addr.user_id!=current_user.id:
        flash('Địa chỉ không tồn tại.', 'danger')
        return redirect(url_for('profile.profile'))

    line = request.form.get('address_line','').strip()
    is_def = request.form.get('is_default') == '1'
    if not line:
        flash('Địa chỉ không được để trống.', 'danger')
    else:
        if is_def:
            for a in current_user.addresses:
                a.is_default = False
        addr.address_line = line
        addr.is_default = is_def
        db.session.commit()
        flash('Cập nhật địa chỉ thành công!', 'success')
    return redirect(url_for('profile.profile'))

# Xóa địa chỉ
@profile_bp.route('/address/delete/<int:id>', methods=['POST'])
@login_required
def delete_address(id):
    addr = Address.query.get(id)
    if addr and addr.user_id==current_user.id:
        db.session.delete(addr)
        db.session.commit()
        flash('Xóa địa chỉ thành công!', 'success')
    else:
        flash('Không thể xóa địa chỉ.', 'danger')
    return redirect(url_for('profile.profile'))
