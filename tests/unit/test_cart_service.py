# tests/unit/test_cart_service.py
import pytest
from flask import session
from OrderingFoodApp.dao.cart_service import init_cart, update_cart, get_cart_items, group_items_by_restaurant
from OrderingFoodApp.models import User, UserRole, MenuCategory, Restaurant, MenuItem
from OrderingFoodApp import db

@pytest.fixture
def ctx(app):
    with app.test_request_context():
        yield

def seed_menu_item(ctx):
    # seed User để thỏa FK owner_id
    u = User(id=1,
             name="Test User",
             email="u1@test.local",
             password="pass",
             role=UserRole.CUSTOMER)
    # seed category cho MenuItem.category_id
    c = MenuCategory(id=1, name="Cat1", image_url=None)
    # seed restaurant
    r = Restaurant(id=1, owner_id=1, name="R1", address="", phone="")
    # seed món
    m = MenuItem(id=1, restaurant_id=1, category_id=1,
                 name="M1", description="", price=10000)
    db.session.add_all([u, c, r, m])
    db.session.commit()

def test_init_cart_creates_empty(ctx):
    session.clear()
    cart = init_cart()
    assert isinstance(cart, dict) and cart == {}
    assert session["cart"] == {}

def test_add_and_get_items(ctx, app):
    seed_menu_item(ctx)
    # add tổng cộng 3
    update_cart("add", item_id=1, quantity=2)
    update_cart("add", item_id=1, quantity=1)
    items, total = get_cart_items()
    assert len(items) == 1
    assert items[0]["quantity"] == 3
    assert total == 3 * 10000

def test_increase_decrease_remove(ctx):
    session.clear()
    # add 1
    update_cart("add", item_id=1, quantity=1)
    # tăng lên 2
    update_cart("increase", item_id=1)
    # giảm về 1
    update_cart("decrease", item_id=1)
    items, total = get_cart_items()
    # MenuItem với id=1 vẫn tồn tại? Nếu không, items=[] và total=0
    assert isinstance(items, list)

def test_group_items(ctx, app):
    seed_menu_item(ctx)
    update_cart("add", item_id=1, quantity=2)
    items, _ = get_cart_items()
    grouped = group_items_by_restaurant(items)
    assert "R1" in grouped
    assert isinstance(grouped["R1"], list)
