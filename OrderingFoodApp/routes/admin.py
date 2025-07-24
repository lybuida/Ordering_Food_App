# admin.py
from functools import wraps

from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_admin import Admin
from flask import make_response

from OrderingFoodApp.dao.restaurant_dao import *
from OrderingFoodApp.models import *
from OrderingFoodApp.dao import user_dao, restaurant_dao, order_owner, reports_dao
import io
import pandas as pd
from flask import send_file
from datetime import datetime
import csv


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
    @login_required  # Đảm bảo người dùng đã đăng nhập trước
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:  # Kiểm tra thuộc tính is_admin của User model
            flash('Bạn không có quyền truy cập vào trang này.', 'danger')
            # Chuyển hướng về trang chủ hoặc trang lỗi
            return redirect(url_for('home'))  # Hoặc url_for('auth_bp.login') nếu muốn đăng nhập lại
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
        pending_restaurants=pending_restaurants
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

# @admin_bp.route('/promo-codes')
# def promo_codes():
#     promos = get_all_promo_codes()
#
#     class DummyPagination:
#         def __init__(self, items):
#             self.items = items
#             self.iter_pages = lambda: [1]
#             self.page = 1
#
#     promos_pagination = DummyPagination(promos)
#
#     return render_template(
#         'admin/promos/list.html',
#         promos_pagination=promos_pagination,
#         current_search=""
#     )


@admin_bp.route('/promos')
@login_required
def promo_management():
    if not current_user.is_admin:
        abort(403)

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    promos_query = PromoCode.query

    if search:
        promos_query = promos_query.filter(PromoCode.code.ilike(f"%{search}%"))

    promos_query = promos_query.order_by(PromoCode.created_at.desc())
    promos_pagination = promos_query.paginate(page=page, per_page=10, error_out=False)

    return render_template(
        'admin/promos/list.html',
        promos_pagination=promos_pagination,
        current_search=search
    )


@admin_bp.route('/promos/add', methods=['GET', 'POST'])
@login_required
def add_promo():
    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        code = request.form.get('code')
        description = request.form.get('description')
        discount_type = request.form.get('discount_type')
        discount_value = request.form.get('discount_value')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        usage_limit = request.form.get('usage_limit')

        if discount_type == 'PERCENT' and float(discount_value) > 50:
            flash('Giảm giá phần trăm không được vượt quá 50%.', 'danger')
            return redirect(url_for('admin.add_promo'))

        if PromoCode.query.filter_by(code=code).first():
            flash('Mã khuyến mãi đã tồn tại.', 'danger')
            return redirect(url_for('admin.add_promo'))

        try:
            new_promo = PromoCode(
                code=code,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                start_date=datetime.strptime(start_date, '%Y-%m-%dT%H:%M'),
                end_date=datetime.strptime(end_date, '%Y-%m-%dT%H:%M'),
                usage_limit=int(usage_limit)
            )
            db.session.add(new_promo)
            db.session.commit()
            flash('Thêm mã khuyến mãi thành công.', 'success')
            return redirect(url_for('admin.promo_management'))
        except Exception as e:
            flash(f'Lỗi khi thêm mã: {e}', 'danger')

    return render_template('admin/promos/add.html')


@admin_bp.route('/promos/<int:promo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_promo(promo_id):
    if not current_user.is_admin:
        abort(403)

    promos = PromoCode.query.get_or_404(promo_id)

    if request.method == 'POST':
        promos.code = request.form.get('code')
        promos.description = request.form.get('description')
        promos.discount_type = request.form.get('discount_type')
        promos.discount_value = request.form.get('discount_value')
        promos.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        promos.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        promos.usage_limit = request.form.get('usage_limit')

        db.session.commit()
        flash('Cập nhật thành công.', 'success')
        return redirect(url_for('admin.promo_management'))

    return render_template('admin/promos/edit.html', promo=promos)

@admin_bp.route('/promos/<int:promo_id>/delete', methods=['POST'])
@login_required
def delete_promo(promo_id):
    if not current_user.is_admin:
        abort(403)

    promo = PromoCode.query.get_or_404(promo_id)
    db.session.delete(promo)
    db.session.commit()
    flash('Xóa thành công.', 'success')
    return redirect(url_for('admin.promo_management'))

# ==========================================================
# ROUTES BÁO CÁO THỐNG KÊ (REPORTS MANAGEMENT)
# ==========================================================

@admin_bp.route('/reports')
@admin_required
def report_dashboard():
    return render_template('admin/reports/dashboard.html')

@admin_bp.route('/reports/users')
@admin_required
def user_report():
    start = request.args.get('start')
    end = request.args.get('end')
    report_type = request.args.get('type', 'daily')  # Mặc định là daily

    start_date = datetime.strptime(start, '%Y-%m-%d') if start else None
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None

    labels = []
    values = []
    total_users = 0
    role_stats = []

    if report_type == 'daily':
        user_stats = reports_dao.get_user_registration_stats(start_date, end_date)
        labels = [row[0].strftime('%Y-%m-%d') for row in user_stats]
        values = [row[1] for row in user_stats]
        total_users = sum(values)

    elif report_type == 'role':
        role_stats = reports_dao.get_user_count_by_role()
        labels = [role.name.title() for role, _ in role_stats]
        values = [count for _, count in role_stats]
        total_users = sum(values)

    return render_template(
        'admin/reports/users.html',
        report_type=report_type,
        labels=labels,
        values=values,
        total_users=total_users,
        start=start,
        end=end,
        role_stats=role_stats
    )




@admin_bp.route('/reports/restaurants')
@admin_required
def restaurant_report():
    report_type = request.args.get('type', 'daily')
    start = request.args.get('start')
    end = request.args.get('end')

    start_date = datetime.strptime(start, '%Y-%m-%d') if start else None
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None

    labels = []
    values = []
    total = 0

    STATUS_DISPLAY = {
        RestaurantApprovalStatus.APPROVED: 'Đã duyệt',
        RestaurantApprovalStatus.PENDING: 'Chờ duyệt',
        RestaurantApprovalStatus.REJECTED: 'Từ chối'
    }

    if report_type == 'daily':
        stats = reports_dao.get_restaurant_registration_stats(start_date, end_date)
        labels = [row[0].strftime('%Y-%m-%d') for row in stats]
        values = [row[1] for row in stats]
        total = sum(values)
    elif report_type == 'status':
        stats = reports_dao.get_restaurant_count_by_status()
        labels = [STATUS_DISPLAY.get(status, str(status)) for status, _ in stats]  # ✅ dùng tên thân thiện
        values = [count for _, count in stats]
        total = sum(values)
    else:
        stats = []

    return render_template(
        'admin/reports/restaurants.html',
        report_type=report_type,
        start=start,
        end=end,
        labels=labels,
        values=values,
        total_restaurants=total,
        restaurant_stats=stats
    )

@admin_bp.route('/reports/users/export/<export_format>')
@admin_required
def export_user_report(export_format):
    user_stats = reports_dao.get_user_registration_stats()
    role_stats = reports_dao.get_user_count_by_role()  # <- NEW

    filename = f"user_report_{datetime.now().strftime('%Y%m%d')}.{export_format}"

    if export_format == 'excel':
        import pandas as pd
        import io

        df_daily = pd.DataFrame(user_stats, columns=["Ngày", "Số lượng người dùng"])
        df_roles = pd.DataFrame(role_stats, columns=["Vai trò", "Số lượng"])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_daily.to_excel(writer, index=False, sheet_name='Theo ngày')
            df_roles.to_excel(writer, index=False, sheet_name='Theo vai trò')

        output.seek(0)
        return send_file(output, download_name=filename, as_attachment=True)

    elif export_format == 'pdf':
        # Tạm thời xuất CSV làm PDF mẫu
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Ngày", "Số lượng người dùng"])
        for row in user_stats:
            writer.writerow([row[0], row[1]])

        writer.writerow([])
        writer.writerow(["Vai trò", "Số lượng"])
        for row in role_stats:
            writer.writerow([row[0], row[1]])

        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv"
        return response

    return "Định dạng không hợp lệ", 400

@admin_bp.route('/reports/restaurants/export/excel')
@admin_required
def export_restaurants_excel():
    start = request.args.get('start')
    end = request.args.get('end')

    start_date = datetime.strptime(start, '%Y-%m-%d') if start else None
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None

    data = reports_dao.get_restaurant_registration_stats(start_date, end_date)
    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='RestaurantReport')

    output.seek(0)
    return send_file(output, download_name="restaurant_report.xlsx", as_attachment=True)

@admin_bp.route('/reports/promos')
@admin_required
def promo_report():
    report_type = request.args.get('type', 'daily')
    start = request.args.get('start')
    end = request.args.get('end')

    start_date = datetime.strptime(start, '%Y-%m-%d') if start else None
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None

    labels = []
    values = []
    promo_stats = []
    total_promos = 0

    if report_type == 'daily':
        promo_stats = reports_dao.get_promo_created_stats(start_date, end_date)
        labels = [row[0].strftime('%Y-%m-%d') for row in promo_stats]
        values = [row[1] for row in promo_stats]
        total_promos = sum(values)

    elif report_type == 'type':
        promo_stats = reports_dao.get_promo_stats_by_type()
        labels = [str(row[0].value) for row in promo_stats]  # Enum -> string
        values = [row[1] for row in promo_stats]
        total_promos = sum(values)

    return render_template(
        'admin/reports/promos.html',
        labels=labels,
        values=values,
        total_promos=total_promos,
        promo_stats=promo_stats,
        start=start,
        end=end,
        report_type=report_type
    )

@admin_bp.route('/reports/promos/export/<export_format>')
@admin_required
def export_promo_report(export_format):
    report_type = request.args.get('type', 'daily')
    start = request.args.get('start')
    end = request.args.get('end')

    start_date = datetime.strptime(start, '%Y-%m-%d') if start else None
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None

    if report_type == 'daily':
        promo_stats = reports_dao.get_promo_stats_by_day(start_date, end_date)
        headers = ['Ngày', 'Số lượng mã']
        rows = [(row[0].strftime('%Y-%m-%d'), row[1]) for row in promo_stats]
    elif report_type == 'type':
        promo_stats = reports_dao.get_promo_count_by_type()
        headers = ['Loại giảm giá', 'Số lượng mã']
        rows = [(row[0].value, row[1]) for row in promo_stats]
    else:
        return "Loại báo cáo không hợp lệ", 400

    filename = f"promo_report_{report_type}_{datetime.now().strftime('%Y%m%d')}"

    if export_format == 'excel':
        df = pd.DataFrame(rows, columns=headers)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PromoReport')
        output.seek(0)
        return send_file(output, download_name=f"{filename}.xlsx", as_attachment=True)

    elif export_format == 'pdf':
        # Chỉ tạo bảng dạng text đơn giản (tuỳ chọn nâng cấp sau)
        from flask import make_response
        pdf_text = f"{headers[0]}\t{headers[1]}\n"
        for row in rows:
            pdf_text += f"{row[0]}\t{row[1]}\n"

        response = make_response(pdf_text)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.txt'
        response.headers['Content-Type'] = 'text/plain'
        return response

    return "Định dạng không hợp lệ", 400
