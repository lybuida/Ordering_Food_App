import pytest
from datetime import datetime, timedelta
from OrderingFoodApp import db
from OrderingFoodApp.models import (
    User, UserRole, Restaurant, RestaurantApprovalStatus,
    PromoCode, DiscountType
)
from OrderingFoodApp.dao import reports_dao
from werkzeug.security import generate_password_hash


@pytest.fixture
def sample_data(app):
    with app.app_context():
        now = datetime.utcnow()

        # Tạo người dùng
        users = [
            User(name="Admin", email="admin@test.com", role=UserRole.ADMIN,
                 password=generate_password_hash("123"), created_at=now - timedelta(days=30)),
            User(name="Owner", email="owner@test.com", role=UserRole.OWNER,
                 password=generate_password_hash("123"), created_at=now - timedelta(days=10)),
            User(name="Customer", email="customer@test.com", role=UserRole.CUSTOMER,
                 password=generate_password_hash("123"), created_at=now)
        ]
        db.session.add_all(users)
        db.session.commit()

        # Lấy ID của owner để tạo nhà hàng
        owner = User.query.filter_by(email="owner@test.com").first()

        restaurants = [
            Restaurant(name="Nhà hàng A", address="123 Đường A", phone="111", owner_id=owner.id,
                       approval_status=RestaurantApprovalStatus.PENDING, created_at=now - timedelta(days=20)),
            Restaurant(name="Nhà hàng B", address="456 Đường B", phone="222", owner_id=owner.id,
                       approval_status=RestaurantApprovalStatus.APPROVED, created_at=now)
        ]
        db.session.add_all(restaurants)
        db.session.commit()

        # Lấy ID của nhà hàng bất kỳ để liên kết mã khuyến mãi
        restaurant = Restaurant.query.first()

        promos = [
            PromoCode(code="PROMO1", discount_type=DiscountType.PERCENT, discount_value=10,
                      usage_limit=10, start_date=now - timedelta(days=1),
                      end_date=now + timedelta(days=5), created_at=now, restaurant_id=restaurant.id),
            PromoCode(code="PROMO2", discount_type=DiscountType.FIXED, discount_value=20000,
                      usage_limit=5, start_date=now,
                      end_date=now + timedelta(days=3), created_at=now, restaurant_id=restaurant.id)
        ]
        db.session.add_all(promos)
        db.session.commit()


# ========== TEST USERS ==========

def test_count_users_by_month(app, sample_data):
    with app.app_context():
        start = datetime.utcnow() - timedelta(days=60)
        end = datetime.utcnow()
        results = reports_dao.count_users_by_month(start, end)
        assert results
        assert all(isinstance(row[1], int) for row in results)


def test_count_users_total_by_role(app, sample_data):
    with app.app_context():
        results = reports_dao.count_users_total_by_role()
        roles = [r[0] for r in results]
        assert UserRole.ADMIN in roles
        assert UserRole.CUSTOMER in roles


def test_get_user_registration_stats_by_day(app, sample_data):
    with app.app_context():
        now = datetime.utcnow()
        start = now - timedelta(days=31)
        end = now + timedelta(days=1)
        stats = reports_dao.get_user_registration_stats(start_date=start, end_date=end, group_by="day")

        print("User stats:", stats)

        assert isinstance(stats, list)
        assert len(stats) > 0
        assert all(isinstance(row, tuple) and len(row) == 2 for row in stats)




def test_get_user_count_by_role(app, sample_data):
    with app.app_context():
        stats = reports_dao.get_user_count_by_role()
        assert isinstance(stats, list)
        assert any(r[0] == UserRole.OWNER for r in stats)


# ========== TEST RESTAURANTS ==========

def test_count_restaurants_by_month(app, sample_data):
    with app.app_context():
        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()
        results = reports_dao.count_restaurants_by_month(start, end)
        assert isinstance(results, list)
        assert all(isinstance(r[1], int) for r in results)


def test_count_restaurants_by_status(app, sample_data):
    with app.app_context():
        stats = reports_dao.count_restaurants_by_status()
        statuses = [s[0] for s in stats]
        assert RestaurantApprovalStatus.PENDING in statuses
        assert RestaurantApprovalStatus.APPROVED in statuses


def test_get_restaurant_registration_stats(app, sample_data):
    with app.app_context():
        stats = reports_dao.get_restaurant_registration_stats()
        print("Restaurant stats by day:", stats)
        assert isinstance(stats, list)
        assert len(stats) > 0
        assert all(isinstance(row, tuple) and len(row) == 2 for row in stats)



def test_get_restaurant_count_by_status(app, sample_data):
    with app.app_context():
        stats = reports_dao.get_restaurant_count_by_status()
        assert isinstance(stats, list)
        assert any(r[0] == RestaurantApprovalStatus.APPROVED for r in stats)


# ========== TEST PROMO CODES ==========

def test_get_promo_created_stats(app, sample_data):
    with app.app_context():
        stats = reports_dao.get_promo_created_stats()
        assert isinstance(stats, list)
        assert len(stats) >= 1


def test_get_promo_stats_by_type(app, sample_data):
    with app.app_context():
        stats = reports_dao.get_promo_stats_by_type()
        types = [s[0] for s in stats]
        assert DiscountType.PERCENT in types
        assert DiscountType.FIXED in types
