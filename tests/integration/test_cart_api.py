# tests/integration/test_cart_api.py
import pytest
from OrderingFoodApp.models import User, UserRole, Restaurant, MenuCategory, MenuItem
from OrderingFoodApp import db

@pytest.fixture
def seed_cart(app):
    with app.app_context():
        # chỉ seed đủ để cart page render
        u = User(id=1, name="U", email="u@x.com", password="p", role=UserRole.CUSTOMER)
        r = Restaurant(id=1, owner_id=1, name="R", address="", phone="")
        c = MenuCategory(id=1, name="Cat", image_url=None)
        m = MenuItem(id=10, restaurant_id=1, category_id=1,
                     name="Item", description="", price=20000)
        db.session.add_all([u, c, r, m])
        db.session.commit()

@pytest.mark.usefixtures("client", "seed_cart")
def test_cart_endpoints(client):
    # GET empty cart (no login_required)
    r0 = client.get('/customer/cart')
    assert r0.status_code == 200

    # bình thường add via form → redirect or 200
    r1 = client.post('/customer/cart',
                     data={'action':'add','item_id':10,'quantity':2})
    assert r1.status_code in (302, 200)

    # AJAX increase
    r2 = client.post('/customer/cart',
                     data={'action':'increase','item_id':10},
                     headers={'X-Requested-With':'XMLHttpRequest'})
    assert r2.is_json
    j2 = r2.get_json()
    assert j2['quantity'] >= 3

    # AJAX remove
    r3 = client.post('/customer/cart',
                     data={'action':'remove','item_id':10},
                     headers={'X-Requested-With':'XMLHttpRequest'})
    j3 = r3.get_json()
    assert j3['quantity'] == 0
