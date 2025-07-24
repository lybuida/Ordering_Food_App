# tests/test_checkout_api.py
import pytest
from OrderingFoodApp import db
from OrderingFoodApp.models import (User, UserRole, Restaurant, MenuCategory,
                                    MenuItem, Order, OrderItem, Payment,
                                    OrderStatus, PaymentMethod, PaymentStatus)


@pytest.fixture
def seed_checkout_data(app):
    """
    Fixture để tạo dữ liệu cần thiết cho việc test checkout:
    - 1 khách hàng (customer)
    - 1 chủ quán (owner)
    - 1 nhà hàng
    - 2 món ăn trong nhà hàng đó
    """
    with app.app_context():
        # Tạo user customer và owner
        customer = User(id=5, name="Customer Test", email="customer@test.com", password="p", role=UserRole.CUSTOMER)
        owner = User(id=6, name="Owner Test", email="owner@test.com", password="p", role=UserRole.OWNER)

        # Tạo danh mục và nhà hàng
        category = MenuCategory(id=1, name="Món chính")
        restaurant = Restaurant(id=10, owner_id=6, name="Nhà hàng Test", address="123 Test", phone="112233")

        # Tạo các món ăn
        menu_item1 = MenuItem(id=101, restaurant_id=10, category_id=1,
                              name="Cơm tấm", description="Cơm tấm sườn bì chả", price=50000.00)
        menu_item2 = MenuItem(id=102, restaurant_id=10, category_id=1,
                              name="Phở bò", description="Phở bò tái", price=45000.00)

        db.session.add_all([customer, owner, category, restaurant, menu_item1, menu_item2])
        db.session.commit()


@pytest.mark.usefixtures("seed_checkout_data")
def test_place_order_cash_on_delivery_success(client, app):  # Thêm app vào fixture
    # 1. Giả lập login và thêm hàng vào giỏ (session)
    with client.session_transaction() as sess:
        sess['_user_id'] = '5'
        sess['_fresh'] = True
        sess['checkout_data'] = {
            'grouped_items': {
                'Nhà hàng Test': [
                    {'id': 101, 'name': 'Cơm tấm', 'price': 50000.00, 'quantity': 2, 'subtotal': 100000.00},
                    {'id': 102, 'name': 'Phở bò', 'price': 45000.00, 'quantity': 1, 'subtotal': 45000.00}
                ]
            },
            'total_price': 145000.00
        }
        sess['cart'] = {'101': 2, '102': 1}

    # 2. Gửi request POST
    payload = {
        'payment_method': 'cash_on_delivery',
        'applied_promo': None
    }
    resp = client.post('/customer/place_order', json=payload)

    # 3. Kiểm tra response
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'order_id' in data
    assert data['message'] == 'Đặt hàng thành công!'

    # 4. Kiểm tra database trong app context
    order_id = data['order_id']
    with app.app_context():  # Thêm app context
        order = Order.query.get(order_id)
        assert order is not None
        assert order.customer_id == 5
        assert order.restaurant_id == 10
        assert float(order.total_amount) == 145000.00
        assert order.status == OrderStatus.PENDING

        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        assert len(order_items) == 2

        payment = Payment.query.filter_by(order_id=order_id).first()
        assert payment is not None
        assert payment.method == PaymentMethod.CASH_ON_DELIVERY
        assert payment.status == PaymentStatus.PENDING
        assert float(payment.amount) == 145000.00

    # 5. Kiểm tra session
    with client.session_transaction() as sess:
        assert 'checkout_data' not in sess
        assert sess.get('cart') == {}

@pytest.mark.usefixtures("seed_checkout_data")
def test_place_order_fails_without_checkout_data(client, app):  # Thêm app vào fixture
    # 1. Giả lập login không có checkout_data
    with client.session_transaction() as sess:
        sess['_user_id'] = '5'
        sess['_fresh'] = True

    # 2. Gửi request POST
    payload = {
        'payment_method': 'cash_on_delivery',
        'applied_promo': None
    }
    resp = client.post('/customer/place_order', json=payload)

    # 3. Kiểm tra response
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert data['message'] == 'Không có dữ liệu thanh toán'

    # 4. Kiểm tra database trong app context
    with app.app_context():  # Thêm app context
        assert Order.query.count() == 0
        assert OrderItem.query.count() == 0
        assert Payment.query.count() == 0