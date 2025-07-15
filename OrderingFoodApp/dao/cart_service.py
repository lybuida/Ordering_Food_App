#cart_service.py
from flask import session
from OrderingFoodApp.models import MenuItem


def init_cart():
    """Khởi tạo giỏ hàng nếu chưa có"""
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']


def update_cart(action, item_id, quantity=None):
    """Cập nhật giỏ hàng theo action"""
    cart = init_cart()
    item_id = str(item_id)

    if action == 'add':
        current_quantity = cart.get(item_id, 0)
        cart[item_id] = current_quantity + (quantity or 1)
    elif action == 'increase':
        cart[item_id] = cart.get(item_id, 0) + 1
    elif action == 'decrease':
        if cart.get(item_id, 0) > 1:
            cart[item_id] -= 1
        else:
            cart.pop(item_id, None)
    elif action == 'remove':
        cart.pop(item_id, None)

    session['cart'] = cart
    return cart


def get_cart_items():
    """Trả về danh sách món trong giỏ hàng + tổng tiền"""
    cart = init_cart()
    items = []
    total_price = 0

    for item_id, quantity in cart.items():
        menu_item = MenuItem.query.get(int(item_id))
        if menu_item:
            restaurant = menu_item.restaurant
            subtotal = float(menu_item.price) * quantity
            total_price += subtotal
            items.append({
                'id': menu_item.id,
                'name': menu_item.name,
                'price': float(menu_item.price),
                'quantity': quantity,
                'subtotal': subtotal,
                'restaurant_name': restaurant.name,
                'image_url': menu_item.image_url
            })
    return items, total_price


def group_items_by_restaurant(items):
    """Nhóm món theo nhà hàng"""
    grouped = {}
    for item in items:
        grouped.setdefault(item['restaurant_name'], []).append(item)
    return grouped
