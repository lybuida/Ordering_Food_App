# customer.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from OrderingFoodApp.models import *
from OrderingFoodApp.dao import customer_service as dao

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

# Giao diện trang chủ
@customer_bp.route('/')
@login_required
def index():
    customer = User.query.filter_by(id=current_user.id).first()

    # Lấy TẤT CẢ mã khuyến mãi còn hiệu lực (không giới hạn)
    current_time = datetime.now()
    promos = PromoCode.query.filter(
        PromoCode.start_date <= current_time,
        PromoCode.end_date >= current_time
    ).all()

    # Lấy TẤT CẢ nhà hàng có đơn hàng (không giới hạn)
    top_restaurants = db.session.query(
        Restaurant,
        func.count(Order.id).label('order_count')
    ).outerjoin(Order, Order.restaurant_id == Restaurant.id) \
        .group_by(Restaurant.id) \
        .order_by(func.count(Order.id).desc()) \
        .all()

    # Lấy TẤT CẢ món ăn bán chạy (không giới hạn)
    top_menu_items = db.session.query(
        MenuItem,
        Restaurant,
        func.sum(OrderItem.quantity).label('total_sold')
    ) \
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id) \
        .join(Restaurant, Restaurant.id == MenuItem.restaurant_id) \
        .group_by(MenuItem.id, Restaurant.id) \
        .order_by(func.sum(OrderItem.quantity).desc()) \
        .all()

    # Chuyển đổi kết quả
    featured_items = []
    for item in top_menu_items:
        menu_item = item[0]
        menu_item.restaurant = item[1]
        menu_item.total_sold = item[2] or 0
        featured_items.append(menu_item)

    return render_template('customer/index.html',
                           user=customer,
                           promos=promos,
                           top_restaurants=top_restaurants,
                           featured_items=featured_items)

@customer_bp.route('/restaurants_list')
@login_required
def restaurants_list():
    search_query = request.args.get('search', '')
    search_type = request.args.get('search_type', 'restaurants')  # Mặc định là tìm nhà hàng
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Xác định loại truy vấn
    if search_query:
        if search_type == 'dishes':
            # Tìm kiếm món ăn
            data = dao.get_menu_items_by_name(search_query, page, per_page)
            menu_items = data['menu_items']
        else:
            # Tìm kiếm NHÀ HÀNG THEO TÊN (sử dụng hàm mới)
            data = dao.get_restaurants_by_name(search_query, page, per_page)
            restaurants = data['restaurants']
    elif category_id:
        # Tìm theo danh mục (chỉ áp dụng cho nhà hàng)
        data = dao.get_restaurants_by_category(category_id, page, per_page)
        restaurants = data['restaurants']
        search_type = 'restaurants'  # Đảm bảo hiển thị đúng loại
    else:
        data = dao.get_all_restaurants(page, per_page)
        restaurants = data['restaurants']
        search_type = 'restaurants'  # Đảm bảo hiển thị đúng loại

    categories = MenuCategory.query.all()

    total_pages = (data['total'] + per_page - 1) // per_page

    # Tính toán start_page và end_page
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    # Nếu số trang ít hơn 5, điều chỉnh để hiển thị đủ
    if end_page - start_page < 4:
        if start_page == 1:
            end_page = min(total_pages, start_page + 4)
        else:
            start_page = max(1, end_page - 4)

    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': data['total'],
        'total_pages': total_pages,
        'start_page': start_page,
        'end_page': end_page
    }

    # Lấy danh sách mã khuyến mãi còn hiệu lực
    current_time = datetime.now()
    promos = PromoCode.query.filter(
        PromoCode.start_date <= current_time,
        PromoCode.end_date >= current_time
    ).limit(5).all()

    # Truyền dữ liệu phù hợp với loại tìm kiếm
    if search_type == 'dishes':
        return render_template('customer/restaurants_list.html',
                               menu_items=menu_items,
                               categories=categories,
                               search_query=search_query,
                               search_type=search_type,
                               selected_category_id=category_id,
                               pagination=pagination_info,
                               promos=promos)
    else:
        return render_template('customer/restaurants_list.html',
                               restaurants=restaurants,
                               categories=categories,
                               search_query=search_query,
                               search_type=search_type,
                               selected_category_id=category_id,
                               pagination=pagination_info,
                               promos=promos)

#Xem menu nhà hàng
@customer_bp.route('/restaurant/<int:restaurant_id>')
@login_required
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template('customer/restaurant_detail.html',
                         restaurant=restaurant,
                         menu_items=menu_items)

# Xem chi tiết món ăn
@customer_bp.route('/menu_item/<int:menu_item_id>')
@login_required
def view_menu_item(menu_item_id):
    menu_item = MenuItem.query.get_or_404(menu_item_id)
    return render_template('customer/menu_item_detail.html', menu_item=menu_item)


#Quản lý giỏ hàng
from OrderingFoodApp.dao import cart_service as cart_dao
@customer_bp.route('/cart', methods=['GET', 'POST'])
def cart():
    cart = cart_dao.init_cart()

    if request.method == 'POST':
        action  = request.form.get('action')
        item_id = request.form.get('item_id')
        if not item_id:
            return redirect(url_for('customer.cart'))
        item_id = str(item_id)

        # ——— AJAX request ———
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart_dao.update_cart(action, item_id)
            menu_item = MenuItem.query.get(int(item_id))
            quantity = cart.get(item_id, 0)
            subtotal = float(menu_item.price) * quantity
            return jsonify({'quantity': quantity, 'subtotal': subtotal})

        # ——— Form submit (bình thường) ———
        if action == 'add':
            qty = int(request.form.get('quantity', 1))
            cart_dao.update_cart(action, item_id, qty)
        else:
            cart_dao.update_cart(action, item_id)

        return redirect(url_for('customer.cart'))

    # GET → render template
    items, total_price = cart_dao.get_cart_items()
    grouped_items    = cart_dao.group_items_by_restaurant(items)
    return render_template('customer/cart.html',
                           grouped_items=grouped_items,
                           total_price=total_price)


