from OrderingFoodApp import db
from OrderingFoodApp.models import Restaurant, User, UserRole, RestaurantApprovalStatus
from sqlalchemy.exc import SQLAlchemyError


def get_all_restaurants(page=1, page_size=10, query=None, owner_id=None):
    """
    Lấy tất cả nhà hàng với phân trang và tìm kiếm/lọc.
    Args:
        page (int): Số trang hiện tại. Mặc định là 1.
        page_size (int): Số lượng nhà hàng trên mỗi trang. Mặc định là 10.
        query (str, optional): Chuỗi tìm kiếm theo tên hoặc địa chỉ nhà hàng. Mặc định là None.
        owner_id (int, optional): ID của chủ sở hữu để lọc nhà hàng. Mặc định là None.
    Returns:
        Pagination: Đối tượng phân trang chứa danh sách nhà hàng và thông tin phân trang.
    """
    restaurants_query = db.session.query(Restaurant)

    if query:
        # Tìm kiếm theo tên hoặc địa chỉ nhà hàng (không phân biệt hoa thường)
        restaurants_query = restaurants_query.filter(
            (Restaurant.name.ilike(f'%{query}%')) |
            (Restaurant.address.ilike(f'%{query}%'))
        )

    if owner_id:
        # Lọc theo chủ sở hữu
        restaurants_query = restaurants_query.filter(Restaurant.owner_id == owner_id)

    # # Sắp xếp theo tên nhà hàng
    # restaurants_query = restaurants_query.order_by(Restaurant.name)

    # Sắp xếp theo ID tăng dần (thường là tuần tự nhất)
    restaurants_query = restaurants_query.order_by(Restaurant.id)

    # Áp dụng phân trang
    restaurants_pagination = restaurants_query.paginate(
        page=page, per_page=page_size, error_out=False
    )
    return restaurants_pagination


def get_restaurant_by_id(restaurant_id):
    """
    Lấy thông tin một nhà hàng theo ID.
    Args:
        restaurant_id (int): ID của nhà hàng.
    Returns:
        Restaurant or None: Đối tượng Restaurant nếu tìm thấy, ngược lại là None.
    """
    return Restaurant.query.get(restaurant_id)


def add_restaurant(name, description, address, phone, owner_id, image_url=None, latitude=None, longitude=None):
    """
    Thêm một nhà hàng mới vào cơ sở dữ liệu.
    Args:
        name (str): Tên nhà hàng.
        description (str): Mô tả nhà hàng.
        address (str): Địa chỉ nhà hàng.
        phone (str): Số điện thoại nhà hàng.
        owner_id (int): ID của chủ sở hữu nhà hàng (phải là User có vai trò OWNER).
        image_url (str, optional): URL hình ảnh của nhà hàng. Mặc định là None.
        latitude (float, optional): Vĩ độ của nhà hàng. Mặc định là None.
        longitude (float, optional): Kinh độ của nhà hàng. Mặc định là None.
    Returns:
        Restaurant or None: Đối tượng Restaurant mới được thêm nếu thành công, ngược lại là None.
    """
    try:
        new_restaurant = Restaurant(
            name=name,
            description=description,
            address=address,
            phone=phone,
            owner_id=owner_id,
            image_url=image_url,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(new_restaurant)
        db.session.commit()
        return new_restaurant
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi thêm nhà hàng: {e}")
        return None


def update_restaurant(restaurant_id, **kwargs):
    """
    Cập nhật thông tin của một nhà hàng.
    Args:
        restaurant_id (int): ID của nhà hàng cần cập nhật.
        **kwargs: Các trường cần cập nhật (ví dụ: name='Nhà hàng mới', address='Địa chỉ mới').
    Returns:
        bool: True nếu cập nhật thành công, False nếu ngược lại.
    """
    restaurant = Restaurant.query.get(restaurant_id)
    if restaurant:
        try:
            for key, value in kwargs.items():
                # Chỉ cập nhật nếu key là một thuộc tính hợp lệ của Restaurant
                if hasattr(restaurant, key):
                    setattr(restaurant, key, value)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi cập nhật nhà hàng: {e}")
            return False
    return False


def delete_restaurant(restaurant_id):
    """
    Xóa một nhà hàng khỏi cơ sở dữ liệu.
    Args:
        restaurant_id (int): ID của nhà hàng cần xóa.
    Returns:
        bool: True nếu xóa thành công, False nếu ngược lại.
    """
    restaurant = Restaurant.query.get(restaurant_id)
    if restaurant:
        try:
            db.session.delete(restaurant)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi xóa nhà hàng: {e}")
            return False
    return False

def count_all_restaurants():
    """
    Đếm tổng số nhà hàng.
    Returns:
        int: Tổng số nhà hàng.
    """
    try:
        return db.session.query(Restaurant).count()
    except SQLAlchemyError as e:
        print(f"Error counting restaurants: {e}")
        return 0

def get_pending_restaurants():
    return Restaurant.query.filter(Restaurant.approval_status == RestaurantApprovalStatus.PENDING).all()

def approve_restaurant(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    if restaurant:
        restaurant.approval_status = RestaurantApprovalStatus.APPROVED
        db.session.commit()
        return True
    return False

def reject_restaurant(restaurant_id, reason):
    restaurant = Restaurant.query.get(restaurant_id)
    if restaurant:
        restaurant.approval_status = RestaurantApprovalStatus.REJECTED
        restaurant.rejection_reason = reason
        db.session.commit()
        return True
    return False


# Có thể thêm các hàm DAO khác liên quan đến nhà hàng tại đây, ví dụ:
# - get_restaurants_by_owner(owner_id)
# - get_top_rated_restaurants()
# - search_restaurants_by_cuisine()