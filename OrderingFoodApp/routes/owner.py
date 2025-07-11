# owner.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from OrderingFoodApp.models import *
from OrderingFoodApp.dao.order_dao import OrderDAO

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')


@owner_bp.route('/')
@login_required
def index():
    owner = User.query.filter_by(id=current_user.id).first()
    return render_template('owner/index.html', user=owner)


@owner_bp.route('/restaurants')
def owner_restaurants():
    return render_template('owner/restaurants.html')


@owner_bp.route('/menu')
def owner_menu():
    return render_template('owner/menu.html')


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