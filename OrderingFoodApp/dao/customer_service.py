# customer_service.py
from sqlalchemy import func
from OrderingFoodApp.models import *
from OrderingFoodApp import db
from flask import request
from datetime import datetime

# Tìm kiếm nhà hàng theo TÊN NHÀ HÀNG
def get_restaurants_by_name(search_query, page, per_page=12):
    restaurants = db.session.query(
        Restaurant,
        func.coalesce(func.avg(Review.rating), 0.0).label('avg_rating')
    ) \
        .outerjoin(Review, Review.restaurant_id == Restaurant.id) \
        .filter(Restaurant.name.ilike(f'%{search_query}%'), Restaurant.approval_status == RestaurantApprovalStatus.APPROVED) \
        .group_by(Restaurant.id) \
        .order_by(Restaurant.id) \
        .paginate(page=page, per_page=per_page)

    results = []
    for restaurant, avg_rating in restaurants.items:
        restaurant.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        results.append(restaurant)

    return {
        'restaurants': results,
        'page': page,
        'per_page': per_page,
        'total': restaurants.total
    }

# Tìm món ăn chứa từ khóa, kèm theo thông tin nhà hàng
def get_menu_items_by_name(search_query, page, per_page=12):

    menu_items = MenuItem.query \
        .join(Restaurant, MenuItem.restaurant_id == Restaurant.id) \
        .filter(MenuItem.name.ilike(f'%{search_query}%')) \
        .add_entity(Restaurant) \
        .order_by(MenuItem.id) \
        .paginate(page=page, per_page=per_page)

    # Tạo danh sách kết quả với đầy đủ thông tin
    results = []
    for item in menu_items.items:
        # item[0] là MenuItem, item[customer] là Restaurant
        menu_item = item[0]
        menu_item.restaurant = item[1]  # Gán nhà hàng cho món ăn
        results.append(menu_item)

    return {
        'menu_items': results,
        'page': page,
        'per_page': per_page,
        'total': menu_items.total
    }

# Tính điểm trung bình cho mỗi nhà hàng
def get_restaurants_by_category(category_id, page, per_page=12):
    # Tính điểm trung bình cho mỗi nhà hàng
    restaurants = db.session.query(
        Restaurant,
        func.coalesce(func.avg(Review.rating), 0.0).label('avg_rating')
    ) \
        .join(MenuItem, Restaurant.id == MenuItem.restaurant_id) \
        .outerjoin(Review, Review.restaurant_id == Restaurant.id) \
        .filter(MenuItem.category_id == category_id, Restaurant.approval_status == RestaurantApprovalStatus.APPROVED) \
        .group_by(Restaurant.id) \
        .order_by(Restaurant.id) \
        .paginate(page=page, per_page=per_page)

    # Gán điểm trung bình vào đối tượng nhà hàng
    results = []
    for restaurant, avg_rating in restaurants.items:
        restaurant.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        results.append(restaurant)

    return {
        'restaurants': results,
        'page': page,
        'per_page': per_page,
        'total': restaurants.total
    }

def get_all_restaurants(page, per_page=12):
    # Tính điểm trung bình cho mỗi nhà hàng
    restaurants = db.session.query(
        Restaurant,
        func.coalesce(func.avg(Review.rating), 0.0).label('avg_rating')
    ) \
        .filter(Restaurant.approval_status == RestaurantApprovalStatus.APPROVED)\
        .outerjoin(Review, Review.restaurant_id == Restaurant.id) \
        .group_by(Restaurant.id) \
        .order_by(Restaurant.id) \
        .paginate(page=page, per_page=per_page)

    # Gán điểm trung bình vào đối tượng nhà hàng
    results = []
    for restaurant, avg_rating in restaurants.items:
        restaurant.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        results.append(restaurant)

    return {
        'restaurants': results,
        'page': page,
        'per_page': per_page,
        'total': restaurants.total
    }

def get_menu_item_by_id(menu_item_id):
    """
    Lấy thông tin món ăn theo ID
    """
    return MenuItem.query.get(menu_item_id)


def get_orders_history(customer_id):
    """
    Lấy lịch sử đơn hàng (completed hoặc cancelled) của một khách hàng
    """
    # orders = Order.query.filter_by(customer_id=customer_id) \
    #     .filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.CANCELLED])) \
    #     .options(
    #     db.joinedload(Order.restaurant),
    #     db.joinedload(Order.order_items).joinedload(OrderItem.menu_item)
    # ) \
    #     .order_by(Order.created_at.desc()) \
    #     .all()
    #
    # # Đảm bảo mỗi order có thuộc tính order_items (ngay cả khi rỗng)
    # for order in orders:
    #     if not hasattr(order, 'order_items'):
    #         order.order_items = []
    #
    # return orders

    orders = Order.query.filter_by(customer_id=customer_id) \
        .filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.CANCELLED])) \
        .options(
        db.joinedload(Order.restaurant),
        db.joinedload(Order.order_items).joinedload(OrderItem.menu_item)
    ) \
        .order_by(Order.created_at.desc()) \
        .all()

    return orders

def apply_promo(promo_code, total_price):
    """Áp dụng mã giảm giá"""
    promo = PromoCode.query.filter_by(code=promo_code).first()
    if not promo:
        return {'success': False, 'message': 'Mã giảm giá không tồn tại'}

    current_time = datetime.now()
    if current_time < promo.start_date or current_time > promo.end_date:
        return {'success': False, 'message': 'Mã giảm giá đã hết hạn'}

    discount_value = float(promo.discount_value)
    if promo.discount_type == DiscountType.PERCENT:
        discount_amount = total_price * (discount_value / 100)
    else:  # FIXED
        discount_amount = discount_value

    # Đảm bảo không giảm quá tổng tiền
    discount_amount = min(discount_amount, total_price)
    final_amount = total_price - discount_amount

    return {
        'success': True,
        'discount_amount': discount_amount,
        'final_amount': final_amount
    }

def place_order(customer_id, order_data, checkout_data):
    """Đặt hàng"""
    if not checkout_data:
        return {'success': False, 'message': 'Không có dữ liệu thanh toán'}

    grouped_items = checkout_data['grouped_items']
    total_amount = checkout_data['total_price']

    # Lấy restaurant_id từ món đầu tiên
    first_restaurant = next(iter(grouped_items.keys()))
    first_item = grouped_items[first_restaurant][0]
    menu_item = MenuItem.query.get(first_item['id'])
    restaurant_id = menu_item.restaurant_id

    # Xử lý mã giảm giá nếu có
    promo_id = None
    if order_data.get('applied_promo'):
        promo = PromoCode.query.filter_by(code=order_data['applied_promo']['code']).first()
        if promo:
            promo_id = promo.id
            total_amount = order_data['applied_promo']['final_amount']

    # Tạo đơn hàng
    new_order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        promo_code_id=promo_id,
        total_amount=total_amount,
        status=OrderStatus.PENDING
    )
    db.session.add(new_order)
    db.session.flush()

    # Thêm các món vào đơn hàng
    for restaurant, items in grouped_items.items():
        for item in items:
            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)

    # Tạo thanh toán
    payment = Payment(
        order_id=new_order.id,
        amount=total_amount,
        method=PaymentMethod(order_data['payment_method']),
        status=PaymentStatus.PENDING
    )
    db.session.add(payment)
    db.session.commit()

    return {
        'success': True,
        'order_id': new_order.id
    }