# customer_service.py
from sqlalchemy import func
from OrderingFoodApp.models import *
from OrderingFoodApp import db
from flask import request

# Tìm kiếm nhà hàng theo TÊN NHÀ HÀNG
def get_restaurants_by_name(search_query, page, per_page=12):
    restaurants = db.session.query(
        Restaurant,
        func.coalesce(func.avg(Review.rating), 0.0).label('avg_rating')
    ) \
        .outerjoin(Review, Review.restaurant_id == Restaurant.id) \
        .filter(Restaurant.name.ilike(f'%{search_query}%')) \
        .group_by(Restaurant.id) \
        .order_by(Restaurant.id) \
        .paginate(page=page, per_page=per_page)

    results = []
    for restaurant, avg_rating in restaurants.items:
        restaurant.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        results.append(restaurant)

    return {
        'restaurants': results,
        'page': page,
        'per_page': per_page,
        'total': restaurants.total
    }

# Tìm món ăn chứa từ khóa, kèm theo thông tin nhà hàng
def get_menu_items_by_name(search_query, page, per_page=12):

    menu_items = MenuItem.query \
        .join(Restaurant, MenuItem.restaurant_id == Restaurant.id) \
        .filter(MenuItem.name.ilike(f'%{search_query}%')) \
        .add_entity(Restaurant) \
        .order_by(MenuItem.id) \
        .paginate(page=page, per_page=per_page)

    # Tạo danh sách kết quả với đầy đủ thông tin
    results = []
    for item in menu_items.items:
        # item[0] là MenuItem, item[customer] là Restaurant
        menu_item = item[0]
        menu_item.restaurant = item[1]  # Gán nhà hàng cho món ăn
        results.append(menu_item)

    return {
        'menu_items': results,
        'page': page,
        'per_page': per_page,
        'total': menu_items.total
    }

# Tính điểm trung bình cho mỗi nhà hàng
def get_restaurants_by_category(category_id, page, per_page=12):
    restaurants = db.session.query(
        Restaurant,
        func.coalesce(func.avg(Review.rating), 0.0).label('avg_rating')
    ) \
        .join(MenuItem, Restaurant.id == MenuItem.restaurant_id) \
        .outerjoin(Review, Review.restaurant_id == Restaurant.id) \
        .filter(MenuItem.category_id == category_id) \
        .group_by(Restaurant.id) \
        .order_by(Restaurant.id) \
        .paginate(page=page, per_page=per_page)

    # Gán điểm trung bình vào đối tượng nhà hàng
    results = []
    for restaurant, avg_rating in restaurants.items:
        restaurant.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        results.append(restaurant)

    return {
        'restaurants': results,
        'page': page,
        'per_page': per_page,
        'total': restaurants.total
    }

def get_all_restaurants(page, per_page=12):
    # Tính điểm trung bình cho mỗi nhà hàng
    restaurants = db.session.query(
        Restaurant,
        func.coalesce(func.avg(Review.rating), 0.0).label('avg_rating')
    ) \
        .outerjoin(Review, Review.restaurant_id == Restaurant.id) \
        .group_by(Restaurant.id) \
        .order_by(Restaurant.id) \
        .paginate(page=page, per_page=per_page)

    # Gán điểm trung bình vào đối tượng nhà hàng
    results = []
    for restaurant, avg_rating in restaurants.items:
        restaurant.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        results.append(restaurant)

    return {
        'restaurants': results,
        'page': page,
        'per_page': per_page,
        'total': restaurants.total
    }
