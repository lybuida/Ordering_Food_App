from OrderingFoodApp import db
from OrderingFoodApp.models import PromoCode
from sqlalchemy.exc import SQLAlchemyError

def get_all_promo_codes():
    return PromoCode.query.order_by(PromoCode.created_at.desc()).all()

def get_promo_code_by_id(promo_id):
    return PromoCode.query.get(promo_id)

def add_promo_code(**kwargs):
    try:
        promo = PromoCode(**kwargs)
        db.session.add(promo)
        db.session.commit()
        return promo
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Lỗi thêm mã khuyến mãi: {e}")
        return None

def delete_promo_code(promo_id):
    promo = PromoCode.query.get(promo_id)
    if promo:
        try:
            db.session.delete(promo)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Lỗi xóa mã khuyến mãi: {e}")
    return False
