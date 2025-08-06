from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import aliased
from OrderingFoodApp.models import db, User, UserRole, Restaurant, PromoCode


def count_users_by_month(start_date: datetime, end_date: datetime):
    """Thống kê số lượng người dùng mới theo tháng."""
    return db.session.query(
        func.date_format(User.created_at, '%Y-%m').label('month'),
        func.count(User.id)
    ).filter(
        User.created_at >= start_date,
        User.created_at <= end_date
    ).group_by('month').order_by('month').all()


def count_restaurants_by_month(start_date: datetime, end_date: datetime):
    """Thống kê số lượng nhà hàng được thêm mới theo tháng."""
    return db.session.query(
        func.date_format(Restaurant.created_at, '%Y-%m').label('month'),
        func.count(Restaurant.id)
    ).filter(
        Restaurant.created_at >= start_date,
        Restaurant.created_at <= end_date
    ).group_by('month').order_by('month').all()


def count_users_total_by_role():
    """Thống kê tổng số lượng người dùng theo vai trò."""
    return db.session.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()


def count_restaurants_by_status():
    """Thống kê tổng số lượng nhà hàng theo trạng thái duyệt."""
    return db.session.query(
        Restaurant.approval_status,
        func.count(Restaurant.id)
    ).group_by(Restaurant.approval_status).all()


def get_user_registration_stats(start_date=None, end_date=None, group_by='day'):
    """
    Thống kê số người dùng đăng ký theo ngày/tháng/năm.

    :param start_date: datetime - Ngày bắt đầu lọc
    :param end_date: datetime - Ngày kết thúc lọc
    :param group_by: str - 'day', 'month', hoặc 'year'
    :return: List các tuple dạng (thời điểm, số lượng người dùng)
    """
    query = db.session.query
    label = None

    if group_by == 'day':
        label = func.date(User.created_at)
    elif group_by == 'month':
        label = func.concat(func.year(User.created_at), '-', func.lpad(func.month(User.created_at), 2, '0'))
    elif group_by == 'year':
        label = func.year(User.created_at)
    else:
        raise ValueError("group_by phải là 'day', 'month', hoặc 'year'")

    q = query(
        label.label('label'),
        func.count(User.id).label('user_count')
    ).select_from(User)

    if start_date:
        q = q.filter(User.created_at >= start_date)
    if end_date:
        q = q.filter(User.created_at <= end_date)

    q = q.group_by(label).order_by(label)

    return q.all()

def get_user_count_by_role():
    from OrderingFoodApp.models import User
    return db.session.query(User.role, func.count(User.id)).group_by(User.role).all()

def get_restaurant_registration_stats(start_date=None, end_date=None):
    query = db.session.query(
        func.date(Restaurant.created_at), func.count(Restaurant.id)
    ).group_by(func.date(Restaurant.created_at)).order_by(func.date(Restaurant.created_at))

    if start_date:
        query = query.filter(Restaurant.created_at >= start_date)
    if end_date:
        query = query.filter(Restaurant.created_at <= end_date)

    return query.all()

def get_restaurant_count_by_status():
    result = (
        db.session.query(Restaurant.approval_status, func.count(Restaurant.id))
        .group_by(Restaurant.approval_status)
        .all()
    )
    return result

def get_promo_created_stats(start_date=None, end_date=None):
    query = db.session.query(
        func.date(PromoCode.created_at),
        func.count(PromoCode.id)
    )

    if start_date:
        query = query.filter(PromoCode.created_at >= start_date)
    if end_date:
        query = query.filter(PromoCode.created_at <= end_date)

    query = query.group_by(func.date(PromoCode.created_at)).order_by(func.date(PromoCode.created_at))
    return query.all()


def get_promo_stats_by_type():
    return db.session.query(
        PromoCode.discount_type,
        func.count(PromoCode.id)
    ).group_by(PromoCode.discount_type).all()

