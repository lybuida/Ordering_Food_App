# customer.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from OrderingFoodApp.models import DiscountType

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

    # total_pages = (data['total'] + per_page - 1) // per_page

    # THÊM KIỂM TRA KHI KHÔNG CÓ DỮ LIỆU
    if data['total'] == 0:
        total_pages = 0
    else:
        total_pages = (data['total'] + per_page - 1) // per_page

    # # Tính toán start_page và end_page
    # start_page = max(1, page - 2)
    # end_page = min(total_pages, page + 2)

    # Tính toán start_page và end_page CHỈ KHI CÓ TRANG
    if total_pages > 0:
        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)

        # Điều chỉnh nếu khoảng trang < 5
        if end_page - start_page < 4:
            if start_page == 1:
                end_page = min(total_pages, start_page + 4)
            else:
                start_page = max(1, end_page - 4)
    else:
        start_page = end_page = 0

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
        action = request.form.get('action')
        item_id = request.form.get('item_id')
        qty = request.form.get('quantity', 1, type=int)

        # AJAX?
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            new_cart = cart_dao.update_cart(action, item_id, qty)
            menu_item = MenuItem.query.get(int(item_id))
            quantity = new_cart.get(str(item_id), 0)
            subtotal = float(menu_item.price) * quantity
            return jsonify({'quantity': quantity, 'subtotal': subtotal})

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


@customer_bp.route('/orders')
@login_required
def orders_history():
    # Chỉ lấy đơn hàng của người dùng hiện tại (current_user.id)
    orders = dao.get_orders_history(current_user.id)
    return render_template('customer/orders_history.html', orders=orders)


@customer_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    # Lấy chi tiết đơn hàng và kiểm tra xem đơn hàng có thuộc về người dùng hiện tại không
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()

    # Lấy các món trong đơn hàng
    order_items = OrderItem.query.filter_by(order_id=order_id) \
        .join(MenuItem) \
        .all()

    # Lấy thông tin thanh toán nếu có
    payment = Payment.query.filter_by(order_id=order_id).first()

    return render_template('customer/orders_history_detail.html',
                           order=order,
                           order_items=order_items,
                           payment=payment)

@customer_bp.route('/restaurant/<int:restaurant_id>/reviews')
@login_required
def restaurant_reviews(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    reviews = restaurant.reviews  # tất cả reviews đã load sẵn quan hệ ORM
    return render_template('customer/restaurant_reviews.html',
                           restaurant=restaurant,
                           reviews=reviews)


#Đặc hàng
@customer_bp.route('/process_checkout', methods=['POST'])
@login_required
def checkout():
    # Lấy danh sách các món được chọn từ form
    selected_items = request.form.getlist('selected_items')

    # Lấy thông tin giỏ hàng từ session
    cart = session.get('cart', {})

    # Tạo danh sách các món hàng được chọn với thông tin đầy đủ
    selected_items_info = []
    total_price = 0
    for item_id in selected_items:
        if item_id in cart:
            menu_item = MenuItem.query.get(int(item_id))
            if menu_item:
                quantity = cart[item_id]
                subtotal = float(menu_item.price) * quantity
                total_price += subtotal
                selected_items_info.append({
                    'id': menu_item.id,
                    'name': menu_item.name,
                    'price': float(menu_item.price),
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'restaurant': menu_item.restaurant.name,
                    'image_url': menu_item.image_url
                })

    # Nhóm các món theo nhà hàng
    grouped_items = {}
    for item in selected_items_info:
        grouped_items.setdefault(item['restaurant'], []).append(item)

    # Lưu dữ liệu vào session để sử dụng trong trang GET checkout
    session['checkout_data'] = {
        'grouped_items': grouped_items,
        'total_price': total_price
    }

    return redirect(url_for('customer.checkout_page'))


@customer_bp.route('/place_order', methods=['POST'])
@login_required
def place_order():
    try:
        # Lấy phương thức thanh toán từ request
        data = request.json
        payment_method_value = data.get('payment_method', 'cash_on_delivery')
        applied_promo = data.get('applied_promo')  # Lấy thông tin mã giảm giá đã áp dụng

        payment_method = PaymentMethod(payment_method_value)

        # Lấy dữ liệu từ session
        checkout_data = session.get('checkout_data', {})
        if not checkout_data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu thanh toán'}), 400

        grouped_items = checkout_data['grouped_items']
        total_amount = checkout_data['total_price']

        # Lấy restaurant_id từ món đầu tiên
        first_restaurant = next(iter(grouped_items.keys()))
        first_item = grouped_items[first_restaurant][0]
        menu_item = MenuItem.query.get(first_item['id'])
        restaurant_id = menu_item.restaurant_id

        # Xử lý mã giảm giá nếu có
        promo_id = None
        if applied_promo:
            promo = PromoCode.query.filter_by(code=applied_promo['code']).first()
            if promo:
                promo_id = promo.id
                total_amount = applied_promo['final_amount']  # Sử dụng tổng sau giảm giá

        # Tạo đơn hàng với mã giảm giá
        new_order = Order(
            customer_id=current_user.id,
            restaurant_id=restaurant_id,
            promo_code_id=promo_id,  # Thêm mã giảm giá
            total_amount=total_amount,  # Sử dụng tổng sau giảm giá
            status=OrderStatus.PENDING
        )
        db.session.add(new_order)
        db.session.flush()

        # Thêm các món vào đơn hàng
        for restaurant, items in grouped_items.items():
            for item in items:
                menu_item = MenuItem.query.get(item['id'])
                order_item = OrderItem(
                    order_id=new_order.id,
                    menu_item_id=menu_item.id,
                    quantity=item['quantity'],
                    price=menu_item.price
                )
                db.session.add(order_item)

        # Tạo thanh toán
        payment = Payment(
            order_id=new_order.id,
            amount=total_amount,
            method=payment_method,
            status=PaymentStatus.PENDING
        )
        db.session.add(payment)

        # Xóa các món đã đặt khỏi giỏ hàng
        cart = session.get('cart', {})
        for restaurant, items in grouped_items.items():
            for item in items:
                item_id_str = str(item['id'])
                if item_id_str in cart:
                    del cart[item_id_str]

        # Cập nhật lại giỏ hàng
        session['cart'] = cart
        session.pop('checkout_data', None)

        db.session.commit()

        # Tạo thông báo
        notification = Notification(
            user_id=current_user.id,
            order_id=new_order.id,
            type=NotificationType.ORDER_STATUS,
            message=f"Đơn hàng #{new_order.id} đã được đặt thành công.",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({
            'success': True,
            'order_id': new_order.id,
            'message': 'Đặt hàng thành công!',
            'redirect_url': url_for('customer.current_orders')
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }), 500


# customer.py - Thêm route GET cho checkout
@customer_bp.route('/checkout', methods=['GET'])
@login_required
def checkout_page():
    # Lấy thông tin từ session
    checkout_data = session.get('checkout_data', {})

    if not checkout_data:
        flash('Không có dữ liệu thanh toán', 'error')
        return redirect(url_for('customer.cart'))

    return render_template('customer/checkout.html',
                           grouped_items=checkout_data['grouped_items'],
                           total_price=checkout_data['total_price'],
                           DiscountType=DiscountType)


@customer_bp.route('/current_orders')
@login_required
def current_orders():
    # Lấy các đơn hàng chưa hoàn thành của khách hàng hiện tại
    orders = Order.query.filter(
        Order.customer_id == current_user.id,
        Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING])
    ).options(
        db.joinedload(Order.restaurant),
        db.joinedload(Order.order_items).joinedload(OrderItem.menu_item)
    ).order_by(Order.created_at.desc()).all()

    # Tạo dictionary để lưu trữ chi tiết từng đơn hàng
    orders_details = {}
    status_colors = {
        OrderStatus.PENDING: 'bg-warning text-dark',
        OrderStatus.CONFIRMED: 'bg-info text-white',
        OrderStatus.PREPARING: 'bg-primary text-white',
        OrderStatus.COMPLETED: 'bg-success text-white',
        OrderStatus.CANCELLED: 'bg-danger text-white'
    }

    for order in orders:
        # Lấy các món trong đơn hàng
        order_items = OrderItem.query.filter_by(order_id=order.id).join(MenuItem).all()

        # Lấy thông tin thanh toán nếu có
        payment = Payment.query.filter_by(order_id=order.id).first()

        orders_details[order.id] = {
            'order': order,
            'order_items': order_items,
            'payment': payment,
            'status_color': status_colors.get(order.status, 'bg-secondary')
        }

    return render_template('customer/current_orders.html',
                           orders=orders,
                           orders_details=orders_details,
                           PaymentStatus=PaymentStatus,
                           OrderStatus=OrderStatus,
                           DiscountType=DiscountType)


@customer_bp.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        order = Order.query.filter_by(
            id=order_id,
            customer_id=current_user.id,
            status=OrderStatus.PENDING
        ).first_or_404()

        order.status = OrderStatus.CANCELLED
        db.session.commit()

        # Tạo thông báo
        notification = Notification(
            user_id=current_user.id,
            order_id=order.id,
            type=NotificationType.ORDER_STATUS,
            message=f"Đơn hàng #{order.id} đã được hủy.",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Đã hủy đơn hàng thành công'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }), 500


@customer_bp.route('/promo_codes')
@login_required
def get_promo_codes():
    try:
        current_time = datetime.now()
        promos = PromoCode.query.filter(
            PromoCode.start_date <= current_time,
            PromoCode.end_date >= current_time
        ).all()

        promos_data = []
        for promo in promos:
            promos_data.append({
                'id': promo.id,
                'code': promo.code,
                'description': promo.description,
                'discount_type': promo.discount_type.value,
                'discount_value': float(promo.discount_value),
                'start_date': promo.start_date.isoformat(),
                'end_date': promo.end_date.isoformat(),
                'usage_limit': promo.usage_limit,
                'image_url': promo.image_url
            })

        return jsonify({'promos': promos_data})

    except Exception as e:
        app.logger.error(f'Lỗi khi lấy mã giảm giá: {str(e)}')
        return jsonify({'promos': [], 'error': str(e)}), 500


@customer_bp.route('/apply_promo', methods=['POST'])
@login_required
def apply_promo():
    data = request.get_json()
    promo_code = data.get('promo_code')
    total_price = float(data.get('total_price', 0))

    # Tìm mã giảm giá
    promo = PromoCode.query.filter_by(code=promo_code).first()
    if not promo:
        return jsonify({'success': False, 'message': 'Mã giảm giá không tồn tại'}), 400

    current_time = datetime.now()
    if current_time < promo.start_date or current_time > promo.end_date:
        return jsonify({'success': False, 'message': 'Mã giảm giá đã hết hạn'}), 400

    # Tính toán số tiền giảm
    # CHUYỂN ĐỔI Decimal SANG FLOAT TRƯỚC KHI TÍNH TOÁN
    discount_value = float(promo.discount_value)

    if promo.discount_type == DiscountType.PERCENT:
        discount_amount = total_price * (discount_value / 100)
    else:  # FIXED
        discount_amount = discount_value

    # Đảm bảo không giảm quá tổng tiền
    if discount_amount > total_price:
        discount_amount = total_price

    final_amount = total_price - discount_amount

    return jsonify({
        'success': True,
        'message': 'Áp dụng mã giảm giá thành công',
        'discount_amount': discount_amount,
        'final_amount': final_amount
    })