# dao/restaurants_owner.py
from OrderingFoodApp.models import db, Restaurant, Branch
from sqlalchemy import func
from datetime import time
from flask import current_app
import os
from werkzeug.utils import secure_filename

class RestaurantDAO:
    @staticmethod
    def get_restaurants_by_owner(owner_id):
        return Restaurant.query.filter_by(owner_id=owner_id).all()

    @staticmethod
    def get_restaurant_by_id(restaurant_id):
        return Restaurant.query.get(restaurant_id)

    @staticmethod
    def create_restaurant(owner_id, name, description, address, phone, opening_time, closing_time, image_url=None):
        restaurant = Restaurant(
            owner_id=owner_id,
            name=name,
            description=description,
            address=address,
            phone=phone,
            opening_time=opening_time,
            closing_time=closing_time,
            image_url=image_url
        )
        db.session.add(restaurant)
        db.session.commit()
        return restaurant

    @staticmethod
    def update_restaurant(restaurant_id, **kwargs):
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return None

        for key, value in kwargs.items():
            if hasattr(restaurant, key):
                setattr(restaurant, key, value)

        db.session.commit()
        return restaurant

    @staticmethod
    def delete_restaurant(restaurant_id):
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return False

        db.session.delete(restaurant)
        db.session.commit()
        return True

    @staticmethod
    def get_branches_by_restaurant(restaurant_id):
        return Branch.query.filter_by(restaurant_id=restaurant_id).all()

    @staticmethod
    def get_branch_by_id(branch_id):
        return Branch.query.get(branch_id)

    @staticmethod
    def create_branch(restaurant_id, name, address, phone, opening_time, closing_time, status='active', image_url=None):
        branch = Branch(
            restaurant_id=restaurant_id,
            name=name,
            address=address,
            phone=phone,
            opening_time=opening_time,
            closing_time=closing_time,
            status=status,
            image_url=image_url
        )
        db.session.add(branch)
        db.session.commit()
        return branch

    @staticmethod
    def update_branch(branch_id, **kwargs):
        branch = Branch.query.get(branch_id)
        if not branch:
            return None

        for key, value in kwargs.items():
            if hasattr(branch, key):
                setattr(branch, key, value)

        db.session.commit()
        return branch

    @staticmethod
    def delete_branch(branch_id):
        branch = Branch.query.get(branch_id)
        if not branch:
            return False

        db.session.delete(branch)
        db.session.commit()
        return True

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}