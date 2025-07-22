# OrderingFoodApp/dao/restaurants_owner.py
from OrderingFoodApp.models import db, Restaurant, RestaurantApprovalStatus, Notification, NotificationType
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


class RestaurantDAO:
    @staticmethod
    def get_restaurants_by_owner(owner_id):
        """Lấy danh sách nhà hàng của chủ sở hữu"""
        return Restaurant.query.filter_by(owner_id=owner_id).order_by(Restaurant.created_at.desc()).all()

    @staticmethod
    def get_restaurant_by_id(restaurant_id, owner_id=None):
        """Lấy thông tin nhà hàng theo ID, kiểm tra quyền sở hữu nếu cần"""
        query = Restaurant.query.filter_by(id=restaurant_id)
        if owner_id:
            query = query.filter_by(owner_id=owner_id)
        return query.first()

    @staticmethod
    def create_restaurant(owner_id, name, description, address, phone, opening_time, closing_time, latitude, longitude,
                          image_url=None):
        """Tạo mới nhà hàng"""
        try:
            restaurant = Restaurant(
                owner_id=owner_id,
                name=name,
                description=description,
                address=address,
                phone=phone,
                opening_time=opening_time,
                closing_time=closing_time,
                latitude=latitude,
                longitude=longitude,
                image_url=image_url,
                approval_status=RestaurantApprovalStatus.PENDING
            )
            db.session.add(restaurant)
            db.session.commit()

            # Tạo thông báo cho admin
            notification = Notification(
                user_id=owner_id,
                type=NotificationType.OTHER,
                message=f"Yêu cầu duyệt nhà hàng mới: {name}",
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()

            return restaurant
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_restaurant(restaurant_id, owner_id, **kwargs):
        """Cập nhật thông tin nhà hàng"""
        try:
            restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id, owner_id)
            if not restaurant:
                return None

            # Chỉ cho phép cập nhật một số trường nhất định
            allowed_fields = ['name', 'description', 'address', 'phone',
                              'opening_time', 'closing_time', 'latitude',
                              'longitude', 'image_url']

            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(restaurant, field):
                    setattr(restaurant, field, value)

            # Nếu nhà hàng bị từ chối và đang cập nhật, reset trạng thái về pending
            if restaurant.approval_status == RestaurantApprovalStatus.REJECTED:
                restaurant.approval_status = RestaurantApprovalStatus.PENDING
                restaurant.rejection_reason = None

                # Tạo thông báo cho admin
                notification = Notification(
                    user_id=owner_id,
                    type=NotificationType.OTHER,
                    message=f"Yêu cầu duyệt lại nhà hàng: {restaurant.name}",
                    is_read=False
                )
                db.session.add(notification)

            db.session.commit()
            return restaurant
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def resubmit_restaurant(restaurant_id, owner_id):
        """Gửi lại yêu cầu duyệt nhà hàng"""
        try:
            restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id, owner_id)
            if not restaurant:
                return None

            if restaurant.approval_status != RestaurantApprovalStatus.REJECTED:
                return restaurant

            restaurant.approval_status = RestaurantApprovalStatus.PENDING
            restaurant.rejection_reason = None

            # Tạo thông báo cho admin
            notification = Notification(
                user_id=owner_id,
                type=NotificationType.OTHER,
                message=f"Yêu cầu duyệt lại nhà hàng: {restaurant.name}",
                is_read=False
            )
            db.session.add(notification)

            db.session.commit()
            return restaurant
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def can_manage_restaurant(restaurant_id, owner_id):
        """Kiểm tra xem chủ nhà hàng có thể quản lý nhà hàng này không"""
        restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id, owner_id)
        if not restaurant:
            return False
        return restaurant.approval_status == RestaurantApprovalStatus.APPROVED

    @staticmethod
    def get_approval_status_display(status):
        """Chuyển đổi trạng thái sang dạng hiển thị"""
        status_map = {
            RestaurantApprovalStatus.PENDING: "Chờ duyệt",
            RestaurantApprovalStatus.APPROVED: "Đã duyệt",
            RestaurantApprovalStatus.REJECTED: "Bị từ chối"
        }
        return status_map.get(status, status.value)

    @staticmethod
    def delete_restaurant(restaurant_id, owner_id):
        """Xóa nhà hàng"""
        try:
            restaurant = RestaurantDAO.get_restaurant_by_id(restaurant_id, owner_id)
            if not restaurant:
                return False

            db.session.delete(restaurant)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e



