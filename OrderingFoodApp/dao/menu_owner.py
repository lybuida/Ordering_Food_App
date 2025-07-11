# OrderingFoodApp/dao/menu_dao.py
from OrderingFoodApp.models import db, MenuItem, MenuCategory, Restaurant
from sqlalchemy import or_
from datetime import datetime


class MenuDAO:
    @staticmethod
    def get_menu_items(restaurant_id, category_id=None, status_filter=None, search=None, page=1, per_page=10):
        query = MenuItem.query.filter_by(restaurant_id=restaurant_id)

        if category_id and category_id != 'all':
            query = query.filter_by(category_id=category_id)

        if status_filter and status_filter != 'all':
            query = query.filter(MenuItem.is_active == (status_filter == 'active'))

        if search:
            search = f"%{search}%"
            query = query.filter(or_(
                MenuItem.name.ilike(search),
                MenuItem.description.ilike(search)
            ))

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_restaurant_categories(restaurant_id):
        return db.session.query(MenuCategory).join(MenuItem).filter(
            MenuItem.restaurant_id == restaurant_id
        ).distinct().all()

    @staticmethod
    def get_menu_item_by_id(item_id):
        return MenuItem.query.get(item_id)

    @staticmethod
    def create_menu_item(restaurant_id, category_id, name, description, price, image_url=None, is_active=True):
        menu_item = MenuItem(
            restaurant_id=restaurant_id,
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            is_active=is_active
        )
        db.session.add(menu_item)
        db.session.commit()
        return menu_item

    @staticmethod
    def update_menu_item(item_id, **kwargs):
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return None

        for key, value in kwargs.items():
            if hasattr(menu_item, key):
                setattr(menu_item, key, value)

        db.session.commit()
        return menu_item

    @staticmethod
    def delete_menu_item(item_id):
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return False

        db.session.delete(menu_item)
        db.session.commit()
        return True

    @staticmethod
    def get_categories():
        return MenuCategory.query.all()

    @staticmethod
    def toggle_menu_item_status(item_id):
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return False

        menu_item.is_active = not menu_item.is_active
        db.session.commit()
        return True