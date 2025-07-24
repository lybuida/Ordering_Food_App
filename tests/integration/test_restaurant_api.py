# tests/integration/test_restaurant_api.py
import pytest
from OrderingFoodApp.models import User, UserRole, MenuCategory, Restaurant, MenuItem
from OrderingFoodApp import db

@pytest.fixture
def seed_restaurant(app):
    with app.app_context():
        # seed owner, category, restaurant, món
        u = User(id=1, name="Owner", email="o@x.com", password="p", role=UserRole.OWNER)
        c = MenuCategory(id=1, name="Cat", image_url=None)
        r = Restaurant(id=5, owner_id=1, name="Quán A", address="Hanoi", phone="0123")
        m1 = MenuItem(id=100, restaurant_id=5, category_id=1,
                      name="Phở gà", description="", price=30000)
        m2 = MenuItem(id=101, restaurant_id=5, category_id=1,
                      name="Bún bò", description="", price=35000)
        db.session.add_all([u, c, r, m1, m2])
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
