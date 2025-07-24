# tests/unit/test_customer_service.py
import pytest
from OrderingFoodApp.dao import customer_service as dao
from OrderingFoodApp.models import *
from OrderingFoodApp import db


@pytest.fixture
def ctx(app):
    with app.test_request_context():
        yield

@pytest.fixture
def seed_data(app):
    with app.app_context():
        # Tạo dữ liệu test
        owner = User(id=1, name="Owner", email="o@x.com", password="p", role="owner")
        customer = User(id=2, name="Customer", email="c@x.com", password="p", role="customer")  # Thêm customer

        category1 = MenuCategory(id=1, name="Món Chính", image_url=None)
        category2 = MenuCategory(id=2, name="Đồ Uống", image_url=None)

        # Nhà hàng 1
        r1 = Restaurant(id=1, owner_id=1, name="Quán Phở Hà Nội", address="Hanoi")
        # Nhà hàng 2
        r2 = Restaurant(id=2, owner_id=1, name="Bún Bò Huế", address="Hue")

        # Món ăn
        m1 = MenuItem(id=1, restaurant_id=1, category_id=1, name="Phở Bò", price=50000)
        m2 = MenuItem(id=2, restaurant_id=1, category_id=2, name="Trà Đá", price=10000)
        m3 = MenuItem(id=3, restaurant_id=2, category_id=1, name="Bún Bò", price=45000)

        # Đánh giá - THÊM customer_id
        rev1 = Review(id=1, customer_id=2, restaurant_id=1, rating=4)
        rev2 = Review(id=2, customer_id=2, restaurant_id=1, rating=5)
        rev3 = Review(id=3, customer_id=2, restaurant_id=2, rating=3)

        # THÊM customer vào danh sách
        db.session.add_all([owner, customer, category1, category2, r1, r2, m1, m2, m3, rev1, rev2, rev3])
        db.session.commit()


def test_get_restaurants_by_name(app, seed_data):
    with app.app_context():
        # Tìm kiếm theo tên
        result = dao.get_restaurants_by_name("Phở", 1)
        assert len(result['restaurants']) == 1
        assert result['restaurants'][0].name == "Quán Phở Hà Nội"
        assert result['restaurants'][0].avg_rating == 4.5  # (4+5)/2


def test_get_menu_items_by_name(app, seed_data):
    with app.app_context():
        # Tìm kiếm món ăn
        result = dao.get_menu_items_by_name("Bò", 1)
        assert len(result['menu_items']) == 2
        assert {item.name for item in result['menu_items']} == {"Phở Bò", "Bún Bò"}


def test_get_restaurants_by_category(app, seed_data):
    with app.app_context():
        # Lọc theo danh mục
        result = dao.get_restaurants_by_category(2, 1)  # Đồ uống
        assert len(result['restaurants']) == 1
        assert result['restaurants'][0].name == "Quán Phở Hà Nội"


def test_pagination(app, seed_data):
    with app.app_context():
        # Kiểm tra phân trang
        result = dao.get_restaurants_by_name("", 1, per_page=1)
        assert len(result['restaurants']) == 1
        assert result['total'] == 2