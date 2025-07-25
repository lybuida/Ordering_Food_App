import pytest
from OrderingFoodApp.dao import restaurants_owner as dao
from OrderingFoodApp.models import Restaurant, RestaurantApprovalStatus, Notification, User, UserRole
from OrderingFoodApp import db
from datetime import time


@pytest.fixture
def seed_restaurant_data(app):
    """Fixture để tạo dữ liệu test cho nhà hàng"""
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
            description="Test Description",
            address="123 Test",
            phone="112233",
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            approval_status=RestaurantApprovalStatus.PENDING
        )
        db.session.add(restaurant)
        db.session.commit()


def test_get_restaurants_by_owner(app, seed_restaurant_data):
    with app.app_context():
        restaurants = dao.RestaurantDAO.get_restaurants_by_owner(1)
        assert len(restaurants) == 1
        assert restaurants[0].name == "Test Restaurant"


def test_get_restaurant_by_id(app, seed_restaurant_data):
    with app.app_context():
        # Test với quyền owner
        restaurant = dao.RestaurantDAO.get_restaurant_by_id(10, 1)
        assert restaurant is not None
        assert restaurant.name == "Test Restaurant"

        # Test không có quyền
        restaurant = dao.RestaurantDAO.get_restaurant_by_id(10, 2)  # owner_id khác
        assert restaurant is None


def test_create_restaurant(app):
    with app.app_context():
        # Tạo user owner
        owner = User(id=1, name="Owner Test", email="owner@test.com", password="p", role=UserRole.OWNER)
        db.session.add(owner)
        db.session.commit()

        restaurant = dao.RestaurantDAO.create_restaurant(
            owner_id=1,
            name="New Restaurant",
            description="New Description",
            address="456 New Address",
            phone="445566",
            opening_time=time(9, 0),
            closing_time=time(21, 0),
            latitude=10.5,
            longitude=106.5
        )

        assert restaurant.id is not None
        assert restaurant.approval_status == RestaurantApprovalStatus.PENDING

        # Kiểm tra notification được tạo
        notification = Notification.query.first()
        assert notification is not None
        assert "Yêu cầu duyệt nhà hàng mới" in notification.message


def test_update_restaurant(app, seed_restaurant_data):
    with app.app_context():
        updated = dao.RestaurantDAO.update_restaurant(
            restaurant_id=10,
            owner_id=1,
            name="Updated Name",
            description="Updated Description",
            phone="999888"
        )

        assert updated.name == "Updated Name"
        assert updated.description == "Updated Description"
        assert updated.phone == "999888"


def test_delete_restaurant(app, seed_restaurant_data):
    with app.app_context():
        success = dao.RestaurantDAO.delete_restaurant(10, 1)
        assert success is True

        restaurant = Restaurant.query.get(10)
        assert restaurant is None

