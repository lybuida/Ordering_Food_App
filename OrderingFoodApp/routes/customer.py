# customer.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, current_user
from OrderingFoodApp.models import *
from OrderingFoodApp.dao import customer_service as dao

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')


@customer_bp.route('/')
@login_required
def index():
    customer = User.query.filter_by(id=current_user.id).first()
    return render_template('customer/index.html', user=customer)


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

    # Truyền dữ liệu phù hợp với loại tìm kiếm
    if search_type == 'dishes':
        return render_template('customer/restaurants_list.html',
                               menu_items=menu_items,
                               categories=categories,
                               search_query=search_query,
                               search_type=search_type,
                               selected_category_id=category_id,
                               pagination=pagination_info)
    else:
        return render_template('customer/restaurants_list.html',
                               restaurants=restaurants,
                               categories=categories,
                               search_query=search_query,
                               search_type=search_type,
                               selected_category_id=category_id,
                               pagination=pagination_info)


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
@customer_bp.route('/cart', methods=['GET', 'POST'])
def cart():
    # Khởi tạo giỏ hàng nếu chưa có
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    if request.method == 'POST':
        action = request.form.get('action')
        item_id = request.form.get('item_id')
        if not item_id:
            return redirect(url_for('customer.cart'))

        item_id = str(item_id)

        # Xử lý các hành động giỏ hàng
        if action == 'add':
            quantity = int(request.form.get('quantity', 1))
            current_quantity = cart.get(item_id, 0)
            cart[item_id] = current_quantity + quantity
            flash(f'Đã thêm {quantity} x {dao.get_menu_item_by_id(int(item_id)).name} vào giỏ hàng!',
                  'success')
        elif action == 'increase':
            cart[item_id] += 1
        elif action == 'decrease':
            if cart[item_id] > 1:
                cart[item_id] -= 1
            else:
                del cart[item_id]  # Xóa nếu số lượng giảm về 0
        elif action == 'remove':
            cart.pop(item_id, None)

        session['cart'] = cart
        return redirect(url_for('customer.cart'))

    # Lấy thông tin món ăn từ DAO để hiển thị giỏ hàng
    items = []
    total_price = 0
    for item_id, quantity in cart.items():
        menu_item = dao.get_menu_item_by_id(int(item_id))
        if menu_item:
            subtotal = menu_item.price * quantity
            total_price += subtotal
            items.append({
                'id': menu_item.id,
                'name': menu_item.name,
                'price': menu_item.price,
                'quantity': quantity,
                'subtotal': subtotal
            })

    return render_template('customer/cart.html', items=items, total_price=total_price)
