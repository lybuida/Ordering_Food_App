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

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


####HOME
# owner.py
@owner_bp.route('/')
@login_required
def index():
    # Lấy thông tin chủ nhà hàng
    owner = User.query.filter_by(id=current_user.id).first()

    # Lấy ngày hiện tại
    today = datetime.now().date()

    # Đếm số đơn hôm nay
    orders_today = db.session.query(Order).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        func.date(Order.created_at) == today
    ).count()

    # Doanh thu hôm nay
    revenue_today = db.session.query(func.sum(Order.total_amount)).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        func.date(Order.created_at) == today,
        Order.status != OrderStatus.CANCELLED
    ).scalar()
    revenue_today = revenue_today or 0  # Tránh None

    # Đơn chờ xác nhận
    pending_orders = db.session.query(Order).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Order.status == OrderStatus.PENDING
    ).count()

    # Đơn mới nhất (5 đơn)
    new_orders = db.session.query(Order).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id,
        Order.status == OrderStatus.PENDING
    ).order_by(Order.created_at.desc()).limit(5).all()

    # Đánh giá mới (2 đánh giá)
    recent_reviews = db.session.query(Review).join(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    ).order_by(Review.created_at.desc()).limit(2).all()

    # # Thông tin nhà hàng (lấy nhà hàng đầu tiên)
    # restaurant = db.session.query(Restaurant).filter(
    #     Restaurant.owner_id == current_user.id
    # ).first()

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
        # Lấy danh sách nhà hàng của owner
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()

    return render_template('owner/index.html',
                           user=owner,
                           orders_today=orders_today,
                           revenue_today=revenue_today,
                           pending_orders=pending_orders,
                           new_orders=formatted_new_orders,
                           recent_reviews=formatted_reviews,
                           restaurants=restaurants)


##RES
### RESTAURANTS
@owner_bp.route('/restaurants')
@login_required
def owner_restaurants():
    restaurants = RestaurantDAO.get_restaurants_by_owner(current_user.id)
    return render_template('owner/restaurants.html',
                           restaurants=restaurants,
                           current_restaurant=None)


@owner_bp.route('/restaurants/<int:restaurant_id>')
@login_required
def restaurant_details(restaurant_id):
    restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.id:
        flash('Nhà hàng không tồn tại hoặc bạn không có quyền truy cập', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    branches = RestaurantDAO.get_branches_by_restaurant(restaurant_id)
    return render_template('owner/restaurants.html',
                           restaurants=None,
                           current_restaurant=restaurant,
                           branches=branches)


@owner_bp.route('/restaurants/add', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            address = request.form.get('address')
            phone = request.form.get('phone')
            opening_time = time.fromisoformat(request.form.get('opening_time'))
            closing_time = time.fromisoformat(request.form.get('closing_time'))

            # Validate required fields
            if not all([name, address, phone, opening_time, closing_time]):
                flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'danger')
                return redirect(url_for('owner.add_restaurant'))

            # Handle image upload
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

            # Create restaurant
            restaurant = RestaurantDAO.create_restaurant(
                owner_id=current_user.id,
                name=name,
                description=description,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time,
                image_url=image_url
            )

            flash('Thêm nhà hàng thành công', 'success')
            return redirect(url_for('owner.restaurant_details', restaurant_id=restaurant.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
            return redirect(url_for('owner.add_restaurant'))

    return render_template('owner/restaurant_form.html', restaurant=None)


@owner_bp.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_restaurant(restaurant_id):
    restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.id:
        flash('Nhà hàng không tồn tại hoặc bạn không có quyền chỉnh sửa', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            address = request.form.get('address')
            phone = request.form.get('phone')
            opening_time = time.fromisoformat(request.form.get('opening_time'))
            closing_time = time.fromisoformat(request.form.get('closing_time'))

            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/restaurants')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/restaurants/{filename}'
                    restaurant.image_url = image_url

            # Update restaurant
            RestaurantDAO.update_restaurant(
                restaurant_id=restaurant_id,
                name=name,
                description=description,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time
            )

            flash('Cập nhật nhà hàng thành công', 'success')
            return redirect(url_for('owner.restaurant_details', restaurant_id=restaurant_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return render_template('owner/restaurant_form.html', restaurant=restaurant)


@owner_bp.route('/restaurants/<int:restaurant_id>/delete', methods=['POST'])
@login_required
def delete_restaurant(restaurant_id):
    restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.id:
        flash('Nhà hàng không tồn tại hoặc bạn không có quyền xóa', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    try:
        RestaurantDAO.delete_restaurant(restaurant_id)
        flash('Xóa nhà hàng thành công', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return redirect(url_for('owner.owner_restaurants'))


### BRANCHES
@owner_bp.route('/branches/add/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def add_branch(restaurant_id):
    restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.id:
        flash('Nhà hàng không tồn tại hoặc bạn không có quyền thêm chi nhánh', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            address = request.form.get('address')
            phone = request.form.get('phone')
            opening_time = time.fromisoformat(request.form.get('opening_time'))
            closing_time = time.fromisoformat(request.form.get('closing_time'))
            status = request.form.get('status', 'active')

            # Validate required fields
            if not all([name, address, phone, opening_time, closing_time]):
                flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'danger')
                return redirect(url_for('owner.add_branch', restaurant_id=restaurant_id))

            # Handle image upload
            image_url = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/branches')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/branches/{filename}'

            # Create branch
            branch = RestaurantDAO.create_branch(
                restaurant_id=restaurant_id,
                name=name,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time,
                status=status,
                image_url=image_url
            )

            flash('Thêm chi nhánh thành công', 'success')
            return redirect(url_for('owner.restaurant_details', restaurant_id=restaurant_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
            return redirect(url_for('owner.add_branch', restaurant_id=restaurant_id))

    return render_template('owner/branch_form.html',
                           restaurant=restaurant,
                           branch=None)


@owner_bp.route('/branches/<int:branch_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_branch(branch_id):
    branch = RestaurantDAO.get_branch_by_id(branch_id)
    if not branch:
        flash('Chi nhánh không tồn tại', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    restaurant = RestaurantDAO.get_restaurant_by_id(branch.restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa chi nhánh này', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            address = request.form.get('address')
            phone = request.form.get('phone')
            opening_time = time.fromisoformat(request.form.get('opening_time'))
            closing_time = time.fromisoformat(request.form.get('closing_time'))
            status = request.form.get('status', 'active')

            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads/branches')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = f'/static/uploads/branches/{filename}'
                    branch.image_url = image_url

            # Update branch
            RestaurantDAO.update_branch(
                branch_id=branch_id,
                name=name,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time,
                status=status
            )

            flash('Cập nhật chi nhánh thành công', 'success')
            return redirect(url_for('owner.restaurant_details', restaurant_id=restaurant.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return render_template('owner/branch_form.html',
                           restaurant=restaurant,
                           branch=branch)


@owner_bp.route('/branches/<int:branch_id>/delete', methods=['POST'])
@login_required
def delete_branch(branch_id):
    branch = RestaurantDAO.get_branch_by_id(branch_id)
    if not branch:
        flash('Chi nhánh không tồn tại', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    restaurant = RestaurantDAO.get_restaurant_by_id(branch.restaurant_id)
    if not restaurant or restaurant.owner_id != current_user.id:
        flash('Bạn không có quyền xóa chi nhánh này', 'danger')
        return redirect(url_for('owner.owner_restaurants'))

    try:
        RestaurantDAO.delete_branch(branch_id)
        flash('Xóa chi nhánh thành công', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return redirect(url_for('owner.restaurant_details', restaurant_id=restaurant.id))


###MENU
# @owner_bp.route('/menu')
# def owner_menu():
#     return render_template('owner/menu.html')


# Route menu chính (đã cập nhật)
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
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()

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
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
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
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()

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
    order = OrderDAO.get_order_details(order_id)  # Đây phải là dictionary đã xử lý
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

    # Kiểm tra quyền
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Đơn hàng không tồn tại'})

    restaurant = Restaurant.query.get(order.restaurant_id)
    if restaurant.owner_id != current_user.id:
        return jsonify({'success': False, 'message': 'Không có quyền thực hiện'})

    # Cập nhật trạng thái
    success = OrderDAO.update_order_status(order_id, status)
    if success:
        return jsonify({'success': True, 'message': 'Cập nhật trạng thái thành công'})
    else:
        return jsonify({'success': False, 'message': 'Không thể chuyển sang trạng thái này'})


##33##
@owner_bp.route('/statistics')
def owner_statistics():
    return render_template('owner/statistics.html')
