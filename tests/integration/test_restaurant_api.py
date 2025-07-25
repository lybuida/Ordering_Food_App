# tests/integration/test_restaurant_api.py
import pytest
from OrderingFoodApp.models import *
from OrderingFoodApp import db


@pytest.fixture
def seed_restaurant(app):
    with app.app_context():
        # Seed dữ liệu cơ bản
        u = User(id=1, name="Owner", email="o@x.com", password="p", role=UserRole.OWNER)

        # Thêm nhiều danh mục
        c1 = MenuCategory(id=1, name="Món Chính", image_url=None)
        c2 = MenuCategory(id=2, name="Đồ Uống", image_url=None)

        # Thêm nhiều nhà hàng - BỔ SUNG TRẠNG THÁI PHÊ DUYỆT
        r1 = Restaurant(
            id=5,
            owner_id=1,
            name="Quán A",
            address="Hanoi",
            phone="0123",
            approval_status=RestaurantApprovalStatus.APPROVED  # Thêm dòng này
        )
        r2 = Restaurant(
            id=6,
            owner_id=1,
            name="Nhà hàng B",
            address="HCM",
            phone="0124",
            approval_status=RestaurantApprovalStatus.APPROVED  # Thêm dòng này
        )

        # Thêm món ăn cho nhiều danh mục/nhà hàng
        m1 = MenuItem(id=100, restaurant_id=5, category_id=1, name="Phở gà", description="", price=30000)
        m2 = MenuItem(id=101, restaurant_id=5, category_id=1, name="Bún bò", description="", price=35000)
        m3 = MenuItem(id=102, restaurant_id=5, category_id=2, name="Trà đá", description="", price=5000)
        m4 = MenuItem(id=103, restaurant_id=6, category_id=1, name="Cơm tấm", description="", price=40000)

        db.session.add_all([u, c1, c2, r1, r2, m1, m2, m3, m4])
        db.session.commit()

@pytest.mark.usefixtures("client", "seed_restaurant")
def test_get_restaurant_detail(client):
    # giả lập login
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    resp = client.get('/customer/restaurant/5')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "Quán A" in text
    assert "Phở gà" in text and "Bún bò" in text


@pytest.mark.usefixtures("client", "seed_restaurant")
class TestRestaurantSearch:
    def login(self, client):
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True

    # Test tìm kiếm theo danh mục
    def test_search_by_category(self, client):
        self.login(client)

        # Tìm theo category_id=1 (Món Chính)
        resp = client.get('/customer/restaurants_list?category_id=1')
        text = resp.get_data(as_text=True)

        assert "Quán A" in text  # Có nhà hàng A
        assert "Nhà hàng B" in text  # Có nhà hàng B
        assert "Trà đá" not in text  # Không có đồ uống

    # Test tìm kiếm nhà hàng
    def test_search_restaurants(self, client):
        self.login(client)

        # Tìm nhà hàng có chữ "Quán"
        resp = client.get('/customer/restaurants_list?search=Quán&search_type=restaurants')
        text = resp.get_data(as_text=True)

        assert "Quán A" in text
        assert "Nhà hàng B" not in text  # Không xuất hiện
        assert "Phở gà" not in text  # Không hiển thị món ăn

    # Test tìm kiếm món ăn
    def test_search_dishes(self, client):
        self.login(client)

        # Tìm món có chữ "bún"
        resp = client.get('/customer/restaurants_list?search=bún&search_type=dishes')
        text = resp.get_data(as_text=True)

        assert "Bún bò" in text  # Có món bún bò
        assert "Quán A" in text  # Hiển thị nhà hàng chứa món
        assert "Cơm tấm" not in text  # Không xuất hiện

    # Test kết quả không tìm thấy
    def test_no_results(self, client):
        self.login(client)

        # Tìm với từ khóa không tồn tại
        resp = client.get('/customer/restaurants_list?search=abcdef&search_type=restaurants')
        text = resp.get_data(as_text=True)

        assert "Không tìm thấy nhà hàng nào" in text