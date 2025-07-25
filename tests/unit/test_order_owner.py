import pytest
from datetime import datetime, timedelta
from OrderingFoodApp.dao import order_owner as dao
from OrderingFoodApp.models import User, Restaurant, Order, OrderItem, OrderStatus, RestaurantApprovalStatus, UserRole
from OrderingFoodApp import db


@pytest.fixture
def seed_order_data(app):
    """Fixture để tạo dữ liệu test cho đơn hàng"""
    with app.app_context():
        # Tạo user owner và customer
        owner = User(id=1, name="Owner Test", email="owner@test.com", password="p", role=UserRole.OWNER)
        customer = User(id=2, name="Customer Test", email="customer@test.com", password="p", role=UserRole.CUSTOMER)
        db.session.add_all([owner, customer])
        db.session.commit()

        # Tạo nhà hàng đã được duyệt
        restaurant = Restaurant(
            id=10,
            owner_id=1,
            name="Test Restaurant",
            approval_status=RestaurantApprovalStatus.APPROVED
        )
        db.session.add(restaurant)
        db.session.commit()

        # Tạo đơn hàng
        order = Order(
            id=100,
            customer_id=2,
            restaurant_id=10,
            total_amount=100000,
            status=OrderStatus.PENDING,
            created_at=datetime.now() - timedelta(days=1))
        db.session.add(order)

        # Tạo order items
        order_item = OrderItem(
            order_id=100,
            menu_item_id=1,
            quantity=2,
            price=50000
        )
        db.session.add(order_item)
        db.session.commit()


def test_get_orders_by_owner(app, seed_order_data):
    with app.app_context():
        # Test lấy tất cả đơn hàng
        result = dao.OrderDAO.get_orders_by_owner(1)
        assert len(result['orders']) == 1
        assert result['orders'][0]['code'] == "#000100"
        assert result['orders'][0]['status_display'] == "Chờ xác nhận"

        # Test lọc theo status
        result = dao.OrderDAO.get_orders_by_owner(1, status=OrderStatus.PENDING)
        assert len(result['orders']) == 1

        result = dao.OrderDAO.get_orders_by_owner(1, status=OrderStatus.COMPLETED)
        assert len(result['orders']) == 0

        # Test lọc theo ngày
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        result = dao.OrderDAO.get_orders_by_owner(
            1,
            start_date=yesterday.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d')
        )
        assert len(result['orders']) == 1

        # Test lọc theo branch
        result = dao.OrderDAO.get_orders_by_owner(1, branch_id=10)
        assert len(result['orders']) == 1

        result = dao.OrderDAO.get_orders_by_owner(1, branch_id=99)
        assert len(result['orders']) == 0


def test_get_order_details(app, seed_order_data):
    with app.app_context():
        order = dao.OrderDAO.get_order_details(100)
        assert order is not None
        assert order['code'] == "#000100"
        assert len(order['items']) == 1
        assert order['items'][0]['total'] == 100000


def test_update_order_status(app, seed_order_data):
    with app.app_context():
        # Test chuyển từ pending -> confirmed
        success = dao.OrderDAO.update_order_status(100, OrderStatus.CONFIRMED)
        assert success is True

        order = Order.query.get(100)
        assert order.status == OrderStatus.CONFIRMED

        # Test chuyển không hợp lệ (confirmed -> completed)
        success = dao.OrderDAO.update_order_status(100, OrderStatus.COMPLETED)
        assert success is False

        # Test chuyển hợp lệ (confirmed -> preparing)
        success = dao.OrderDAO.update_order_status(100, OrderStatus.PREPARING)
        assert success is True

        # Test chuyển hợp lệ (preparing -> delivered)
        success = dao.OrderDAO.update_order_status(100, OrderStatus.DELIVERED)
        assert success is True

        # Test chuyển hợp lệ (delivered -> completed)
        success = dao.OrderDAO.update_order_status(100, OrderStatus.COMPLETED)
        assert success is True


