# tests/integration/test_orders_api.py
import pytest
from flask import url_for, session

from OrderingFoodApp import db
from OrderingFoodApp.models import User, Restaurant, Order, OrderStatus, OrderItem, MenuItem
from datetime import datetime, timedelta


@pytest.fixture
def seed_order_data(app):
    """Fixture để tạo dữ liệu test cho đơn hàng"""
    with app.app_context():
        # Tạo user owner
        owner = User(
            id=1,
            name="Owner",
            email="owner@test.com",
            password="password",
            role="owner"
        )

        # Tạo user customer
        customer = User(
            id=2,
            name="Customer",
            email="customer@test.com",
            password="password",
            role="customer"
        )

        # Tạo nhà hàng
        restaurant = Restaurant(
            id=1,
            owner_id=1,
            name="Test Restaurant",
            address="123 Test St",
            phone="0123456789",
            approval_status="approved"
        )

        # Tạo menu item
        menu_item = MenuItem(
            id=1,
            restaurant_id=1,
            category_id=1,
            name="Test Item",
            price=100000,
            is_active=True
        )

        # Tạo đơn hàng
        order = Order(
            id=1,
            customer_id=2,
            restaurant_id=1,
            total_amount=200000,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow()
        )

        # Tạo order item
        order_item = OrderItem(
            order_id=1,
            menu_item_id=1,
            quantity=2,
            price=100000
        )

        db.session.add_all([owner, customer, restaurant, menu_item, order, order_item])
        db.session.commit()

@pytest.mark.usefixtures("client", "seed_order_data")
class TestOrderAPI:
    def test_get_orders_page(self, client):
        """Test truy cập trang quản lý đơn hàng"""
        # Login với tư cách owner
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        response = client.get('/owner/orders')
        assert response.status_code == 200
        assert "Quản lý Đơn Hàng" in response.data.decode('utf-8')

    def test_order_details_page(self, client):
        """Test xem chi tiết đơn hàng"""
        # Login với tư cách owner
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        response = client.get('/owner/orders/1')
        assert response.status_code == 200
        assert "Chi tiết đơn hàng" in response.data.decode('utf-8')

    def test_update_order_status(self, client):
        """Test cập nhật trạng thái đơn hàng"""
        # Login với tư cách owner
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        # Test xác nhận đơn hàng
        response = client.post(
            '/owner/orders/1/update-status',
            data={'status': 'confirmed'},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert "Đã xác nhận đơn hàng" in response.data.decode('utf-8')

    def test_cancel_order_with_reason(self, client):
        """Test hủy đơn hàng với lý do"""
        # Login với tư cách owner
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        response = client.post(
            '/owner/orders/1/update-status',
            data={
                'status': 'cancelled',
                'rejection_reason': 'Hết nguyên liệu'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert "Đã hủy đơn hàng" in response.data.decode('utf-8')
        assert "Hết nguyên liệu" in response.data.decode('utf-8')

    def test_filter_orders(self, client):
        """Test lọc đơn hàng theo trạng thái"""
        # Login với tư cách owner
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        response = client.get('/owner/orders?status=completed')
        assert response.status_code == 200
        assert "Quản lý Đơn Hàng" in response.data.decode('utf-8')
        assert "Hoàn thành" in response.data.decode('utf-8')