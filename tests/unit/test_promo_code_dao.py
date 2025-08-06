import pytest
from datetime import datetime, timedelta
from OrderingFoodApp.dao import promo_code_dao
from OrderingFoodApp.models import PromoCode, DiscountType


def create_sample_promo(code="SALE50", value=50, discount_type=DiscountType.PERCENT, usage_limit=10):
    return promo_code_dao.add_promo_code(
        code=code,
        description="Giảm giá khủng",
        discount_type=discount_type,
        discount_value=value,
        usage_limit=usage_limit,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=5),
        restaurant_id=None  # hoặc bạn truyền 1 id nhà hàng nếu cần test riêng
    )


def test_add_promo_code_success(app):
    with app.app_context():
        promo = create_sample_promo()
        assert promo is not None
        assert promo.code == "SALE50"
        assert promo.discount_value == 50


def test_get_all_promo_codes(app):
    with app.app_context():
        create_sample_promo(code="PROMO1")
        create_sample_promo(code="PROMO2")
        result = promo_code_dao.get_all_promo_codes()
        assert isinstance(result, list)
        assert any(p.code == "PROMO1" for p in result)
        assert any(p.code == "PROMO2" for p in result)


def test_get_promo_code_by_id(app):
    with app.app_context():
        promo = create_sample_promo(code="TESTID")
        fetched = promo_code_dao.get_promo_code_by_id(promo.id)
        assert fetched is not None
        assert fetched.code == "TESTID"


def test_delete_promo_code_success(app):
    with app.app_context():
        promo = create_sample_promo(code="DELETE_ME")
        success = promo_code_dao.delete_promo_code(promo.id)
        assert success is True

        deleted = promo_code_dao.get_promo_code_by_id(promo.id)
        assert deleted is None


def test_delete_promo_code_invalid_id(app):
    with app.app_context():
        result = promo_code_dao.delete_promo_code(promo_id=999999)
        assert result is False
