import pytest

from OrderingFoodApp import db
from OrderingFoodApp.models import User, UserRole, Restaurant, MenuCategory, MenuItem, Order, OrderStatus, \
    RestaurantApprovalStatus


@pytest.fixture
def seed_owner_data(app):
    """Fixture để tạo dữ liệu test cho owner"""
    with app.app_context():
        # Tạo user owner
        owner = User(id=1, name="Owner Test", email="owner@test.com", password="p", role=UserRole.OWNER)
        db.session.add(owner)
        db.session.commit()

        # Tạo nhà hàng
        restaurant = Restaurant(
            id=10,
            owner_id=1,
            name="Test Restaurant",
            approval_status=RestaurantApprovalStatus.APPROVED
        )
        db.session.add(restaurant)

        # Tạo danh mục
        category = MenuCategory(id=1, name="Test Category")
        db.session.add(category)

        # Tạo món ăn
        menu_item = MenuItem(
            id=101,
            restaurant_id=10,
            category_id=1,
            name="Test Item",
            price=50000,
            is_active=True
        )
        db.session.add(menu_item)

        # Tạo đơn hàng
        order = Order(
            id=100,
            customer_id=2,
            restaurant_id=10,
            total_amount=100000,
            status=OrderStatus.PENDING
        )
        db.session.add(order)
        db.session.commit()


def test_owner_restaurants_page(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    resp = client.get('/owner/restaurants')
    assert resp.status_code == 200
    assert b"Test Restaurant" in resp.data


def test_add_restaurant(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    # Test GET
    resp = client.get('/owner/restaurants/add')
    assert resp.status_code == 200

    # Test POST
    resp = client.post('/owner/restaurants/add', data={
        'name': 'New Restaurant',
        'description': 'New Description',
        'address': '123 New Address',
        'phone': '112233',
        'opening_time': '08:00',
        'closing_time': '22:00',
        'latitude': '10.5',
        'longitude': '106.5'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"New Restaurant" in resp.data


def test_edit_restaurant(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    # Test GET
    resp = client.get('/owner/restaurants/10/edit')
    assert resp.status_code == 200
    assert b"Test Restaurant" in resp.data

    # Test POST
    resp = client.post('/owner/restaurants/10/edit', data={
        'name': 'Updated Restaurant',
        'description': 'Updated Description',
        'address': '456 Updated Address',
        'phone': '445566',
        'opening_time': '09:00',
        'closing_time': '21:00',
        'latitude': '10.6',
        'longitude': '106.6'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Updated Restaurant" in resp.data


def test_owner_orders_page(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    resp = client.get('/owner/orders')
    assert resp.status_code == 200
    assert b"#000100" in resp.data


def test_order_details_page(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    resp = client.get('/owner/orders/100')
    assert resp.status_code == 200
    assert b"#000100" in resp.data
    assert b"Test Restaurant" in resp.data


def test_update_order_status(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    # Test update status to confirmed
    resp = client.post('/owner/orders/100/update-status', data={
        'status': 'confirmed'
    })

    assert resp.status_code == 200
    assert resp.json['success'] is True

    # Verify status changed
    resp = client.get('/owner/orders/100')
    assert b"Đã xác nhận" in resp.data


def test_owner_menu_page(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    resp = client.get('/owner/menu?restaurant_id=10')
    assert resp.status_code == 200
    assert b"Test Item" in resp.data


def test_toggle_menu_item_status(client, seed_owner_data):
    # Login as owner
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    # Test toggle status
    resp = client.post('/owner/menu/101/toggle-status',
                       headers={'X-Requested-With': 'XMLHttpRequest'})

    assert resp.status_code == 200
    assert resp.json['success'] is True

    # Verify status changed
    resp = client.get('/owner/menu?restaurant_id=10')
    assert b"Tạm ngừng" in resp.data