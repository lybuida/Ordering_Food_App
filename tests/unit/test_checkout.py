import pytest
from OrderingFoodApp import db
from OrderingFoodApp.models import *
from OrderingFoodApp.dao import customer_service as dao
from flask import session
from datetime import datetime, timedelta


@pytest.fixture
def ctx(app):
    with app.test_request_context():
        yield

# Test for apply_promo function
def test_apply_promo_valid_percent(app):
    with app.app_context():
        # Create test data
        promo = PromoCode(
            code='SALE10',
            description='Giảm 10%',
            discount_type=DiscountType.PERCENT,
            discount_value=10,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1),
            usage_limit=100
        )
        db.session.add(promo)
        db.session.commit()

        # Test valid percent discount
        result = dao.apply_promo('SALE10', 100000)
        assert result['success'] is True
        assert result['discount_amount'] == 10000
        assert result['final_amount'] == 90000

def test_apply_promo_valid_fixed(app):
    with app.app_context():
        # Create test data
        promo = PromoCode(
            code='FIXED50',
            description='Giảm 50,000 đ',
            discount_type=DiscountType.FIXED,
            discount_value=50000,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1),
            usage_limit=100
        )
        db.session.add(promo)
        db.session.commit()

        # Test valid fixed discount
        result = dao.apply_promo('FIXED50', 100000)
        assert result['success'] is True
        assert result['discount_amount'] == 50000
        assert result['final_amount'] == 50000

def test_apply_promo_expired(app):
    with app.app_context():
        # Create expired promo
        promo = PromoCode(
            code='EXPIRED',
            description='Mã hết hạn',
            discount_type=DiscountType.PERCENT,
            discount_value=10,
            start_date=datetime.now() - timedelta(days=10),
            end_date=datetime.now() - timedelta(days=1),
            usage_limit=100
        )
        db.session.add(promo)
        db.session.commit()

        # Test expired promo
        result = dao.apply_promo('EXPIRED', 100000)
        assert result['success'] is False
        assert 'hết hạn' in result['message']

def test_apply_promo_not_found(app):
    with app.app_context():  # THÊM VÀO
        # Test non-existent promo
        result = dao.apply_promo('NOTEXIST', 100000)
        assert result['success'] is False
        assert 'không tồn tại' in result['message']

# Test for place_order function
def test_place_order_success(app):
    with app.app_context():
        # Create test data - COMMIT USER FIRST
        user = User(name='Test User', email='test@example.com', password='password', role=UserRole.CUSTOMER)
        db.session.add(user)
        db.session.commit()  # Commit để có user.id

        restaurant = Restaurant(name='Test Restaurant', owner_id=user.id, address='Test Address')
        db.session.add(restaurant)

        # THÊM TRƯỚC KHI TẠO MENU_ITEM
        category = MenuCategory(name="Test Category")
        db.session.add(category)
        db.session.flush()

        menu_item = MenuItem(
            restaurant=restaurant,
            category_id=category.id,
            name='Test Item',
            price=50000)
        db.session.add(menu_item)
        db.session.commit()

        # Set session data
        with app.test_request_context():
            session['checkout_data'] = {
                'grouped_items': {
                    'Test Restaurant': [{
                        'id': menu_item.id,
                        'name': 'Test Item',
                        'price': 50000,
                        'quantity': 2,
                        'subtotal': 100000,
                        'restaurant': 'Test Restaurant',
                        'image_url': None
                    }]
                },
                'total_price': 100000
            }

            # Test successful order placement
            order_data = {
                'payment_method': 'cash_on_delivery',
                'applied_promo': None
            }

            # Place order
            response = dao.place_order(user.id, order_data, session['checkout_data'])
            assert response['success'] is True

            # Verify order in database
            order = Order.query.first()
            assert order is not None
            assert order.customer_id == user.id
            assert order.restaurant_id == restaurant.id
            assert order.total_amount == 100000
            assert order.status == OrderStatus.PENDING

            # Verify order items
            order_items = OrderItem.query.all()
            assert len(order_items) == 1
            assert order_items[0].menu_item_id == menu_item.id
            assert order_items[0].quantity == 2

            # Verify payment
            payment = Payment.query.first()
            assert payment.order_id == order.id
            assert payment.amount == 100000
            assert payment.method == PaymentMethod.CASH_ON_DELIVERY
            assert payment.status == PaymentStatus.PENDING

def test_place_order_with_promo(app):
    with app.app_context():
        # Create test data - COMMIT USER FIRST
        user = User(name='Test User', email='test@example.com', password='password', role=UserRole.CUSTOMER)
        db.session.add(user)
        db.session.commit()  # Commit để có user.id

        restaurant = Restaurant(
            name='Test Restaurant',
            owner_id=user.id,
            address='Test Address')
        db.session.add(restaurant)

        # THÊM TRƯỚC KHI TẠO MENU_ITEM
        category = MenuCategory(name="Test Category")
        db.session.add(category)
        db.session.flush()

        menu_item = MenuItem(
            restaurant=restaurant,
            category_id=category.id,  # THÊM CATEGORY_ID
            name='Test Item',
            price=50000)

        db.session.add(menu_item)
        promo = PromoCode(
            code='PROMO10',
            description='Giảm 10%',
            discount_type=DiscountType.PERCENT,
            discount_value=10,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1),
            usage_limit=100
        )
        db.session.add(promo)
        db.session.commit()

        # Set session data
        with app.test_request_context():
            session['checkout_data'] = {
                'grouped_items': {
                    'Test Restaurant': [{
                        'id': menu_item.id,
                        'name': 'Test Item',
                        'price': 50000,
                        'quantity': 2,
                        'subtotal': 100000,
                        'restaurant': 'Test Restaurant',
                        'image_url': None
                    }]
                },
                'total_price': 100000
            }

            # Test order with promo
            order_data = {
                'payment_method': 'cash_on_delivery',
                'applied_promo': {
                    'code': 'PROMO10',
                    'discount_amount': 10000,
                    'final_amount': 90000
                }
            }

            response = dao.place_order(user.id, order_data, session['checkout_data'])
            assert response['success'] is True

            # Verify order with discount
            order = Order.query.first()
            assert order.total_amount == 90000
            assert order.promo_code_id == promo.id

def test_place_order_no_checkout_data(app):
    with app.app_context():
        # Create test user
        user = User(name='Test User', email='test@example.com', password='password', role=UserRole.CUSTOMER)
        db.session.add(user)
        db.session.commit()

        # Test without checkout data
        order_data = {
            'payment_method': 'cash_on_delivery',
            'applied_promo': None
        }

        response = dao.place_order(user.id, order_data, None)
        assert response['success'] is False
        assert 'Không có dữ liệu thanh toán' in response['message']