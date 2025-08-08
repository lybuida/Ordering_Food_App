# owner.py
from datetime import time

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from OrderingFoodApp.dao import restaurants_owner
from OrderingFoodApp.dao.restaurants_owner import RestaurantDAO
# from OrderingFoodApp.dao.restaurants_owner import RestaurantDAO
from OrderingFoodApp.models import *
from OrderingFoodApp.dao.order_owner import OrderDAO
from flask import flash
from werkzeug.utils import secure_filename
import os
from OrderingFoodApp.dao.menu_owner import MenuDAO
from flask import current_app
from sqlalchemy import func

from OrderingFoodApp.models import RestaurantApprovalStatus

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


####HOME

@owner_bp.route('/')
@login_required
def index():
    # Lấy thông tin chủ nhà hàng
    owner = User.query.filter_by(id=current_user.id).first()

    # Lấy danh sách nhà hàng của owner
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
    for r in restaurants:
        r.approval_status = r.approval_status.value

    approved_restaurants = [r for r in restaurants if r.approval_status == 'approved']
    approved_restaurant_ids = [r.id for r in approved_restaurants]

    # Lấy ngày hiện tại
    today = datetime.now().date()

    # Đếm số đơn hôm nay
    orders_in_today = db.session.query(Order).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Restaurant.id.in_(approved_restaurant_ids),
        Order.status == OrderStatus.COMPLETED,
    func.date(Order.updated_at) == today
    ).count()

    # Doanh thu hôm nay
    revenue_in_today = db.session.query(func.sum(Order.total_amount)).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Restaurant.id.in_(approved_restaurant_ids),
        func.date(Order.updated_at) == today,
        Order.status == OrderStatus.COMPLETED
    ).scalar()
    revenue_in_today = revenue_in_today or 0

    # Đơn chờ xác nhận
    pending_orders = db.session.query(Order).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Restaurant.id.in_(approved_restaurant_ids),
        Order.status == OrderStatus.PENDING
    ).count()

    # Đơn mới nhất
    new_orders = db.session.query(Order).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Restaurant.id.in_(approved_restaurant_ids),
        Order.status == OrderStatus.PENDING
    ).order_by(Order.created_at.desc()).limit(5).all()

    # Đánh giá mới
    recent_reviews = db.session.query(Review).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Restaurant.id.in_(approved_restaurant_ids)
    ).order_by(Review.created_at.desc()).limit(3).all()

    # Chuẩn bị danh sách đơn hàng mới cho template
    formatted_new_orders = []
    for order in new_orders:
        customer = User.query.get(order.customer_id)
        item_count = db.session.query(OrderItem).filter_by(order_id=order.id).count()

        formatted_new_orders.append({
            'id': order.id,
            'code': f"#{order.id:06d}",
            'time': order.created_at.strftime('%H:%M %d/%m'),
            'amount': order.total_amount,
            'item_count': item_count,
            'status': order.status.value
        })

    # Chuẩn bị danh sách đánh giá cho template
    formatted_reviews = []
    for review in recent_reviews:
        customer = User.query.get(review.customer_id)

        formatted_reviews.append({
            'id': review.id,
            'customer_name': customer.name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%d/%m/%Y')
        })

    return render_template('owner/index.html',
                           user=owner,
                           orders_in_today= orders_in_today,
                           revenue_in_today=revenue_in_today,
                           pending_orders=pending_orders,
                           new_orders=formatted_new_orders,
                           recent_reviews=formatted_reviews,
                           restaurants=restaurants,
                           approved_restaurants=approved_restaurants)

### RESTAURANTS
# ==========================================================
# ROUTES QUẢN LÝ NHÀ HÀNG (RESTAURANT MANAGEMENT)
# ==========================================================

@owner_bp.route('/restaurants')
@login_required
def owner_restaurants():
    """Trang quản lý nhà hàng của chủ sở hữu"""
    restaurants = RestaurantDAO.get_restaurants_by_owner(current_user.id)

    # Format dữ liệu cho template
    formatted_restaurants = []
    for restaurant in restaurants:
        formatted_restaurants.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'description': restaurant.description,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'opening_time': restaurant.opening_time.strftime('%H:%M'),
            'closing_time': restaurant.closing_time.strftime('%H:%M'),
            'image_url': restaurant.image_url,
            'approval_status': restaurant.approval_status.value,
            'approval_status_display': RestaurantDAO.get_approval_status_display(restaurant.approval_status),
            'rejection_reason': restaurant.rejection_reason,
            'created_at': restaurant.created_at.strftime('%d/%m/%Y')
        })

    return render_template('owner/restaurants.html', restaurants=formatted_restaurants)


# owner.py (phần sửa đổi)

### RESTAURANTS
@owner_bp.route('/restaurants/add', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    """Thêm nhà hàng mới"""
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            name = request.form.get('name')
            description = request.form.get('description')
            address = request.form.get('address')
            phone = request.form.get('phone')

            # Xử lý thời gian với định dạng linh hoạt
            opening_time_str = request.form.get('opening_time', '').strip()
            closing_time_str = request.form.get('closing_time', '').strip()

            try:
                opening_time = datetime.strptime(opening_time_str, '%H:%M').time() if len(
                    opening_time_str) <= 5 else datetime.strptime(opening_time_str, '%H:%M:%S').time()
                closing_time = datetime.strptime(closing_time_str, '%H:%M').time() if len(
                    closing_time_str) <= 5 else datetime.strptime(closing_time_str, '%H:%M:%S').time()
            except ValueError:
                flash('Định dạng giờ không hợp lệ. Vui lòng nhập theo định dạng HH:MM hoặc HH:MM:SS', 'danger')
                return render_template('owner/restaurant_form.html', restaurant=None)

            try:
                latitude = float(request.form.get('latitude', 0))
                longitude = float(request.form.get('longitude', 0))
            except ValueError:
                latitude = longitude = 0.0

            # Xử lý upload ảnh
            image_url = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/restaurants')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/restaurants/{filename}'

            # Tạo nhà hàng mới
            restaurant = RestaurantDAO.create_restaurant(
                owner_id=current_user.id,
                name=name,
                description=description,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time,
                latitude=latitude,
                longitude=longitude,
                image_url=image_url
            )

            flash('Đã gửi yêu cầu tạo nhà hàng. Vui lòng chờ quản trị viên duyệt.', 'success')
            return redirect(url_for('owner.owner_restaurants'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Lỗi khi thêm nhà hàng: {str(e)}')
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return render_template('owner/restaurant_form.html', restaurant=None)


@owner_bp.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_restaurant(restaurant_id):
    """Chỉnh sửa thông tin nhà hàng"""
    restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id, current_user.id)
    if not restaurant:
        flash('Nhà hàng không tồn tại hoặc bạn không có quyền chỉnh sửa', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            name = request.form.get('name')
            description = request.form.get('description')
            address = request.form.get('address')
            phone = request.form.get('phone')

            # Xử lý thời gian với định dạng linh hoạt
            opening_time_str = request.form.get('opening_time', '').strip()
            closing_time_str = request.form.get('closing_time', '').strip()

            try:
                opening_time = datetime.strptime(opening_time_str, '%H:%M').time() if len(
                    opening_time_str) <= 5 else datetime.strptime(opening_time_str, '%H:%M:%S').time()
                closing_time = datetime.strptime(closing_time_str, '%H:%M').time() if len(
                    closing_time_str) <= 5 else datetime.strptime(closing_time_str, '%H:%M:%S').time()
            except ValueError:
                flash('Định dạng giờ không hợp lệ. Vui lòng nhập theo định dạng HH:MM hoặc HH:MM:SS', 'danger')
                return render_template('owner/restaurant_form.html', restaurant=restaurant)

            try:
                latitude = float(request.form.get('latitude', 0))
                longitude = float(request.form.get('longitude', 0))
            except ValueError:
                latitude = restaurant.latitude
                longitude = restaurant.longitude

            resubmit = request.form.get('resubmit') == 'on'

            # Xử lý upload ảnh
            image_url = restaurant.image_url
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/restaurants')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/restaurants/{filename}'

            # Cập nhật thông tin nhà hàng
            updated_restaurant = RestaurantDAO.update_restaurant(
                restaurant_id=restaurant.id,
                owner_id=current_user.id,
                name=name,
                description=description,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time,
                latitude=latitude,
                longitude=longitude,
                image_url=image_url
            )

            # Nếu chọn gửi lại yêu cầu duyệt
            if resubmit and restaurant.approval_status == RestaurantApprovalStatus.REJECTED:
                RestaurantDAO.resubmit_restaurant(restaurant.id, current_user.id)
                flash('Đã gửi lại yêu cầu duyệt nhà hàng. Vui lòng chờ quản trị viên xử lý.', 'success')
            else:
                flash('Cập nhật thông tin nhà hàng thành công', 'success')

            return redirect(url_for('owner.owner_restaurants'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Lỗi khi cập nhật nhà hàng: {str(e)}')
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return render_template('owner/restaurant_form.html', restaurant=restaurant)



@owner_bp.route('/restaurants/<int:restaurant_id>')
@login_required
def restaurant_details(restaurant_id):
    """Xem chi tiết nhà hàng"""
    restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id, current_user.id)
    if not restaurant:
        flash('Nhà hàng không tồn tại hoặc bạn không có quyền xem', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    # Format dữ liệu cho template
    restaurant_data = {
        'id': restaurant.id,
        'name': restaurant.name,
        'description': restaurant.description,
        'address': restaurant.address,
        'phone': restaurant.phone,
        'opening_time': restaurant.opening_time.strftime('%H:%M'),
        'closing_time': restaurant.closing_time.strftime('%H:%M'),
        'image_url': restaurant.image_url,
        'approval_status': restaurant.approval_status.value,
        'approval_status_display': RestaurantDAO.get_approval_status_display(restaurant.approval_status),
        'rejection_reason': restaurant.rejection_reason,
        'created_at': restaurant.created_at.strftime('%d/%m/%Y'),
        'latitude': restaurant.latitude,
        'longitude': restaurant.longitude
    }

    return render_template('owner/restaurant_dt.html', restaurant=restaurant_data)

@owner_bp.route('/restaurants/<int:restaurant_id>/delete', methods=['POST'])
@login_required
def delete_restaurant(restaurant_id):
    """Xóa nhà hàng"""
    try:
        success = RestaurantDAO.delete_restaurant(restaurant_id, current_user.id)
        if success:
            flash('Xóa nhà hàng thành công', 'success')
        else:
            flash('Nhà hàng không tồn tại hoặc bạn không có quyền xóa', 'danger')
    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return redirect(url_for('owner.owner_restaurants'))



###MENU

@owner_bp.route('/menu')
@login_required
def owner_menu():
    # Lấy thông số lọc từ request
    restaurant_id = request.args.get('restaurant_id')
    category_id = request.args.get('category_id', 'all')
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)

    # Lấy danh sách nhà hàng của owner
    restaurants = Restaurant.query.filter_by(
        owner_id=current_user.id,
        approval_status=RestaurantApprovalStatus.APPROVED
    ).all()

    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('owner.index'))

    # Nếu không chọn nhà hàng, lấy nhà hàng đầu tiên
    if not restaurant_id:
        restaurant_id = restaurants[0].id

    # Lấy danh sách món ăn
    menu_items = MenuDAO.get_menu_items(
        restaurant_id=restaurant_id,
        category_id=category_id,
        status_filter=status_filter,
        search=search,
        page=page
    )

    categories = MenuDAO.get_categories()

    return render_template('owner/menu.html',
                           menu_items=menu_items,
                           categories=categories,
                           restaurants=restaurants,
                           current_restaurant_id=int(restaurant_id),
                           filter_values={
                               'restaurant_id': restaurant_id,
                               'category_id': category_id,
                               'status': status_filter,
                               'search': search
                           })


@owner_bp.route('/menu/add', methods=['GET', 'POST'])
@login_required
def add_menu_item():
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            restaurant_id = request.form.get('restaurant_id')
            category_id = request.form.get('category_id')
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            is_active = request.form.get('is_active', 'off') == 'on'

            # Validate dữ liệu
            if not all([restaurant_id, category_id, name, price]):
                flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'danger')
                return redirect(url_for('owner.add_menu_item'))

            # Xử lý upload ảnh
            image_url = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/menu_items')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/menu_items/{filename}'

            # Tạo món ăn mới
            new_item = MenuItem(
                restaurant_id=restaurant_id,
                category_id=category_id,
                name=name,
                description=description,
                price=price,
                image_url=image_url,
                is_active=is_active
            )

            db.session.add(new_item)
            db.session.commit()

            flash('Thêm món ăn thành công', 'success')
            return redirect(url_for('owner.owner_menu'))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
            return redirect(url_for('owner.add_menu_item'))

    # Lấy danh sách nhà hàng và danh mục
    restaurants = Restaurant.query.filter_by(
        owner_id=current_user.id,
        approval_status=RestaurantApprovalStatus.APPROVED
    ).all()
    categories = MenuCategory.query.all()

    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('owner.index'))

    return render_template('owner/menu_form.html',
                           restaurants=restaurants,
                           categories=categories,
                           menu_item=None)


@owner_bp.route('/menu/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_menu_item(item_id):
    menu_item = MenuDAO.get_menu_item_by_id(item_id)

    if not menu_item:
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('owner.owner_menu'))

    # Kiểm tra quyền sở hữu
    restaurant = Restaurant.query.get(menu_item.restaurant_id)
    if restaurant.owner_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa món ăn này', 'danger')
        return redirect(url_for('owner.owner_menu'))

    if request.method == 'POST':
        try:
            category_id = request.form.get('category_id')
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            is_active = request.form.get('is_active') == 'on'

            # Xử lý upload ảnh
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/menu_items')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/menu_items/{filename}'
                    menu_item.image_url = image_url

            # Cập nhật thông tin
            MenuDAO.update_menu_item(
                item_id=item_id,
                category_id=category_id,
                name=name,
                description=description,
                price=price,
                is_active=is_active
            )

            flash('Cập nhật món ăn thành công', 'success')
            return redirect(url_for('owner.owner_menu'))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    categories = MenuCategory.query.all()
    return render_template('owner/menu_form.html',
                           menu_item=menu_item,
                           categories=categories,
                           restaurants=None)


@owner_bp.route('/menu/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_menu_item(item_id):
    menu_item = MenuDAO.get_menu_item_by_id(item_id)

    if not menu_item:
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('owner.owner_menu'))

    # Kiểm tra quyền sở hữu
    restaurant = Restaurant.query.get(menu_item.restaurant_id)
    if restaurant.owner_id != current_user.id:
        flash('Bạn không có quyền xóa món ăn này', 'danger')
        return redirect(url_for('owner.owner_menu'))

    try:
        MenuDAO.delete_menu_item(item_id)
        flash('Xóa món ăn thành công', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return redirect(url_for('owner.owner_menu'))


@owner_bp.route('/menu/<int:item_id>/toggle-status', methods=['POST'])
@login_required
def toggle_menu_item_status(item_id):
    menu_item = MenuDAO.get_menu_item_by_id(item_id)

    if not menu_item:
        return jsonify({'success': False, 'message': 'Món ăn không tồn tại'})

    # Kiểm tra quyền sở hữu
    restaurant = Restaurant.query.get(menu_item.restaurant_id)
    if restaurant.owner_id != current_user.id:
        return jsonify({'success': False, 'message': 'Bạn không có quyền thực hiện'})

    success = MenuDAO.toggle_menu_item_status(item_id)
    if success:
        return jsonify({
            'success': True,
            'message': 'Cập nhật trạng thái thành công',
            'is_active': menu_item.is_active
        })
    else:
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra'})


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


### ORDER
@owner_bp.route('/orders', methods=['GET', 'POST'])
@login_required
def owner_orders():
    # Lấy thông số lọc từ request
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    branch_id = request.args.get('branch_id')
    page = request.args.get('page', 1, type=int)

    # Lấy danh sách nhà hàng của owner để hiển thị trong dropdown
    restaurants = Restaurant.query.filter_by(
        owner_id=current_user.id,
        approval_status=RestaurantApprovalStatus.APPROVED
    ).all()
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào được duyệt', 'warning')
        return redirect(url_for('owner.index'))

    # Lấy danh sách đơn hàng
    orders_data = OrderDAO.get_orders_by_owner(
        owner_id=current_user.id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
        page=page,
        per_page=10
    )

    return render_template('owner/orders.html',
                           orders=orders_data['orders'],
                           pagination=orders_data,
                           restaurants=restaurants,
                           filter_values={
                               'status': status,
                               'start_date': start_date,
                               'end_date': end_date,
                               'branch_id': branch_id
                           })


@owner_bp.route('/orders/<int:order_id>')
@login_required
def order_details(order_id):
    order = OrderDAO.get_order_details(order_id)
    if not order:
        return redirect(url_for('owner.owner_orders'))

    # Kiểm tra quyền - sửa lại cách truy cập restaurant_id
    restaurant = Restaurant.query.get(order['restaurant_id'])  # Truy cập như dictionary
    if not restaurant or restaurant.owner_id != current_user.id:
        return redirect(url_for('owner.owner_orders'))

    return render_template('owner/order_details.html', order=order)  # Truyền dictionary

@owner_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    status = request.form.get('status')
    rj_reason = request.form.get('rejection_reason')

    # Kiểm tra quyền
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Đơn hàng không tồn tại'})

    restaurant = Restaurant.query.get(order.restaurant_id)
    if restaurant.owner_id != current_user.id:
        return jsonify({'success': False, 'message': 'Không có quyền thực hiện'})

    # Kiểm tra nếu là hủy đơn thì phải có lý do
    if status == 'cancelled' and not rj_reason:
        return jsonify({'success': False, 'message': 'Vui lòng nhập lý do hủy đơn'})

    # Cập nhật trạng thái
    success = OrderDAO.update_order_status(order_id, status, rj_reason)
    if success:
        return jsonify({'success': True, 'message': 'Cập nhật trạng thái thành công'})
    else:
        return jsonify({'success': False, 'message': 'Không thể chuyển sang trạng thái này'})


##33##doanh thu####

@owner_bp.route('/statistics', methods=['GET'])
@login_required
def advanced_statistics():
    """Trang thống kê nâng cao"""
    # Lấy thông số lọc từ request
    restaurant_id = request.args.get('restaurant_id', 'all')
    time_range = request.args.get('time_range', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Lấy danh sách nhà hàng của owner
    restaurants = Restaurant.query.filter_by(
        owner_id=current_user.id,
        approval_status=RestaurantApprovalStatus.APPROVED
    ).all()

    if not restaurants:
        flash('Bạn chưa có nhà hàng nào được duyệt', 'warning')
        return redirect(url_for('owner.index'))

    # Lấy thống kê
    stats = OrderDAO.get_advanced_statistics(
        owner_id=current_user.id,
        restaurant_id=restaurant_id if restaurant_id != 'all' else None,
        start_date=start_date,
        end_date=end_date
    )

    # Lấy dữ liệu biểu đồ
    chart_data = OrderDAO.get_time_series_statistics(
        owner_id=current_user.id,
        restaurant_id=restaurant_id if restaurant_id != 'all' else None,
        time_range=time_range
    )

    return render_template('owner/statistics.html',
                         statistics=stats,
                         chart_data=chart_data,
                         restaurants=restaurants,
                         current_restaurant_id=restaurant_id,
                         time_range=time_range,
                         start_date=start_date,
                         end_date=end_date)