# owner.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from OrderingFoodApp.models import *
from OrderingFoodApp.dao.order_owner import OrderDAO
from flask import flash
from werkzeug.utils import secure_filename
import os
from OrderingFoodApp.dao.menu_owner import MenuDAO
from flask import current_app

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


@owner_bp.route('/')
@login_required
def index():
    owner = User.query.filter_by(id=current_user.id).first()
    return render_template('owner/index.html', user=owner)


@owner_bp.route('/restaurants')
def owner_restaurants():
    return render_template('owner/restaurants.html')

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
    restaurant = Restaurant.query.get(order['restaurant_id']) # Truy cập như dictionary
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


@owner_bp.route('/statistics')
def owner_statistics():
    return render_template('owner/statistics.html')



