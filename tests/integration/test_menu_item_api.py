# tests/integration/test_menu_item_api.py
import pytest
from OrderingFoodApp.models import User, UserRole, Restaurant, MenuCategory, MenuItem
from OrderingFoodApp import db

@pytest.fixture
def seed_menu_item(app):
    with app.app_context():
        # seed owner + category + restaurant + món
        u = User(id=1, name="O", email="o@x.com", password="p", role=UserRole.OWNER)
        c = MenuCategory(id=2, name="Cat2", image_url=None)
        r = Restaurant(id=2, owner_id=1, name="R2", address="", phone="")
        m = MenuItem(id=20, restaurant_id=2, category_id=2,
                     name="Chả cá", description="Đặc sản", price=45000)
        db.session.add_all([u, c, r, m])
        db.session.commit()

@pytest.mark.usefixtures("client", "seed_menu_item")
def test_get_menu_item_detail(client):
    # giả lập login để không redirect
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    resp = client.get('/customer/menu_item/20')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "Chả cá" in text
    assert "Đặc sản" in text
