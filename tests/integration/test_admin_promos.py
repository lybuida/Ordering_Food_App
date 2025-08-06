import pytest
from flask import url_for
from OrderingFoodApp.models import *
from datetime import datetime, timedelta
from OrderingFoodApp.init_db import db


def login(client, email, password):
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


@pytest.fixture
def admin_login(client, admin_user):
    login(client, admin_user.email, "admin123")


@pytest.fixture
def customer_login(client, customer_user):
    login(client, customer_user.email, "customer123")


def test_access_promos_as_admin(client, admin_login):
    response = client.get("/admin/promos", follow_redirects=True)
    assert response.status_code == 200
    assert "Danh sách mã khuyến mãi" in response.data.decode()


def test_access_denied_for_customer(client, customer_login):
    response = client.get("/admin/promos", follow_redirects=True)
    assert response.status_code == 403  # Truy cập bị từ chối


def test_add_promo(client, admin_login, app):
    with app.app_context():
        code = "TESTPROMO"
        # Xoá nếu đã tồn tại
        existing = PromoCode.query.filter_by(code=code).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

    response = client.post("/admin/promos/add", data={
        "code": code,
        "description": "Giảm giá test",
        "discount_type": DiscountType.PERCENTAGE.name,
        "discount_value": 20,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        "usage_limit": 50
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Mã khuyến mãi đã được tạo thành công" in response.data.decode()


def test_invalid_discount_value(client, admin_login):
    response = client.post("/admin/promos/add", data={
        "code": "INVALIDDISCOUNT",
        "description": "Giảm quá mức cho phép",
        "discount_type": DiscountType.PERCENTAGE.name,
        "discount_value": 70,  # > 50%
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "usage_limit": 10
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Giá trị giảm giá không được vượt quá 50%" in response.data.decode()
