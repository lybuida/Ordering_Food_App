#admin.py
from functools import wraps

from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_admin import Admin

from OrderingFoodApp.dao.restaurant_dao import *
from OrderingFoodApp.models import *
from OrderingFoodApp.dao import user_dao, restaurant_dao, order_owner

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def index():
    admin = User.query.filter_by(id=current_user.id).first()
    return render_template('admin/index.html', user=admin)

def admin_required(f):
    """
    Decorator tùy chỉnh để yêu cầu quyền ADMIN.
    Đảm bảo người dùng đã đăng nhập và có vai trò ADMIN.
    """
    @wraps(f)
    @login_required # Đảm bảo người dùng đã đăng nhập trước
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin: # Kiểm tra thuộc tính is_admin của User model
            flash('Bạn không có quyền truy cập vào trang này.', 'danger')
            # Chuyển hướng về trang chủ hoặc trang lỗi
            return redirect(url_for('home')) # Hoặc url_for('auth_bp.login') nếu muốn đăng nhập lại
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================
# ROUTES QUẢN LÝ NGƯỜI DÙNG (USER MANAGEMENT)
# ==========================================================

@admin_bp.route('/users')
@admin_required
def users_management():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)

    users_pagination = user_dao.get_all_users(page=page, page_size=10, query=search_query)

    return render_template(
        'admin/users/list.html',
        users_pagination=users_pagination,
        current_search=search_query
    )


@admin_bp.route('/users/add', methods=['GET', 'POST'])  # GET để hiển thị form, POST để xử lý
@admin_required
def add_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role_str = request.form.get('role')

        if not all([name, email, password, role_str]):
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return render_template('admin/users/add.html', UserRole=UserRole)  # Render lại form với dữ liệu đã nhập

        try:
            role = UserRole(role_str.lower())
        except ValueError:
            flash('Vai trò không hợp lệ.', 'danger')
            return render_template('admin/users/add.html', UserRole=UserRole)

        existing_user = user_dao.get_user_by_email(email)
        if existing_user:
            flash('Email đã tồn tại.', 'danger')
            return render_template('admin/users/add.html', UserRole=UserRole)

        new_user = user_dao.add_user(name, email, password, role)
        if new_user:
            flash(f'Người dùng "{new_user.name}" đã được thêm thành công.', 'success')
            return redirect(url_for('admin.users_management'))
        else:
            print("‼️ Không thêm được user:", name, email, role)
            flash('Có lỗi xảy ra khi thêm người dùng.', 'danger')
            return render_template('admin/users/add.html', UserRole=UserRole)

    # GET request: Hiển thị form thêm người dùng
    return render_template('admin/users/add.html', UserRole=UserRole)


@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user_to_edit = user_dao.get_user_by_id(user_id)
    if not user_to_edit:
        flash('Người dùng không tồn tại.', 'danger')
        return redirect(url_for('admin.users_management'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')  # Có thể rỗng nếu không đổi
        role_str = request.form.get('role')

        if not all([name, email, role_str]):
            flash('Vui lòng điền đầy đủ thông tin bắt buộc.', 'danger')
            return render_template('admin/users/edit.html', user=user_to_edit, UserRole=UserRole)

        try:
            role = UserRole(role_str)
        except ValueError:
            flash('Vai trò không hợp lệ.', 'danger')
            return render_template('admin/users/edit.html', user=user_to_edit, UserRole=UserRole)

        update_data = {
            'name': name,
            'email': email,
            'role': role
        }
        if password:  # Chỉ cập nhật mật khẩu nếu có nhập
            update_data['password'] = password

        if user_dao.update_user(user_id, **update_data):
            flash('Cập nhật người dùng thành công.', 'success')
            return redirect(url_for('admin.users_management'))
        else:
            flash('Có lỗi xảy ra khi cập nhật người dùng.', 'danger')
            return render_template('admin/users/edit.html', user=user_to_edit, UserRole=UserRole)

    # GET request: Hiển thị form chỉnh sửa người dùng
    return render_template('admin/users/edit.html', user=user_to_edit, UserRole=UserRole)


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_dao.delete_user(user_id):
        flash('Người dùng đã được xóa thành công.', 'success')
    else:
        flash('Không tìm thấy người dùng để xóa hoặc có lỗi xảy ra.', 'danger')
    return redirect(url_for('admin.users_management'))


# ==========================================================
# ROUTES QUẢN LÝ NHÀ HÀNG (RESTAURANT MANAGEMENT)
# ==========================================================

@admin_bp.route('/restaurants')
@admin_required
def restaurants_management():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    owners = User.query.filter_by(role=UserRole.OWNER).order_by(User.name).all()
    owner_filter = request.args.get('owner_id', type=int)

    restaurants_pagination = restaurant_dao.get_all_restaurants(
        page=page, page_size=10, query=search_query, owner_id=owner_filter
    )
    pending_restaurants = get_pending_restaurants()

    return render_template(
        'admin/restaurants/list.html',
        restaurants_pagination=restaurants_pagination,
        owners=owners,  # Truyền danh sách owners
        current_search=search_query,
        current_owner_filter=owner_filter,
        pending_restaurants = pending_restaurants
    )


@admin_bp.route('/restaurants/add', methods=['GET', 'POST'])
@admin_required
def add_restaurant():
    owners = User.query.filter_by(role=UserRole.OWNER).order_by(User.name).all()  # Luôn lấy owners
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        address = request.form.get('address')
        phone = request.form.get('phone')
        owner_id = request.form.get('owner_id', type=int)
        image_url = request.form.get('image_url')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not (name and address and phone and owner_id):
            flash('Vui lòng điền đầy đủ các trường bắt buộc.', 'danger')
            return render_template('admin/restaurants/add.html', owners=owners)  # Render lại form với data

        new_restaurant = restaurant_dao.add_restaurant(
            name, description, address, phone, owner_id,
            latitude=latitude, longitude=longitude, image_url=image_url
        )
        if new_restaurant:
            flash(f'Nhà hàng "{new_restaurant.name}" đã được thêm thành công.', 'success')
            return redirect(url_for('admin.restaurants_management'))
        else:
            flash('Có lỗi xảy ra khi thêm nhà hàng. Vui lòng kiểm tra lại Owner hoặc thử lại.', 'danger')
            return render_template('admin/restaurants/add.html', owners=owners)

    return render_template('admin/restaurants/add.html', owners=owners)


@admin_bp.route('/restaurants/edit/<int:restaurant_id>', methods=['GET', 'POST'])
@admin_required
def edit_restaurant(restaurant_id):
    restaurant_to_edit = restaurant_dao.get_restaurant_by_id(restaurant_id)
    if not restaurant_to_edit:
        flash('Nhà hàng không tồn tại.', 'danger')
        return redirect(url_for('admin.restaurants_management'))

    owners = User.query.filter_by(role=UserRole.OWNER).order_by(User.name).all()  # Luôn lấy owners

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        address = request.form.get('address')
        phone = request.form.get('phone')
        owner_id = request.form.get('owner_id', type=int)
        image_url = request.form.get('image_url')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not (name and address and phone and owner_id):
            flash('Vui lòng điền đầy đủ các trường bắt buộc.', 'danger')
            return render_template('admin/restaurants/edit.html', restaurant=restaurant_to_edit, owners=owners)

        update_data = {
            'name': name,
            'description': description,
            'address': address,
            'phone': phone,
            'owner_id': owner_id,
            'image_url': image_url,
            'latitude': latitude,
            'longitude': longitude
        }

        if restaurant_dao.update_restaurant(restaurant_id, **update_data):
            flash('Cập nhật nhà hàng thành công.', 'success')
            return redirect(url_for('admin.restaurants_management'))
        else:
            flash('Có lỗi xảy ra khi cập nhật nhà hàng. Vui lòng kiểm tra lại.', 'danger')
            return render_template('admin/restaurants/edit.html', restaurant=restaurant_to_edit, owners=owners)

    return render_template('admin/restaurants/edit.html', restaurant=restaurant_to_edit, owners=owners)


@admin_bp.route('/restaurants/delete/<int:restaurant_id>', methods=['POST'])
@admin_required
def delete_restaurant(restaurant_id):
    if restaurant_dao.delete_restaurant(restaurant_id):
        flash('Nhà hàng đã được xóa thành công.', 'success')
    else:
        flash('Không tìm thấy nhà hàng để xóa hoặc có lỗi xảy ra.', 'danger')
    return redirect(url_for('admin.restaurants_management'))

@admin_bp.route('/restaurants/<int:restaurant_id>/approve', methods=['POST'])
@login_required
def approve_restaurant_route(restaurant_id):
    approve_restaurant(restaurant_id)
    flash('Nhà hàng đã được duyệt!', 'success')
    return redirect(url_for('admin.restaurants_management'))

@admin_bp.route('/restaurants/<int:restaurant_id>/reject', methods=['POST'])
@login_required
def reject_restaurant_route(restaurant_id):
    reason = request.form.get('reason')
    reject_restaurant(restaurant_id, reason)
    flash('Nhà hàng đã bị từ chối!', 'danger')
    return redirect(url_for('admin.restaurants_management'))

# ==========================================================
# ROUTES QUẢN LÝ MÃ KHUYẾN MÃI (PROMO MANAGEMENT)
# ==========================================================

